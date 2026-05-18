from __future__ import annotations

import json

from energy_brain.ui.tablet_renderer import (
    render_tablet_cockpit,
)

payload = {
    "soc_percent": 68,
    "current_action": "charge",
    "price": -0.12,
    "solar_kw": 3.2,
    "house_kw": 2.1,
    "battery_kw": 1.1,
    "grid_kw": -0.6,
    "reasons": [
        "Negative energy price",
        "Reserve remains protected",
        "PV surplus expected",
    ],
}

result = render_tablet_cockpit(payload)

print(json.dumps(result, indent=2))
