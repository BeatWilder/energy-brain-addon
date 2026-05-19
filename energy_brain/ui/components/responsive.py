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
        return f'<span class="quality-chip">Some telemetry unavailable: {esc(", ".join(str(item) for item in unknown[:3]))}</span>'
    if clamped:
        return f'<span class="quality-chip">Display capped for safety: {esc(", ".join(str(item) for item in clamped[:3]))}</span>'
    return '<span class="quality-chip quality-live">Live telemetry</span>'


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
    <section class="hero powerflow-hero" aria-label="Live energy powerflow">
      <div class="hero-head">
        <div>
          <div class="eyebrow">Live Powerflow</div>
          <div class="decision">{esc(section.get("decision", "Wachten"))}</div>
        </div>
        <div class="soc">
          <span class="eyebrow">Battery</span>
          <strong>{esc(section.get("soc_label") or format_percent(soc))}</strong>
        </div>
      </div>
      <div class="flow-map" data-grid-flow="{esc(grid_flow)}" data-battery-flow="{esc(battery_flow)}">
        <svg class="flow-svg" viewBox="0 0 420 420" role="img" aria-label="Solar, home, battery and grid flow">
          <defs>
            <linearGradient id="solar-flow" x1="0" x2="1">
              <stop offset="0%" stop-color="#ffd166"/>
              <stop offset="100%" stop-color="#58e8b6"/>
            </linearGradient>
            <linearGradient id="grid-flow" x1="0" x2="1">
              <stop offset="0%" stop-color="#7fc7ff"/>
              <stop offset="100%" stop-color="#c792ff"/>
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
          <div class="orb-core">
            <span>State of charge</span>
            <b>{esc(section.get("soc_label") or format_percent(soc))}</b>
            <em>{format_price(section.get("price"))}</em>
          </div>
        </div>
        <div class="node node-solar"><span>Solar</span><b>{display_label(section, "solar_label", "solar_kw")}</b></div>
        <div class="node node-home"><span>Home</span><b>{display_label(section, "house_label", "house_kw")}</b></div>
        <div class="node node-battery {esc(battery_flow)}"><span>Battery</span><b>{display_label(section, "battery_label", "battery_kw")}</b></div>
        <div class="node node-grid {esc(grid_flow)}"><span>{'Export' if grid_flow == 'exporting' else 'Grid'}</span><b>{display_label(section, "grid_label", "grid_kw")}</b></div>
      </div>
      <div class="hero-foot">
        <span class="chip">{esc(section.get("status", "Observer"))}</span>
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
          <p>{esc(item.get("action", "hold"))} at {esc(item.get("time", "nu"))}</p>
        </details>
        """
        for item in entries[:3]
        if isinstance(item, dict)
    )
    return f"""
    <section class="panel strategy-panel planner" aria-label="Now and next strategy">
      <div class="panel-head">
        <span class="eyebrow">{esc(section.get("title", "Now / next"))}</span>
        <span class="status-dot"></span>
      </div>
      <h2>{esc(section.get("headline", "Holding battery until conditions improve"))}</h2>
      <div class="strategy-metrics">
        <div><span>Confidence</span><b>{esc(section.get("confidence", "medium"))}</b></div>
        <div><span>Expected savings</span><b>{esc(section.get("expected_savings", "calculating"))}</b></div>
        <div><span>Next action</span><b>{esc(section.get("next_action_time", "next cycle"))}</b></div>
      </div>
      <div class="timeline" aria-label="Planner timeline">{blocks}</div>
      <div class="plan-list">{items}</div>
      <div class="metric-row"><span>Execution</span><b>{esc(section.get("execution", "Geen aansturing"))}</b></div>
    </section>
    """


def render_explainability_panel(section: dict[str, Any]) -> str:
    reasons = section.get("reasons") if isinstance(section.get("reasons"), list) else []
    body = "".join(f"<p>{esc(reason)}</p>" for reason in reasons[:3] if reason)
    if not body:
        body = "<p>Geen extra uitleg beschikbaar voor deze cyclus.</p>"
    return f"""
    <section class="panel explain-panel" aria-label="Explainability">
      <h2>{esc(section.get("title", "Waarom"))}</h2>
      <div class="reason-stack">{body}</div>
    </section>
    """


def render_safety_panel(section: dict[str, Any]) -> str:
    rows = [
        ("Observer", section.get("observer_state", "observer/shadow")),
        ("Forecast", section.get("forecast_valid", "valid")),
        ("Safety", section.get("reserve_status", "reserve protected")),
        ("Writes", "blocked"),
        ("Updated", section.get("last_update", "latest cycle")),
    ]
    row_html = "".join(
        f'<div class="health-pill"><span>{esc(label)}</span><b>{esc(value)}</b></div>'
        for label, value in rows
    )
    return f"""
    <section class="panel health-panel" aria-label="System health">
      <h2>{esc(section.get("title", "Safety"))}</h2>
      <div class="health-row">{row_html}</div>
      <p>{esc(section.get("blocked_reason", "UI is read-only."))}</p>
    </section>
    """


def render_health_strip(section: dict[str, Any]) -> str:
    rows = [
        ("Mode", section.get("observer_state", "observer/shadow")),
        ("Forecast", section.get("forecast_valid", "valid")),
        ("Safety", section.get("reserve_status", "reserve protected")),
        ("Writes", "protected"),
        ("Updated", section.get("last_update", "latest cycle")),
    ]
    row_html = "".join(
        f'<div class="health-strip-item"><span>{esc(label)}</span><b>{esc(value)}</b></div>'
        for label, value in rows
    )
    return f'<section class="health-strip" aria-label="Persistent system health">{row_html}</section>'
