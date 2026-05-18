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

    grid = payload["sections"][1]

    assert grid["left"]["type"] == "powerflow"


def test_has_explainability():
    payload = build_desktop_renderer()

    right = payload["sections"][1]["right"]

    assert right[0]["type"] == "explainability"


def test_no_dispatch():
    payload = build_desktop_renderer()

    runtime = payload["sections"][1]["right"][2]

    assert runtime["dispatch_allowed"] is False
