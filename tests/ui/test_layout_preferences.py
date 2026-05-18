from energy_brain.ui.layout_preferences import (
    normalize_layout_mode,
)


def test_valid_mode():
    assert normalize_layout_mode("mobile") == "mobile"


def test_invalid_mode_falls_back():
    assert normalize_layout_mode("broken") == "auto"
