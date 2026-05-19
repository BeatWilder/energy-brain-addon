#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "V2727-V2748 UI profile selector + workstation router"
echo "=================================================="

mkdir -p \
  energy_brain/ui \
  tests/ui \
  docs/ui

echo
echo "=== STEP 1: backup ==="

cp energy_brain/web_ui.py \
   "backups/web_ui.py.v2727_$(date +%s).bak"

cp energy_brain/ui/layout_preferences.py \
   "backups/layout_preferences.py.v2727_$(date +%s).bak" \
   2>/dev/null || true

cp energy_brain/ui/layout_router.py \
   "backups/layout_router.py.v2727_$(date +%s).bak" \
   2>/dev/null || true

echo
echo "=== STEP 2: layout preferences ==="

cat > energy_brain/ui/layout_preferences.py <<'PY'
from __future__ import annotations

VALID_LAYOUTS = {
    "mobile",
    "tablet",
    "workstation",
}


def normalize_layout_profile(value: str | None) -> str:
    if not value:
        return "tablet"

    value = str(value).strip().lower()

    if value not in VALID_LAYOUTS:
        return "tablet"

    return value
PY

echo
echo "=== STEP 3: layout router ==="

cat > energy_brain/ui/layout_router.py <<'PY'
from __future__ import annotations

from energy_brain.ui.layout_preferences import normalize_layout_profile


def resolve_layout_profile(request_args: dict | None = None) -> str:
    request_args = request_args or {}

    requested = request_args.get("layout")

    return normalize_layout_profile(requested)
PY

echo
echo "=== STEP 4: workstation renderer stub ==="

cat > energy_brain/ui/workstation_renderer.py <<'PY'
from __future__ import annotations


def render_workstation_shell() -> str:
    return """
    <div class="eb-workstation-shell">
        <div class="eb-workstation-title">
            🖥️ Energy Brain Workstation
        </div>

        <div class="eb-workstation-subtitle">
            Tesla-style EMS cockpit mode
        </div>
    </div>
    """
PY

echo
echo "=== STEP 5: patch web_ui ==="

python3 - <<'PY'
from pathlib import Path

path = Path("energy_brain/web_ui.py")
text = path.read_text(encoding="utf-8")

if "resolve_layout_profile" not in text:
    text = (
        'from energy_brain.ui.layout_router import resolve_layout_profile\n'
        + text
    )

marker = "return html"

if marker in text and "UI Profile" not in text:
    inject = '''
    profile = resolve_layout_profile(
        getattr(request, "args", {})
    )

    profile_selector = f"""
    <div style="
        display:flex;
        gap:12px;
        margin-bottom:20px;
        align-items:center;
        font-size:14px;
    ">
        <strong>UI Profile</strong>

        <a href="?layout=mobile">📱 Mobile</a>
        <a href="?layout=tablet">📲 Tablet</a>
        <a href="?layout=workstation">🖥️ Workstation</a>

        <span style="opacity:0.7;">
            active: {profile}
        </span>
    </div>
    """

    html = profile_selector + html
'''

    text = text.replace(marker, inject + "\n    return html", 1)

path.write_text(text, encoding="utf-8")

print("PASS: web_ui patched")
PY

echo
echo "=== STEP 6: tests ==="

cat > tests/ui/test_layout_preferences.py <<'PY'
from energy_brain.ui.layout_preferences import (
    normalize_layout_profile,
)


def test_mobile():
    assert normalize_layout_profile("mobile") == "mobile"


def test_tablet():
    assert normalize_layout_profile("tablet") == "tablet"


def test_workstation():
    assert normalize_layout_profile("workstation") == "workstation"


def test_invalid_fallback():
    assert normalize_layout_profile("banana") == "tablet"
PY

cat > tests/ui/test_layout_router.py <<'PY'
from energy_brain.ui.layout_router import (
    resolve_layout_profile,
)


def test_router_mobile():
    assert (
        resolve_layout_profile(
            {"layout": "mobile"}
        )
        == "mobile"
    )


def test_router_default():
    assert (
        resolve_layout_profile({})
        == "tablet"
    )
PY

echo
echo "=== STEP 7: docs ==="

cat > docs/ui/workstation_renderer.md <<'MD'
# Workstation Renderer

Introduces explicit UI layout profiles:

- mobile
- tablet
- workstation

Goals:

- responsive EMS cockpit
- Tesla-style workstation mode
- deterministic layout routing
- future explainability/timeline expansion

This change affects presentation only.

No planner/controller/runtime behavior changes.
MD

echo
echo "=== STEP 8: smoke ==="

python3 -m py_compile \
  energy_brain/ui/layout_preferences.py \
  energy_brain/ui/layout_router.py \
  energy_brain/ui/workstation_renderer.py \
  energy_brain/web_ui.py

python3 -m pytest -q \
  tests/ui/test_layout_preferences.py \
  tests/ui/test_layout_router.py

echo
echo "=== STEP 9: git status ==="

git status --short

echo
echo "=================================================="
echo "PATCH COMPLETE"
echo "=================================================="
echo
echo "Run daarna:"
echo
echo "bash tools/run_v2727_v2748_ui_profile_selector_workstation_router.sh"
