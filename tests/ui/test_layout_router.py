from energy_brain.ui.layout_router import (
    resolve_layout_profile,
)


def test_router_mobile():
    assert (
        resolve_layout_profile(
            {"layout": "mobile"}
        )
        == "mobile"
    )


def test_router_default():
    assert (
        resolve_layout_profile({})
        == "tablet"
    )
