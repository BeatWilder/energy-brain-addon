# V2000-V2031 Predbat-Lesson Simulation Contract

This contract defines an Energy Brain-owned offline simulator surface. It uses
lessons from battery planning systems without copying or importing another
project. The scope is deliberately narrow: deterministic self-consumption
simulation, traceable physics limits, and advisory-only output.

## Safety Boundary

- Pure offline Python data model and simulator.
- No Home Assistant runtime dependency.
- No network clients or MQTT dependencies.
- No service or state writes.
- No changes to the existing runtime controller or UI.
- Every result has `execution_allowed=false`.

## Contract Objects

`EnergySlot` is normalized per-slot input in kWh:

- `pv_kwh`
- `load_kwh`
- `import_price_per_kwh`
- `export_price_per_kwh`
- `duration_hours`

`BatteryPhysics` captures:

- capacity
- minimum and maximum state of charge
- initial state of charge
- reserve floor
- charge and discharge power limits
- round-trip efficiency

`SimulationInput` wraps slots and physics and requires `observer_only=true`.

## Self-Consumption Order

The canonical simulator applies this order for each slot:

1. PV serves load first.
2. PV surplus charges the battery within SOC and power limits.
3. Remaining PV exports.
4. Remaining load discharges the battery down to the reserve/SOC floor.
5. Remaining load imports from the grid.

The simulator never charges from the grid. Negative import prices can reduce
the cost of real load import, but they do not create charging behavior.

## Trace Output

Each slot returns a trace with:

- SOC start and end
- PV and load input
- import and export
- PV-to-load, PV-to-battery, and battery-to-load energy
- signed battery power where positive means charging
- cost
- reason codes explaining the path taken

Invalid input returns a no-action result with errors and
`execution_allowed=false`.
