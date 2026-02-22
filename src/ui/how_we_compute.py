from __future__ import annotations

import streamlit as st


def render_how_we_compute() -> None:
    st.header("How we compute")
    st.markdown(
        """
### Prices & returns
- Daily return: \(r_t = P_t/P_{t-1} - 1\)
- Monthly return: last business day of month and same formula.
- Rolling volatility (annualized): \(\sigma_{12m} = std(r_{m,t-11:t})\sqrt{12}\)
- Drawdown: \(DD_t = P_t / max(P_{0:t}) - 1\)

### Macro transforms
- YoY: \(x_t/x_{t-12}-1\)
- MoM: \(x_t/x_{t-1}-1\)
- Rolling z-score: \((x_t-\mu_w)/\sigma_w\)
- Winsorization: cap tails at 1st/99th percentile.
- Frequency alignment: all series displayed on daily axis with forward fill from native frequency.

### Composites
- For each country and bucket we compute weighted sum:
\[Composite_t = \sum_i w_i z_{i,t}\]
- Hard/Soft, Leading/Coincident/Lagging are grouped from catalog taxonomy.
- Contribution = \(w_i\times z_{i,t}\).

### Regime probabilities (4 quadrants)
- Inputs: growth_z and inflation_z.
- Regime centers: Reflation (+1,+1), Goldilocks (+1,-1), Stagflation (-1,+1), Slowdown (-1,-1).
- Score: \(s_r = -((g-c_x)^2+(\pi-c_y)^2)/(2\sigma^2)\)
- Probability via softmax over 4 scores.

### Example
If growth_z=0.8 and infl_z=-0.6, distance to Goldilocks center is smallest, so Goldilocks probability is highest.
"""
    )
