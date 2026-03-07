<div align="center">

# 🌍 AtlasAI

### Autonomous Logistics Intelligence Layer

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG_Memory-E05A2B?style=for-the-badge)](https://trychroma.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://platform.openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

*An autonomous AI agent that monitors global logistics disruptions in real time, reasons about cascading failures, retrieves historical Plans of Action from vector memory, and either self-executes mitigations or escalates to a human operator — all from a single live dashboard.*

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [API Reference](#-api-reference) • [Agent Loop](#-agent-loop) • [Memory System](#-memory--rag-system) • [Roadmap](#️-roadmap)

</div>

---

## 📌 Overview

AtlasAI is a full-stack autonomous logistics intelligence system. When a disruption event is detected — a port strike, hurricane, or geopolitical conflict — the system's LangGraph agent automatically reasons about affected shipments, retrieves similar past incidents from a ChromaDB vector memory, and formulates a mitigation plan. Low and medium severity events are handled autonomously; high severity events are escalated to a human operator for approval.

When the operator approves, the action is embedded back into ChromaDB — making the system smarter with every incident.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 Autonomous AI Agent | 4-node LangGraph loop: Observe → Reason → Decide → Act |
| 🧠 RAG Vector Memory | ChromaDB stores and retrieves historical Plans of Action via OpenAI embeddings |
| 👤 Human-in-the-Loop | HIGH severity events pause for human approval before execution |
| 🔄 Self-Learning | Approved human decisions are written back to ChromaDB for future recall |
| 🌐 OSINT News Feed | Live MediaStack API monitors disruptions across 80+ countries |
| ⚡ Chaos Injection | Manually trigger disruption events via the dashboard to simulate scenarios |
| 📊 Global Shipment Dashboard | Real-time tracking of 1,000+ shipments with live risk status |
| 🗺️ Disruption Radar | Live feed of geopolitical and natural events matched to shipment routes |

---

## 📁 Project Structure

```
AtlasAI/
│
├── backend/
│   ├── main.py               # FastAPI app — all REST endpoints
│   ├── agent.py              # LangGraph agent (Observe/Reason/Decide/Act)
│   ├── memory.py             # ChromaDB RAG memory — seed, search, learn
│   ├── state.py              # Pydantic models: Shipment, Alert, AgentState
│   ├── newsEngine.py         # MediaStack OSINT feed & disruption filter
│   ├── chaos_engine.py       # Disruption event generator
│   └── riskAnalysis.py       # Shipment risk scoring
│
├── maindata/
│   ├── simulated_shipments.json   # 1,000+ simulated shipments
│   └── LogisticSimulator.py       # Shipment data generator
│
├── chroma_db/                # Auto-generated local ChromaDB vector store
├── .env                      # API keys (never commit this)
├── requirements.txt
└── README.md
```

---

## 🏗️ Architecture

### System Flow

```
  [MediaStack OSINT]           [Frontend Dashboard]
        │                             │
        ▼                             ▼ (Trigger Chaos Event)
  newsEngine.py            POST /api/trigger-chaos
        │                             │
        └──────────┬──────────────────┘
                   ▼
          POST /api/run-agent
                   │
        ┌──────────▼──────────┐
        │   LangGraph Agent   │
        │  ┌───────────────┐  │
        │  │   OBSERVE     │  │  ← Scans At Risk shipments & active alerts
        │  └──────┬────────┘  │
        │  ┌──────▼────────┐  │
        │  │    REASON     │  │  ← GPT-4o-mini formulates failure hypothesis
        │  └──────┬────────┘  │
        │  ┌──────▼────────┐  │
        │  │    DECIDE     │  │  ← RAG retrieves historical POA from ChromaDB
        │  └──────┬────────┘  │
        │  ┌──────▼────────┐  │
        │  │      ACT      │  │  ← Auto-executes or flags [NEEDS APPROVAL]
        │  └───────────────┘  │
        └─────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
   Auto-Rerouted      Pending Approval
  (Medium / Low)       (High Severity)
                            │
                  POST /api/approve-actions
                            │
                   ┌────────▼────────┐
                   │  ChromaDB Learn │  ← New POA embedded for future use
                   └─────────────────┘
```

### Core Modules

#### `agent.py` — LangGraph Agent
The decision engine, built as a compiled `StateGraph` with four sequential nodes:

| Node | Role |
|---|---|
| `observe` | Collects all `At Risk` shipments and active alerts into structured context |
| `reason` | Sends context to GPT-4o-mini to produce a 2-sentence failure hypothesis |
| `decide` | Retrieves the most similar historical POA from ChromaDB via RAG, then instructs GPT-4o-mini to formulate a mitigation plan. Tags `[NEEDS APPROVAL]` for HIGH severity |
| `act` | Executes the decision — sets shipment status to `Rerouted (Auto)` or `Pending Approval` |

#### `memory.py` — ChromaDB RAG System
The agent's long-term memory. Uses `text-embedding-3-small` to convert alert descriptions into vectors.

- Pre-seeded with 6 historical POAs covering High, Medium, and Low severity scenarios
- **`get_past_poa(alert_description)`** — similarity search, returns the closest historical plan
- **`add_learned_action(...)`** — called after human approval to write new experiences into the DB
- Persisted locally at `backend/chroma_db/`

#### `main.py` — FastAPI Backend
Serves the frontend and manages global in-memory state for shipments and alerts. Loads 1,000+ shipments from `simulated_shipments.json` on startup.

#### `newsEngine.py` — OSINT Feed
Polls MediaStack API for live news, filters by disruption keywords, and matches article locations against the active shipment dataset.

#### `state.py` — Data Models

```python
class Shipment(BaseModel):
    shipment_id, origin, destination, carrier
    weight_kg, distance_km, eta_hours
    status, delay_probability
    operational_cost, partner_reliability, timestamp

class Alert(BaseModel):
    id, type, location
    severity   # "High" | "Medium" | "Low"
    description

class AgentState(TypedDict):
    messages, shipments, alerts
    hypothesis, decision, action_taken
```

---

## 🚀 Installation

### Prerequisites

- Python **3.12+**
- `pip` or `conda`
- [OpenAI API key](https://platform.openai.com/api-keys) — powers the agent (`gpt-4o-mini`) and embeddings (`text-embedding-3-small`)
- [MediaStack API key](https://mediastack.com/) — powers the live OSINT news feed

### 1. Clone the Repository

```bash
git clone https://github.com/andy1924/AtlasAI.git
cd AtlasAI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI — used by agent.py (GPT-4o-mini) and memory.py (text-embedding-3-small)
OPENAI_API_KEY="sk-..."

# MediaStack — used by newsEngine.py for live OSINT disruption news
MEDIA_STACK_API="your_mediastack_api_key_here"
```

| Variable | Required | Used By | Where to Get |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | `agent.py`, `memory.py` | [platform.openai.com](https://platform.openai.com/api-keys) |
| `MEDIA_STACK_API` | ✅ Yes | `newsEngine.py` | [mediastack.com](https://mediastack.com/) |

> ⚠️ **Never commit your `.env` file.** Add `.env` to your `.gitignore`.

### 4. Start the Backend

```bash
cd backend
python main.py
```

The API will be live at `http://127.0.0.1:8000`. ChromaDB will auto-initialize and seed its knowledge base on first run:

```
📚 Initializing AtlasAI ChromaDB Memory...
🌱 Seeding initial Knowledge Base into ChromaDB...
✅ Successfully loaded 1000 shipments.
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

## 🔧 Agent Loop

### Step 1 — Inject a Chaos Event

Use the **"TRIGGER EVENT"** button on the dashboard, or call the API directly:

```bash
curl -X POST http://127.0.0.1:8000/api/trigger-chaos \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Port Strike",
    "location": "Kellyland",
    "severity": "High",
    "description": "Dock workers have halted all loading operations indefinitely."
  }'
```

All shipments with `origin` or `destination` matching `Kellyland` are immediately flagged `At Risk` with `delay_probability: 0.95`.

### Step 2 — Run the Agent

```bash
curl -X POST http://127.0.0.1:8000/api/run-agent
```

The agent executes its full loop and returns a structured log:

```json
{
  "message": "Agent cycle complete.",
  "log": {
    "hypothesis": "The port strike at Kellyland has halted all loading operations, causing cascading delays for carriers relying on this hub.",
    "decision": "Action: Reroute affected shipments via alternate inland hub.\nReasoning: Based on historical precedent where a similar port strike required emergency rerouting... [NEEDS APPROVAL]",
    "action_taken": "Drafted mitigation plan for 3 shipments. Escalated to human operator due to HIGH severity."
  }
}
```

### Step 3 — Approve High Severity Actions

When the agent flags `[NEEDS APPROVAL]`, shipments are held at `Pending Approval`. The human operator reviews and confirms:

```bash
curl -X POST http://127.0.0.1:8000/api/approve-actions
```

This promotes shipments to `Rerouted (Approved)`, sets `delay_probability: 0.05`, and **writes the approved action into ChromaDB** so the agent can recall it in future incidents.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/shipments` | Returns all shipments with current status |
| `GET` | `/api/alerts` | Returns all active disruption alerts |
| `GET` | `/api/news` | Returns live OSINT news events from MediaStack |
| `POST` | `/api/trigger-chaos` | Injects a disruption event and flags at-risk shipments |
| `POST` | `/api/run-agent` | Executes the full LangGraph Observe→Reason→Decide→Act cycle |
| `POST` | `/api/approve-actions` | Approves pending HIGH severity actions + triggers ChromaDB learn loop |

---

## 🧠 Memory & RAG System

The `memory.py` module provides the agent with persistent, searchable experience using OpenAI's `text-embedding-3-small` model and a local ChromaDB vector store.

### Pre-Seeded Knowledge Base

| Severity | Scenario | Plan of Action |
|---|---|---|
| 🔴 High | Port bombing — total maritime halt | Halt all maritime loading, reroute critical shipments via emergency air freight |
| 🔴 High | Category 5 hurricane at hub | Divert all inbound transit to inland hubs, shelter high-weight inventory |
| 🟡 Medium | Piracy threat at sea | Reroute vessels 200 nautical miles offshore |
| 🟡 Medium | Carrier operational degradation | Transfer high-priority shipments to carriers with reliability score > 0.90 |
| 🟢 Low | Highway traffic congestion | Reroute ground transport to secondary highways, accept minor ETA increase |
| 🟢 Low | Minor customs delay | Monitor only, send automated ETA update to end-customer |

### The Learn Loop

Every human-approved action becomes a permanent memory:

```
Human Approves → add_learned_action(description, severity, action)
                          │
                          ▼
              ChromaDB ← New vector document
                          │
                          ▼
         Retrieved by agent in next similar incident
```

### Verify Memory

```bash
python backend/memory.py
```

```
📚 Initializing AtlasAI ChromaDB Memory...
📄 Total Memories Stored: 6
🔍 Testing Retrieval (Searching for 'Traffic Jam')...
💡 Retrieved Plan of Action:
   -> Autonomously rerouted ground transport to secondary highways...
✅ Memory Module is fully operational!
```

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` + `uvicorn` | REST API server |
| `langgraph` | Agent graph orchestration |
| `langchain-openai` | GPT-4o-mini LLM + text-embedding-3-small |
| `langchain-chroma` | ChromaDB vector store integration |
| `pydantic` | Data validation — Shipment, Alert, AgentState |
| `python-dotenv` | `.env` key loading |
| `requests` | MediaStack HTTP client |
| `faker` | Synthetic shipment data generation |

---

## 🛠️ Troubleshooting

**`openai.AuthenticationError: Incorrect API key`**
→ Add `OPENAI_API_KEY="sk-..."` to your `.env` file.

**`ValueError: MEDIA_STACK_API key not found`**
→ Add `MEDIA_STACK_API="..."` to your `.env` file.

**`FileNotFoundError: simulated_shipments.json`**
→ Run `python main.py` from inside the `backend/` directory, not the project root.

**ChromaDB not persisting between runs**
→ The `chroma_db/` folder is created automatically next to `memory.py`. Ensure that directory is writable and not inside a read-only mount.

**Agent always responds "System normal. No shipments currently at risk."**
→ No shipments are flagged `At Risk`. Call `POST /api/trigger-chaos` first to inject a disruption event.

---

## 🗺️ Roadmap

- [ ] Connect to real carrier APIs (FedEx, DHL, Maersk)
- [ ] Persistent shipment state with PostgreSQL or Redis
- [ ] Confidence scoring on RAG-retrieved POAs
- [ ] Multi-agent coordination for large-scale disruptions
- [ ] Slack / email operator notifications for HIGH severity escalations
- [ ] Docker + deployment guide

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -m 'Add YourFeature'`
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

<div align="center">

**Version 2.0.0** · Last Updated March 2026 · Active Development

</div>