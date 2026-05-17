from __future__ import annotations

from html import escape
from typing import Any


MISSING_VALUES = (None, "", "unknown", "unavailable", "none", "None", "nan")


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        cur: Any = data
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in MISSING_VALUES:
            return cur
    return None


def _num(value: Any) -> float | None:
    if value in MISSING_VALUES:
        return None
    try:
        if isinstance(value, str):
            cleaned = (
                value.strip()
                .replace(",", ".")
                .replace("kWh", "")
                .replace("kW", "")
                .replace("W", "")
                .replace("%", "")
                .strip()
            )
            if cleaned in ("", "-", "--", "—"):
                return None
            return float(cleaned)
        return float(value)
    except (TypeError, ValueError):
        return None


def _power(value: Any) -> tuple[str, str]:
    number = _num(value)
    if number is None:
        return "—", "kW"
    if abs(number) > 50:
        number = number / 1000.0
    if abs(number) < 0.05:
        return "0", "W"
    return f"{abs(number):.1f}".replace(".", ","), "kW"


def _signed_w(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "—"
    if abs(number) <= 50:
        number = number * 1000.0
    return str(int(round(abs(number))))


def _percent(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "—"
    return str(int(round(number)))


def render_ha_powerflow_card(display_data: dict[str, Any] | None = None) -> str:
    data = display_data if isinstance(display_data, dict) else {}

    pv_raw = _pick(
        data,
        "pv_power_kw",
        "pv_now_kw",
        "pv_now",
        "pv_power_w",
        "pv_power",
        "energy_flow.pv_power_kw",
        "predbat.pv_power_kw",
    )
    home_raw = _pick(
        data,
        "household_load_kw",
        "home_load_kw",
        "load_kw",
        "house_kw",
        "house",
        "household_load_w",
        "energy_flow.household_load_kw",
        "predbat.household_load_kw",
    )
    grid_raw = _pick(
        data,
        "grid_power_kw",
        "grid_kw",
        "net_kw",
        "grid_power_w",
        "grid_power",
        "energy_flow.grid_power_kw",
        "predbat.grid_power_kw",
    )
    battery_raw = _pick(
        data,
        "battery_power_kw",
        "battery_kw",
        "battery_power_w",
        "battery_charge_kw",
        "battery_discharge_kw",
        "predbat.battery_power",
        "predbat.battery_power_best",
    )
    soc_raw = _pick(
        data,
        "soc_percent",
        "battery_soc_percent",
        "soc",
        "battery_soc",
        "battery.soc_percent",
        "predbat.soc_percent",
    )

    pv, pv_unit = _power(pv_raw)
    home, home_unit = _power(home_raw)
    grid_w = _signed_w(grid_raw)
    battery_w = _signed_w(battery_raw)
    soc = _percent(soc_raw)

    return f'''
<style>
  /* ENERGY_BRAIN_HA_POWERFLOW_COMPONENT_V1_START */
  .eb-ha-flow-card {{
    width:100%;
    max-width:500px;
    margin:0 auto;
    padding:8px 5px 6px;
    border:1px solid rgba(222,238,246,.13);
    border-radius:8px;
    background:linear-gradient(180deg,rgba(19,29,36,.92),rgba(10,16,21,.97));
    overflow:hidden;
  }}
  .eb-ha-flow-svg {{
    display:block;
    width:100%;
    height:auto;
    max-height:284px;
  }}
  .eb-ha-title {{
    fill:rgba(246,247,244,.78);
    font:600 15px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  }}
  .eb-ha-label {{
    fill:rgba(246,247,244,.82);
    font:600 12px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  }}
  .eb-ha-value {{
    fill:rgba(250,250,247,.94);
    font:600 12px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  }}
  .eb-ha-small {{
    fill:rgba(250,250,247,.86);
    font:600 10px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  }}
  .eb-ha-node {{ fill:#10110f; }}
  .eb-ha-road {{
    fill:none;
    stroke-linecap:round;
    stroke-linejoin:round;
    stroke-width:1.3;
    opacity:.8;
  }}
  .eb-ha-road-soft {{
    fill:none;
    stroke-linecap:round;
    stroke-linejoin:round;
    stroke-width:.85;
    opacity:.36;
  }}
  .eb-ha-dot {{ opacity:.82; }}
  @media (max-width:430px) {{
    .eb-ha-flow-card {{ padding:6px 2px 4px; }}
    .eb-ha-flow-svg {{ max-height:260px; }}
    .eb-ha-title {{ font-size:14px; }}
    .eb-ha-label {{ font-size:11.5px; }}
    .eb-ha-value {{ font-size:11.5px; }}
    .eb-ha-small {{ font-size:9.5px; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    .eb-ha-dot {{ display:none; }}
  }}
  /* ENERGY_BRAIN_HA_POWERFLOW_COMPONENT_V1_END */
</style>

<div class="eb-ha-flow-card" aria-label="Energy Brain powerflow">
  <svg class="eb-ha-flow-svg" viewBox="0 0 360 278" role="img" aria-label="Zonne-energie, net, huis en batterij powerflow">
    <text class="eb-ha-title" x="180" y="20" text-anchor="middle">Zonne-energie</text>

    <path class="eb-ha-road-soft" stroke="#9d61ff" d="M172 83 L172 192"/>
    <path class="eb-ha-road" stroke="#f6a33b" d="M180 83 L180 192"/>
    <path class="eb-ha-road-soft" stroke="#54d9c9" d="M188 83 L188 192"/>

    <path class="eb-ha-road-soft" stroke="#9d61ff" d="M96 138 L264 138"/>
    <path class="eb-ha-road" stroke="#69b7ff" d="M96 146 L264 146"/>
    <path class="eb-ha-road-soft" stroke="#54d9c9" d="M96 154 L264 154"/>

    <path class="eb-ha-road-soft" stroke="#9d61ff" d="M172 85 C156 112 132 128 96 138"/>
    <path class="eb-ha-road-soft" stroke="#f6a33b" d="M188 85 C204 112 228 128 264 154"/>

    <circle class="eb-ha-dot" r="3" fill="#f6a33b">
      <animateMotion dur="4.6s" repeatCount="indefinite" path="M180 83 L180 192"/>
    </circle>
    <circle class="eb-ha-dot" r="3" fill="#9d61ff">
      <animateMotion dur="5.2s" repeatCount="indefinite" path="M96 138 L264 138"/>
    </circle>
    <circle class="eb-ha-dot" r="3" fill="#54d9c9">
      <animateMotion dur="5.7s" repeatCount="indefinite" path="M96 154 L264 154"/>
    </circle>

    <circle class="eb-ha-node" cx="180" cy="56" r="29"/>
    <circle cx="180" cy="56" r="29" fill="none" stroke="#f6a33b" stroke-width="1.8"/>
    <text x="180" y="53" text-anchor="middle" font-size="18" fill="#ffd56d">PV</text>
    <text class="eb-ha-value" x="180" y="73" text-anchor="middle">{escape(pv)} {escape(pv_unit)}</text>
    <text class="eb-ha-label" x="180" y="104" text-anchor="middle">PV</text>

    <circle class="eb-ha-node" cx="62" cy="146" r="33"/>
    <circle cx="62" cy="146" r="33" fill="none" stroke="#9d61ff" stroke-width="1.8"/>
    <text x="62" y="142" text-anchor="middle" font-size="17" fill="#f4f5f2">Net</text>
    <text class="eb-ha-small" x="62" y="162" text-anchor="middle">↔ {escape(grid_w)} W</text>
    <text class="eb-ha-label" x="62" y="192" text-anchor="middle">Net</text>

    <circle class="eb-ha-node" cx="298" cy="146" r="33"/>
    <path d="M298 113 A33 33 0 0 1 331 146" fill="none" stroke="#f6a33b" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M331 146 A33 33 0 1 1 298 113" fill="none" stroke="#54d9c9" stroke-width="1.8" stroke-linecap="round"/>
    <text x="298" y="142" text-anchor="middle" font-size="16" fill="#f4f5f2">Huis</text>
    <text class="eb-ha-value" x="298" y="162" text-anchor="middle">{escape(home)} {escape(home_unit)}</text>
    <text class="eb-ha-label" x="298" y="192" text-anchor="middle">Huis</text>

    <circle class="eb-ha-node" cx="180" cy="220" r="34"/>
    <circle cx="180" cy="220" r="34" fill="none" stroke="#54d9c9" stroke-width="1.8"/>
    <text class="eb-ha-value" x="180" y="205" text-anchor="middle">{escape(soc)} %</text>
    <text x="180" y="226" text-anchor="middle" font-size="17" fill="#f4f5f2">Bat</text>
    <text class="eb-ha-small" x="180" y="245" text-anchor="middle">↕ {escape(battery_w)} W</text>
    <text class="eb-ha-label" x="180" y="270" text-anchor="middle">Batterij</text>
  </svg>
</div>
'''
