# V2160-V2191 Planner Quality Scenario Pack

This is Energy Brain-owned code for deterministic offline quality validation.
No Predbat source code is copied.

## Boundary

- Offline only.
- Scenario pack validation uses neutral fixtures.
- This is not a controller.
- No device writes are possible from this layer.
- No live Home Assistant data, entity IDs, or runtime control surfaces are used.
- Every scenario result returns `observer_only=true`.
- Every scenario result returns `execution_allowed=false`.
- These scenarios are for offline quality validation before live data or controller validation.

## Scenarios

The pack includes deterministic fixtures for:

- `negative_prices`
- `flat_prices`
- `full_battery`
- `empty_battery`
- `reserve_reached`
- `high_pv`
- `no_pv`
- `high_load`
- `export_opportunity`
- `charge_opportunity`

Each fixture includes a schema version marker, battery limits, at least four
slots, PV/load values, import prices, export prices, and scenario metadata in
the scenario pack layer.

## Runner

`app.v2161.scenario_pack_runner.run_planner_quality_scenario_pack` runs every
scenario through `build_planner_replay_audit_report` and returns a deterministic
pack result with per-scenario summaries.

The runner validates:

- no scenario allows execution
- no scenario crashes silently
- valid scenarios include strategy lines
- valid scenarios include slot lines
- winning min SOC does not drop below the configured min/reserve floor
- winning final SOC remains inside configured min/max bounds
- invalid results are explicit with reason codes

The pack validates planner quality across fixture-based replay and audit
behavior. It does not validate a live controller.
