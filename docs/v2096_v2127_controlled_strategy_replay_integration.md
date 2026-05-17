# V2096-V2127 Controlled Strategy Replay Integration

This is Energy Brain-owned code for deterministic offline strategy replay. It
connects V2032-style strategy selection to V2064/V2065 physical action-intent
simulation without copying Predbat source.

## Boundary

- Offline only.
- This is strategy replay and candidate evaluation, not a controller.
- Action intents are candidate simulations only.
- No Predbat source code is copied.
- No device writes are possible from this layer.
- No live system access, network client, message bus client, or runtime command surface is included.
- The runtime controller, v5 code, configuration, and cockpit UI are unchanged.
- Every replay result returns `observer_only=true`.
- Every replay result returns `execution_allowed=false`.

## What V2096 Adds

`app.v2096.strategy_action_intent_builder` converts deterministic strategy
choices into typed V2064 `ActionIntent` objects:

- `build_baseline_action_intents` returns no explicit actions, so V2065 applies
  self-consumption defaults.
- `build_cheapest_window_charge_intents` selects import slots by lowest import
  price, breaking ties by lowest slot index.
- `build_export_aware_intents` selects export slots by highest export price,
  breaking ties by lowest slot index.
- `build_hold_reserve_intents` selects deterministic reserve-hold candidate
  slots.

The builders are pure offline selectors. They do not perform actions and do
not authorize actions.

## What V2097 Adds

`app.v2097.controlled_strategy_replay.run_controlled_strategy_replay` loads a
neutral fixture through the existing V2032 fixture contract, builds strategy
action intents, and evaluates each strategy with
`simulate_controlled_actions`.

The replay currently evaluates four strategies in fixed order:

1. `baseline_self_consumption`
2. `cheapest_window_charge_controlled`
3. `export_aware_controlled`
4. `hold_reserve_controlled`

Best strategy selection chooses the lowest total cost among valid results.
Cost ties are resolved by the fixed strategy order above.

## Safety Behavior

Invalid fixtures fail safe with `valid=false`, `observer_only=true`,
`execution_allowed=false`, no selected best strategy, and reason codes that
describe the invalid fixture.

Invalid action-intent generation also fails safe. The integration returns
advisory result objects only and never grants execution permission.
