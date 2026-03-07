import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

print("📚 Initializing AtlasAI ChromaDB Memory...")
vector_db = Chroma(
    collection_name="logistics_memory",
    embedding_function=embeddings,
    persist_directory=CHROMA_PATH
)

# --- 1. Synthetic Pre-Seeded Knowledge Base ---
initial_kb = [
    # HIGH SEVERITY — always escalate to human
    Document(
        page_content="Alert: Critical infrastructure destroyed. Total maritime halt. Port Bombing at South Kathryntown.",
        metadata={
            "poa": "ESCALATE. Halted all maritime loading. Rerouted critical shipments via emergency air freight, prioritizing high-reliability carriers (e.g., DHL at 0.94 reliability) to bypass the destroyed port.",
            "severity": "High",
            "action_type": "ESCALATE",
            "outcome": "success"
        }
    ),
    Document(
        page_content="Alert: Category 5 hurricane halting all inbound and outbound traffic at Haleview.",
        metadata={
            "poa": "ESCALATE. Diverted all inbound Haleview transit to inland regional hubs. Sheltered high-weight inventory (90+ kg) to prevent operational cost losses from stranded assets.",
            "severity": "High",
            "action_type": "ESCALATE",
            "outcome": "success"
        }
    ),

    # MEDIUM SEVERITY — autonomous action
    Document(
        page_content="Alert: Vessels rerouting due to elevated security risks. Piracy Threat at North Sandraberg.",
        metadata={
            "poa": "REROUTE. Instructed carriers to reroute maritime vessels 200 nautical miles off the coast of North Sandraberg. Accepted moderate operational cost increase to secure payload.",
            "severity": "Medium",
            "action_type": "REROUTE",
            "outcome": "success"
        }
    ),
    Document(
        page_content="Alert: Logistics partner experiencing sudden operational degradation and elevated delay probability above 0.20.",
        metadata={
            "poa": "SWITCH_CARRIER. Transferred high-priority, low-weight shipments to alternative carriers with reliability scores above 0.90 to ensure ETA compliance.",
            "severity": "Medium",
            "action_type": "SWITCH_CARRIER",
            "outcome": "success"
        }
    ),
    Document(
        page_content="Alert: Port workers strike announced. Partial loading halt expected for 48 hours.",
        metadata={
            "poa": "HOLD. Placed all outbound shipments on hold for 48 hours pending strike resolution. Notified downstream partners of ETA adjustment.",
            "severity": "Medium",
            "action_type": "HOLD",
            "outcome": "success"
        }
    ),

    # LOW SEVERITY — monitor or minor adjustment
    Document(
        page_content="Alert: Severe congestion on main highway causing minor delays. Traffic Jam at Port Elizabeth.",
        metadata={
            "poa": "REROUTE. Rerouted ground transport (UPS/DHL) to secondary highways. Accepted minor ETA increase (+3 hours) to prevent total standstill and keep delay probability below 0.15.",
            "severity": "Low",
            "action_type": "REROUTE",
            "outcome": "success"
        }
    ),
    Document(
        page_content="Alert: Minor customs delay at destination border checkpoint.",
        metadata={
            "poa": "MONITOR. No physical rerouting required. Sent automated ETA update to end-customer regarding minor 2-hour delay.",
            "severity": "Low",
            "action_type": "MONITOR",
            "outcome": "success"
        }
    ),
    Document(
        page_content="Alert: High-priority shipment at risk due to tight ETA and low carrier reliability score.",
        metadata={
            "poa": "EXPEDITE. Upgraded shipment to express lane and switched to highest-reliability available carrier. Accepted 15% cost increase to meet SLA.",
            "severity": "Medium",
            "action_type": "EXPEDITE",
            "outcome": "success"
        }
    ),
]

# Seed only if empty
if vector_db._collection.count() == 0:
    print("🌱 Seeding initial Knowledge Base into ChromaDB...")
    vector_db.add_documents(initial_kb)
    print(f"✅ Seeded {len(initial_kb)} historical POAs.")


# --- 2. Search Function — returns POA + action_type + outcome context ---
def get_past_poa(alert_description: str) -> dict:
    """
    Searches ChromaDB for the most similar past event.
    Returns the POA text, action_type, and outcome so the agent
    can make a more informed decision.
    """
    results = vector_db.similarity_search(alert_description, k=3)

    if not results:
        return {
            "poa": "No similar historical events found. Use best judgment.",
            "action_type": "REROUTE",
            "outcome": "unknown",
            "confidence_hint": 30
        }

    # Prefer successful outcomes — weight the top result
    successful = [r for r in results if r.metadata.get("outcome") == "success"]
    best = successful[0] if successful else results[0]

    # Confidence hint: higher if we have multiple successful precedents
    confidence_hint = 85 if len(successful) >= 2 else 65 if len(successful) == 1 else 40

    return {
        "poa": best.metadata.get("poa", "No action recorded."),
        "action_type": best.metadata.get("action_type", "REROUTE"),
        "outcome": best.metadata.get("outcome", "unknown"),
        "confidence_hint": confidence_hint
    }


# --- 3. Learn Function — records outcome-tagged experience ---
def add_learned_action(alert_description: str, severity: str, action_taken: str,
                       action_type: str = "REROUTE", outcome: str = "success"):
    """
    Embeds a new experience into ChromaDB with outcome tagging.
    Called after human approval (outcome='success') or after
    evaluate_outcomes detects a failure (outcome='failure').
    """
    new_doc = Document(
        page_content=f"Alert: {alert_description}",
        metadata={
            "poa": action_taken,
            "severity": severity,
            "action_type": action_type,
            "outcome": outcome
        }
    )
    vector_db.add_documents([new_doc])
    print(f"\n🧠 [LEARN LOOP] Embedded new {outcome.upper()} experience into ChromaDB!")


# --- 4. Outcome Update — marks an existing memory as failed ---
def mark_outcome(alert_description: str, outcome: str):
    """
    After evaluate_outcomes runs, call this to add a failure record
    so future retrievals deprioritise the failed strategy.
    """
    results = vector_db.similarity_search(alert_description, k=1)
    if results:
        failed_doc = Document(
            page_content=results[0].page_content,
            metadata={**results[0].metadata, "outcome": outcome}
        )
        vector_db.add_documents([failed_doc])
        print(f"📝 [OUTCOME UPDATE] Marked memory as '{outcome}'")


# --- Diagnostics ---
if __name__ == "__main__":
    print("\n=== AtlasAI Vector Memory Diagnostics ===")
    print(f"📂 Database Path: {CHROMA_PATH}")
    print(f"📄 Total Memories Stored: {vector_db._collection.count()}")

    print("\n🔍 Testing Retrieval (Searching for 'Traffic Jam')...")
    result = get_past_poa("Severe congestion on main highway causing minor delays.")
    print(f"💡 Retrieved POA: {result['poa']}")
    print(f"🎯 Action Type: {result['action_type']}")
    print(f"📊 Confidence Hint: {result['confidence_hint']}%")
    print("\n✅ Memory Module is fully operational!")