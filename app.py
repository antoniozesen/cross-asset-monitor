from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import ALLOWED_TICKERS, RATIO_PAIRS, TICKER_NAMES
from src.data_extra import resolve_series
from src.data_yf import fetch_prices
from src.diagnostics import check_allowed_tickers, check_percentiles, check_regime_probs, check_required_ratios
from src.features import build_market_features
from src.narrative import committee_text, key_takeaways_from_metrics
from src.plots import bars, heatmap, line
from src.portfolio import recommend_weights
from src.regime import infer_regime
from src.signals import build_signals
from src.utils import pct_rank, safe_div

st.set_page_config(page_title="Cross-Asset Market Monitor", layout="wide")
st.title("Cross-Asset Market Monitor")


def label(t: str) -> str:
    return f"{t} | {TICKER_NAMES.get(t, t)}"


def with_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [label(c) for c in out.columns]
    return out


with st.sidebar:
    start = st.date_input("Start date", value=pd.Timestamp.today() - pd.DateOffset(years=20))
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

tickers = [t for t in ALLOWED_TICKERS if t != "MCHI" or include_mchi]
prices = fetch_prices(tickers, str(start))
if prices.empty:
    st.error("No market prices loaded.")
    st.stop()

features = build_market_features(prices)
monthly = features["monthly_ret"]

macro, meta = {}, {}
for concept in ["us_2y", "us_10y", "us_real_10y", "hy_oas", "ig_oas", "euro_inflation", "euro_unemployment"]:
    df, m = resolve_series(concept, "global", str(start), provider_flags=provider_flags)
    macro[concept], meta[concept] = df, m

macro_df = pd.DataFrame(index=monthly.index)
macro_df["growth"] = monthly.get("SPY", pd.Series(index=monthly.index, dtype=float)).rolling(6).mean()
macro_df["inflation"] = macro["euro_inflation"].get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df["real_rates"] = macro["us_real_10y"].get("value", pd.Series(dtype=float)).reindex(monthly.index)
macro_df["slope"] = (macro["us_10y"].get("value", pd.Series(dtype=float)) - macro["us_2y"].get("value", pd.Series(dtype=float))).reindex(monthly.index)
macro_df["stress"] = macro["hy_oas"].get("value", pd.Series(dtype=float)).reindex(monthly.index)

proxy_stress = (safe_div(features["monthly_px"].get("LQD", pd.Series(dtype=float)), features["monthly_px"].get("HYG", pd.Series(dtype=float))) - 1).reindex(monthly.index)
macro_df["inflation"] = macro_df["inflation"].fillna(monthly.get("BZ=F", pd.Series(index=monthly.index, dtype=float)).pct_change(12) * 100)
macro_df["real_rates"] = macro_df["real_rates"].fillna(macro_df["slope"])
macro_df["stress"] = macro_df["stress"].fillna(proxy_stress)
macro_df = macro_df.interpolate(limit_direction="both")

probs, regime_state = infer_regime(macro_df)
signals = build_signals(features)
benchmark_6040 = 0.6 * monthly.get("SPY", 0) + 0.4 * monthly.get("IEF", 0)
stress_pct = pct_rank(macro_df["stress"]).dropna()
reco = recommend_weights(monthly, profile, probs.dropna().iloc[-1] if not probs.dropna().empty else pd.Series(), float(stress_pct.iloc[-1] / 100 if not stress_pct.empty else 0.5), flex=flex)

pct_dash = pd.DataFrame({
    "SPY": pct_rank((1 + monthly.get("SPY", 0)).cumprod()),
    "VGK": pct_rank((1 + monthly.get("VGK", 0)).cumprod()),
    "HYG/LQD": pct_rank(safe_div(features["monthly_px"].get("HYG", pd.Series(dtype=float)), features["monthly_px"].get("LQD", pd.Series(dtype=float))),),
    "US 10Y-2Y": pct_rank(macro_df["slope"]),
}).dropna(how="all")

bad = check_allowed_tickers(tickers)
ratio_missing = check_required_ratios(prices)

missing_concepts = [k for k, v in macro.items() if v.empty]
if missing_concepts:
    st.warning(f"Series no disponibles en proveedor primario: {', '.join(missing_concepts)}. Se usan proxies cuando aplica.")

tabs = st.tabs(["Overview", "Regime", "Markets", "Signals", "Comparatives", "Valuation", "Allocation", "Narrative", "Sources"])

with tabs[0]:
    latest_reg = regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A"
    cols = st.columns(5)
    metrics = {"Assets": prices.shape[1], "Obs": prices.shape[0], "Regime": latest_reg, "Missing ratios": len(ratio_missing), "Forbidden tickers": len(bad)}
    for i, (k, v) in enumerate(metrics.items()):
        cols[i].metric(k, v)
    st.plotly_chart(heatmap(pct_dash.tail(12).T.fillna(50), "Cross-Asset Percentile Dashboard (0-100)"), use_container_width=True)
    st.plotly_chart(line(probs.tail(12), "Regime probabilities (1y)", "Probability"), use_container_width=True)
    st.plotly_chart(line(with_labels(features["drawdown"][["SPY", "VGK", "IEMG"]].dropna()), "Drawdowns: SPY/VGK/IEMG", "%"), use_container_width=True)
    st.plotly_chart(line(with_labels(features["vol_12m"][["SPY", "TLT", "HYG"]].dropna()), "12m vol: SPY/TLT/HYG", "% ann"), use_container_width=True)
    st.plotly_chart(line(with_labels(features["monthly_px"][["^GSPC", "^STOXX", "^N225"]].dropna()), "Indices principales", "Level"), use_container_width=True)
    for b in key_takeaways_from_metrics({"top_regime": latest_reg, "stress": float(stress_pct.iloc[-1] / 100 if not stress_pct.empty else 0.5), "risk_on_off": 0.1, "median_pct": float(pct_dash.tail(1).median(axis=1).iloc[0] if not pct_dash.empty else 50)}):
        st.write(f"- {b}")

with tabs[1]:
    st.plotly_chart(line(probs.tail(180), "Regime probabilities (15y)", "Probability"), use_container_width=True)
    st.area_chart(probs.tail(12))
    st.plotly_chart(line(macro_df[["growth", "inflation", "real_rates", "slope", "stress"]], "Regime drivers", "z/level"), use_container_width=True)
    st.dataframe(probs.tail(12).round(3))
    st.write("### Key takeaways")
    st.write(f"- Último régimen: {regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else 'N/A'}")
    st.write(f"- Chequeo de probabilidades (suma=1): {'ok' if check_regime_probs(probs.dropna()) else 'falla'}")
    st.write(f"- Muestras útiles para régimen: {macro_df.dropna().shape[0]} meses")

with tabs[2]:
    group = st.selectbox("Market bucket", ["Indices", "Regions", "US Sectors", "EU Sectors", "FX", "Commodities"], index=0)
    bucket_map = {
        "Indices": ["^GSPC", "^IXIC", "^DJI", "^RUT", "^STOXX", "^GDAXI", "^N225", "^HSI"],
        "Regions": ["SPY", "VGK", "EWJ", "IEMG"],
        "US Sectors": ["XLK", "XLF", "XLI", "XLV", "XLP", "XLU", "XLE", "XLB", "XLY", "XLRE", "XLC"],
        "EU Sectors": ["ESIF.L", "EXV6.DE", "HLTH.L", "ESIE.F", "ESIS.F", "ESIN.L", "EXV3.DE", "ESIC.F", "EXV1.DE", "EXH6.DE", "EXH9.DE"],
        "FX": ["EURUSD=X", "EURGBP=X", "EURJPY=X", "USDJPY=X", "GBPUSD=X", "USDCHF=X"],
        "Commodities": ["GC=F", "SI=F", "BZ=F", "CL=F", "NG=F", "HG=F"],
    }
    b = [x for x in bucket_map[group] if x in prices.columns]
    st.plotly_chart(line(with_labels(features["monthly_px"][b].dropna(how="all")), f"{group} levels", "Level"), use_container_width=True)
    st.plotly_chart(heatmap(with_labels(features["monthly_ret"][b].tail(12).T.fillna(0)), f"{group} monthly return heatmap"), use_container_width=True)
    latest = features["monthly_ret"][b].tail(1).T.reset_index(); latest.columns = ["ticker", "ret"]; latest["ticker"] = latest["ticker"].map(label)
    st.plotly_chart(bars(latest.sort_values("ret"), "ticker", "ret", f"{group} latest monthly return"), use_container_width=True)
    st.write("- Lectura determinista: liderazgo por momentum mensual y dispersión intra-bucket.")

with tabs[3]:
    latest_s = signals[signals["date"] == signals["date"].max()].copy()
    latest_s["ticker"] = latest_s["ticker"].map(label)
    st.plotly_chart(bars(latest_s.sort_values("mom_12m"), "ticker", "mom_12m", "Momentum 12m"), use_container_width=True)
    st.plotly_chart(bars(latest_s.sort_values("vol_12m"), "ticker", "vol_12m", "Vol 12m"), use_container_width=True)
    st.plotly_chart(heatmap(latest_s.set_index("ticker")[["mom_pct", "vol_pct", "dd_pct"]].T.fillna(50), "Signal percentiles"), use_container_width=True)
    st.write("- Señales: combinar momentum alto + volatilidad contenida + drawdown acotado.")

with tabs[4]:
    ratio_name = st.selectbox("Ratio", list(RATIO_PAIRS.keys()), index=0)
    a, b = RATIO_PAIRS[ratio_name]
    ratio = safe_div(features["monthly_px"][a], features["monthly_px"][b]).dropna()
    rret = ratio.pct_change()
    dfc = pd.DataFrame({"ratio": ratio, "pct": pct_rank(ratio), "ret_12m": (1 + rret).rolling(12).apply(lambda x: x.prod() - 1), "vol_12m": rret.rolling(12).std() * (12**0.5)})
    st.plotly_chart(line(dfc[["ratio"]], f"{ratio_name} level", "x"), use_container_width=True)
    st.plotly_chart(line(dfc[["pct"]], f"{ratio_name} percentile", "Percentile"), use_container_width=True)
    st.plotly_chart(line(dfc[["ret_12m", "vol_12m"]], f"{ratio_name} rolling metrics", "ret/vol"), use_container_width=True)
    st.plotly_chart(line(pd.DataFrame({"corr_spy": rret.rolling(12).corr(monthly.get("SPY")), "corr_gspc": rret.rolling(12).corr(monthly.get("^GSPC")), "corr_6040": rret.rolling(12).corr(benchmark_6040)}), f"{ratio_name} rolling correlations", "corr"), use_container_width=True)
    dd = ratio / ratio.cummax() - 1
    st.plotly_chart(line(pd.DataFrame({"rolling_mdd_36m": dd.rolling(36).min(), "since_inception_dd": dd}), f"{ratio_name} drawdowns", "drawdown"), use_container_width=True)
    st.write("- Lectura: combinar tendencia relativa, percentil histórico y correlación con benchmarks.")

with tabs[5]:
    val = pd.DataFrame({
        "us_curve_slope": pct_rank(macro_df["slope"]),
        "us_real_10y": pct_rank(macro_df["real_rates"]),
        "hy_oas": pct_rank(macro_df["stress"]),
        "hyg_lqd_proxy": pct_rank(safe_div(features["monthly_px"].get("HYG", pd.Series(dtype=float)), features["monthly_px"].get("LQD", pd.Series(dtype=float)))),
    }).dropna(how="all")
    st.plotly_chart(heatmap(val.tail(36).T.fillna(50), "Valuation percentile dashboard"), use_container_width=True)
    st.plotly_chart(line(val, "Valuation percentiles", "0-100"), use_container_width=True)
    st.write("- Valoración: percentiles altos de spread = crédito más barato, pero con mayor estrés macro-financiero.")

with tabs[6]:
    reco_plot = reco.copy(); reco_plot["ticker"] = reco_plot["ticker"].map(label)
    st.plotly_chart(bars(reco_plot, "ticker", "weight", f"Recommended weights ({profile})"), use_container_width=True)
    st.plotly_chart(bars(reco_plot, "ticker", "delta", "Delta vs anchor"), use_container_width=True)
    st.write("- Asignación sensible al perfil, régimen y estrés (penalización explícita a HY en risk-off).")

with tabs[7]:
    top_reg = regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A"
    stress = float(stress_pct.iloc[-1] / 100 if not stress_pct.empty else 0.5)
    st.plotly_chart(line(probs.tail(24), "Regime backdrop", "Probability"), use_container_width=True)
    st.plotly_chart(bars(reco.head(10).assign(ticker=lambda x: x["ticker"].map(label)), "ticker", "delta", "Top active tilts"), use_container_width=True)
    st.markdown(committee_text({"top_regime": top_reg, "stress": stress, "credit": "frágil" if stress > 0.6 else "estable", "trend": "positiva" if top_reg in ["Goldilocks", "Reflation"] else "débil"}))
    st.write("### Key takeaways")
    for b in key_takeaways_from_metrics({"top_regime": top_reg, "stress": stress, "risk_on_off": 0.1, "median_pct": 50}):
        st.write(f"- {b}")

with tabs[8]:
    st.dataframe(pd.DataFrame(meta).T)
    st.dataframe(pd.DataFrame({"forbidden_tickers": [", ".join(bad) if bad else "none"], "missing_ratios": [len(ratio_missing)], "percentiles_ok": [check_percentiles(pct_dash.tail(12))], "regime_probs_ok": [check_regime_probs(probs.dropna())]}))
    st.plotly_chart(heatmap(pd.DataFrame(meta).T.select_dtypes("number").fillna(0), "Source quality/staleness"), use_container_width=True)
    st.write("### Data transparency")
    for concept, m in meta.items():
        with st.expander(concept):
            st.json(m)
