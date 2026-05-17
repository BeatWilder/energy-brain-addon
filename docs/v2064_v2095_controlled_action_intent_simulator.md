# V2064-V2095 Controlled Action-Intent Simulator

This is Energy Brain-owned code for deterministic offline research. It builds
on the V2000 simulator contract, V2001 canonical self-consumption simulator,
and V2032 fixture replay contract without copying source from Predbat.

## Boundary

- Offline only.
- This is a simulator, not a controller.
- Action intents are candidate simulations only.
- No Predbat source code is copied.
- No device writes are possible from this layer.
- No live system access, network client, message bus client, or dispatch surface is included.
- The runtime controller, v5 code, configuration, and cockpit UI are unchanged.
- Every result returns `observer_only=true`.
- Every result returns `execution_allowed=false`.

## Action Intent Contract

`app.v2064.action_intent_contract.ActionIntent` is a typed offline contract:

```python
ActionIntent(
    slot_index=0,
    action_type="grid_charge_candidate",
    requested_energy_kwh=1.5,
    reason_codes=("cheap_import_window",),
)
```

Supported action types are:

- `self_consumption`
- `grid_charge_candidate`
- `battery_discharge_candidate`
- `export_candidate`
- `hold_candidate`

Validation fails safe for an invalid slot index, negative requested energy,
unknown action type, duplicate slot index, missing action list, or missing
fixture/simulation input.

## Controlled Simulator

`app.v2065.controlled_action_simulator.simulate_controlled_actions` accepts a
neutral fixture dictionary or a `SimulationInput`, plus a list or tuple of
`ActionIntent` objects.

No action intent for a slot defaults that slot to canonical self-consumption.
Candidate actions are clipped by:

- SOC minimum
- SOC maximum
- reserve floor
- charge power limit
- discharge power limit
- timestep duration
- efficiency

## Behavior

`self_consumption` follows the V2001 PV-first baseline behavior.

`hold_candidate` prevents battery discharge to serve load in that slot. PV may
still serve load, and PV surplus may charge the battery when physically allowed.

`grid_charge_candidate` imports extra energy from the grid into the battery,
clipped by SOC room and charge power. It remains a simulated candidate only.

`battery_discharge_candidate` discharges to serve remaining load when available,
clipped by reserve and discharge power.

`export_candidate` discharges the battery to grid export when available above
reserve and within discharge power. This is simulated only.

## Output

Each per-slot trace includes slot index, applied action type, requested energy,
clipped energy, start/end SOC, grid import/export, PV/battery/grid load service,
PV-to-battery/export, battery charge/discharge power, slot cost, and reason
codes.

The summary includes validity, `observer_only=true`,
`execution_allowed=false`, total cost, total grid import/export, final SOC,
minimum SOC, maximum SOC, per-slot trace, errors, and reason codes.
