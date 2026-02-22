from __future__ import annotations

import numpy as np
import pandas as pd


def to_daily_ffill(s: pd.Series) -> pd.Series:
    if s.empty:
        return s
    daily = s.resample("D").ffill()
    return daily


def yoy(s: pd.Series) -> pd.Series:
    return s.pct_change(12) * 100


def mom(s: pd.Series) -> pd.Series:
    return s.pct_change(1) * 100


def zscore(s: pd.Series, window: int = 36) -> pd.Series:
    mu = s.rolling(window).mean()
    sd = s.rolling(window).std().replace(0, np.nan)
    return (s - mu) / sd


def winsorize(s: pd.Series, p: float = 0.01) -> pd.Series:
    if s.empty:
        return s
    lo, hi = s.quantile(p), s.quantile(1 - p)
    return s.clip(lo, hi)


def apply_transform(s: pd.Series, transform: str) -> pd.Series:
    if transform == "LEVEL":
        out = s
    elif transform == "yoy":
        out = yoy(s)
    elif transform == "mom":
        out = mom(s)
    elif transform.startswith("zscore_") and transform.endswith("_inv"):
        w = int(transform.split("_")[1])
        out = -zscore(s, w)
    elif transform.startswith("zscore_"):
        w = int(transform.split("_")[1])
        out = zscore(s, w)
    else:
        out = s
    return winsorize(out).dropna()
