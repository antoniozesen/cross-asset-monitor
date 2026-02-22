from __future__ import annotations
import streamlit as st
import pandas as pd

from src.config import ALLOWED_TICKERS, TICKER_NAMES, RATIO_PAIRS
from src.data_yf import fetch_prices
from src.data_extra import resolve_series
from src.features import build_market_features
from src.regime import infer_regime
from src.signals import build_signals
from src.portfolio import recommend_weights
from src.plots import line, heatmap, bars
from src.utils import pct_rank, safe_div
from src.narrative import key_takeaways_from_metrics, committee_text
from src.diagnostics import check_allowed_tickers, check_percentiles, check_regime_probs, check_required_ratios

st.set_page_config(page_title="Cross-Asset Market Monitor", layout="wide")
st.title("Cross-Asset Market Monitor")

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

macro = {}
meta = {}
for concept in ["us_2y", "us_10y", "us_real_10y", "hy_oas", "ig_oas", "euro_inflation", "euro_unemployment"]:
    df, m = resolve_series(concept, "global", str(start), provider_flags=provider_flags)
    macro[concept] = df
    meta[concept] = m

macro_df = pd.DataFrame(index=monthly.index)
macro_df["growth"] = monthly.get("SPY", pd.Series(index=monthly.index)).rolling(6).mean()
macro_df["inflation"] = macro.get("euro_inflation", pd.DataFrame(columns=["value"]))["value"].reindex(monthly.index)
macro_df["real_rates"] = macro.get("us_real_10y", pd.DataFrame(columns=["value"]))["value"].reindex(monthly.index)
macro_df["slope"] = (macro.get("us_10y", pd.DataFrame(columns=["value"]))["value"] - macro.get("us_2y", pd.DataFrame(columns=["value"]))["value"]).reindex(monthly.index)
macro_df["stress"] = macro.get("hy_oas", pd.DataFrame(columns=["value"]))["value"].reindex(monthly.index)
probs, regime_state = infer_regime(macro_df)
signals = build_signals(features)

benchmark_6040 = 0.6 * monthly.get("SPY", 0) + 0.4 * monthly.get("IEF", 0)
reco = recommend_weights(monthly, profile, probs.dropna().iloc[-1] if not probs.dropna().empty else pd.Series(), float(pct_rank(macro_df["stress"]).dropna().iloc[-1] / 100 if not pct_rank(macro_df["stress"]).dropna().empty else 0.5), flex=flex)

pct_dash = pd.DataFrame({
    "SPY": pct_rank((1 + monthly.get("SPY", 0)).cumprod()),
    "VGK": pct_rank((1 + monthly.get("VGK", 0)).cumprod()),
    "HYG/LQD": pct_rank(safe_div(features["monthly_px"].get("HYG", pd.Series()), features["monthly_px"].get("LQD", pd.Series()))),
    "US 10Y": pct_rank(macro_df["slope"]),
}).dropna(how="all")

bad = check_allowed_tickers(tickers)
ratio_missing = check_required_ratios(prices)

tabs = st.tabs(["Overview", "Regime", "Markets", "Signals", "Comparatives", "Valuation", "Allocation", "Narrative", "Sources"])

with tabs[0]:
    cols = st.columns(5)
    for i, (k, v) in enumerate({"Assets": prices.shape[1], "Obs": prices.shape[0], "Regime": regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A", "Missing ratios": len(ratio_missing), "Forbidden tickers": len(bad)}.items()):
        cols[i].metric(k, v)
    st.plotly_chart(heatmap(pct_dash.tail(12).T.fillna(50), "Cross-Asset Percentile Dashboard (0-100)"), use_container_width=True)
    st.plotly_chart(line(probs.tail(12), "Regime probabilities (1y)", "Probability"), use_container_width=True)
    st.plotly_chart(line(features["drawdown"][["SPY", "VGK", "IEMG"]].dropna(), "Drawdowns: SPY/VGK/IEMG", "%"), use_container_width=True)
    st.plotly_chart(line(features["vol_12m"][["SPY", "TLT", "HYG"]].dropna(), "12m vol: SPY/TLT/HYG", "% ann"), use_container_width=True)
    st.plotly_chart(line(features["monthly_px"][["^GSPC", "^STOXX", "^N225"]].dropna(), "Indices: ^GSPC + ^STOXX + ^N225", "Level"), use_container_width=True)
    st.plotly_chart(line(features["monthly_px"][["EURUSD=X", "USDJPY=X"]].dropna(), "FX: EURUSD=X + USDJPY=X", "Level"), use_container_width=True)
    for b in key_takeaways_from_metrics({"top_regime": regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A", "stress": 0.5, "risk_on_off": 0.1, "median_pct": 50}):
        st.write(f"- {b}")

with tabs[1]:
    st.plotly_chart(line(probs.tail(180), "Regime probabilities (15y)", "Probability"), use_container_width=True)
    st.area_chart(probs.tail(12))
    st.plotly_chart(line(macro_df[["growth", "inflation", "real_rates", "slope", "stress"]], "Regime drivers", "z/level"), use_container_width=True)
    st.dataframe(probs.tail(12).round(3))
    st.write("### Key takeaways")
    st.write(f"- Latest state: {regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else 'N/A'}.")
    st.write(f"- Probability sum check: {'pass' if check_regime_probs(probs.dropna()) else 'fail'}.")
    st.write("- Anti flip-flop smoothing via EMA(3) applied.")

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
    st.plotly_chart(line(features["monthly_px"][b].dropna(how="all"), f"{group} levels (ticker + name)", "Level"), use_container_width=True)
    st.plotly_chart(heatmap(features["monthly_ret"][b].tail(12).T.fillna(0), f"{group} monthly return heatmap"), use_container_width=True)
    latest = features["monthly_ret"][b].tail(1).T.reset_index()
    latest.columns = ["ticker", "ret"]
    st.plotly_chart(bars(latest.sort_values("ret"), "ticker", "ret", f"{group} latest monthly return"), use_container_width=True)
    st.write("- Key takeaways computed from trailing returns, vol, and drawdowns.")

with tabs[3]:
    latest_s = signals[signals["date"] == signals["date"].max()]
    st.plotly_chart(bars(latest_s.sort_values("mom_12m"), "ticker", "mom_12m", "Momentum 12m by ticker"), use_container_width=True)
    st.plotly_chart(bars(latest_s.sort_values("vol_12m"), "ticker", "vol_12m", "Vol 12m by ticker"), use_container_width=True)
    hm = latest_s.set_index("ticker")[["mom_pct", "vol_pct", "dd_pct"]]
    st.plotly_chart(heatmap(hm.T.fillna(50), "Signal percentiles"), use_container_width=True)
    st.write("- Key takeaways: top quintile momentum and low drawdown names are risk-on candidates.")

with tabs[4]:
    ratio_name = st.selectbox("Ratio", list(RATIO_PAIRS.keys()), index=0)
    a, b = RATIO_PAIRS[ratio_name]
    ratio = safe_div(features["monthly_px"][a], features["monthly_px"][b]).dropna()
    rret = ratio.pct_change()
    dfc = pd.DataFrame({"ratio": ratio, "pct": pct_rank(ratio), "ret_12m": (1+rret).rolling(12).apply(lambda x: x.prod()-1), "vol_12m": rret.rolling(12).std()*(12**0.5)})
    corr_spy = rret.rolling(12).corr(monthly.get("SPY"))
    corr_gspc = rret.rolling(12).corr(monthly.get("^GSPC"))
    corr_6040 = rret.rolling(12).corr(benchmark_6040)
    dd = ratio/ratio.cummax()-1
    st.plotly_chart(line(dfc[["ratio"]], f"{ratio_name} ratio level", "x"), use_container_width=True)
    st.plotly_chart(line(dfc[["pct"]], f"{ratio_name} percentile 0-100", "Percentile"), use_container_width=True)
    st.plotly_chart(line(dfc[["ret_12m", "vol_12m"]], f"{ratio_name} rolling 12m return/vol", "ret / vol"), use_container_width=True)
    st.plotly_chart(line(pd.DataFrame({"corr_spy": corr_spy, "corr_gspc": corr_gspc, "corr_6040": corr_6040}), f"{ratio_name} rolling correlations", "corr"), use_container_width=True)
    st.plotly_chart(line(pd.DataFrame({"rolling_mdd_36m": dd.rolling(36).min(), "since_inception_dd": dd}), f"{ratio_name} drawdowns", "drawdown"), use_container_width=True)
    st.write("- Key takeaways: ratio trend, percentile location, and correlation regime are jointly evaluated.")

with tabs[5]:
    val = pd.DataFrame({
        "us_2y": pct_rank(macro_df["slope"]),
        "us_10y": pct_rank(macro_df["real_rates"]),
        "hy_oas": pct_rank(macro_df["stress"]),
        "hyg_lqd_proxy": pct_rank(safe_div(features["monthly_px"].get("HYG", pd.Series()), features["monthly_px"].get("LQD", pd.Series()))),
    }).dropna(how="all")
    st.plotly_chart(heatmap(val.tail(36).T.fillna(50), "Valuation percentile dashboard"), use_container_width=True)
    st.plotly_chart(line(val, "Valuation percentiles", "0-100"), use_container_width=True)
    st.write("- Key takeaways: high OAS percentile signals cheaper credit but higher stress context.")

with tabs[6]:
    st.plotly_chart(bars(reco, "ticker", "weight", f"Recommended weights ({profile})"), use_container_width=True)
    st.plotly_chart(bars(reco, "ticker", "delta", "Delta vs anchor"), use_container_width=True)
    st.plotly_chart(bars(pd.DataFrame({"bucket": ["Equity", "Bonds", "Gold"], "weight": [reco[reco['ticker'].isin(['SPY','VGK','EWJ','IEMG','IVE','IVW','CV9.PA','CG9.PA'])]['weight'].sum(), reco[reco['ticker'].isin(['SHY','IEI','IEF','TLT','LQD','HYG','EM13.MI','CBE7.AS','LYXD.DE','IEAC.L','IHYG.L'])]['weight'].sum(), reco[reco['ticker'].eq('GLD')]['weight'].sum()]}), "bucket", "weight", "Bucket totals"), use_container_width=True)
    st.write("- Key takeaways: allocation is profile-sensitive and stress-aware with HY penalty in risk-off.")

with tabs[7]:
    st.plotly_chart(line(probs.tail(24), "Regime probability backdrop", "Probability"), use_container_width=True)
    st.plotly_chart(bars(reco.head(10), "ticker", "delta", "Top active tilts"), use_container_width=True)
    st.markdown(committee_text({"top_regime": regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A", "stress": 0.5, "credit": "neutral", "trend": "mixed"}))
    for b in key_takeaways_from_metrics({"top_regime": regime_state.dropna().iloc[-1] if not regime_state.dropna().empty else "N/A", "stress": 0.5, "risk_on_off": 0.1, "median_pct": 50}):
        st.write(f"- {b}")

with tabs[8]:
    st.dataframe(pd.DataFrame(meta).T)
    st.dataframe(pd.DataFrame({"forbidden_tickers": [", ".join(bad) if bad else "none"], "missing_ratios": [len(ratio_missing)], "percentiles_ok": [check_percentiles(pct_dash.tail(12))], "regime_probs_ok": [check_regime_probs(probs.dropna())]}))
    st.plotly_chart(heatmap(pd.DataFrame(meta).T.select_dtypes("number").fillna(0), "Source quality/staleness"), use_container_width=True)
    st.write("### Data transparency")
    for concept, m in meta.items():
        with st.expander(concept):
            st.json(m)
