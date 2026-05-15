from __future__ import annotations

import os
from dataclasses import dataclass
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

        url = f"{self.base_url}/states/{entity_id}"
        response = requests.get(url, headers=self.headers, timeout=10)

        if response.status_code != 200:
            print(f"[HA ERROR] entity={entity_id} status={response.status_code} body={response.text}")
            return None

        return response.json().get("state")

    @staticmethod
    def _float_or_none(value: Any) -> float | None:
        try:
            if value in (None, "", "unknown", "unavailable"):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _cfg(config: Any, *names: str) -> Any:
        for name in names:
            if hasattr(config, name):
                return getattr(config, name)
        if isinstance(config, dict):
            for name in names:
                if name in config:
                    return config[name]
        return ""

    def read_snapshot(self, config: Any) -> HomeAssistantSnapshot:
        return HomeAssistantSnapshot(
            battery_soc_percent=self._float_or_none(
                self.get_state(self._cfg(config, "battery_soc_entity", "battery_soc_entity_id"))
            ),
            pv_power_kw=self._float_or_none(
                self.get_state(self._cfg(config, "pv_power_entity", "pv_power_entity_id"))
            ),
            grid_price=self._float_or_none(
                self.get_state(self._cfg(config, "grid_price_entity", "grid_price_entity_id"))
            ),
            household_load_kw=self._float_or_none(
                self.get_state(self._cfg(config, "household_load_entity", "household_load_entity_id"))
            ),
        )


def snapshot_as_dict(snapshot: HomeAssistantSnapshot) -> dict[str, float | None]:
    return {
        "battery_soc_percent": snapshot.battery_soc_percent,
        "pv_power_kw": snapshot.pv_power_kw,
        "grid_price": snapshot.grid_price,
        "household_load_kw": snapshot.household_load_kw,
    }
