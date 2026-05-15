from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


VALID_MODES = {"observer", "shadow", "active"}


@dataclass(frozen=True)
class EntityConfig:
    battery_soc: str
    pv_power: str
    grid_price: str
    household_load: str


@dataclass(frozen=True)
class BatteryConfig:
    capacity_kwh: float
    soc_min_percent: float
    soc_max_percent: float
    reserve_percent: float
    max_charge_kw: float
    max_discharge_kw: float
    charge_efficiency: float
    discharge_efficiency: float


@dataclass(frozen=True)
class CommandConfig:
    entity_id: str
    service: str
    service_domain: str
    value_field: str

    @property
    def configured(self) -> bool:
        return bool(self.entity_id and self.service and self.service_domain and self.value_field)


@dataclass(frozen=True)
class AppConfig:
    mode: str
    cycle_seconds: int
    horizon_steps: int
    entities: EntityConfig
    battery: BatteryConfig | None
    command: CommandConfig

    @property
    def required_entities_configured(self) -> bool:
        return all(
            [
                self.entities.battery_soc,
                self.entities.pv_power,
                self.entities.grid_price,
                self.entities.household_load,
            ]
        )


def load_config(env: Mapping[str, str] | None = None) -> AppConfig:
    source = os.environ if env is None else env
    mode = _str(source, "ENERGY_BRAIN_MODE", "observer")
    if mode not in VALID_MODES:
        mode = "observer"

    battery = _load_battery(source)
    return AppConfig(
        mode=mode,
        cycle_seconds=max(60, _int(source, "ENERGY_BRAIN_CYCLE_SECONDS", 900)),
        horizon_steps=max(1, _int(source, "ENERGY_BRAIN_HORIZON_STEPS", 96)),
        entities=EntityConfig(
            battery_soc=_str(source, "ENERGY_BRAIN_BATTERY_SOC_ENTITY", ""),
            pv_power=_str(source, "ENERGY_BRAIN_PV_POWER_ENTITY", ""),
            grid_price=_str(source, "ENERGY_BRAIN_GRID_PRICE_ENTITY", ""),
            household_load=_str(source, "ENERGY_BRAIN_HOUSEHOLD_LOAD_ENTITY", ""),
        ),
        battery=battery,
        command=CommandConfig(
            entity_id=_str(source, "ENERGY_BRAIN_COMMAND_ENTITY", ""),
            service=_str(source, "ENERGY_BRAIN_COMMAND_SERVICE", ""),
            service_domain=_str(source, "ENERGY_BRAIN_COMMAND_SERVICE_DOMAIN", ""),
            value_field=_str(source, "ENERGY_BRAIN_COMMAND_VALUE_FIELD", ""),
        ),
    )


def _load_battery(source: Mapping[str, str]) -> BatteryConfig | None:
    required = [
        "ENERGY_BRAIN_BATTERY_CAPACITY_KWH",
        "ENERGY_BRAIN_SOC_MIN_PERCENT",
        "ENERGY_BRAIN_SOC_MAX_PERCENT",
        "ENERGY_BRAIN_RESERVE_PERCENT",
        "ENERGY_BRAIN_MAX_CHARGE_KW",
        "ENERGY_BRAIN_MAX_DISCHARGE_KW",
    ]
    if any(_str(source, key, "") in {"", "null", "None"} for key in required):
        return None

    battery = BatteryConfig(
        capacity_kwh=_float(source, "ENERGY_BRAIN_BATTERY_CAPACITY_KWH", 0.0),
        soc_min_percent=_float(source, "ENERGY_BRAIN_SOC_MIN_PERCENT", 0.0),
        soc_max_percent=_float(source, "ENERGY_BRAIN_SOC_MAX_PERCENT", 100.0),
        reserve_percent=_float(source, "ENERGY_BRAIN_RESERVE_PERCENT", 0.0),
        max_charge_kw=_float(source, "ENERGY_BRAIN_MAX_CHARGE_KW", 0.0),
        max_discharge_kw=_float(source, "ENERGY_BRAIN_MAX_DISCHARGE_KW", 0.0),
        charge_efficiency=_float(source, "ENERGY_BRAIN_CHARGE_EFFICIENCY", 0.95),
        discharge_efficiency=_float(source, "ENERGY_BRAIN_DISCHARGE_EFFICIENCY", 0.95),
    )
    if not valid_battery_config(battery):
        return None
    return battery


def valid_battery_config(battery: BatteryConfig) -> bool:
    return (
        battery.capacity_kwh > 0.0
        and 0.0 <= battery.soc_min_percent <= battery.reserve_percent <= battery.soc_max_percent <= 100.0
        and battery.max_charge_kw >= 0.0
        and battery.max_discharge_kw >= 0.0
        and 0.0 < battery.charge_efficiency <= 1.0
        and 0.0 < battery.discharge_efficiency <= 1.0
    )


def _str(source: Mapping[str, str], key: str, default: str) -> str:
    return str(source.get(key, default)).strip()


def _int(source: Mapping[str, str], key: str, default: int) -> int:
    try:
        return int(float(_str(source, key, str(default))))
    except ValueError:
        return default


def _float(source: Mapping[str, str], key: str, default: float) -> float:
    try:
        return float(_str(source, key, str(default)))
    except ValueError:
        return default
