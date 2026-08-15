"""
CloudGuard Rule-Based Detection Engine

Each rule is a pure function that takes a RuntimeEvent and returns a DetectionResult or None.
Rules are composable and explainable by design.

Detection Rules implemented:
  RULE-001: Suspicious Shell Execution
  RULE-002: Reverse Shell Indicator
  RULE-003: Privilege Escalation Indicator
  RULE-004: Suspicious External Connection
  RULE-005: Cryptomining Behavior
  RULE-006: Rapid File Modification
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, timezone


# ─── Detection Result Dataclass ───────────────────────────────────────────────

@dataclass
class DetectionResult:
    """Structured result from a detection rule."""
    triggered: bool
    rule_id: str
    rule_name: str
    severity: str           # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float       # 0.0–1.0
    risk_contribution: float  # points added to risk score
    explanation: str        # human-readable reason (for viva/transparency)
    indicators: List[str]   # specific evidence strings
    mitre_technique: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    recommended_actions: List[str] = field(default_factory=list)

    def __bool__(self):
        return self.triggered


# ─── Known suspicious shells ─────────────────────────────────────────────────

SUSPICIOUS_SHELLS = {"bash", "sh", "zsh", "ash", "dash", "ksh", "csh", "tcsh", "fish"}

# ─── Known suspicious processes ──────────────────────────────────────────────

SUSPICIOUS_PROCESSES = {
    "nmap", "masscan", "nc", "ncat", "netcat", "socat",
    "curl", "wget", "python", "python3", "perl", "ruby",
    "xmrig", "minerd", "cpuminer", "ccminer",  # cryptominers
    "mimikatz", "psexec",  # privilege escalation tools
}

# ─── Known cryptomining process names ────────────────────────────────────────

CRYPTOMINER_PROCESSES = {"xmrig", "minerd", "cpuminer", "ccminer", "ethminer", "cgminer"}

# ─── Suspicious destination ports ────────────────────────────────────────────

CRYPTOMINING_PORTS = {3333, 4444, 5555, 7777, 8888, 14444, 14433, 45560, 3032}

# ─── Sensitive file paths ─────────────────────────────────────────────────────

SENSITIVE_PATHS = {"/etc/passwd", "/etc/shadow", "/etc/sudoers", "/root/", "/proc/", "/sys/"}


# ─── RULE 001: Suspicious Shell Execution ────────────────────────────────────

def rule_suspicious_shell(event) -> DetectionResult:
    """
    RULE-001: Detect unexpected shell execution inside a container.

    Triggers when:
    - event_type is PROCESS_EXEC or SHELL_EXEC
    - process_name is a known shell binary

    Severity escalates if parent process is suspicious.
    """
    triggered = False
    indicators = []
    severity = "MEDIUM"
    confidence = 0.7
    risk = 20.0

    if event.event_type not in ("PROCESS_EXEC", "SHELL_EXEC"):
        return DetectionResult(False, "RULE-001", "Suspicious Shell Execution",
                               "LOW", 0.0, 0.0, "Event type not applicable", [])

    proc = (event.process_name or "").lower().split("/")[-1]
    if proc in SUSPICIOUS_SHELLS:
        triggered = True
        indicators.append(f"Shell process detected: {proc}")

        # Escalate if parent is also suspicious
        parent = (event.parent_process or "").lower().split("/")[-1]
        if parent in SUSPICIOUS_PROCESSES or parent in SUSPICIOUS_SHELLS:
            severity = "HIGH"
            confidence = 0.85
            risk = 30.0
            indicators.append(f"Suspicious parent process: {parent}")

        # Escalate if running as root
        if event.user_uid == 0 or event.user == "root":
            severity = "HIGH"
            risk += 10.0
            indicators.append("Shell running as root user")

    return DetectionResult(
        triggered=triggered,
        rule_id="RULE-001",
        rule_name="Suspicious Shell Execution",
        severity=severity,
        confidence=confidence,
        risk_contribution=risk if triggered else 0.0,
        explanation=(
            f"Unexpected shell '{proc}' was executed inside container. "
            "Shells inside containers often indicate interactive access or malicious activity."
        ) if triggered else "No suspicious shell detected",
        indicators=indicators,
        mitre_technique="Command and Scripting Interpreter: Unix Shell",
        mitre_technique_id="T1059.004",
        recommended_actions=[
            "Investigate why a shell was executed in this container",
            "Check parent process lineage",
            "Review container image for shell binaries",
        ],
    )


# ─── RULE 002: Reverse Shell Indicator ───────────────────────────────────────

def rule_reverse_shell(event, recent_shell_in_container: bool = False) -> DetectionResult:
    """
    RULE-002: Detect reverse shell indicators.

    Triggers when:
    - A shell process has an outbound network connection
    - OR NET_CONNECT event originates from a shell process to unusual destination
    - recent_shell_in_container: True if a shell was seen recently in the same container
    """
    triggered = False
    indicators = []
    severity = "CRITICAL"
    confidence = 0.80
    risk = 45.0

    proc = (event.process_name or "").lower().split("/")[-1]
    is_shell = proc in SUSPICIOUS_SHELLS

    if event.event_type == "NET_CONNECT":
        if is_shell and event.destination_ip:
            triggered = True
            indicators.append(f"Shell process '{proc}' initiated outbound connection")
            indicators.append(f"Destination: {event.destination_ip}:{event.destination_port}")
        elif recent_shell_in_container and event.destination_ip:
            # Outbound connection shortly after shell execution in same container
            triggered = True
            confidence = 0.65
            risk = 35.0
            indicators.append("Outbound connection following shell execution in container")
            indicators.append(f"Destination: {event.destination_ip}:{event.destination_port}")

    elif event.event_type in ("PROCESS_EXEC", "SHELL_EXEC") and is_shell:
        if event.destination_ip:
            triggered = True
            indicators.append(f"Shell process with embedded network destination: {event.destination_ip}")

    return DetectionResult(
        triggered=triggered,
        rule_id="RULE-002",
        rule_name="Reverse Shell Indicator",
        severity=severity if triggered else "LOW",
        confidence=confidence if triggered else 0.0,
        risk_contribution=risk if triggered else 0.0,
        explanation=(
            "A shell process initiated an outbound network connection, which is a "
            "strong indicator of a reverse shell. Attacker may have gained remote access."
        ) if triggered else "No reverse shell indicators",
        indicators=indicators,
        mitre_technique="Command and Scripting Interpreter",
        mitre_technique_id="T1059",
        recommended_actions=[
            "Immediately investigate outbound connection destination",
            "Check if destination IP is known malicious",
            "Consider isolating container",
            "Capture network traffic for forensic analysis",
        ],
    )


# ─── RULE 003: Privilege Escalation Indicator ────────────────────────────────

def rule_privilege_escalation(event) -> DetectionResult:
    """
    RULE-003: Detect privilege escalation attempts.

    Triggers when:
    - Unexpected root execution (UID 0) for non-system processes
    - PRIV_CHANGE event type
    - Suspicious processes running as root
    """
    triggered = False
    indicators = []
    severity = "HIGH"
    confidence = 0.75
    risk = 30.0

    proc = (event.process_name or "").lower().split("/")[-1]

    if event.event_type == "PRIV_CHANGE":
        triggered = True
        indicators.append("Privilege change event detected")
        severity = "HIGH"
        risk = 35.0

    elif event.event_type in ("PROCESS_EXEC", "SHELL_EXEC"):
        if event.user_uid == 0 or event.user == "root":
            if proc in SUSPICIOUS_PROCESSES or proc in SUSPICIOUS_SHELLS:
                triggered = True
                indicators.append(f"Suspicious process '{proc}' running as root (UID 0)")
                severity = "HIGH"

        if "sudo" in (event.command_line or "").lower():
            triggered = True
            indicators.append("sudo command detected in container")
            risk += 10.0

        if "su " in (event.command_line or "").lower():
            triggered = True
            indicators.append("su command detected in container")

    return DetectionResult(
        triggered=triggered,
        rule_id="RULE-003",
        rule_name="Privilege Escalation Indicator",
        severity=severity if triggered else "LOW",
        confidence=confidence if triggered else 0.0,
        risk_contribution=risk if triggered else 0.0,
        explanation=(
            "Privilege escalation behavior detected. A process is attempting to gain "
            "elevated privileges within the container."
        ) if triggered else "No privilege escalation indicators",
        indicators=indicators,
        mitre_technique="Privilege Escalation",
        mitre_technique_id="T1068",
        recommended_actions=[
            "Verify if root access is expected for this container",
            "Review container capabilities and seccomp profile",
            "Check if container is running with --privileged flag",
        ],
    )


# ─── RULE 004: Suspicious External Connection ────────────────────────────────

def rule_suspicious_external_connection(event, known_destinations: set = None) -> DetectionResult:
    """
    RULE-004: Detect containers communicating with unexpected external destinations.

    Triggers when:
    - Outbound connection to unknown/private-range-external IP
    - Connection to unusual ports
    """
    triggered = False
    indicators = []
    severity = "MEDIUM"
    confidence = 0.65
    risk = 15.0

    known_destinations = known_destinations or set()

    if event.event_type != "NET_CONNECT":
        return DetectionResult(False, "RULE-004", "Suspicious External Connection",
                               "LOW", 0.0, 0.0, "Not a network event", [])

    dst_ip = event.destination_ip or ""
    dst_port = event.destination_port or 0

    # Skip internal/loopback addresses
    if dst_ip.startswith(("127.", "10.", "172.16.", "172.17.", "192.168.", "::1")):
        return DetectionResult(False, "RULE-004", "Suspicious External Connection",
                               "LOW", 0.0, 0.0, "Internal network address — not suspicious", [])

    if dst_ip and dst_ip not in known_destinations:
        triggered = True
        indicators.append(f"Connection to previously unseen destination: {dst_ip}:{dst_port}")

        # Escalate for unusual ports
        unusual_ports = {4444, 6666, 9999, 31337, 1337, 1234}
        if dst_port in unusual_ports:
            severity = "HIGH"
            confidence = 0.80
            risk = 25.0
            indicators.append(f"Unusual destination port: {dst_port}")

    return DetectionResult(
        triggered=triggered,
        rule_id="RULE-004",
        rule_name="Suspicious External Connection",
        severity=severity if triggered else "LOW",
        confidence=confidence if triggered else 0.0,
        risk_contribution=risk if triggered else 0.0,
        explanation=(
            f"Container initiated connection to unknown external IP {dst_ip}:{dst_port}. "
            "This may indicate data exfiltration or C2 communication."
        ) if triggered else "Connection to known destination",
        indicators=indicators,
        mitre_technique="Exfiltration Over C2 Channel",
        mitre_technique_id="T1041",
        recommended_actions=[
            "Investigate destination IP reputation",
            "Check if connection is expected for this service",
            "Block outbound connection if malicious",
        ],
    )


# ─── RULE 005: Cryptomining Behavior ─────────────────────────────────────────

def rule_cryptomining(event, cpu_percent: float = 0.0) -> DetectionResult:
    """
    RULE-005: Detect cryptomining behavior.

    Triggers on combination of:
    - Known miner process name
    - OR high CPU with connection to known mining ports
    - Does NOT rely solely on process name (as spec requires)
    """
    triggered = False
    indicators = []
    severity = "HIGH"
    confidence = 0.70
    risk = 35.0

    proc = (event.process_name or "").lower().split("/")[-1]
    dst_port = event.destination_port or 0

    # Known miner process — strong signal
    if proc in CRYPTOMINER_PROCESSES:
        triggered = True
        confidence = 0.90
        risk = 45.0
        indicators.append(f"Known cryptominer process: {proc}")

    # Mining pool port + network connection (process-name-independent)
    if event.event_type == "NET_CONNECT" and dst_port in CRYPTOMINING_PORTS:
        triggered = True
        indicators.append(f"Connection to common mining pool port: {dst_port}")
        if cpu_percent > 80:
            confidence = 0.85
            risk = 50.0
            indicators.append(f"High CPU usage correlated: {cpu_percent:.1f}%")

    # High CPU without typical system processes
    if cpu_percent > 90 and event.event_type == "PROCESS_EXEC":
        if proc not in {"java", "node", "python", "python3"}:
            triggered = True
            confidence = 0.55
            risk = 20.0
            indicators.append(f"Abnormally high CPU ({cpu_percent:.1f}%) from unknown process: {proc}")

    return DetectionResult(
        triggered=triggered,
        rule_id="RULE-005",
        rule_name="Cryptomining Behavior",
        severity=severity if triggered else "LOW",
        confidence=confidence if triggered else 0.0,
        risk_contribution=risk if triggered else 0.0,
        explanation=(
            "Cryptomining behavior detected based on process characteristics, "
            "network activity to mining pools, and/or abnormal CPU usage."
        ) if triggered else "No cryptomining indicators",
        indicators=indicators,
        mitre_technique="Resource Hijacking",
        mitre_technique_id="T1496",
        recommended_actions=[
            "Terminate suspicious mining process",
            "Block connections to mining pools",
            "Investigate container image source",
        ],
    )


# ─── RULE 006: Rapid File Modification ───────────────────────────────────────

def rule_rapid_file_modification(event, file_mod_rate_per_minute: float = 0.0) -> DetectionResult:
    """
    RULE-006: Detect unusually high file modification activity.

    High file modification rate is a behavioral indicator for:
    - Ransomware-like activity
    - Bulk data destruction
    - Log tampering

    Triggers on:
    - file_mod_rate_per_minute > threshold
    - OR modification of sensitive system files
    """
    triggered = False
    indicators = []
    severity = "HIGH"
    confidence = 0.75
    risk = 30.0

    RAPID_MOD_THRESHOLD = 50.0  # modifications per minute

    if event.event_type not in ("FILE_MODIFY", "FILE_DELETE", "FILE_CREATE"):
        return DetectionResult(False, "RULE-006", "Rapid File Modification",
                               "LOW", 0.0, 0.0, "Not a file event", [])

    file_path = event.file_path or ""

    # High file modification rate
    if file_mod_rate_per_minute > RAPID_MOD_THRESHOLD:
        triggered = True
        indicators.append(f"File modification rate: {file_mod_rate_per_minute:.0f}/min (threshold: {RAPID_MOD_THRESHOLD})")
        if file_mod_rate_per_minute > 200:
            severity = "CRITICAL"
            confidence = 0.90
            risk = 55.0
            indicators.append("Extremely high file modification rate — possible ransomware")

    # Modification of sensitive files
    for sensitive in SENSITIVE_PATHS:
        if file_path.startswith(sensitive):
            triggered = True
            severity = "HIGH"
            confidence = 0.80
            risk = max(risk, 35.0)
            indicators.append(f"Modification of sensitive path: {file_path}")
            break

    return DetectionResult(
        triggered=triggered,
        rule_id="RULE-006",
        rule_name="Rapid File Modification",
        severity=severity if triggered else "LOW",
        confidence=confidence if triggered else 0.0,
        risk_contribution=risk if triggered else 0.0,
        explanation=(
            "Unusually high file modification activity detected. This pattern is "
            "consistent with ransomware-like behavior, bulk data destruction, or exfiltration."
        ) if triggered else "Normal file activity",
        indicators=indicators,
        mitre_technique="Data Encrypted for Impact",
        mitre_technique_id="T1486",
        recommended_actions=[
            "Immediately snapshot affected volume",
            "Check file integrity",
            "Consider isolating container to prevent further modifications",
            "Investigate process responsible for modifications",
        ],
    )


# ─── Rule Registry ────────────────────────────────────────────────────────────

ALL_RULES = [
    rule_suspicious_shell,
    rule_reverse_shell,
    rule_privilege_escalation,
    rule_suspicious_external_connection,
    rule_cryptomining,
    rule_rapid_file_modification,
]

RULE_METADATA = {
    "RULE-001": {"name": "Suspicious Shell Execution", "enabled": True},
    "RULE-002": {"name": "Reverse Shell Indicator", "enabled": True},
    "RULE-003": {"name": "Privilege Escalation Indicator", "enabled": True},
    "RULE-004": {"name": "Suspicious External Connection", "enabled": True},
    "RULE-005": {"name": "Cryptomining Behavior", "enabled": True},
    "RULE-006": {"name": "Rapid File Modification", "enabled": True},
}
