# V2514-V2529 Hillview Dispatch Form Controls

This phase extends the Energy Brain EMS Hillview / AlphaESS page with guarded dispatch form controls.

Added to `/hillview`:

- dispatch mode selector
- duration input
- power input
- cutoff SoC input
- save settings button
- dispatch on button
- dispatch off button

Guarded Home Assistant writes:

- `input_select.alphaess_helper_dispatch_mode`
- `input_number.alphaess_helper_dispatch_duration`
- `input_number.alphaess_helper_dispatch_power`
- `input_number.alphaess_helper_dispatch_cutoff_soc`
- `input_boolean.alphaess_helper_dispatch`

Safety:

- all writes remain behind `hillview_controls_enabled: true`
- all writes use a fixed allowlist
- input_select options are validated against Home Assistant state attributes
- input_number values are validated against Home Assistant min/max attributes
- planner, controller and main runtime remain unchanged
- force charging / force discharging / force export remain unavailable from the Energy Brain app
