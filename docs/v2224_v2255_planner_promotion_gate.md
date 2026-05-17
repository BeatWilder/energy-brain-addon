# V2224-V2255 Planner Promotion Gate

This is Energy Brain-owned code for deterministic offline planner validation.
No Predbat source code is copied.

## Boundary

- Offline only.
- This is not a controller.
- Promotion means accepted for shadow/observer comparison only.
- Promotion does not mean live control.
- No device writes are possible from this layer.
- No live Home Assistant data, entity IDs, service calls, or runtime control surfaces are used.
- Every gate decision returns `observer_only=true`.
- Every gate decision returns `execution_allowed=false`.

## Decisions

Allowed decision values are:

- `accepted_for_shadow`
- `needs_review`
- `rejected`

Missing or invalid scoreboard input fails safe and cannot be accepted.

## Gate Rules

The gate consumes the V2192-V2223 scenario regression scoreboard shape and
checks:

- no safety violations
- no reserve/SOC violations
- no missing required scenario results
- deterministic scoreboard status
- minimum pass count
- maximum allowed failures
- regression score threshold
- all required edge scenarios represented

Accepted output is only for shadow/observer comparison before any live data or
controller validation.
