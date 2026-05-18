from energy_brain.ui.mobile_renderer import (
    render_mobile_cockpit,
)


def test_mobile_layout():
    payload = {
        "soc_percent": 70,
        "current_action": "charge",
    }

    result = render_mobile_cockpit(payload)

    assert result["layout"] == "mobile"


def test_mobile_has_sections():
    payload = {}

    result = render_mobile_cockpit(payload)

    assert len(result["sections"]) == 4


def test_mobile_has_explainability():
    payload = {}

    result = render_mobile_cockpit(payload)

    types = [
        section["type"]
        for section in result["sections"]
    ]

    assert "explainability" in types
