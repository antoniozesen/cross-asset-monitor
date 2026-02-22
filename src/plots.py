from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _coerce_numeric_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.replace([float("inf"), float("-inf")], pd.NA).dropna(axis=1, how="all").dropna(axis=0, how="all")
    return out


def line(df: pd.DataFrame, title: str, y_title: str = ""):
    clean = _coerce_numeric_frame(df)
    fig = go.Figure()
    if clean.empty:
        fig.add_annotation(text="No numeric data available", x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper")
    else:
        for col in clean.columns:
            fig.add_trace(go.Scatter(x=clean.index, y=clean[col], mode="lines", name=str(col)))
    fig.update_layout(title=title, height=280, yaxis_title=y_title, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def heatmap(df: pd.DataFrame, title: str):
    clean = _coerce_numeric_frame(df)
    if clean.empty:
        clean = pd.DataFrame([[0.0]], index=["No data"], columns=["No data"])
    fig = go.Figure(data=go.Heatmap(z=clean.values, x=clean.columns, y=clean.index, colorscale="RdYlGn"))
    fig.update_layout(title=title, height=320, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def bars(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None):
    clean = df.copy()
    if y in clean.columns:
        clean[y] = pd.to_numeric(clean[y], errors="coerce")
    clean = clean.dropna(subset=[x, y]) if x in clean.columns and y in clean.columns else pd.DataFrame(columns=[x, y])
    if clean.empty:
        clean = pd.DataFrame({x: ["No data"], y: [0.0]})
    fig = px.bar(clean, x=x, y=y, color=color if color in clean.columns else None, title=title)
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
    return fig
