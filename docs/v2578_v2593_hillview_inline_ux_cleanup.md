# V2578-V2593 Hillview Inline UX Cleanup

This phase cleans up Hillview dispatch feedback after inline no-refresh controls.

Changes:

- Hide the old top redirect notice when inline feedback is active.
- Keep feedback inside the dispatch control card.
- Improve blocked reason extraction from nested backend results.
- Show a useful fallback reason when the backend returns no reason.
- Clarify copy: Dispatch on first saves mode, duration, power and cutoff, then enables dispatch.

Safety:

- Existing guarded Home Assistant allowlist remains unchanged.
- Planner/controller/main are untouched.
- No broad service-call surface is added.
