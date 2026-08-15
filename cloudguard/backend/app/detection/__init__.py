"""Detection package init."""
from app.detection.rules import (
    rule_suspicious_shell,
    rule_reverse_shell,
    rule_privilege_escalation,
    rule_suspicious_external_connection,
    rule_cryptomining,
    rule_rapid_file_modification,
    DetectionResult,
    ALL_RULES,
    RULE_METADATA,
)
from app.detection.risk_engine import calculate_risk, RiskScore, score_to_level

__all__ = [
    "rule_suspicious_shell",
    "rule_reverse_shell",
    "rule_privilege_escalation",
    "rule_suspicious_external_connection",
    "rule_cryptomining",
    "rule_rapid_file_modification",
    "DetectionResult",
    "ALL_RULES",
    "RULE_METADATA",
    "calculate_risk",
    "RiskScore",
    "score_to_level",
]
