from __future__ import annotations
import pandas as pd


def key_takeaways_from_metrics(metrics: dict) -> list[str]:
    bullets = []
    reg = metrics.get("top_regime", "Unknown")
    bullets.append(f"Dominant regime: {reg}.")
    if metrics.get("stress", 0) > 0.6:
        bullets.append("Stress is elevated; favor higher-quality bonds and limit high yield.")
    else:
        bullets.append("Stress is contained; carry and equity beta can be held close to anchor.")
    bullets.append(f"Risk-on/off score: {metrics.get('risk_on_off', 0):.2f} (positive is risk-on).")
    bullets.append(f"Global percentile median is {metrics.get('median_pct', 50):.1f}/100.")
    return bullets[:6]


def committee_text(metrics: dict) -> str:
    return (
        f"Committee brief: regime={metrics.get('top_regime','Unknown')}, stress={metrics.get('stress',0):.2f}, "
        f"credit_condition={metrics.get('credit', 'mixed')}, trend_state={metrics.get('trend', 'mixed')}."
    )
