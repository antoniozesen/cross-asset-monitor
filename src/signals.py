from __future__ import annotations
import pandas as pd
from src.utils import pct_rank


def build_signals(features: dict[str, pd.DataFrame]) -> pd.DataFrame:
    mret = features["monthly_ret"]
    vol = features["monthly_vol_12m"]
    dd = features["drawdown"].resample("M").last()
    out = []
    for t in mret.columns:
        s = pd.DataFrame(index=mret.index)
        s["ticker"] = t
        s["mom_3m"] = (1 + mret[t]).rolling(3).apply(lambda x: x.prod() - 1)
        s["mom_6m"] = (1 + mret[t]).rolling(6).apply(lambda x: x.prod() - 1)
        s["mom_12m"] = (1 + mret[t]).rolling(12).apply(lambda x: x.prod() - 1)
        s["vol_12m"] = vol[t]
        s["drawdown"] = dd[t]
        s["mom_pct"] = pct_rank(s["mom_12m"])
        s["vol_pct"] = pct_rank(s["vol_12m"])
        s["dd_pct"] = pct_rank(s["drawdown"])
        out.append(s)
    return pd.concat(out).reset_index(names="date")
