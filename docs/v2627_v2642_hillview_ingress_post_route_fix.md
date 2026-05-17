# V2627-V2642 Hillview Ingress POST Route Fix

This phase fixes Hillview dispatch form POST routing through Home Assistant ingress.

Observed failure:

- Frontend received HTTP 404.
- Backend response was `{"read_only": true, "status": "not_found"}`.
- The request reached the add-on webserver, but did not match the exact POST route.

Fix:

- Change form action from absolute `/api/hillview/control` to relative `api/hillview/control`.
- Accept both exact and ingress-prefixed POST paths:
  - `/api/hillview/control`
  - paths ending with `/api/hillview/control`

Safety:

- No allowlist expansion.
- No planner/controller/main changes.
- This only makes the existing guarded route reachable under ingress.
