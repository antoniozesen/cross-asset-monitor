from __future__ import annotations
import pandas as pd
import numpy as np


def to_monthly_last(df: pd.DataFrame) -> pd.DataFrame:
    return df.resample("M").last().dropna(how="all")


def pct_rank(s: pd.Series, window: int = 120) -> pd.Series:
    return s.rolling(window).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100, raw=False).clip(0, 100)


def safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    out = a.align(b, join="inner")
    return (out[0] / out[1]).replace([np.inf, -np.inf], np.nan)


def fmt(x: float, unit: str = "") -> str:
    if pd.isna(x):
        return "—"
    return f"{x:,.2f}{unit}"


def non_nan(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace([np.inf, -np.inf], np.nan).dropna(how="all")


def annualized_vol(ret: pd.Series, window: int = 12) -> pd.Series:
    return ret.rolling(window).std() * np.sqrt(12)
