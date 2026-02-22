from __future__ import annotations
import pandas as pd
from src.config import ALLOWED_TICKERS, RATIO_PAIRS


def check_allowed_tickers(tickers: list[str]) -> list[str]:
    return [t for t in tickers if t not in ALLOWED_TICKERS]


def check_percentiles(df: pd.DataFrame) -> bool:
    d = df.select_dtypes("number")
    if d.empty:
        return True
    return bool(((d >= 0) & (d <= 100)).stack().all())


def check_regime_probs(probs: pd.DataFrame) -> bool:
    if probs.empty:
        return False
    s = probs.sum(axis=1).dropna()
    return bool(((s - 1).abs() < 1e-6).all())


def check_required_ratios(prices: pd.DataFrame) -> list[str]:
    miss = []
    for name, (a, b) in RATIO_PAIRS.items():
        if a not in prices.columns or b not in prices.columns:
            miss.append(name)
    return miss
