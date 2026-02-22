from __future__ import annotations
import pandas as pd
import streamlit as st
from fredapi import Fred


@st.cache_data(ttl=21600)
def fetch_fred_series(series_id: str, start: str, end: str | None = None) -> pd.DataFrame:
    key = st.secrets["FRED_API_KEY"]
    fred = Fred(api_key=key)
    ser = fred.get_series(series_id, observation_start=start, observation_end=end)
    if ser is None or ser.empty:
        return pd.DataFrame(columns=["value"])
    df = ser.to_frame("value")
    df.index = pd.to_datetime(df.index)
    return df
