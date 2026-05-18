from __future__ import annotations

import json

from energy_brain.ui.live.live_payload_adapter import (
    build_live_payload,
)

payload = build_live_payload()

print(json.dumps(payload, indent=2))
