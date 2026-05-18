from energy_brain.ui.renderers.desktop_renderer import (
    build_desktop_renderer,
)


def test_layout():
    payload = build_desktop_renderer()

    assert payload["layout"] == "desktop"


def test_mode():
    payload = build_desktop_renderer()

    assert payload["mode"] == "mission_control"


def test_observer_only():
    payload = build_desktop_renderer()

    assert payload["observer_only"] is True


def test_has_powerflow():
    payload = build_desktop_renderer()

    hero = payload["sections"][0]

    assert hero["type"] == "powerflow_hero"


def test_has_explainability():
    payload = build_desktop_renderer()

    section_types = [
        section["type"]
        for section in payload["sections"]
    ]

    assert "explainability" in section_types


def test_no_dispatch():
    payload = build_desktop_renderer()

    safety = payload["sections"][3]

    assert safety["readonly"] is True
