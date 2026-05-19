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


def flow_state(value: Any) -> str:
    number = num(value)
    if number is None or abs(number) < 0.05:
        return "idle"
    return "active"


def render_powerflow(display_data: dict[str, Any] | None = None) -> str:
    data = display_data if isinstance(display_data, dict) else {}
    pv_raw = safe_pick(data, "pv_power_kw", "pv_now_kw", "pv_power_w", "pv_power")
    home_raw = safe_pick(data, "household_load_kw", "home_load_kw", "load_kw", "house_kw", "household_load_w")
    grid_raw = safe_pick(data, "grid_power_kw", "grid_kw", "net_kw", "grid_power_w", "grid_power")
    battery_raw = safe_pick(data, "battery_power_kw", "battery_kw", "battery_power_w", "battery_charge_kw", "battery_discharge_kw")
    soc = fmt_percent(safe_pick(data, "soc_percent", "battery_soc_percent", "soc", "battery_soc"))
    pv, pv_unit = fmt_power(pv_raw)
    home, home_unit = fmt_power(home_raw)
    grid = fmt_power_w(grid_raw)
    battery = fmt_power_w(battery_raw)
    state_class = " ".join(
        [
            f"pv-{flow_state(pv_raw)}",
            f"home-{flow_state(home_raw)}",
            f"grid-{flow_state(grid_raw)}",
            f"battery-{flow_state(battery_raw)}",
        ]
    )

    return f'''
<div class="pf2-card {escape(state_class)}" aria-label="Energy Brain powerflow">
  <!-- ENERGY_BRAIN_POWERFLOW_V2_START -->
  <svg class="pf2-svg" viewBox="0 0 360 278" role="img" aria-label="Zonne-energie, net, huis en batterij">
    <defs>
      <filter id="pf2SoftGlow" x="-40%" y="-40%" width="180%" height="180%">
        <feGaussianBlur stdDeviation="2.1" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    <text class="pf2-title" x="180" y="22" text-anchor="middle">Zonne-energie</text>

    <path class="pf2-lane soft" stroke="#8f77ff" d="M171 91 L171 187"/>
    <path class="pf2-lane main lane-pv" stroke="#f5b45d" d="M180 91 L180 187"/>
    <path class="pf2-lane soft lane-battery" stroke="#54d9c9" d="M189 91 L189 187"/>

    <path class="pf2-lane soft lane-grid" stroke="#8f77ff" d="M98 138 L262 138"/>
    <path class="pf2-lane main lane-home" stroke="#75b9ff" d="M98 147 L262 147"/>
    <path class="pf2-lane soft lane-return" stroke="#54d9c9" d="M98 156 L262 156"/>

    <circle class="pf2-dot pf2-particle pv one" cx="180" cy="139" r="2.7" fill="#f5b45d"/>
    <circle class="pf2-dot pf2-particle pv two" cx="180" cy="139" r="2.2" fill="#ffd56d"/>
    <circle class="pf2-dot pf2-particle home one" cx="180" cy="147" r="2.6" fill="#75b9ff"/>
    <circle class="pf2-dot pf2-particle home two" cx="180" cy="147" r="2.1" fill="#9fd2ff"/>
    <circle class="pf2-dot pf2-particle battery one" cx="180" cy="156" r="2.4" fill="#54d9c9"/>
    <circle class="pf2-dot pf2-particle battery two" cx="180" cy="156" r="2.0" fill="#8af2df"/>

    <circle class="pf2-node" cx="180" cy="57" r="30"/>
    <circle class="pf2-ring solar" cx="180" cy="57" r="30"/>
    <text class="pf2-node-name solar-text" x="180" y="54" text-anchor="middle">PV</text>
    <text class="pf2-node-value" x="180" y="74" text-anchor="middle">{escape(pv)} {escape(pv_unit)}</text>

    <circle class="pf2-node pf2-grid-node" cx="62" cy="147" r="33"/>
    <circle class="pf2-ring grid" cx="62" cy="147" r="33"/>
    <text class="pf2-node-name" x="62" y="143" text-anchor="middle">Net</text>
    <text class="pf2-node-small" x="62" y="163" text-anchor="middle">↔ {escape(grid)} W</text>

    <circle class="pf2-node" cx="298" cy="147" r="33"/>
    <circle class="pf2-ring home" cx="298" cy="147" r="33"/>
    <text class="pf2-node-name" x="298" y="143" text-anchor="middle">Huis</text>
    <text class="pf2-node-value" x="298" y="163" text-anchor="middle">{escape(home)} {escape(home_unit)}</text>

    <circle class="pf2-node pf2-battery-node" cx="180" cy="222" r="34"/>
    <circle class="pf2-ring battery" cx="180" cy="222" r="34"/>
    <text class="pf2-node-value" x="180" y="207" text-anchor="middle">{escape(soc)} %</text>
    <text class="pf2-node-name" x="180" y="228" text-anchor="middle">Batterij</text>
    <text class="pf2-node-small" x="180" y="247" text-anchor="middle">↕ {escape(battery)} W</text>
  </svg>
</div>
'''
