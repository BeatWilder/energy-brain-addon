# V2128-V2159 Planner Replay Audit Report

This is Energy Brain-owned code for deterministic offline reporting. It turns
controlled strategy replay results into an explainable planner audit report.
No Predbat source code is copied.

## Boundary

- Offline only.
- This is an audit/report layer, not a controller.
- The report explains candidate strategy replay results only.
- No device writes are possible from this layer.
- No live system access, network client, message bus client, or command surface is included.
- The runtime controller, v5 code, configuration, and cockpit UI are unchanged.
- Every report returns `observer_only=true`.
- Every report returns `execution_allowed=false`.
- V2128-V2159 is the explainability layer before any controller validation.

## Contract

`app.v2128.planner_replay_audit_contract` defines:

- `StrategyAuditLine`
- `SlotAuditLine`
- `PlannerReplayAuditReport`

The report includes the selected strategy, winning and losing reason codes,
strategy comparison lines, slot trace lines, and a compact markdown summary.

## Report Builder

`app.v2129.planner_replay_audit_report.build_planner_replay_audit_report`
calls `run_controlled_strategy_replay`, marks the winner from
`best_strategy_name`, and explains why other strategies did not win.

Losing explanations are deterministic:

- `higher_cost_than_winner`
- `invalid_strategy_result`
- `tie_lost_by_strategy_order`

Winning explanations are deterministic:

- `lowest_total_cost`
- `deterministic_strategy_order_tie_break` when another valid strategy has the
  same total cost as the winner.

## Markdown Summary

The generated markdown includes:

- Safety status
- Winner details
- Strategy comparison table
- Slot trace summary table
- Notes that the layer is offline and candidate-simulation only

Slot trace rows include applied action type, SOC start/end, import/export,
slot cost, and reason codes. Constraint clipping appears in the reason codes
when the controlled simulator clips a candidate action.
