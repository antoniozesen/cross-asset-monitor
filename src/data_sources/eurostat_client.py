from __future__ import annotations

import time
import pandas as pd
import requests
import streamlit as st

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def _get(url: str, timeout: int = 20, retries: int = 3) -> requests.Response:
    last: Exception | None = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(0.7 * (i + 1))
    raise RuntimeError(f"Eurostat fetch failed: {last}")


@st.cache_data(ttl=21600)
def fetch_eurostat_series(dataset: str, filters: dict[str, str] | None = None) -> pd.DataFrame:
    filters = filters or {}
    query = "&".join([f"{k}={v}" for k, v in filters.items()])
    url = f"{BASE}/{dataset}?{query}" if query else f"{BASE}/{dataset}"
    try:
        js = _get(url).json()
        vals = js.get("value", {})
        if not vals:
            return pd.DataFrame(columns=["value"])
        times = js.get("dimension", {}).get("time", {}).get("category", {}).get("index", {})
        rev = {v: k for k, v in times.items()}
        out = pd.DataFrame({"idx": list(vals.keys()), "value": list(vals.values())})
        out["idx"] = out["idx"].astype(int)
        out["date"] = out["idx"].map(rev)
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        return out[["date", "value"]].dropna().set_index("date").sort_index()
    except Exception:
        return pd.DataFrame(columns=["value"])
