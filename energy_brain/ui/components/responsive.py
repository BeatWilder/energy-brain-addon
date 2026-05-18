from __future__ import annotations

import html
from typing import Any


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def format_kw(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:.1f} kW"


def format_percent(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:.0f}%"


def render_powerflow_hero(section: dict[str, Any]) -> str:
    return f"""
    <section class="hero" aria-label="Powerflow">
      <div class="hero-head">
        <div>
          <div class="eyebrow">Powerflow</div>
          <div class="decision">{esc(section.get("decision", "Wachten"))}</div>
        </div>
        <div class="soc">
          <span class="eyebrow">Battery</span>
          <strong>{format_percent(section.get("soc_percent"))}</strong>
        </div>
      </div>
      <div class="flow">
        <div class="rail"></div>
        <div class="rail vertical"></div>
        <div class="node solar"><b>{format_kw(section.get("solar_kw"))}</b><span>Solar</span></div>
        <div class="node house"><b>{format_kw(section.get("house_kw"))}</b><span>Home</span></div>
        <div class="node battery"><b>{format_kw(section.get("battery_kw"))}</b><span>Battery</span></div>
        <div class="node grid"><b>{format_kw(section.get("grid_kw"))}</b><span>Grid</span></div>
        <div class="core"><div><span>Price</span><b>{esc(section.get("price", 0.0))}</b></div></div>
      </div>
      <div class="hero-foot">
        <span class="chip">{esc(section.get("status", "Observer"))}</span>
        <span class="eyebrow">{esc(section.get("updated", "laatste cyclus"))}</span>
      </div>
    </section>
    """


def render_planner_summary(section: dict[str, Any]) -> str:
    entries = section.get("entries") if isinstance(section.get("entries"), list) else []
    items = "".join(
        f"""
        <div class="plan-item">
          <div class="plan-time">{esc(item.get("time", "nu"))}</div>
          <div class="plan-action">{esc(item.get("action", "hold"))}</div>
          <p>{esc(item.get("reason", ""))}</p>
        </div>
        """
        for item in entries
        if isinstance(item, dict)
    )
    return f"""
    <section class="panel planner" aria-label="Planner summary">
      <h2>{esc(section.get("title", "Planner"))}</h2>
      <div class="metric-row"><span>Mode</span><b>{esc(section.get("mode", "observer"))}</b></div>
      <div class="metric-row"><span>Execution</span><b>{esc(section.get("execution", "Geen aansturing"))}</b></div>
      <div class="plan-list">{items}</div>
    </section>
    """


def render_explainability_panel(section: dict[str, Any]) -> str:
    reasons = section.get("reasons") if isinstance(section.get("reasons"), list) else []
    body = "".join(f"<p>{esc(reason)}</p>" for reason in reasons[:3] if reason)
    if not body:
        body = "<p>Geen extra uitleg beschikbaar voor deze cyclus.</p>"
    return f"""
    <section class="panel" aria-label="Explainability">
      <h2>{esc(section.get("title", "Waarom"))}</h2>
      {body}
    </section>
    """


def render_safety_panel(section: dict[str, Any]) -> str:
    return f"""
    <section class="panel" aria-label="Safety">
      <h2>{esc(section.get("title", "Safety"))}</h2>
      <div class="metric-row"><span>Reserve</span><b>{esc(section.get("reserve_status", "onbekend"))}</b></div>
      <div class="metric-row"><span>Faults</span><b>{esc(section.get("fault_status", "geen bekende melding"))}</b></div>
      <div class="metric-row"><span>Writes</span><b>Blocked</b></div>
      <p>{esc(section.get("blocked_reason", "UI is read-only."))}</p>
    </section>
    """

