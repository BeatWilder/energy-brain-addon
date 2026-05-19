from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(".")

ENTITY_PATTERNS = [
    r"sensor\.alphaess_[a-zA-Z0-9_]+",
    r"sensor\.solcast_[a-zA-Z0-9_]+",
    r"sensor\.energybrain_[a-zA-Z0-9_]+",
    r"binary_sensor\.[a-zA-Z0-9_]+",
    r"input_boolean\.[a-zA-Z0-9_]+",
    r"input_number\.[a-zA-Z0-9_]+",
    r"climate\.[a-zA-Z0-9_]+",
]

found = set()

for path in ROOT.rglob("*.py"):
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        continue

    for pattern in ENTITY_PATTERNS:
        for match in re.findall(pattern, text):
            found.add(match)

groups = {
    "powerflow": [],
    "battery": [],
    "solar": [],
    "grid": [],
    "comfort": [],
    "presence": [],
    "dispatch": [],
    "forecast": [],
    "prices": [],
}

for entity in sorted(found):

    e = entity.lower()

    if "battery" in e or "soc" in e:
        groups["battery"].append(entity)

    if "pv" in e or "solcast" in e:
        groups["solar"].append(entity)

    if "grid" in e:
        groups["grid"].append(entity)

    if "load" in e or "power" in e:
        groups["powerflow"].append(entity)

    if "climate" in e or "ir_" in e:
        groups["comfort"].append(entity)

    if "occupancy" in e or "aanwezig" in e or "thuis" in e:
        groups["presence"].append(entity)

    if "dispatch" in e:
        groups["dispatch"].append(entity)

    if "forecast" in e:
        groups["forecast"].append(entity)

    if "price" in e or "nordpool" in e:
        groups["prices"].append(entity)

report = {
    "summary": {
        "total_entities": len(found),
    },
    "groups": groups,
}

Path("reports/ui_intelligence_report.json").write_text(
    json.dumps(report, indent=2)
)

print()
print("===================================")
print("LIVE UI INTELLIGENCE REPORT")
print("===================================")

for name, values in groups.items():
    print()
    print(f"[{name.upper()}] ({len(values)})")

    for v in values[:25]:
        print(" -", v)

print()
print("Saved:")
print("reports/ui_intelligence_report.json")
