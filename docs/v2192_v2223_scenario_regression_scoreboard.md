# V2192-V2223 Scenario Regression Scoreboard

This is Energy Brain-owned code for deterministic offline regression
detection. No Predbat source code is copied.

## Boundary

- Offline only.
- The scoreboard summarizes deterministic planner quality scenarios.
- This is not a controller.
- No device writes are possible from this layer.
- No live Home Assistant data, entity IDs, or runtime control surfaces are used.
- Every scoreboard returns `observer_only=true`.
- Every scoreboard returns `execution_allowed=false`.
- This scoreboard is for regression detection before live data or controller validation.

## What It Summarizes

`app.v2193.scenario_regression_scoreboard.build_scenario_regression_scoreboard`
runs the V2160-V2191 planner quality scenario pack and emits one compact row
per scenario.

Each row includes:

- scenario name
- expected focus
- best strategy
- total cost
- grid import/export
- min SOC and final SOC
- strategy count
- slot trace count
- safety pass/fail
- regression reason codes
- scenario notes

## Regression Rules

A row passes safety when:

- the scenario result is valid
- `observer_only=true`
- `execution_allowed=false`
- strategy count is non-zero
- slot trace count is non-zero
- min SOC is present
- final SOC is present

Output ordering follows the scenario pack order and is deterministic.
