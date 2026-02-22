from __future__ import annotations

import pandas as pd
import streamlit as st
from fredapi import Fred


def _get_fred_key() -> str | None:
    try:
        key = st.secrets.get("FRED_API_KEY", None)
    except Exception:
        return None
    if key is None:
        return None
    key = str(key).strip()
    return key or None


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_fred_series(series_id: str, start: str, end: str | None = None) -> pd.DataFrame:
    key = _get_fred_key()
    if not key:
        return pd.DataFrame(columns=["value"])

    try:
        fred = Fred(api_key=key)
        ser = fred.get_series(series_id, observation_start=start, observation_end=end)
    except BaseException:
        return pd.DataFrame(columns=["value"])

    if ser is None or ser.empty:
        return pd.DataFrame(columns=["value"])

    try:
        df = ser.to_frame("value")
        df.index = pd.to_datetime(df.index, errors="coerce")
        return df.dropna(how="all")
    except BaseException:
        return pd.DataFrame(columns=["value"])
