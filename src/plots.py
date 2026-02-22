from __future__ import annotations
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def line(df: pd.DataFrame, title: str, y_title: str = ""):
    fig = px.line(df, title=title)
    fig.update_layout(height=280, yaxis_title=y_title, margin=dict(l=10,r=10,t=40,b=10))
    return fig


def heatmap(df: pd.DataFrame, title: str):
    fig = go.Figure(data=go.Heatmap(z=df.values, x=df.columns, y=df.index, colorscale="RdYlGn"))
    fig.update_layout(title=title, height=320, margin=dict(l=10,r=10,t=40,b=10))
    return fig


def bars(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None):
    fig = px.bar(df, x=x, y=y, color=color, title=title)
    fig.update_layout(height=300, margin=dict(l=10,r=10,t=40,b=10))
    return fig
