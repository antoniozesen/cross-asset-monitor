from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.covariance import LedoitWolf
from src.config import PROFILE_ANCHORS


def recommend_weights(monthly_ret: pd.DataFrame, profile: str, regime_probs: pd.Series, stress: float, flex: float = 0.10) -> pd.DataFrame:
    anchor = PROFILE_ANCHORS[profile]
    eq = [c for c in ["SPY", "VGK", "EWJ", "IEMG", "IVE", "IVW", "CV9.PA", "CG9.PA"] if c in monthly_ret.columns]
    bd = [c for c in ["SHY", "IEI", "IEF", "TLT", "LQD", "HYG", "EM13.MI", "CBE7.AS", "LYXD.DE", "IEAC.L", "IHYG.L"] if c in monthly_ret.columns]
    gd = [c for c in ["GLD"] if c in monthly_ret.columns]
    investable = eq + bd + gd
    r = monthly_ret[investable].dropna(how="any").tail(120)
    if r.empty:
        return pd.DataFrame({"ticker": investable, "weight": 0.0, "anchor": 0.0, "delta": 0.0})
    mu = r.mean() * (1 - 0.5) + r.tail(12).mean() * 0.5
    cov = pd.DataFrame(LedoitWolf().fit(r.values).covariance_, index=r.columns, columns=r.columns)
    risk = pd.Series(np.diag(cov), index=r.columns)
    score = mu - 0.5 * risk
    if stress > 0.6 and "HYG" in score.index:
        score["HYG"] -= 0.05
    w = score.clip(lower=0)
    w = w / w.sum()
    def scale(bucket, target):
        s = w[bucket].sum()
        return w[bucket] * (target / s if s > 0 else 0)
    we = scale(eq, anchor["equity"] + flex * (regime_probs.get("Goldilocks", 0) - regime_probs.get("Slowdown", 0)))
    wb = scale(bd, anchor["bonds"] + flex * (regime_probs.get("Slowdown", 0) + regime_probs.get("Stagflation", 0) - 0.5))
    wg = scale(gd, anchor["gold"])
    w_all = pd.concat([we, wb, wg]).clip(0, 0.25)
    w_all = w_all / w_all.sum()
    out = pd.DataFrame({"ticker": w_all.index, "weight": w_all.values})
    out["anchor"] = out["ticker"].map({**{t: anchor["equity"]/max(len(eq),1) for t in eq}, **{t: anchor["bonds"]/max(len(bd),1) for t in bd}, **{t: anchor["gold"]/max(len(gd),1) for t in gd}})
    out["delta"] = out["weight"] - out["anchor"]
    return out.sort_values("weight", ascending=False)
