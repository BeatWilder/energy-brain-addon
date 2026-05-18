from energy_brain.ui.components.tesla_powerflow import (
    build_tesla_powerflow,
    calculate_flow_direction,
)


def test_component_type():
    payload = build_tesla_powerflow()

    assert payload["type"] == "tesla_powerflow"


def test_animation_enabled():
    payload = build_tesla_powerflow()

    assert payload["animated"] is True


def test_has_flows():
    payload = build_tesla_powerflow()

    assert len(payload["flows"]) > 0


def test_direction_forward():
    assert calculate_flow_direction(2.0) == "forward"


def test_direction_reverse():
    assert calculate_flow_direction(-2.0) == "reverse"


def test_direction_idle():
    assert calculate_flow_direction(0.0) == "idle"
