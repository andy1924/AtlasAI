# CloudGuard — AI-Assisted Cloud-Native Runtime Threat Detection Platform

**CloudGuard** is a cloud-native runtime threat detection and automated response platform designed for final-year Computer Engineering projects, viva demonstrations, and technical interviews.

---

## 1. Overview & Architecture

```text
                    CLOUD / LOCAL LAB
                           |
             +-------------+-------------+
             |             |             |
        Container A   Container B   Container C
             |             |             |
             +-------------+-------------+
                           |
                           v
                 Runtime Telemetry Layer
                           |
                     Falco / eBPF
                           |
                           v
                  Event Normalizer
                           |
             +-------------+-------------+
             |                           |
             v                           v
      Rule-Based Engine            ML Engine
             |                           |
             +-------------+-------------+
                           |
                           v
                   Threat Correlation & Risk Scoring
                           |
                           v
                  Incident Management & Response
                           |
                      SOC Dashboard
```

---

## 2. Detection Rules Implemented

| Rule ID | Rule Name | MITRE ATT&CK Mapping | Description |
|---------|-----------|-----------------------|-------------|
| **RULE-001** | Suspicious Shell Execution | `T1059.004` Unix Shell | Detects unexpected interactive shell spawns (`bash`, `sh`, `zsh`) inside running containers. |
| **RULE-002** | Reverse Shell Indicator | `T1059` Command Interpreter | Detects shell processes opening outbound connections to unusual IPs/ports (`4444`, `1337`). |
| **RULE-003** | Privilege Escalation | `T1068` Privilege Escalation | Detects processes escalating to `root` (UID 0) or executing `sudo`/`su` inside container boundaries. |
| **RULE-004** | Suspicious External Connection | `T1041` Exfiltration Over C2 | Detects outbound connections to unknown external IPs or non-standard ports. |
| **RULE-005** | Cryptomining Behavior | `T1496` Resource Hijacking | Detects known miner processes (`xmrig`), mining pool port connections, and abnormal CPU utilization. |
| **RULE-006** | Rapid File Modification | `T1486` Data Encrypted for Impact | Detects high file modification rates (>50 mods/min) consistent with ransomware or log tampering. |

---

## 3. Technology Stack

* **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2
* **Database**: SQLite (Local Dev) / PostgreSQL (Production)
* **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Recharts, Lucide Icons
* **Machine Learning**: Scikit-Learn (Isolation Forest), Pandas, NumPy

---

## 4. Quick Start (Local Development)

### Backend Setup
```bash
cd cloudguard/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at: `http://localhost:8000/api/docs`

### Frontend Setup
```bash
cd cloudguard/frontend
npm install
npm run dev
```
Dashboard will be available at: `http://localhost:3000`

---

## 5. Academic Demo & Viva Scenarios

Navigate to `http://localhost:3000/demo` or use the API:
```bash
# Trigger Reverse Shell scenario
curl -X POST http://localhost:8000/api/demo/simulate/reverse_shell

# Run all 6 scenarios in sequence
curl -X POST http://localhost:8000/api/demo/simulate-all
```
