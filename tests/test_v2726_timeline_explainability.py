from energy_brain.v2726.timeline_explainability import (
    build_timeline_explainability,
)


def test_timeline_explainability():

    payload = build_timeline_explainability({
        "steps": [
            {
                "index": 0,
                "reason": "discharge_to_load",
                "soc_percent": 48.0,
                "battery_setpoint_kw": -3.2,
            },
            {
                "index": 1,
                "reason": "reserve_hold",
                "soc_percent": 20.0,
                "battery_setpoint_kw": 0.0,
            },
        ]
    })

    assert len(payload) == 2

    assert payload[0]["action"] == "discharge"

    assert payload[1]["constraint"] == "min_soc_floor"

    assert payload[0]["observer_only"] is True

    assert payload[1]["write_allowed"] is False
