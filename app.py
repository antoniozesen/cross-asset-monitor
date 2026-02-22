from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import ALLOWED_TICKERS, RATIO_PAIRS, TICKER_NAMES
from src.data_extra import resolve_series
from src.data_fred import fetch_fred_series
from src.data_sources.ecb_client import fetch_ecb_series
from src.data_sources.eurostat_client import fetch_eurostat_series
from src.data_sources.oecd_client import fetch_oecd_series
from src.data_yf import fetch_prices
from src.diagnostics import check_allowed_tickers, check_percentiles, check_regime_probs, check_required_ratios
from src.features import build_market_features
from src.macro.composites import build_composites
from src.macro.regimes import regime_probabilities
from src.macro.transforms import apply_transform
from src.narrative import committee_text, key_takeaways_from_metrics, macro_regime_section
from src.plots import bars, heatmap, line
from src.portfolio import recommend_weights
from src.regime import infer_regime
from src.signals import build_signals
from src.ui.how_we_compute import render_how_we_compute
from src.utils import pct_rank, safe_div
from src.macro.catalog_data import CATALOG_INDICATORS

st.set_page_config(page_title="Cross-Asset Market Monitor", layout="wide")
st.title("Cross-Asset Market Monitor")


def label(t: str) -> str:
    return f"{t} | {TICKER_NAMES.get(t, t)}"


def with_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [label(c) for c in out.columns]
    return out


@st.cache_data(ttl=21600)
def load_macro_catalog(path: str = "src/macro/catalog.yaml") -> list[dict]:
    try:
        import yaml  # optional runtime dependency
        with open(path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
            items = loaded.get("indicators", [])
            if isinstance(items, list) and items:
                return items
    except Exception:
        pass
    return CATALOG_INDICATORS


@st.cache_data(ttl=21600)
def fetch_catalog_data(catalog: list[dict], start: str, end: str | None) -> pd.DataFrame:
    rows = []
    for ind in catalog:
        source = ind["source"]
        key = ind["source_key"]
        try:
            if source == "FRED":
                df = fetch_fred_series(key, start, end)
            elif source == "OECD":
                df = fetch_oecd_series(key, start, end)
            elif source == "EUROSTAT":
                df = fetch_eurostat_series(key)
            elif source == "ECB":
                parts = key.split("/")
                df = fetch_ecb_series(parts[1], "/".join(parts[2:]), start, end) if len(parts) >= 3 else pd.DataFrame(columns=["value"])
            else:
                df = pd.DataFrame(columns=["value"])
        except Exception:
            df = pd.DataFrame(columns=["value"])
        if df.empty:
            continue
        s = df["value"].astype(float)
        t = apply_transform(s, ind.get("transform", "LEVEL"))
        tmp = pd.DataFrame({"date": t.index, "value_t": t.values})
        for k in ["id", "display_name", "source", "country", "frequency", "type", "timing", "pillar", "weight"]:
            tmp[k] = ind.get(k)
        tmp["as_of"] = s.dropna().index.max() if not s.dropna().empty else pd.NaT
        tmp["ffill_applied"] = ind.get("frequency") in {"M", "Q", "A"}
        rows.append(tmp)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


with st.sidebar:
    start = st.date_input("Start date", value=pd.Timestamp.today() - pd.DateOffset(years=20))
    end = st.date_input("End date", value=pd.Timestamp.today())
    profile = st.selectbox("Profile", ["Conservative", "Balanced", "Growth"], index=1)
    flex = st.slider("Anchor flexibility (±pp)", 0, 10, 10) / 100
    include_mchi = st.toggle("Include MCHI", value=False)
    provider_flags = {
        "OECD": st.toggle("OECD", value=True),
        "TREASURY": st.toggle("US Treasury", value=True),
        "ECB": st.toggle("ECB", value=True),
        "EUROSTAT": st.toggle("Eurostat", value=True),
        "BUNDESBANK": st.toggle("Bundesbank", value=True),
        "WORLDBANK": st.toggle("World Bank", value=True),
    }

# market layer
tickers = [t for t in ALLOWED_TICKERS if t != "MCHI" or include_mchi]
prices = fetch_prices(tickers, str(start))
if prices.empty:
    st.error("No market prices loaded.")
    st.stop()

features = build_market_features(prices)
monthly = features["monthly_ret"]
signals = build_signals(features)
benchmark_6040 = 0.6 * monthly.get("SPY", 0) + 0.4 * monthly.get("IEF", 0)

# macro backbone
macro, meta = {}, {}
for concept in ["us_2y", "us_10y", "us_real_10y", "hy_oas", "ig_oas", "euro_inflation", "euro_unemployment"]:
    df, m = resolve_series(concept, "global", str(start), str(end), provider_flags=provider_flags)
    macro[concept], meta[concept] = df, m

macro_df = pd.DataFrame(index=monthly.index)
macro_df["growth"] = monthly.get("SPY", pd.Series(index=monthly.index, dtype=float)).rolling(6).mean()
macro_df["inflation"] = macro["euro_inflation"].get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df["real_rates"] = macro["us_real_10y"].get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df["slope"] = (macro["us_10y"].get("value", pd.Series(dtype=float)) - macro["us_2y"].get("value", pd.Series(dtype=float))).reindex(monthly.index)
macro_df["stress"] = macro["hy_oas"].get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df["inflation"] = macro_df["inflation"].fillna(monthly.get("BZ=F", pd.Series(index=monthly.index, dtype=float)).pct_change(12) * 100)
macro_df["stress"] = macro_df["stress"].fillna((safe_div(features["monthly_px"].get("LQD", pd.Series(dtype=float)), features["monthly_px"].get("HYG", pd.Series(dtype=float))) - 1).reindex(monthly.index))
macro_df = macro_df.interpolate(limit_direction="both")

probs, regime_state = infer_regime(macro_df)
stress_pct = pct_rank(macro_df["stress"]).dropna()
reco = recommend_weights(monthly, profile, probs.dropna().iloc[-1] if not probs.dropna().empty else pd.Series(), float(stress_pct.iloc[-1] / 100 if not stress_pct.empty else 0.5), flex=flex)

# macro layer
catalog = load_macro_catalog()
macro_tidy = fetch_catalog_data(catalog, str(start), str(end))
composites, contrib = build_composites(macro_tidy)

# fallback regime probs from macro composites if infer_regime is insufficient
macro_regime_fallback = pd.DataFrame()
if "US|GROWTH" in composites.columns and "US|INFLATION" in composites.columns:
    macro_regime_fallback = regime_probabilities(composites["US|GROWTH"], composites["US|INFLATION"], sigma=1.0)

# valuation metrics (best effort)
val_raw = pd.DataFrame(index=monthly.index)
for sid, col in [("DGS10", "us10y"), ("FEDFUNDS", "fedfunds"), ("T10YIE", "breakeven10y"), ("BAMLH0A0HYM2", "hy_oas"), ("BAMLC0A0CM", "ig_oas"), ("CAPE", "cape"), ("SP500", "spx")]:
    s = fetch_fred_series(sid, str(start), str(end))
    val_raw[col] = s.get("value", pd.Series(dtype=float)).reindex(monthly.index)
val_raw["hyg_lqd"] = safe_div(features["monthly_px"].get("HYG", pd.Series(dtype=float)), features["monthly_px"].get("LQD", pd.Series(dtype=float))).reindex(monthly.index)
val_raw["equity_risk_premium_proxy"] = (1 / val_raw["cape"]).replace([pd.NA, float("inf")], pd.NA) * 100 - val_raw["us10y"]
val_raw["yardeni_proxy"] = val_raw["equity_risk_premium_proxy"] - val_raw["fedfunds"]
val_pct = val_raw.apply(pct_rank).dropna(how="all")

pct_dash = pd.DataFrame({
    "SPY": pct_rank((1 + monthly.get("SPY", 0)).cumprod()),
    "VGK": pct_rank((1 + monthly.get("VGK", 0)).cumprod()),
    "HYG/LQD": pct_rank(val_raw["hyg_lqd"]),
    "US 10Y-2Y": pct_rank(macro_df["slope"]),
}).dropna(how="all")

bad = check_allowed_tickers(tickers)
ratio_missing = check_required_ratios(prices)

tabs = st.tabs(["Overview", "Regime", "Markets", "Signals", "Comparatives", "Valuation", "Allocation", "Narrative", "Macro (Hard/Soft)", "How we compute", "Sources"])

with tabs[0]:
    latest_reg = regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A"
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Assets", prices.shape[1]); c2.metric("Obs", prices.shape[0]); c3.metric("Regime", latest_reg); c4.metric("Missing ratios", len(ratio_missing)); c5.metric("Forbidden", len(bad))
    st.plotly_chart(heatmap(pct_dash.tail(12).T.fillna(50), "Cross-Asset Percentile Dashboard"), use_container_width=True)

with tabs[1]:
    st.plotly_chart(line(probs.tail(180), "Primary regime probabilities", "%"), use_container_width=True)
    if probs.dropna().empty and not macro_regime_fallback.empty:
        st.warning("Primary regime engine has insufficient data; showing fallback macro regime probabilities.")
    st.plotly_chart(line(macro_regime_fallback[["Reflation", "Goldilocks", "Stagflation", "Slowdown"]] if not macro_regime_fallback.empty else pd.DataFrame(), "Fallback macro regime probabilities", "%"), use_container_width=True)
    st.plotly_chart(line(macro_df[["growth", "inflation", "real_rates", "slope", "stress"]], "Regime drivers", "z/level"), use_container_width=True)
    st.write(f"EU unemployment source used: {meta.get('euro_unemployment', {}).get('source', 'N/A')} | series: {meta.get('euro_unemployment', {}).get('series_id', 'N/A')}")
    st.write(f"- Probability check: {'ok' if check_regime_probs(probs.dropna()) else 'fail'}")

with tabs[2]:
    b = [x for x in ["^GSPC", "^IXIC", "^DJI", "^RUT", "^STOXX", "^GDAXI", "^N225", "^HSI"] if x in prices.columns]
    st.plotly_chart(line(with_labels(features["monthly_px"][b].dropna(how="all")), "Indices levels", "Level"), use_container_width=True)
    st.plotly_chart(heatmap(with_labels(features["monthly_ret"][b].tail(12).T.fillna(0)), "Indices monthly returns"), use_container_width=True)

with tabs[3]:
    latest = signals[signals["date"] == signals["date"].max()].copy()
    latest["ticker"] = latest["ticker"].map(label)
    st.plotly_chart(bars(latest.sort_values("mom_3m"), "ticker", "mom_3m", "Momentum 3m"), use_container_width=True)
    st.plotly_chart(bars(latest.sort_values("mom_6m"), "ticker", "mom_6m", "Momentum 6m"), use_container_width=True)
    st.plotly_chart(bars(latest.sort_values("mom_12m"), "ticker", "mom_12m", "Momentum 12m"), use_container_width=True)
    st.plotly_chart(bars(latest.sort_values("vol_12m"), "ticker", "vol_12m", "Volatility 12m"), use_container_width=True)
    st.plotly_chart(heatmap(latest.set_index("ticker")[["mom_pct", "vol_pct", "dd_pct"]].T.fillna(50), "Signals percentiles"), use_container_width=True)

with tabs[4]:
    ratio_name = st.selectbox("Ratio", list(RATIO_PAIRS.keys()), index=0)
    a, b = RATIO_PAIRS[ratio_name]
    ratio = safe_div(features["monthly_px"][a], features["monthly_px"][b]).dropna()
    st.plotly_chart(line(pd.DataFrame({"ratio": ratio, "pct": pct_rank(ratio)}), ratio_name, "ratio/pct"), use_container_width=True)

with tabs[5]:
    st.plotly_chart(heatmap(val_pct.tail(60).T.fillna(50), "Valuation percentile dashboard"), use_container_width=True)
    st.plotly_chart(line(val_raw[["us10y", "fedfunds", "breakeven10y", "hy_oas", "ig_oas"]].dropna(how="all"), "Rates & credit valuation inputs", "%/bps"), use_container_width=True)
    st.plotly_chart(line(val_raw[["cape", "equity_risk_premium_proxy", "yardeni_proxy"]].dropna(how="all"), "ERP / Yardeni / CAPE proxies", "level"), use_container_width=True)

with tabs[6]:
    rp = reco.copy(); rp["ticker"] = rp["ticker"].map(label)
    st.plotly_chart(bars(rp, "ticker", "weight", f"Recommended weights ({profile})"), use_container_width=True)
    st.plotly_chart(bars(rp, "ticker", "delta", "Delta vs anchor"), use_container_width=True)

with tabs[7]:
    top_reg = regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A"
    st.markdown(committee_text({"top_regime": top_reg, "stress": float(stress_pct.iloc[-1] / 100 if not stress_pct.empty else 0.5), "credit": "mixto", "trend": "mixta"}))
    if not contrib.empty:
        st.markdown(macro_regime_section(contrib, composites))
    for b in key_takeaways_from_metrics({"top_regime": top_reg, "stress": 0.5, "risk_on_off": 0.1, "median_pct": 50}):
        st.write(f"- {b}")

with tabs[8]:
    st.subheader("Macro Layer (Hard/Soft)")
    macro_start = st.date_input("Macro start", value=pd.Timestamp(start), key="macro_start")
    macro_end = st.date_input("Macro end", value=pd.Timestamp(end), key="macro_end")
    countries = sorted(macro_tidy["country"].dropna().unique().tolist()) if not macro_tidy.empty else []
    selected_countries = st.multiselect("Countries", countries, default=countries)
    timing_filter = st.multiselect("Timing", ["LEADING", "COINCIDENT", "LAGGING"], default=["LEADING", "COINCIDENT", "LAGGING"])
    type_filter = st.multiselect("Type", ["HARD", "SOFT"], default=["HARD", "SOFT"])
    pillar_filter = st.multiselect("Pillar", ["GROWTH", "INFLATION", "LABOR", "FINANCIAL"], default=["GROWTH", "INFLATION", "LABOR", "FINANCIAL"])

    filt = macro_tidy.copy()
    if not filt.empty:
        filt = filt[(filt["date"] >= pd.Timestamp(macro_start)) & (filt["date"] <= pd.Timestamp(macro_end))]
        filt = filt[filt["country"].isin(selected_countries) & filt["timing"].isin(timing_filter) & filt["type"].isin(type_filter) & filt["pillar"].isin(pillar_filter)]
    if filt.empty:
        st.warning("No macro data available for current filters/date range.")
    else:
        wide = filt.pivot_table(index="date", columns="display_name", values="value_t")
        st.plotly_chart(line(wide.resample("D").ffill(), "Indicator evolution (daily aligned)", "transformed"), use_container_width=True)

        comp_cols = [c for c in composites.columns if any(c.startswith(f"{ctry}|") for ctry in selected_countries)]
        comp_window = composites.loc[(composites.index >= pd.Timestamp(macro_start)) & (composites.index <= pd.Timestamp(macro_end)), comp_cols] if comp_cols else pd.DataFrame()
        st.plotly_chart(line(comp_window, "Composites by country", "z"), use_container_width=True)

        for c in selected_countries:
            gz = comp_window.get(f"{c}|GROWTH", pd.Series(dtype=float))
            iz = comp_window.get(f"{c}|INFLATION", pd.Series(dtype=float))
            rp = regime_probabilities(gz, iz, sigma=1.0)
            if rp.empty:
                continue
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(f"{c} Reflation %", f"{rp['Reflation_prob'].iloc[-1]:.1f}")
            k2.metric(f"{c} Slowdown %", f"{rp['Slowdown_prob'].iloc[-1]:.1f}")
            k3.metric(f"{c} Goldilocks %", f"{rp['Goldilocks'].iloc[-1]:.1f}")
            k4.metric(f"{c} Stagflation %", f"{rp['Stagflation'].iloc[-1]:.1f}")
            st.plotly_chart(line(rp[["Reflation", "Goldilocks", "Stagflation", "Slowdown"]], f"{c} regime probabilities", "%"), use_container_width=True)

        snap = filt.sort_values("date").groupby("id").tail(1)[["display_name", "country", "value_t", "as_of", "source", "type", "timing", "pillar", "ffill_applied"]]
        st.dataframe(snap.rename(columns={"value_t": "latest_transformed"}), use_container_width=True)
        contrib_latest = contrib[contrib["country"].isin(selected_countries)].sort_values("date").groupby(["country", "display_name"]).tail(1)
        st.dataframe(contrib_latest[["country", "display_name", "type", "timing", "weight", "value_t", "contribution", "source"]], use_container_width=True)

with tabs[9]:
    render_how_we_compute()

with tabs[10]:
    st.dataframe(pd.DataFrame(meta).T)
    st.dataframe(pd.DataFrame({"forbidden_tickers": [", ".join(bad) if bad else "none"], "missing_ratios": [len(ratio_missing)], "percentiles_ok": [check_percentiles(pct_dash.tail(12))], "regime_probs_ok": [check_regime_probs(probs.dropna())]}))
