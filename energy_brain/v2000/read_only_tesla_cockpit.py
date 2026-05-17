"""Deterministic read-only Tesla-style cockpit payload and HTML rendering."""

from __future__ import annotations

import html
import json
from typing import Any
import math

from energy_brain.v1969.tesla_style_cockpit_spec import REQUIRED_SECTIONS, build_tesla_style_cockpit_spec

SCHEMA_VERSION = "v2064_v2095.usable_interactive_read_only_cockpit.1"


def human_action_for_step(step: dict[str, Any]) -> str:
    """Return a plain-Dutch action summary for one planner step."""

    reason = _text(step.get("reason_code") or step.get("reason"), "shadow_hold")
    setpoint = _num(step.get("setpoint_kw", step.get("battery_setpoint_kw")), 0.0)
    if reason == "charge_from_pv_surplus" or setpoint > 0.05:
        return "batterij laden met zonne-overschot"
    if reason == "max_soc_clamped_charge":
        return "laden begrenzen omdat de batterij bijna vol is"
    if reason == "max_soc_hold":
        return "batterij vol genoeg houden"
    if reason == "reserve_hold":
        return "energie bewaren als reserve"
    if reason == "baseline_compare":
        return "alleen vergelijken met een simpele basisstrategie"
    if reason == "shadow_hold":
        return "geen actie nodig"
    return "Energy Brain kijkt mee en verandert niets"


def human_reason_for_step(step: dict[str, Any]) -> str:
    """Return a plain-Dutch reason for one planner step."""

    reason = _text(step.get("reason_code") or step.get("reason"), "shadow_hold")
    reasons = {
        "charge_from_pv_surplus": "Er wordt meer zonne-energie verwacht dan het huis nodig heeft. Het overschot kan in de batterij.",
        "max_soc_clamped_charge": "De batterij raakt bijna vol. Laden wordt daarom begrensd.",
        "max_soc_hold": "De batterij is vol genoeg. Energy Brain houdt hem vast en voorkomt overladen.",
        "reserve_hold": "Energy Brain bewaart energie als reserve.",
        "baseline_compare": "Dit is alleen een vergelijking met een simpele basisstrategie.",
        "shadow_hold": "Er is geen duidelijke betere actie of de data is alleen voorbeeld-/schaduwdata.",
        "hold": "Er is nu geen duidelijke actie nodig. Energy Brain blijft meekijken.",
    }
    return reasons.get(reason, reasons["shadow_hold"])


def human_safety_summary() -> list[str]:
    return [
        "Ja. Deze cockpit stuurt niets aan.",
        "Geen service calls.",
        "Geen dispatch.",
        "Geen batterijcommando.",
        "Alleen lezen en uitleggen.",
    ]


def human_chart_legend() -> list[str]:
    return [
        "Groene lijn = verwachte batterijvulling.",
        "Gele balkjes = stroomprijs.",
        "Blauwe/geelachtige lijnen = verwachte zon en verbruik.",
        "Onderste gele lijn = reservegrens.",
        "Rode streep = maximale batterijgrens.",
        "Gekleurde vlakken = perioden waarin Energy Brain iets zou overwegen.",
    ]



def human_step_time_label(index: int) -> str:
    """Return a human-friendly step time label for visible UI text."""
    try:
        step = int(index)
    except (TypeError, ValueError):
        step = 0
    if step <= 0:
        return "nu"
    if step == 1:
        return "over ongeveer 1 uur"
    return f"over ongeveer {step} uur"


def human_next_step_sentence(payload: dict) -> str:
    """Return a short Dutch next-step sentence without technical planner wording."""
    plain = payload.get("plain_planner") if isinstance(payload, dict) else {}
    if not isinstance(plain, dict):
        plain = {}

    sections = plain.get("plan_card_sections") or []
    first = sections[0] if sections and isinstance(sections[0], dict) else {}
    action = str(first.get("action") or plain.get("meaning", {}).get("wat") or "").strip().lower()

    if "laden" in action and "zon" in action:
        step = "laden met zonne-overschot"
    elif "laden" in action:
        step = "laden"
    elif "ontladen" in action or "huisverbruik" in action or "batterij gebruiken" in action:
        step = "de batterij gebruiken voor huisverbruik"
    elif "reserve" in action:
        step = "reserve bewaren"
    elif "vasthouden" in action or "niets" in action or not action:
        step = "niets veranderen"
    else:
        step = action

    return f"Energy Brain kijkt mee. De volgende logische stap is {step}. Er wordt niets aangestuurd."



def plain_window_label(reason_or_kind: str) -> str:
    value = _text(reason_or_kind, "hold").lower()
    if value in ("charge", "charge_from_pv_surplus") or "charge_from_pv" in value:
        return "Laden met zon"
    if value in ("clamp", "max_soc_clamped_charge") or "clamp" in value:
        return "Bijna vol, laden begrensd"
    if value in ("baseline", "baseline_compare") or "baseline" in value:
        return "Vergelijking met simpel plan"
    if value in ("hold", "max_soc_hold", "reserve_hold", "shadow_hold") or "hold" in value:
        return "Vasthouden"
    return "Vasthouden"


def plain_step_summary(step: dict[str, Any]) -> dict[str, str]:
    reason = _text(step.get("reason_code") or step.get("reason"), "shadow_hold")
    label = plain_window_label(reason)
    soc = _fmt_plain(_num(step.get("soc_percent"), 0.0))
    pv = _fmt_plain(_num(step.get("pv_forecast"), 0.0))
    load = _fmt_plain(_num(step.get("load_forecast"), 0.0))
    return {
        "wat": label,
        "waarom": human_reason_for_step({"reason_code": reason}),
        "huis": f"De batterij staat rond {soc}%. Verwachte zon is {pv} kW en verwacht huisverbruik is {load} kW.",
        "stuurt": "Nee, alleen meekijken.",
    }


def plain_daypart_plan(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    usable = rows if rows else []
    picks = [("Nu", 0), ("Straks", 2), ("Vanavond", 12), ("Morgen", 20)]
    plan = []
    for label, index in picks:
        step = usable[min(index, len(usable) - 1)] if usable else {}
        summary = plain_step_summary(step)
        plan.append(
            {
                "label": label,
                "summary": summary["wat"],
                "why": summary["waarom"],
                "home": summary["huis"],
            }
        )
    return plan


def plain_cost_comparison(payload: dict[str, Any]) -> dict[str, str]:
    data = _dict(payload.get("benchmark_comparison"))
    energy_brain = data.get("shadow_cost")
    baseline = data.get("baseline_cost")
    if not isinstance(energy_brain, (int, float)) or isinstance(energy_brain, bool):
        return {
            "energy_brain": "Nog onvoldoende echte kostendata.",
            "baseline": "Simpele basisstrategie ontbreekt.",
            "difference": "Nog onvoldoende echte kostendata; dit is een schaduwvergelijking.",
        }
    if not isinstance(baseline, (int, float)) or isinstance(baseline, bool):
        return {
            "energy_brain": f"Energy Brain verwachting: ongeveer EUR {_fmt_money(energy_brain)}.",
            "baseline": "Simpele basisstrategie ontbreekt.",
            "difference": "Nog onvoldoende echte kostendata; dit is een schaduwvergelijking.",
        }
    difference = round(float(baseline) - float(energy_brain), 2)
    direction = "beter" if difference >= 0 else "slechter"
    return {
        "energy_brain": f"Energy Brain verwachting: ongeveer EUR {_fmt_money(energy_brain)}.",
        "baseline": f"Simpele basisstrategie: ongeveer EUR {_fmt_money(baseline)}.",
        "difference": f"Energy Brain verwacht ongeveer EUR {_fmt_money(abs(difference))} {direction} dan de simpele basislijn.",
    }


def plain_scenario_cards(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows = _list(payload.get("planner_timeline"))
    battery = _dict(payload.get("battery_soc_card"))
    current = _num(battery.get("soc_percent"), 64.0)
    end_soc = _num((rows[-1] if rows else {}).get("soc_percent"), current)
    return [
        {
            "title": "Normaal",
            "value": f"Eindigt rond {_fmt_plain(end_soc)}% batterijvulling.",
            "note": "Schaduw/voorbeeld op basis van de huidige planning.",
        },
        {
            "title": "Minder zon",
            "value": f"Eindigt grofweg rond {_fmt_plain(max(0.0, end_soc - 6.0))}%.",
            "note": "Voorbeeldscenario: minder zonne-opwek dan verwacht.",
        },
        {
            "title": "Meer verbruik",
            "value": f"Eindigt grofweg rond {_fmt_plain(max(0.0, end_soc - 4.0))}%.",
            "note": "Voorbeeldscenario: het huis gebruikt meer stroom.",
        },
    ]


def plain_predbat_reference_note() -> str:
    return (
        "Net als Predbat kijkt Energy Brain vooruit naar batterijvulling, zon, verbruik en prijs. "
        "Energy Brain gebruikt Predbat alleen als voorbeeld/benchmark en draait zelfstandig."
    )


def plan_card_section_for_step(label: str, step: dict[str, Any]) -> dict[str, str]:
    reason = _text(step.get("reason_code") or step.get("reason"), "shadow_hold")
    return {
        "label": _text(label, "Nu"),
        "action": plain_window_label(reason),
        "reason": _short_household_reason(reason),
        "impact": _household_impact(step),
        "safety": "Alleen meekijken",
    }


def plan_card_sections(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows = _list(payload.get("planner_timeline"))
    picks = [("Nu", 0), ("Straks", 2), ("Vanavond", 12), ("Morgen", 20)]
    sections = []
    for label, index in picks:
        step = rows[min(index, len(rows) - 1)] if rows else {}
        sections.append(plan_card_section_for_step(label, _dict(step)))
    return sections


def plan_confidence(payload: dict[str, Any]) -> dict[str, str]:
    banner = _dict(payload.get("degraded_mode_banner"))
    timeline = _list(payload.get("planner_timeline"))
    if banner.get("active") is True or any("fallback" in _text(_dict(row).get("validity"), "").lower() for row in timeline):
        return {"label": "Schaduwplanning", "explanation": "De cockpit gebruikt voorbeeld- of schaduwdata en stuurt niets aan."}
    if not timeline:
        return {"label": "Onvoldoende data", "explanation": "Er zijn nog niet genoeg plannerstappen om een dagplan te tonen."}
    if _dict(payload.get("hero_status")).get("planner_valid") is True:
        return {"label": "Betrouwbaar", "explanation": "De laatste lokale plannerdata is beschikbaar voor deze weergave."}
    return {"label": "Onvoldoende data", "explanation": "De plannerdata is nog niet volledig genoeg voor een betrouwbare uitleg."}


def today_summary(payload: dict[str, Any]) -> dict[str, str]:
    battery = _dict(payload.get("battery_soc_card"))
    flow = _dict(payload.get("energy_flow"))
    rows = _list(payload.get("planner_timeline"))
    current_soc = _num(battery.get("soc_percent"), 0.0)
    end_soc = _num(_dict(rows[-1] if rows else {}).get("soc_percent"), current_soc)
    pv = _num(flow.get("pv_kw"), 0.0)
    load = _num(flow.get("load_kw"), 0.0)
    if pv > load + 0.1:
        situation = "Er is nu meer zon dan verbruik."
    elif load > pv + 0.1:
        situation = "Het huis gebruikt nu meer dan de zon opwekt."
    else:
        situation = "Zon en verbruik zijn nu ongeveer in balans."
    confidence = plan_confidence(payload)
    return {
        "Batterij nu": f"{_fmt_plain(current_soc)}%",
        "Verwachte eindstand": f"{_fmt_plain(end_soc)}%",
        "Zon/verbruik situatie": situation,
        "Veiligheidsstatus": f"{confidence['label']} · Alleen meekijken",
    }


def _pf_float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _pf_get_number(source: dict[str, Any], keys: list[str], fallback: float = 0.0) -> float:
    for key in keys:
        if key in source:
            return _pf_float(source.get(key), fallback)
    return fallback


def powerflow_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    flow = source.get("flow") if isinstance(source.get("flow"), dict) else {}
    energy_flow = source.get("energy_flow") if isinstance(source.get("energy_flow"), dict) else {}
    summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
    battery_soc_card = source.get("battery_soc_card") if isinstance(source.get("battery_soc_card"), dict) else {}

    merged: dict[str, Any] = {}
    merged.update(source)
    merged.update(flow)
    merged.update(energy_flow)
    merged.update(summary)
    merged.update(battery_soc_card)

    pv_kw = _pf_get_number(merged, ["pv_kw", "solar_kw", "pv_power_kw", "expected_pv_kw"], 0.0)
    pv_raw_kw = pv_kw
    pv_sign_normalized = pv_raw_kw < -0.05
    if pv_sign_normalized:
        pv_kw = abs(pv_raw_kw)
    load_kw = _pf_get_number(merged, ["load_kw", "house_kw", "household_load_kw", "expected_load_kw"], 0.0)
    battery_kw = _pf_get_number(merged, ["battery_kw", "battery_setpoint_kw", "battery_power_kw", "planned_battery_kw"], 0.0)
    grid_raw_kw = _pf_get_number(merged, ["grid_kw", "grid_balance_kw", "net_kw", "estimated_grid_kw"], load_kw - pv_kw)

    # Display-only physical balance guard.
    # Convention used by this cockpit:
    #   battery_kw > 0  => battery charging, extra demand
    #   battery_kw < 0  => battery discharging, helps the house
    #   grid_kw > 0     => import from grid
    #   grid_kw < 0     => export to grid
    #
    # Expected grid = house load + battery charging - PV - battery discharging.
    charge_kw = max(battery_kw, 0.0)
    discharge_kw = max(-battery_kw, 0.0)
    grid_balanced_kw = load_kw + charge_kw - pv_kw - discharge_kw
    grid_balance_delta_kw = grid_raw_kw - grid_balanced_kw

    # Display-only correction threshold:
    # - ignore tiny meter jitter below roughly 80 W
    # - still correct small-load contradictions, e.g. house 0.3 kW + battery -0.3 kW
    #   should not also show 0.3 kW grid import.
    balance_reference_kw = max(abs(load_kw), abs(pv_kw), abs(battery_kw), abs(grid_raw_kw), 0.0)
    grid_balance_threshold_kw = max(0.08, min(0.35, balance_reference_kw * 0.20))
    grid_balance_corrected = abs(grid_balance_delta_kw) > grid_balance_threshold_kw

    grid_kw = grid_balanced_kw if grid_balance_corrected else grid_raw_kw
    soc = _pf_get_number(merged, ["soc_percent", "battery_soc_percent", "battery_soc"], 0.0)

    quality = "live/schaduwdata"
    if not source:
        quality = "schaduwdata"
    elif abs(pv_kw) < 0.001 and abs(load_kw) < 0.001:
        quality = "beperkte data"

    planner_soc = None
    timeline = source.get("planner_timeline") or source.get("latest_cycle_table") or []
    if isinstance(timeline, list) and timeline:
        first_step = timeline[0] if isinstance(timeline[0], dict) else {}
        planner_soc = _pf_float(first_step.get("soc_percent"), soc)

    quality_notes = []
    if pv_sign_normalized:
        quality_notes.append("PV teken genormaliseerd")
    if grid_balance_corrected:
        quality_notes.append("netwaarde gebalanceerd voor weergave")
    if quality_notes:
        quality = f"{quality} · " + " · ".join(quality_notes)

    return {
        "pv_kw": round(pv_kw, 1),
        "pv_raw_kw": round(pv_raw_kw, 1),
        "pv_sign_normalized": bool(pv_sign_normalized),
        "load_kw": round(load_kw, 1),
        "battery_kw": round(battery_kw, 1),
        "grid_kw": round(grid_kw, 1),
        "grid_raw_kw": round(grid_raw_kw, 1),
        "grid_balanced_kw": round(grid_balanced_kw, 1),
        "grid_balance_delta_kw": round(grid_balance_delta_kw, 1),
        "grid_balance_threshold_kw": round(grid_balance_threshold_kw, 2),
        "grid_balance_corrected": bool(grid_balance_corrected),
        "battery_soc_percent": round(soc),
        "battery_soc_live_percent": round(soc, 1),
        "planner_step_soc_percent": round(planner_soc, 1) if planner_soc is not None else None,
        "data_quality": quality,
        "read_only": True,
        "control_allowed": False,
    }


def powerflow_edges(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    snap = snapshot if isinstance(snapshot, dict) else {}
    pv_kw = _pf_float(snap.get("pv_kw"), 0.0)
    load_kw = _pf_float(snap.get("load_kw"), 0.0)
    battery_kw = _pf_float(snap.get("battery_kw"), 0.0)
    grid_kw = _pf_float(snap.get("grid_kw"), 0.0)

    edges: list[dict[str, Any]] = []

    if pv_kw > 0.05:
        edges.append({
            "source": "Zon",
            "target": "Huis",
            "value_kw": round(min(pv_kw, max(load_kw, 0.0)), 1),
            "direction": "zon_naar_huis",
            "label": "Zon naar huis",
            "active": True,
        })

    surplus = pv_kw - load_kw
    if surplus > 0.05 and battery_kw > 0.05:
        edges.append({
            "source": "Zon",
            "target": "Batterij",
            "value_kw": round(min(surplus, battery_kw), 1),
            "direction": "zon_naar_batterij",
            "label": "Overschot naar batterij",
            "active": True,
        })

    if battery_kw < -0.05:
        edges.append({
            "source": "Batterij",
            "target": "Huis",
            "value_kw": round(abs(battery_kw), 1),
            "direction": "batterij_naar_huis",
            "label": "Batterij helpt huis",
            "active": True,
        })

    if grid_kw > 0.05:
        edges.append({
            "source": "Net",
            "target": "Huis",
            "value_kw": round(grid_kw, 1),
            "direction": "net_import",
            "label": "Import uit net",
            "active": True,
        })
    elif grid_kw < -0.05:
        edges.append({
            "source": "Huis",
            "target": "Net",
            "value_kw": round(abs(grid_kw), 1),
            "direction": "net_export",
            "label": "Export naar net",
            "active": True,
        })

    if not edges:
        edges.append({
            "source": "Energy Brain",
            "target": "Huis",
            "value_kw": 0.0,
            "direction": "geen_duidelijke_stroomrichting",
            "label": "Geen duidelijke stroomrichting",
            "active": False,
        })

    return edges


def powerflow_explanation(snapshot: dict[str, Any], edges: list[dict[str, Any]]) -> str:
    active = [edge for edge in edges if isinstance(edge, dict) and edge.get("active")]
    labels = " ".join(str(edge.get("label", "")) for edge in active)

    if not active:
        return "Er is nog niet genoeg duidelijke data om de stroomrichting betrouwbaar te tonen."
    if "Overschot" in labels:
        return "Er lijkt zonne-overschot te zijn. Een deel kan richting batterij."
    if "Import" in labels:
        return "Het huis gebruikt meer dan zon en batterij nu leveren. Het net helpt mee."
    if "Export" in labels:
        return "Er lijkt stroom over te zijn. Die gaat richting het net."
    if "Batterij" in labels:
        return "De batterij helpt mee om het huis te voeden."
    return "Energy Brain toont de actuele stroomrichting als read-only weergave."


def _pf_kw(value: Any) -> str:
    return f"{_pf_float(value, 0.0):.1f} kW"


def powerflow_plain_status(snapshot: dict[str, Any]) -> dict[str, str]:
    snap = snapshot if isinstance(snapshot, dict) else {}
    pv_kw = _pf_float(snap.get("pv_kw"), 0.0)
    load_kw = _pf_float(snap.get("load_kw"), 0.0)
    battery_kw = _pf_float(snap.get("battery_kw"), 0.0)
    grid_kw = _pf_float(snap.get("grid_kw"), 0.0)
    live_soc = _pf_float(snap.get("battery_soc_live_percent", snap.get("battery_soc_percent")), 0.0)
    planner_soc = snap.get("planner_step_soc_percent")

    if battery_kw > 0.05:
        battery_text = f"Batterij wordt geladen met {_pf_kw(battery_kw)}."
        battery_badge = f"Laden: {_pf_kw(battery_kw)}"
    elif battery_kw < -0.05:
        battery_text = f"Batterij helpt het huis met {_pf_kw(abs(battery_kw))}."
        battery_badge = f"Helpt huis: {_pf_kw(abs(battery_kw))}"
    else:
        battery_text = "Batterij staat praktisch stil."
        battery_badge = "Batterij stil"

    if grid_kw > 0.05:
        grid_text = f"Het net vult nog {_pf_kw(grid_kw)} bij."
        grid_badge = f"Net vult bij: {_pf_kw(grid_kw)}"
    elif grid_kw < -0.05:
        grid_text = f"Er gaat {_pf_kw(abs(grid_kw))} terug naar het net."
        grid_badge = f"Teruglevering: {_pf_kw(abs(grid_kw))}"
    else:
        grid_text = "Er is bijna geen netverbruik of teruglevering."
        grid_badge = "Net bijna nul"

    solar_text = f"Zon levert {_pf_kw(pv_kw)}."
    if bool(snap.get("pv_sign_normalized")):
        solar_text += " PV-teken is genormaliseerd."

    if bool(snap.get("grid_balance_corrected")):
        grid_text += " De ruwe netwaarde paste niet bij zon, huis en batterij; daarom toont de cockpit de gebalanceerde weergave."
        grid_badge += " · gebalanceerd"
    house_text = f"Huis gebruikt {_pf_kw(load_kw)}."

    if isinstance(planner_soc, (int, float)) and abs(float(planner_soc) - live_soc) >= 1.0:
        soc_text = f"Batterij nu {live_soc:.1f}%. Planner stap 0 rekent met {float(planner_soc):.1f}%."
    else:
        soc_text = f"Batterij nu {live_soc:.1f}%."

    return {
        "headline": f"{house_text} {solar_text} {battery_text} {grid_text}",
        "solar": solar_text,
        "house": house_text,
        "battery": battery_text,
        "grid": grid_text,
        "soc": soc_text,
        "battery_badge": battery_badge,
        "grid_badge": grid_badge,
    }




def _pf_clamp01(value: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def _pf_polar(cx: float, cy: float, radius: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    return (
        cx + radius * math.cos(angle_rad),
        cy + radius * math.sin(angle_rad),
    )


def _pf_arc_path(cx: float, cy: float, radius: float, start_angle: float, sweep_angle: float) -> str:
    sweep = max(0.0, float(sweep_angle))
    if sweep <= 0.0:
        return ""
    end_angle = start_angle + sweep
    start = _pf_polar(cx, cy, radius, start_angle)
    end = _pf_polar(cx, cy, radius, end_angle)
    large_arc = 1 if sweep > 180 else 0
    return (
        f"M {start[0]:.2f} {start[1]:.2f} "
        f"A {radius:.2f} {radius:.2f} 0 {large_arc} 1 {end[0]:.2f} {end[1]:.2f}"
    )


def _pf_flow_breakdown(snapshot: dict[str, Any]) -> dict[str, float]:
    pv = max(_pf_float(snapshot.get("pv_kw"), 0.0), 0.0)
    load = max(_pf_float(snapshot.get("load_kw"), 0.0), 0.0)
    battery = _pf_float(snapshot.get("battery_kw"), 0.0)
    grid = _pf_float(snapshot.get("grid_kw"), 0.0)

    solar_to_home = min(pv, load)
    remaining_load = max(load - solar_to_home, 0.0)

    battery_to_home = min(max(-battery, 0.0), remaining_load)
    remaining_load = max(remaining_load - battery_to_home, 0.0)

    grid_to_home = min(max(grid, 0.0), remaining_load)
    remaining_load = max(remaining_load - grid_to_home, 0.0)

    solar_surplus = max(pv - solar_to_home, 0.0)
    solar_to_battery = min(max(battery, 0.0), solar_surplus)
    solar_surplus = max(solar_surplus - solar_to_battery, 0.0)

    solar_to_grid = min(max(-grid, 0.0), solar_surplus)

    return {
        "pv": pv,
        "load": load,
        "battery": battery,
        "grid": grid,
        "solar_to_home": solar_to_home,
        "battery_to_home": battery_to_home,
        "grid_to_home": grid_to_home,
        "solar_to_battery": solar_to_battery,
        "solar_to_grid": solar_to_grid,
    }


def _pf_ring_segments(
    cx: float,
    cy: float,
    radius: float,
    node_name: str,
    segments: list[tuple[str, float]],
    start_angle: float = -90.0,
    gap_deg: float = 3.0,
) -> str:
    parts: list[str] = []
    cursor = start_angle

    for source_name, fraction in segments:
        frac = _pf_clamp01(fraction)
        if frac <= 0.0:
            continue
        sweep_full = frac * 360.0
        sweep_visible = max(sweep_full - gap_deg, 0.0)
        arc = _pf_arc_path(cx, cy, radius, cursor, sweep_visible)
        if arc:
            parts.append(
                f'<path class="pf-ring-segment pf-ring-{source_name}" '
                f'data-node="{_esc(node_name)}" data-source="{_esc(source_name)}" '
                f'd="{arc}" />'
            )
        cursor += sweep_full

    return "".join(parts)


def _pf_house_ring_segments(snapshot: dict[str, Any]) -> list[tuple[str, float]]:
    flow = _pf_flow_breakdown(snapshot)
    load = flow["load"]
    if load <= 0.0:
        return []

    solar_frac = flow["solar_to_home"] / load
    battery_frac = flow["battery_to_home"] / load
    grid_frac = flow["grid_to_home"] / load
    other_frac = max(0.0, 1.0 - solar_frac - battery_frac - grid_frac)

    segments: list[tuple[str, float]] = []
    if solar_frac > 0:
        segments.append(("solar", solar_frac))
    if battery_frac > 0:
        segments.append(("battery", battery_frac))
    if grid_frac > 0:
        segments.append(("grid", grid_frac))
    if other_frac > 0:
        segments.append(("home", other_frac))
    return segments or [("home", 1.0)]


def _pf_battery_soc_segments(snapshot: dict[str, Any]) -> list[tuple[str, float]]:
    soc = _pf_float(snapshot.get("battery_soc_live_percent", snapshot.get("battery_soc_percent", 0.0)), 0.0)
    return [("battery", _pf_clamp01(soc / 100.0))]


def _pf_solar_segments(snapshot: dict[str, Any]) -> list[tuple[str, float]]:
    pv = max(_pf_float(snapshot.get("pv_kw"), 0.0), 0.0)
    if pv <= 0.0:
        return []
    return [("solar", 1.0)]


def _pf_grid_segments(snapshot: dict[str, Any]) -> list[tuple[str, float]]:
    grid = abs(_pf_float(snapshot.get("grid_kw"), 0.0))
    if grid <= 0.02:
        return []
    return [("grid", 1.0)]


def _pf_node_circle(
    cx: float,
    cy: float,
    label: str,
    value: str,
    node_name: str,
    base_ring_class: str,
    segments_html: str,
) -> str:
    return f'''
    <g class="pf-node-circle pf-node-{_esc(node_name)}" data-node="{_esc(node_name)}">
      <circle class="pf-ring-base {base_ring_class}" cx="{cx}" cy="{cy}" r="66"/>
      {segments_html}
      <circle class="pf-core" cx="{cx}" cy="{cy}" r="56"/>
      <text class="pf-node-label" x="{cx}" y="{cy - 9}">{_esc(label)}</text>
      <text class="pf-node-value" x="{cx}" y="{cy + 20}">{_esc(value)}</text>
    </g>
    '''


def render_powerflow_svg(snapshot: dict[str, Any], edges: list[dict[str, Any]]) -> str:
    snap = snapshot if isinstance(snapshot, dict) else {}
    edge_list = edges if isinstance(edges, list) else []
    plain = powerflow_plain_status(snap)

    path_map = {
        "zon_naar_huis": "M 380 178 C 418 190, 468 214, 512 236",
        "zon_naar_batterij": "M 368 178 C 368 232, 368 284, 368 332",
        "batterij_naar_huis": "M 392 332 C 430 326, 476 292, 512 264",
        "net_import": "M 248 236 C 330 236, 430 236, 512 236",
        "net_export": "M 512 264 C 430 264, 330 264, 248 264",
    }

    paths: list[str] = []
    dots: list[str] = []

    flow = _pf_flow_breakdown(snap)
    route_order = [
        "zon_naar_huis",
        "zon_naar_batterij",
        "batterij_naar_huis",
        "net_import",
        "net_export",
    ]
    route_power = {
        "zon_naar_huis": flow.get("solar_to_home", 0.0),
        "zon_naar_batterij": flow.get("solar_to_battery", 0.0),
        "batterij_naar_huis": flow.get("battery_to_home", 0.0),
        "net_import": flow.get("grid_to_home", 0.0),
        "net_export": flow.get("solar_to_grid", 0.0),
    }
    edge_by_direction = {
        str(edge.get("direction", "geen_duidelijke_stroomrichting")): edge
        for edge in edge_list
        if isinstance(edge, dict)
    }

    for idx, direction in enumerate(route_order):
        edge = edge_by_direction.get(direction, {})
        path_id = f"pf-path-{idx}"
        d = path_map[direction]
        physically_active = max(_pf_float(route_power.get(direction, 0.0), 0.0), 0.0) > 0.02
        edge_active = bool(edge.get("active", physically_active))
        active = edge_active and physically_active
        cls = f"pf-edge pf-edge-{direction} active" if active else f"pf-edge pf-edge-{direction} idle"
        paths.append(f'<path id="{path_id}" class="{cls}" d="{d}" />')
        if active:
            dots.append(
                f'<circle class="pf-dot" r="2.1">'
                f'<animateMotion dur="2.8s" repeatCount="indefinite">'
                f'<mpath href="#{path_id}" />'
                f'</animateMotion></circle>'
            )

    live_soc = snap.get("battery_soc_live_percent", snap.get("battery_soc_percent", 0))
    node_soc = snap.get("battery_soc_percent", live_soc)

    sun_segments = _pf_ring_segments(380, 110, 66, "solar", _pf_solar_segments(snap))
    house_segments = _pf_ring_segments(580, 250, 66, "house", _pf_house_ring_segments(snap))
    battery_segments = _pf_ring_segments(380, 390, 66, "battery", _pf_battery_soc_segments(snap))
    grid_segments = _pf_ring_segments(180, 250, 66, "grid", _pf_grid_segments(snap))

    return f'''<article class="powerflow-panel human-card compact-powerflow ha-powerflow-large" data-read-only="true">
  <div class="powerflow-head">
    <div>
      <p class="eyebrow">Alleen meekijken - Geen aansturing</p>
      <h2>Energy Flow nu</h2>
      <p>Dit is alleen een weergave. Energy Brain stuurt niets aan. Waar komt de stroom nu vandaan en waar gaat die heen?</p>
    </div>
    <div class="powerflow-quality">Stroomrichting - {_esc(snap.get("data_quality", "schaduwdata"))}</div>
  </div>

  <div class="powerflow-plain">
    <strong>{_esc(plain["headline"])}</strong>
    <span>{_esc(plain["soc"])}</span>
  </div>

  <svg class="powerflow-svg compact ha-flow" viewBox="0 0 760 560" role="img" aria-label="Read-only Energy Brain powerflow">
    <g class="pf-cross">
      <line x1="380" y1="176" x2="380" y2="390"></line>
      <line x1="180" y1="250" x2="580" y2="250"></line>
      <circle cx="380" cy="250" r="6"></circle>
    </g>

    <g class="pf-lines">{''.join(paths)}{''.join(dots)}</g>

    {_pf_node_circle(380, 110, "Zon", _pf_kw(snap.get("pv_kw", 0.0)), "solar", "pf-ring-solar-base", sun_segments)}
    {_pf_node_circle(180, 250, "Net", _pf_kw(abs(_pf_float(snap.get("grid_kw"), 0.0))), "grid", "pf-ring-grid-base", grid_segments)}
    {_pf_node_circle(580, 250, "Huis", _pf_kw(snap.get("load_kw", 0.0)), "house", "pf-ring-home-base", house_segments)}
    {_pf_node_circle(380, 390, "Batterij", f"{_esc(node_soc)}% nu", "battery", "pf-ring-battery-base", battery_segments)}
  </svg>

  <div class="powerflow-summary-grid">
    <div class="pf-summary pf-summary-solar"><span>Zon</span><strong>{_pf_kw(snap.get("pv_kw", 0.0))}</strong><small>naar huis of batterij</small></div>
    <div class="pf-summary pf-summary-home"><span>Huis</span><strong>{_pf_kw(snap.get("load_kw", 0.0))}</strong><small>actueel verbruik</small></div>
    <div class="pf-summary pf-summary-battery"><span>Batterij</span><strong>{_esc(plain["battery_badge"])}</strong><small>{_esc(plain["soc"])}</small></div>
    <div class="pf-summary pf-summary-grid"><span>Net</span><strong>{_esc(plain["grid_badge"])}</strong><small>import of teruglevering</small></div>
  </div>

  <p class="powerflow-explain">{_esc(powerflow_explanation(snap, edge_list))}</p>
</article>'''


def render_powerflow_panel(payload: dict[str, Any]) -> str:
    snapshot = powerflow_snapshot(payload)
    return render_powerflow_svg(snapshot, powerflow_edges(snapshot))

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
    selected_step = cycle_rows[0] if cycle_rows else {}
    next_step = _next_interesting_step(cycle_rows)
    next_step_index = int(_num(next_step.get("step"), 0.0)) if next_step else 0

    payload = {
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
            "Alleen meekijken",
            "Geen aansturing",
            "Veilig",
            "Schaduwplanning",
        ],
        "degraded_mode_banner": {
            "active": degraded,
            "reason": "No valid local cycle available" if degraded else "Inputs currently usable for display",
            "fallback_mode": "deterministic shadow sample" if degraded else "latest local cycle",
            "missing_source": "latest local planner cycle" if degraded else "none",
            "explanation": (
                "Values shown below are display fallback values because the latest local planner cycle is missing or invalid."
                if degraded
                else "Values shown below come from the latest local display cycle."
            ),
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
        "human_summary": {
            "current_state": [
                "Energy Brain kijkt alleen mee.",
                "Er wordt niets aangestuurd.",
                f"De batterij staat rond {_fmt_plain(soc_now)}%.",
                (
                    "Er is nu ongeveer "
                    f"{_fmt_plain(_num(snapshot.get('pv_power_kw'), 3.2))} kW zonne-opwek, "
                    f"{_fmt_plain(_num(snapshot.get('household_load_kw'), 1.4))} kW huisverbruik en "
                    f"{_fmt_plain(round(_num(snapshot.get('household_load_kw'), 1.4) - _num(snapshot.get('pv_power_kw'), 3.2), 2))} kW netbalans."
                ),
            ],
            "next_step": _human_next_step(next_step, next_step_index),
            "next_step_action": human_action_for_step(next_step),
            "why": human_reason_for_step(next_step),
            "safety": human_safety_summary(),
            "chart_legend": human_chart_legend(),
            "selected_step_heading": f"Stap #{_text(selected_step.get('step'), '0')} · {human_step_time_label(selected_step.get('step', 0))}",
            "selected_step_advice": f"Advies: {human_action_for_step(selected_step)}",
            "selected_step_why": f"Waarom: {_human_reason_fragment(selected_step)}",
        },
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
            "human_reason_explanations": _human_reason_explanations(),
        },
        "benchmark_comparison": {
            "baseline_cost": plan.get("baseline_cost"),
            "shadow_cost": plan.get("expected_cost"),
            "delta": plan.get("delta_vs_baseline"),
            "quality_notes": [
                "Energy Brain expected cost is compared with a baseline display metric.",
                "Predbat-inspired conceptual comparison is benchmark/reference only, not a runtime dependency.",
                "These windows are conceptual comparison labels.",
                "Energy Brain does not depend on Predbat at runtime.",
                "No commands are sent from this cockpit.",
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
    payload["plain_planner"] = {
        "short": (
            "Energy Brain kijkt mee. De volgende logische stap is "
            f"{human_action_for_step(next_step)}, maar er wordt niets aangestuurd."
        ),
        "meaning": plain_step_summary(next_step),
        "plan_card_sections": plan_card_sections(payload),
        "confidence": plan_confidence(payload),
        "today_summary": today_summary(payload),
        "daypart_plan": plain_daypart_plan(cycle_rows),
        "cost_comparison": plain_cost_comparison(payload),
        "scenarios": plain_scenario_cards(payload),
        "actual_vs_predicted": {
            "title": "Voorspelling vs werkelijkheid",
            "status": "Nog niet genoeg meetdata om dit betrouwbaar te beoordelen.",
        },
        "predbat_reference": plain_predbat_reference_note(),
        "what_to_do": (
            "Niets. Dit scherm is bedoeld om te controleren of de planning logisch lijkt voordat er ooit automatische aansturing komt."
        ),
    }
    return payload


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
    .tab-button {{ min-height: 38px; padding: 8px 13px; position: relative; }}
    .tab-button::after {{ content: "inspect"; color: var(--muted); font-size: .66rem; margin-left: 8px; text-transform: uppercase; }}
    .tab-button[aria-selected="true"] {{ border-color: rgba(105,167,255,.82); background: rgba(105,167,255,.24); box-shadow: inset 0 -2px 0 var(--blue); }}
    .tab-button:focus-visible, .step-button:focus-visible, .json-toggle:focus-visible {{ outline: 2px solid var(--green); outline-offset: 2px; }}
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
    .human-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 14px; }}
    .human-card {{ border: 1px solid var(--line); border-radius: 8px; background: rgba(21,31,41,.88); padding: 16px; }}
    .human-card h2 {{ font-size: 1.06rem; }}
    .human-card ul {{ margin: 12px 0 0; padding-left: 18px; color: #d9e6ef; }}
    .human-card li + li {{ margin-top: 7px; }}
    .human-card strong {{ display: block; margin-top: 12px; font-size: 1.05rem; line-height: 1.34; }}
    .powerflow-panel {{
      --pf-sun: #ffd166;
      --pf-sun-bg: rgba(255,209,102,.13);
      --pf-home: #55c7ff;
      --pf-home-bg: rgba(85,199,255,.13);
      --pf-battery: #64e38b;
      --pf-battery-bg: rgba(100,227,139,.13);
      --pf-grid: #ff9f43;
      --pf-grid-bg: rgba(255,159,67,.13);
      grid-column: 1 / -1;
      overflow: hidden;
      position: relative;
    }}
    .powerflow-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:10px; }}
    .powerflow-head h2 {{ margin:3px 0 7px; font-size:1.25rem; }}
    .powerflow-head p {{ margin:0; color:var(--muted); }}
    .powerflow-quality {{ border:1px solid var(--line); border-radius:999px; padding:8px 12px; color:#d9e6ef; white-space:nowrap; background:rgba(255,255,255,.05); }}
    .powerflow-svg {{ width:100%; min-height:260px; display:block; margin-top:6px; border-radius:18px; background:radial-gradient(circle at 50% 35%, rgba(90,160,255,.13), rgba(0,0,0,0) 42%); }}
    .pf-node circle, .pf-node rect {{ fill:rgba(16,28,38,.92); stroke:rgba(149,218,255,.42); stroke-width:2; }}
    .pf-node text {{ fill:#edf7fb; font-size:22px; font-weight:800; text-anchor:middle; dominant-baseline:middle; }}
    .pf-node text + text {{ fill:#a9c1cf; font-size:18px; font-weight:700; }}
    .pf-sun circle {{ stroke:rgba(255,211,106,.75); }}
    .pf-battery rect {{ stroke:rgba(95,220,160,.65); }}
    .pf-grid rect {{ stroke:rgba(160,180,255,.62); }}
    .pf-edge {{ fill:none; stroke:rgba(130,150,165,.35); stroke-width:5; stroke-linecap:round; stroke-dasharray:10 12; }}
    .pf-edge.active {{ stroke:rgba(113,214,255,.75); animation:eb-flow-dash 2.8s linear infinite; }}
    .pf-edge.idle {{ stroke:rgba(130,150,165,.25); }}
    .pf-dot {{ fill:#ffffff; opacity:.95; }}
    .powerflow-labels {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 0; }}
    .pf-edge-label {{ border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:#d9e6ef; background:rgba(255,255,255,.05); }}
    .powerflow-explain {{ margin:12px 0 0; color:#d9e6ef; }}
    .compact-powerflow {{ padding:22px; }}
    .compact-powerflow .powerflow-head {{ margin-bottom:14px; }}
    .powerflow-plain {{ border:1px solid rgba(122,186,255,.18); background:rgba(255,255,255,.04); border-radius:18px; padding:14px 16px; margin:12px 0 14px; display:grid; gap:6px; }}
    .powerflow-plain strong {{ margin:0; font-size:1.02rem; color:#edf7fb; }}
    .powerflow-plain span {{ color:var(--muted); }}
    .powerflow-svg.compact {{ min-height:420px; max-height:560px; background:radial-gradient(circle at 50% 50%, rgba(90,160,255,.18), rgba(0,0,0,0) 56%); }}
    .powerflow-svg.ha-flow {{ height:clamp(420px, 68vw, 560px); }}
    .compact-powerflow .pf-node circle,
    .compact-powerflow .pf-node rect {{ filter: drop-shadow(0 12px 22px rgba(0,0,0,.22)); }}
    .pf-node.pf-sun circle {{ stroke:var(--pf-sun); fill:linear-gradient(135deg, var(--pf-sun-bg), rgba(16,28,38,.94)); filter:drop-shadow(0 0 22px rgba(255,209,102,.23)); }}
    .pf-node.pf-home rect {{ stroke:var(--pf-home); fill:rgba(20,43,58,.94); filter:drop-shadow(0 0 22px rgba(85,199,255,.20)); }}
    .pf-node.pf-battery rect {{ stroke:var(--pf-battery); fill:rgba(18,48,35,.94); filter:drop-shadow(0 0 22px rgba(100,227,139,.20)); }}
    .pf-node.pf-grid rect {{ stroke:var(--pf-grid); fill:rgba(55,37,20,.94); filter:drop-shadow(0 0 22px rgba(255,159,67,.20)); }}
    .pf-node .pf-value-pill {{ fill:rgba(7,13,18,.72); stroke-width:1.8; filter:none; }}
    .pf-node .pf-sun-pill {{ stroke:var(--pf-sun); }}
    .pf-node .pf-home-pill {{ stroke:var(--pf-home); }}
    .pf-node .pf-battery-pill {{ stroke:var(--pf-battery); }}
    .pf-node .pf-grid-pill {{ stroke:var(--pf-grid); }}
    .pf-node.pf-sun text + text {{ fill:var(--pf-sun); }}
    .pf-node.pf-home text + text {{ fill:var(--pf-home); }}
    .pf-node.pf-battery text + text {{ fill:var(--pf-battery); }}
    .pf-node.pf-grid text + text {{ fill:var(--pf-grid); }}
    .pf-edge-zon_naar_huis.active,
    .pf-edge-zon_naar_batterij.active {{ stroke:var(--pf-sun); }}
    .pf-edge-batterij_naar_huis.active {{ stroke:var(--pf-battery); }}
    .pf-edge-net_import.active,
    .pf-edge-net_export.active {{ stroke:var(--pf-grid); }}
    .compact-powerflow .pf-edge {{ stroke-width:7; stroke-dasharray:10 13; opacity:.92; }}
    .pf-backbone {{ fill:none; stroke:rgba(130,150,165,.22); stroke-width:4; stroke-linecap:round; }}
    .pf-junction {{ fill:#f7fbff; opacity:.85; filter:drop-shadow(0 0 10px rgba(255,255,255,.55)); }}
    .compact-powerflow .pf-dot {{ fill:#f7fbff; filter:drop-shadow(0 0 7px rgba(255,255,255,.8)); }}
    .powerflow-summary-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:12px; }}
    .powerflow-summary-grid div {{ border:1px solid var(--line); border-radius:16px; padding:11px 12px; background:rgba(255,255,255,.035); }}
    .powerflow-summary-grid span {{ display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; }}
    .powerflow-summary-grid strong {{ display:block; margin-top:4px; color:#edf7fb; font-size:1rem; line-height:1.25; }}
    .powerflow-summary-grid small {{ display:block; margin-top:5px; color:var(--muted); line-height:1.3; }}
    .powerflow-summary-grid .pf-summary-source {{ border-color:var(--pf-source); background:linear-gradient(135deg, var(--pf-source-bg), rgba(255,255,255,.025)); }}
    .powerflow-summary-grid .pf-summary-source strong {{ color:var(--pf-source); border:1px solid var(--pf-source); border-radius:999px; display:inline-block; padding:4px 9px; }}
    .pf-summary-sun {{ --pf-source:var(--pf-sun); --pf-source-bg:var(--pf-sun-bg); }}
    .pf-summary-home {{ --pf-source:var(--pf-home); --pf-source-bg:var(--pf-home-bg); }}
    .pf-summary-battery {{ --pf-source:var(--pf-battery); --pf-source-bg:var(--pf-battery-bg); }}
    .pf-summary-grid {{ --pf-source:var(--pf-grid); --pf-source-bg:var(--pf-grid-bg); }}
    @media (max-width: 900px) {{ .powerflow-summary-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media (max-width: 620px) {{
      .compact-powerflow {{ padding:18px; }}
      .powerflow-head {{ flex-direction:column; }}
      .powerflow-quality {{ white-space:normal; }}
      .powerflow-svg.ha-flow {{ height:430px; }}
      .pf-node text {{ font-size:24px; }}
      .pf-node text + text {{ font-size:19px; }}
      .powerflow-summary-grid div {{ padding:10px; border-radius:14px; }}
      .powerflow-summary-grid strong {{ font-size:.95rem; }}
    }}
    @keyframes eb-flow-dash {{ from {{ stroke-dashoffset:42; }} to {{ stroke-dashoffset:0; }} }}

    /* --- V2352-J HA-style segmented circular powerflow --- */
    .ha-powerflow-large .powerflow-svg.ha-flow {{
      min-height: 640px;
      max-height: none;
      background:
        radial-gradient(circle at 50% 42%, rgba(90,160,255,.18), rgba(0,0,0,0) 46%),
        linear-gradient(90deg, rgba(255,255,255,.02) 1px, transparent 1px),
        linear-gradient(0deg, rgba(255,255,255,.02) 1px, transparent 1px);
      background-size: auto, 48px 48px, 48px 48px;
      border-radius: 24px;
    }}

    .ha-powerflow-large .pf-cross line {{
      stroke: rgba(160,185,210,.18);
      stroke-width: 4;
      stroke-linecap: round;
    }}

    .ha-powerflow-large .pf-cross circle {{
      fill: rgba(235,242,249,.88);
    }}

    .ha-powerflow-large .pf-node-circle .pf-core {{
      fill: rgba(8,15,24,.96);
      stroke: rgba(255,255,255,.06);
      stroke-width: 1.5;
      filter: drop-shadow(0 10px 24px rgba(0,0,0,.28));
    }}

    .ha-powerflow-large .pf-ring-base {{
      fill: none;
      stroke-width: 11;
      opacity: .34;
    }}

    .ha-powerflow-large .pf-ring-solar-base {{ stroke: #f4c54d; }}
    .ha-powerflow-large .pf-ring-home-base {{ stroke: #4cb5ff; }}
    .ha-powerflow-large .pf-ring-battery-base {{ stroke: #5ee07a; }}
    .ha-powerflow-large .pf-ring-grid-base {{ stroke: #f39b42; }}

    .ha-powerflow-large .pf-ring-segment {{
      fill: none;
      stroke-width: 11;
      stroke-linecap: round;
      opacity: 1;
      filter: drop-shadow(0 0 7px rgba(255,255,255,.12));
    }}

    .ha-powerflow-large .pf-ring-solar {{ stroke: #f4c54d; }}
    .ha-powerflow-large .pf-ring-home {{ stroke: #4cb5ff; }}
    .ha-powerflow-large .pf-ring-battery {{ stroke: #5ee07a; }}
    .ha-powerflow-large .pf-ring-grid {{ stroke: #f39b42; }}

    .ha-powerflow-large .pf-node-label {{
      fill: #eef7ff;
      font-size: 18px;
      font-weight: 750;
      text-anchor: middle;
      dominant-baseline: middle;
    }}

    .ha-powerflow-large .pf-node-value {{
      fill: #eef7ff;
      font-size: 16px;
      font-weight: 750;
      text-anchor: middle;
      dominant-baseline: middle;
    }}

    .ha-powerflow-large .powerflow-summary-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-top: 14px;
    }}

    .ha-powerflow-large .pf-summary {{
      border-radius: 24px;
      padding: 18px 18px 16px;
      background: rgba(255,255,255,.035);
    }}

    .ha-powerflow-large .pf-summary-solar {{ border: 2px solid rgba(244,197,77,.95); }}
    .ha-powerflow-large .pf-summary-home {{ border: 2px solid rgba(76,181,255,.95); }}
    .ha-powerflow-large .pf-summary-battery {{ border: 2px solid rgba(94,224,122,.95); }}
    .ha-powerflow-large .pf-summary-grid {{ border: 2px solid rgba(243,155,66,.95); }}

    .ha-powerflow-large .pf-summary strong {{
      font-size: 1.12rem;
      line-height: 1.2;
      border: 0;
      padding: 0;
    }}

    @media (max-width: 700px) {{
      .ha-powerflow-large .powerflow-svg.ha-flow {{ min-height: 600px; }}
      .ha-powerflow-large .pf-node-label {{ font-size: 16px; }}
      .ha-powerflow-large .pf-node-value {{ font-size: 15px; }}
    }}

    @media (prefers-reduced-motion: reduce) {{ .pf-edge.active {{ animation:none; }} .pf-dot animateMotion {{ display:none; }} }}
    .plain-dashboard {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 14px; }}
    .plain-wide {{ grid-column: 1 / -1; }}
    .plan-card {{ grid-column: 1 / -1; background: linear-gradient(145deg, rgba(21,31,41,.96), rgba(8,12,16,.94)); }}
    .plan-card-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; flex-wrap: wrap; }}
    .confidence-pill {{ border: 1px solid rgba(67,214,166,.28); border-radius: 999px; color: #b7ffe5; font-size: .78rem; font-weight: 780; padding: 6px 10px; white-space: nowrap; }}
    .plan-sections {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }}
    .plan-section {{ border: 1px solid rgba(238,244,248,.1); border-radius: 8px; background: rgba(5,7,10,.26); padding: 14px; }}
    .plan-section h3 {{ color: var(--text); text-transform: none; font-size: 1rem; }}
    .plan-action {{ color: #b7ffe5; font-size: 1.05rem; font-weight: 780; margin-top: 10px; }}
    .safety-label {{ border: 1px solid rgba(67,214,166,.24); border-radius: 999px; color: #b7ffe5; display: inline-flex; font-size: .76rem; font-weight: 780; margin-top: 12px; padding: 5px 8px; }}
    .summary-list {{ display: grid; gap: 8px; margin-top: 12px; }}
    .summary-list div {{ border-bottom: 1px solid rgba(238,244,248,.08); display: flex; justify-content: space-between; gap: 14px; padding-bottom: 8px; }}
    .forecast-overview {{ display:grid; gap:14px; }}
    .forecast-hero {{ border:1px solid rgba(122,186,255,.18); background:linear-gradient(135deg, rgba(54,116,181,.16), rgba(255,255,255,.035)); border-radius:22px; padding:18px; }}
    .forecast-hero h2 {{ margin:0 0 8px; }}
    .forecast-hero p {{ margin:0; color:var(--muted); line-height:1.5; }}
    .forecast-cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .forecast-card-human {{ border:1px solid var(--line); border-radius:18px; padding:14px; background:rgba(255,255,255,.04); }}
    .forecast-card-human span {{ display:block; color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; }}
    .forecast-card-human strong {{ display:block; margin-top:6px; font-size:1.08rem; color:#edf7fb; }}
    .forecast-card-human small {{ display:block; margin-top:8px; color:var(--muted); line-height:1.35; }}
    .forecast-technical details {{ margin-top:14px; }}
    .forecast-technical summary {{ cursor:pointer; font-weight:800; color:var(--text); padding:12px 0; }}
    .forecast-technical .grid {{ margin-top:12px; }}
    @media (max-width: 1000px) {{ .forecast-cards {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
    @media (max-width: 620px) {{ .forecast-cards {{ grid-template-columns:1fr; }} }}
    .dayparts, .scenario-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }}
    .scenario-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .plain-tile {{ border: 1px solid rgba(238,244,248,.1); border-radius: 8px; background: rgba(5,7,10,.22); padding: 12px; }}
    .plain-tile h3 {{ color: var(--text); text-transform: none; font-size: .92rem; }}
    .plain-tile p {{ color: #d9e6ef; margin-top: 8px; }}
    .technical-toggle {{ margin-top: 14px; }}
    .technical-area {{ margin-top: 14px; }}
    .technical-area summary {{ cursor: pointer; color: var(--text); font-weight: 780; }}
    .technical-area[open] {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: rgba(7,10,14,.48); }}
    .chart {{ width: 100%; height: 330px; display: block; margin-top: 12px; }}
    .chart-head {{ display: flex; justify-content: space-between; gap: 14px; align-items: start; flex-wrap: wrap; }}
    .chart-title {{ font-size: 1.28rem; font-weight: 760; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .legend-item {{ align-items: center; border: 1px solid var(--line); border-radius: 999px; display: inline-flex; gap: 7px; padding: 6px 9px; color: var(--muted); font-size: .78rem; }}
    .swatch {{ width: 18px; height: 4px; border-radius: 999px; background: var(--green); }}
    .swatch.reserve {{ background: var(--warn); }}
    .swatch.max {{ background: var(--red); }}
    .swatch.price {{ background: var(--sun); }}
    .swatch.overlay {{ background: var(--blue); }}
    .swatch.charge {{ background: var(--green); }}
    .swatch.clamp {{ background: var(--warn); }}
    .chart-layout {{ display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 14px; align-items: start; }}
    .chart-explain {{ border: 1px solid var(--line); border-radius: 8px; background: rgba(21,31,41,.78); padding: 14px; margin-top: 12px; }}
    .timeline-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 14px; }}
    .steps {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }}
    .step-button {{ min-height: 84px; padding: 10px; text-align: left; box-shadow: inset 0 0 0 1px rgba(255,255,255,.02); transition: border-color .12s ease, transform .12s ease, background .12s ease; }}
    .step-button:hover {{ border-color: rgba(67,214,166,.62); transform: translateY(-1px); background: rgba(67,214,166,.09); }}
    .step-button.active {{ outline: 2px solid rgba(67,214,166,.78); background: rgba(67,214,166,.15); }}
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
    @media (max-width: 1040px) {{ .hero, .top, .timeline-grid, .chart-layout, .three, .four, .flow, .human-grid, .plain-dashboard, .plan-sections, .dayparts, .scenario-grid {{ grid-template-columns: 1fr; }} .steps {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} .inspector {{ position: static; }} }}
    @media (max-width: 620px) {{ main {{ padding: 14px; }} .hero {{ padding: 22px; }} .steps {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .window-row {{ grid-template-columns: 1fr; }} }}

  
    /* --- V2352-L obvious thin HA-style lanes --- */
    .ha-powerflow-large .pf-lines .pf-edge {{
      fill: none !important;
      stroke-width: 1.7 !important;
      stroke-linecap: round !important;
      opacity: .82 !important;
      filter: none !important;
    }}

    .ha-powerflow-large .pf-lines .pf-edge.idle {{
      opacity: .10 !important;
      stroke-dasharray: 5 13 !important;
      animation: none !important;
    }}

    .ha-powerflow-large .pf-lines .pf-edge.active {{
      opacity: .92 !important;
      stroke-dasharray: 7 12 !important;
    }}

    .ha-powerflow-large .pf-lines .pf-dot {{
      r: 2.1;
      fill: rgba(245,248,252,.96) !important;
      opacity: .90 !important;
      filter: none !important;
    }}

    .ha-powerflow-large .pf-cross line {{
      stroke-width: 2 !important;
      opacity: .55 !important;
    }}

    .ha-powerflow-large .pf-cross circle {{
      r: 4;
      opacity: .65 !important;
    }}

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
    <section id="tab-overview" class="tab-panel active" role="tabpanel" data-tab-panel="overview">
      {render_powerflow_panel(payload)}
      {_plain_planner_html(payload["plain_planner"])}
      {_human_summary_html(payload["human_summary"])}
      <div class="grid top">
        <article class="card">
          <div class="chart-head">
            <div>
              <h2 class="chart-title">Technische grafiek voor controle</h2>
              <p class="note">Niet nodig voor dagelijks gebruik.</p>
            </div>
            <span class="badge safe">read-only inspect</span>
          </div>
          <div class="legend" aria-label="Chart legend">
            <span class="legend-item"><span class="swatch"></span>Batterijvulling</span>
            <span class="legend-item"><span class="swatch reserve"></span>Reservegrens</span>
            <span class="legend-item"><span class="swatch max"></span>Maximale batterijgrens</span>
            <span class="legend-item"><span class="swatch price"></span>Stroomprijs</span>
            <span class="legend-item"><span class="swatch overlay"></span>Zon/verbruik</span>
            <span class="legend-item"><span class="swatch charge"></span>laden met zonne-overschot</span>
            <span class="legend-item"><span class="swatch clamp"></span>bijna vol / vasthouden</span>
          </div>
          <div class="chart-layout">
            {_horizon_chart(payload)}
            <aside class="chart-explain" id="chart-selected-step-panel">
              <h3>Current/selected step details</h3>
              {_chart_step_summary(payload["planner_timeline"][0] if payload["planner_timeline"] else {})}
              <p class="note">Klik op een stap om details te bekijken. The vertical marker moves to the selected step.</p>
            </aside>
          </div>
        </article>
        <article class="card soft">
          <h2>Battery SOC Card · Batterijvulling</h2>
          {_kv(payload["battery_soc_card"], "%")}
        </article>
      </div>
      <section class="flow" aria-label="Energy Flow Overview">{_energy_flow(payload["energy_flow"])}</section>
    </section>
    <section id="tab-plan" class="tab-panel" role="tabpanel" data-tab-panel="plan" data-legacy-chart-title="Batterijvulling · SOC Trajectory">
      <div class="timeline-grid">
        <article class="card">
          <h2>Planner Timeline</h2>
          <p class="mini">Legacy technical reference: SOC Trajectory · SOC trajectory · Integrated Horizon Chart · How to read this chart.</p>
          <p class="note">Klik op een stap om details te bekijken. First 24 planner steps are inspect-only selections.</p>
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
    <section id="tab-forecast" class="tab-panel" role="tabpanel" data-tab-panel="forecast">
      {_forecast_layperson_html(payload)}
    </section>
    <section id="tab-benchmark" class="tab-panel" role="tabpanel" data-tab-panel="benchmark">
      <div class="grid top">
        <article class="card">
          <h2>Benchmark Comparison Panel</h2>
          {_benchmark(payload["benchmark_comparison"])}
        </article>
        <article class="card">
          <h2>Predbat Benchmark/Reference Notice</h2>
          <p class="note">Predbat is benchmark/reference only, not runtime dependency. These windows are conceptual comparison labels. Energy Brain does not depend on Predbat at runtime. No commands are sent from this cockpit.</p>
        </article>
      </div>
    </section>
    <section id="tab-safety" class="tab-panel" role="tabpanel" data-tab-panel="safety">
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
  <script id="cockpit-payload" type="application/json">{_json_for_script_tag(payload_json)}</script>
  <script>
    const payload = JSON.parse(document.getElementById('cockpit-payload').textContent);
    const tabButtons = Array.from(document.querySelectorAll('.tab-button'));
    const panels = Array.from(document.querySelectorAll('.tab-panel'));
    tabButtons.forEach((button) => {{
      button.addEventListener('click', () => {{
        const target = button.dataset.tab;
        tabButtons.forEach((item) => item.setAttribute('aria-selected', String(item === button)));
        panels.forEach((panel) => panel.classList.toggle('active', panel.dataset.tabPanel === target));
      }});
    }});
    const detail = document.getElementById('step-detail-panel');
    const reasonMap = payload.plan_explainability.reason_explanations || {{}};
    const humanReasons = payload.plan_explainability.human_reason_explanations || {{}};
    function humanAction(step) {{
      const reason = step.reason_code || 'shadow_hold';
      const power = Number(step.setpoint_kw || 0);
      if (reason === 'charge_from_pv_surplus' || power > 0.05) return 'batterij laden met zonne-overschot';
      if (reason === 'max_soc_clamped_charge') return 'laden begrenzen omdat de batterij bijna vol is';
      if (reason === 'max_soc_hold') return 'batterij vol genoeg houden';
      if (reason === 'reserve_hold') return 'energie bewaren als reserve';
      if (reason === 'baseline_compare') return 'alleen vergelijken met een simpele basisstrategie';
      if (reason === 'shadow_hold') return 'geen actie nodig';
      return 'Energy Brain kijkt mee en verandert niets';
    }}
    function plainWindowLabel(reason) {{
      if (reason === 'charge_from_pv_surplus') return 'Laden met zon';
      if (reason === 'max_soc_clamped_charge') return 'Bijna vol, laden begrensd';
      if (reason === 'baseline_compare') return 'Vergelijking met simpel plan';
      return 'Vasthouden';
    }}
    function homeMeaning(step) {{
      return `De batterij staat rond ${{safeValue(step.soc_percent, '%')}}. Verwachte zon is ${{safeValue(step.pv_forecast)}} kW en verwacht huisverbruik is ${{safeValue(step.load_forecast)}} kW.`;
    }}
    function reasonFragment(step) {{
      const text = humanReasons[step.reason_code || 'shadow_hold'] || humanReasons.shadow_hold || 'er is geen duidelijke betere actie';
      return text.charAt(0).toLowerCase() + text.slice(1).replace(/\\.$/, '');
    }}
    function safeValue(value, suffix = '') {{
      return value === null || value === undefined || value === '' ? 'n/a' : `${{value}}${{suffix}}`;
    }}
    function showStep(index) {{
      const step = payload.planner_timeline[index] || payload.planner_timeline[0] || {{}};
      document.querySelectorAll('.step-button').forEach((item) => item.classList.toggle('active', Number(item.dataset.step) === index));
      const reason = step.reason_code || 'shadow_hold';
      const constraint = step.constraint || 'display-only planner boundary';
      detail.innerHTML = `
        <div class="list">
          <div><span>Stap</span><strong>#${{safeValue(step.step)}} · over ${{index}} uur</strong></div>
          <div><span>Wat gebeurt er?</span><strong>${{plainWindowLabel(reason)}}</strong></div>
          <div><span>Waarom?</span><strong>${{reasonFragment(step)}}</strong></div>
          <div><span>Wat betekent dit voor mijn huis?</span><strong>${{homeMeaning(step)}}</strong></div>
          <div><span>Stuurt dit iets aan?</span><strong>Nee, alleen meekijken.</strong></div>
        </div>
        <details class="technical-area">
          <summary>Technische details tonen/verbergen</summary>
        <div class="list">
          <div><span>selected step index/time</span><strong>#${{safeValue(step.step)}} / +${{index}}h</strong></div>
          <div><span>Batterijvulling (SOC %)</span><strong>${{safeValue(step.soc_percent, '%')}}</strong></div>
          <div><span>Gewenst batterijvermogen (battery setpoint kW)</span><strong>${{safeValue(step.setpoint_kw)}}</strong></div>
          <div><span>Reden (reason code)</span><strong>${{reason}}</strong></div>
          <div><span>price</span><strong>${{safeValue(step.price)}}</strong></div>
          <div><span>PV forecast</span><strong>${{safeValue(step.pv_forecast)}}</strong></div>
          <div><span>load forecast</span><strong>${{safeValue(step.load_forecast)}}</strong></div>
          <div><span>Verwachte netbalans (grid estimate)</span><strong>${{safeValue(step.grid_estimate)}}</strong></div>
          <div><span>Alleen tonen (validation/display-only status)</span><strong>${{safeValue(step.validity)}}</strong></div>
          <div><span>safety status</span><strong>${{safeValue(step.validity)}} / no dispatch</strong></div>
          <div><span>Begrenzing (constraint applied)</span><strong>${{constraint}}</strong></div>
        </div>
        <p class="note" id="selected-reason-explanation">${{reasonMap[reason] || reasonMap.shadow_hold || 'Display-only planner interval.'}}</p>
        </details>
      `;
      const chartPanel = document.getElementById('chart-selected-step-panel');
      if (chartPanel) {{
        chartPanel.innerHTML = `
          <h3>Current/selected step details</h3>
          <div class="list">
            <div><span>Stap</span><strong>#${{safeValue(step.step)}} · over ${{index}} uur</strong></div>
            <div><span>Wat gebeurt er?</span><strong>${{plainWindowLabel(reason)}}</strong></div>
            <div><span>Waarom?</span><strong>${{reasonFragment(step)}}</strong></div>
            <div><span>Wat betekent dit voor mijn huis?</span><strong>${{homeMeaning(step)}}</strong></div>
            <div><span>Stuurt dit iets aan?</span><strong>Nee, alleen meekijken.</strong></div>
          </div>
          <details class="technical-area">
            <summary>Technische details tonen/verbergen</summary>
            <div class="list">
              <div><span>step/hour</span><strong>#${{safeValue(step.step)}} / +${{index}}h</strong></div>
              <div><span>Batterijvulling (SOC)</span><strong>${{safeValue(step.soc_percent, '%')}}</strong></div>
              <div><span>Reden (reason)</span><strong>${{reason}}</strong></div>
              <div><span>Begrenzing (constraint)</span><strong>${{constraint}}</strong></div>
            </div>
            <p class="note">${{reasonMap[reason] || reasonMap.shadow_hold || 'Display-only planner interval.'}}</p>
          </details>
          <p class="note">Klik op een stap om details te bekijken. The vertical marker moves to the selected step.</p>
        `;
      }}
      const marker = document.getElementById('selected-step-marker');
      const markerLabel = document.getElementById('selected-step-marker-label');
      if (marker && marker.dataset.stepWidth) {{
        const x = Number(marker.dataset.chartPad) + index * Number(marker.dataset.stepWidth);
        marker.setAttribute('x1', String(x));
        marker.setAttribute('x2', String(x));
        if (markerLabel) {{
          markerLabel.setAttribute('x', String(x + 6));
          markerLabel.textContent = `selected step #${{safeValue(step.step)}}`;
        }}
      }}
    }}
    document.querySelectorAll('.step-button').forEach((button) => {{
      button.addEventListener('click', () => showStep(Number(button.dataset.index)));
      button.addEventListener('keydown', (event) => {{
        if (event.key === 'Enter' || event.key === ' ') {{
          event.preventDefault();
          showStep(Number(button.dataset.index));
        }}
      }});
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



def _json_for_script_tag(json_text: str) -> str:
    """Return raw JSON safe for an application/json script tag.

    Quotes must remain real JSON quotes. HTML-escaping JSON inside a script tag
    produces &quot; text and can break JSON.parse before click handlers attach.
    """
    return str(json_text).replace("</", "<\\/")

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
        "constraint": _constraint_for_reason(_text(item.get("reason"), "shadow_hold")),
    }


def _shadow_rows(current_soc: float, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    reasons = ["shadow_hold", "charge_from_pv_surplus", "reserve_hold", "max_soc_clamped_charge", "max_soc_hold", "baseline_compare"]
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
                "constraint": _constraint_for_reason(reasons[index % len(reasons)]),
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
        {"label": plain_window_label("charge"), "technical_label": "charge windows", "kind": "charge", "segments": _segments(rows, lambda row: _num(row.get("setpoint_kw"), 0.0) > 0.05)},
        {"label": plain_window_label("hold"), "technical_label": "hold windows", "kind": "hold", "segments": _segments(rows, lambda row: abs(_num(row.get("setpoint_kw"), 0.0)) <= 0.05)},
        {"label": plain_window_label("clamp"), "technical_label": "clamp/max-SOC windows", "kind": "clamp", "segments": _segments(rows, lambda row: "clamp" in _text(row.get("reason_code"), "").lower() or "max_soc" in _text(row.get("reason_code"), "").lower())},
        {"label": plain_window_label("baseline"), "technical_label": "baseline comparison windows", "kind": "baseline", "segments": _segments(rows, lambda row: "baseline" in _text(row.get("reason_code"), "").lower() or int(_num(row.get("step"), 0)) % 8 == 0)},
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


def _next_interesting_step(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        reason = _text(row.get("reason_code"), "shadow_hold")
        if reason not in ("hold", "shadow_hold", "baseline_compare") or abs(_num(row.get("setpoint_kw"), 0.0)) > 0.05:
            return row
    return rows[0] if rows else {}


def _human_next_step(step: dict[str, Any], index: int) -> str:
    if not step:
        return "Er is geen actie nodig."
    action = human_action_for_step(step)
    if action == "geen actie nodig":
        return "Er is geen actie nodig."
    if action == "batterij laden met zonne-overschot":
        return f"Over ongeveer {index} uur zou Energy Brain de batterij laden met zonne-overschot."
    if action == "laden begrenzen omdat de batterij bijna vol is":
        return "De batterij blijft vol omdat de maximumgrens bijna bereikt is."
    if action == "batterij vol genoeg houden":
        return "Energy Brain houdt de batterij vast voor later."
    if action == "energie bewaren als reserve":
        return "Energy Brain bewaart energie als reserve voor later."
    return f"Over ongeveer {index} uur: {action}."


def _short_household_reason(reason: str) -> str:
    reasons = {
        "charge_from_pv_surplus": "Er is meer zon dan het huis nodig heeft.",
        "max_soc_clamped_charge": "De batterij raakt bijna vol.",
        "max_soc_hold": "De batterij is vol genoeg.",
        "reserve_hold": "Energy Brain bewaart energie als reserve.",
        "baseline_compare": "Dit is alleen een vergelijking met een simpel plan.",
        "shadow_hold": "Er is geen duidelijke betere actie.",
        "hold": "Er is nu geen actie nodig.",
    }
    return reasons.get(reason, reasons["shadow_hold"])


def _household_impact(step: dict[str, Any]) -> str:
    reason = _text(step.get("reason_code") or step.get("reason"), "shadow_hold")
    impacts = {
        "charge_from_pv_surplus": "Het overschot kan naar de batterij.",
        "max_soc_clamped_charge": "Laden wordt rustig begrensd om overladen te voorkomen.",
        "max_soc_hold": "De batterij blijft beschikbaar voor later.",
        "reserve_hold": "Er blijft stroom achter de hand.",
        "baseline_compare": "Dit helpt alleen om Energy Brain met een simpele basislijn te vergelijken.",
        "shadow_hold": "Energy Brain blijft meekijken en verandert niets.",
        "hold": "De batterij blijft ongeveer zoals hij is.",
    }
    return impacts.get(reason, impacts["shadow_hold"])


def _human_reason_fragment(step: dict[str, Any]) -> str:
    reason = human_reason_for_step(step)
    return reason[:1].lower() + reason[1:].rstrip(".")


def _fmt_plain(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        text = f"{float(value):.1f}"
        return text[:-2] if text.endswith(".0") else text
    return str(value)


def _fmt_money(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.2f}"
    return str(value)


def _reason_explanations() -> dict[str, str]:
    return {
        "shadow_hold": "Holding is shown when the shadow plan has no beneficial move or fallback data is active.",
        "hold": "Hold keeps the battery stable while price, reserve, and forecast constraints are inspected.",
        "reserve_hold": "Reserve hold protects the visual reserve/min SOC band in the forward horizon.",
        "charge_from_pv_surplus": "PV surplus charging is a display label for forecasted local solar surplus.",
        "discharge_to_load": "Discharge-to-load marks a shadow interval where stored energy offsets household demand.",
        "max_soc_clamp": "Max-SOC clamp marks an interval constrained by an upper SOC boundary.",
        "max_soc_clamped_charge": "Charge is visually clamped by the max-SOC boundary; this is an inspection label only.",
        "max_soc_hold": "The plan is holding near the max-SOC boundary to avoid exceeding the visual ceiling.",
        "baseline_compare": "Baseline comparison marks an interval used for cost comparison against a non-optimized path.",
    }


def _human_reason_explanations() -> dict[str, str]:
    return {
        "charge_from_pv_surplus": human_reason_for_step({"reason_code": "charge_from_pv_surplus"}),
        "max_soc_clamped_charge": human_reason_for_step({"reason_code": "max_soc_clamped_charge"}),
        "max_soc_hold": human_reason_for_step({"reason_code": "max_soc_hold"}),
        "reserve_hold": human_reason_for_step({"reason_code": "reserve_hold"}),
        "baseline_compare": human_reason_for_step({"reason_code": "baseline_compare"}),
        "shadow_hold": human_reason_for_step({"reason_code": "shadow_hold"}),
        "hold": human_reason_for_step({"reason_code": "hold"}),
    }


def _constraint_for_reason(reason: str) -> str:
    lowered = reason.lower()
    if "reserve" in lowered:
        return "reserve/min SOC boundary"
    if "max_soc" in lowered or "clamp" in lowered:
        return "max SOC boundary"
    if "charge" in lowered:
        return "PV surplus and price window"
    if "baseline" in lowered:
        return "baseline comparison window"
    return "display-only planner boundary"


def _badges(values: list[str]) -> str:
    return "".join(f'<span class="badge safe">{_esc(value)}</span>' for value in values)


def _tab_button(tab_id: str, label: str, selected: bool) -> str:
    return f'<button type="button" class="tab-button" role="tab" data-tab="{_esc(tab_id)}" aria-selected="{str(selected).lower()}">{_esc(label)}</button>'


def _banner(data: dict[str, Any]) -> str:
    label = "Degraded-Mode Banner"
    return (
        f'<section class="banner"><strong>{label}:</strong> {_esc(data.get("reason"))} · '
        f'fallback {_esc(data.get("fallback_mode"))} · missing source {_esc(data.get("missing_source"))}. '
        f'{_esc(data.get("explanation"))}</section>'
    )


def _plain_planner_html(data: dict[str, Any]) -> str:
    meaning = _dict(data.get("meaning"))
    cost = _dict(data.get("cost_comparison"))
    confidence = _dict(data.get("confidence"))
    summary = _dict(data.get("today_summary"))
    plan_sections = "".join(
        '<article class="plan-section">'
        f'<h3>{_esc(item.get("label"))}</h3>'
        f'<p class="plan-action">{_esc(item.get("action"))}</p>'
        f'<p>{_esc(item.get("reason"))}</p>'
        f'<p class="note">{_esc(item.get("impact"))}</p>'
        f'<span class="safety-label">{_esc(item.get("safety"))}</span>'
        "</article>"
        for item in _list(data.get("plan_card_sections"))
    )
    summary_rows = "".join(
        f"<div><span>{_esc(key)}</span><strong>{_esc(value)}</strong></div>"
        for key, value in summary.items()
    )
    dayparts = "".join(
        '<article class="plain-tile">'
        f'<h3>{_esc(item.get("label"))}</h3>'
        f'<p><strong>{_esc(item.get("summary"))}</strong></p>'
        f'<p class="mini">{_esc(item.get("why"))}</p>'
        "</article>"
        for item in _list(data.get("daypart_plan"))
    )
    scenarios = "".join(
        '<article class="plain-tile">'
        f'<h3>{_esc(item.get("title"))}</h3>'
        f'<p>{_esc(item.get("value"))}</p>'
        f'<p class="mini">{_esc(item.get("note"))}</p>'
        "</article>"
        for item in _list(data.get("scenarios"))
    )
    actual = _dict(data.get("actual_vs_predicted"))
    return (
        '<section class="plain-dashboard" aria-label="Predbat-inspired planner uitleg">'
        '<article class="human-card plan-card"><div class="plan-card-head"><div>'
        '<h2>Planning in gewone taal</h2>'
        f'<p class="note">{_esc(confidence.get("explanation"))}</p></div>'
        f'<span class="confidence-pill">{_esc(confidence.get("label"))}</span></div>'
        f'<div class="plan-sections">{plan_sections}</div></article>'
        '<article class="human-card"><h2>Vandaag samengevat</h2>'
        f'<div class="summary-list">{summary_rows}</div></article>'
        '<article class="human-card"><h2>Kort gezegd</h2>'
        f'<strong>{_esc(data.get("short"))}</strong></article>'
        '<article class="human-card"><h2>Wat betekent dit?</h2>'
        f'<strong>{_esc(meaning.get("huis"))}</strong>'
        f'<p class="note">Stuurt dit iets aan? {_esc(meaning.get("stuurt"))}</p></article>'
        '<article class="human-card"><h2>Wat moet ik hiermee doen?</h2>'
        f'<strong>{_esc(data.get("what_to_do"))}</strong></article>'
        ''
        '<article class="human-card"><h2>Kostenvergelijking</h2>'
        f'<p class="note">{_esc(cost.get("energy_brain"))}</p>'
        f'<p class="note">{_esc(cost.get("baseline"))}</p>'
        f'<strong>{_esc(cost.get("difference"))}</strong></article>'
        '<article class="human-card"><h2>Voorspelling vs werkelijkheid</h2>'
        f'<strong>{_esc(actual.get("status"))}</strong></article>'
        '<article class="human-card"><h2>Waarom lijkt dit op Predbat?</h2>'
        f'<strong>{_esc(data.get("predbat_reference"))}</strong></article>'
        '<article class="human-card plain-wide"><h2>Scenario&#x27;s</h2>'
        f'<div class="scenario-grid">{scenarios}</div></article>'
        "</section>"
    )


def _human_summary_html(data: dict[str, Any]) -> str:
    current = "".join(f"<li>{_esc(item)}</li>" for item in _list(data.get("current_state")))
    safety = "".join(f"<li>{_esc(item)}</li>" for item in _list(data.get("safety")))
    legend = "".join(f"<li>{_esc(item)}</li>" for item in _list(data.get("chart_legend")))
    return (
        '<section class="human-grid" aria-label="Uitleg in gewone taal">'
        '<article class="human-card"><h2>Wat gebeurt er nu?</h2>'
        f"<ul>{current}</ul></article>"
        '<article class="human-card"><h2>Volgende slimme stap</h2>'
        f'<strong>{_esc(data.get("next_step"))}</strong></article>'
        '<article class="human-card"><h2>Waarom?</h2>'
        f'<strong>{_esc(data.get("why"))}</strong></article>'
        '<article class="human-card"><h2>Is dit veilig?</h2>'
        f"<ul>{safety}</ul></article>"
        '<article class="human-card" style="grid-column:1/-1"><h2>Hoe lees ik deze grafiek?</h2>'
        f"<ul>{legend}</ul></article>"
        "</section>"
    )


def _energy_flow(flow: dict[str, Any]) -> str:
    labels = [
        ("Zonne-opwek", "pv_kw", "Verwachte zon"),
        ("Batterij", "battery_kw", "Gewenst batterijvermogen"),
        ("Huisverbruik", "load_kw", "Verwacht verbruik"),
        ("Verwachte netbalans", "grid_kw", "Import/export estimate"),
    ]
    return "".join(f'<article class="card"><h3>{label}</h3><div class="value">{_fmt(flow.get(key), " kW")}</div><p class="note">{note}</p></article>' for label, key, note in labels)


def _kv(data: dict[str, Any], suffix: str = "") -> str:
    return '<div class="list">' + "".join(f"<div><span>{_esc(key)}</span><strong>{_fmt(value, suffix)}</strong></div>" for key, value in data.items()) + "</div>"


def _avg_forecast(rows: list[dict[str, Any]], key: str) -> float:
    values = [_num(row.get(key), 0.0) for row in rows if isinstance(row, dict)]
    if not values:
        return 0.0
    return sum(values) / len(values)


def _forecast_range(rows: list[dict[str, Any]], key: str) -> tuple[float, float]:
    values = [_num(row.get(key), 0.0) for row in rows if isinstance(row, dict)]
    if not values:
        return (0.0, 0.0)
    return (min(values), max(values))


def forecast_layperson_summary(payload: dict[str, Any]) -> dict[str, Any]:
    price_rows = payload.get("price_forecast") if isinstance(payload.get("price_forecast"), list) else []
    pv_rows = payload.get("pv_forecast") if isinstance(payload.get("pv_forecast"), list) else []
    load_rows = payload.get("load_forecast") if isinstance(payload.get("load_forecast"), list) else []
    cycle_rows = payload.get("latest_cycle_table") if isinstance(payload.get("latest_cycle_table"), list) else []

    avg_price = _avg_forecast(price_rows, "import_price")
    avg_pv = _avg_forecast(pv_rows, "pv_kwh")
    avg_load = _avg_forecast(load_rows, "load_kwh")
    pv_min, pv_max = _forecast_range(pv_rows, "pv_kwh")
    load_min, load_max = _forecast_range(load_rows, "load_kwh")

    if avg_price >= 0.30:
        price_label = "Duur"
        price_text = f"Gemiddeld ongeveer EUR {avg_price:.2f}/kWh. Voorzichtig met inkopen."
    elif avg_price <= 0.16:
        price_label = "Goedkoop"
        price_text = f"Gemiddeld ongeveer EUR {avg_price:.2f}/kWh. Dit is een gunstiger prijsvenster."
    else:
        price_label = "Normaal"
        price_text = f"Gemiddeld ongeveer EUR {avg_price:.2f}/kWh. Geen extreem prijsvenster."

    if avg_pv >= 3.0:
        pv_label = "Veel zon"
        pv_text = f"Zon ligt grofweg tussen {pv_min:.1f} en {pv_max:.1f} kW. Er is waarschijnlijk ruimte om lokaal te gebruiken of te laden."
    elif avg_pv >= 1.0:
        pv_label = "Redelijke zon"
        pv_text = f"Zon ligt grofweg tussen {pv_min:.1f} en {pv_max:.1f} kW. Niet slecht, maar niet onbeperkt."
    else:
        pv_label = "Weinig zon"
        pv_text = f"Zon ligt grofweg tussen {pv_min:.1f} en {pv_max:.1f} kW. Verwacht weinig overschot."

    if avg_load >= 3.0:
        load_label = "Hoog verbruik"
        load_text = f"Huisverbruik ligt grofweg tussen {load_min:.1f} en {load_max:.1f} kW. Het huis vraagt relatief veel."
    elif avg_load >= 1.2:
        load_label = "Normaal verbruik"
        load_text = f"Huisverbruik ligt grofweg tussen {load_min:.1f} en {load_max:.1f} kW. Dit is een normaal verbruiksblok."
    else:
        load_label = "Laag verbruik"
        load_text = f"Huisverbruik ligt grofweg tussen {load_min:.1f} en {load_max:.1f} kW. Het huis vraagt weinig."

    first = cycle_rows[0] if cycle_rows and isinstance(cycle_rows[0], dict) else {}
    reason = _text(first.get("reason_code"), "shadow_hold")
    soc = _num(first.get("soc_percent"), _num(_dict(payload.get("battery_soc_card")).get("soc_percent"), 0.0))
    setpoint = _num(first.get("setpoint_kw"), 0.0)

    if reason == "charge_from_pv_surplus" or setpoint > 0.05:
        plan_label = "Batterij laden met zon"
        plan_text = f"De planning verwacht zonne-overschot. Batterij start rond {soc:.1f}% en mag richting de bovengrens lopen."
    elif reason == "max_soc_clamped_charge":
        plan_label = "Bijna vol, laden begrenzen"
        plan_text = f"De batterij zit rond {soc:.1f}%. Laden wordt begrensd om niet over de bovengrens te gaan."
    elif reason == "max_soc_hold" or soc >= 94.0:
        plan_label = "Vasthouden bij bijna vol"
        plan_text = f"De batterij zit rond {soc:.1f}%. De planning wil vooral vasthouden."
    else:
        plan_label = "Alleen observeren"
        plan_text = "Er is geen harde actie. Energy Brain kijkt mee en toont alleen een schaduwplanning."

    meaning = f"{pv_label.lower()}, {load_label.lower()}, prijs {price_label.lower()}. Verwachte richting: {plan_label.lower()}."

    return {
        "meaning": meaning,
        "cards": [
            {"title": "Stroomprijs", "value": price_label, "detail": price_text},
            {"title": "Zon", "value": pv_label, "detail": pv_text},
            {"title": "Huisverbruik", "value": load_label, "detail": load_text},
            {"title": "Batterijplan", "value": plan_label, "detail": plan_text},
        ],
    }


def _forecast_layperson_html(payload: dict[str, Any]) -> str:
    data = forecast_layperson_summary(payload)
    cards = "".join(
        "<div class=\"forecast-card-human\">"
        f"<span>{_esc(card.get('title'))}</span>"
        f"<strong>{_esc(card.get('value'))}</strong>"
        f"<small>{_esc(card.get('detail'))}</small>"
        "</div>"
        for card in data.get("cards", [])
        if isinstance(card, dict)
    )

    return f"""
      <div class="forecast-overview">
        <article class="forecast-hero">
          <p class="eyebrow">Forecast in gewone taal · Alleen meekijken</p>
          <h2>Komende uren samengevat</h2>
          <p>{_esc(data.get("meaning", "Geen betrouwbare forecast-samenvatting beschikbaar."))}</p>
        </article>
        <div class="forecast-cards">{cards}</div>
        <article class="card forecast-technical">
          <details>
            <summary>Technische details tonen</summary>
            <div class="grid three">
              {_forecast_card("Price Forecast Panel", payload["price_forecast"])}
              {_forecast_card("PV Forecast Panel", payload["pv_forecast"])}
              {_forecast_card("Load Forecast Panel", payload["load_forecast"])}
            </div>
            <article class="card" style="margin-top:14px">
              <h2>Latest Cycle Table</h2>
              {_cycle_table(payload["latest_cycle_table"])}
            </article>
          </details>
        </article>
      </div>
    """



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
            f'<button type="button" class="step-button{active}" data-index="{index}" data-step="{index}" aria-label="inspect only planner step {index}">'
            f'<span class="step-index"><span>#{_esc(row.get("step"))}</span><span>{_esc(row.get("validity"))}</span></span>'
            f'<span class="step-soc">{_fmt(row.get("soc_percent"), "%")}</span>'
            f'<span class="step-reason">{_esc(plain_window_label(reason))}</span>'
            "</button>"
        )
    return '<div class="steps">' + "".join(parts) + "</div>"


def _window_html(windows: list[dict[str, Any]]) -> str:
    rows = []
    for window in windows:
        segments = "".join(f'<span class="segment {_esc(window.get("kind"))}" style="left:{segment["left"]}%;width:{segment["width"]}%"></span>' for segment in _list(window.get("segments")))
        rows.append(
            f'<div class="window-row"><span class="mini">{_esc(window.get("label"))}'
            f'<small style="display:block;color:var(--muted)">{_esc(window.get("technical_label"))}</small></span>'
            f'<span class="track">{segments}</span></div>'
        )
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
    reason = _text(step.get("reason_code"), "shadow_hold")
    plain = plain_step_summary(step)
    human_fields = {
        "Stap": f"#{_text(step.get('step'), '0')} · {human_step_time_label(step.get('step', 0))}",
        "Wat gebeurt er?": plain.get("wat"),
        "Waarom?": plain.get("waarom"),
        "Wat betekent dit voor mijn huis?": plain.get("huis"),
        "Stuurt dit iets aan?": plain.get("stuurt"),
    }
    technical_fields = {
        "selected step index/time": f"#{_text(step.get('step'), '0')} / +0h",
        "Batterijvulling (SOC %)": step.get("soc_percent"),
        "Gewenst batterijvermogen (battery setpoint kW)": step.get("setpoint_kw"),
        "Reden (reason code)": reason,
        "price": step.get("price"),
        "PV forecast": step.get("pv_forecast"),
        "load forecast": step.get("load_forecast"),
        "Verwachte netbalans (grid estimate)": step.get("grid_estimate"),
        "Alleen tonen (validation/display-only status)": step.get("validity"),
        "safety status": f"{_text(step.get('validity'), 'display-only')} / no dispatch",
        "Begrenzing (constraint applied)": _text(step.get("constraint"), _constraint_for_reason(reason)),
    }
    explanation = _reason_explanations().get(reason, _reason_explanations()["shadow_hold"])
    return (
        _kv(human_fields)
        + '<details class="technical-area"><summary>Technische details tonen/verbergen</summary>'
        + _kv(technical_fields)
        + f'<p class="note" id="selected-reason-explanation">{_esc(explanation)}</p></details>'
    )


def _chart_step_summary(step: dict[str, Any]) -> str:
    reason = _text(step.get("reason_code"), "shadow_hold")
    plain = plain_step_summary(step)
    human_fields = {
        "Stap": f"#{_text(step.get('step'), '0')} · {human_step_time_label(step.get('step', 0))}",
        "Wat gebeurt er?": plain.get("wat"),
        "Waarom?": plain.get("waarom"),
        "Wat betekent dit voor mijn huis?": plain.get("huis"),
        "Stuurt dit iets aan?": plain.get("stuurt"),
    }
    technical_fields = {
        "step/hour": f"#{_text(step.get('step'), '0')} / +0h",
        "Batterijvulling (SOC)": _fmt(step.get("soc_percent"), "%"),
        "Reden (reason)": reason,
        "Begrenzing (constraint)": _text(step.get("constraint"), _constraint_for_reason(reason)),
    }
    return (
        _kv(human_fields)
        + '<details class="technical-area"><summary>Technische details tonen/verbergen</summary>'
        + _kv(technical_fields)
        + "</details>"
    )


def _horizon_chart(payload: dict[str, Any]) -> str:
    points = _list(payload.get("soc_trajectory"))
    rows = _list(payload.get("planner_timeline"))
    if not points:
        return '<p class="note">SOC trajectory placeholder chart area</p>'
    width = 900
    height = 330
    pad = 52
    values = [_num(point.get("soc_percent"), 0.0) for point in points]
    reserve = _num(points[0].get("reserve_floor"), 20.0)
    max_soc = _num(_dict(payload.get("battery_soc_card")).get("max_forecast_soc"), max(values or [reserve]))
    lower = max(0.0, min(values + [reserve]) - 4.0)
    upper = min(100.0, max(values + [reserve, max_soc]) + 4.0)
    span = max(1.0, upper - lower)
    x_step = (width - pad * 2) / max(1, len(points) - 1)
    soc_pairs = []
    pv_pairs = []
    load_pairs = []
    price_bars = []
    decision_bands = []
    x_labels = []
    max_price = max([_num(row.get("price"), 0.0) for row in rows] or [1.0]) or 1.0
    for index, point in enumerate(points):
        x = pad + index * x_step
        y = pad + (upper - _num(point.get("soc_percent"), 0.0)) / span * (height - pad * 2)
        soc_pairs.append(f"{x:.1f},{y:.1f}")
        row = rows[min(index, len(rows) - 1)] if rows else {}
        reason = _text(row.get("reason_code"), "")
        decision_class = ""
        if reason == "charge_from_pv_surplus":
            decision_class = "#43d6a6"
        elif reason in ("max_soc_clamped_charge", "max_soc_hold", "max_soc_clamp") or "max_soc" in reason:
            decision_class = "#f2b84b"
        if decision_class:
            decision_bands.append(f'<rect x="{x - x_step / 2:.1f}" y="{pad:.1f}" width="{max(6.0, x_step):.1f}" height="{height - pad * 2:.1f}" fill="{decision_class}" opacity=".14"/>')
        pv_y = height - pad - min(1.0, _num(row.get("pv_forecast"), 0.0) / 6.0) * 54
        load_y = height - pad - min(1.0, _num(row.get("load_forecast"), 0.0) / 4.0) * 54
        pv_pairs.append(f"{x:.1f},{pv_y:.1f}")
        load_pairs.append(f"{x:.1f},{load_y:.1f}")
        bar_h = 10 + (_num(row.get("price"), 0.0) / max_price) * 58
        price_bars.append(f'<rect x="{x - 4:.1f}" y="{height - pad - bar_h:.1f}" width="8" height="{bar_h:.1f}" rx="3" fill="rgba(255,209,102,.38)"/>')
        if index in (0, 6, 12, 18, len(points) - 1):
            x_labels.append(f'<text x="{x:.1f}" y="{height - 14}" fill="#9eacb8" font-size="11" text-anchor="middle">+{index}h</text>')
    reserve_y = pad + (upper - reserve) / span * (height - pad * 2)
    max_y = pad + (upper - max_soc) / span * (height - pad * 2)
    y_mid_value = (upper + lower) / 2
    y_mid = pad + (upper - y_mid_value) / span * (height - pad * 2)
    return (
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="SOC trajectory placeholder chart area">'
        f'<title>SOC trajectory, price, PV/load overlay, reserve and max SOC horizon</title>'
        f'<rect x="{pad}" y="{pad}" width="{width - pad * 2}" height="{height - pad * 2}" fill="rgba(255,255,255,.018)" stroke="rgba(238,244,248,.12)"/>'
        f'<rect x="{pad}" y="{reserve_y:.1f}" width="{width - pad * 2}" height="{height - pad - reserve_y:.1f}" fill="rgba(242,184,75,.08)"/>'
        f'{"".join(decision_bands)}'
        f'<line x1="{pad}" x2="{width-pad}" y1="{reserve_y:.1f}" y2="{reserve_y:.1f}" stroke="#f2b84b" stroke-dasharray="6 6"/>'
        f'<text x="{width - pad - 118}" y="{reserve_y - 6:.1f}" fill="#f2b84b" font-size="12">Reserve / min SOC</text>'
        f'<line x1="{pad}" x2="{width-pad}" y1="{max_y:.1f}" y2="{max_y:.1f}" stroke="#ff7777" stroke-dasharray="4 5"/>'
        f'<text x="{width - pad - 62}" y="{max_y - 6:.1f}" fill="#ff9999" font-size="12">Max SOC</text>'
        f'{"".join(price_bars)}'
        f'<polyline points="{" ".join(pv_pairs)}" fill="none" stroke="#ffd166" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>'
        f'<polyline points="{" ".join(load_pairs)}" fill="none" stroke="#69a7ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>'
        f'<polyline points="{" ".join(soc_pairs)}" fill="none" stroke="#43d6a6" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<line id="selected-step-marker" data-chart-pad="{pad}" data-step-width="{x_step:.4f}" x1="{pad}" x2="{pad}" y1="{pad}" y2="{height - pad}" stroke="#eef4f8" stroke-width="2" opacity=".86"/>'
        f'<text id="selected-step-marker-label" x="{pad + 6}" y="{pad + 16}" fill="#eef4f8" font-size="12">selected step #0</text>'
        f'<text x="14" y="{pad + 4}" fill="#9eacb8" font-size="12">{upper:.1f}%</text>'
        f'<text x="14" y="{y_mid + 4:.1f}" fill="#9eacb8" font-size="12">{y_mid_value:.1f}%</text>'
        f'<text x="14" y="{height - pad + 4}" fill="#9eacb8" font-size="12">{lower:.1f}%</text>'
        f'<text x="10" y="{height / 2:.1f}" fill="#9eacb8" font-size="12" transform="rotate(-90 10 {height / 2:.1f})">SOC %</text>'
        f'{"".join(x_labels)}'
        f'<text x="{width / 2:.1f}" y="{height - 2}" fill="#9eacb8" font-size="12" text-anchor="middle">step / hour</text>'
        f'<text x="{width - 326}" y="39" fill="#9eacb8" font-size="12">SOC line · price bars · PV/load overlays · reserve band</text>'
        f'<text x="{width - 256}" y="22" fill="#9eacb8" font-size="12">Gekleurde vlakken tonen controleperiodes</text>'
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
