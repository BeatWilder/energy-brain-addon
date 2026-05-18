from __future__ import annotations

import json

from energy_brain.ui.responsive_router import (
    build_responsive_payload,
)

payload = {
    "mobile": build_responsive_payload(430),
    "tablet": build_responsive_payload(1024),
    "desktop": build_responsive_payload(1720),
    "manual_mobile": build_responsive_payload(
        1720,
        manual_override="mobile",
    ),
}

print(json.dumps(payload, indent=2))
