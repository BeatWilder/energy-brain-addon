from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

import requests

from .config import AppConfig
from .planner import EnergySnapshot


class HomeAssistantClient:
    def __init__(self, base_url: str | None = None, token: str | None = None, timeout: int = 10) -> None:
        self.base_url = (base_url or os.environ.get("SUPERVISOR_URL") or "http://supervisor/core").rstrip("/")
        self.token = token or os.environ.get("SUPERVISOR_TOKEN", "")
        self.timeout = timeout

    def read_snapshot(self, config: AppConfig) -> EnergySnapshot:
        if not config.required_entities_configured:
            return EnergySnapshot(None, None, None, None)
        return EnergySnapshot(
            battery_soc_percent=self._read_float_state(config.entities.battery_soc),
            pv_power_kw=self._read_float_state(config.entities.pv_power),
            grid_price=self._read_float_state(config.entities.grid_price),
            household_load_kw=self._read_float_state(config.entities.household_load),
        )

    def write_battery_setpoint(self, config: AppConfig, setpoint_kw: float) -> dict[str, Any]:
        if not config.command.configured:
            return {"ok": False, "error": "missing_command_configuration"}
        payload = {"entity_id": config.command.entity_id, config.command.value_field: setpoint_kw}
        path = f"/api/services/{config.command.service_domain}/{config.command.service}"
        response = self._request("POST", path, json=payload)
        return {"ok": response.ok, "status_code": response.status_code}

    def _read_float_state(self, entity_id: str) -> float | None:
        response = self._request("GET", f"/api/states/{entity_id}")
        if not response.ok:
            return None
        try:
            state = response.json().get("state")
            if state in {None, "unknown", "unavailable"}:
                return None
            return float(state)
        except (TypeError, ValueError):
            return None

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        return requests.request(method, f"{self.base_url}{path}", headers=headers, timeout=self.timeout, **kwargs)


def snapshot_as_dict(snapshot: EnergySnapshot) -> dict[str, Any]:
    return asdict(snapshot)
