from __future__ import annotations

import numpy as np
import pandas as pd


def _softmax(v: np.ndarray) -> np.ndarray:
    e = np.exp(v - np.max(v, axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def regime_probabilities(growth_z: pd.Series, infl_z: pd.Series, sigma: float = 1.0) -> pd.DataFrame:
    df = pd.concat([growth_z.rename("growth_z"), infl_z.rename("infl_z")], axis=1).dropna()
    if df.empty:
        return pd.DataFrame(columns=["Reflation", "Goldilocks", "Stagflation", "Slowdown"]) 

    centers = {
        "Reflation": (1.0, 1.0),
        "Goldilocks": (1.0, -1.0),
        "Stagflation": (-1.0, 1.0),
        "Slowdown": (-1.0, -1.0),
    }
    scores = []
    names = []
    for n, (cx, cy) in centers.items():
        d2 = (df["growth_z"] - cx) ** 2 + (df["infl_z"] - cy) ** 2
        scores.append((-(d2) / (2 * sigma * sigma)).values)
        names.append(n)
    p = _softmax(np.vstack(scores).T)
    out = pd.DataFrame(p * 100, index=df.index, columns=names)
    out["Reflation_prob"] = out["Reflation"]
    out["Slowdown_prob"] = out["Slowdown"]
    return out
