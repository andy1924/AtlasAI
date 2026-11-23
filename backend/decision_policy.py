"""Deterministic approval policy; model prose never authorizes an action."""

import re

ACTIONS = {"REROUTE", "HOLD", "SWITCH_CARRIER", "EXPEDITE", "ESCALATE", "MONITOR"}


def requires_approval(action: str, confidence: int, severity: str) -> bool:
    return (
        action not in ACTIONS
        or action == "ESCALATE"
        or not 45 <= confidence <= 100
        or severity not in {"Low", "Medium", "None"}
    )


def parse_decision(content: str, severity: str) -> tuple[str, int, str]:
    """Missing, duplicated, or invalid fields fail closed to operator review."""
    actions = re.findall(r"^Action:\s*([A-Z_]+)\s*$", content, re.I | re.M)
    confidences = re.findall(r"^Confidence:\s*([0-9]+)\s*%?\s*$", content, re.I | re.M)
    action = actions[0].upper() if len(actions) == 1 else "ESCALATE"
    confidence = int(confidences[0]) if len(confidences) == 1 else 0
    if not 0 <= confidence <= 100:
        confidence = 0
    if requires_approval(action, confidence, severity) or "[NEEDS APPROVAL]" in content.upper():
        action = "ESCALATE"
        content += "\n[NEEDS APPROVAL] Deterministic policy requires operator review."
    return action, confidence, content
