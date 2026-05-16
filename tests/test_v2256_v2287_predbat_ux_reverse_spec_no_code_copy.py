from __future__ import annotations

import ast
import importlib
import json
import sys
from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON_ROOT))

MODULE_PATH = Path("app/v2256/predbat_ux_reverse_spec.py")
DOC_PATH = Path("docs/v2256_v2287_predbat_ux_reverse_spec_no_code_copy.md")
SMOKE_PATH = Path("tools/run_v2256_v2287_predbat_ux_reverse_spec_no_code_copy_smoke.sh")


def test_module_imports_without_home_assistant_installed():
    module = importlib.import_module("app.v2256.predbat_ux_reverse_spec")

    assert module.SCHEMA_VERSION == "v2256_v2287.predbat_ux_reverse_spec.no_code_copy.1"


def test_spec_output_is_json_serializable_and_deterministic():
    module = _module()

    first = module.build_predbat_ux_reverse_spec()
    second = module.build_predbat_ux_reverse_spec()

    assert first == second
    assert json.loads(json.dumps(first, sort_keys=True)) == first
    assert first["schema_version"] == "v2256_v2287.predbat_ux_reverse_spec.no_code_copy.1"
    assert first["source_role"] == "benchmark_reference_only"
    assert first["ui_mode"] == "read_only_reverse_spec"
    assert first["clean_room_status"] == "enforced"


def test_safety_flags_are_closed_and_validation_passes():
    module = _module()

    spec = module.build_predbat_ux_reverse_spec()
    validation = module.validate_reverse_spec_safety(spec)

    assert validation["valid"] is True
    assert validation["errors"] == []
    for flag in [
        "runtime_dependency_allowed",
        "home_assistant_write_allowed",
        "service_calls_allowed",
        "dispatch_allowed",
        "controller_changes_allowed",
        "runtime_network_access_allowed",
        "predbat_import_allowed",
    ]:
        assert spec[flag] is False
    assert spec["no_code_copy"] is True


def test_no_predbat_or_network_imports_are_present():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    blocked_roots = {
        "homeassistant",
        "hass",
        "appdaemon",
        "requests",
        "aiohttp",
        _join("url", "lib"),
        "predbat",
        _join("apps", ".", "predbat"),
    }
    assert {name.split(".")[0] for name in imports}.isdisjoint(blocked_roots)
    assert all(not name.startswith(_join("apps", ".", "predbat")) for name in imports)


def test_no_forbidden_runtime_strings_are_present_in_v2256_files():
    offenders: list[str] = []
    for path in [MODULE_PATH, DOC_PATH, Path("app/v2256/__init__.py"), Path(__file__), SMOKE_PATH]:
        text = _scan_text(path)
        offenders.extend(f"{path}:{term}" for term in _forbidden_terms() if term in text)

    assert offenders == []


def test_clean_room_boundary_is_explicit():
    module = _module()

    boundary = module.clean_room_boundaries()
    spec = module.build_predbat_ux_reverse_spec()

    for flag in [
        "no_predbat_source_copied",
        "no_predbat_imports",
        "no_predbat_runtime_dependency",
        "no_runtime_github_or_docs_scraping",
        "no_predbat_assets_screens_css_html_copied",
    ]:
        assert boundary[flag] is True
        assert spec["clean_room_boundaries"][flag] is True


def test_lessons_include_required_predbat_ux_concepts():
    module = _module()

    lesson_ids = {item["id"] for item in module.predbat_ux_lessons()}
    assert {
        "battery_prediction_over_time",
        "plan_card_and_windows",
        "cost_comparison",
        "scenario_thinking",
        "actual_vs_predicted",
        "read_only_planning",
    } <= lesson_ids


def test_adaptations_and_rejections_cover_required_energy_brain_boundaries():
    module = _module()

    adaptation_ids = {item["id"] for item in module.energy_brain_adaptations()}
    rejection_ids = {item["id"] for item in module.energy_brain_rejections()}

    assert {
        "layperson_summary",
        "simple_dayline",
        "scenario_cards",
        "cost_confidence",
        "technical_details_hidden",
    } <= adaptation_ids
    assert {
        "source_copying",
        "runtime_dependency",
        "service_calls",
        "controller_changes",
        "direct_device_control",
    } <= rejection_ids


def test_future_backlog_contains_plan_card_and_at_least_five_items():
    module = _module()

    backlog = module.future_backlog()

    assert len(backlog) >= 6
    assert any(item["version"] == "V2288-V2319" and "plan card" in item["title"] for item in backlog)


def test_markdown_document_exists_and_contains_no_code_copy_language():
    text = DOC_PATH.read_text(encoding="utf-8")

    for label in [
        "# V2256-V2287 Predbat UX reverse-spec",
        "Predbat wordt in deze sprint alleen gebruikt als benchmark en referentie.",
        "geen Predbat source code gekopieerd",
        "geen Predbat runtime dependency",
        "geen runtime GitHub/docs scraping",
        "geen controller changes",
        "What Energy Brain should adapt",
        "What Energy Brain should reject",
        "V2288-V2319 Predbat-style Energy Brain plan card",
    ]:
        assert label in text


def test_optional_report_writer_only_writes_when_explicit_path_is_passed(tmp_path: Path):
    module = _module()

    assert list(tmp_path.iterdir()) == []
    module.build_predbat_ux_reverse_spec()
    assert list(tmp_path.iterdir()) == []

    target = tmp_path / "reverse_spec.json"
    result = module.write_reverse_spec_report(target)

    assert result["written"] is True
    assert target.exists()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["clean_room_status"] == "enforced"


def _scan_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.name.endswith("_smoke.sh"):
        return "\n".join(line for line in text.splitlines() if "printf" not in line)
    return text


def _module():
    return importlib.import_module("app.v2256.predbat_ux_reverse_spec")


def _forbidden_terms() -> list[str]:
    parts = [
        ("call", "_", "service", "("),
        ("hass", ".", "services"),
        ("set", "_", "state", "("),
        ("input", "_", "boolean", "."),
        ("input", "_", "number", "."),
        ("input", "_", "select", "."),
        ("switch", "."),
        ("climate", "."),
        ("notify", "."),
        ("shell", "_", "command", "."),
        ("do", "_", "POST"),
        ("do", "_", "PUT"),
        ("do", "_", "PATCH"),
        ("do", "_", "DELETE"),
        ("dis", "patch", "("),
        ("execute", "("),
        ("requests", "."),
        ("aiohttp", "."),
        ("url", "lib", "."),
        ("from", " ", "predbat"),
        ("import", " ", "predbat"),
        ("from", " ", "apps", ".", "predbat"),
        ("import", " ", "apps", ".", "predbat"),
    ]
    return [_join(*part) for part in parts]


def _join(*parts: str) -> str:
    return "".join(parts)
