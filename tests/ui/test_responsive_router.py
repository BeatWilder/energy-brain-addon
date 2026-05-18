from energy_brain.ui.responsive_router import (
    build_responsive_payload,
    detect_layout_mode,
)


def test_mobile_detection():
    assert detect_layout_mode(430) == "mobile"


def test_tablet_detection():
    assert detect_layout_mode(900) == "tablet"


def test_desktop_detection():
    assert detect_layout_mode(1600) == "desktop"


def test_manual_override():
    assert (
        detect_layout_mode(
            1600,
            manual_override="mobile",
        )
        == "mobile"
    )


def test_payload():
    payload = build_responsive_payload(1024)

    assert payload["selected_layout"] == "tablet"


def test_observer_only():
    payload = build_responsive_payload(430)

    assert payload["observer_only"] is True
