from __future__ import annotations

import json

from energy_brain.ui.components.shared_components import (
    explainability_component,
    hero_component,
    powerflow_component,
    runtime_component,
    safety_component,
    timeline_component,
)

payload = {
    "hero": hero_component(),
    "powerflow": powerflow_component(),
    "timeline": timeline_component(),
    "explainability": explainability_component(),
    "safety": safety_component(),
    "runtime": runtime_component(),
}

print(json.dumps(payload, indent=2))
