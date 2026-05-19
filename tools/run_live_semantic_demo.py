from __future__ import annotations

import json
from pathlib import Path

from energy_brain.ui.live_ems_semantic_engine import (
    build_semantic_state,
)

snapshot = {
    "sensor.alphaess_current_pv_production": 3600,
    "sensor.alphaess_current_house_load": 400,
    "sensor.alphaess_power_battery": -1200,
    "sensor.alphaess_power_grid": -600,
    "sensor.alphaess_soc_battery": 60,
    "sensor.energybrain_required_reserve_soc": 25,
    "input_boolean.alphaess_helper_dispatch": "off",
    "binary_sensor.aanwezigheidssensor_woonkamer_occupancy": "on",
    "input_boolean.ai_ir_override_keuken": "off",
    "sensor.energybrain_prices_forecast": [
        0.18,
        0.17,
        0.24,
        0.31,
    ],
}

state = build_semantic_state(snapshot)

result = {
    "energy_mode": state.energy_mode,
    "battery_state": state.battery_state,
    "grid_state": state.grid_state,
    "solar_state": state.solar_state,
    "comfort_state": state.comfort_state,
    "planner_state": state.planner_state,
    "confidence": state.confidence,
    "glow_intensity": state.glow_intensity,
    "timeline_hint": state.timeline_hint,
}

Path("reports/live_semantic_state.json").write_text(
    json.dumps(result, indent=2)
)

print()
print("===================================")
print("LIVE ENERGY BRAIN SEMANTIC STATE")
print("===================================")

for k, v in result.items():
    print(f"{k}: {v}")

print()
print("saved:")
print("reports/live_semantic_state.json")
