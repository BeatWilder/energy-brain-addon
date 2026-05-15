from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import logging
import time
from dataclasses import asdict

from .config import load_config
from .controller import validate_and_decide
from .ha_client import HomeAssistantClient, snapshot_as_dict
from .planner import build_plan


logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger("energy_brain")


def main() -> None:
    config = load_config()
    client = HomeAssistantClient()
    LOGGER.info(_json_log("startup", {"mode": config.mode, "cycle_seconds": config.cycle_seconds}))

    while True:
        started = time.time()
        state = run_cycle(config, client)
        LOGGER.info(_json_log("cycle", state))
        elapsed = time.time() - started
        time.sleep(max(1.0, config.cycle_seconds - elapsed))


def run_cycle(config, client: HomeAssistantClient) -> dict:
    snapshot = client.read_snapshot(config)
    plan = build_plan(snapshot, config.battery, config.horizon_steps)
    decision = validate_and_decide(plan, config)
    execution = {"attempted": False}
    if decision.execute:
        execution = {"attempted": True, **client.write_battery_setpoint(config, decision.setpoint_kw)}
    return {
        "mode": config.mode,
        "snapshot": snapshot_as_dict(snapshot),
        "plan": asdict(plan),
        "controller": asdict(decision),
        "execution": execution,
    }


def _json_log(event: str, payload: dict) -> str:
    return json.dumps({"event": event, **payload}, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    main()


def write_cycle_history(state: dict) -> None:
    path = Path("/data/energy_brain_cycles.jsonl")
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **state,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
