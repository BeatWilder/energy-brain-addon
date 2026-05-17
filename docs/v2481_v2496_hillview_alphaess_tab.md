# V2481-V2496 Hillview AlphaESS Tab + Control Intent Preparation

This phase adds a Hillview / AlphaESS tab to the Energy Brain EMS Home Assistant add-on.

Routes:

- `GET /hillview`
- `GET /api/hillview`

Purpose:

- show AlphaESS / Hillview entity groups inside the Energy Brain EMS app
- prepare future guarded control intent metadata
- keep all controls read-only for now
- document that future writes must go through a guarded controller path

Safety boundaries:

- no Home Assistant writes
- no service calls
- no active control buttons
- no planner changes
- no controller changes
- no main runtime replacement
