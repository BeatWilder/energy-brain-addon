# V1968-V1999 Predbat-inspired Tesla-style EMS cockpit and planner benchmark audit

## Scope

This proposal uses Predbat only as a human research benchmark for planner quality, simulation concepts, forecast handling, explainability, comparison reporting, and UI ideas. Energy Brain remains an independent system with strict runtime boundaries and no dependency on Predbat.

Primary references reviewed at concept level:

- Predbat documentation: https://springfall2008.github.io/batpred/
- What Predbat does: https://springfall2008.github.io/batpred/what-does-predbat-do/
- Predbat customisation and modes: https://springfall2008.github.io/batpred/customisation/
- Predbat output data: https://springfall2008.github.io/batpred/output-data/
- Predbat web interface: https://springfall2008.github.io/batpred/web-interface/
- Predbat GitHub repository: https://github.com/springfall2008/batpred

No Predbat source code is copied, vendored, imported, scraped at runtime, or connected to Energy Brain execution.

## Predbat Concepts Worth Studying

Predbat is useful as a mature home-battery planning reference because it combines tariff inputs, PV forecasts, load assumptions, reserve settings, SOC prediction, and plan display. The relevant lesson for Energy Brain is not to clone Predbat. The lesson is that high-quality battery planning needs a clear forecast-to-simulation-to-explanation chain.

### Forecast normalization

Predbat-style planning depends on bringing different forecast sources into comparable time slots. Energy Brain should adopt the principle of normalized planning intervals that carry explicit units, source names, staleness, confidence, and missing-data markers.

Energy Brain should keep this in the Forecast Layer. The Planner Layer should receive normalized inputs and validity flags, not raw Home Assistant entities or provider-specific payloads.

### Forward SOC simulation

A forward SOC simulation is the best audit artifact for a battery planner. It lets tests and humans inspect whether a plan violates reserve, overfills the battery, overuses export, or depends on unrealistic PV/load assumptions.

Energy Brain should expose the SOC trajectory in observer and shadow outputs before any production execution path can consume it.

### Candidate charge, discharge, and export windows

Predbat demonstrates the value of reasoning over candidate windows. Energy Brain can adapt this as offline planner hypotheses:

- candidate charge windows from low import prices, PV surplus, or reserve recovery
- candidate discharge windows from high import prices or load support
- candidate export windows only as comparison hypotheses
- rejected windows with reason codes

These must remain planner candidates, never direct device instructions.

### Reserve handling

Reserve handling should be visible in both planner output and controller safety. The planner can show reserve-constrained intervals, but the controller boundary must still independently refuse unsafe execution if live runtime ever reaches that layer.

For this task, reserve handling remains research/spec/audit only.

### Read-only and degraded modes

Predbat has read-only and monitor concepts that are valuable for planning visibility. Energy Brain should be stricter: missing data, stale forecasts, invalid SOC, or unclear limits should degrade to observer-only with no writes and a clear reason.

The future cockpit should make degraded state prominent instead of hiding it in logs.

### Anti-churn and plan acceptance

Planner quality is not just finding a cheaper plan. A production-quality EMS also needs anti-churn controls:

- minimum benefit threshold before accepting a new plan
- stale-input rejection
- confidence gating
- hold-down time between materially similar plans
- reason-coded rejection of noisy alternatives

This belongs in the Planner/Policy boundary, not in device adapters.

### Explainable reason codes

Every interval should carry a compact reason code and a readable explanation. Examples include holding due to reserve, charging due to forecast PV deficit, rejecting export due to low confidence, or accepting a plan due to material cost improvement.

Reason codes are core audit data, not decoration.

## Benchmark Comparison Against Energy Brain

Predbat can serve as a conceptual benchmark in these dimensions:

- forecast quality: source freshness, normalization, and uncertainty
- simulation quality: SOC trajectory realism and constraint handling
- economic quality: cost, baseline delta, and tariff use
- stability quality: anti-churn and acceptance rules
- explanation quality: reason codes and degraded-mode visibility
- UI quality: readable plan timeline, energy flow, and comparison outputs

Energy Brain should compare itself against these concepts using offline reports. It should not add a runtime Predbat bridge, Predbat import, GitHub scraping, or cross-system execution path.

## Why Energy Brain Should Remain Stricter About Boundaries

Energy Brain should maintain stricter separation than a single automation application because safety and auditability depend on explicit layers:

- Data Layer gathers and validates observed data.
- Forecast Layer normalizes forecast inputs.
- Planner Layer produces candidate plans and trajectories.
- Policy Layer accepts or rejects plans under safety and confidence rules.
- Real-time Controller remains isolated from planner internals.
- Device Controllers are the only future location for device-specific behavior.
- Home Assistant adapter stays separate from planning and policy.
- Logging and tests verify observer-only behavior.

This project must not mix planner logic with Home Assistant writes, device writes, or UI-triggered actions.

## Tesla-style EMS Cockpit Lessons

A future Energy Brain cockpit can borrow UI principles without borrowing execution behavior:

- calm dark cockpit style
- prominent observer-only/read-only status
- SOC trajectory as the primary planning graph
- energy-flow overview for PV, battery, grid, and load
- readable cards with compact current values
- planner timeline with reason codes
- price, PV, and load forecast panels
- benchmark comparison against baseline and Predbat-inspired concepts
- degraded-mode banner for stale or missing inputs
- safety panel showing disabled execution/write permissions
- latest cycle table for audit detail

The cockpit should show observer, shadow, comparison, and degraded-mode data only. It should not include direct execution controls.

## Observer-only Home Assistant UI Path

This work can later support a Home Assistant UI by emitting read-only data structures that an adapter can display. The adapter should not infer entity IDs, write helpers, call services, or expose control buttons.

Safe future path:

1. Keep planner audit output JSON-serializable.
2. Store latest observer/shadow cycle in the existing logging path.
3. Render a read-only cockpit from existing cycle data.
4. Show benchmark deltas and reason codes.
5. Keep all execution/write flags disabled unless a separate protected runtime review changes policy.

## Do Not Copy

- no source-code copying
- no runtime dependency
- no direct architecture cloning
- no Home Assistant service calls
- no inverter/device writes
- no bypassing existing controller logic
- no direct UI dispatch controls
- no Predbat import
- no vendored Predbat files
- no runtime GitHub scraping

## Deliverables Added By This Proposal

- `docs/v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit.md`
- `app/v1968/predbat_concept_audit.py`
- `app/v1969/tesla_style_cockpit_spec.py`
- `tests/test_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit.py`
- `tools/run_v1968_v1999_predbat_inspired_ems_cockpit_and_benchmark_audit_smoke.sh`

All deliverables are addon-local and offline.

