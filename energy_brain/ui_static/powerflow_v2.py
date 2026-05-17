from __future__ import annotations

from html import escape
from typing import Any


MISSING = (None, "", "unknown", "unavailable", "none", "None", "nan")


def safe_pick(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        cur: Any = data
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in MISSING:
            return cur
    return default


def num(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("state", value.get("value"))
    if value in MISSING:
        return None
    try:
        text = str(value).strip()
        text = (
            text.replace(",", ".")
            .replace("kWh", "")
            .replace("kW", "")
            .replace("W", "")
            .replace("%", "")
            .strip()
        )
        if text in ("", "-", "--", "—"):
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def fmt_power(value: Any, *, signed: bool = False) -> tuple[str, str]:
    number = num(value)
    if number is None:
        return "—", "kW"
    if abs(number) > 50:
        number = number / 1000.0
    prefix = "+" if signed and number > 0 else ""
    return f"{prefix}{number:.1f}".replace(".", ","), "kW"


def fmt_power_w(value: Any) -> str:
    number = num(value)
    if number is None:
        return "—"
    if abs(number) <= 50:
        number = number * 1000.0
    return str(int(round(abs(number))))


def fmt_percent(value: Any) -> str:
    number = num(value)
    if number is None:
        return "—"
    return f"{number:.0f}"


def render_powerflow(display_data: dict[str, Any] | None = None) -> str:
    data = display_data if isinstance(display_data, dict) else {}
    soc = fmt_percent(safe_pick(data, "soc_percent", "battery_soc_percent", "soc", "battery_soc"))
    pv, pv_unit = fmt_power(safe_pick(data, "pv_power_kw", "pv_now_kw", "pv_power_w", "pv_power"))
    home, home_unit = fmt_power(
        safe_pick(data, "household_load_kw", "home_load_kw", "load_kw", "house_kw", "household_load_w")
    )
    grid = fmt_power_w(safe_pick(data, "grid_power_kw", "grid_kw", "net_kw", "grid_power_w", "grid_power"))
    battery = fmt_power_w(
        safe_pick(data, "battery_power_kw", "battery_kw", "battery_power_w", "battery_charge_kw", "battery_discharge_kw")
    )

    return f'''
<div class="pf2-card" aria-label="Energy Brain powerflow">
  <!-- ENERGY_BRAIN_POWERFLOW_V2_START -->
  <svg class="pf2-svg" viewBox="0 0 360 278" role="img" aria-label="Zonne-energie, net, huis en batterij">
    <text class="pf2-title" x="180" y="22" text-anchor="middle">Zonne-energie</text>

    <path class="pf2-lane soft" stroke="#8f77ff" d="M171 83 L171 195"/>
    <path class="pf2-lane main" stroke="#f5b45d" d="M180 83 L180 195"/>
    <path class="pf2-lane soft" stroke="#54d9c9" d="M189 83 L189 195"/>

    <path class="pf2-lane soft" stroke="#8f77ff" d="M96 138 L264 138"/>
    <path class="pf2-lane main" stroke="#75b9ff" d="M96 147 L264 147"/>
    <path class="pf2-lane soft" stroke="#54d9c9" d="M96 156 L264 156"/>

    <circle class="pf2-dot" r="2.8" fill="#f5b45d">
      <animateMotion dur="5.2s" repeatCount="indefinite" path="M180 83 L180 195"/>
    </circle>
    <circle class="pf2-dot" r="2.7" fill="#75b9ff">
      <animateMotion dur="5.8s" repeatCount="indefinite" path="M96 147 L264 147"/>
    </circle>
    <circle class="pf2-dot" r="2.5" fill="#54d9c9">
      <animateMotion dur="6.4s" repeatCount="indefinite" path="M264 156 L96 156"/>
    </circle>

    <circle class="pf2-node" cx="180" cy="57" r="30"/>
    <circle class="pf2-ring solar" cx="180" cy="57" r="30"/>
    <text class="pf2-node-name solar-text" x="180" y="54" text-anchor="middle">PV</text>
    <text class="pf2-node-value" x="180" y="74" text-anchor="middle">{escape(pv)} {escape(pv_unit)}</text>

    <circle class="pf2-node" cx="62" cy="147" r="33"/>
    <circle class="pf2-ring grid" cx="62" cy="147" r="33"/>
    <text class="pf2-node-name" x="62" y="143" text-anchor="middle">Net</text>
    <text class="pf2-node-small" x="62" y="163" text-anchor="middle">↔ {escape(grid)} W</text>

    <circle class="pf2-node" cx="298" cy="147" r="33"/>
    <circle class="pf2-ring home" cx="298" cy="147" r="33"/>
    <text class="pf2-node-name" x="298" y="143" text-anchor="middle">Huis</text>
    <text class="pf2-node-value" x="298" y="163" text-anchor="middle">{escape(home)} {escape(home_unit)}</text>

    <circle class="pf2-node" cx="180" cy="222" r="34"/>
    <circle class="pf2-ring battery" cx="180" cy="222" r="34"/>
    <text class="pf2-node-value" x="180" y="207" text-anchor="middle">{escape(soc)} %</text>
    <text class="pf2-node-name" x="180" y="228" text-anchor="middle">Batterij</text>
    <text class="pf2-node-small" x="180" y="247" text-anchor="middle">↕ {escape(battery)} W</text>
  </svg>
</div>
'''
