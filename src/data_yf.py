from __future__ import annotations
import pandas as pd
import streamlit as st
import yfinance as yf
from src.config import ALLOWED_TICKERS


@st.cache_data(ttl=21600)
def fetch_prices(tickers: list[str], start: str) -> pd.DataFrame:
    bad = [t for t in tickers if t not in ALLOWED_TICKERS]
    if bad:
        raise ValueError(f"Forbidden tickers: {bad}")
    data = yf.download(tickers=tickers, start=start, auto_adjust=True, progress=False, threads=True, timeout=20)
    if data.empty:
        return pd.DataFrame()
    px = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data.to_frame(name=tickers[0])
    return px.dropna(how="all")
