from __future__ import annotations
import pandas as pd
import numpy as np
from src.utils import to_monthly_last, annualized_vol, pct_rank


def build_market_features(px: pd.DataFrame) -> dict[str, pd.DataFrame]:
    daily_ret = px.pct_change()
    monthly_px = to_monthly_last(px)
    monthly_ret = monthly_px.pct_change()
    vol_1m = daily_ret.rolling(21).std() * np.sqrt(252)
    vol_3m = daily_ret.rolling(63).std() * np.sqrt(252)
    vol_12m = daily_ret.rolling(252).std() * np.sqrt(252)
    dd = px / px.cummax() - 1
    rolling_mdd_36m = dd.rolling(756).min()
    pct = monthly_ret.apply(pct_rank)
    return {
        "px": px, "daily_ret": daily_ret, "monthly_px": monthly_px, "monthly_ret": monthly_ret,
        "vol_1m": vol_1m, "vol_3m": vol_3m, "vol_12m": vol_12m, "drawdown": dd,
        "rolling_mdd_36m": rolling_mdd_36m, "monthly_vol_12m": monthly_ret.apply(annualized_vol),
        "ret_pct": pct,
    }
