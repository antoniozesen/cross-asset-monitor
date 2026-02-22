from __future__ import annotations

import pandas as pd


def key_takeaways_from_metrics(metrics: dict) -> list[str]:
    reg = metrics.get("top_regime", "Indeterminado")
    stress = float(metrics.get("stress", 0.5))
    risk = float(metrics.get("risk_on_off", 0.0))
    med = float(metrics.get("median_pct", 50.0))
    return [
        f"Régimen dominante: {reg}.",
        "Estrés de mercado elevado; priorizar calidad crediticia y duración defensiva." if stress > 0.60 else "Estrés contenido; se puede mantener beta cercana al ancla.",
        f"Indicador risk-on/risk-off: {risk:.2f}.",
        f"Percentil agregado transversal: {med:.1f}/100.",
    ]


def committee_text(metrics: dict) -> str:
    reg = metrics.get("top_regime", "Indeterminado")
    stress = float(metrics.get("stress", 0.5))
    credit = metrics.get("credit", "mixto")
    trend = metrics.get("trend", "mixta")
    sesgo = "neutral"
    if reg in {"Goldilocks", "Reflation"} and stress < 0.55:
        sesgo = "pro-riesgo"
    elif reg in {"Slowdown", "Stagflation"} or stress >= 0.60:
        sesgo = "defensivo"
    return (
        "### Informe del Comité de Inversión\n"
        f"**Diagnóstico:** régimen **{reg}**, estrés **{stress:.2f}**, crédito **{credit}**, tendencia **{trend}**.\n\n"
        f"**Sesgo táctico:** **{sesgo}** con disciplina de riesgo en crédito y duración."
    )


def macro_regime_section(contrib: pd.DataFrame, composites: pd.DataFrame) -> str:
    if contrib.empty or composites.empty:
        return "### MACRO REGIME\nSin datos macro suficientes para construir el bloque."
    lines = ["### MACRO REGIME"]
    countries = sorted(contrib["country"].dropna().unique().tolist())
    latest_date = composites.dropna(how="all").index.max()
    for c in countries[:5]:
        g = composites.get(f"{c}|GROWTH", pd.Series(dtype=float))
        i = composites.get(f"{c}|INFLATION", pd.Series(dtype=float))
        gz = float(g.dropna().iloc[-1]) if not g.dropna().empty else float("nan")
        iz = float(i.dropna().iloc[-1]) if not i.dropna().empty else float("nan")
        sub = contrib[contrib["country"] == c].sort_values("date").groupby("display_name").tail(1)
        top = sub.sort_values("contribution", ascending=False).head(3)
        drivers = ", ".join([f"{r.display_name} ({r.type}/{r.timing})" for r in top.itertuples()]) if not top.empty else "n/a"
        lines.append(f"- **{c}** | Growth z: {gz:.2f} | Inflation z: {iz:.2f} | Top drivers: {drivers}.")
    lines.append(f"As-of macro composites: {latest_date.date() if pd.notna(latest_date) else 'n/a'}.")
    return "\n".join(lines)
