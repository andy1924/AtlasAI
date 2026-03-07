import os
import re
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from state import AgentState, Shipment, Alert
from memory import get_past_poa

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ─────────────────────────────────────────────
# HELPER: Proactive risk scoring
# Runs before the agent loop — auto-flags shipments
# without needing a manual chaos injection.
# ─────────────────────────────────────────────
def auto_flag_at_risk(shipments: list[Shipment]) -> list[Shipment]:
    """
    Proactively flags shipments At Risk based on multi-signal scoring.
    This closes the 'Observe' gap — the agent detects early warning signals,
    not just manually-injected chaos events.
    """
    for shipment in shipments:
        # Skip shipments already actioned
        if shipment.status in ["At Risk", "Pending Approval",
                                "Rerouted (Auto)", "Rerouted (Approved)",
                                "On Hold", "Carrier Switch Pending", "Expedited"]:
            continue

        risk_score = 0.0

        # Signal 1: Carrier reliability degradation
        if shipment.partner_reliability < 0.70:
            risk_score += 0.35
        elif shipment.partner_reliability < 0.80:
            risk_score += 0.15

        # Signal 2: Tight ETA window (non-delivered)
        if shipment.status != "Delivered" and 0 < shipment.eta_hours < 8:
            risk_score += 0.25

        # Signal 3: Already elevated delay probability
        if shipment.delay_probability > 0.65:
            risk_score += 0.30
        elif shipment.delay_probability > 0.50:
            risk_score += 0.15

        # Signal 4: Heavy cargo on long route — high cost exposure
        if shipment.weight_kg > 1500 and shipment.distance_km > 2500:
            risk_score += 0.15

        if risk_score >= 0.50 and shipment.status == "In Transit":
            shipment.status = "At Risk"
            # Bump delay probability to reflect detected signals
            shipment.delay_probability = min(0.92, shipment.delay_probability + risk_score * 0.4)

    return shipments


# ─────────────────────────────────────────────
# NODE 1: OBSERVE
# ─────────────────────────────────────────────
def observe(state: AgentState):
    """
    Scans all shipments (including proactively flagged ones) and
    active alerts, builds a structured context string for the LLM.
    """
    # Run proactive flagging first
    updated_shipments = auto_flag_at_risk(state.get("shipments", []))

    at_risk = [s for s in updated_shipments if s.status == "At Risk"]

    if not at_risk:
        return {
            "shipments": updated_shipments,
            "messages": [SystemMessage(content="System normal. No shipments currently at risk.")],
            "severity_level": "None"
        }

    context = f"OBSERVE — {len(at_risk)} SHIPMENTS AT RISK:\n"
    for s in at_risk:
        context += (
            f"  • {s.shipment_id} | {s.origin} → {s.destination} "
            f"| Carrier: {s.carrier} (reliability: {s.partner_reliability:.2f}) "
            f"| Delay prob: {s.delay_probability:.2f} "
            f"| ETA: {s.eta_hours}h | Weight: {s.weight_kg}kg\n"
        )

    alerts = state.get("alerts", [])
    if alerts:
        context += "\nACTIVE DISRUPTION ALERTS:\n"
        for a in alerts:
            context += f"  • [{a.severity}] {a.type} @ {a.location} — {a.description}\n"

    return {
        "shipments": updated_shipments,
        "messages": [SystemMessage(content=f"System Context:\n{context}")],
        "severity_level": "pending"
    }


# ─────────────────────────────────────────────
# NODE 2: REASON
# ─────────────────────────────────────────────
def reason(state: AgentState):
    """
    Uses the LLM to identify patterns and form a specific
    hypothesis about root causes and cascading risk.
    """
    messages = state.get("messages", [])
    if "System normal" in messages[0].content:
        return {"hypothesis": "All systems operational.", "messages": messages}

    prompt = HumanMessage(content=(
        "You are an expert logistics operations analyst.\n"
        "Based on the system context above:\n"
        "1. Identify the ROOT CAUSE of the risk (carrier failure, route disruption, external event, etc.)\n"
        "2. Describe the CASCADING IMPACT — which downstream shipments or partners are at risk.\n"
        "3. Identify any PATTERNS (e.g., multiple shipments from same carrier, same region).\n"
        "Keep your response to 3 concise sentences."
    ))
    response = llm.invoke(messages + [prompt])
    return {"hypothesis": response.content, "messages": messages + [response]}


# ─────────────────────────────────────────────
# NODE 3: DECIDE
# ─────────────────────────────────────────────
def decide(state: AgentState):
    """
    Retrieves historical POA from ChromaDB via RAG, then instructs
    the LLM to choose from a named action menu with a confidence score.
    """
    hypothesis = state.get("hypothesis", "")
    messages = state.get("messages", [])
    alerts = state.get("alerts", [])

    if hypothesis == "All systems operational.":
        return {
            "decision": "Maintain current routes.",
            "messages": messages,
            "confidence": 99,
            "action_type": "MONITOR",
            "severity_level": "None"
        }

    # Determine highest severity
    highest_severity = "Low"
    current_alert_desc = ""
    for a in alerts:
        current_alert_desc += a.description + " "
        if a.severity == "High":
            highest_severity = "High"
        elif a.severity == "Medium" and highest_severity != "High":
            highest_severity = "Medium"

    # Also consider proactively flagged shipments with no alert
    if not alerts:
        at_risk = [s for s in state.get("shipments", []) if s.status == "At Risk"]
        if at_risk:
            current_alert_desc = f"Carrier degradation detected. {len(at_risk)} shipments at risk."
            highest_severity = "Medium"

    # RAG memory retrieval
    memory = get_past_poa(current_alert_desc.strip())
    historical_poa = memory["poa"]
    suggested_action = memory["action_type"]
    confidence_hint = memory["confidence_hint"]

    prompt = HumanMessage(content=(
        f"Hypothesis: {hypothesis}\n\n"
        f"SEVERITY CLASSIFICATION: '{highest_severity}'\n"
        f"HISTORICAL KNOWLEDGE BASE: Similar past event POA was: '{historical_poa}'\n"
        f"SUGGESTED ACTION TYPE from history: {suggested_action}\n\n"
        "Choose ONE action from this menu:\n"
        "  REROUTE       — Change the shipment's physical route\n"
        "  HOLD          — Pause dispatch and wait for disruption to resolve\n"
        "  SWITCH_CARRIER — Transfer to a higher-reliability carrier\n"
        "  EXPEDITE      — Upgrade to express/priority lane, accept cost increase\n"
        "  ESCALATE      — Flag for human operator approval (REQUIRED for High severity)\n"
        "  MONITOR       — No action, continue monitoring\n\n"
        "RULES:\n"
        "  - If severity is 'High', action MUST be ESCALATE and include '[NEEDS APPROVAL]'\n"
        "  - If severity is 'Medium' or 'Low', choose the most appropriate action autonomously\n"
        "  - You MUST provide a Confidence score (0-100) based on how closely the historical precedent matches\n\n"
        "Respond EXACTLY in this format:\n"
        "Action: [ACTION_TYPE]\n"
        "Confidence: [NUMBER]\n"
        "Reasoning: Based on historical precedent where [explain the past POA and why you are applying/adapting it].\n"
        "Trade-offs: [What operational cost or time trade-off does this action make?]"
    ))

    response = llm.invoke(messages + [prompt])
    content = response.content

    # Parse action type and confidence from response
    action_match = re.search(r"Action:\s*(REROUTE|HOLD|SWITCH_CARRIER|EXPEDITE|ESCALATE|MONITOR)", content, re.IGNORECASE)
    confidence_match = re.search(r"Confidence:\s*(\d+)", content)

    parsed_action = action_match.group(1).upper() if action_match else suggested_action
    parsed_confidence = int(confidence_match.group(1)) if confidence_match else confidence_hint

    # Safety override: if confidence too low for autonomous action, escalate
    if parsed_confidence < 45 and highest_severity != "High":
        content += "\n[LOW CONFIDENCE — escalated for human review] [NEEDS APPROVAL]"
        parsed_action = "ESCALATE"

    return {
        "decision": content,
        "messages": messages + [response],
        "confidence": parsed_confidence,
        "action_type": parsed_action,
        "severity_level": highest_severity
    }


# ─────────────────────────────────────────────
# NODE 4: ACT
# ─────────────────────────────────────────────
def act(state: AgentState):
    """
    Executes the decision. Applies the correct status and delay_probability
    per action type. Escalates to human if HIGH severity or low confidence.
    """
    decision = state.get("decision", "")
    action_type = state.get("action_type", "REROUTE")
    updated_shipments = list(state.get("shipments", []))

    if "Maintain current routes" in decision:
        return {
            "action_taken": "✅ Monitored situation. No action needed.",
            "shipments": updated_shipments
        }

    needs_approval = "[NEEDS APPROVAL]" in decision.upper()
    affected_count = 0
    action_log = ""

    for shipment in updated_shipments:
        if shipment.status == "At Risk":
            affected_count += 1

            if needs_approval:
                shipment.status = "Pending Approval"
                action_log = (
                    f"⚠️ Drafted {action_type} plan for {affected_count} shipment(s). "
                    f"Escalated to human operator (HIGH severity or LOW confidence)."
                )
            else:
                # Apply action-specific state changes
                if action_type == "REROUTE":
                    shipment.status = "Rerouted (Auto)"
                    shipment.delay_probability = 0.10
                elif action_type == "HOLD":
                    shipment.status = "On Hold"
                    shipment.delay_probability = 0.20
                    shipment.eta_hours = shipment.eta_hours + 24
                elif action_type == "SWITCH_CARRIER":
                    shipment.status = "Carrier Switch Pending"
                    shipment.delay_probability = 0.12
                    shipment.partner_reliability = 0.92  # Assume switched to reliable carrier
                elif action_type == "EXPEDITE":
                    shipment.status = "Expedited"
                    shipment.delay_probability = 0.05
                    shipment.eta_hours = max(1, shipment.eta_hours - 12)
                    shipment.operational_cost = shipment.operational_cost * 1.15  # 15% cost increase
                elif action_type == "MONITOR":
                    shipment.status = "Monitoring"
                    # No structural change
                else:
                    shipment.status = "Rerouted (Auto)"
                    shipment.delay_probability = 0.10

                action_log = (
                    f"🤖 [{action_type}] Autonomously executed for {affected_count} shipment(s) "
                    f"based on historical precedent."
                )

    return {"action_taken": action_log, "shipments": updated_shipments}


# ─────────────────────────────────────────────
# BUILD THE LANGGRAPH WORKFLOW
# ─────────────────────────────────────────────
workflow = StateGraph(AgentState)
workflow.add_node("observe", observe)
workflow.add_node("reason", reason)
workflow.add_node("decide", decide)
workflow.add_node("act", act)

workflow.add_edge(START, "observe")
workflow.add_edge("observe", "reason")
workflow.add_edge("reason", "decide")
workflow.add_edge("decide", "act")
workflow.add_edge("act", END)

app = workflow.compile()