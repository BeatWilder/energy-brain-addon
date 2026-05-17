# V2643-V2658 Hillview POST Path Hardening

This phase hardens the Hillview dispatch POST route for Home Assistant ingress variants.

Observed failure:

- UI still received HTTP 404.
- Raw response showed `status: not_found`.
- That proves the request reached the add-on webserver but did not match the control route.

Fix:

- Accept route variants containing `hillview/control`.
- Keep the exact `/api/hillview/control` route.
- Keep suffix support for `/api/hillview/control`.
- Add POST 404 diagnostics:
  - method
  - request_path
  - route_hint

Safety:

- No allowlist expansion.
- No direct new write surface.
- No planner/controller/main changes.
- Existing guarded Hillview allowlist remains the only control path.
