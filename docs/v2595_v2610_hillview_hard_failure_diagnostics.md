# V2595-V2610 Hillview Hard Failure Diagnostics

This phase makes Hillview guarded control failures visible enough to debug in the UI.

Changes:

- Flatten failed guarded write context into the JSON result:
  - failed_domain
  - failed_service
  - failed_entity_id
  - failed_value
  - failed_reason
- Add compact debug JSON to the inline blocked message.
- Keep the existing guarded allowlist unchanged.

Safety:

- No new Home Assistant control surface is added.
- Planner/controller/main are untouched.
- This is diagnostic only; it does not loosen guards.
