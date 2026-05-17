from __future__ import annotations

from html import escape
from typing import Any

from energy_brain.ui_static.ha_powerflow_card import render_ha_powerflow_card


MISSING_VALUES = (None, "", "unknown", "unavailable", "none", "None", "nan")


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
        if ok and cur not in MISSING_VALUES:
            return cur
    return default


def _as_float(value: Any) -> float | None:
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
                .replace("EUR", "")
                .replace("€", "")
                .strip()
            )
            if cleaned in ("", "-", "--", "—"):
                return None
            return float(cleaned)
        return float(value)
    except (TypeError, ValueError):
        return None


def format_power(value: Any) -> tuple[str, str]:
    number = _as_float(value)
    if number is None:
        return "—", "kW"
    if abs(number) > 50:
        number = number / 1000.0
    return f"{number:.1f}".replace(".", ","), "kW"


def format_percent(value: Any) -> tuple[str, str]:
    number = _as_float(value)
    if number is None:
        return "—", "%"
    return f"{number:.0f}", "%"


def _format_kwh(value: Any) -> tuple[str, str]:
    number = _as_float(value)
    if number is None:
        return "—", "kWh"
    return f"{number:.1f}".replace(".", ","), "kWh"


def _format_price(value: Any) -> tuple[str, str]:
    number = _as_float(value)
    if number is None:
        return "—", "EUR/kWh"
    return f"{number:.3f}".replace(".", ","), "EUR/kWh"


def _format_money(value: Any) -> tuple[str, str]:
    number = _as_float(value)
    if number is None:
        return "—", "EUR"
    return f"{number:.2f}".replace(".", ","), "EUR"


def _text(value: Any, fallback: str = "—") -> str:
    if value in MISSING_VALUES:
        return fallback
    return str(value)


def render_status_chip(label: str, tone: str = "neutral") -> str:
    return f'<span class="mode-chip {escape(tone)}">{escape(label)}</span>'


def render_metric_card(label: str, value: str, unit: str = "", note: str = "") -> str:
    unit_html = f'<span class="metric-unit">{escape(unit)}</span>' if unit else ""
    note_html = f'<div class="metric-note">{escape(note)}</div>' if note else ""
    return f'''
      <article class="metric-card">
        <div class="metric-label">{escape(label)}</div>
        <div class="metric-value">{escape(value)}{unit_html}</div>
        {note_html}
      </article>
    '''


def _brain_logo() -> str:
    return '''
      <svg class="eb-logo" viewBox="0 0 64 64" aria-hidden="true">
        <circle cx="32" cy="32" r="25" fill="none" stroke="rgba(84,217,201,.25)" stroke-width="1.5"/>
        <path d="M30 14c-8 0-13 6-13 13-6 2-8 8-5 14 2 5 7 8 13 7h5V14Z"
          fill="none" stroke="#54d9c9" stroke-width="3.1" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M34 14c8 0 13 6 13 13 6 2 8 8 5 14-2 5-7 8-13 7h-5V14Z"
          fill="none" stroke="#54d9c9" stroke-width="3.1" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M24 25h-6M25 34h-9M24 42h-5M40 25h6M39 34h9M40 42h5"
          fill="none" stroke="#7bb8ff" stroke-width="2.2" stroke-linecap="round"/>
      </svg>
    '''


def _metric_cards(data: dict[str, Any]) -> str:
    soc, soc_unit = format_percent(safe_pick(data, "soc_percent", "battery_soc_percent", "soc", "battery_soc"))
    pv, pv_unit = format_power(safe_pick(data, "pv_power_kw", "pv_now_kw", "pv_now", "pv_power_w", "pv_power"))
    home, home_unit = format_power(safe_pick(data, "household_load_kw", "home_load_kw", "load_kw", "house_kw", "household_load_w", "house"))
    grid, grid_unit = format_power(safe_pick(data, "grid_power_kw", "grid_kw", "net_kw", "grid_power_w", "grid_power", "grid"))
    battery, battery_unit = format_power(safe_pick(data, "battery_power_kw", "battery_kw", "battery_power_w", "battery_charge_kw", "battery_discharge_kw"))
    price, price_unit = _format_price(safe_pick(data, "price_now", "grid_price", "energy_flow.grid_price", "snapshot.grid_price"))
    return "\n".join(
        [
            render_metric_card("SOC", soc, soc_unit, _text(safe_pick(data, "soc_status", "battery_status"), "Batterijstand")),
            render_metric_card("PV nu", pv, pv_unit, _text(safe_pick(data, "pv_status", "solar_status"), "Live bron of laatste cyclus")),
            render_metric_card("Huis", home, home_unit, _text(safe_pick(data, "home_status", "load_status"), "Huidige belasting")),
            render_metric_card("Net", grid, grid_unit, _text(safe_pick(data, "grid_status"), "Import/export indicatie")),
            render_metric_card("Batterij", battery, battery_unit, _text(safe_pick(data, "battery_power_status"), "Laad/ontlaad vermogen")),
            render_metric_card("Prijs nu", price, price_unit, _text(safe_pick(data, "price_status"), "Tarief uit displaydata")),
        ]
    )


def render_predbat_comparison(data: dict[str, Any]) -> str:
    predbat = safe_pick(data, "predbat", default={})
    predbat = predbat if isinstance(predbat, dict) else {}
    rows = [
        ("Status", safe_pick(data, "predbat.status", "predbat_status", default=None)),
        ("SOC", safe_pick(data, "predbat.soc_kw", "predbat_soc_kw", default=None)),
        ("Best SOC", safe_pick(data, "predbat.soc_kw_best", "predbat.best_soc_min_kwh", "predbat_best_soc", default=None)),
        ("Charge window", _window_text(predbat, "charge_start", "charge_end", "charge_limit_kw")),
        ("Best charge", _window_text(predbat, "best_charge_start", "best_charge_end", "best_charge_limit_kw")),
        ("Export/discharge", _window_text(predbat, "best_export_start", "best_export_end", "best_export_limit_kw")),
        ("Cost today", safe_pick(data, "predbat.cost_today", "predbat_cost_today", default=None)),
        ("Best metric", safe_pick(data, "predbat.best_metric", "predbat_best_metric", default=None)),
    ]
    present = any(value not in MISSING_VALUES for _, value in rows if value != "—")
    body = "".join(
        f'<div class="kv-row"><span>{escape(label)}</span><strong>{escape(_text(value))}</strong></div>'
        for label, value in rows
    )
    degraded = "" if present else '<p class="degraded-copy">Geen Predbat benchmarkdata beschikbaar in display_data. Vergelijking blijft gedegradeerd en read-only.</p>'
    return f'''
      <section id="benchmark" class="panel comparison-panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Benchmark</p>
            <h2>Predbat vergelijking</h2>
          </div>
          {render_status_chip("benchmark only", "warn")}
        </div>
        <p class="panel-copy">Predbat is hier alleen referentie-input. Energy Brain neemt geen runtime-aansturing over en schrijft niets terug.</p>
        {degraded}
        <div class="kv-grid">{body}</div>
      </section>
    '''


def _window_text(source: dict[str, Any], start_key: str, end_key: str, limit_key: str) -> str:
    start = source.get(start_key)
    end = source.get(end_key)
    limit = source.get(limit_key)
    if start in MISSING_VALUES and end in MISSING_VALUES and limit in MISSING_VALUES:
        return "—"
    limit_value, limit_unit = format_power(limit)
    return f"{_text(start)} - {_text(end)} · {limit_value} {limit_unit}"


def render_plan_timeline(data: dict[str, Any]) -> str:
    windows = safe_pick(data, "plan_windows", "plan.timeline", "planner_timeline", "timeline", default=None)
    if not isinstance(windows, list) or not windows:
        rows = '''
          <article class="timeline-item muted">
            <span class="timeline-time">nu</span>
            <div>
              <strong>Geen geldig plan / observer-only</strong>
              <p>Geen planner-vensters beschikbaar in display_data. Er wordt niets aangestuurd.</p>
            </div>
          </article>
        '''
    else:
        rows = "\n".join(_render_timeline_item(item) for item in windows[:12] if isinstance(item, dict))
    return f'''
      <section id="plan" class="panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Volgende 24 uur</p>
            <h2>Plan vandaag</h2>
          </div>
          {render_status_chip("observer-only", "safe")}
        </div>
        <div class="timeline">{rows}</div>
      </section>
    '''


def _render_timeline_item(item: dict[str, Any]) -> str:
    start = _text(safe_pick(item, "start", "time", "from", default="—"))
    end = _text(safe_pick(item, "end", "to", default=""))
    kind = _text(safe_pick(item, "kind", "type", "action", default="no-action")).replace("_", " ")
    reason = _text(safe_pick(item, "reason", "explanation", default="Read-only planvenster."))
    time_label = f"{start} - {end}" if end else start
    return f'''
      <article class="timeline-item">
        <span class="timeline-time">{escape(time_label)}</span>
        <div>
          <strong>{escape(kind)}</strong>
          <p>{escape(reason)}</p>
        </div>
      </article>
    '''


def render_safety_card(data: dict[str, Any]) -> str:
    flags = safe_pick(data, "missing_data_flags", "safety.missing_data_flags", default=[])
    flags = flags if isinstance(flags, list) else []
    degraded_flags = safe_pick(data, "degraded_flags", "safety.degraded_flags", default=[])
    degraded_flags = degraded_flags if isinstance(degraded_flags, list) else []
    rows = [
        ("Observer-only", "ja"),
        ("Shadow/comparison", _text(safe_pick(data, "shadow_state", "mode"), "observer")),
        ("Degraded flags", ", ".join(str(x) for x in degraded_flags) if degraded_flags else "—"),
        ("Missing data", ", ".join(str(x) for x in flags) if flags else "—"),
        ("Execution blocked", _text(safe_pick(data, "execution_blocked_reason", "safety.execution_blocked_reason"), "UI read-only")),
        ("Battery reserve", _text(safe_pick(data, "reserve_status", "battery_reserve_status"), "—")),
        ("Fault/warning", _text(safe_pick(data, "fault_status", "warning_status", "safety.fault_status"), "geen bekende melding")),
    ]
    body = "".join(
        f'<div class="kv-row"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in rows
    )
    return f'''
      <section id="safety" class="panel safety-panel">
        <div class="section-head">
          <div>
            <p class="section-kicker">Safety</p>
            <h2>Geen aansturing</h2>
          </div>
          {render_status_chip("read-only", "safe")}
        </div>
        <p class="panel-copy">Deze pagina toont status, vergelijking en planning zonder Home Assistant writes of controller-wijzigingen.</p>
        <div class="kv-grid">{body}</div>
      </section>
    '''


def render_fresh_home_v1(display_data: dict[str, Any] | None = None) -> str:
    data = display_data if isinstance(display_data, dict) else {}
    mode = _text(safe_pick(data, "mode", "status.mode", default="observer-only")).replace("_", "-")
    last_update = _text(safe_pick(data, "last_update", "updated_at", "cycle_time", "timestamp"), "—")
    blocked = _text(safe_pick(data, "execution", "execution_state", "safety.execution_state"), "Uitvoering geblokkeerd")

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>Energy Brain EMS</title>
  <style>
    /* ENERGY_BRAIN_EMS_PAGE_V1_START */
    :root {{
      color-scheme: dark;
      --bg:#071018;
      --panel:#0d1821;
      --panel-2:#121f2a;
      --line:rgba(220,238,248,.13);
      --text:#f2f7f9;
      --muted:#a6b5c0;
      --soft:#d4e1e8;
      --cyan:#54d9c9;
      --blue:#79b8ff;
      --amber:#f6b35f;
      --bad:#ff8b7c;
      --safe:#88e0b0;
      --shadow:0 18px 48px rgba(0,0,0,.28);
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{
      margin:0;
      min-height:100vh;
      background:linear-gradient(180deg,#061019 0%,#09141d 48%,#071018 100%);
      color:var(--text);
      font:15px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      overflow-x:hidden;
    }}
    a {{ color:inherit; text-decoration:none; }}
    .topbar {{
      position:sticky;
      top:0;
      z-index:20;
      min-height:64px;
      padding:8px max(13px,env(safe-area-inset-left)) 8px max(13px,env(safe-area-inset-right));
      background:rgba(7,16,24,.94);
      border-bottom:1px solid var(--line);
      backdrop-filter:blur(16px);
    }}
    .topbar-inner {{
      width:min(1120px,100%);
      margin:0 auto;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
    }}
    .brand {{ display:flex; align-items:center; gap:10px; min-width:0; }}
    .eb-logo {{ width:36px; height:36px; flex:0 0 auto; }}
    .brand h1 {{ margin:0; font-size:clamp(18px,5vw,26px); line-height:1.05; font-weight:680; letter-spacing:0; white-space:nowrap; }}
    .mode-chips {{ display:flex; gap:6px; flex-wrap:nowrap; justify-content:flex-end; }}
    .mode-chip {{
      display:inline-flex;
      align-items:center;
      min-height:26px;
      border:1px solid var(--line);
      border-radius:999px;
      padding:4px 8px;
      color:var(--soft);
      background:rgba(255,255,255,.045);
      font-size:11px;
      font-weight:650;
      white-space:nowrap;
    }}
    .mode-chip.safe {{ color:var(--safe); border-color:rgba(136,224,176,.32); background:rgba(136,224,176,.10); }}
    .mode-chip.warn {{ color:var(--amber); border-color:rgba(246,179,95,.34); background:rgba(246,179,95,.10); }}
    .app {{
      width:min(1120px,100%);
      margin:0 auto;
      padding:10px 12px calc(94px + env(safe-area-inset-bottom));
    }}
    .hero {{
      border:1px solid var(--line);
      border-radius:8px;
      padding:12px;
      background:linear-gradient(180deg,rgba(20,33,44,.94),rgba(11,22,31,.96));
      box-shadow:var(--shadow);
    }}
    .section-kicker {{ margin:0 0 3px; color:var(--cyan); font-size:11px; font-weight:760; letter-spacing:.1em; text-transform:uppercase; }}
    h2 {{ margin:0; font-size:clamp(21px,5.5vw,34px); line-height:1.08; letter-spacing:0; }}
    .hero-grid {{ display:grid; gap:10px; }}
    .status-list {{ display:grid; gap:5px; margin-top:8px; color:var(--soft); }}
    .status-line {{ display:flex; gap:7px; align-items:flex-start; font-size:13px; line-height:1.3; }}
    .status-dot {{ width:6px; height:6px; margin-top:6px; border-radius:50%; background:var(--cyan); flex:0 0 auto; }}
    .hero-copy {{ margin:8px 0 0; color:var(--muted); max-width:760px; font-size:13px; line-height:1.35; font-weight:400; }}
    .metrics {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-top:10px; }}
    .metric-card {{
      min-height:92px;
      padding:11px;
      border:1px solid var(--line);
      border-radius:8px;
      background:rgba(16,26,35,.82);
    }}
    .metric-label {{ color:var(--muted); font-size:11px; font-weight:760; text-transform:uppercase; letter-spacing:.07em; }}
    .metric-value {{ margin-top:8px; color:var(--text); font-size:clamp(22px,7vw,34px); line-height:1; font-weight:680; overflow-wrap:anywhere; }}
    .metric-unit {{ margin-left:4px; color:var(--muted); font-size:.48em; font-weight:650; }}
    .metric-note {{ margin-top:7px; color:var(--muted); font-size:11px; line-height:1.25; }}
    .panel {{
      margin-top:10px;
      padding:13px;
      border:1px solid var(--line);
      border-radius:8px;
      background:linear-gradient(180deg,rgba(16,26,35,.94),rgba(10,20,29,.95));
      box-shadow:0 10px 30px rgba(0,0,0,.22);
    }}
    .section-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; margin-bottom:9px; }}
    .section-head h2 {{ font-size:20px; }}
    .panel-copy,.degraded-copy {{ margin:0 0 10px; color:var(--muted); font-size:13px; line-height:1.35; }}
    .degraded-copy {{ color:var(--amber); }}
    .kv-grid {{ display:grid; gap:8px; }}
    .kv-row {{
      display:grid;
      grid-template-columns:minmax(105px,.8fr) minmax(0,1.2fr);
      gap:10px;
      align-items:start;
      padding:8px 0;
      border-top:1px solid rgba(255,255,255,.08);
    }}
    .kv-row span {{ color:var(--muted); }}
    .kv-row strong {{ color:var(--soft); font-weight:650; overflow-wrap:anywhere; }}
    .timeline {{ display:grid; gap:9px; }}
    .timeline-item {{
      display:grid;
      grid-template-columns:74px minmax(0,1fr);
      gap:12px;
      padding:12px;
      border:1px solid rgba(255,255,255,.08);
      border-radius:8px;
      background:rgba(255,255,255,.035);
    }}
    .timeline-item.muted {{ border-color:rgba(246,179,95,.25); background:rgba(246,179,95,.08); }}
    .timeline-time {{ color:var(--cyan); font-size:12px; font-weight:760; }}
    .timeline-item strong {{ display:block; margin-bottom:3px; color:var(--text); text-transform:capitalize; }}
    .timeline-item p {{ margin:0; color:var(--muted); }}
    .bottom-nav {{
      position:fixed;
      left:0;
      right:0;
      bottom:0;
      z-index:25;
      display:grid;
      grid-template-columns:repeat(5,1fr);
      min-height:64px;
      padding:6px max(8px,env(safe-area-inset-left)) calc(6px + env(safe-area-inset-bottom)) max(8px,env(safe-area-inset-right));
      background:rgba(7,16,24,.96);
      border-top:1px solid var(--line);
      backdrop-filter:blur(16px);
    }}
    .bottom-nav a {{ display:flex; flex-direction:column; align-items:center; justify-content:center; gap:3px; color:var(--muted); font-size:11px; font-weight:650; }}
    .bottom-nav svg {{ width:21px; height:21px; stroke:currentColor; fill:none; stroke-width:2; }}
    @media (max-width:430px) {{
      .topbar-inner {{ align-items:center; gap:8px; }}
      .brand {{ gap:8px; }}
      .mode-chip {{ font-size:10.5px; min-height:24px; padding-inline:7px; }}
      .brand h1 {{ font-size:18px; white-space:normal; }}
      .eb-logo {{ width:32px; height:32px; }}
    }}
    @media (min-width:720px) {{
      .app {{ padding:18px 22px calc(104px + env(safe-area-inset-bottom)); }}
      .hero {{ padding:22px; }}
      .hero-grid {{ grid-template-columns:minmax(0,.9fr) minmax(330px,.75fr); align-items:center; }}
      .metrics {{ grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
      .panel {{ padding:20px; margin-top:16px; }}
      .kv-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:22px; }}
      .timeline-item {{ grid-template-columns:110px minmax(0,1fr); }}
    }}
    /* ENERGY_BRAIN_EMS_PAGE_V1_END */
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        {_brain_logo()}
        <h1>Energy Brain EMS</h1>
      </div>
      <div class="mode-chips" aria-label="Modus">
        {render_status_chip("observer", "safe")}
        {render_status_chip("read-only", "safe")}
      </div>
    </div>
  </header>

  <main class="app">
    <section id="home" class="hero">
      <div class="hero-grid">
        <div>
          <p class="section-kicker">Cockpit</p>
          <h2>Vandaag</h2>
          <div class="status-list">
            <div class="status-line"><span class="status-dot"></span><span>Mode: {escape(mode)}</span></div>
            <div class="status-line"><span class="status-dot"></span><span>{escape(blocked)}</span></div>
            <div class="status-line"><span class="status-dot"></span><span>Laatste update: {escape(last_update)}</span></div>
          </div>
          <p class="hero-copy">Energy Brain kijkt mee, vergelijkt en plant, maar stuurt nu niets aan.</p>
        </div>
        {render_ha_powerflow_card(data)}
      </div>
    </section>

    <section id="forecast" class="metrics" aria-label="EMS metrics">
      {_metric_cards(data)}
    </section>

    {render_predbat_comparison(data)}
    {render_plan_timeline(data)}
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
