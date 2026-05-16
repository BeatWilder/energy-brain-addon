#!/usr/bin/with-contenv bashio
set -euo pipefail

# Energy Brain read-only web UI
# Safe by design:
# - reads /data/energy_brain_cycles.jsonl only
# - no Home Assistant service calls
# - no battery writes
# - no control buttons
export ENERGY_BRAIN_UI_HOST="${ENERGY_BRAIN_UI_HOST:-0.0.0.0}"
export ENERGY_BRAIN_UI_PORT="${ENERGY_BRAIN_UI_PORT:-8099}"
export ENERGY_BRAIN_HISTORY_PATH="${ENERGY_BRAIN_HISTORY_PATH:-/data/energy_brain_cycles.jsonl}"

echo "Starting Energy Brain read-only UI on ${ENERGY_BRAIN_UI_HOST}:${ENERGY_BRAIN_UI_PORT}"
python3 -m energy_brain.web_ui &


export ENERGY_BRAIN_MODE="$(bashio::config 'mode')"
export ENERGY_BRAIN_CYCLE_SECONDS="$(bashio::config 'cycle_seconds')"
export ENERGY_BRAIN_HORIZON_STEPS="$(bashio::config 'horizon_steps')"

export ENERGY_BRAIN_BATTERY_SOC_ENTITY="$(bashio::config 'battery_soc_entity')"
export ENERGY_BRAIN_PV_POWER_ENTITY="$(bashio::config 'pv_power_entity')"
export ENERGY_BRAIN_GRID_PRICE_ENTITY="$(bashio::config 'grid_price_entity')"
export ENERGY_BRAIN_HOUSEHOLD_LOAD_ENTITY="$(bashio::config 'household_load_entity')"

export ENERGY_BRAIN_BATTERY_CAPACITY_KWH="$(bashio::config 'battery_capacity_kwh')"
export ENERGY_BRAIN_SOC_MIN_PERCENT="$(bashio::config 'soc_min_percent')"
export ENERGY_BRAIN_SOC_MAX_PERCENT="$(bashio::config 'soc_max_percent')"
export ENERGY_BRAIN_RESERVE_PERCENT="$(bashio::config 'reserve_percent')"
export ENERGY_BRAIN_MAX_CHARGE_KW="$(bashio::config 'max_charge_kw')"
export ENERGY_BRAIN_MAX_DISCHARGE_KW="$(bashio::config 'max_discharge_kw')"
export ENERGY_BRAIN_CHARGE_EFFICIENCY="$(bashio::config 'charge_efficiency')"
export ENERGY_BRAIN_DISCHARGE_EFFICIENCY="$(bashio::config 'discharge_efficiency')"

export ENERGY_BRAIN_COMMAND_ENTITY="$(bashio::config 'command_entity')"
export ENERGY_BRAIN_COMMAND_SERVICE="$(bashio::config 'command_service')"
export ENERGY_BRAIN_COMMAND_SERVICE_DOMAIN="$(bashio::config 'command_service_domain')"
export ENERGY_BRAIN_COMMAND_VALUE_FIELD="$(bashio::config 'command_value_field')"

exec python3 -m energy_brain.main
