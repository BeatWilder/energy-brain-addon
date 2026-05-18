# Energy Brain Live Entity Mapping

Canonical live Home Assistant entities validated against real runtime data.

==================================================
BATTERY
==================================================

Entity:
sensor.alphaess_soc_battery

Meaning:
Battery state of charge

Unit:
%

Observed:
73.2

Notes:
- Canonical battery SOC source
- Used by planner + controller
- Must remain within configured SOC limits


==================================================
PV
==================================================

Entity:
sensor.alphaess_current_pv_production

Meaning:
Current PV inverter production

Unit:
W

Observed:
10

Canonical normalization:
pv_power_kw = value_w / 1000.0

Notes:
- Raw HA value is Watts
- Planner/controller should use kW internally


==================================================
HOUSE LOAD
==================================================

Entity:
sensor.alphaess_current_house_load

Meaning:
Current household consumption

Unit:
W

Observed:
1216

Canonical normalization:
household_load_kw = value_w / 1000.0

Notes:
- Raw HA value is Watts
- Planner/controller should use kW internally


==================================================
GRID POWER
==================================================

Entity:
sensor.alphaess_power_grid

Meaning:
Current grid import/export power

Unit:
W

Observed:
-47

Canonical normalization:
grid_power_kw = value_w / 1000.0

Sign convention:
Negative = export
Positive = import

IMPORTANT:
Do not invert sign convention without validation.


==================================================
ELECTRICITY PRICE
==================================================

Entity:
sensor.current_electricity_price_all_in

Meaning:
Current electricity price

Unit:
€/kWh

Observed:
0.373

Notes:
- Already canonical
- No normalization required


==================================================
ARCHITECTURE RULES
==================================================

1. Planner must only consume canonical normalized values
2. Unit conversion belongs in HA adapter / normalization layer
3. Planner/controller must never consume raw HA units directly
4. Missing/invalid entities must fail safe to observer/no-action
5. Sign conventions must remain deterministic and documented
