# Cross-Asset Market Monitor

Institutional-style Streamlit dashboard for cross-asset monitoring across equities, sectors, factors, bonds, credit, FX, commodities, macro regime, valuation, and allocation.

## What the app does
- Builds a chart-first monitor with tabs: Overview, Regime, Markets, Signals, Comparatives, Valuation, Allocation, Narrative, Sources.
- Uses **yfinance only** for market prices from the allowed ticker universe.
- Uses **FRED via fredapi** as primary macro source and resolver-based no-auth fallback adapters (OECD/ECB/Treasury/Bundesbank/World Bank hooks).
- Produces deterministic key takeaways and diagnostics.

## Deploy with GitHub Web UI + Streamlit Cloud (no terminal)
1. In GitHub, click **New repository** and create a **public** repo.
2. In the repo page, click **Add file → Upload files**.
3. Upload every file/folder from this project exactly as shown in the tree.
4. Commit upload via GitHub web UI.
5. Go to **https://share.streamlit.io/** and sign in with GitHub.
6. Click **New app**, choose your repo/branch, set main file to `app.py`.
7. In app settings, add secret:
   - `FRED_API_KEY="YOUR_KEY"`
8. Click **Deploy**.

## Troubleshooting (no terminal)
- If market charts are sparse, some tickers may have limited history in Yahoo for your selected window.
- If macro panels show warnings, provider failed or data quality/staleness thresholds triggered fallback.
- Check the **Sources** tab for lineage, fallback reasons, and quality scores.

## Data policy
- No Bloomberg, no paid APIs, no HTML scraping.
- FRED key is read only from `st.secrets["FRED_API_KEY"]`.
- Official no-auth fallback adapters are designed for SDMX/JSON/CSV APIs.

## Pitfalls avoided
- No incompatible multi-axis overlays without separate traces/panels.
- Percentiles bounded 0–100 and validated.
- Regime probabilities are smoothed, floored, and normalized to sum to one.
- Graceful degradation for missing series and insufficient history.

## References
- Hamilton, J.D. (1989). “A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle.” *Econometrica*. https://doi.org/10.2307/1912559
- Ang, A., & Bekaert, G. (2002). “International Asset Allocation with Regime Shifts.” *Review of Financial Studies*. https://doi.org/10.1093/rfs/15.4.1137
- Ledoit, O., & Wolf, M. (2004). “A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices.” *Journal of Multivariate Analysis*. https://doi.org/10.1016/S0047-259X(03)00096-4
- Rockafellar, R.T., & Uryasev, S. (2000). “Optimization of Conditional Value-at-Risk.” *Journal of Risk*.
- Jagannathan, R., & Ma, T. (2003). “Risk Reduction in Large Portfolios: Why Imposing the Wrong Constraints Helps.” *Journal of Finance*. https://doi.org/10.1111/1540-6261.00580
- Stock, J.H., & Watson, M.W. (1999). “Business cycle fluctuations in US macroeconomic time series.” *Handbook of Macroeconomics*.
- DeMiguel, V., Garlappi, L., & Uppal, R. (2009). “Optimal Versus Naive Diversification.” *Review of Financial Studies*. https://doi.org/10.1093/rfs/hhm075
- Black, F., & Litterman, R. (1992). “Global Portfolio Optimization.” *Financial Analysts Journal*.
