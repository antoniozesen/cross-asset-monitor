from __future__ import annotations

import pandas as pd
import streamlit as st
import yaml

from src.config import ALLOWED_TICKERS, RATIO_PAIRS, TICKER_NAMES
from src.data_extra import resolve_series
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
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("indicators", [])


@st.cache_data(ttl=21600)
def fetch_catalog_data(catalog: list[dict], start: str, end: str | None) -> pd.DataFrame:
    rows = []
    for ind in catalog:
        source = ind["source"]
        key = ind["source_key"]
        if source == "FRED":
            from src.data_fred import fetch_fred_series
            df = fetch_fred_series(key, start, end)
        elif source == "OECD":
            df = fetch_oecd_series(key, start, end)
        elif source == "EUROSTAT":
            df = fetch_eurostat_series(key)
        elif source == "ECB":
            parts = key.split("/")
            if len(parts) >= 3:
                df = fetch_ecb_series(parts[1], "/".join(parts[2:]), start, end)
            else:
                df = pd.DataFrame(columns=["value"])
        else:
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
        "BUNDESBANK": st.toggle("Bundesbank", value=True),
        "WORLDBANK": st.toggle("World Bank", value=True),
    }

# core market layer
tickers = [t for t in ALLOWED_TICKERS if t != "MCHI" or include_mchi]
prices = fetch_prices(tickers, str(start))
if prices.empty:
    st.error("No market prices loaded.")
    st.stop()

features = build_market_features(prices)
monthly = features["monthly_ret"]
signals = build_signals(features)
benchmark_6040 = 0.6 * monthly.get("SPY", 0) + 0.4 * monthly.get("IEF", 0)

# existing macro backbone
macro, meta = {}, {}
for concept in ["us_2y", "us_10y", "us_real_10y", "hy_oas", "ig_oas", "euro_inflation", "euro_unemployment"]:
    df, m = resolve_series(concept, "global", str(start), str(end), provider_flags=provider_flags)
    macro[concept], meta[concept] = df, m

macro_df = pd.DataFrame(index=monthly.index)
macro_df["growth"] = monthly.get("SPY", pd.Series(index=monthly.index, dtype=float)).rolling(6).mean()
macro_df["inflation"] = macro.get("euro_inflation", pd.DataFrame(columns=["value"])).get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df["real_rates"] = macro.get("us_real_10y", pd.DataFrame(columns=["value"])).get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df["slope"] = (macro.get("us_10y", pd.DataFrame(columns=["value"])).get("value", pd.Series(dtype=float)) - macro.get("us_2y", pd.DataFrame(columns=["value"])).get("value", pd.Series(dtype=float))).reindex(monthly.index)
macro_df["stress"] = macro.get("hy_oas", pd.DataFrame(columns=["value"])).get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df = macro_df.interpolate(limit_direction="both")
probs, regime_state = infer_regime(macro_df)
stress_pct = pct_rank(macro_df["stress"]).dropna()
reco = recommend_weights(monthly, profile, probs.dropna().iloc[-1] if not probs.dropna().empty else pd.Series(), float(stress_pct.iloc[-1] / 100 if not stress_pct.empty else 0.5), flex=flex)

pct_dash = pd.DataFrame({
    "SPY": pct_rank((1 + monthly.get("SPY", 0)).cumprod()),
    "VGK": pct_rank((1 + monthly.get("VGK", 0)).cumprod()),
    "HYG/LQD": pct_rank(safe_div(features["monthly_px"].get("HYG", pd.Series(dtype=float)), features["monthly_px"].get("LQD", pd.Series(dtype=float)))),
    "US 10Y-2Y": pct_rank(macro_df["slope"]),
}).dropna(how="all")

# new macro layer
catalog = load_macro_catalog()
macro_tidy = fetch_catalog_data(catalog, str(start), str(end))
composites, contrib = build_composites(macro_tidy)

bad = check_allowed_tickers(tickers)
ratio_missing = check_required_ratios(prices)

# tabs
tabs = st.tabs(["Overview", "Regime", "Markets", "Signals", "Comparatives", "Valuation", "Allocation", "Narrative", "Macro (Hard/Soft)", "How we compute", "Sources"])

with tabs[0]:
    latest_reg = regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A"
    cols = st.columns(5)
    for i, (k, v) in enumerate({"Assets": prices.shape[1], "Obs": prices.shape[0], "Regime": latest_reg, "Missing ratios": len(ratio_missing), "Forbidden tickers": len(bad)}.items()):
        cols[i].metric(k, v)
    st.plotly_chart(heatmap(pct_dash.tail(12).T.fillna(50), "Cross-Asset Percentile Dashboard"), use_container_width=True)
    st.plotly_chart(line(probs.tail(12), "Regime probabilities (1y)", "Probability"), use_container_width=True)
    st.plotly_chart(line(with_labels(features["monthly_px"][["^GSPC", "^STOXX", "^N225"]].dropna()), "Main indices", "Level"), use_container_width=True)

with tabs[1]:
    st.plotly_chart(line(probs.tail(180), "Regime probabilities (15y)", "Probability"), use_container_width=True)
    st.plotly_chart(line(macro_df[["growth", "inflation", "real_rates", "slope", "stress"]], "Regime drivers", "z/level"), use_container_width=True)
    st.write(f"- Probability check: {'ok' if check_regime_probs(probs.dropna()) else 'fail'}")

with tabs[2]:
    b = [x for x in ["^GSPC", "^IXIC", "^DJI", "^RUT", "^STOXX", "^GDAXI", "^N225", "^HSI"] if x in prices.columns]
    st.plotly_chart(line(with_labels(features["monthly_px"][b].dropna(how="all")), "Indices levels", "Level"), use_container_width=True)
    st.plotly_chart(heatmap(with_labels(features["monthly_ret"][b].tail(12).T.fillna(0)), "Indices monthly returns"), use_container_width=True)

with tabs[3]:
    latest_s = signals[signals["date"] == signals["date"].max()].copy()
    latest_s["ticker"] = latest_s["ticker"].map(label)
    st.plotly_chart(bars(latest_s.sort_values("mom_12m"), "ticker", "mom_12m", "Momentum 12m"), use_container_width=True)

with tabs[4]:
    ratio_name = st.selectbox("Ratio", list(RATIO_PAIRS.keys()), index=0)
    a, b = RATIO_PAIRS[ratio_name]
    ratio = safe_div(features["monthly_px"][a], features["monthly_px"][b]).dropna()
    rret = ratio.pct_change()
    st.plotly_chart(line(pd.DataFrame({"ratio": ratio, "pct": pct_rank(ratio)}), f"{ratio_name}", "ratio / pct"), use_container_width=True)
    st.plotly_chart(line(pd.DataFrame({"corr_spy": rret.rolling(12).corr(monthly.get("SPY")), "corr_6040": rret.rolling(12).corr(benchmark_6040)}), "Rolling corr", "corr"), use_container_width=True)

with tabs[5]:
    val = pd.DataFrame({"slope": pct_rank(macro_df["slope"]), "real": pct_rank(macro_df["real_rates"]), "stress": pct_rank(macro_df["stress"])})
    st.plotly_chart(heatmap(val.tail(36).T.fillna(50), "Valuation Dashboard"), use_container_width=True)

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
    countries = sorted(macro_tidy["country"].dropna().unique().tolist()) if not macro_tidy.empty else []
    selected_countries = st.multiselect("Countries", countries, default=countries[:2] if countries else [])
    timing_filter = st.multiselect("Timing", ["LEADING", "COINCIDENT", "LAGGING"], default=["LEADING", "COINCIDENT", "LAGGING"])
    type_filter = st.multiselect("Type", ["HARD", "SOFT"], default=["HARD", "SOFT"])
    pillar_filter = st.multiselect("Pillar", ["GROWTH", "INFLATION", "LABOR", "FINANCIAL"], default=["GROWTH", "INFLATION", "LABOR", "FINANCIAL"])

    filt = macro_tidy.copy()
    if not filt.empty:
        filt = filt[filt["country"].isin(selected_countries) & filt["timing"].isin(timing_filter) & filt["type"].isin(type_filter) & filt["pillar"].isin(pillar_filter)]
    if filt.empty:
        st.warning("No macro data available for current filters.")
    else:
        wide = filt.pivot_table(index="date", columns="display_name", values="value_t")
        st.plotly_chart(line(wide.resample("D").ffill(), "Indicator evolution (daily aligned)", "transformed value"), use_container_width=True)

        comp_cols = [c for c in composites.columns if any(c.startswith(f"{ctry}|") for ctry in selected_countries)]
        if comp_cols:
            st.plotly_chart(line(composites[comp_cols], "Country composites (z-index)", "z"), use_container_width=True)

        # regime probabilities per selected country using growth/inflation pillars
        for c in selected_countries:
            gz = composites.get(f"{c}|GROWTH", pd.Series(dtype=float))
            iz = composites.get(f"{c}|INFLATION", pd.Series(dtype=float))
            rp = regime_probabilities(gz, iz, sigma=1.0)
            if rp.empty:
                continue
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(f"{c} Reflation %", f"{rp['Reflation_prob'].iloc[-1]:.1f}")
            k2.metric(f"{c} Slowdown %", f"{rp['Slowdown_prob'].iloc[-1]:.1f}")
            k3.metric(f"{c} Goldilocks %", f"{rp['Goldilocks'].iloc[-1]:.1f}")
            k4.metric(f"{c} Stagflation %", f"{rp['Stagflation'].iloc[-1]:.1f}")
            st.plotly_chart(line(rp[["Reflation", "Goldilocks", "Stagflation", "Slowdown"]], f"{c} regime probabilities", "%"), use_container_width=True)

        snap = filt.sort_values("date").groupby("id").tail(1)[["display_name", "country", "value_t", "as_of", "source", "type", "timing", "pillar"]]
        st.dataframe(snap.rename(columns={"value_t": "latest_transformed"}), use_container_width=True)
        contrib_latest = contrib[contrib["country"].isin(selected_countries)].sort_values("date").groupby(["country", "display_name"]).tail(1)
        st.dataframe(contrib_latest[["country", "display_name", "type", "timing", "weight", "value_t", "contribution", "source"]], use_container_width=True)

with tabs[9]:
    render_how_we_compute()

with tabs[10]:
    st.dataframe(pd.DataFrame(meta).T)
    st.dataframe(pd.DataFrame({"forbidden_tickers": [", ".join(bad) if bad else "none"], "missing_ratios": [len(ratio_missing)], "percentiles_ok": [check_percentiles(pct_dash.tail(12))], "regime_probs_ok": [check_regime_probs(probs.dropna())]}))
    st.write("As-of and ffill flags in macro snapshot table under Macro tab.")
