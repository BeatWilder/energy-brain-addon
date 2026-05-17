# V2465-V2480 Energy Brain EMS Add-on Cockpit Polish

This phase improves the `/cockpit` route inside the existing Energy Brain EMS Home Assistant add-on.

Changes:

- adds a polished mobile-friendly cockpit renderer
- keeps the original cockpit renderer available
- updates `/cockpit` to use the polished renderer
- adds a visible link from the `/` powerflow page to `/cockpit`
- keeps `/api/energy-brain-cockpit` read-only

Safety boundaries:

- no Home Assistant writes
- no service calls
- no battery writes
- no control buttons
- no planner changes
- no controller changes
- no main runtime replacement
