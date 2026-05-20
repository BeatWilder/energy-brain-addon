from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass(frozen=True)
class HomeAssistantSnapshot:
    battery_soc_percent: float | None
    pv_power_kw: float | None
    grid_price: float | None
    household_load_kw: float | None


class HomeAssistantClient:
    def __init__(self) -> None:
        self.base_url = "http://supervisor/core/api"
        self.token = os.environ.get("SUPERVISOR_TOKEN")
        if not self.token:
            raise RuntimeError("Missing SUPERVISOR_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_state_object(self, entity_id: str) -> dict[str, Any] | None:
        if not entity_id:
            return None
        r = requests.get(f"{self.base_url}/states/{entity_id}", headers=self.headers, timeout=10)
        if r.status_code != 200:
            print(f"[HA ERROR] {entity_id}: {r.status_code} {r.text}")
            return None
        data = r.json()
        return data if isinstance(data, dict) else None

    def get_state(self, entity_id: str) -> Any:
        data = self.get_state_object(entity_id)
        if not data:
            return None
        return data.get("state")

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        try:
            if value in (None, "", "unknown", "unavailable"):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _options() -> dict[str, Any]:
        path = Path("/data/options.json")
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception as exc:
            print(f"[CONFIG ERROR] failed to read /data/options.json: {exc}")
            return {}

    @staticmethod
    def _cfg(config: Any, name: str) -> str:
        if hasattr(config, name):
            value = getattr(config, name)
            if value:
                return str(value)
        if isinstance(config, dict) and config.get(name):
            return str(config[name])
        return str(HomeAssistantClient._options().get(name, ""))

    @staticmethod
    def _power_kw(value: Any) -> float | None:
        power = HomeAssistantClient._float_or_none(value)
        if power is None:
            return None

        # AlphaESS power sensors are often W, while planner expects kW.
        # Safe heuristic: normal home power above 50 is almost certainly W.
        if abs(power) > 50:
            return power / 1000.0

        return power


    def call_service_guarded(self, domain: str, service: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call a Home Assistant service through a tiny allowlisted Hillview control surface."""
        entity_id = str(payload.get("entity_id", ""))

        allowed = {
            ("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch"),
            ("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch"),
            ("input_select", "select_option", "input_select.alphaess_helper_dispatch_mode"),
            ("input_number", "set_value", "input_number.alphaess_helper_dispatch_duration"),
            ("input_number", "set_value", "input_number.alphaess_helper_dispatch_power"),
            ("input_number", "set_value", "input_number.alphaess_helper_dispatch_cutoff_soc"),
            ("climate", "set_temperature", "climate.ir_woonkamer"),
            ("climate", "set_temperature", "climate.w100_keuken"),
        }

        if (domain, service, entity_id) not in allowed:
            return {
                "ok": False,
                "reason": "not_allowlisted",
                "domain": domain,
                "service": service,
                "entity_id": entity_id,
            }

        guard = self._validate_guarded_payload(domain, service, entity_id, payload)
        if not guard.get("ok"):
            return guard

        url = f"{self.base_url}/services/{domain}/{service}"
        r = requests.post(url, headers=self.headers, json=payload, timeout=10)

        return {
            "ok": 200 <= r.status_code < 300,
            "status_code": r.status_code,
            "domain": domain,
            "service": service,
            "entity_id": entity_id,
            "response": r.text[:500],
        }

    def _validate_guarded_payload(
        self,
        domain: str,
        service: str,
        entity_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate options/min/max from Home Assistant before writing."""
        if domain == "input_boolean":
            return {"ok": True}

        state = self.get_state_object(entity_id)
        if not state:
            return {
                "ok": False,
                "reason": "state_unavailable",
                "domain": domain,
                "service": service,
                "entity_id": entity_id,
            }

        attrs = state.get("attributes")
        if not isinstance(attrs, dict):
            attrs = {}

        if domain == "input_select":
            option = str(payload.get("option", ""))
            options = attrs.get("options")
            if not isinstance(options, list) or not options:
                return {
                    "ok": False,
                    "reason": "input_select_options_missing",
                    "entity_id": entity_id,
                }
            if option not in [str(item) for item in options]:
                return {
                    "ok": False,
                    "reason": "option_not_allowed",
                    "entity_id": entity_id,
                    "option": option,
                    "allowed_options": options,
                }
            return {"ok": True}

        if domain == "input_number":
            try:
                value = float(payload.get("value"))
            except (TypeError, ValueError):
                return {
                    "ok": False,
                    "reason": "invalid_number",
                    "entity_id": entity_id,
                    "value": payload.get("value"),
                }

            minimum = self._float_or_none(attrs.get("min"))
            maximum = self._float_or_none(attrs.get("max"))

            if minimum is None or maximum is None:
                return {
                    "ok": False,
                    "reason": "input_number_bounds_missing",
                    "entity_id": entity_id,
                }

            if value < minimum or value > maximum:
                return {
                    "ok": False,
                    "reason": "value_outside_bounds",
                    "entity_id": entity_id,
                    "value": value,
                    "min": minimum,
                    "max": maximum,
                }

            return {"ok": True}

        if domain == "climate" and service == "set_temperature":
            try:
                temperature = float(payload.get("temperature"))
            except (TypeError, ValueError):
                return {
                    "ok": False,
                    "reason": "invalid_temperature",
                    "entity_id": entity_id,
                    "temperature": payload.get("temperature"),
                }

            minimum = self._float_or_none(attrs.get("min_temp"))
            maximum = self._float_or_none(attrs.get("max_temp"))
            if minimum is None or maximum is None:
                return {
                    "ok": False,
                    "reason": "climate_temperature_bounds_missing",
                    "entity_id": entity_id,
                }

            if temperature < minimum or temperature > maximum:
                return {
                    "ok": False,
                    "reason": "temperature_outside_bounds",
                    "entity_id": entity_id,
                    "temperature": temperature,
                    "min": minimum,
                    "max": maximum,
                }

            return {"ok": True}

        return {
            "ok": False,
            "reason": "unsupported_guarded_payload",
            "domain": domain,
            "service": service,
            "entity_id": entity_id,
        }


    def read_snapshot(self, config: Any) -> HomeAssistantSnapshot:
        return HomeAssistantSnapshot(
            battery_soc_percent=self._float_or_none(self.get_state(self._cfg(config, "battery_soc_entity"))),
            pv_power_kw=self._power_kw(self.get_state(self._cfg(config, "pv_power_entity"))),
            grid_price=self._float_or_none(self.get_state(self._cfg(config, "grid_price_entity"))),
            household_load_kw=self._power_kw(self.get_state(self._cfg(config, "household_load_entity"))),
        )


def snapshot_as_dict(snapshot: HomeAssistantSnapshot) -> dict[str, float | None]:
    return {
        "battery_soc_percent": snapshot.battery_soc_percent,
        "pv_power_kw": snapshot.pv_power_kw,
        "grid_price": snapshot.grid_price,
        "household_load_kw": snapshot.household_load_kw,
    }
