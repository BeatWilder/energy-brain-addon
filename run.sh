#!/usr/bin/with-contenv bashio
set -euo pipefail

# Energy Brain add-on runtime
# Safe by design:
# - web UI is read-only
# - no Home Assistant service calls from web UI
# - no battery writes from web UI
# - no control buttons unless explicitly enabled elsewhere

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

export ENERGY_BRAIN_UI_HOST="${ENERGY_BRAIN_UI_HOST:-0.0.0.0}"
export ENERGY_BRAIN_UI_PORT="${ENERGY_BRAIN_UI_PORT:-8099}"
export ENERGY_BRAIN_HISTORY_PATH="${ENERGY_BRAIN_HISTORY_PATH:-/data/energy_brain_cycles.jsonl}"

echo "Starting Energy Brain read-only UI on ${ENERGY_BRAIN_UI_HOST}:${ENERGY_BRAIN_UI_PORT}"
python3 -B -m energy_brain.web_ui &
WEB_UI_PID="$!"

echo "Waiting for Energy Brain read-only UI health endpoint..."
for i in $(seq 1 30); do
  if wget -q -O - "http://127.0.0.1:${ENERGY_BRAIN_UI_PORT}/health" >/dev/null 2>&1; then
    echo "Energy Brain read-only UI is ready"
    break
  fi

  if ! kill -0 "${WEB_UI_PID}" >/dev/null 2>&1; then
    echo "FAIL: Energy Brain read-only UI exited before becoming ready"
    wait "${WEB_UI_PID}" || true
    exit 1
  fi

  sleep 1
done

if ! wget -q -O - "http://127.0.0.1:${ENERGY_BRAIN_UI_PORT}/health" >/dev/null 2>&1; then
  echo "FAIL: Energy Brain read-only UI did not become ready on port ${ENERGY_BRAIN_UI_PORT}"
  exit 1
fi

echo "Starting Energy Brain main loop in ${ENERGY_BRAIN_MODE} mode"
exec python3 -m energy_brain.main
