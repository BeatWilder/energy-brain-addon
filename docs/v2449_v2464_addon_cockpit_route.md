# V2449-V2464 Energy Brain EMS Add-on Cockpit Route

This phase adds a read-only cockpit route to the existing Energy Brain EMS Home Assistant add-on web UI.

Added routes:

- `GET /api/energy-brain-cockpit`
- `GET /cockpit`

Safety boundaries:

- no Home Assistant writes
- no service calls
- no battery writes
- no control buttons
- no planner changes
- no controller changes
- no main runtime replacement
- existing `/` powerflow route remains unchanged

The route is served by the existing add-on web UI on port 8099 / ingress.
