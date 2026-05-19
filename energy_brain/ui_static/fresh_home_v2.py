from __future__ import annotations

from html import escape
from typing import Any

from energy_brain.ui_static.powerflow_v2 import render_powerflow


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
            .replace("EUR/kWh", "")
            .replace("€/kWh", "")
            .replace("EUR", "")
            .replace("€", "")
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


def fmt_percent(value: Any) -> tuple[str, str]:
    number = num(value)
    if number is None:
        return "—", "%"
    return f"{number:.0f}", "%"


def fmt_price(value: Any) -> tuple[str, str]:
    number = num(value)
    if number is None:
        return "—", "EUR/kWh"
    return f"{number:.3f}".replace(".", ","), "EUR/kWh"


def fmt_temp(value: Any) -> str:
    number = num(value)
    if number is None:
        return "—"
    return f"{number:.1f}".replace(".", ",")


def text(value: Any, fallback: str = "—") -> str:
    if isinstance(value, dict):
        value = value.get("state", value.get("value"))
    if value in MISSING:
        return fallback
    return str(value)


def render_chip(label: str, tone: str = "neutral") -> str:
    return f'<span class="chip {escape(tone)}">{escape(label)}</span>'


def render_metric_card(label: str, value: str, unit: str, subtitle: str) -> str:
    unit_html = f'<span>{escape(unit)}</span>' if unit else ""
    return f'''
      <article class="metric-card">
        <p>{escape(label)}</p>
        <strong>{escape(value)}{unit_html}</strong>
        <small>{escape(subtitle)}</small>
      </article>
    '''


def _logo() -> str:
    return '''
      <svg class="logo" viewBox="0 0 64 64" aria-hidden="true">
        <circle cx="32" cy="32" r="25" fill="none" stroke="rgba(84,217,201,.26)" stroke-width="1.4"/>
        <path d="M30 14c-8 0-13 6-13 13-6 2-8 8-5 14 2 5 7 8 13 7h5V14Z"
          fill="none" stroke="#54d9c9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M34 14c8 0 13 6 13 13 6 2 8 8 5 14-2 5-7 8-13 7h-5V14Z"
          fill="none" stroke="#54d9c9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M24 25h-6M25 34h-9M24 42h-5M40 25h6M39 34h9M40 42h5"
          fill="none" stroke="#7bb8ff" stroke-width="2.1" stroke-linecap="round"/>
      </svg>
    '''


def _metrics(data: dict[str, Any]) -> str:
    soc, soc_unit = fmt_percent(safe_pick(data, "soc_percent", "battery_soc_percent", "soc", "battery_soc"))
    pv, pv_unit = fmt_power(safe_pick(data, "pv_power_kw", "pv_now_kw", "pv_power_w", "pv_power"))
    home, home_unit = fmt_power(safe_pick(data, "household_load_kw", "home_load_kw", "load_kw", "house_kw", "household_load_w"))
    grid, grid_unit = fmt_power(safe_pick(data, "grid_power_kw", "grid_kw", "net_kw", "grid_power_w", "grid_power"), signed=True)
    battery, battery_unit = fmt_power(
        safe_pick(data, "battery_power_kw", "battery_kw", "battery_power_w", "battery_charge_kw", "battery_discharge_kw"),
        signed=True,
    )
    price, price_unit = fmt_price(safe_pick(data, "price_now", "grid_price", "electricity_price"))
    reserve, reserve_unit = fmt_percent(safe_pick(data, "reserve_percent", "reserve", "battery.reserve_percent", "config.reserve_percent"))
    quality, quality_unit = fmt_percent(safe_pick(data, "forecast_confidence", "data_quality.confidence", "confidence_percent"))

    cards = [
        render_metric_card("SOC", soc, soc_unit, text(safe_pick(data, "soc_status", "battery_status"), "Batterijstand")),
        render_metric_card("PV nu", pv, pv_unit, text(safe_pick(data, "pv_status", "solar_status"), "Live vermogen")),
        render_metric_card("Huis", home, home_unit, text(safe_pick(data, "home_status", "load_status"), "Huidige vraag")),
        render_metric_card("Net", grid, grid_unit, text(safe_pick(data, "grid_status"), "Import/export")),
        render_metric_card("Batterij", battery, battery_unit, text(safe_pick(data, "battery_power_status"), "Laad/ontlaad")),
        render_metric_card("Prijs nu", price, price_unit, text(safe_pick(data, "price_status"), "Actueel tarief")),
        render_metric_card("Reserve", reserve, reserve_unit, text(safe_pick(data, "reserve_status"), "Minimum buffer")),
        render_metric_card("Data quality", quality, quality_unit, text(safe_pick(data, "data_quality.status", "degraded_text"), "Read-only display")),
    ]
    return "\n".join(cards)


def _window(predbat: dict[str, Any], start_key: str, end_key: str, limit_key: str) -> str:
    start = predbat.get(start_key)
    end = predbat.get(end_key)
    limit = predbat.get(limit_key)
    if start in MISSING and end in MISSING and limit in MISSING:
        return "—"
    power, unit = fmt_power(limit)
    return f"{text(start)} - {text(end)} · {power} {unit}"


def render_predbat_card(data: dict[str, Any]) -> str:
    predbat = safe_pick(data, "predbat", default={})
    predbat = predbat if isinstance(predbat, dict) else {}
    rows = [
        ("Status", safe_pick(data, "predbat.status", "predbat_status", default=None)),
        ("SOC", safe_pick(data, "predbat.soc_kw", "predbat_soc_kw", default=None)),
        ("Best SOC", safe_pick(data, "predbat.soc_kw_best", "predbat.best_soc_min_kwh", "predbat_best_soc", default=None)),
        ("Charge window", _window(predbat, "charge_start", "charge_end", "charge_limit_kw")),
        ("Export window", _window(predbat, "best_export_start", "best_export_end", "best_export_limit_kw")),
        ("Cost today", safe_pick(data, "predbat.cost_today", "predbat_cost_today", default=None)),
        ("Best metric", safe_pick(data, "predbat.best_metric", "predbat_best_metric", default=None)),
    ]
    has_data = any(value not in MISSING and value != "—" for _, value in rows)
    degraded = "" if has_data else '<p class="degraded">Geen Predbat benchmarkdata beschikbaar. De vergelijking blijft read-only gedegradeerd.</p>'
    body = "".join(f'<div class="kv"><span>{escape(label)}</span><strong>{escape(text(value))}</strong></div>' for label, value in rows)
    return f'''
      <section id="benchmark" class="panel">
        <div class="panel-head">
          <div><p class="eyebrow">Benchmark</p><h2>Predbat vergelijking</h2></div>
          {render_chip("benchmark only", "warn")}
        </div>
        <p class="copy">Predbat is referentie-input voor vergelijking. Energy Brain schrijft niets terug en gebruikt dit niet als runtime-aansturing.</p>
        {degraded}
        <div class="kv-grid">{body}</div>
      </section>
    '''


def _plan_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    items = safe_pick(data, "plan_windows", "plan.windows", "plan.steps", "timeline", "planner_timeline", default=[])
    return items if isinstance(items, list) else []


def render_plan_card(data: dict[str, Any]) -> str:
    items = [item for item in _plan_items(data) if isinstance(item, dict)]
    if not items:
        rows = '''
          <article class="timeline-row muted">
            <time>nu</time>
            <div><strong>Geen geldig plan / observer-only</strong><p>Geen planner-vensters beschikbaar. Er wordt niets aangestuurd.</p></div>
          </article>
        '''
    else:
        rows = "\n".join(_render_plan_row(item) for item in items[:10])
    return f'''
      <section id="plan" class="panel">
        <div class="panel-head">
          <div><p class="eyebrow">Volgende 24 uur</p><h2>Plan vandaag</h2></div>
          {render_chip("observer-only", "safe")}
        </div>
        <div class="timeline">{rows}</div>
      </section>
    '''


def _climate_attr(climate: Any, key: str) -> Any:
    if not isinstance(climate, dict):
        return None
    attrs = climate.get("attributes")
    if isinstance(attrs, dict):
        return attrs.get(key)
    return climate.get(key)


def _temp_ring(value: Any) -> str:
    number = num(value)
    if number is None:
        return "0"
    return f"{max(0, min(100, (number - 10) / 20 * 100)):.1f}"


def render_thermostat_card(title: str, entity_id: str, climate: Any) -> str:
    state = climate.get("state") if isinstance(climate, dict) else None
    current = _climate_attr(climate, "current_temperature")
    target = _climate_attr(climate, "temperature")
    hvac_action = _climate_attr(climate, "hvac_action") or state or "onbekend"
    current_label = fmt_temp(current)
    target_label = fmt_temp(target)
    return f'''
      <article class="thermo-card" aria-label="{escape(title)} thermostaat">
        <div class="thermo-top">
          <div>
            <p>{escape(title)}</p>
            <span>{escape(entity_id)}</span>
          </div>
          <strong>{escape(text(hvac_action))}</strong>
        </div>
        <div class="thermo-ring" style="--temp-ring:{_temp_ring(current)}">
          <div>
            <strong>{escape(current_label)}<span>°</span></strong>
            <small>doel {escape(target_label)}°</small>
          </div>
        </div>
        <div class="thermo-controls" aria-label="Read-only temperatuurknoppen">
          <span aria-hidden="true">−</span>
          <span aria-hidden="true">+</span>
        </div>
      </article>
    '''


def render_thermostat_panel(data: dict[str, Any]) -> str:
    living = safe_pick(data, "climate.ir_woonkamer", "thermostats.living", "living_climate", default={})
    kitchen = safe_pick(data, "climate.w100_keuken", "thermostats.kitchen", "kitchen_climate", default={})
    living = living if isinstance(living, dict) else {}
    kitchen = kitchen if isinstance(kitchen, dict) else {}
    return f'''
      <section id="thermal" class="panel thermal-panel">
        <div class="panel-head">
          <div><p class="eyebrow">Thermal intelligence</p><h2>IR Verwarming</h2></div>
          {render_chip("read-only", "safe")}
        </div>
        <div class="thermo-grid">
          {render_thermostat_card("Woonkamer", "climate.ir_woonkamer", living)}
          {render_thermostat_card("Keuken", "climate.w100_keuken", kitchen)}
        </div>
      </section>
    '''


def _render_plan_row(item: dict[str, Any]) -> str:
    start = text(safe_pick(item, "start", "time", "from", default="—"))
    end = text(safe_pick(item, "end", "to", default=""))
    label = f"{start} - {end}" if end else start
    kind = text(safe_pick(item, "kind", "type", "action", default="no-action")).replace("_", " ")
    reason = text(safe_pick(item, "reason", "explanation", default="Read-only planvenster."))
    return f'''
      <article class="timeline-row">
        <time>{escape(label)}</time>
        <div><strong>{escape(kind)}</strong><p>{escape(reason)}</p></div>
      </article>
    '''


def render_safety_card(data: dict[str, Any]) -> str:
    degraded = safe_pick(data, "degraded_flags", "safety.degraded_flags", default=[])
    missing = safe_pick(data, "missing_data_flags", "safety.missing_data_flags", default=[])
    degraded = degraded if isinstance(degraded, list) else []
    missing = missing if isinstance(missing, list) else []
    rows = [
        ("Observer-only", "ja"),
        ("Read-only", "ja"),
        ("Degraded flags", ", ".join(str(x) for x in degraded) if degraded else "—"),
        ("Missing data", ", ".join(str(x) for x in missing) if missing else "—"),
        ("Execution blocked", text(safe_pick(data, "execution_blocked_reason", "safety.execution_blocked_reason"), "UI read-only")),
        ("Battery reserve", text(safe_pick(data, "reserve_status", "battery_reserve_status"), "Reserve onbekend/safe")),
        ("Service calls", "geen"),
    ]
    body = "".join(f'<div class="kv"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>' for label, value in rows)
    return f'''
      <section id="safety" class="panel safety">
        <div class="panel-head">
          <div><p class="eyebrow">Safety</p><h2>Geen aansturing</h2></div>
          {render_chip("read-only", "safe")}
        </div>
        <p class="copy">Deze cockpit toont alleen status, planning en benchmarkinformatie. Er worden geen Home Assistant acties uitgevoerd.</p>
        <div class="kv-grid">{body}</div>
      </section>
    '''


STYLE = '''
  <style>
    /* ENERGY_BRAIN_FRESH_HOME_V2_START */
    :root {
      color-scheme: dark;
      --bg:#071018;
      --panel:#0f1922;
      --panel2:#121f2a;
      --card:#101b24;
      --line:rgba(222,238,246,.13);
      --text:#f4f8fa;
      --muted:#9dafba;
      --soft:#cfdee6;
      --cyan:#54d9c9;
      --blue:#7bb8ff;
      --amber:#f5b45d;
      --safe:#85e0ae;
      --shadow:0 18px 42px rgba(0,0,0,.28);
    }
    * { box-sizing:border-box; }
    html { scroll-behavior:smooth; }
    body {
      margin:0;
      min-height:100vh;
      overflow-x:hidden;
      background:linear-gradient(180deg,#071018 0%,#0a141d 48%,#071018 100%);
      color:var(--text);
      font:15px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    }
    a { color:inherit; text-decoration:none; }
    .topbar {
      position:sticky;
      top:0;
      z-index:30;
      min-height:68px;
      padding:8px max(13px,env(safe-area-inset-left)) 8px max(13px,env(safe-area-inset-right));
      background:rgba(7,16,24,.94);
      border-bottom:1px solid var(--line);
      backdrop-filter:blur(18px);
    }
    .topbar-inner {
      width:min(1120px,100%);
      margin:0 auto;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:10px;
    }
    .brand { display:flex; align-items:center; gap:9px; min-width:0; }
    .logo { width:34px; height:34px; flex:0 0 auto; }
    h1 { margin:0; font-size:clamp(18px,5vw,26px); line-height:1.05; font-weight:700; letter-spacing:0; }
    .chips { display:flex; gap:6px; flex:0 0 auto; }
    .chip {
      display:inline-flex;
      align-items:center;
      min-height:25px;
      padding:4px 8px;
      border:1px solid var(--line);
      border-radius:999px;
      background:rgba(255,255,255,.045);
      color:var(--soft);
      font-size:11px;
      font-weight:700;
      white-space:nowrap;
    }
    .chip.safe { color:var(--safe); border-color:rgba(133,224,174,.32); background:rgba(133,224,174,.1); }
    .chip.warn { color:var(--amber); border-color:rgba(245,180,93,.34); background:rgba(245,180,93,.1); }
    .app {
      width:min(1120px,100%);
      margin:0 auto;
      padding:10px 12px calc(96px + env(safe-area-inset-bottom));
    }
    .cockpit {
      padding:12px;
      border:1px solid var(--line);
      border-radius:8px;
      background:linear-gradient(180deg,rgba(18,31,42,.96),rgba(9,18,26,.97));
      box-shadow:var(--shadow);
    }
    .cockpit-grid { display:grid; gap:10px; }
    .eyebrow { margin:0 0 3px; color:var(--cyan); font-size:11px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
    h2 { margin:0; color:var(--text); font-size:clamp(21px,5.8vw,34px); line-height:1.08; letter-spacing:0; }
    .status { display:grid; gap:5px; margin-top:8px; color:var(--soft); }
    .status div { display:flex; gap:7px; align-items:flex-start; font-size:13px; line-height:1.3; }
    .dot { width:6px; height:6px; margin-top:6px; border-radius:50%; background:var(--cyan); flex:0 0 auto; }
    .lead { margin:8px 0 0; color:var(--muted); font-size:13px; line-height:1.35; }
    .pf2-card {
      width:100%;
      max-width:500px;
      margin:0 auto;
      padding:7px 4px 5px;
      border:1px solid rgba(222,238,246,.13);
      border-radius:8px;
      background:linear-gradient(180deg,rgba(22,25,26,.92),rgba(11,14,16,.98));
      overflow:hidden;
    }
    .pf2-svg { display:block; width:100%; height:auto; max-height:262px; }
    .pf2-title { fill:rgba(246,247,244,.78); font:700 14px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    .pf2-node { fill:#101315; }
    .pf2-ring { fill:none; stroke-width:1.8; }
    .pf2-ring.solar { stroke:#f5b45d; }
    .pf2-ring.grid { stroke:#8f77ff; }
    .pf2-ring.home { stroke:#54d9c9; }
    .pf2-ring.battery { stroke:#54d9c9; }
    .pf2-lane { fill:none; stroke-linecap:round; stroke-linejoin:round; }
    .pf2-lane.main { stroke-width:1.35; opacity:.82; }
    .pf2-lane.soft { stroke-width:.9; opacity:.36; }
    .pf2-card.pv-active .lane-pv,
    .pf2-card.home-active .lane-home,
    .pf2-card.battery-active .lane-battery,
    .pf2-card.grid-active .lane-grid {
      opacity:.92;
      filter:url(#pf2SoftGlow);
    }
    .pf2-dot { opacity:.78; filter:url(#pf2SoftGlow); transform-box:fill-box; transform-origin:center; }
    .pf2-particle { animation-duration:4.8s; animation-iteration-count:infinite; animation-timing-function:linear; }
    .pf2-particle.two { animation-delay:-2.4s; opacity:.52; }
    .pf2-particle.pv { animation-name:pf2-flow-down; }
    .pf2-particle.home { animation-name:pf2-flow-right; }
    .pf2-particle.battery { animation-name:pf2-flow-left; }
    .pf2-card.pv-idle .pf2-particle.pv,
    .pf2-card.home-idle .pf2-particle.home,
    .pf2-card.battery-idle .pf2-particle.battery { animation-play-state:paused; opacity:.18; }
    .pf2-grid-node { filter:url(#pf2SoftGlow); }
    .pf2-card.grid-active .pf2-ring.grid,
    .pf2-card.pv-active .pf2-ring.solar,
    .pf2-card.home-active .pf2-ring.home,
    .pf2-card.battery-active .pf2-ring.battery { filter:url(#pf2SoftGlow); }
    .pf2-node-name { fill:#f4f8fa; font:700 16px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    .pf2-node-name.solar-text { fill:#ffd56d; }
    .pf2-node-value { fill:#f4f8fa; font:700 11.5px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    .pf2-node-small { fill:rgba(244,248,250,.86); font:700 9.7px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    .metrics {
      display:grid;
      grid-template-columns:repeat(2,minmax(0,1fr));
      gap:8px;
      margin-top:10px;
    }
    .metric-card {
      min-height:92px;
      padding:11px;
      border:1px solid var(--line);
      border-radius:8px;
      background:rgba(16,27,36,.86);
    }
    .metric-card p { margin:0; color:var(--muted); font-size:11px; font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    .metric-card strong { display:block; margin-top:8px; color:var(--text); font-size:clamp(22px,7vw,33px); line-height:1; font-weight:750; overflow-wrap:anywhere; }
    .metric-card strong span { margin-left:4px; color:var(--muted); font-size:.46em; font-weight:700; }
    .metric-card small { display:block; margin-top:7px; color:var(--muted); font-size:11px; line-height:1.25; }
    .panel {
      margin-top:10px;
      padding:13px;
      border:1px solid var(--line);
      border-radius:8px;
      background:linear-gradient(180deg,rgba(16,27,36,.94),rgba(9,18,26,.96));
      box-shadow:0 10px 28px rgba(0,0,0,.2);
    }
    .panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; margin-bottom:9px; }
    .panel-head h2 { font-size:20px; }
    .copy,.degraded { margin:0 0 10px; color:var(--muted); font-size:13px; line-height:1.35; }
    .degraded { color:var(--amber); }
    .kv-grid { display:grid; gap:7px; }
    .kv {
      display:grid;
      grid-template-columns:minmax(110px,.85fr) minmax(0,1.15fr);
      gap:10px;
      padding:8px 0;
      border-top:1px solid rgba(255,255,255,.08);
    }
    .kv span { color:var(--muted); }
    .kv strong { color:var(--soft); font-weight:700; overflow-wrap:anywhere; }
    .timeline { display:grid; gap:8px; }
    .timeline-row {
      display:grid;
      grid-template-columns:72px minmax(0,1fr);
      gap:11px;
      padding:11px;
      border:1px solid rgba(255,255,255,.08);
      border-radius:8px;
      background:rgba(255,255,255,.035);
    }
    .timeline-row.muted { border-color:rgba(245,180,93,.25); background:rgba(245,180,93,.08); }
    .timeline-row time { color:var(--cyan); font-size:12px; font-weight:800; }
    .timeline-row strong { display:block; margin-bottom:3px; text-transform:capitalize; }
    .timeline-row p { margin:0; color:var(--muted); font-size:13px; line-height:1.35; }
    .thermal-panel {
      background:
        radial-gradient(circle at 50% 0%, rgba(245,180,93,.075), transparent 18rem),
        linear-gradient(180deg,rgba(16,27,36,.94),rgba(9,18,26,.96));
    }
    .thermo-grid {
      display:grid;
      grid-template-columns:repeat(2,minmax(0,1fr));
      gap:10px;
    }
    .thermo-card {
      min-width:0;
      padding:13px;
      border:1px solid rgba(222,238,246,.11);
      border-radius:8px;
      background:
        radial-gradient(circle at 50% 10%, rgba(245,180,93,.08), transparent 48%),
        linear-gradient(180deg,rgba(255,255,255,.032),rgba(255,255,255,.01));
      box-shadow:inset 0 1px 0 rgba(255,255,255,.04), 0 12px 28px rgba(0,0,0,.22);
    }
    .thermo-top {
      display:flex;
      align-items:flex-start;
      justify-content:space-between;
      gap:8px;
      min-height:42px;
    }
    .thermo-top p { margin:0; color:var(--text); font-size:14px; font-weight:800; }
    .thermo-top span { display:block; margin-top:3px; color:rgba(157,175,186,.62); font-size:10px; overflow-wrap:anywhere; }
    .thermo-top strong {
      flex:0 0 auto;
      max-width:86px;
      padding:4px 7px;
      border:1px solid rgba(245,180,93,.18);
      border-radius:999px;
      color:#ffdca0;
      background:rgba(245,180,93,.08);
      font-size:10px;
      font-weight:800;
      text-transform:uppercase;
      overflow:hidden;
      text-overflow:ellipsis;
      white-space:nowrap;
    }
    .thermo-ring {
      width:132px;
      height:132px;
      margin:12px auto 10px;
      border-radius:50%;
      display:grid;
      place-items:center;
      background:
        radial-gradient(circle at center, rgba(7,16,24,.98) 58%, transparent 59%),
        conic-gradient(from -90deg, rgba(245,180,93,.68) calc(var(--temp-ring) * 1%), rgba(255,255,255,.045) 0);
      box-shadow:0 0 28px rgba(245,180,93,.08), inset 0 0 26px rgba(255,255,255,.014);
    }
    .thermo-ring div { text-align:center; }
    .thermo-ring strong { display:block; color:var(--text); font-size:34px; line-height:.95; font-weight:760; }
    .thermo-ring strong span { color:var(--muted); font-size:.58em; font-weight:650; }
    .thermo-ring small { display:block; margin-top:6px; color:var(--muted); font-size:11px; font-weight:700; }
    .thermo-controls {
      display:grid;
      grid-template-columns:repeat(2,46px);
      justify-content:center;
      gap:16px;
      margin-top:8px;
    }
    .thermo-controls span {
      display:grid;
      place-items:center;
      width:46px;
      height:34px;
      border:1px solid rgba(222,238,246,.10);
      border-radius:999px;
      color:rgba(244,248,250,.82);
      background:linear-gradient(180deg,rgba(255,255,255,.064),rgba(255,255,255,.016));
      box-shadow:inset 0 1px 0 rgba(255,255,255,.05), 0 10px 22px rgba(0,0,0,.20);
      font-size:19px;
      font-weight:760;
      user-select:none;
    }
    .bottom-nav {
      position:fixed;
      left:0;
      right:0;
      bottom:0;
      z-index:35;
      display:grid;
      grid-template-columns:repeat(5,1fr);
      min-height:64px;
      padding:6px max(8px,env(safe-area-inset-left)) calc(6px + env(safe-area-inset-bottom)) max(8px,env(safe-area-inset-right));
      background:rgba(7,16,24,.96);
      border-top:1px solid var(--line);
      backdrop-filter:blur(18px);
    }
    .bottom-nav a { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:3px; color:var(--muted); font-size:11px; font-weight:700; }
    .bottom-nav svg { width:21px; height:21px; stroke:currentColor; fill:none; stroke-width:2; }
    @keyframes pf2-flow-down {
      from { transform:translateY(-48px); }
      to { transform:translateY(48px); }
    }
    @keyframes pf2-flow-right {
      from { transform:translateX(-82px); }
      to { transform:translateX(82px); }
    }
    @keyframes pf2-flow-left {
      from { transform:translateX(82px); }
      to { transform:translateX(-82px); }
    }
    @media (prefers-reduced-motion: reduce) { .pf2-dot { display:none; } html { scroll-behavior:auto; } }
    @media (max-width:380px) {
      .topbar { min-height:64px; }
      .logo { width:31px; height:31px; }
      h1 { font-size:17px; }
      .chip { font-size:10.5px; padding-inline:7px; }
      .pf2-svg { max-height:248px; }
      .thermo-grid { grid-template-columns:1fr; }
      .thermo-ring { width:124px; height:124px; }
    }
    @media (min-width:720px) {
      .app { padding:18px 22px calc(104px + env(safe-area-inset-bottom)); }
      .cockpit { padding:18px; }
      .cockpit-grid { grid-template-columns:minmax(0,.86fr) minmax(340px,.8fr); align-items:center; }
      .metrics { grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
      .panel { padding:18px; margin-top:14px; }
      .kv-grid { grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:22px; }
      .timeline-row { grid-template-columns:108px minmax(0,1fr); }
    }
    /* ENERGY_BRAIN_FRESH_HOME_V2_END */
  </style>
'''


def render_fresh_home_v2(display_data: dict[str, Any] | None = None) -> str:
    data = display_data if isinstance(display_data, dict) else {}
    mode = text(safe_pick(data, "mode", "status.mode", default="observer")).replace("_", "-")
    latest = text(safe_pick(data, "last_update", "updated_at", "cycle_time", "timestamp"), "—")
    execution = text(safe_pick(data, "execution", "execution_state", "safety.execution_state"), "Uitvoering geblokkeerd / Geen aansturing")

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>Energy Brain EMS</title>
  {STYLE}
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">{_logo()}<h1>Energy Brain EMS</h1></div>
      <div class="chips" aria-label="Modus">{render_chip("observer", "safe")}{render_chip("read-only", "safe")}</div>
    </div>
  </header>

  <main class="app">
    <section id="home" class="cockpit">
      <div class="cockpit-grid">
        <div>
          <p class="eyebrow">Cockpit</p>
          <h2>Vandaag</h2>
          <div class="status">
            <div><span class="dot"></span><span>Mode: {escape(mode)}</span></div>
            <div><span class="dot"></span><span>{escape(execution)}</span></div>
            <div><span class="dot"></span><span>Laatste update: {escape(latest)}</span></div>
          </div>
          <p class="lead">Energy Brain kijkt mee, vergelijkt en plant, maar stuurt nu niets aan.</p>
        </div>
        {render_powerflow(data)}
      </div>
    </section>

    <section id="forecast" class="metrics" aria-label="EMS metrics">
      {_metrics(data)}
    </section>

    {render_predbat_card(data)}
    {render_plan_card(data)}
    {render_thermostat_panel(data)}
    {render_safety_card(data)}
  </main>

  <nav class="bottom-nav" aria-label="Energy Brain navigatie">
    <a href="#home" aria-label="Home"><svg viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span>Home</span></a>
    <a href="#plan" aria-label="Plan"><svg viewBox="0 0 24 24"><path d="M4 5h16"/><path d="M4 12h16"/><path d="M4 19h10"/></svg><span>Plan</span></a>
    <a href="#forecast" aria-label="Forecast"><svg viewBox="0 0 24 24"><path d="M4 18l5-6 4 3 7-9"/><path d="M4 20h16"/></svg><span>Forecast</span></a>
    <a href="#benchmark" aria-label="Benchmark"><svg viewBox="0 0 24 24"><path d="M5 20V6"/><path d="M12 20V4"/><path d="M19 20v-9"/></svg><span>Benchmark</span></a>
    <a href="#safety" aria-label="Safety"><svg viewBox="0 0 24 24"><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z"/><path d="M9 12l2 2 4-5"/></svg><span>Safety</span></a>
  </nav>
</body>
</html>'''
