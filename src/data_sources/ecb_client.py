from __future__ import annotations

import time
import pandas as pd
import requests
import streamlit as st

BASE = "https://data-api.ecb.europa.eu/service/data"


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
    raise RuntimeError(f"ECB fetch failed: {last}")


@st.cache_data(ttl=21600)
def fetch_ecb_series(flow: str, key: str, start: str, end: str | None = None) -> pd.DataFrame:
    end_q = f"&endPeriod={pd.Timestamp(end).strftime('%Y-%m-%d')}" if end else ""
    url = f"{BASE}/{flow}/{key}?startPeriod={pd.Timestamp(start).strftime('%Y-%m-%d')}{end_q}&format=csvdata"
    try:
        r = _get(url)
        df = pd.read_csv(pd.io.common.StringIO(r.text))
        time_col = next((c for c in ["TIME_PERIOD", "TIME", "TIME_PERIOD:Time"] if c in df.columns), None)
        val_col = next((c for c in ["OBS_VALUE", "OBS_VALUE:Value", "value"] if c in df.columns), None)
        if not time_col or not val_col:
            return pd.DataFrame(columns=["value"])
        out = df[[time_col, val_col]].rename(columns={time_col: "date", val_col: "value"})
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        return out.dropna().set_index("date").sort_index()
    except Exception:
        return pd.DataFrame(columns=["value"])
