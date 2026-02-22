from __future__ import annotations


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
        f"**Diagnóstico macro-financiero:** el régimen estimado es **{reg}**, con una lectura de estrés en **{stress:.2f}**. "
        f"La señal de crédito se mantiene en estado **{credit}** y la tendencia agregada es **{trend}**.\n\n"
        f"**Implicación táctica:** el sesgo recomendado para el próximo rebalanceo mensual es **{sesgo}**. "
        "En términos operativos, se propone modular la exposición a renta variable alrededor del ancla de perfil, "
        "manteniendo disciplina de riesgo en crédito high yield y favoreciendo tramos de renta fija gubernamental cuando "
        "el entorno se vuelve más adverso.\n\n"
        "**Riesgos a vigilar:** (1) aceleración inesperada de inflación, (2) deterioro abrupto de spreads de crédito, "
        "(3) pérdida simultánea de tendencia en renta variable y crédito."
    )
