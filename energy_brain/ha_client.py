import os
import requests
import json


class HAClient:
    def __init__(self):
        self.base_url = "http://supervisor/core/api"
        self.token = os.environ.get("SUPERVISOR_TOKEN")

        if not self.token:
            raise Exception("Missing SUPERVISOR_TOKEN (HA add-on environment)")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get(self, entity_id: str):
        url = f"{self.base_url}/states/{entity_id}"
        r = requests.get(url, headers=self.headers, timeout=10)

        if r.status_code != 200:
            return None

        return r.json().get("state")

    def _f(self, v):
        try:
            return float(v)
        except:
            return None

    def get_state_snapshot(self, config: dict):
        return {
            "battery_soc_percent": self._f(self._get(config["battery_soc_entity"])),
            "pv_power_kw": self._f(self._get(config["pv_power_entity"])),
            "grid_price": self._f(self._get(config["grid_price_entity"])),
            "household_load_kw": self._f(self._get(config["household_load_entity"])),
        }
