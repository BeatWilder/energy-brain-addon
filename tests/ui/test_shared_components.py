from energy_brain.ui.components.shared_components import (
    explainability_component,
    hero_component,
    powerflow_component,
    runtime_component,
    safety_component,
    timeline_component,
)


def test_hero():
    payload = hero_component()

    assert payload["type"] == "hero"


def test_powerflow():
    payload = powerflow_component()

    assert payload["type"] == "powerflow"


def test_timeline():
    payload = timeline_component()

    assert payload["type"] == "planner_timeline"


def test_explainability():
    payload = explainability_component()

    assert payload["type"] == "explainability"


def test_safety():
    payload = safety_component()

    assert payload["reserve_protected"] is True


def test_runtime():
    payload = runtime_component()

    assert payload["dispatch_allowed"] is False
