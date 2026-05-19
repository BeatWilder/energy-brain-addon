from __future__ import annotations

import html
from typing import Any

from energy_brain.ui.state.display_values import power_intensity


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def format_kw(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:.1f} kW"


def display_label(section: dict[str, Any], label_key: str, value_key: str) -> str:
    label = section.get(label_key)
    if isinstance(label, str) and label:
        return esc(label)
    return esc(format_kw(section.get(value_key)))


def _node_state(section: dict[str, Any], known_key: str) -> str:
    return "known" if section.get(known_key) is not False else "unknown"


def _num(value: Any) -> float | None:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def format_percent(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:.0f}%"


def format_price(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return esc(value or "—")
    return f"€{number:.3f}/kWh"


def _flow_label(flow: str) -> str:
    return {
        "charging": "Laden",
        "discharging": "Ontladen",
        "importing": "Import",
        "exporting": "Teruglevering",
        "active": "Actief",
        "reverse": "Terug",
        "idle": "Rust",
    }.get(flow, "Rust")


def flow_class(value: Any, positive: str = "active", negative: str = "reverse") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number > 0.05:
        return positive
    if number < -0.05:
        return negative
    return "idle"


def quality_note(section: dict[str, Any]) -> str:
    quality = section.get("data_quality")
    if not isinstance(quality, dict):
        return ""
    unknown = quality.get("unknown") if isinstance(quality.get("unknown"), list) else []
    clamped = quality.get("clamped") if isinstance(quality.get("clamped"), list) else []
    if unknown:
        return f'<span class="quality-chip">Meetdata mist: {esc(", ".join(str(item) for item in unknown[:3]))}</span>'
    if clamped:
        return f'<span class="quality-chip">Weergave begrensd: {esc(", ".join(str(item) for item in clamped[:3]))}</span>'
    return '<span class="quality-chip quality-live">Realtime meetdata</span>'


def _timeline_horizon(entries: list[dict[str, Any]]) -> str:
    segments = []
    for hour in range(24):
        item = entries[hour] if hour < len(entries) and isinstance(entries[hour], dict) else {}
        tone = esc(item.get("tone", "hold"))
        label = esc(item.get("action", "Geen preview"))
        soc_number = _num(item.get("soc_percent"))
        price_number = _num(item.get("price"))
        soc = max(0.0, min(100.0, soc_number)) if soc_number is not None else 0
        price = max(0.0, min(100.0, abs(price_number) * 220)) if price_number is not None else 0
        known_class = "known" if item else "unknown"
        segments.append(
            f'<div class="horizon-hour {known_class} tone-{tone}" style="--soc:{soc};--price:{price}" title="{hour:02d}:00 - {label}">'
            f'<span>{hour:02d}</span><i></i><b></b></div>'
        )
    return "".join(segments)


def _primary_reason(entries: list[dict[str, Any]]) -> str:
    for item in entries:
        if isinstance(item, dict) and item.get("reason"):
            return str(item.get("reason"))
    return "Energy Brain bewaakt live meetdata en houdt de veilige modus actief."


def render_powerflow_hero(section: dict[str, Any]) -> str:
    solar = section.get("solar_kw")
    house = section.get("house_kw")
    battery = section.get("battery_kw")
    grid = section.get("grid_kw")
    soc = section.get("soc_percent")
    battery_flow = flow_class(battery, "charging", "discharging")
    grid_flow = flow_class(grid, "importing", "exporting")
    solar_intensity = power_intensity(solar)
    house_intensity = power_intensity(house)
    battery_intensity = power_intensity(battery)
    grid_intensity = power_intensity(grid)
    return f"""
    <section class="hero powerflow-hero" aria-label="Realtime energiestromen">
      <div class="hero-head">
        <div>
          <div class="eyebrow">Realtime energiestroom</div>
          <div class="decision">{esc(section.get("decision", "Wachten"))}</div>
        </div>
        <div class="soc">
          <span class="eyebrow">Batterij</span>
          <strong>{esc(section.get("soc_label") or format_percent(soc))}</strong>
        </div>
      </div>
      <div class="flow-map" data-grid-flow="{esc(grid_flow)}" data-battery-flow="{esc(battery_flow)}">
        <svg class="flow-svg" viewBox="0 0 420 420" role="img" aria-label="Zon, huis, batterij en netstroom">
          <defs>
            <linearGradient id="solar-flow" x1="0" x2="1">
              <stop offset="0%" stop-color="#ffd166"/>
              <stop offset="100%" stop-color="#58e8b6"/>
            </linearGradient>
            <linearGradient id="grid-flow" x1="0" x2="1">
              <stop offset="0%" stop-color="#7fc7ff"/>
              <stop offset="100%" stop-color="#c792ff"/>
            </linearGradient>
            <linearGradient id="import-flow" x1="0" x2="1">
              <stop offset="0%" stop-color="#ff8b5f"/>
              <stop offset="100%" stop-color="#ffcf70"/>
            </linearGradient>
            <linearGradient id="export-flow" x1="0" x2="1">
              <stop offset="0%" stop-color="#ffd166"/>
              <stop offset="100%" stop-color="#fff1a8"/>
            </linearGradient>
          </defs>
          <path class="flow-lane lane-solar {flow_class(solar)}" style="--flow:{solar_intensity}" d="M210 66 C210 134 210 145 210 184" />
          <path class="flow-lane lane-home {flow_class(house)}" style="--flow:{house_intensity}" d="M236 210 C286 210 304 210 352 210" />
          <path class="flow-lane lane-battery {battery_flow}" style="--flow:{battery_intensity}" d="M184 210 C132 210 116 210 68 210" />
          <path class="flow-lane lane-grid {grid_flow}" style="--flow:{grid_intensity}" d="M210 236 C210 286 210 304 210 352" />
          <path class="flow-pulse pulse-solar {flow_class(solar)}" style="--flow:{solar_intensity}" d="M210 66 C210 134 210 145 210 184" />
          <path class="flow-pulse pulse-home {flow_class(house)}" style="--flow:{house_intensity}" d="M236 210 C286 210 304 210 352 210" />
          <path class="flow-pulse pulse-battery {battery_flow}" style="--flow:{battery_intensity}" d="M184 210 C132 210 116 210 68 210" />
          <path class="flow-pulse pulse-grid {grid_flow}" style="--flow:{grid_intensity}" d="M210 236 C210 286 210 304 210 352" />
        </svg>
        <div class="orb" style="--soc: {esc(soc or 0)}">
          <div class="orb-ring"></div>
          <div class="reserve-band"></div>
          <div class="orb-core">
            <span>Lading</span>
            <b>{esc(section.get("soc_label") or format_percent(soc))}</b>
            <em>{format_price(section.get("price"))}</em>
          </div>
        </div>
        <span class="particle particle-a"></span>
        <span class="particle particle-b"></span>
        <span class="particle particle-c"></span>
        <span class="particle particle-d"></span>
        <div class="node node-solar {_node_state(section, "solar_known")}"><span>Zon</span><b>{display_label(section, "solar_label", "solar_kw")}</b></div>
        <div class="node node-home {_node_state(section, "house_known")}"><span>Huis</span><b>{display_label(section, "house_label", "house_kw")}</b></div>
        <div class="node node-battery {esc(battery_flow)} {_node_state(section, "battery_known")}"><span>{_flow_label(battery_flow)}</span><b>{display_label(section, "battery_label", "battery_kw")}</b></div>
        <div class="node node-grid {esc(grid_flow)} {_node_state(section, "grid_known")}"><span>{_flow_label(grid_flow)}</span><b>{display_label(section, "grid_label", "grid_kw")}</b></div>
      </div>
      <div class="hero-foot">
        <span class="chip">{esc(section.get("status", "Observer actief"))}</span>
        {quality_note(section)}
        <span class="eyebrow">{esc(section.get("updated", "laatste cyclus"))}</span>
      </div>
    </section>
    """


def render_planner_summary(section: dict[str, Any]) -> str:
    entries = section.get("entries") if isinstance(section.get("entries"), list) else []
    blocks = "".join(
        f"""
        <div class="timeline-block tone-{esc(item.get("tone", "hold"))}" style="--span:{esc(item.get("width", "16"))}">
          <span>{esc(item.get("time", "nu"))}</span>
          <b>{esc(item.get("action", "hold"))}</b>
        </div>
        """
        for item in entries
        if isinstance(item, dict)
    )
    items = "".join(
        f"""
        <details class="reason-item">
          <summary>{esc(item.get("reason", ""))}</summary>
          <p>{esc(item.get("action", "Vasthouden"))} om {esc(item.get("time", "nu"))}</p>
        </details>
        """
        for item in entries[:3]
        if isinstance(item, dict)
    )
    return f"""
    <section class="panel strategy-panel planner" aria-label="Slimme strategie">
      <div class="panel-head">
        <span class="eyebrow">Wat denkt Energy Brain nu?</span>
        <span class="status-dot"></span>
      </div>
      <h2>{esc(section.get("headline", "Batterij vasthouden tot omstandigheden verbeteren"))}</h2>
      <p class="strategy-why">{esc(_primary_reason(entries))}</p>
      <div class="strategy-metrics">
        <div><span>Zekerheid</span><b>{esc(section.get("confidence", "gemiddeld"))}</b></div>
        <div><span>Verwachte besparing</span><b>{esc(section.get("expected_savings", "berekenen"))}</b></div>
        <div><span>Volgende verwachting</span><b>{esc(section.get("next_action_time", "volgende cyclus"))}</b></div>
      </div>
      <div class="horizon" aria-label="24-uurs planning">
        <div class="horizon-head"><span>Komende uren</span><b>Batterij · prijs · strategie</b></div>
        <div class="horizon-grid">{_timeline_horizon(entries)}</div>
        <div class="horizon-legend">
          <span class="tone-charge">Laden</span><span class="tone-discharge">Ontladen</span><span class="tone-cheap">Goedkoop</span><span class="tone-expensive">Duur</span><span>Reserveband</span>
        </div>
      </div>
      <div class="timeline" aria-label="Planningslijn">{blocks}</div>
      <div class="plan-list">{items}</div>
      <div class="metric-row"><span>Aansturing</span><b>{esc(section.get("execution", "Geen aansturing"))}</b></div>
    </section>
    """


def render_battery_panel(section: dict[str, Any]) -> str:
    soc = section.get("soc_percent", 0)
    soc_label = section.get("soc_label", "onbekend")
    flow = flow_class(section.get("battery_kw"), "charging", "discharging")
    flow_text = _flow_label(flow)
    return f"""
    <section class="panel battery-panel" aria-label="Batterijstatus">
      <div class="panel-head">
        <span class="eyebrow">Batterijstatus</span>
        <span class="battery-mode {esc(flow)}">{esc(flow_text)}</span>
      </div>
      <div class="battery-visual" style="--soc:{esc(soc or 0)}">
        <div class="battery-shell"><span></span></div>
        <div>
          <strong>{esc(soc_label)}</strong>
          <p>{display_label(section, "battery_label", "battery_kw")} huidig vermogen</p>
        </div>
      </div>
      <div class="battery-meta">
        <span>Reserve beschermd</span>
        <span>{esc(section.get("updated", "laatste cyclus"))}</span>
      </div>
    </section>
    """


def render_explainability_panel(section: dict[str, Any]) -> str:
    reasons = section.get("reasons") if isinstance(section.get("reasons"), list) else []
    body = "".join(f"<p>{esc(reason)}</p>" for reason in reasons[:3] if reason)
    if not body:
        body = "<p>Geen extra uitleg beschikbaar voor deze cyclus.</p>"
    return f"""
    <section class="panel explain-panel" aria-label="Uitleg">
      <h2>{esc(section.get("title", "Waarom"))}</h2>
      <div class="reason-stack compact-reasons">{body}</div>
    </section>
    """


def render_safety_panel(section: dict[str, Any]) -> str:
    rows = [
        ("Status", section.get("observer_state", "Observer actief")),
        ("Prognose", section.get("forecast_valid", "Prognose geldig")),
        ("Reserve", section.get("reserve_status", "Reserve beschermd")),
        ("Aansturing", "beveiligd"),
        ("Update", section.get("last_update", "laatste cyclus")),
    ]
    row_html = "".join(
        f'<div class="health-pill"><span>{esc(label)}</span><b>{esc(value)}</b></div>'
        for label, value in rows
    )
    return f"""
    <section class="panel health-panel" aria-label="Systeemstatus">
      <h2>{esc(section.get("title", "Systeemstatus"))}</h2>
      <div class="health-row">{row_html}</div>
      <p>{esc(section.get("blocked_reason", "Aansturing beveiligd. Deze cockpit is alleen-lezen."))}</p>
    </section>
    """


def render_health_strip(section: dict[str, Any]) -> str:
    rows = [
        ("Actueel", "Realtime"),
        ("Observer", section.get("observer_state", "Observer actief")),
        ("Markt", section.get("market_status", "Marktdata bewaakt")),
        ("Zon", section.get("forecast_valid", "Voorspelling actief")),
        ("Planning", section.get("planner_status", "Plan actief")),
        ("Reserve", section.get("reserve_status", "Reserve beschermd")),
        ("Update", section.get("last_update", "laatste cyclus")),
    ]
    row_html = "".join(
        f'<div class="health-strip-item"><i></i><span>{esc(label)}</span><b>{esc(value)}</b></div>'
        for label, value in rows
    )
    return f'<section class="health-strip" aria-label="Permanente systeemstatus">{row_html}</section>'
