from __future__ import annotations

import html
from typing import Any

from energy_brain.ui.powerflow import build_powerflow_scene
from energy_brain.ui.powerflow_v2.renderer import render_powerflow_v2


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
        return "Stand-by"
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
        "discharging": "Voedt huis",
        "importing": "Import",
        "exporting": "Export",
        "transferring": "Actief",
        "active": "Actief",
        "reverse": "Terug",
        "idle": "Stand-by",
    }.get(flow, "Stand-by")


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
            f'<animateMotion dur="{esc(speed)}" begin="{delay:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.58;1" keySplines="0.22 0.66 0.30 1;0.18 0 0.28 1"{reverse_attrs}>'
            f'<mpath href="#{esc(lane.get("path_id"))}"/></animateMotion>'
            f'<animate attributeName="r" dur="{esc(speed)}" begin="{delay:.2f}s" values="1.8;4.2;3.0;0.6" keyTimes="0;0.22;0.74;1" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" dur="{esc(speed)}" begin="{delay:.2f}s" values="0;0.62;0.42;0" keyTimes="0;0.20;0.74;1" repeatCount="indefinite"/></circle>'
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
    return ""


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
    semantic = section.get("semantic_state") if isinstance(section.get("semantic_state"), dict) else {}
    for key in ("battery_strategy", "reserve_state"):
        value = semantic.get(key) or section.get(key)
        if value and value != "onbekend":
            intents.append(str(value))
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
    return intents[:1]


def _grid_micro_label(section: dict[str, Any]) -> str:
    if section.get("grid_known") is False:
        return ""
    grid = _num(section.get("grid_kw")) or 0.0
    power = format_kw(abs(grid))
    if grid > 0.05:
        return f"Import {power}"
    if grid < -0.05:
        return f"Export {power}"
    return "Geen netverbruik"


def _battery_micro_label(section: dict[str, Any], battery_flow: str) -> str:
    if section.get("battery_known") is False:
        return ""
    battery = _num(section.get("battery_kw")) or 0.0
    power = format_kw(abs(battery))
    if battery_flow == "charging":
        return f"Laden {power}"
    if battery_flow == "discharging":
        return f"Levert {power}"
    return "Stand-by"


def _micro_telemetry(section: dict[str, Any]) -> str:
    items = [
        ("PV", visible_power_label(section, "solar_known", "solar_label", "solar_kw")),
        ("Huis", visible_power_label(section, "house_known", "house_label", "house_kw")),
        ("Net", _grid_micro_label(section)),
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
    soc_number = _num(section.get("soc_percent"))
    abundance = "scarcity" if soc_number is not None and float(section.get("soc_percent") or 0) <= 25 else "abundance"
    price_number = _num(section.get("price"))
    price_state = "cheap" if price_number is not None and price_number <= 0.08 else "expensive" if price_number is not None and price_number >= 0.32 else "balanced"
    return render_powerflow_v2(
        grid_flow=grid_flow,
        battery_flow=battery_flow,
        solar_label=visible_power_label(section, "solar_known", "solar_label", "solar_kw") or "Stand-by",
        home_label=visible_power_label(section, "house_known", "house_label", "house_kw") or "Stand-by",
        grid_label=_grid_micro_label(section) or "Stand-by",
        battery_label=_battery_micro_label(section, battery_flow) or "Stand-by",
        soc_label=soc_label,
    )

    # old renderer disabled

    return f"""
    <section class="hero powerflow-hero living-scene" aria-label="Realtime energiestromen" data-legacy-label="Realtime energiestroom" data-energy-state="{esc(abundance)}" data-price-state="{esc(price_state)}">
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
          <circle cx="145" cy="145" r="3" fill="rgba(255,255,255,.75)" />
          <circle cx="275" cy="170" r="3" fill="rgba(255,255,255,.75)" />
          <circle cx="240" cy="300" r="3" fill="rgba(255,255,255,.75)" />
          <circle cx="110" cy="255" r="3" fill="rgba(255,255,255,.75)" />

          <g class="flow-particles" aria-hidden="true">
            {_render_particles(scene)}
          </g>
        </svg>
        <div class="orb" style="--soc: {esc(soc or 0)}; --scene-intensity:{esc(scene["scene_intensity"])}">
          <div class="orb-ring"></div>
          <div class="orb-soc-ring"></div>
          <div class="reserve-band"></div>
          <div class="orb-core">
            <span>Batterij</span>
            <b>{soc_label}</b>
            <em>{visible_power_label(section, "battery_known", "battery_label", "battery_kw") or esc(_flow_label(battery_flow))}</em>
          </div>
        </div>
        <div class="node node-solar state-{esc(nodes["solar"]["state"])} {_node_state(section, "solar_known")}" style="{_node_vars(nodes["solar"])}"><i></i><span>Zon</span><b>{visible_power_label(section, "solar_known", "solar_label", "solar_kw")}</b></div>
        <div class="node node-home state-{esc(nodes["home"]["state"])} {_node_state(section, "house_known")}" style="{_node_vars(nodes["home"])}"><i></i><span>Huis</span><b>{visible_power_label(section, "house_known", "house_label", "house_kw")}</b></div>
        <div class="node node-grid state-{esc(grid_flow)} {_node_state(section, "grid_known")}" style="{_node_vars(nodes["grid"])}"><i></i><span>Net</span><b>{visible_power_label(section, "grid_known", "grid_label", "grid_kw")}</b></div>

        <div class="node node-battery state-{esc(battery_flow)} {_node_state(section, "battery_known")}" style="{_node_vars(nodes["battery"])}"><i></i><span>Batterij</span><b>{visible_power_label(section, "battery_known", "battery_label", "battery_kw")}</b></div>      </div>
      <div class="hero-foot">
        <ul class="intent-orbit" aria-label="Actuele energie-intentie">{intents}</ul>
        <div class="micro-telemetry" aria-label="Microtelemetrie">{telemetry}{quality_note(section)}</div>
      </div>
    </section>
    """


def render_planner_summary(section: dict[str, Any]) -> str:
    entries = section.get("entries") if isinstance(section.get("entries"), list) else []
    reserve_state = section.get("reserve_state", "Reserve onbekend")
    solar_state = section.get("solar_state", "Niet beschikbaar")
    grid_dependency = section.get("grid_dependency", "Niet beschikbaar")
    if solar_state == "onbekend":
        solar_state = "Niet beschikbaar"
    if grid_dependency == "onbekend":
        grid_dependency = "Niet beschikbaar"
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
    <section class="panel strategy-panel planner ambient-panel intelligence-strip" aria-label="Slimme strategie">
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
      <div class="semantic-grid" aria-label="Semantische EMS-status">
        <span><b>Reserve</b>{esc(reserve_state)}</span>
        <span><b>Zon</b>{esc(solar_state)}</span>
        <span><b>Net</b>{esc(grid_dependency)}</span>
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


def _state_row(label: str, value: Any) -> str:
    display = "Niet beschikbaar" if value in (None, "", "onbekend") else value
    return f'<div class="comfort-row"><span>{esc(label)}</span><b>{esc(display)}</b></div>'


def _climate_attr(climate: Any, key: str) -> Any:
    if not isinstance(climate, dict):
        return None
    attrs = climate.get("attributes")
    if isinstance(attrs, dict):
        return attrs.get(key)
    return None


def _temp_label(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "—"
    return f"{number:.1f}°"


def _thermostat_preview(title: str, entity_id: str, climate: Any) -> str:
    state = climate.get("state") if isinstance(climate, dict) else None
    current = _climate_attr(climate, "current_temperature")
    target = _climate_attr(climate, "temperature")
    hvac_action = _climate_attr(climate, "hvac_action") or state
    current_number = _num(current)
    target_number = _num(target)
    ring = 0 if current_number is None else max(0, min(100, (current_number - 5) / 25 * 100))
    disabled = target_number is None
    disabled_attr = " disabled aria-disabled=\"true\"" if disabled else ""
    disabled_class = " disabled" if disabled else ""
    target_value = "" if target_number is None else f"{target_number:.1f}"
    hvac_label = "Stand-by" if hvac_action in (None, "", "unknown", "unavailable", "onbekend") else hvac_action
    return f"""
      <article class="thermostat-preview{disabled_class}" aria-label="{esc(title)} thermostaat preview" data-thermostat-card data-entity-id="{esc(entity_id)}" data-target-temperature="{esc(target_value)}">
        <div class="thermostat-top">
          <span>{esc(title)}</span>
          <b>{esc(hvac_label)}</b>
        </div>
        <div class="thermostat-dial" style="--temp-ring:{ring:.1f}">
          <div>
            <strong>{esc(_temp_label(current))}</strong>
            <span>Doel <b data-thermostat-target>{esc(_temp_label(target))}</b></span>
            <em>Comfort zone</em>
          </div>
        </div>
        <div class="thermostat-controls" aria-label="{esc(title)} temperatuur aanpassen">
          <button type="button" data-thermostat-step="-0.5" aria-label="{esc(title)} doeltemperatuur lager"{disabled_attr}>−</button>
          <button type="button" data-thermostat-step="0.5" aria-label="{esc(title)} doeltemperatuur hoger"{disabled_attr}>+</button>
        </div>
        <div class="thermostat-feedback" data-thermostat-feedback>{esc(entity_id)}</div>
      </article>
    """


def _thermostat_runtime_script() -> str:
    return """
      <script>
        (function () {
          const cards = document.querySelectorAll("[data-thermostat-card]");
          if (!cards.length || !window.fetch) {
            return;
          }

          function setFeedback(card, text, state) {
            const feedback = card.querySelector("[data-thermostat-feedback]");
            if (!feedback) return;
            feedback.textContent = text;
            feedback.dataset.state = state || "";
          }

          function formatTemp(value) {
            return value.toFixed(1) + "°";
          }

          cards.forEach((card) => {
            const buttons = card.querySelectorAll("[data-thermostat-step]");
            const target = card.querySelector("[data-thermostat-target]");
            buttons.forEach((button) => {
              button.addEventListener("click", async () => {
                if (button.disabled || card.classList.contains("is-pending")) {
                  return;
                }

                const entityId = card.dataset.entityId || "";
                const delta = Number(button.dataset.thermostatStep || 0);
                const currentTarget = Number(card.dataset.targetTemperature || NaN);
                if (!entityId || !Number.isFinite(delta) || !Number.isFinite(currentTarget)) {
                  setFeedback(card, "Bediening niet beschikbaar", "blocked");
                  return;
                }

                const nextTarget = Math.round((currentTarget + delta) * 10) / 10;
                const previousText = target ? target.textContent : "";
                card.classList.add("is-pending");
                buttons.forEach((item) => item.disabled = true);
                if (target) target.textContent = formatTemp(nextTarget);
                setFeedback(card, "Aanpassen...", "pending");

                try {
                  const response = await fetch("api/climate/temperature", {
                    method: "POST",
                    body: new URLSearchParams({entity_id: entityId, delta: String(delta)}),
                    headers: {
                      "Accept": "application/json",
                      "Content-Type": "application/x-www-form-urlencoded"
                    }
                  });
                  const result = await response.json();
                  if (!response.ok || !result.ok) {
                    if (target) target.textContent = previousText;
                    setFeedback(card, "Geblokkeerd", "blocked");
                    return;
                  }
                  const confirmed = Number(result.temperature);
                  if (Number.isFinite(confirmed)) {
                    card.dataset.targetTemperature = confirmed.toFixed(1);
                    if (target) target.textContent = formatTemp(confirmed);
                  }
                  setFeedback(card, "Opgeslagen", "ok");
                } catch (error) {
                  if (target) target.textContent = previousText;
                  setFeedback(card, "Geen verbinding", "blocked");
                } finally {
                  card.classList.remove("is-pending");
                  buttons.forEach((item) => item.disabled = false);
                }
              });
            });
          });
        })();
      </script>
    """


def render_comfort_panel(section: dict[str, Any]) -> str:
    thermostats = (
        _thermostat_preview("Woonkamer", "climate.ir_woonkamer", section.get("living_climate"))
        + _thermostat_preview("Keuken", "climate.w100_keuken", section.get("kitchen_climate"))
    )
    rows = "".join(
        [
            _state_row("Woonkamer", section.get("living_state")),
            _state_row("Keuken", section.get("kitchen_state")),
            _state_row("Aanwezig woonkamer", section.get("presence_living")),
            _state_row("Aanwezig keuken", section.get("presence_kitchen")),
            _state_row("Override woonkamer", section.get("override_living")),
            _state_row("Override keuken", section.get("override_kitchen")),
        ]
    )
    comfort_mode = section.get("comfort_mode", "Comfort niet beschikbaar")
    thermal_strategy = section.get("thermal_strategy", "Thermiek niet beschikbaar")
    if comfort_mode == "Comfort onbekend":
        comfort_mode = "Comfort niet beschikbaar"
    if thermal_strategy == "Thermiek onbekend":
        thermal_strategy = "Thermiek niet beschikbaar"
    return f"""
    <section class="panel comfort-panel ambient-panel" aria-label="Comfort Intelligence">
      <div class="panel-head">
        <span class="eyebrow">Comfort Intelligence</span>
        <span class="thermal-chip">{esc(section.get("heating_allowed") if section.get("heating_allowed") != "onbekend" else "Niet beschikbaar")}</span>
      </div>
      <h2>{esc(comfort_mode)}</h2>
      <p>{esc(thermal_strategy)}</p>
      <div class="thermostat-grid">{thermostats}</div>
      <div class="comfort-grid">{rows}</div>
    </section>
    {_thermostat_runtime_script()}
    """


def render_living_controls(section: dict[str, Any]) -> str:
    rows = [
        ("Dispatch", section.get("dispatch_state", "Dispatch onbekend")),
        ("Modus", section.get("dispatch_mode", "Niet beschikbaar")),
        ("Vermogen", section.get("dispatch_power", "Niet beschikbaar")),
        ("Duur", section.get("dispatch_duration", "Niet beschikbaar")),
        ("Cutoff SOC", section.get("dispatch_cutoff_soc", "Niet beschikbaar")),
        ("Schrijven", "Alleen-lezen"),
    ]
    row_html = "".join(
        f'<div class="control-row"><span>{esc(label)}</span><b>{esc("Niet beschikbaar" if value == "onbekend" else value)}</b></div>'
        for label, value in rows
    )
    return f"""
    <section class="panel controls-panel ambient-panel" aria-label="Living Controls">
      <div class="panel-head">
        <span class="eyebrow">Living Controls</span>
        <span class="thermal-chip">observer</span>
      </div>
      <h2>Handmatige laag beveiligd</h2>
      <div class="control-grid">{row_html}</div>
    </section>
    """


def render_battery_panel(section: dict[str, Any]) -> str:
    soc = section.get("soc_percent", 0)
    soc_label = section.get("soc_label") if section.get("soc_label") != "onbekend" else "Stand-by"
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
        ("Prognose", section.get("forecast_valid", "Prognose geldig")),
        ("Reserve", section.get("reserve_status", "Reserve beschermd")),
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
          <span>Bewaking<b>{esc(section.get("observer_state", "Actief bewaakt"))}</b></span>
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
        ("Reserve", section.get("reserve_status", "Reserve beschermd")),
        ("Strategie", section.get("planner_status", "Actief")),
        ("Update", section.get("last_update", "laatste cyclus")),
    ]
    row_html = "".join(
        f'<div class="health-strip-item"><i></i><span>{esc(label)}</span><b>{esc(value)}</b></div>'
        for label, value in rows
    )
    return f'<section class="health-strip energy-state-island" aria-label="Permanente systeemstatus">{row_html}</section>'
