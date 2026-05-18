from energy_brain.ui.layout_router import (
    build_layout_view,
)


PAYLOAD = {
    "soc": 50,
}


def test_desktop_layout():
    result = build_layout_view(
        PAYLOAD,
        "desktop",
    )

    assert result["layout"] == "desktop"


def test_tablet_layout():
    result = build_layout_view(
        PAYLOAD,
        "tablet",
    )

    assert result["layout"] == "tablet"


def test_mobile_layout():
    result = build_layout_view(
        PAYLOAD,
        "mobile",
    )

    assert result["layout"] == "mobile"


def test_auto_layout():
    result = build_layout_view(
        PAYLOAD,
        "auto",
    )

    assert result["layout"] == "desktop"


def test_invalid_layout_falls_back_to_desktop():
    result = build_layout_view(
        PAYLOAD,
        "wall-panel",
    )

    assert result["layout"] == "desktop"
