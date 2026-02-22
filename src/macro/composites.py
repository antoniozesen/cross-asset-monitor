from __future__ import annotations

import pandas as pd


def build_composites(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    x = df.copy()
    x["contribution"] = x["value_t"] * x["weight"]
    grp = x.groupby(["date", "country", "pillar", "type", "timing"], as_index=False)["contribution"].sum()

    comp = grp.pivot_table(index="date", columns=["country", "pillar"], values="contribution")
    comp.columns = [f"{c[0]}|{c[1]}" for c in comp.columns]

    hs = x.groupby(["date", "country", "type"], as_index=False)["contribution"].mean().pivot_table(index="date", columns=["country", "type"], values="contribution")
    hs.columns = [f"{c[0]}|{c[1]}" for c in hs.columns]

    timing = x.groupby(["date", "country", "timing"], as_index=False)["contribution"].mean().pivot_table(index="date", columns=["country", "timing"], values="contribution")
    timing.columns = [f"{c[0]}|{c[1]}" for c in timing.columns]

    out = comp.join(hs, how="outer").join(timing, how="outer").sort_index().resample("D").ffill()
    contrib = x[["date", "country", "display_name", "type", "timing", "weight", "value_t", "contribution", "source"]].copy()
    return out, contrib
