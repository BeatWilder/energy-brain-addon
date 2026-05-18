from energy_brain.ui.live.live_payload_adapter import (
    build_live_payload,
)


def test_schema():
    payload = build_live_payload()

    assert payload["schema_version"] == \
        "phase_ui_i.live_payload.v1"


def test_observer_only():
    payload = build_live_payload()

    assert payload["observer_only"] is True


def test_no_dispatch():
    payload = build_live_payload()

    assert payload["dispatch_allowed"] is False
    assert payload["ha_writes_allowed"] is False


def test_override():
    payload = build_live_payload({
        "soc_percent": 42,
    })

    assert payload["soc_percent"] == 42
