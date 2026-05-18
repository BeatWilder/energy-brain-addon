from __future__ import annotations

import json

from energy_brain.ui.layout_preferences import (
    get_layout_description,
)

payload = {
    "schema_version": "phase_ui.layout_mode_config.v1",
    "location": "configuration_only",
    "always_visible": False,
    "recommended_default": "auto",
    "modes": [
        {
            "mode": "auto",
            "title": "Automatic",
            "description": get_layout_description("auto"),
        },
        {
            "mode": "desktop",
            "title": "Desktop",
            "description": get_layout_description("desktop"),
        },
        {
            "mode": "tablet",
            "title": "Tablet",
            "description": get_layout_description("tablet"),
        },
        {
            "mode": "mobile",
            "title": "Mobile",
            "description": get_layout_description("mobile"),
        },
    ],
    "ui_design": {
        "runtime_clean": True,
        "config_based_switching": True,
        "manual_override_supported": True,
    },
}

print(json.dumps(payload, indent=2))
