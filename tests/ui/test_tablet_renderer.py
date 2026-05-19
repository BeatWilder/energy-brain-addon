from energy_brain.ui.tablet_renderer import (
    render_tablet_cockpit,
)


def test_tablet_layout():
    result = render_tablet_cockpit({})

    assert result["layout"] == "tablet"


def test_tablet_has_sections():
    result = render_tablet_cockpit({})

    assert len(result["sections"]) >= 3


def test_tablet_has_split_panel():
    result = render_tablet_cockpit({})

    section_types = [
        section["type"]
        for section in result["sections"]
    ]

    assert section_types == [
        "powerflow_hero",
        "planner_summary",
        "explainability",
        "safety",
        "battery_status",
    ]
