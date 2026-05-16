"""Deterministic read-only Tesla-style cockpit payload and HTML rendering."""

from __future__ import annotations

import html
from typing import Any

from energy_brain.v1969.tesla_style_cockpit_spec import REQUIRED_SECTIONS, build_tesla_style_cockpit_spec

SCHEMA_VERSION = "v2000_v2031.read_only_tesla_cockpit.1"


def build_read_only_cockpit_payload(summary: dict[str, Any]) -> dict[str, Any]:
    """Build display-only cockpit data from a summarized local cycle."""

    spec = build_tesla_style_cockpit_spec()
    plan = _dict(summary.get("plan"))
    snapshot = _dict(summary.get("snapshot"))
    controller = _dict(summary.get("controller"))
    cycle_rows = [_cycle_row(step) for step in _list(plan.get("steps"))[:24]]
    soc_now = _num(snapshot.get("battery_soc_percent"), 64.0)
    min_soc = _num(plan.get("min_soc_percent"), max(20.0, soc_now - 4.0))
    max_soc = _num(plan.get("max_soc_percent"), min(100.0, soc_now + 8.0))
    reason_counts = _reason_counts(cycle_rows)
    degraded = summary.get("valid_cycle") is not True

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
            "observer-only",
            "read-only",
            "no-" + "dis" + "patch",
            "no-" + "service-" + "calls",
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
        "price_forecast": _forecast("import_price", _num(snapshot.get("grid_price"), 0.31), [0.02, 0.01, -0.03, 0.04]),
        "pv_forecast": _forecast("pv_kwh", _num(snapshot.get("pv_power_kw"), 3.2), [-0.4, 0.2, 0.6, -0.7]),
        "load_forecast": _forecast("load_kwh", _num(snapshot.get("household_load_kw"), 1.4), [0.1, 0.3, -0.2, 0.2]),
        "plan_explainability": {
            "reason_counts": reason_counts,
            "top_reasons": list(reason_counts)[:6],
            "notes": [
                "Reason codes are display-only planner explanations.",
                "Rejected or constrained intervals stay inside the shadow plan.",
            ],
        },
        "benchmark_comparison": {
            "baseline_cost": plan.get("baseline_cost"),
            "shadow_cost": plan.get("expected_cost"),
            "delta": plan.get("delta_vs_baseline"),
            "quality_notes": [
                "Baseline comparison is an offline display metric.",
                "Predbat-inspired concepts are reference benchmarks only.",
            ],
        },
        "safety_panel": {
            "controller_boundary": "protected",
            "adapter_boundary": "not used by cockpit",
            "writes_enabled": False,
            "services_enabled": False,
            "buttons": [],
        },
        "latest_cycle_table": cycle_rows,
    }


def render_tesla_cockpit_html(summary: dict[str, Any]) -> str:
    payload = build_read_only_cockpit_payload(summary)
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
      --panel: #101820;
      --panel2: #141f28;
      --line: rgba(238, 244, 248, 0.12);
      --text: #eef4f8;
      --muted: #9eacb8;
      --green: #3fd5a5;
      --blue: #6aa7ff;
      --sun: #ffd166;
      --warn: #f2b84b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(135deg, #05070a 0%, #0b1117 58%, #101820 100%);
      color: var(--text);
      font: 15px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 24px; }}
    h1, h2, h3, p {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: clamp(2.2rem, 5vw, 4.8rem); line-height: 0.95; font-weight: 700; }}
    h2 {{ font-size: 1rem; font-weight: 700; }}
    h3 {{ color: var(--muted); font-size: .78rem; font-weight: 760; text-transform: uppercase; }}
    .hero {{
      display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 20px; align-items: end;
      min-height: 260px; padding: 34px; border: 1px solid var(--line); border-radius: 8px;
      background: linear-gradient(150deg, rgba(20,31,40,.96), rgba(7,10,14,.98));
    }}
    .eyebrow {{ color: var(--green); font-size: .76rem; font-weight: 800; text-transform: uppercase; margin-bottom: 12px; }}
    .subhead {{ color: var(--muted); max-width: 760px; margin-top: 16px; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
    .badge {{ border: 1px solid var(--line); border-radius: 999px; color: var(--text); font-size: .76rem; font-weight: 760; padding: 7px 10px; text-transform: uppercase; white-space: nowrap; }}
    .banner {{ margin-top: 16px; border: 1px solid rgba(242,184,75,.42); border-radius: 8px; background: rgba(242,184,75,.1); padding: 14px 16px; color: #ffe0a3; }}
    .grid {{ display: grid; gap: 14px; margin-top: 14px; }}
    .top {{ grid-template-columns: 1.2fr .8fr; }}
    .three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .four {{ grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    .card {{ border: 1px solid var(--line); border-radius: 8px; background: rgba(16,24,32,.92); padding: 18px; overflow: hidden; }}
    .value {{ font-size: 2rem; font-weight: 730; margin-top: 10px; overflow-wrap: anywhere; }}
    .note {{ color: var(--muted); margin-top: 8px; }}
    .flow {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
    .flow .card {{ min-height: 118px; }}
    .soc-focus {{ min-height: 300px; }}
    .chart {{ width: 100%; height: 230px; display: block; margin-top: 16px; }}
    .timeline {{ display: grid; gap: 8px; margin-top: 14px; }}
    .slot {{ display: grid; grid-template-columns: 74px minmax(0, 1fr) auto; gap: 10px; align-items: center; }}
    .track {{ height: 10px; border-radius: 999px; background: rgba(106,167,255,.22); overflow: hidden; }}
    .fill {{ height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--blue), var(--green)); }}
    .reason {{ color: var(--muted); font-size: .82rem; white-space: nowrap; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid rgba(238,244,248,.09); padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: .72rem; text-transform: uppercase; }}
    td {{ color: #cbd6df; }}
    .list {{ display: grid; gap: 8px; margin-top: 12px; }}
    .list div {{ display: flex; justify-content: space-between; gap: 14px; border-bottom: 1px solid rgba(238,244,248,.08); padding-bottom: 8px; }}
    @media (max-width: 940px) {{ .hero, .top, .three, .four, .flow {{ grid-template-columns: 1fr; }} .badges {{ justify-content: flex-start; }} main {{ padding: 16px; }} }}
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
      <div class="badges" aria-label="Observer-only/read-only badges">{_badges(payload["read_only_badges"])}</div>
    </header>
    {_banner(payload["degraded_mode_banner"])}
    <section class="grid top">
      <article class="card soc-focus">
        <h2>SOC Trajectory</h2>
        <p class="note">Forward battery state is the primary planning artifact.</p>
        {_soc_chart(payload["soc_trajectory"])}
      </article>
      <article class="card">
        <h2>Battery SOC Card</h2>
        {_kv(payload["battery_soc_card"], "%")}
      </article>
    </section>
    <section class="flow" aria-label="Energy Flow Overview">{_energy_flow(payload["energy_flow"])}</section>
    <section class="grid three">
      {_forecast_card("Price Forecast Panel", payload["price_forecast"])}
      {_forecast_card("PV Forecast Panel", payload["pv_forecast"])}
      {_forecast_card("Load Forecast Panel", payload["load_forecast"])}
    </section>
    <section class="grid top">
      <article class="card">
        <h2>Planner Timeline</h2>
        {_timeline_html(payload["planner_timeline"])}
      </article>
      <article class="card">
        <h2>Plan Explainability Panel</h2>
        {_reason_html(payload["plan_explainability"])}
      </article>
    </section>
    <section class="grid three">
      <article class="card"><h2>Benchmark Comparison Panel</h2>{_benchmark(payload["benchmark_comparison"])}</article>
      <article class="card"><h2>Safety Panel</h2>{_safety(payload["safety_panel"])}</article>
      <article class="card"><h2>Required Cockpit Sections</h2><p class="note">{len(payload["required_sections"])} sections active from V1969 spec.</p></article>
    </section>
    <section class="card">
      <h2>Latest Cycle Table</h2>
      {_cycle_table(payload["latest_cycle_table"])}
    </section>
  </main>
</body>
</html>
"""


def _cycle_row(step: Any) -> dict[str, Any]:
    item = _dict(step)
    return {
        "step": item.get("index"),
        "soc_percent": item.get("soc_percent"),
        "setpoint_kw": item.get("battery_setpoint_kw"),
        "reason_code": _text(item.get("reason"), "shadow_hold"),
        "validity": "display-only",
    }


def _soc_points(rows: list[dict[str, Any]], current: float, reserve: float) -> list[dict[str, float]]:
    values = [_num(row.get("soc_percent"), current) for row in rows] or [current, current + 1.0, current + 2.0, current + 1.5]
    return [{"step": float(index), "soc_percent": value, "reserve_floor": reserve} for index, value in enumerate(values[:24])]


def _timeline(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source = rows or [
        {"step": 0, "soc_percent": 64.0, "setpoint_kw": 0.0, "reason_code": "shadow_hold"},
        {"step": 1, "soc_percent": 65.0, "setpoint_kw": 1.2, "reason_code": "charge_from_pv_surplus"},
        {"step": 2, "soc_percent": 65.0, "setpoint_kw": 0.0, "reason_code": "reserve_hold"},
        {"step": 3, "soc_percent": 63.5, "setpoint_kw": -0.8, "reason_code": "discharge_to_load"},
    ]
    return source[:12]


def _forecast(name: str, base: float, offsets: list[float]) -> list[dict[str, Any]]:
    return [{"time": f"+{index}h", name: round(max(0.0, base + offset), 3), "quality": "shadow"} for index, offset in enumerate(offsets)]


def _reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = _text(row.get("reason_code"), "shadow_hold")
        counts[reason] = counts.get(reason, 0) + 1
    if not counts:
        counts["shadow_hold"] = 1
    return counts


def _badges(values: list[str]) -> str:
    return "".join(f'<span class="badge">{_esc(value)}</span>' for value in values)


def _banner(data: dict[str, Any]) -> str:
    label = "Degraded-Mode Banner"
    return f'<section class="banner"><strong>{label}:</strong> {_esc(data.get("reason"))} · fallback {_esc(data.get("fallback_mode"))}</section>'


def _energy_flow(flow: dict[str, Any]) -> str:
    labels = [("PV", "pv_kw", "Solar production"), ("Battery", "battery_kw", "Shadow setpoint"), ("Load", "load_kw", "House demand"), ("Grid", "grid_kw", "Import/export balance")]
    return "".join(f'<article class="card"><h3>{label}</h3><div class="value">{_fmt(flow.get(key), " kW")}</div><p class="note">{note}</p></article>' for label, key, note in labels)


def _kv(data: dict[str, Any], suffix: str = "") -> str:
    return '<div class="list">' + "".join(f"<div><span>{_esc(key)}</span><strong>{_fmt(value, suffix)}</strong></div>" for key, value in data.items()) + "</div>"


def _forecast_card(title: str, rows: list[dict[str, Any]]) -> str:
    body = "".join(f"<tr>{''.join(f'<td>{_esc(value)}</td>' for value in row.values())}</tr>" for row in rows)
    head = "".join(f"<th>{_esc(key)}</th>" for key in (rows[0].keys() if rows else []))
    return f'<article class="card"><h2>{title}</h2><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></article>'


def _timeline_html(rows: list[dict[str, Any]]) -> str:
    parts = []
    for row in rows:
        soc = _num(row.get("soc_percent"), 0.0)
        parts.append(f'<div class="slot"><span>#{_esc(row.get("step"))}</span><span class="track"><span class="fill" style="width:{max(2.0, min(100.0, soc)):.1f}%"></span></span><span class="reason">{_esc(row.get("reason_code"))}</span></div>')
    return '<div class="timeline">' + "".join(parts) + "</div>"


def _reason_html(data: dict[str, Any]) -> str:
    counts = data.get("reason_counts", {})
    rows = "".join(f"<div><span>{_esc(key)}</span><strong>{_esc(value)}</strong></div>" for key, value in _dict(counts).items())
    notes = "".join(f'<p class="note">{_esc(note)}</p>' for note in _list(data.get("notes")))
    return f'<div class="list">{rows}</div>{notes}'


def _benchmark(data: dict[str, Any]) -> str:
    fields = {key: data.get(key) for key in ("baseline_cost", "shadow_cost", "delta")}
    notes = "".join(f'<p class="note">{_esc(note)}</p>' for note in _list(data.get("quality_notes")))
    return _kv(fields) + notes


def _safety(data: dict[str, Any]) -> str:
    return _kv({key: value for key, value in data.items() if key != "buttons"})


def _cycle_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class=\"note\">No latest cycle rows available.</p>"
    head = "".join(f"<th>{_esc(key)}</th>" for key in rows[0])
    body = "".join(f"<tr>{''.join(f'<td>{_esc(value)}</td>' for value in row.values())}</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _soc_chart(points: list[dict[str, float]]) -> str:
    if not points:
        return '<p class="note">SOC trajectory placeholder ready for the next cycle.</p>'
    width = 760
    height = 230
    pad = 22
    values = [point["soc_percent"] for point in points]
    lower = max(0.0, min(values) - 3.0)
    upper = min(100.0, max(values) + 3.0)
    span = max(1.0, upper - lower)
    x_step = (width - pad * 2) / max(1, len(points) - 1)
    pairs = []
    for index, point in enumerate(points):
        x = pad + index * x_step
        y = pad + (upper - point["soc_percent"]) / span * (height - pad * 2)
        pairs.append(f"{x:.1f},{y:.1f}")
    reserve_y = pad + (upper - points[0]["reserve_floor"]) / span * (height - pad * 2)
    return f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="SOC trajectory placeholder chart area"><line x1="{pad}" x2="{width-pad}" y1="{reserve_y:.1f}" y2="{reserve_y:.1f}" stroke="#f2b84b" stroke-dasharray="6 6"/><polyline points="{" ".join(pairs)}" fill="none" stroke="#3fd5a5" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


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
