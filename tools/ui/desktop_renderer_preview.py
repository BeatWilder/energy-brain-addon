from __future__ import annotations

import json

from energy_brain.ui.renderers.desktop_renderer import (
    build_desktop_renderer,
)

payload = build_desktop_renderer()

print(json.dumps(payload, indent=2))
