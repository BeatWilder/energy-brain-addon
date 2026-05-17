# V2659-V2674 Hillview form.action shadowing fix

This phase fixes the real Hillview POST 404 root cause.

Observed failure:

- Backend debug showed request_path `"/[object%20RadioNodeList]"`.
- The form contains submit buttons named `action`.
- In browser DOM, `form.action` can be shadowed by controls named `action`.
- JavaScript therefore posted to `[object RadioNodeList]` instead of the form endpoint.

Fix:

- Stop using `form.action`.
- Use `form.getAttribute("action") || "api/hillview/control"`.
- Keep the guarded backend route and allowlist unchanged.

Safety:

- No allowlist expansion.
- No planner/controller/main changes.
- Existing guarded Hillview control path remains the only write path.
