from __future__ import annotations

import html


def _number(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def render_powerflow(data: dict) -> str:
    solar = _number(data.get("solar_kw", 0))
    house = _number(data.get("house_kw", 0))
    battery = _number(data.get("battery_kw", 0))
    grid = _number(data.get("grid_kw", 0))

    return f"""
    <div class="powerflow-mini" aria-label="Samenvatting energiestromen">
      <div class="mini-node"><span>Zon</span><b>{solar:.1f} kW</b></div>
      <div class="mini-node"><span>Huis</span><b>{house:.1f} kW</b></div>
      <div class="mini-node"><span>Batterij</span><b>{battery:.1f} kW</b></div>
      <div class="mini-node"><span>Net</span><b>{grid:.1f} kW</b></div>
      <div class="mini-status">{html.escape(str(data.get("state", "observer")), quote=True)}</div>
    </div>
    """


def powerflow_hero_component(data: dict) -> dict:
    return {
        "type": "powerflow_hero",
        "title": "Energy Brain",
        "status": "Live",
        "soc_percent": data.get("soc_percent", data.get("battery_soc_percent", 0)),
        "solar_kw": data.get("solar_kw", data.get("pv_power_kw", 0)),
        "house_kw": data.get("house_kw", data.get("household_load_kw", 0)),
        "battery_kw": data.get("battery_kw", data.get("battery_power_kw", 0)),
        "grid_kw": data.get("grid_kw", data.get("grid_power_kw", 0)),
        "price": data.get("price", data.get("grid_price", 0)),
        "decision": data.get("decision", "Energiestroom bewaken"),
        "updated": data.get("last_update", "laatste cyclus"),
    }
