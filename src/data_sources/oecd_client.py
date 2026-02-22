from __future__ import annotations

import time
import pandas as pd
import requests
import streamlit as st

BASE = "https://sdmx.oecd.org/public/rest/data"


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
    raise RuntimeError(f"OECD fetch failed: {last}")


@st.cache_data(ttl=21600)
def fetch_oecd_series(dataset_key: str, start: str, end: str | None = None) -> pd.DataFrame:
    end_part = f"&endPeriod={pd.Timestamp(end).strftime('%Y-%m')}" if end else ""
    url = f"{BASE}/{dataset_key}?startPeriod={pd.Timestamp(start).strftime('%Y-%m')}{end_part}&format=csvfile"
    try:
        r = _get(url)
        df = pd.read_csv(pd.io.common.StringIO(r.text))
        time_col = next((c for c in ["TIME_PERIOD", "TIME", "Time"] if c in df.columns), None)
        val_col = next((c for c in ["OBS_VALUE", "Value", "value"] if c in df.columns), None)
        if not time_col or not val_col:
            return pd.DataFrame(columns=["value"])
        out = df[[time_col, val_col]].rename(columns={time_col: "date", val_col: "value"})
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        return out.dropna().set_index("date").sort_index()
    except Exception:
        return pd.DataFrame(columns=["value"])
