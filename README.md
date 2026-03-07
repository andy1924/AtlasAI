<div align="center">

# 🌍 AtlasAI-2

### Logistics Disruption Analysis System

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen?style=for-the-badge)]()

<br/>

*A comprehensive logistics intelligence platform that monitors real-time disruptions, analyzes geopolitical and natural events, and delivers AI-driven risk assessments for smarter shipment management.*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Roadmap](#%EF%B8%8F-roadmap)

</div>

---

## 📌 Overview

AtlasAI-2 integrates multiple intelligence systems to provide real-time monitoring and predictive analytics for logistics operations. By combining live news feeds, chaos event simulation, and machine learning-based risk analysis, the platform helps operations teams make faster, more informed supply chain decisions.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 Real-Time Monitoring | Live news feed via MediaStack API across 80+ countries |
| 🤖 AI Risk Analysis | Multi-factor failure probability modeling per shipment |
| ⚡ Chaos Engine | Simulates and detects real-world logistics disruption events |
| 🗺️ Geopolitical Intelligence | Filters and categorizes political and conflict-based events |
| 🌩️ Natural Disaster Alerts | Detects storms, floods, earthquakes, and more |
| 📋 Actionable Recommendations | Route-level guidance: monitor, mitigate, or reroute |

---

## 📁 Project Structure

```
AtlasAI-2/
│
├── backend/
│   ├── agent.py              # Agent orchestration & decision engine
│   ├── chaos_engine.py       # Real-time disruption event generator
│   ├── newsEngine.py         # News feed fetcher & disruption filter
│   ├── riskAnalysis.py       # Shipment risk scoring & recommendations
│   ├── main.py               # Application entry point
│   └── state.py              # State management & data persistence
│
├── maindata/
│   ├── simulated_shipments.json   # 1,847 simulated shipments with metadata
│   └── LogisticSimulator.py       # Shipment data generator
│
├── data/
│   ├── chaos_feed.json        # Real & simulated disruption events
│   ├── news_events.json       # Filtered news with disruption keywords
│   └── shipements.json        # Processed shipment records
│
├── .env                       # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## 🚀 Installation

### Prerequisites

- Python **3.12+**
- `pip` or `conda`
- A [MediaStack API key](https://mediastack.com/) for real-time news

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/AtlasAI-2.git
cd AtlasAI-2
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
MEDIA_STACK_API="your_mediastack_api_key_here"
```

### 4. Verify Installation

```bash
python backend/chaos_engine.py
python backend/newsEngine.py
python backend/riskAnalysis.py
```

---

## 🔧 Usage

### Workflow 1 — Monitor Disruptions

```bash
# Fetch real-time news disruptions
python backend/newsEngine.py

# Generate the chaos event feed
python backend/chaos_engine.py

# Review output at data/chaos_feed.json
```

### Workflow 2 — Analyze Shipment Risk

```bash
python backend/riskAnalysis.py
```

When prompted, enter a shipment ID:

```
Enter Shipment ID to analyze (e.g., SHP-492664): SHP-492664
```

**Sample Output:**

```
============================================================
RISK ANALYSIS REPORT
============================================================

📦 Shipment ID: SHP-492664
🗺️  Route: North Anthony → Kellyland
⚠️  Failure Probability: 22%
🎯 Risk Level: LOW

✅ No specific risk factors identified
📋 Recommended Action: Monitor shipment

============================================================
```

### Workflow 3 — Full Intelligence Run

```bash
python backend/chaos_engine.py
python backend/newsEngine.py
python backend/riskAnalysis.py
```

Cross-reference live disruption events with active shipment routes to dynamically adjust risk profiles.

---

## 🏗️ Architecture

### Core Components

#### 🔴 Chaos Engine (`chaos_engine.py`)
Fetches live disruption news and generates simulated chaos events, outputting a unified `chaos_feed.json` for downstream risk analysis.

#### 📰 News Engine (`newsEngine.py`)
Monitors MediaStack's real-time API and classifies events into:
- **Natural Events** — storm, hurricane, flood, earthquake, cyclone, wildfire, typhoon
- **Geopolitical Events** — war, conflict, strike, protest, blockade

#### 📊 Risk Analysis Engine (`riskAnalysis.py`)
Scores each shipment across 8 weighted risk dimensions:

| Factor | Weight | Basis |
|---|---|---|
| Distance Risk | 15% | Route distance (0–3,000 km) |
| ETA Risk | 15% | Time-to-delivery window (0–72 hrs) |
| Carrier Reliability | 20% | Partner reliability score |
| Weight Risk | 10% | Cargo weight (0–2,000 kg) |
| Warehouse Load | 15% | Congestion level at hub |
| Weather Risk | 10% | Climate & natural event impact |
| Geopolitical Risk | 10% | Political instability index |
| Chaos Risk | 5% | Simulated disruption feed |

### Risk Classification

| Level | Threshold | Recommended Action |
|---|---|---|
| ✅ **LOW** | < 30% | Monitor — no immediate action needed |
| ⚠️ **MEDIUM** | 30–60% | Prepare mitigation — consider alternatives |
| 🚨 **HIGH** | ≥ 60% | Reroute — use alternate hub or delay |

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework & API layer |
| `langchain` / `langgraph` | AI agent workflows |
| `requests` | HTTP client for external APIs |
| `python-dotenv` | `.env` variable management |
| `faker` | Synthetic shipment data generation |

See `requirements.txt` for the full list.

---

## 🛠️ Troubleshooting

**`ValueError: MEDIA_STACK_API key not found in .env file`**
→ Create a `.env` file in the project root containing your MediaStack API key.

**`FileNotFoundError: No such file or directory`**
→ Always run scripts from the project root, not from inside `backend/`.

**Empty or missing shipment results**
→ Verify `maindata/simulated_shipments.json` exists. Use `SHP-492664` as a test ID.

---

## 🗺️ Roadmap

- [ ] Integration with real shipping carrier APIs
- [ ] Advanced ML models for failure prediction
- [ ] Web dashboard interface
- [ ] Mobile app support
- [ ] Blockchain-based shipment tracking
- [ ] Enhanced geopolitical intelligence layer
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions are welcome!

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