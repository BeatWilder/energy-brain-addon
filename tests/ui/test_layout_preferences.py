from energy_brain.ui.layout_preferences import (
    normalize_layout_profile,
)


def test_mobile():
    assert normalize_layout_profile("mobile") == "mobile"


def test_tablet():
    assert normalize_layout_profile("tablet") == "tablet"


def test_workstation():
    assert normalize_layout_profile("workstation") == "workstation"


def test_invalid_fallback():
    assert normalize_layout_profile("banana") == "tablet"
