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

    def get_state(self, entity_id: str) -> Any:
        if not entity_id:
            return None
        r = requests.get(f"{self.base_url}/states/{entity_id}", headers=self.headers, timeout=10)
        if r.status_code != 200:
            print(f"[HA ERROR] {entity_id}: {r.status_code} {r.text}")
            return None
        return r.json().get("state")

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
        """Call a Home Assistant service through a tiny allowlisted control surface."""
        allowed = {
            ("input_boolean", "turn_on", "input_boolean.alphaess_helper_dispatch"),
            ("input_boolean", "turn_off", "input_boolean.alphaess_helper_dispatch"),
        }

        entity_id = str(payload.get("entity_id", ""))
        if (domain, service, entity_id) not in allowed:
            return {
                "ok": False,
                "reason": "not_allowlisted",
                "domain": domain,
                "service": service,
                "entity_id": entity_id,
            }

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
