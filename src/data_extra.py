from __future__ import annotations
import pandas as pd
import requests
import streamlit as st
from src.config import CONCEPT_PRIORITY, MAX_MISSINGNESS_AFTER_RESAMPLE, MAX_STALENESS_DAYS_MONTHLY
from src.data_fred import fetch_fred_series


def _quality(df: pd.DataFrame) -> tuple[float, dict]:
    if df.empty:
        return 0.0, {"missingness": 1.0, "staleness_days": 9_999}
    monthly = df.resample("M").last()
    miss = monthly.isna().mean().iloc[0]
    stale = (pd.Timestamp.utcnow().tz_localize(None) - monthly.dropna().index.max()).days
    score = max(0.0, 1 - miss - max(0, stale - MAX_STALENESS_DAYS_MONTHLY) / 365)
    return score, {"missingness": float(miss), "staleness_days": int(stale)}


def _fetch_treasury(code: str, start: str, end: str | None) -> pd.DataFrame:
    url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/"  # best effort
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame(columns=["value"])
        df = pd.read_csv(pd.compat.StringIO(r.text))
    except Exception:
        return pd.DataFrame(columns=["value"])
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
    lineage = []
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
            else:
                df = pd.DataFrame(columns=["value"])
            score, q = _quality(df)
            lineage.append({"candidate": candidate, "status": "ok" if score > 0 else "bad", "quality_score": score, **q})
            if score > _quality(best_df)[0]:
                best_df = df
                best_meta = {"concept": concept, "region": region, "source": source, "series_id": sid, **q, "quality_score": score}
            if score >= (1 - MAX_MISSINGNESS_AFTER_RESAMPLE):
                break
        except Exception as e:
            lineage.append({"candidate": candidate, "status": "error", "reason": str(e)})
    best_meta["lineage"] = lineage
    return best_df, best_meta
