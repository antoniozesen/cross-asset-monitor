from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture


def infer_regime(feature_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    X = feature_df.dropna().copy()
    if len(X) < 36:
        probs = pd.DataFrame(index=feature_df.index, data=np.nan, columns=["Goldilocks", "Reflation", "Slowdown", "Stagflation"])
        state = pd.Series(index=feature_df.index, data="Insufficient data")
        return probs, state
    gm = GaussianMixture(n_components=4, random_state=7)
    gm.fit(X.values)
    p = gm.predict_proba(X.values)
    p = np.clip(p, 0.02, 0.94)
    p = p / p.sum(axis=1, keepdims=True)
    probs_raw = pd.DataFrame(p, index=X.index, columns=[f"S{i}" for i in range(4)])
    growth = X.iloc[:, 0].rank(pct=True)
    infl = X.iloc[:, 1].rank(pct=True)
    labels = {}
    for c in probs_raw.columns:
        idx = probs_raw[c].idxmax()
        gh, ih = growth.loc[idx] >= 0.5, infl.loc[idx] >= 0.5
        labels[c] = "Reflation" if gh and ih else "Goldilocks" if gh else "Stagflation" if ih else "Slowdown"
    probs = probs_raw.rename(columns=labels).groupby(level=0, axis=1).sum().reindex(columns=["Goldilocks", "Reflation", "Slowdown", "Stagflation"], fill_value=0)
    probs = probs.ewm(span=3, adjust=False).mean()
    probs = probs / probs.sum(axis=1).values.reshape(-1, 1)
    state = probs.idxmax(axis=1)
    return probs.reindex(feature_df.index), state.reindex(feature_df.index)
