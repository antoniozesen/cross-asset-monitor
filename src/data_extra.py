from __future__ import annotations

import io
import pandas as pd
import requests
import streamlit as st

from src.config import CONCEPT_PRIORITY, MAX_MISSINGNESS_AFTER_RESAMPLE, MAX_STALENESS_DAYS_MONTHLY
from src.data_fred import fetch_fred_series


def _quality(df: pd.DataFrame) -> tuple[float, dict]:
    if df.empty:
        return 0.0, {"missingness": 1.0, "staleness_days": 9999}
    monthly = df.resample("M").last()
    miss = float(monthly.isna().mean().iloc[0])
    last_valid = monthly.dropna().index.max()
    if pd.isna(last_valid):
        return 0.0, {"missingness": 1.0, "staleness_days": 9999}
    stale = int((pd.Timestamp.utcnow().tz_localize(None) - last_valid).days)
    score = max(0.0, 1 - miss - max(0, stale - MAX_STALENESS_DAYS_MONTHLY) / 365)
    return score, {"missingness": miss, "staleness_days": stale}


def _fetch_treasury(code: str, start: str, end: str | None) -> pd.DataFrame:
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/DailyTreasuryYieldCurveRateData.csv"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        raw = pd.read_csv(io.StringIO(r.text))
        raw["Date"] = pd.to_datetime(raw["Date"], errors="coerce")
        col_map = {"DGS2": "2 Yr", "DGS3MO": "3 Mo", "DGS10": "10 Yr", "DGS30": "30 Yr"}
        col = col_map.get(code)
        if not col or col not in raw.columns:
            return pd.DataFrame(columns=["value"])
        out = raw[["Date", col]].dropna().rename(columns={"Date": "date", col: "value"}).set_index("date").sort_index()
        out = out[(out.index >= pd.Timestamp(start)) & (out.index <= pd.Timestamp(end) if end else True)]
        return out
    except Exception:
        return pd.DataFrame(columns=["value"])


def _fetch_worldbank(series_id: str, start: str, end: str | None) -> pd.DataFrame:
    try:
        country, indicator = series_id.split("|", 1)
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&per_page=20000"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or len(data) < 2:
            return pd.DataFrame(columns=["value"])
        rows = data[1]
        out = pd.DataFrame(rows)[["date", "value"]].dropna()
        out["date"] = pd.to_datetime(out["date"] + "-12-31", errors="coerce")
        out = out.dropna().set_index("date").sort_index()
        out = out[(out.index >= pd.Timestamp(start)) & (out.index <= pd.Timestamp(end) if end else True)]
        return out[["value"]]
    except Exception:
        return pd.DataFrame(columns=["value"])


def _fetch_oecd(series_id: str, start: str, end: str | None) -> pd.DataFrame:
    return pd.DataFrame(columns=["value"])


def _fetch_ecb(series_id: str, start: str, end: str | None) -> pd.DataFrame:
    return pd.DataFrame(columns=["value"])


def _fetch_bundesbank(series_id: str, start: str, end: str | None) -> pd.DataFrame:
    return pd.DataFrame(columns=["value"])


@st.cache_data(ttl=21600)
def resolve_series(concept: str, region: str, start: str, end: str | None = None, prefer_monthly: bool = True, provider_flags: dict | None = None):
    provider_flags = provider_flags or {"OECD": True, "TREASURY": True, "ECB": True, "BUNDESBANK": True, "WORLDBANK": True}
    lineage: list[dict] = []
    best_df = pd.DataFrame(columns=["value"])
    best_meta = {"concept": concept, "region": region, "source": "NONE", "series_id": "", "lineage": []}

    for candidate in CONCEPT_PRIORITY.get(concept, []):
        source, sid = candidate.split(":", 1)
        if source in provider_flags and not provider_flags[source]:
            lineage.append({"candidate": candidate, "status": "skipped", "reason": "provider disabled"})
            continue
        try:
            if source == "FRED":
                df = fetch_fred_series(sid, start, end)
            elif source == "TREASURY":
                df = _fetch_treasury(sid, start, end)
            elif source == "OECD":
                df = _fetch_oecd(sid, start, end)
            elif source == "ECB":
                df = _fetch_ecb(sid, start, end)
            elif source == "BUNDESBANK":
                df = _fetch_bundesbank(sid, start, end)
            elif source == "WORLDBANK":
                df = _fetch_worldbank(sid, start, end)
            else:
                df = pd.DataFrame(columns=["value"])

            if not df.empty:
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
            score, q = _quality(df)
            lineage.append({"candidate": candidate, "status": "ok" if score > 0 else "bad", "quality_score": score, **q})
            if score > _quality(best_df)[0]:
                best_df = df
                best_meta = {"concept": concept, "region": region, "source": source, "series_id": sid, "quality_score": score, **q}
            if score >= (1 - MAX_MISSINGNESS_AFTER_RESAMPLE):
                break
        except Exception as e:
            lineage.append({"candidate": candidate, "status": "error", "reason": str(e)})

    best_meta["lineage"] = lineage
    return best_df, best_meta
