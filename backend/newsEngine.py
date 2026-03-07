import requests
import json
import os
from dotenv import load_dotenv


def get_latest_news():
    load_dotenv()
    API_KEY = os.getenv("MEDIA_STACK_API")

    if not API_KEY:
        print("❌ MEDIA_STACK_API key not found")
        return []

    # Load Locations
    dataset_path = os.path.join(os.path.dirname(__file__), "../maindata/simulated_shipments.json")
    try:
        with open(dataset_path, "r", encoding="utf-8") as file:
            shipments = json.load(file)

        dataset_locations = {shipment["origin"].lower() for shipment in shipments}
        dataset_locations.update(shipment["destination"].lower() for shipment in shipments)
        dataset_locations = list(dataset_locations)

    except Exception as e:
        print(f"Error loading locations for news engine: {e}")
        dataset_locations = []

    # Fetch News
    url = "https://api.mediastack.com/v1/news"
    params = {"access_key": API_KEY, "languages": "en", "limit": 50}

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print("News API request failed")
            return []

        data = response.json()

        if "error" in data:
            print("MediaStack API Error:", data["error"])
            return []

    except Exception as e:
        print(f"News API Error: {e}")
        return []

    # Disruption Categories
    natural_events = [
        "storm", "hurricane", "flood",
        "earthquake", "cyclone", "wildfire", "typhoon"
    ]

    geopolitical_events = [
        "war", "conflict", "strike",
        "protest", "blockade"
    ]

    disruption_words = natural_events + geopolitical_events

    chaos_alerts = []

    for article in data.get("data", []):

        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        combined_text = title + " " + description

        detected_word = None
        event_type = None

        # Natural event detection
        for word in natural_events:
            if word in combined_text:
                detected_word = word
                event_type = "Natural Event"
                break

        # Geopolitical detection
        if event_type is None:
            for word in geopolitical_events:
                if word in combined_text:
                    detected_word = word
                    event_type = "Geopolitical Event"
                    break

        if detected_word:

            matched_location = next(
                (loc for loc in dataset_locations if loc in combined_text),
                None
            )

            chaos_alerts.append({
                "title": article.get("title"),
                "source": article.get("source"),
                "url": article.get("url"),
                "chaos_type": detected_word.upper(),
                "event_type": event_type,
                "location": matched_location.title() if matched_location else None
            })

    # Demo Fallback (so UI never empty)
    if len(chaos_alerts) == 0:
        chaos_alerts.append({
            "title": "Storm warning issued for coastal regions near major transit hubs.",
            "source": "Reuters",
            "url": "#",
            "chaos_type": "STORM",
            "event_type": "Natural Event",
            "location": None
        })

    return chaos_alerts


if __name__ == "__main__":
    print(get_latest_news())