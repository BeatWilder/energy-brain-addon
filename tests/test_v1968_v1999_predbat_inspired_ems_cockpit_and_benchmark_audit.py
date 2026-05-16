from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

ADDON_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADDON_ROOT))

from app.v1968.predbat_concept_audit import (
    build_predbat_concept_audit,
    classify_predbat_lessons,
    validate_predbat_audit_safety,
    write_audit_report,
)
from app.v1969.tesla_style_cockpit_spec import (
    REQUIRED_SECTIONS,
    build_tesla_style_cockpit_spec,
    validate_cockpit_spec_safety,
)

NEW_FILES = [
    Path("docs/v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit.md"),
    Path("app/__init__.py"),
    Path("app/v1968/__init__.py"),
    Path("app/v1968/predbat_concept_audit.py"),
    Path("app/v1969/__init__.py"),
    Path("app/v1969/tesla_style_cockpit_spec.py"),
    Path("tests/test_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit.py"),
    Path("tools/run_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit_smoke.sh"),
]


def test_predbat_lesson_categories_are_complete():
    lessons = classify_predbat_lessons()

    assert set(lessons) == {
        "adopt_as_principle",
        "adapt_to_energy_brain",
        "reject_for_energy_brain",
        "future_research",
    }
    assert all(lessons[category] for category in lessons)


def test_audit_output_is_deterministic_and_safe():
    first = build_predbat_concept_audit()
    second = build_predbat_concept_audit()

    assert first == second
    assert first["source_role"] == "benchmark_reference_only"
    boundary = first["safety_boundary"]
    assert boundary["observer_only"] is True
    for flag in [
        "runtime_dependency_allowed",
        "home_assistant_write_allowed",
        "controller_execution_allowed",
        "planner_dispatch_allowed",
        "ui_dispatch_allowed",
        "copied_source_code",
        "runtime_network_access",
    ]:
        assert boundary[flag] is False

    validation = validate_predbat_audit_safety(first)
    assert validation["valid"] is True
    assert validation["errors"] == []


def test_cockpit_spec_output_is_deterministic_and_read_only():
    first = build_tesla_style_cockpit_spec()
    second = build_tesla_style_cockpit_spec()

    assert first == second
    assert first["ui_mode"] == "read_only_cockpit_spec"
    assert first["observer_only"] is True
    assert first["dispatch_controls_allowed"] is False
    assert first["service_calls_allowed"] is False
    assert first["write_controls_allowed"] is False
    assert {"observer_only", "read_only", "no_dispatch", "no_service_calls"}.issubset(
        set(first["safety_badges"])
    )

    for section in REQUIRED_SECTIONS:
        assert section in first["sections"]
        assert first["sections"][section]["controls"] == []

    validation = validate_cockpit_spec_safety(first)
    assert validation["valid"] is True
    assert validation["errors"] == []


def test_outputs_are_json_serializable():
    json.dumps(build_predbat_concept_audit(), sort_keys=True)
    json.dumps(build_tesla_style_cockpit_spec(), sort_keys=True)


def test_modules_import_without_home_assistant_installed():
    assert importlib.import_module("app.v1968.predbat_concept_audit")
    assert importlib.import_module("app.v1969.tesla_style_cockpit_spec")


def test_optional_report_writer_only_writes_when_explicit_path_is_given(tmp_path: Path):
    before = set(tmp_path.iterdir())
    audit = build_predbat_concept_audit()
    after = set(tmp_path.iterdir())
    assert audit["safety_boundary"]["observer_only"] is True
    assert before == after

    report = tmp_path / "audit.json"
    result = write_audit_report(report)
    assert result["written"] is True
    assert report.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["validation"]["valid"] is True


def test_predbat_is_reference_only():
    audit = build_predbat_concept_audit()
    notes = audit["reference_notes"]

    assert audit["source_role"] == "benchmark_reference_only"
    assert all(note["runtime_use"] == "none" for note in notes)
    assert audit["safety_boundary"]["runtime_dependency_allowed"] is False


def test_new_code_is_standard_library_only():
    module_files = [
        Path("app/v1968/predbat_concept_audit.py"),
        Path("app/v1969/tesla_style_cockpit_spec.py"),
    ]
    allowed_import_roots = {"__future__", "json", "pathlib", "typing"}
    offenders = []

    for path in module_files:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("import "):
                root = stripped.split()[1].split(".")[0]
                if root not in allowed_import_roots:
                    offenders.append(f"{path}:{root}")
            if stripped.startswith("from "):
                root = stripped.split()[1].split(".")[0]
                if root not in allowed_import_roots:
                    offenders.append(f"{path}:{root}")

    assert offenders == []


def test_no_forbidden_runtime_surfaces_in_new_files():
    forbidden = _forbidden_terms()
    offenders = []

    for path in NEW_FILES:
        text = path.read_text(encoding="utf-8")
        for term in forbidden:
            if term in text:
                offenders.append(f"{path}:{term}")

    assert offenders == []


def test_no_protected_runtime_controller_files_are_modified():
    addon_result = subprocess.run(
        [
            "git",
            "diff",
            "--",
            "energy_brain/controller.py",
            "energy_brain/main.py",
            "energy_brain/ha_client.py",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    parent_result = subprocess.run(
        [
            "git",
            "-C",
            "..",
            "diff",
            "--",
            "app/energy_brain_v5.py",
            "archive/app_old_versions/energy_brain_v5.py",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert addon_result.stdout == ""
    assert parent_result.stdout == ""


def _forbidden_terms() -> list[str]:
    pieces = [
        ("call", "_", "service", "("),
        ("hass", ".", "services"),
        ("requests", "."),
        ("aio", "http", "."),
        ("url", "lib", "."),
        (".", "publish", "("),
        ("Alpha", "ESS", "("),
        ("set", "_", "state", "("),
        ("serv", "ice", ":"),
        ("input", "_", "boolean", "."),
        ("input", "_", "number", "."),
        ("input", "_", "select", "."),
        ("switch", "."),
        ("climate", "."),
        ("notify", "."),
        ("shell", "_", "command", "."),
    ]
    return ["".join(piece) for piece in pieces]
