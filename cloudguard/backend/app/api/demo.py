"""Demo/Simulation API — triggers attack scenarios for demonstration."""
import random
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import EventIngest
from app.services.event_service import ingest_event
from app.telemetry.simulator import (
    ATTACK_SCENARIOS,
    generate_attack_scenario,
    get_random_container,
    SIMULATED_CONTAINERS,
)

router = APIRouter()


@router.get("/demo/scenarios", tags=["Demo"])
async def list_scenarios():
    """List all available attack simulation scenarios."""
    return [
        {
            "id": key,
            "name": val["name"],
            "description": val["description"],
            "expected_severity": val["expected_severity"],
            "expected_rules": val["expected_rules"],
        }
        for key, val in ATTACK_SCENARIOS.items()
    ]


@router.post("/demo/simulate/{scenario_id}", tags=["Demo"])
async def run_simulation(
    scenario_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    container_id: Optional[str] = None,
):
    """
    Trigger an attack simulation scenario.

    Generates harmless simulated events that flow through the full
    detection pipeline: events → rules → risk score → incident.

    Safe: no real system calls, network connections, or destructive actions.
    """
    if scenario_id not in ATTACK_SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario '{scenario_id}'. Available: {list(ATTACK_SCENARIOS.keys())}",
        )

    scenario_meta = ATTACK_SCENARIOS[scenario_id]

    # Select target container
    container = None
    if container_id:
        container = next(
            (c for c in SIMULATED_CONTAINERS if c["container_id"] == container_id), None
        )
    if not container:
        container = get_random_container()

    # Generate events
    raw_events = generate_attack_scenario(scenario_id, container)

    # Ingest each event through the pipeline
    ingested_ids = []
    for raw in raw_events:
        event_data = EventIngest(**{k: v for k, v in raw.items() if k != "timestamp"})
        event = await ingest_event(db, event_data)
        ingested_ids.append(event.id)

    return {
        "scenario": scenario_id,
        "name": scenario_meta["name"],
        "description": scenario_meta["description"],
        "target_container": container["name"],
        "events_generated": len(ingested_ids),
        "event_ids": ingested_ids,
        "expected_severity": scenario_meta["expected_severity"],
        "expected_rules": scenario_meta["expected_rules"],
        "message": "Simulation complete. Check /api/incidents for results.",
    }


@router.post("/demo/simulate-all", tags=["Demo"])
async def run_all_simulations(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Run all attack scenarios in sequence for a comprehensive demo."""
    results = []
    for scenario_id in ATTACK_SCENARIOS:
        container = get_random_container()
        raw_events = generate_attack_scenario(scenario_id, container)
        event_ids = []
        for raw in raw_events:
            event_data = EventIngest(**{k: v for k, v in raw.items() if k != "timestamp"})
            event = await ingest_event(db, event_data)
            event_ids.append(event.id)

        results.append({
            "scenario": scenario_id,
            "name": ATTACK_SCENARIOS[scenario_id]["name"],
            "container": container["name"],
            "events_generated": len(event_ids),
        })

    return {
        "scenarios_run": len(results),
        "results": results,
        "message": "All simulations complete. Check /api/incidents and /api/analytics.",
    }
