"""Deterministic read-only Tesla-style cockpit payload and HTML rendering."""

from __future__ import annotations

import html
import json
from typing import Any

from energy_brain.v1969.tesla_style_cockpit_spec import REQUIRED_SECTIONS, build_tesla_style_cockpit_spec

SCHEMA_VERSION = "v2032_v2063.interactive_read_only_cockpit.1"


def build_read_only_cockpit_payload(summary: dict[str, Any]) -> dict[str, Any]:
    """Build display-only cockpit data from a summarized local cycle."""

    spec = build_tesla_style_cockpit_spec()
    plan = _dict(summary.get("plan"))
    snapshot = _dict(summary.get("snapshot"))
    controller = _dict(summary.get("controller"))
    raw_rows = [_cycle_row(step, snapshot) for step in _list(plan.get("steps"))[:24]]
    degraded = summary.get("valid_cycle") is not True
    soc_now = _num(snapshot.get("battery_soc_percent"), 64.0)
    min_soc = _num(plan.get("min_soc_percent"), max(20.0, soc_now - 4.0))
    max_soc = _num(plan.get("max_soc_percent"), min(100.0, soc_now + 8.0))
    cycle_rows = raw_rows if raw_rows else _shadow_rows(soc_now, snapshot)
    reason_counts = _reason_counts(cycle_rows)

    return {
        "schema_version": SCHEMA_VERSION,
        "source": "local_cycle_summary_or_deterministic_shadow",
        "read_only": True,
        "observer_only": True,
        "service_calls_allowed": False,
        "write_controls_allowed": False,
        "control_buttons": [],
        "spec_schema_version": spec["schema_version"],
        "required_sections": list(REQUIRED_SECTIONS),
        "hero_status": {
            "title": "Energy Brain cockpit",
            "state": "Observer-only" if not degraded else "Safe observer waiting",
            "mode": _text(summary.get("mode"), "observer"),
            "message": _text(summary.get("message"), "Latest shadow cycle available"),
            "planner_valid": plan.get("valid") is True,
        },
        "read_only_badges": [
            "OBSERVER-ONLY",
            "READ-ONLY",
            "NO DISPATCH",
            "NO SERVICE CALLS",
            "DISPLAY ONLY",
        ],
        "degraded_mode_banner": {
            "active": degraded,
            "reason": "No valid local cycle available" if degraded else "Inputs currently usable for display",
            "fallback_mode": "deterministic shadow sample" if degraded else "latest local cycle",
        },
        "energy_flow": {
            "pv_kw": _num(snapshot.get("pv_power_kw"), 3.2),
            "battery_kw": _num(controller.get("setpoint_kw"), 0.0),
            "load_kw": _num(snapshot.get("household_load_kw"), 1.4),
            "grid_kw": round(_num(snapshot.get("household_load_kw"), 1.4) - _num(snapshot.get("pv_power_kw"), 3.2), 2),
        },
        "battery_soc_card": {
            "soc_percent": soc_now,
            "reserve_percent": 20.0,
            "min_forecast_soc": min_soc,
            "max_forecast_soc": max_soc,
        },
        "soc_trajectory": _soc_points(cycle_rows, soc_now, min_soc),
        "planner_timeline": _timeline(cycle_rows),
        "plan_windows": _plan_windows(cycle_rows),
        "price_forecast": _forecast("import_price", _num(snapshot.get("grid_price"), 0.31), [0.02, 0.01, -0.03, 0.04]),
        "pv_forecast": _forecast("pv_kwh", _num(snapshot.get("pv_power_kw"), 3.2), [-0.4, 0.2, 0.6, -0.7]),
        "load_forecast": _forecast("load_kwh", _num(snapshot.get("household_load_kw"), 1.4), [0.1, 0.3, -0.2, 0.2]),
        "plan_explainability": {
            "reason_counts": reason_counts,
            "top_reasons": list(reason_counts)[:6],
            "selected_reason": next(iter(reason_counts), "shadow_hold"),
            "constraints_applied": [
                "reserve/min SOC band is always visualized",
                "max-SOC clamp windows are labels only",
                "baseline comparison stays local to the display payload",
            ],
            "display_only_safety": "All planner data is rendered for inspection only; no write controls or service paths are present.",
            "degraded_explanation": (
                "Fallback shadow data is deterministic and marked display-only when no valid cycle is available."
                if degraded
                else "Latest local cycle data is available; fallback shadow values are not active."
            ),
            "reason_explanations": _reason_explanations(),
        },
        "benchmark_comparison": {
            "baseline_cost": plan.get("baseline_cost"),
            "shadow_cost": plan.get("expected_cost"),
            "delta": plan.get("delta_vs_baseline"),
            "quality_notes": [
                "Energy Brain expected cost is compared with a baseline display metric.",
                "Predbat-inspired conceptual comparison is benchmark/reference only, not a runtime dependency.",
            ],
        },
        "safety_panel": {
            "controller_boundary": "protected",
            "adapter_boundary": "not used by cockpit",
            "writes_enabled": False,
            "services_enabled": False,
            "buttons": [],
        },
        "latest_cycle_table": raw_rows,
    }


def render_tesla_cockpit_html(summary: dict[str, Any]) -> str:
    payload = build_read_only_cockpit_payload(summary)
    payload_json = json.dumps(payload, sort_keys=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Energy Brain Tesla-Style Cockpit</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #05070a;
      --panel: #0f171f;
      --panel2: #151f29;
      --panel3: #1b2631;
      --line: rgba(238, 244, 248, 0.12);
      --text: #eef4f8;
      --muted: #9eacb8;
      --green: #43d6a6;
      --blue: #69a7ff;
      --sun: #ffd166;
      --warn: #f2b84b;
      --red: #ff7777;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background:
        linear-gradient(rgba(255,255,255,.026) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.026) 1px, transparent 1px),
        linear-gradient(135deg, #05070a 0%, #0b1117 58%, #111a22 100%);
      background-size: 38px 38px, 38px 38px, auto;
      color: var(--text);
      font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{ max-width: 1480px; margin: 0 auto; padding: 24px; }}
    h1, h2, h3, p {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: clamp(2.1rem, 5vw, 4.6rem); line-height: .95; font-weight: 720; }}
    h2 {{ font-size: 1rem; font-weight: 740; }}
    h3 {{ color: var(--muted); font-size: .76rem; font-weight: 780; text-transform: uppercase; }}
    button {{ font: inherit; }}
    .hero {{
      display: grid; grid-template-columns: minmax(0, 1fr) minmax(260px, auto); gap: 20px; align-items: end;
      min-height: 236px; padding: 30px; border: 1px solid var(--line); border-radius: 8px;
      background: linear-gradient(150deg, rgba(21,31,41,.96), rgba(7,10,14,.98));
    }}
    .eyebrow {{ color: var(--green); font-size: .76rem; font-weight: 820; text-transform: uppercase; margin-bottom: 12px; }}
    .subhead {{ color: var(--muted); max-width: 780px; margin-top: 16px; }}
    .safety-rail {{
      position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
      margin: 14px 0; padding: 10px; border: 1px solid var(--line); border-radius: 8px;
      background: rgba(5, 7, 10, .9); backdrop-filter: blur(10px);
    }}
    .badge {{ border: 1px solid var(--line); border-radius: 999px; color: var(--text); font-size: .74rem; font-weight: 780; padding: 7px 10px; text-transform: uppercase; white-space: nowrap; }}
    .badge.safe {{ border-color: rgba(67,214,166,.36); background: rgba(67,214,166,.1); color: #b7ffe5; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 0; }}
    .tab-button, .step-button, .json-toggle {{
      border: 1px solid var(--line); border-radius: 8px; background: rgba(21,31,41,.78); color: var(--text);
      cursor: pointer; font-weight: 760;
    }}
    .tab-button {{ min-height: 38px; padding: 8px 13px; }}
    .tab-button[aria-selected="true"] {{ border-color: rgba(105,167,255,.65); background: rgba(105,167,255,.18); }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .banner {{ margin-top: 14px; border: 1px solid rgba(242,184,75,.42); border-radius: 8px; background: rgba(242,184,75,.1); padding: 13px 15px; color: #ffe0a3; }}
    .grid {{ display: grid; gap: 14px; margin-top: 14px; }}
    .top {{ grid-template-columns: 1.25fr .75fr; }}
    .three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .four {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .card {{ border: 1px solid var(--line); border-radius: 8px; background: rgba(15,23,31,.94); padding: 18px; overflow: hidden; }}
    .card.soft {{ background: rgba(21,31,41,.86); }}
    .value {{ font-size: 2rem; font-weight: 740; margin-top: 10px; overflow-wrap: anywhere; }}
    .note {{ color: var(--muted); margin-top: 8px; }}
    .mini {{ color: var(--muted); font-size: .82rem; }}
    .flow {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }}
    .flow .card {{ min-height: 116px; }}
    .chart {{ width: 100%; height: 270px; display: block; margin-top: 16px; }}
    .timeline-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 14px; }}
    .steps {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }}
    .step-button {{ min-height: 74px; padding: 9px; text-align: left; }}
    .step-button.active {{ outline: 2px solid rgba(67,214,166,.7); background: rgba(67,214,166,.13); }}
    .step-index {{ color: var(--muted); display: flex; justify-content: space-between; font-size: .76rem; font-weight: 760; }}
    .step-soc {{ font-size: 1.2rem; font-weight: 780; margin-top: 5px; }}
    .step-reason {{ color: var(--muted); font-size: .76rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .windows {{ display: grid; gap: 9px; margin-top: 12px; }}
    .window-row {{ display: grid; grid-template-columns: 126px minmax(0, 1fr); gap: 10px; align-items: center; }}
    .track {{ height: 14px; border-radius: 999px; background: rgba(238,244,248,.08); position: relative; overflow: hidden; }}
    .segment {{ position: absolute; top: 0; bottom: 0; border-radius: 999px; }}
    .charge {{ background: rgba(67,214,166,.72); }}
    .hold {{ background: rgba(158,172,184,.5); }}
    .clamp {{ background: rgba(242,184,75,.72); }}
    .baseline {{ background: rgba(105,167,255,.62); }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid rgba(238,244,248,.09); padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: .72rem; text-transform: uppercase; }}
    td {{ color: #cbd6df; }}
    .list {{ display: grid; gap: 8px; margin-top: 12px; }}
    .list div {{ display: flex; justify-content: space-between; gap: 14px; border-bottom: 1px solid rgba(238,244,248,.08); padding-bottom: 8px; }}
    .reason-badge {{ border: 1px solid rgba(255,255,255,.1); border-radius: 999px; display: inline-flex; font-size: .76rem; font-weight: 740; padding: 5px 9px; white-space: nowrap; }}
    .reason-charge {{ background: rgba(67,214,166,.13); color: #a7f7da; }}
    .reason-discharge {{ background: rgba(105,167,255,.13); color: #a8cfff; }}
    .reason-clamp {{ background: rgba(242,184,75,.14); color: #ffd99b; }}
    .reason-hold {{ background: rgba(158,172,184,.12); color: #d4dce7; }}
    .inspector {{ position: sticky; top: 72px; }}
    .json-toggle {{ margin-top: 14px; padding: 9px 12px; }}
    .json-viewer {{ display: none; max-height: 420px; overflow: auto; margin-top: 12px; border: 1px solid var(--line); border-radius: 8px; background: #070a0e; padding: 14px; color: #d9e6ef; white-space: pre-wrap; }}
    .json-viewer.open {{ display: block; }}
    @media (max-width: 1040px) {{ .hero, .top, .timeline-grid, .three, .four, .flow {{ grid-template-columns: 1fr; }} .steps {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} .inspector {{ position: static; }} }}
    @media (max-width: 620px) {{ main {{ padding: 14px; }} .hero {{ padding: 22px; }} .steps {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .window-row {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <div>
        <p class="eyebrow">Hero Status</p>
        <h1>{_esc(payload["hero_status"]["title"])}</h1>
        <p class="subhead">{_esc(payload["hero_status"]["state"])} · mode {_esc(payload["hero_status"]["mode"])} · {_esc(payload["hero_status"]["message"])}</p>
      </div>
      <div>
        <div class="badge safe">inspect only</div>
        <p class="note">Predbat-inspired planning views are display labels and comparisons only.</p>
      </div>
    </header>
    <nav class="safety-rail" aria-label="Safety rail visible on every tab">{_badges(payload["read_only_badges"])}<span class="mini">Observer-only/read-only badges</span></nav>
    <div class="tabs" role="tablist" aria-label="Inspect only cockpit tabs">
      {_tab_button("overview", "Overview", True)}
      {_tab_button("plan", "Plan", False)}
      {_tab_button("forecast", "Forecast", False)}
      {_tab_button("benchmark", "Benchmark", False)}
      {_tab_button("safety", "Safety", False)}
    </div>
    {_banner(payload["degraded_mode_banner"])}
    <section id="tab-overview" class="tab-panel active" role="tabpanel">
      <div class="grid top">
        <article class="card">
          <h2>SOC Trajectory · Integrated Horizon Chart</h2>
          <p class="note">SOC trajectory with price, PV/load overlays, and reserve/min SOC band.</p>
          {_horizon_chart(payload)}
        </article>
        <article class="card soft">
          <h2>Battery SOC Card</h2>
          {_kv(payload["battery_soc_card"], "%")}
        </article>
      </div>
      <section class="flow" aria-label="Energy Flow Overview">{_energy_flow(payload["energy_flow"])}</section>
    </section>
    <section id="tab-plan" class="tab-panel" role="tabpanel">
      <div class="timeline-grid">
        <article class="card">
          <h2>Planner Timeline</h2>
          <p class="note">First 24 planner steps. Step tiles are inspect-only selections.</p>
          {_timeline_html(payload["planner_timeline"])}
          <h2 style="margin-top:18px">Predbat-Inspired Plan Windows</h2>
          {_window_html(payload["plan_windows"])}
        </article>
        <article class="card inspector" id="selected-step-inspector" aria-live="polite">
          <h2>Selected-Step Inspector</h2>
          <div id="step-detail-panel">{_step_detail(payload["planner_timeline"][0] if payload["planner_timeline"] else {})}</div>
        </article>
      </div>
    </section>
    <section id="tab-forecast" class="tab-panel" role="tabpanel">
      <div class="grid three">
        {_forecast_card("Price Forecast Panel", payload["price_forecast"])}
        {_forecast_card("PV Forecast Panel", payload["pv_forecast"])}
        {_forecast_card("Load Forecast Panel", payload["load_forecast"])}
      </div>
      <article class="card" style="margin-top:14px">
        <h2>Latest Cycle Table</h2>
        {_cycle_table(payload["latest_cycle_table"])}
      </article>
    </section>
    <section id="tab-benchmark" class="tab-panel" role="tabpanel">
      <div class="grid top">
        <article class="card">
          <h2>Benchmark Comparison Panel</h2>
          {_benchmark(payload["benchmark_comparison"])}
        </article>
        <article class="card">
          <h2>Predbat Benchmark/Reference Notice</h2>
          <p class="note">Predbat is benchmark/reference only, not runtime dependency. This cockpit uses local display payloads and conceptual comparison labels.</p>
        </article>
      </div>
    </section>
    <section id="tab-safety" class="tab-panel" role="tabpanel">
      <div class="grid top">
        <article class="card">
          <h2>Plan Explainability Panel</h2>
          {_reason_html(payload["plan_explainability"])}
        </article>
        <article class="card">
          <h2>Safety Panel</h2>
          {_safety(payload["safety_panel"])}
          <p class="note">Required Cockpit Sections: {len(payload["required_sections"])} sections active from V1969 spec.</p>
          <button type="button" class="json-toggle" id="json-toggle" aria-controls="json-viewer" aria-expanded="false">Show read-only JSON viewer</button>
          <pre id="json-viewer" class="json-viewer" aria-label="Read-only current /api/tesla-cockpit payload"></pre>
        </article>
      </div>
    </section>
  </main>
  <script id="cockpit-payload" type="application/json">{_esc(payload_json)}</script>
  <script>
    const payload = JSON.parse(document.getElementById('cockpit-payload').textContent);
    const tabButtons = Array.from(document.querySelectorAll('.tab-button'));
    const panels = Array.from(document.querySelectorAll('.tab-panel'));
    tabButtons.forEach((button) => {{
      button.addEventListener('click', () => {{
        const target = button.dataset.tab;
        tabButtons.forEach((item) => item.setAttribute('aria-selected', String(item === button)));
        panels.forEach((panel) => panel.classList.toggle('active', panel.id === `tab-${{target}}`));
      }});
    }});
    const detail = document.getElementById('step-detail-panel');
    const reasonMap = payload.plan_explainability.reason_explanations || {{}};
    function safeValue(value, suffix = '') {{
      return value === null || value === undefined || value === '' ? 'n/a' : `${{value}}${{suffix}}`;
    }}
    function showStep(index) {{
      const step = payload.planner_timeline[index] || payload.planner_timeline[0] || {{}};
      document.querySelectorAll('.step-button').forEach((item) => item.classList.toggle('active', Number(item.dataset.index) === index));
      const reason = step.reason_code || 'shadow_hold';
      detail.innerHTML = `
        <div class="list">
          <div><span>step index</span><strong>${{safeValue(step.step)}}</strong></div>
          <div><span>SOC %</span><strong>${{safeValue(step.soc_percent, '%')}}</strong></div>
          <div><span>battery setpoint kW</span><strong>${{safeValue(step.setpoint_kw)}}</strong></div>
          <div><span>reason code</span><strong>${{reason}}</strong></div>
          <div><span>price</span><strong>${{safeValue(step.price)}}</strong></div>
          <div><span>PV forecast</span><strong>${{safeValue(step.pv_forecast)}}</strong></div>
          <div><span>load forecast</span><strong>${{safeValue(step.load_forecast)}}</strong></div>
          <div><span>grid estimate</span><strong>${{safeValue(step.grid_estimate)}}</strong></div>
          <div><span>validation/display-only status</span><strong>${{safeValue(step.validity)}}</strong></div>
        </div>
        <p class="note" id="selected-reason-explanation">${{reasonMap[reason] || reasonMap.shadow_hold || 'Display-only planner interval.'}}</p>
      `;
    }}
    document.querySelectorAll('.step-button').forEach((button) => {{
      button.addEventListener('click', () => showStep(Number(button.dataset.index)));
    }});
    const jsonToggle = document.getElementById('json-toggle');
    const jsonViewer = document.getElementById('json-viewer');
    if (jsonToggle && jsonViewer) {{
      jsonViewer.textContent = JSON.stringify(payload, null, 2);
      jsonToggle.addEventListener('click', () => {{
        const open = jsonViewer.classList.toggle('open');
        jsonToggle.setAttribute('aria-expanded', String(open));
        jsonToggle.textContent = open ? 'Hide read-only JSON viewer' : 'Show read-only JSON viewer';
      }});
    }}
    showStep(0);
  </script>
</body>
</html>
"""


def _cycle_row(step: Any, snapshot: dict[str, Any]) -> dict[str, Any]:
    item = _dict(step)
    soc = item.get("soc_percent")
    setpoint = item.get("battery_setpoint_kw")
    pv = _num(item.get("pv_forecast"), _num(snapshot.get("pv_power_kw"), 3.2))
    load = _num(item.get("load_forecast"), _num(snapshot.get("household_load_kw"), 1.4))
    grid = item.get("grid_estimate")
    return {
        "step": item.get("index"),
        "soc_percent": soc,
        "setpoint_kw": setpoint,
        "reason_code": _text(item.get("reason"), "shadow_hold"),
        "price": _num(item.get("price"), _num(snapshot.get("grid_price"), 0.31)),
        "pv_forecast": pv,
        "load_forecast": load,
        "grid_estimate": _num(grid, round(load - pv - _num(setpoint, 0.0), 2)),
        "validity": "display-only",
    }


def _shadow_rows(current_soc: float, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    reasons = ["shadow_hold", "charge_from_pv_surplus", "reserve_hold", "max_soc_clamp", "baseline_compare"]
    rows = []
    for index in range(24):
        setpoint = 1.1 if index in (2, 3, 4, 13) else (-0.5 if index in (18, 19) else 0.0)
        soc = max(20.0, min(96.0, current_soc + (index % 6) * 0.8 - max(0, index - 14) * 0.35))
        rows.append(
            {
                "step": index,
                "soc_percent": round(soc, 2),
                "setpoint_kw": setpoint,
                "reason_code": reasons[index % len(reasons)],
                "price": round(_num(snapshot.get("grid_price"), 0.31) + ((index % 5) - 2) * 0.018, 3),
                "pv_forecast": round(max(0.0, _num(snapshot.get("pv_power_kw"), 3.2) + ((index % 8) - 3) * 0.18), 2),
                "load_forecast": round(max(0.2, _num(snapshot.get("household_load_kw"), 1.4) + ((index % 4) - 1) * 0.16), 2),
                "grid_estimate": round(_num(snapshot.get("household_load_kw"), 1.4) - _num(snapshot.get("pv_power_kw"), 3.2) - setpoint, 2),
                "validity": "display-only fallback",
            }
        )
    return rows


def _soc_points(rows: list[dict[str, Any]], current: float, reserve: float) -> list[dict[str, float]]:
    values = [_num(row.get("soc_percent"), current) for row in rows] or [current, current + 1.0, current + 2.0, current + 1.5]
    return [{"step": float(index), "soc_percent": value, "reserve_floor": reserve} for index, value in enumerate(values[:24])]


def _timeline(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return rows[:24]


def _plan_windows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"label": "charge windows", "kind": "charge", "segments": _segments(rows, lambda row: _num(row.get("setpoint_kw"), 0.0) > 0.05)},
        {"label": "hold windows", "kind": "hold", "segments": _segments(rows, lambda row: abs(_num(row.get("setpoint_kw"), 0.0)) <= 0.05)},
        {"label": "clamp/max-SOC windows", "kind": "clamp", "segments": _segments(rows, lambda row: "clamp" in _text(row.get("reason_code"), "").lower() or "max_soc" in _text(row.get("reason_code"), "").lower())},
        {"label": "baseline comparison windows", "kind": "baseline", "segments": _segments(rows, lambda row: "baseline" in _text(row.get("reason_code"), "").lower() or int(_num(row.get("step"), 0)) % 8 == 0)},
    ]


def _segments(rows: list[dict[str, Any]], predicate: Any) -> list[dict[str, float]]:
    total = max(1, len(rows))
    segments: list[dict[str, float]] = []
    start: int | None = None
    for index, row in enumerate(rows):
        active = bool(predicate(row))
        if active and start is None:
            start = index
        if (not active or index == len(rows) - 1) and start is not None:
            end = index + 1 if active and index == len(rows) - 1 else index
            segments.append({"left": round(start / total * 100.0, 2), "width": round(max(1, end - start) / total * 100.0, 2)})
            start = None
    return segments


def _forecast(name: str, base: float, offsets: list[float]) -> list[dict[str, Any]]:
    return [{"time": f"+{index}h", name: round(max(0.0, base + offset), 3), "quality": "shadow"} for index, offset in enumerate(offsets)]


def _reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = _text(row.get("reason_code"), "shadow_hold")
        counts[reason] = counts.get(reason, 0) + 1
    return counts or {"shadow_hold": 1}


def _reason_explanations() -> dict[str, str]:
    return {
        "shadow_hold": "Holding is shown when the shadow plan has no beneficial move or fallback data is active.",
        "hold": "Hold keeps the battery stable while price, reserve, and forecast constraints are inspected.",
        "reserve_hold": "Reserve hold protects the visual reserve/min SOC band in the forward horizon.",
        "charge_from_pv_surplus": "PV surplus charging is a display label for forecasted local solar surplus.",
        "discharge_to_load": "Discharge-to-load marks a shadow interval where stored energy offsets household demand.",
        "max_soc_clamp": "Max-SOC clamp marks an interval constrained by an upper SOC boundary.",
        "baseline_compare": "Baseline comparison marks an interval used for cost comparison against a non-optimized path.",
    }


def _badges(values: list[str]) -> str:
    return "".join(f'<span class="badge safe">{_esc(value)}</span>' for value in values)


def _tab_button(tab_id: str, label: str, selected: bool) -> str:
    return f'<button type="button" class="tab-button" role="tab" data-tab="{_esc(tab_id)}" aria-selected="{str(selected).lower()}">{_esc(label)}</button>'


def _banner(data: dict[str, Any]) -> str:
    label = "Degraded-Mode Banner"
    return f'<section class="banner"><strong>{label}:</strong> {_esc(data.get("reason"))} · fallback {_esc(data.get("fallback_mode"))}</section>'


def _energy_flow(flow: dict[str, Any]) -> str:
    labels = [("PV", "pv_kw", "Solar production"), ("Battery", "battery_kw", "Shadow setpoint"), ("Load", "load_kw", "House demand"), ("Grid", "grid_kw", "Import/export estimate")]
    return "".join(f'<article class="card"><h3>{label}</h3><div class="value">{_fmt(flow.get(key), " kW")}</div><p class="note">{note}</p></article>' for label, key, note in labels)


def _kv(data: dict[str, Any], suffix: str = "") -> str:
    return '<div class="list">' + "".join(f"<div><span>{_esc(key)}</span><strong>{_fmt(value, suffix)}</strong></div>" for key, value in data.items()) + "</div>"


def _forecast_card(title: str, rows: list[dict[str, Any]]) -> str:
    body = "".join(f"<tr>{''.join(f'<td>{_esc(value)}</td>' for value in row.values())}</tr>" for row in rows)
    head = "".join(f"<th>{_esc(key)}</th>" for key in (rows[0].keys() if rows else []))
    return f'<article class="card"><h2>{title}</h2><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></article>'


def _timeline_html(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="note">No planner steps available</p>'
    parts = []
    for index, row in enumerate(rows[:24]):
        reason = _text(row.get("reason_code"), "shadow_hold")
        active = " active" if index == 0 else ""
        parts.append(
            f'<button type="button" class="step-button{active}" data-index="{index}" aria-label="inspect only planner step {index}">'
            f'<span class="step-index"><span>#{_esc(row.get("step"))}</span><span>{_esc(row.get("validity"))}</span></span>'
            f'<span class="step-soc">{_fmt(row.get("soc_percent"), "%")}</span>'
            f'<span class="step-reason">{_esc(reason)}</span>'
            "</button>"
        )
    return '<div class="steps">' + "".join(parts) + "</div>"


def _window_html(windows: list[dict[str, Any]]) -> str:
    rows = []
    for window in windows:
        segments = "".join(f'<span class="segment {_esc(window.get("kind"))}" style="left:{segment["left"]}%;width:{segment["width"]}%"></span>' for segment in _list(window.get("segments")))
        rows.append(f'<div class="window-row"><span class="mini">{_esc(window.get("label"))}</span><span class="track">{segments}</span></div>')
    return '<div class="windows" aria-label="visual plan window labels only">' + "".join(rows) + "</div>"


def _reason_html(data: dict[str, Any]) -> str:
    counts = data.get("reason_counts", {})
    rows = "".join(f"<div><span>{_esc(key)}</span><strong>{_esc(value)}</strong></div>" for key, value in _dict(counts).items())
    constraints = "".join(f'<p class="note">{_esc(item)}</p>' for item in _list(data.get("constraints_applied")))
    return (
        f'<h3>Reason-Code Summary</h3><div class="list">{rows}</div>'
        f'<h3 style="margin-top:16px">Selected Reason-Code Explanation</h3><p class="note" id="reason-code-explanation-area">{_esc(data.get("display_only_safety"))}</p>'
        f'<h3 style="margin-top:16px">Constraints Applied</h3>{constraints}'
        f'<h3 style="margin-top:16px">Degraded-Mode Explanation</h3><p class="note">{_esc(data.get("degraded_explanation"))}</p>'
    )


def _benchmark(data: dict[str, Any]) -> str:
    fields = {
        "Energy Brain expected cost": data.get("shadow_cost"),
        "baseline cost": data.get("baseline_cost"),
        "delta": data.get("delta"),
    }
    notes = "".join(f'<p class="note">{_esc(note)}</p>' for note in _list(data.get("quality_notes")))
    return _kv(fields) + notes


def _safety(data: dict[str, Any]) -> str:
    return _kv({key: value for key, value in data.items() if key != "buttons"})


def _cycle_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<p class="note">No latest cycle rows available; deterministic shadow data is active in visual panels.</p>'
    head = "".join(f"<th>{_esc(key)}</th>" for key in rows[0])
    body = "".join(f"<tr>{''.join(f'<td>{_esc(value)}</td>' for value in row.values())}</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _step_detail(step: dict[str, Any]) -> str:
    fields = {
        "step index": step.get("step"),
        "SOC %": step.get("soc_percent"),
        "battery setpoint kW": step.get("setpoint_kw"),
        "reason code": step.get("reason_code"),
        "price": step.get("price"),
        "PV forecast": step.get("pv_forecast"),
        "load forecast": step.get("load_forecast"),
        "grid estimate": step.get("grid_estimate"),
        "validation/display-only status": step.get("validity"),
    }
    return _kv(fields)


def _horizon_chart(payload: dict[str, Any]) -> str:
    points = _list(payload.get("soc_trajectory"))
    rows = _list(payload.get("planner_timeline"))
    if not points:
        return '<p class="note">SOC trajectory placeholder chart area</p>'
    width = 900
    height = 270
    pad = 30
    values = [_num(point.get("soc_percent"), 0.0) for point in points]
    reserve = _num(points[0].get("reserve_floor"), 20.0)
    lower = max(0.0, min(values + [reserve]) - 4.0)
    upper = min(100.0, max(values + [reserve]) + 4.0)
    span = max(1.0, upper - lower)
    x_step = (width - pad * 2) / max(1, len(points) - 1)
    soc_pairs = []
    pv_pairs = []
    load_pairs = []
    price_bars = []
    max_price = max([_num(row.get("price"), 0.0) for row in rows] or [1.0]) or 1.0
    for index, point in enumerate(points):
        x = pad + index * x_step
        y = pad + (upper - _num(point.get("soc_percent"), 0.0)) / span * (height - pad * 2)
        soc_pairs.append(f"{x:.1f},{y:.1f}")
        row = rows[min(index, len(rows) - 1)] if rows else {}
        pv_y = height - pad - min(1.0, _num(row.get("pv_forecast"), 0.0) / 6.0) * 54
        load_y = height - pad - min(1.0, _num(row.get("load_forecast"), 0.0) / 4.0) * 54
        pv_pairs.append(f"{x:.1f},{pv_y:.1f}")
        load_pairs.append(f"{x:.1f},{load_y:.1f}")
        bar_h = 10 + (_num(row.get("price"), 0.0) / max_price) * 58
        price_bars.append(f'<rect x="{x - 4:.1f}" y="{height - pad - bar_h:.1f}" width="8" height="{bar_h:.1f}" rx="3" fill="rgba(255,209,102,.38)"/>')
    reserve_y = pad + (upper - reserve) / span * (height - pad * 2)
    return (
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="SOC trajectory placeholder chart area">'
        f'<rect x="{pad}" y="{reserve_y:.1f}" width="{width - pad * 2}" height="{height - pad - reserve_y:.1f}" fill="rgba(242,184,75,.08)"/>'
        f'<line x1="{pad}" x2="{width-pad}" y1="{reserve_y:.1f}" y2="{reserve_y:.1f}" stroke="#f2b84b" stroke-dasharray="6 6"/>'
        f'{"".join(price_bars)}'
        f'<polyline points="{" ".join(pv_pairs)}" fill="none" stroke="#ffd166" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>'
        f'<polyline points="{" ".join(load_pairs)}" fill="none" stroke="#69a7ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>'
        f'<polyline points="{" ".join(soc_pairs)}" fill="none" stroke="#43d6a6" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<text x="{pad}" y="18" fill="#9eacb8" font-size="12">{upper:.1f}%</text>'
        f'<text x="{pad}" y="{height - 6}" fill="#9eacb8" font-size="12">{lower:.1f}%</text>'
        f'<text x="{width - 278}" y="18" fill="#9eacb8" font-size="12">SOC line · price bars · PV/load overlays · reserve band</text>'
        "</svg>"
    )


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any, fallback: float) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else fallback


def _text(value: Any, fallback: str) -> str:
    return str(value) if value not in (None, "") else fallback


def _fmt(value: Any, suffix: str = "") -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.2f}{suffix}"
    return _esc(value)


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
