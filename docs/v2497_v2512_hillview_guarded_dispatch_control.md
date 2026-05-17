# V2497-V2512 Hillview Guarded Dispatch Control

This phase adds the first guarded Hillview control endpoint to the Energy Brain EMS Home Assistant add-on.

Scope:

- adds `hillview_controls_enabled` add-on option
- adds `POST /api/hillview/control`
- allows only `input_boolean.alphaess_helper_dispatch`
- supports only `on` and `off`
- keeps force charging, force discharging, force export, reset, power, duration and cutoff controls disabled
- keeps planner, controller and main runtime unchanged

Safety:

- controls are disabled by default
- writes require `hillview_controls_enabled: true`
- only one entity is allowlisted
- no generic service executor is exposed
- no broad Home Assistant write surface is added
- failed or disabled control returns a blocked result
