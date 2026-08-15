"""
CloudGuard Risk Scoring Engine

Transparent, explainable risk scoring.
Every point contribution is documented so it can be defended in a viva.

Risk Scale:
  0–25    LOW
  26–50   MEDIUM
  51–75   HIGH
  76–100  CRITICAL
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RiskFactor:
    name: str
    contribution: float
    reason: str


@dataclass
class RiskScore:
    raw_score: float
    capped_score: float  # 0–100
    level: str           # LOW, MEDIUM, HIGH, CRITICAL
    factors: List[RiskFactor] = field(default_factory=list)

    @property
    def breakdown(self) -> dict:
        return {
            "score": round(self.capped_score, 1),
            "level": self.level,
            "factors": [
                {"name": f.name, "contribution": round(f.contribution, 1), "reason": f.reason}
                for f in self.factors
            ],
        }


def score_to_level(score: float) -> str:
    if score <= 25:
        return "LOW"
    elif score <= 50:
        return "MEDIUM"
    elif score <= 75:
        return "HIGH"
    else:
        return "CRITICAL"


def calculate_risk(
    rule_results: list,
    anomaly_score: Optional[float] = None,
    is_privileged: bool = False,
    is_critical_asset: bool = False,
    correlated_event_count: int = 1,
    has_external_connection: bool = False,
) -> RiskScore:
    """
    Calculate a transparent risk score from multiple contributing factors.

    Parameters
    ----------
    rule_results : list of DetectionResult
        Results from all fired detection rules.
    anomaly_score : float, optional
        ML anomaly score (0.0–1.0, higher = more anomalous).
    is_privileged : bool
        Whether the container runs in privileged mode.
    is_critical_asset : bool
        Whether the container hosts a critical service.
    correlated_event_count : int
        Number of related events in the correlation window.
    has_external_connection : bool
        Whether an external network connection was detected.
    """
    factors: List[RiskFactor] = []
    total = 0.0

    # 1. Detection rule contributions
    for result in rule_results:
        if result.triggered:
            contrib = min(result.risk_contribution, 50.0)  # cap individual rule contribution
            factors.append(RiskFactor(
                name=result.rule_name,
                contribution=contrib,
                reason=result.explanation[:120],
            ))
            total += contrib

    # 2. ML anomaly score
    if anomaly_score is not None:
        ml_contrib = anomaly_score * 25.0  # max +25 from ML
        factors.append(RiskFactor(
            name="ML Anomaly Score",
            contribution=ml_contrib,
            reason=f"Isolation Forest anomaly score: {anomaly_score:.3f}",
        ))
        total += ml_contrib

    # 3. Correlated event bonus (more correlated events = higher confidence)
    if correlated_event_count > 1:
        corr_contrib = min((correlated_event_count - 1) * 3.0, 15.0)
        factors.append(RiskFactor(
            name="Correlated Events",
            contribution=corr_contrib,
            reason=f"{correlated_event_count} related events in correlation window",
        ))
        total += corr_contrib

    # 4. Privileged container multiplier
    if is_privileged:
        priv_contrib = 15.0
        factors.append(RiskFactor(
            name="Privileged Container",
            contribution=priv_contrib,
            reason="Container runs with elevated privileges — higher blast radius",
        ))
        total += priv_contrib

    # 5. Critical asset bonus
    if is_critical_asset:
        asset_contrib = 10.0
        factors.append(RiskFactor(
            name="Critical Asset",
            contribution=asset_contrib,
            reason="Container hosts a critical service — impact is higher",
        ))
        total += asset_contrib

    # 6. External connection bonus (already partially covered by rules, but adds context)
    if has_external_connection:
        net_contrib = 5.0
        factors.append(RiskFactor(
            name="External Network Activity",
            contribution=net_contrib,
            reason="Outbound connection to external destination detected",
        ))
        total += net_contrib

    capped = min(total, 100.0)
    return RiskScore(
        raw_score=total,
        capped_score=capped,
        level=score_to_level(capped),
        factors=factors,
    )
