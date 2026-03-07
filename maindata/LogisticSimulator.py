import random
import numpy as np
import json
import os
from faker import Faker

# -------------------------
# CONFIG
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(BASE_DIR, "simulated_shipments.json")

NUM_SIMULATIONS = 1000

fake = Faker()

# -------------------------
# DISRUPTION SIMULATION
# -------------------------

def apply_disruption(shipment):

    if shipment["status"] == "Delivered":
        return shipment

    chance = random.random()

    if chance < shipment["delay_probability"]:

        shipment["status"] = "Delayed"

        shipment["delay_reason"] = random.choice([
            "Weather disruption",
            "Port congestion",
            "Carrier capacity issue",
            "Customs clearance delay",
            "Warehouse backlog"
        ])

        shipment["eta_hours"] += random.randint(12, 48)

    return shipment


# -------------------------
# SHIPMENT GENERATOR
# -------------------------

def generate_shipment():

    status = random.choice([
        "In Transit",
        "Delivered",
        "At Warehouse"
    ])

    eta_hours = 0 if status == "Delivered" else random.randint(5, 72)

    shipment = {

        "shipment_id": fake.unique.bothify(text="SHP-######"),

        "origin": fake.city(),

        "destination": fake.city(),

        "carrier": random.choice([
            "DHL",
            "FedEx",
            "UPS",
            "BlueDart",
            "Maersk"
        ]),

        "weight_kg": round(random.uniform(1, 100), 2),

        "distance_km": random.randint(50, 2000),

        "eta_hours": eta_hours,

        "status": status,

        "delay_probability": float(round(np.random.beta(2, 5), 2)),

        "operational_cost": round(random.uniform(500.00, 15000.00), 2),

        "partner_reliability": round(random.uniform(0.70, 0.99), 2),

        "timestamp": fake.date_time_between(start_date='-1w', end_date='now').isoformat()
    }

    shipment = apply_disruption(shipment)

    return shipment


# -------------------------
# SIMULATION ENGINE
# -------------------------

def run_simulation():
    # Clear the JSON file
    with open(OUTPUT_JSON, "w") as f:
        json.dump([], f, indent=4)

    # Generate new shipments
    shipments = []
    for _ in range(NUM_SIMULATIONS):
        shipment = generate_shipment()
        shipments.append(shipment)

    # Write the shipments
    with open(OUTPUT_JSON, "w") as f:
        json.dump(shipments, f, indent=4)

    print(f"{NUM_SIMULATIONS} simulated shipments saved to {OUTPUT_JSON}")


# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":
    run_simulation()