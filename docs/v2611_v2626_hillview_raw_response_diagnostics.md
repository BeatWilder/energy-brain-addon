# V2611-V2626 Hillview Raw Response Diagnostics

This phase makes the Hillview inline control notice show the raw backend response context.

Why:

- The UI still showed a generic blocked message.
- Flattened fields were empty, so the frontend needed to expose the full response payload and HTTP status.

Changes:

- Frontend reads response text first.
- Frontend safely parses JSON or reports non_json_response.
- Debug JSON now includes:
  - http_status
  - http_ok
  - route
  - reason/status/message
  - failed fields
  - raw backend result
- Backend control results include route marker `hillview_control`.

Safety:

- No Home Assistant allowlist expansion.
- No planner/controller/main changes.
- Diagnostic-only hardening.
