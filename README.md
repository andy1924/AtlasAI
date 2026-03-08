<div align="center">

# 🌍 AtlasAI

### Autonomous Logistics Intelligence Layer

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG_Memory-E05A2B?style=for-the-badge)](https://trychroma.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://platform.openai.com)
[![NumPy](https://img.shields.io/badge/NumPy-LSTM_Engine-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

*A full-stack autonomous AI agent that proactively detects logistics disruptions, reasons about cascading failures, retrieves outcome-weighted historical Plans of Action from vector memory, and either self-executes mitigations or escalates to a human operator — then evaluates whether its decisions actually worked, closing the full observe → reason → decide → act → learn loop. Now featuring a pure-NumPy dual-head LSTM for carrier reliability forecasting and a real-time global fleet tracking map.*

[Features](#-features) • [Architecture](#-architecture) • [LSTM ML Engine](#-lstm-ml-engine) • [Installation](#-installation) • [Agent Loop](#-agent-loop) • [API Reference](#-api-reference) • [Memory System](#-memory--rag-system) • [Dashboard](#-dashboard)

</div>

---

## 📌 Overview

AtlasAI is a full-stack autonomous logistics intelligence system built around a 4-node LangGraph agent. When a disruption is detected — whether injected manually or auto-flagged by the proactive observer — the agent reasons about root causes and cascading impact, retrieves the closest historical Plan of Action from ChromaDB using semantic similarity, chooses from a structured action menu, and either executes the mitigation autonomously or escalates it based on severity and confidence.

After actions are taken, a dedicated outcome evaluator checks whether each intervention actually reduced delay probability. Failures are written back into ChromaDB so the agent improves with every incident cycle.

A custom-built dual-head LSTM (zero external ML dependencies — pure NumPy) runs in parallel to predict next-day carrier reliability and degradation probability, feeding its risk flags directly into the agent's decision node. The frontend visualises all of this on a live D3-powered world map showing real-time vessel positions, chaos-affected ships highlighted in red, and animated route lines to destination ports.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔭 Proactive Observer | Auto-flags `At Risk` shipments from 4 live signals before any chaos is injected |
| 🤖 LangGraph Agent | 4-node graph: Observe → Reason → Decide → Act with full state management |
| 🎯 Structured Action Menu | Agent chooses: `REROUTE` / `HOLD` / `SWITCH_CARRIER` / `EXPEDITE` / `ESCALATE` / `MONITOR` |
| 📊 Confidence Scoring | Agent outputs 0–100% confidence; decisions below 45% auto-escalate to human |
| 🧠 Outcome-Weighted RAG | ChromaDB retrieval prioritises `outcome: success` records over failed strategies |
| 🔄 Full Learn Loop | Outcome evaluator checks interventions, writes failures back to ChromaDB memory |
| 👤 Human-in-the-Loop | HIGH severity or low-confidence decisions pause for operator approval |
| 📡 Carrier Intelligence | Live reliability scores calculated from real delay data across all shipments |
| 🌐 OSINT News Feed | MediaStack API monitors 80+ countries for natural and geopolitical disruptions |
| ⚡ Chaos Simulation | 6 pre-built scenarios (port bombing, hurricane, piracy, strike, carrier degradation…) |
| 📋 Full Audit Trail | Timestamped agent history with confidence, action type, affected count, autonomous flag |
| 🧬 Dual-Head LSTM | Pure-NumPy LSTM predicts next-day carrier reliability **and** degradation probability simultaneously |
| 📈 3-Day Carrier Forecast | Autoregressive LSTM forecast per carrier — click any carrier card to expand the 3-day outlook |
| 🗺️ Live Fleet Tracker | Real-time D3 world map with 12 vessel positions, route lines, affected ships in red, and hover tooltips |
| 👤 User Profile | Authenticated session shown as Aditya (Logistics Analyst) with profile dropdown in the header |

---

## 📁 Project Structure

```
AtlasAI/
│
├── backend/
│   ├── main.py                    # FastAPI app — 10 REST endpoints, carrier stats, ML predictions, outcome eval
│   ├── agent.py                   # LangGraph agent — proactive observer + 4-node graph, ML risk integration
│   ├── memory.py                  # ChromaDB RAG — seed, outcome-weighted search, learn, mark
│   ├── state.py                   # Pydantic models: Shipment, Alert, CarrierStats, AgentState
│   ├── newsEngine.py              # MediaStack OSINT feed & disruption keyword filter
│   │
│   └── ml/
│       ├── lstm_model.py          # Pure-NumPy dual-head LSTM — zero external ML deps
│       ├── data_prep.py           # Feature engineering, MinMax scaler, sequence builder
│       ├── predictor.py           # Inference layer — refresh, get predictions, 3-day forecast
│       └── train.py               # Training script — run once to produce carrier_lstm.npz
│       └── models/
│           ├── carrier_lstm.npz   # Trained model weights (NumPy savez format)
│           ├── scaler_params.json # MinMax scaler lo/rng values for all 11 features
│           └── eval_metrics.json  # Last training run: MAE, RMSE, Acc, Precision, Recall, F1
│
├── frontend/
│   └── app/
│       └── page.tsx               # Next.js dashboard — map, fleet tracker, tabbed panels, profile
│
├── maindata/
│   ├── simulated_shipments.json   # 1,000 simulated shipments
│   ├── carrier_daily_series.json  # Daily carrier reliability time-series for LSTM training
│   └── LogisticSimulator.py       # Shipment + time-series data generator
│
├── data/
│   ├── shipements.json            # Seed shipments
│   ├── chaos_feed.json            # Chaos event log
│   └── news_events.json           # OSINT event cache
│
├── backend/chroma_db/             # Auto-generated ChromaDB vector store (persisted locally)
├── .env                           # API keys — never commit
├── requirements.txt
└── README.md
```

---

## 🏗️ Architecture

### Full System Flow

```
  [MediaStack OSINT]        [Frontend: TRIGGER EVENT]     [Proactive Signals]
        │                           │                            │
        ▼                           ▼                            ▼
  newsEngine.py         POST /api/trigger-chaos        auto_flag_at_risk()
        │                           │                  (carrier reliability,
        └──────────┬────────────────┘                   ETA, delay_prob,
                   ▼                                    weight+distance)
          POST /api/run-agent                                    │
                   │                              ┌─────────────▼──────────────┐
                   │                              │   LSTM Predictor (parallel) │
                   │                              │  predicted_reliability[t+1] │
                   │                              │  degradation_probability    │
                   │                              │  is_degraded / risk_flag    │
                   │                              └─────────────┬──────────────┘
      ┌────────────▼────────────┐                               │
      │     LangGraph Agent     │◄──────────────────────────────┘
      │  ┌─────────────────┐    │
      │  │    OBSERVE      │    │  ← Runs auto_flag_at_risk(), integrates LSTM risk flags
      │  └────────┬────────┘    │
      │  ┌────────▼────────┐    │
      │  │     REASON      │    │  ← GPT-4o-mini: root cause + cascading impact
      │  └────────┬────────┘    │
      │  ┌────────▼────────┐    │
      │  │     DECIDE      │    │  ← RAG retrieves outcome-weighted POA
      │  │  (ChromaDB)     │    │     GPT picks action + outputs confidence %
      │  └────────┬────────┘    │
      │  ┌────────▼────────┐    │
      │  │      ACT        │    │  ← Applies action-specific status + cost/ETA changes
      │  └─────────────────┘    │
      └────────────┬────────────┘
                   │
       ┌───────────┴────────────┐
       ▼                        ▼
  Confidence ≥ 45%         Confidence < 45%
  + Medium/Low severity    OR High severity
       │                        │
  Auto-execute            [NEEDS APPROVAL]
  REROUTE / HOLD /        → Pending Approval
  SWITCH_CARRIER /                │
  EXPEDITE / MONITOR      POST /api/approve-actions
                                  │
                       ┌──────────▼──────────┐
                       │   ChromaDB Learn    │  ← add_learned_action(outcome=success)
                       └─────────────────────┘
                                  │
                       POST /api/evaluate-outcomes
                                  │
                       ┌──────────▼──────────┐
                       │  Outcome Evaluator  │  ← Checks delay_prob vs threshold
                       │                     │     Writes failures → mark_outcome()
                       └─────────────────────┘
```

---

## 🧬 LSTM ML Engine

AtlasAI includes a fully custom dual-head LSTM built from scratch in pure NumPy — no PyTorch, no TensorFlow, no Keras. It is trained on historical carrier daily series data and serves two simultaneous predictions per carrier.

### Architecture

```
Input  (batch, 7 days, 11 features)
  │
  ├── LSTM Layer 1   hidden=64   return_sequences=True
  │   └── Dropout 0.25
  │
  ├── LSTM Layer 2   hidden=32   return_sequences=False
  │   └── Dropout 0.25
  │
  └── Dense(16, tanh)
        │
        ├── Head A: Dense(1, sigmoid)  →  predicted_reliability   [regression]
        └── Head B: Dense(1, sigmoid)  →  degradation_probability [classification]
```

### Training

```
Loss = 0.65 × MSE(reliability) + 0.35 × BCE(is_degraded)
Optimizer: Adam   lr=0.001   β1=0.9   β2=0.999
Epochs: 100   Batch: 32   Early-stop patience: 15
```

Run training once before starting the backend:

```bash
cd backend
python ml/train.py
```

This produces `backend/ml/models/carrier_lstm.npz` and `scaler_params.json`. On completion it prints test-set metrics:

```
📊 Test-set evaluation
────────────────────────────────────────
  Regression      — MAE=0.0182  RMSE=0.0241
  Classification  — Acc=0.894  Prec=0.871  Rec=0.883  F1=0.877
```

### What the LSTM outputs per carrier

| Output | Type | Description |
|---|---|---|
| `predicted_reliability` | float 0–1 | Forecast reliability for next day |
| `degradation_probability` | float 0–1 | Probability of entering degraded state |
| `trend` | float (signed) | Delta vs current live reliability |
| `is_degrading` | bool | Downward trend detected (warn proactively) |
| `is_degraded` | bool | Predicted to fall below 0.80 threshold |
| `risk_flag` | string | Emoji badge: 🟢 / 🟡 / 🔴 |

### Integration with the Agent

When `is_degraded = True`, the agent's `observe` node receives a pre-populated risk flag for that carrier. This feeds into the `reason` node's context window so GPT-4o-mini can explicitly factor in predictive degradation — not just current live reliability — when selecting an action.

### 3-Day Autoregressive Forecast

The `/api/ml-forecast/{carrier}?days=3` endpoint runs the LSTM autoregressively: the output of each prediction step is fed back as input for the next. Click any carrier card in the **Carriers** tab to expand the 3-day panel. Accuracy naturally decreases each step ahead.

---

## 🗺️ Live Fleet Tracker

The dashboard includes a real-time D3.js world map (Natural Earth projection) rendering global vessel positions with live movement simulation.

### What the map shows

- **12 mock vessels** plotted at real geographic coordinates, updated every 2.5 seconds
- **Cyan ships** — nominal operations, moving along their routes
- **Orange ships** — at-risk; elevated delay probability or flagged by LSTM
- **Red ships** — chaos-affected; stopped or severely disrupted
- **Dashed route lines** from each vessel's current position to its destination port
- **Port markers** for 10 major hubs (Shanghai, Rotterdam, Dubai, Mumbai, etc.)
- **Alert zone rings** — pulsing red halos appear on the map around any active chaos location
- **Hover tooltip** — click or hover any vessel to see: vessel name, ID, route, carrier, speed (knots), cargo type, and current status badge

### Live status sync

When a chaos event is triggered via the dashboard, the ship status layer automatically updates: a proportion of vessels are promoted to `affected` (stopped) and `at-risk` (slowed), visually reflecting the disruption on the map in real time. Resolving all alerts resets ships to nominal state.

---

## 🚀 Installation

### Prerequisites

- Python **3.12+**
- Node.js **18+**
- [OpenAI API key](https://platform.openai.com/api-keys) — `gpt-4o-mini` + `text-embedding-3-small`
- [MediaStack API key](https://mediastack.com/) — live OSINT news feed

### 1. Clone the Repository

```bash
git clone https://github.com/andy1924/AtlasAI.git
cd AtlasAI
```

### 2. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI — agent reasoning (GPT-4o-mini) + vector embeddings (text-embedding-3-small)
OPENAI_API_KEY="sk-..."

# MediaStack — live OSINT disruption news feed
MEDIA_STACK_API="your_mediastack_api_key_here"
```

| Variable | Required | Used By | Where to Get |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | `agent.py`, `memory.py` | [platform.openai.com](https://platform.openai.com/api-keys) |
| `MEDIA_STACK_API` | ✅ Yes | `newsEngine.py` | [mediastack.com](https://mediastack.com/) |

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

### 5. Train the LSTM (one-time setup)

```bash
cd backend
python ml/train.py
```

This generates `backend/ml/models/carrier_lstm.npz` and `scaler_params.json`. Takes ~30–60 seconds. Skip this step only if you want the dashboard to show the LSTM-unavailable banner instead of live predictions.

### 6. Start the Backend

```bash
cd backend
python main.py
```

On first run, ChromaDB initialises and seeds 8 historical POAs automatically:

```
📚 Initializing AtlasAI ChromaDB Memory...
🌱 Seeding initial Knowledge Base into ChromaDB...
✅ Seeded 8 historical POAs.
✅ Successfully loaded 1000 shipments.
INFO: Uvicorn running on http://127.0.0.1:8000
```

### 7. Start the Frontend

```bash
cd frontend
npm run dev
```

Dashboard will be live at `http://localhost:3000`.

---

## 🔧 Agent Loop

The complete loop from detection to learning runs in 5 steps:

### Step 1 — Proactive Detection (automatic)

Every time the agent runs, `auto_flag_at_risk()` scans all `In Transit` shipments and flags those exceeding a composite risk score across 4 signals — no manual event injection needed. The LSTM predictor runs in parallel and pre-flags any carriers it predicts will degrade by the next day.

### Step 2 — Inject a Chaos Event (optional, for demos)

Use the **⚡ Trigger Event** button on the dashboard, or call directly:

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

### Step 3 — Run the Agent

```bash
curl -X POST http://127.0.0.1:8000/api/run-agent
```

Returns a structured log with hypothesis, decision, confidence score, action type, and affected shipment count:

```json
{
  "log": {
    "timestamp": "2026-03-08T14:23:11",
    "hypothesis": "The port strike at Kellyland disrupts 3 carriers relying on this hub, with cascading ETA breaches for downstream partners.",
    "decision": "Action: ESCALATE\nConfidence: 82\nReasoning: Based on historical precedent where a port bombing required halting maritime loading... [NEEDS APPROVAL]",
    "action_taken": "⚠️ Drafted ESCALATE plan for 3 shipment(s). Escalated to human operator (HIGH severity).",
    "confidence": 82,
    "action_type": "ESCALATE",
    "severity_level": "High",
    "shipments_affected": 3,
    "autonomous": false
  }
}
```

### Step 4 — Approve (High Severity / Low Confidence only)

```bash
curl -X POST http://127.0.0.1:8000/api/approve-actions
```

Promotes `Pending Approval` → `Rerouted (Approved)`, sets `delay_probability: 0.05`, and writes the approved action into ChromaDB tagged `outcome: success`.

### Step 5 — Evaluate Outcomes (closes the Learn loop)

```bash
curl -X POST http://127.0.0.1:8000/api/evaluate-outcomes
```

Compares each actioned shipment's current `delay_probability` against per-action thresholds. Failures are written to ChromaDB via `mark_outcome()` so the agent deprioritises that strategy next time.

```json
{
  "message": "Outcome evaluation complete. 2 successes, 1 failures.",
  "results": {
    "successful": 2,
    "failed": 1,
    "details": [
      { "shipment_id": "SHP-492664", "status": "Rerouted (Auto)", "delay_probability": 0.10, "outcome": "✅ SUCCESS" },
      { "shipment_id": "SHP-965162", "status": "On Hold", "delay_probability": 0.41, "outcome": "❌ FAILED — delay still elevated" }
    ]
  }
}
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/shipments` | All shipments with current status |
| `GET` | `/api/alerts` | All active disruption alerts |
| `GET` | `/api/news` | Live OSINT events from MediaStack |
| `GET` | `/api/carrier-reliability` | Live reliability scores per carrier, calculated from delay data |
| `GET` | `/api/agent-history` | Full timestamped audit trail of all agent decisions |
| `GET` | `/api/ml-predictions` | LSTM predictions for all carriers — reliability, degradation prob, trend, risk flag |
| `GET` | `/api/ml-forecast/{carrier}?days=N` | Autoregressive N-day LSTM forecast for a single carrier |
| `POST` | `/api/trigger-chaos` | Inject a disruption event, flag matching shipments `At Risk` |
| `POST` | `/api/run-agent` | Run the full Observe → Reason → Decide → Act cycle |
| `POST` | `/api/approve-actions` | Human approval — execute pending actions + trigger ChromaDB learn |
| `POST` | `/api/evaluate-outcomes` | Check intervention success, write failures to ChromaDB memory |

---

## 🧠 Memory & RAG System

The `memory.py` module gives the agent persistent, outcome-aware experience using OpenAI `text-embedding-3-small` and a local ChromaDB vector store.

### Pre-Seeded Knowledge Base (8 POAs)

| Severity | Action Type | Scenario | Plan of Action |
|---|---|---|---|
| 🔴 High | ESCALATE | Port bombing — maritime halt | Halt loading, reroute via emergency air freight |
| 🔴 High | ESCALATE | Category 5 hurricane | Divert to inland hubs, shelter high-weight inventory |
| 🟡 Medium | REROUTE | Piracy threat | Reroute vessels 200 nautical miles offshore |
| 🟡 Medium | SWITCH_CARRIER | Carrier degradation | Transfer to carriers with reliability > 0.90 |
| 🟡 Medium | HOLD | Port workers strike | Hold outbound 48h, notify downstream partners |
| 🟡 Medium | EXPEDITE | High-priority SLA at risk | Upgrade to express lane, accept 15% cost increase |
| 🟢 Low | REROUTE | Highway congestion | Secondary highway reroute, +3h ETA accepted |
| 🟢 Low | MONITOR | Minor customs delay | Monitor only, send automated ETA update |

### Outcome-Weighted Retrieval

`get_past_poa()` fetches top-3 similar results, filters for `outcome: success`, and returns a `confidence_hint` based on how many successful precedents matched:

```python
# ≥2 successful matches → confidence_hint: 85
# 1 successful match   → confidence_hint: 65
# 0 successful matches → confidence_hint: 40 (may trigger auto-escalate)
```

### The Full Learn Loop

```
Agent Acts → Outcome Evaluator Runs
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   ✅ SUCCESS              ❌ FAILURE
        │                       │
add_learned_action(          mark_outcome(
  outcome="success")           outcome="failure")
        │                       │
        └───────────┬───────────┘
                    ▼
         ChromaDB updated
         Future retrievals weighted accordingly
```

---

## 📊 Dashboard

The Next.js frontend exposes the full agent lifecycle in a single dark-themed, deep-navy dashboard.

### Header

Sticky navigation bar with the AtlasAI logo, a live vessel counter (total / affected / at-risk), action buttons (Evaluate, Run Agent, Trigger Event), and the **Aditya** profile dropdown showing name, email, role, active session indicator, and a sign-out option.

### Stats Bar

Four glowing stat cards showing: Total Tracked, At Risk (pulses red when active), Pending Approval, and Resolved — all updating live after each agent cycle.

### Live Fleet Tracker

A full-width D3 Natural Earth world map showing all 12 vessels with real-time positional drift, colour-coded by status (cyan / orange / red), dashed route lines, port labels, and alert zone rings. Ships update position every 2.5 seconds. Hover any vessel for a detailed tooltip. Toggle visibility with the Hide/Show Map button.

### Approval Banner

Appears automatically when `Pending Approval` shipments exist. Shows the agent's reasoning excerpt and a pulsing **VERIFY & EXECUTE** button with a scrollable list of all pending shipment IDs.

### Left Panel — Alerts + Shipment Table

Active disruption alerts shown with type, location, description, and severity badge. Below, the full shipment table sorted by risk priority — affected rows are highlighted red. Includes delay probability mini-bar, colour-coded status badge, and paginated navigation for large fleets.

### Right Panel — Tabbed

**🤖 Agent Log** — Full decision audit trail per cycle. Each entry shows action type badge, hypothesis, execution result (🤖 AUTO vs 👤 HUMAN), confidence meter bar, affected count, and severity level.

**📦 Carriers** — Live carrier reliability panel with LSTM integration. Each carrier card shows:
- Live reliability progress bar (green / amber / red)
- 🧠 LSTM Tomorrow bar with predicted reliability and trend delta
- Warning banners for `is_degraded` or `is_degrading` states
- Click to expand an inline **3-Day LSTM Forecast** panel
- LSTM status banner at the top (active vs needs training)

**📊 Outcomes** — Outcome evaluation results showing success/failure counts and per-shipment details with delay probability and pass/fail indicators.

### Global Disruption Radar

Live OSINT news cards from MediaStack showing chaos type, matched location (if applicable), article title linked to source, and publisher name.

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` + `uvicorn` | REST API server |
| `langgraph` | Agent graph orchestration |
| `langchain-openai` | GPT-4o-mini LLM + text-embedding-3-small |
| `langchain-chroma` | ChromaDB vector store integration |
| `pydantic` | Data validation — Shipment, Alert, CarrierStats, AgentState |
| `python-dotenv` | `.env` key loading |
| `requests` | MediaStack HTTP client |
| `faker` | Synthetic shipment data generation |
| `numpy` | Pure-NumPy LSTM — no ML framework required |
| `next` 16 | React frontend framework |
| `typescript` | Type safety across all frontend interfaces |
| `tailwindcss` 4 | Dashboard styling |
| `d3` | World map rendering + fleet visualisation |
| `topojson-client` | TopoJSON geometry decoding for country outlines |
| `world-atlas` | Natural Earth country geometry dataset |

---

## 🛠️ Troubleshooting

**`openai.AuthenticationError: Incorrect API key`**
→ Add `OPENAI_API_KEY="sk-..."` to your `.env` file in the project root.

**`ValueError: MEDIA_STACK_API key not found`**
→ Add `MEDIA_STACK_API="..."` to your `.env` file.

**`FileNotFoundError: simulated_shipments.json`**
→ Run `python main.py` from inside the `backend/` directory, not the project root.

**`Model not found at backend/ml/models/carrier_lstm.npz`**
→ Run `python ml/train.py` from inside `backend/` before starting the server. The LSTM banner in the Carriers tab will show a yellow warning until training is complete.

**LSTM predictions not appearing in the dashboard**
→ The `/api/ml-predictions` endpoint returns `ml_available: false` if the model file is missing. Run `python ml/train.py` and restart the backend.

**ChromaDB not persisting between runs**
→ The `chroma_db/` folder is auto-created next to `memory.py`. Ensure the `backend/` directory is writable.

**Agent always responds "System normal"**
→ No shipments are `At Risk`. Either trigger a chaos event via the dashboard, or check that `auto_flag_at_risk()` has `In Transit` shipments to scan (delivered shipments are skipped).

**World map not rendering / blank**
→ The map fetches the world atlas GeoJSON from `cdn.jsdelivr.net` on load. Ensure your browser has internet access. If offline, the map container will still render with the ocean background and vessel markers.

**Frontend can't reach backend**
→ Ensure `python main.py` is running on port 8000 before starting the Next.js dev server. CORS is open to all origins by default.

---

## 🗺️ Roadmap

- [x] Proactive shipment risk flagging (multi-signal observer)
- [x] Structured action menu with confidence scoring
- [x] Outcome evaluation + ChromaDB failure tagging
- [x] Live carrier reliability tracker
- [x] Full agent audit trail with timestamps
- [x] Pure-NumPy dual-head LSTM for carrier reliability + degradation forecasting
- [x] 3-day autoregressive LSTM forecast per carrier
- [x] LSTM risk flags integrated into agent observe/reason nodes
- [x] Real-time D3 world map with live fleet tracking
- [x] Chaos-aware ship status (affected ships shown in red on map)
- [x] User profile (Aditya — Logistics Analyst)
- [ ] Connect to real carrier APIs (FedEx, DHL, Maersk)
- [ ] Persistent state with PostgreSQL or Redis
- [ ] Slack / email notifications for HIGH severity escalations
- [ ] Multi-agent coordination for large-scale disruptions
- [ ] Docker + one-command deployment guide
- [ ] AIS integration for real vessel position data

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

---

## 👤 Authors

**Arnav** — AI/ML Lead  
**Sarvesh** — Backend Lead  
**Atharva** — Frontend Lead  

For issues, suggestions, or questions, please [open a GitHub issue](https://github.com/andy1924/AtlasAI/issues).

---

<div align="center">

**Version 4.0.0** · Last Updated March 2026 · Active Development

</div>