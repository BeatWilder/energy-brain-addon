from __future__ import annotations

import json

from energy_brain.ui.components.tesla_powerflow import (
    build_tesla_powerflow,
)

payload = build_tesla_powerflow()

print(json.dumps(payload, indent=2))
