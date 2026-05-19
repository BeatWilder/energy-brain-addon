from __future__ import annotations

import html
from typing import Any

from energy_brain.ui.powerflow import build_powerflow_scene


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
    if isinstance(label, str) and label and label != "onbekend":
        return esc(label)
    return esc(format_kw(section.get(value_key)))


def visible_power_label(section: dict[str, Any], known_key: str, label_key: str, value_key: str) -> str:
    if section.get(known_key) is False:
        return ""
    return display_label(section, label_key, value_key)


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


def visible_soc_label(section: dict[str, Any]) -> str:
    label = section.get("soc_label")
    if section.get("soc_known") is False or label == "onbekend":
        return "Rust"
    return esc(label or format_percent(section.get("soc_percent")))


def format_price(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return esc(value or "—")
    return f"€{number:.3f}/kWh"


def _flow_label(flow: str) -> str:
    return {
        "charging": "Laden",
        "discharging": "Huis op batterij",
        "importing": "Import",
        "exporting": "Export",
        "transferring": "Actief",
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


def _css_vars(values: dict[str, Any]) -> str:
    return ";".join(f"--{esc(key)}:{esc(value)}" for key, value in values.items())


def _lane_vars(lane: dict[str, Any]) -> str:
    values = lane.get("vars") if isinstance(lane.get("vars"), dict) else {}
    return _css_vars(
        {
            "flow-intensity": values.get("intensity", "0"),
            "flow-speed": values.get("speed", "5.2s"),
            "particle-density": values.get("density", "0"),
            "energy-glow": values.get("glow", "0.14"),
            "lane-width": values.get("thickness", "5"),
        }
    )


def _node_vars(node: dict[str, Any]) -> str:
    return _css_vars(
        {
            "node-intensity": f'{float(node.get("intensity") or 0):.3f}',
            "node-ring": node.get("ring", "rgba(255,255,255,0.16)"),
            "soc": f'{float(node.get("soc") or 0):.1f}',
        }
    )


def _lane_particles(lane: dict[str, Any]) -> str:
    values = lane.get("vars") if isinstance(lane.get("vars"), dict) else {}
    density = int(values.get("density") or 0)
    if not lane.get("active") or density <= 0:
        return ""
    state = str(lane.get("state") or "idle")
    reverse_attrs = ""
    speed = str(values.get("speed", "5s"))
    try:
        seconds = float(speed.rstrip("s"))
    except ValueError:
        seconds = 5.0
    dots = []
    for index in range(density):
        delay = -(index * (seconds / density))
        dots.append(
            f'<circle class="flow-dot tone-{esc(lane.get("tone", "home"))} state-{esc(state)}" r="4.6" style="{_lane_vars(lane)}">'
            f'<animateMotion dur="{esc(speed)}" begin="{delay:.2f}s" repeatCount="indefinite"{reverse_attrs}>'
            f'<mpath href="#{esc(lane.get("path_id"))}"/></animateMotion>'
            f'<animate attributeName="opacity" dur="{esc(speed)}" begin="{delay:.2f}s" values="0;0.9;0.78;0" keyTimes="0;0.18;0.72;1" repeatCount="indefinite"/></circle>'
        )
    return "".join(dots)


def _render_lane_defs(scene: dict[str, Any]) -> str:
    return "".join(
        f'<path id="{esc(lane["path_id"])}" d="{esc(lane["path"])}" />'
        for lane in scene.get("lanes", [])
        if isinstance(lane, dict)
    )


def _render_lanes(scene: dict[str, Any], layer: str) -> str:
    class_name = "flow-lane" if layer == "backbone" else "flow-pulse"
    return "".join(
        f'<use href="#{esc(lane["path_id"])}" class="{class_name} tone-{esc(lane.get("tone", "home"))} state-{esc(lane.get("state", "idle"))}" style="{_lane_vars(lane)}" />'
        for lane in scene.get("lanes", [])
        if isinstance(lane, dict)
    )


def _render_particles(scene: dict[str, Any]) -> str:
    return "".join(
        _lane_particles(lane)
        for lane in scene.get("lanes", [])
        if isinstance(lane, dict)
    )


def quality_note(section: dict[str, Any]) -> str:
    quality = section.get("data_quality")
    if not isinstance(quality, dict):
        return ""
    unknown = quality.get("unknown") if isinstance(quality.get("unknown"), list) else []
    clamped = quality.get("clamped") if isinstance(quality.get("clamped"), list) else []
    if unknown:
        return '<span class="quality-chip quality-degraded" aria-label="Meetkwaliteit beperkt"><i></i>Beperkt</span>'
    if clamped:
        return '<span class="quality-chip quality-degraded" aria-label="Weergave begrensd"><i></i>Begrensd</span>'
    return '<span class="quality-chip quality-live"><i></i>Live</span>'


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


def _scene_intents(section: dict[str, Any], scene: dict[str, Any]) -> list[str]:
    intents: list[str] = []
    transfers = scene.get("transfers") if isinstance(scene.get("transfers"), dict) else {}
    if float(transfers.get("solar_battery") or 0) > 0.05:
        intents.append("Laden uit zon")
    if float(transfers.get("grid_battery") or 0) > 0.05:
        intents.append("Goedkope energie opnemen")
    if float(transfers.get("battery_house") or 0) > 0.05:
        intents.append("Huis draait op batterij")
    if float(transfers.get("solar_grid") or 0) > 0.05:
        intents.append("Overschot rustig exporteren")
    if float(section.get("soc_percent") or 0) <= 25:
        intents.append("Reserve beschermen")
    if not intents:
        intents.append(esc(section.get("decision", "Slim wachten")))
    intents.append("Volgende kans bewaken")
    return intents[:4]


def _micro_telemetry(section: dict[str, Any]) -> str:
    items = [
        ("PV", visible_power_label(section, "solar_known", "solar_label", "solar_kw")),
        ("Huis", visible_power_label(section, "house_known", "house_label", "house_kw")),
        ("Batterij", visible_power_label(section, "battery_known", "battery_label", "battery_kw")),
        ("Net", visible_power_label(section, "grid_known", "grid_label", "grid_kw")),
        ("Observer", esc(section.get("status", "actief"))),
    ]
    return "".join(
        f'<span class="telemetry-pill"><b>{label}</b>{value}</span>'
        for label, value in items
        if value
    )


def render_powerflow_hero(section: dict[str, Any]) -> str:
    soc = section.get("soc_percent")
    soc_label = visible_soc_label(section)
    scene = build_powerflow_scene(section)
    nodes = scene["nodes"]
    battery_flow = scene["battery_state"]
    grid_flow = scene["grid_state"]
    orb_state = scene.get("orb_state", "idle")
    intents = "".join(f"<li>{esc(intent)}</li>" for intent in _scene_intents(section, scene))
    telemetry = _micro_telemetry(section)
    abundance = "scarcity" if _num(section.get("soc_percent")) is not None and float(section.get("soc_percent") or 0) <= 25 else "abundance"
    return f"""
    <section class="hero powerflow-hero living-scene" aria-label="Realtime energiestromen" data-legacy-label="Realtime energiestroom" data-energy-state="{esc(abundance)}">
      <div class="hero-head">
        <div>
          <div class="eyebrow">Live energie-ecosysteem</div>
          <div class="decision">{esc(section.get("decision", "Wachten"))}</div>
        </div>
        <div class="soc">
          <span class="eyebrow">Batterij</span>
          <strong>{soc_label}</strong>
        </div>
      </div>
      <div class="flow-map" data-grid-flow="{esc(grid_flow)}" data-battery-flow="{esc(battery_flow)}" data-orb-state="{esc(orb_state)}" style="--scene-intensity:{esc(scene["scene_intensity"])}">
        <svg class="flow-svg" viewBox="0 0 420 420" role="img" aria-label="Zon, huis, batterij en netstroom">
          <defs>
            {_render_lane_defs(scene)}
            <radialGradient id="junction-glow">
              <stop offset="0%" stop-color="#f8fff9" stop-opacity="0.95"/>
              <stop offset="42%" stop-color="#65f0a7" stop-opacity="0.44"/>
              <stop offset="100%" stop-color="#65f0a7" stop-opacity="0"/>
            </radialGradient>
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
          <g class="flow-backbone">
            {_render_lanes(scene, "backbone")}
          </g>
          <g class="flow-ribbons">
            {_render_lanes(scene, "pulse")}
          </g>
          <circle class="junction-aura" cx="210" cy="210" r="52" />
          <circle class="junction-core" cx="210" cy="210" r="7" />
          <g class="flow-particles" aria-hidden="true">
            {_render_particles(scene)}
          </g>
        </svg>
        <div class="orb" style="--soc: {esc(soc or 0)}; --scene-intensity:{esc(scene["scene_intensity"])}">
          <div class="orb-ring"></div>
          <div class="orb-soc-ring"></div>
          <div class="reserve-band"></div>
          <div class="orb-core">
            <span>{esc(_flow_label(battery_flow))}</span>
            <b>{soc_label}</b>
            <em>{format_price(section.get("price"))}</em>
          </div>
        </div>
        <div class="node node-solar state-{esc(nodes["solar"]["state"])} {_node_state(section, "solar_known")}" style="{_node_vars(nodes["solar"])}"><i></i><span>Zon</span><b>{visible_power_label(section, "solar_known", "solar_label", "solar_kw")}</b></div>
        <div class="node node-home state-{esc(nodes["home"]["state"])} {_node_state(section, "house_known")}" style="{_node_vars(nodes["home"])}"><i></i><span>Huis</span><b>{visible_power_label(section, "house_known", "house_label", "house_kw")}</b></div>
        <div class="node node-battery state-{esc(battery_flow)} {_node_state(section, "battery_known")}" style="{_node_vars(nodes["battery"])}"><i></i><span>{_flow_label(battery_flow)}</span><b>{visible_power_label(section, "battery_known", "battery_label", "battery_kw")}</b></div>
        <div class="node node-grid state-{esc(grid_flow)} {_node_state(section, "grid_known")}" data-legacy-label="Teruglevering" style="{_node_vars(nodes["grid"])}"><i></i><span class="sr-only">Teruglevering</span><span>{_flow_label(grid_flow)}</span><b>{visible_power_label(section, "grid_known", "grid_label", "grid_kw")}</b></div>
      </div>
      <div class="hero-foot">
        <ul class="intent-orbit" aria-label="Actuele energie-intentie">{intents}</ul>
        <div class="micro-telemetry" aria-label="Microtelemetrie">{telemetry}{quality_note(section)}</div>
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
    <section class="panel strategy-panel planner ambient-panel" aria-label="Slimme strategie">
      <div class="panel-head">
        <span class="eyebrow">Live strategie</span>
        <span class="status-dot"></span>
      </div>
      <h2>{esc(section.get("headline", "Batterij vasthouden tot omstandigheden verbeteren"))}</h2>
      <p class="strategy-why">{esc(_primary_reason(entries))}</p>
      <div class="strategy-metrics">
        <div><span>Zekerheid</span><b>{esc(section.get("confidence", "gemiddeld"))}</b></div>
        <div><span>Verwachte besparing</span><b>{esc(section.get("expected_savings", "berekenen"))}</b></div>
        <div><span>Volgende verwachting</span><b>{esc(section.get("next_action_time", "volgende cyclus"))}</b></div>
      </div>
      <div class="horizon" aria-label="24-uurs planning" data-legacy-label="Komende uren">
        <div class="horizon-head"><span>Energy Brain ziet vooruit</span><b>lading · prijs · actie</b></div>
        <div class="horizon-grid">{_timeline_horizon(entries)}</div>
        <div class="horizon-legend">
          <span class="tone-charge">Laden</span><span class="tone-discharge">Huis voeden</span><span class="tone-cheap">Goedkoop</span><span class="tone-expensive">Duur</span><span>Reserve</span>
        </div>
      </div>
      <div class="timeline" aria-label="Planningslijn">{blocks}</div>
      <div class="plan-list">{items}</div>
      <div class="metric-row"><span>Aansturing</span><b>{esc(section.get("execution", "Geen aansturing"))}</b></div>
    </section>
    """


def render_battery_panel(section: dict[str, Any]) -> str:
    soc = section.get("soc_percent", 0)
    soc_label = section.get("soc_label") if section.get("soc_label") != "onbekend" else "Rust"
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
          <p>{visible_power_label(section, "battery_known", "battery_label", "battery_kw") or "Inactief"} huidig vermogen</p>
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
    body = "".join(f"<p>{esc(reason)}</p>" for reason in reasons[:4] if reason)
    if not body:
        body = "<p>Slim wachten</p>"
    return f"""
    <section class="panel explain-panel ambient-panel" aria-label="Tactisch bewustzijn" data-legacy-title="Waarom wacht Energy Brain?">
      <h2>{esc(section.get("title", "Tactisch bewustzijn"))}</h2>
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
    diagnostics = f"""
      <details class="diagnostic-overlay">
        <summary>Geavanceerde observerdiagnose</summary>
        <div class="diagnostic-grid">
          <span>SOC traject<b>{esc(section.get("reserve_status", "Reserve beschermd"))}</b></span>
          <span>Reservegrens<b>{esc(section.get("reserve_status", "Reserve beschermd"))}</b></span>
          <span>Prognosevertrouwen<b>{esc(section.get("forecast_valid", "Prognose geldig"))}</b></span>
          <span>Observermodus<b>{esc(section.get("observer_state", "Observer actief"))}</b></span>
          <span>Aansturing<b>{esc(section.get("blocked_reason", "Geblokkeerd"))}</b></span>
          <span>Actieve constraints<b>{esc(section.get("fault_status", "Geen storingen"))}</b></span>
        </div>
      </details>
    """
    return f"""
    <section class="panel health-panel" aria-label="Systeemstatus" data-legacy-status="Aansturing beveiligd">
      <h2>{esc(section.get("title", "Systeemstatus"))}</h2>
      <div class="health-row">{row_html}</div>
      <p>{esc(section.get("blocked_reason", "Aansturing beveiligd. Deze cockpit is alleen-lezen."))}</p>
      {diagnostics}
    </section>
    """


def render_health_strip(section: dict[str, Any]) -> str:
    rows = [
        ("Observer", section.get("observer_state", "Observer actief")),
        ("Reserve", section.get("reserve_status", "Reserve beschermd")),
        ("Planning", section.get("planner_status", "Plan actief")),
        ("Update", section.get("last_update", "laatste cyclus")),
    ]
    row_html = "".join(
        f'<div class="health-strip-item"><i></i><span>{esc(label)}</span><b>{esc(value)}</b></div>'
        for label, value in rows
    )
    return f'<section class="health-strip energy-state-island" aria-label="Permanente systeemstatus">{row_html}</section>'
