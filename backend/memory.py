import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

load_dotenv()

# Use OpenAI's embedding model to turn text into searchable vectors
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Define where ChromaDB will save its data locally
CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

print("📚 Initializing AtlasAI ChromaDB Memory...")
vector_db = Chroma(
    collection_name="logistics_memory",
    embedding_function=embeddings,
    persist_directory=CHROMA_PATH
)

# --- 1. Synthetic Pre-Known Knowledge Base ---
initial_kb = [
    # --- HIGH SEVERITY (Human Escalation) ---
    Document(
        page_content="Alert: Critical infrastructure destroyed. Total maritime halt. Port Bombing at South Kathryntown.",
        metadata={
            "poa": "Escalated to human operator. Halted all maritime loading. Rerouted critical shipments via emergency air freight, prioritizing high-reliability carriers (e.g., DHL at 0.94 reliability) to bypass the destroyed port.",
            "severity": "High"
        }
    ),
    Document(
        page_content="Alert: Category 5 hurricane halting all inbound and outbound traffic at Haleview.",
        metadata={
            "poa": "Escalated to human operator. Diverted all inbound Haleview transit to inland regional hubs. Sheltered high-weight inventory (90+ kg) to prevent massive operational cost losses from stranded assets.",
            "severity": "High"
        }
    ),

    # --- MEDIUM SEVERITY (Autonomous Actions) ---
    Document(
        page_content="Alert: Vessels rerouting due to elevated security risks. Piracy Threat at North Sandraberg.",
        metadata={
            "poa": "Autonomously instructed carriers to reroute maritime vessels 200 nautical miles off the coast of North Sandraberg. Accepted a moderate operational cost increase to maintain partner reliability and secure the payload.",
            "severity": "Medium"
        }
    ),
    Document(
        page_content="Alert: Logistics partner experiencing sudden operational degradation and elevated delay probability above 0.20.",
        metadata={
            "poa": "Autonomously transferred high-priority, low-weight shipments to alternative carriers with reliability scores above 0.90 to ensure ETA compliance.",
            "severity": "Medium"
        }
    ),

    # --- LOW SEVERITY (Autonomous Actions) ---
    Document(
        page_content="Alert: Severe congestion on main highway causing minor delays. Traffic Jam at Port Elizabeth.",
        metadata={
            "poa": "Autonomously rerouted ground transport (UPS/DHL) to secondary highways. Accepted a minor ETA increase (+3 hours) to prevent total standstill and keep overall delay probability below 0.15.",
            "severity": "Low"
        }
    ),
    Document(
        page_content="Alert: Minor customs delay at destination border checkpoint.",
        metadata={
            "poa": "Autonomously monitored the situation. No physical rerouting required. Sent automated ETA update to end-customer regarding minor 2-hour delay.",
            "severity": "Low"
        }
    )
]

# Only seed the database if it is currently empty
if vector_db._collection.count() == 0:
    print("🌱 Seeding initial Knowledge Base into ChromaDB...")
    vector_db.add_documents(initial_kb)


# --- 2. Search Function (Used in the 'Decide' phase) ---
def get_past_poa(alert_description: str) -> str:
    """Searches ChromaDB for similar past events and returns the Plan of Action."""
    results = vector_db.similarity_search(alert_description, k=1)
    if results:
        return results[0].metadata.get("poa", "No specific historical action recorded.")
    return "No similar historical events found."


# --- 3. Learn Function (Used in the Human Approval phase) ---
def add_learned_action(alert_description: str, severity: str, action_taken: str):
    """Embeds a newly approved action into ChromaDB for future use."""
    new_doc = Document(
        page_content=f"Alert: {alert_description}",
        metadata={"poa": action_taken, "severity": severity}
    )
    vector_db.add_documents([new_doc])
    print(f"\n🧠 [LEARN LOOP] Successfully embedded new experience into ChromaDB!")


# --- Command Line Execution & Testing ---
if __name__ == "__main__":
    print("\n=== AtlasAI Vector Memory Diagnostics ===")
    print(f"📂 Database Path: {CHROMA_PATH}")
    print(f"📄 Total Memories Stored: {vector_db._collection.count()}")

    print("\n🔍 Testing Retrieval (Searching for 'Traffic Jam')...")
    test_query = "Severe congestion on main highway causing minor delays. Traffic Jam at Port Elizabeth."
    result = get_past_poa(test_query)
    print(f"💡 Retrieved Plan of Action:\n   -> {result}")

    print("\n✅ Memory Module is fully operational!")