"""
agent.py
────────
LangGraph agent with LSTM-powered proactive observer.
The LSTM predictor replaces static partner_reliability
with a forward-looking predicted score in auto_flag_at_risk().
"""

import os, re, sys
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from state  import AgentState, Shipment, Alert
from memory import get_past_poa

# ── LSTM predictor (graceful fallback if model not trained yet) ──
ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml")
sys.path.insert(0, ML_DIR)

try:
    from predictor import get_predicted_reliability, get_all_predictions, refresh_predictions
    LSTM_AVAILABLE = True
    print("🧠 [Agent] LSTM predictor loaded.")
except Exception as e:
    LSTM_AVAILABLE = False
    print(f"⚠️  [Agent] LSTM unavailable ({e}). Using static reliability.")
    def get_predicted_reliability(c): return 0.84
    def get_all_predictions(): return {}
    def refresh_predictions(s=None): return {}

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ═══════════════════════════════════════════════════════════════
# LSTM-POWERED PROACTIVE RISK FLAGGING
# ═══════════════════════════════════════════════════════════════

def auto_flag_at_risk(shipments: list) -> list:
    """
    Scans In Transit shipments using FOUR signals:

      Signal 1  LSTM predicted reliability   (primary — forward-looking)
      Signal 2  Tight ETA window             (<8 hours)
      Signal 3  High delay probability       (>0.65)
      Signal 4  Heavy cargo on long route    (cost exposure)

    LSTM replaces the static partner_reliability field — the agent
    now acts on WHERE the carrier is heading, not where it was.
    """
    if LSTM_AVAILABLE:
        try: refresh_predictions(shipments)
        except Exception as e:
            print(f"  ⚠️ LSTM refresh failed: {e}")

    already_actioned = {
        "At Risk", "Pending Approval", "Rerouted (Auto)", "Rerouted (Approved)",
        "On Hold", "Carrier Switch Pending", "Expedited", "Monitoring"
    }

    for s in shipments:
        if s.status in already_actioned:
            continue

        score   = 0.0
        reasons = []

        # Signal 1 — LSTM prediction (replaces static reliability)
        lstm_rel = get_predicted_reliability(s.carrier)
        if   lstm_rel < 0.72:
            score += 0.45
            reasons.append(f"LSTM: carrier critical ({lstm_rel:.2f})")
        elif lstm_rel < 0.80:
            score += 0.28
            reasons.append(f"LSTM: carrier degrading ({lstm_rel:.2f})")
        elif lstm_rel < 0.84:
            score += 0.12
            reasons.append(f"LSTM: carrier under watch ({lstm_rel:.2f})")

        # Signal 2 — Tight ETA
        if s.status != "Delivered" and 0 < s.eta_hours < 8:
            score += 0.25
            reasons.append(f"ETA critical ({s.eta_hours}h)")

        # Signal 3 — Elevated delay probability
        if   s.delay_probability > 0.65:
            score += 0.30
            reasons.append(f"High delay prob ({s.delay_probability:.2f})")
        elif s.delay_probability > 0.50:
            score += 0.15

        # Signal 4 — Heavy cargo + long route
        if s.weight_kg > 1500 and s.distance_km > 2500:
            score += 0.10
            reasons.append("Heavy+long route exposure")

        if score >= 0.50 and s.status == "In Transit":
            s.status = "At Risk"
            s.delay_probability = min(0.92, s.delay_probability + score * 0.30)

    return shipments


# ═══════════════════════════════════════════════════════════════
# NODE 1 — OBSERVE
# ═══════════════════════════════════════════════════════════════

def observe(state: AgentState):
    updated = auto_flag_at_risk(state.get("shipments", []))
    at_risk = [s for s in updated if s.status == "At Risk"]

    if not at_risk:
        return {
            "shipments": updated,
            "messages":  [SystemMessage(content="System normal. No shipments at risk.")],
            "severity_level": "None",
        }

    ctx = f"OBSERVE — {len(at_risk)} SHIPMENT(S) AT RISK:\n"
    for s in at_risk:
        lstm_r = get_predicted_reliability(s.carrier)
        ctx += (f"  • {s.shipment_id} | {s.origin}→{s.destination} "
                f"| {s.carrier}  static_rel={s.partner_reliability:.2f} "
                f"lstm_pred={lstm_r:.2f}  delay_prob={s.delay_probability:.2f} "
                f"eta={s.eta_hours}h\n")

    alerts = state.get("alerts", [])
    if alerts:
        ctx += "\nACTIVE ALERTS:\n"
        for a in alerts:
            ctx += f"  • [{a.severity}] {a.type} @ {a.location} — {a.description}\n"

    if LSTM_AVAILABLE:
        preds = get_all_predictions()
        ctx += "\nLSTM CARRIER FORECAST:\n"
        for c, p in preds.items():
            ctx += (f"  • {c}: pred={p['predicted_reliability']:.3f} "
                    f"trend={p['trend']:+.3f} {p['risk_flag']}\n")

    return {
        "shipments": updated,
        "messages":  [SystemMessage(content=ctx)],
        "severity_level": "pending",
    }


# ═══════════════════════════════════════════════════════════════
# NODE 2 — REASON
# ═══════════════════════════════════════════════════════════════

def reason(state: AgentState):
    msgs = state.get("messages", [])
    if "System normal" in msgs[0].content:
        return {"hypothesis": "All systems operational.", "messages": msgs}

    prompt = HumanMessage(content=(
        "You are an expert logistics analyst.\n"
        "Based on the context (which includes LSTM carrier forecasts):\n"
        "1. ROOT CAUSE — carrier degradation trend, route disruption, or external event.\n"
        "2. CASCADING IMPACT — downstream partners and shipments at risk.\n"
        "3. PATTERN NOTE — if LSTM forecast confirms or contradicts static signals.\n"
        "3 concise sentences maximum."
    ))
    resp = llm.invoke(msgs + [prompt])
    return {"hypothesis": resp.content, "messages": msgs + [resp]}


# ═══════════════════════════════════════════════════════════════
# NODE 3 — DECIDE
# ═══════════════════════════════════════════════════════════════

def decide(state: AgentState):
    hyp   = state.get("hypothesis", "")
    msgs  = state.get("messages", [])
    alerts= state.get("alerts", [])

    if hyp == "All systems operational.":
        return {"decision": "Maintain current routes.", "messages": msgs,
                "confidence": 99, "action_type": "MONITOR", "severity_level": "None"}

    severity = "Low"
    alert_desc = ""
    for a in alerts:
        alert_desc += a.description + " "
        if a.severity == "High":   severity = "High"
        elif a.severity == "Medium" and severity != "High": severity = "Medium"

    if not alerts:
        at_risk = [s for s in state.get("shipments", []) if s.status == "At Risk"]
        if at_risk:
            alert_desc = f"LSTM-flagged carrier degradation. {len(at_risk)} shipment(s) at risk."
            severity   = "Medium"

    memory = get_past_poa(alert_desc.strip())

    lstm_ctx = ""
    if LSTM_AVAILABLE:
        preds = get_all_predictions()
        lstm_ctx = "\nLSTM CARRIER FORECAST:\n" + "".join(
            f"  {c}: {p['predicted_reliability']:.3f} (trend {p['trend']:+.3f}) {p['risk_flag']}\n"
            for c, p in preds.items()
        )

    prompt = HumanMessage(content=(
        f"Hypothesis: {hyp}\n"
        f"Severity: {severity}\n"
        f"Historical POA: {memory['poa']}\n"
        f"Suggested action from history: {memory['action_type']}\n"
        f"{lstm_ctx}\n"
        "Choose ONE action:\n"
        "  REROUTE        — change physical route\n"
        "  HOLD           — pause dispatch\n"
        "  SWITCH_CARRIER — transfer to higher-reliability carrier\n"
        "  EXPEDITE       — express lane (+15% cost)\n"
        "  ESCALATE       — requires human approval\n"
        "  MONITOR        — watch and wait\n\n"
        "RULES:\n"
        "  - High severity → ESCALATE + '[NEEDS APPROVAL]'\n"
        "  - LSTM shows carrier degradation → prefer SWITCH_CARRIER over REROUTE\n"
        "  - Output Confidence 0-100\n\n"
        "Exact format:\n"
        "Action: [TYPE]\nConfidence: [N]\nReasoning: ...\nTrade-offs: ..."
    ))

    resp    = llm.invoke(msgs + [prompt])
    content = resp.content

    act_m   = re.search(r"Action:\s*(REROUTE|HOLD|SWITCH_CARRIER|EXPEDITE|ESCALATE|MONITOR)",
                         content, re.I)
    conf_m  = re.search(r"Confidence:\s*(\d+)", content)

    action  = act_m.group(1).upper()   if act_m   else memory["action_type"]
    conf    = int(conf_m.group(1))     if conf_m  else memory["confidence_hint"]

    # Safety guardrail: low confidence → escalate
    if conf < 45 and severity != "High":
        content += "\n[LOW CONFIDENCE — escalated] [NEEDS APPROVAL]"
        action   = "ESCALATE"

    return {
        "decision": content, "messages": msgs + [resp],
        "confidence": conf,  "action_type": action, "severity_level": severity,
    }


# ═══════════════════════════════════════════════════════════════
# NODE 4 — ACT
# ═══════════════════════════════════════════════════════════════

def act(state: AgentState):
    decision    = state.get("decision", "")
    action_type = state.get("action_type", "REROUTE")
    shipments   = list(state.get("shipments", []))

    if "Maintain current routes" in decision:
        return {"action_taken": "✅ No action needed.", "shipments": shipments}

    needs_approval = "[NEEDS APPROVAL]" in decision.upper()
    count = 0

    for s in shipments:
        if s.status != "At Risk":
            continue
        count += 1
        if needs_approval:
            s.status = "Pending Approval"
        elif action_type == "REROUTE":
            s.status = "Rerouted (Auto)";         s.delay_probability = 0.10
        elif action_type == "HOLD":
            s.status = "On Hold";                 s.delay_probability = 0.20; s.eta_hours += 24
        elif action_type == "SWITCH_CARRIER":
            s.status = "Carrier Switch Pending";  s.delay_probability = 0.12; s.partner_reliability = 0.92
        elif action_type == "EXPEDITE":
            s.status = "Expedited";               s.delay_probability = 0.05
            s.eta_hours = max(1, s.eta_hours - 12); s.operational_cost *= 1.15
        elif action_type == "MONITOR":
            s.status = "Monitoring"
        else:
            s.status = "Rerouted (Auto)";         s.delay_probability = 0.10

    if needs_approval:
        log = f"⚠️ [{action_type}] plan drafted for {count} shipment(s). Awaiting human approval."
    else:
        log = f"🤖 [{action_type}] autonomously executed for {count} shipment(s) (LSTM-informed)."

    return {"action_taken": log, "shipments": shipments}


# ═══════════════════════════════════════════════════════════════
# LANGGRAPH WORKFLOW
# ═══════════════════════════════════════════════════════════════

workflow = StateGraph(AgentState)
workflow.add_node("observe", observe)
workflow.add_node("reason",  reason)
workflow.add_node("decide",  decide)
workflow.add_node("act",     act)
workflow.add_edge(START, "observe")
workflow.add_edge("observe", "reason")
workflow.add_edge("reason",  "decide")
workflow.add_edge("decide",  "act")
workflow.add_edge("act", END)

app = workflow.compile()