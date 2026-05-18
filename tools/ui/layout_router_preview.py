from __future__ import annotations

import json

from energy_brain.ui.layout_router import (
    build_layout_view,
)

sample_payload = {
    "soc_percent": 68,
    "current_action": "charge",
    "price": -0.12,
}

preview = {
    "desktop": build_layout_view(
        sample_payload,
        "desktop",
    ),
    "tablet": build_layout_view(
        sample_payload,
        "tablet",
    ),
    "mobile": build_layout_view(
        sample_payload,
        "mobile",
    ),
    "auto": build_layout_view(
        sample_payload,
        "auto",
    ),
}

print(json.dumps(preview, indent=2))
