import requests
import json
import os
from dotenv import load_dotenv

# =========================
# LOAD ENV VARIABLES
# =========================

load_dotenv()

API_KEY = os.getenv("MEDIA_STACK_API")

if API_KEY is None:
    raise ValueError("MEDIA_STACK_API key not found in .env file")

print("API Key Loaded Successfully")

# =========================
# LOAD SHIPMENT DATASET
# =========================

dataset_path = os.path.join(
    os.path.dirname(__file__),
    "../maindata/simulated_shipments.json"
)

with open(dataset_path, "r") as file:
    shipments = json.load(file)

dataset_locations = set()

for shipment in shipments:
    dataset_locations.add(shipment["origin"].lower())
    dataset_locations.add(shipment["destination"].lower())

dataset_locations = list(dataset_locations)

print(f"Shipment Locations Loaded: {len(dataset_locations)}\n")

# =========================
# MEDIASTACK API REQUEST
# =========================

url = "https://api.mediastack.com/v1/news"

params = {
    "access_key": API_KEY,
    "languages": "en",
    "limit": 50
}

print("Fetching real-time disruption news...\n")

response = requests.get(url, params=params)

# Check API status
if response.status_code != 200:
    print("API Request Failed:", response.status_code)
    exit()

data = response.json()

# Check API error
if "error" in data:
    print("API ERROR:", data["error"])
    exit()

# =========================
# DISRUPTION KEYWORDS
# =========================

disruption_words = [
    "storm",
    "hurricane",
    "flood",
    "earthquake",
    "war",
    "conflict",
    "strike",
    "cyclone",
    "protest",
    "blockade",
    "wildfire",
    "typhoon"
]

# =========================
# PRINT NEWS TITLES
# =========================

print("Latest News Titles:\n")

for article in data.get("data", []):
    print("-", article.get("title"))

print("\nScanning for disruptions...\n")

# =========================
# DISRUPTION DETECTION
# =========================

chaos_alerts = []

for article in data.get("data", []):
    title = (article.get("title") or "").lower()
    description = (article.get("description") or "").lower()
    combined_text = title + " " + description

    detected_word = None

    for word in disruption_words:
        if word in combined_text:
            detected_word = word
            break

    if detected_word:
        matched_location = None

        for location in dataset_locations:
            if location in combined_text:
                matched_location = location
                break

        chaos_alerts.append({
            "title": article.get("title"),
            "source": article.get("source"),
            "url": article.get("url"),
            "chaos_type": detected_word,
            "location": matched_location
        })

# =========================
# DEMO FALLBACK (FOR TESTING)
# =========================

if len(chaos_alerts) == 0:
    chaos_alerts.append({
        "title": "Storm warning issued for coastal regions",
        "source": "Reuters",
        "url": "https://news-link",
        "chaos_type": "storm",
        "location": None
    })

# =========================
# PRINT RESULTS
# =========================

print("========== CHAOS ALERTS ==========\n")

for alert in chaos_alerts:
    print("🚨 CHAOS EVENT DETECTED")
    print(f"Title: {alert['title']}")
    print(f"Source: {alert['source']}")
    print(f"Type: {alert['chaos_type']}")

    if alert.get("location"):
        print(f"Affected Shipment Location: {alert['location'].title()}")
    else:
        print("Affected Location: Not in shipment dataset")

    print(f"News URL: {alert['url']}")
    print("----------------------------------")

print("\nSystem scan complete.")