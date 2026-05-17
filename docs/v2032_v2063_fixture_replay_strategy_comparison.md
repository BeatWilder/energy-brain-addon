# V2032-V2063 Fixture Replay Strategy Comparison

This is an Energy Brain-owned offline comparison and replay harness. It builds
on the V2000 simulation contract and the V2001 canonical self-consumption
simulator without copying source from Predbat.

## Boundary

- Offline only.
- This is a comparison/replay harness, not a controller.
- It does not import Predbat.
- It does not copy Predbat source code.
- It does not access Home Assistant.
- It does not make service calls, network calls, MQTT calls, or writes.
- It does not dispatch actions or write Alpha ESS settings.
- It does not change the runtime controller, v5 code, or cockpit UI.
- Every strategy score returns `execution_allowed=false`.

## Fixture Loader

`app.v2032.fixture_replay_contract.build_simulation_input` accepts either an
existing `SimulationInput` or a neutral fixture dictionary:

```python
{
    "observer_only": True,
    "slots": [
        {
            "slot_id": "s0",
            "pv_kwh": 0.0,
            "load_kwh": 1.0,
            "import_price_per_kwh": 0.30,
            "export_price_per_kwh": 0.05,
            "duration_hours": 1.0,
        }
    ],
    "battery": {
        "capacity_kwh": 10.0,
        "min_soc_kwh": 0.0,
        "max_soc_kwh": 10.0,
        "initial_soc_kwh": 5.0,
        "reserve_kwh": 1.0,
        "charge_power_kw": 5.0,
        "discharge_power_kw": 5.0,
        "round_trip_efficiency": 1.0,
    },
}
```

Invalid fixture shape fails safe with `valid=false` and no-action reason codes.

## Strategies

`baseline_self_consumption` runs `simulate_self_consumption` directly and
reports the resulting cost, import, export, SOC, and trace-derived action
change count.

`cheapest_window_charge` identifies the cheapest import-price slot with stable
tie-breaking by `slot_id`. It reports that slot as a candidate only. It does not
grid charge because the current simulator does not support controlled grid
charge actions.

`export_aware_placeholder` identifies the highest export-price slot with stable
tie-breaking by `slot_id`. It reports that slot as a candidate only. It does not
perform controlled export because the current simulator does not support
controlled export actions.

## Comparison Output

`compare_strategies(fixture)` always returns scores in this order:

1. `baseline_self_consumption`
2. `cheapest_window_charge`
3. `export_aware_placeholder`

Each score includes:

- strategy name
- validity
- execution allowance, always false
- total cost
- total grid import and export
- final and minimum SOC
- action change count
- reason codes
- candidate slot IDs for placeholder strategies

