from __future__ import annotations

from typing import Any

from energy_brain.ui.state.display_values import sanitize_percent, sanitize_power_kw
from energy_brain.ui.state.layout_state import effective_layout_mode


def _float_value(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return default
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _text_value(value: Any, default: str) -> str:
    if value in (None, "", "unknown", "unavailable", "none", "None"):
        return default
    return str(value)


def _money_value(value: Any, default: str = "berekenen") -> str:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return default
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if number < 0 else ""
    return f"{sign}€{abs(number):.2f}"


def _percent_value(value: Any, default: str = "gemiddeld") -> str:
    if value in (None, "", "unknown", "unavailable", "none", "None", "—"):
        return default
    try:
        return f"{float(str(value).replace(',', '.')):.0f}%"
    except (TypeError, ValueError):
        return str(value)


def _strategy_text(payload: dict[str, Any]) -> str:
    explicit = _text_value(payload.get("decision"), "")
    if explicit:
        lower = explicit.lower()
        if any(word in lower for word in ("charge", "laden")):
            return "Laden in het gunstigste energiemoment"
        if any(word in lower for word in ("discharge", "export", "ontladen")):
            return "Opgeslagen energie gebruiken tijdens dure uren"
        if any(word in lower for word in ("hold", "wacht", "wait")):
            return "Batterij vasthouden tot omstandigheden verbeteren"
        return explicit

    solar = _float_value(payload.get("pv_power_kw") or payload.get("pv_now_kw"))
    battery = _float_value(payload.get("battery_power_kw"))
    grid = _float_value(payload.get("grid_power_kw"))
    price = _float_value(payload.get("grid_price") or payload.get("price_now"))
    if solar > 0.4 and battery > 0.1:
        return "Laden met zonne-overschot"
    if grid < -0.1:
        return "Overschot terugleveren aan het net"
    if price < 0:
        return "Wachten op goedkopere stroom"
    return "Reserve beschermen en volgende kans bewaken"


def _action_text(value: Any) -> str:
    text = _text_value(value, "vasthouden")
    lower = text.lower()
    if "charge" in lower or "laden" in lower:
        return "Laden"
    if "discharge" in lower or "ontladen" in lower:
        return "Ontladen"
    if "export" in lower or "terug" in lower:
        return "Terugleveren"
    if "cheap" in lower or "negative" in lower or "goedkoop" in lower:
        return "Goedkoop uur"
    if "expensive" in lower or "peak" in lower or "duur" in lower:
        return "Duur uur"
    if "observer" in lower:
        return "Observeren"
    if "hold" in lower or "wait" in lower or "wacht" in lower:
        return "Vasthouden"
    return text


def _reason_text(value: Any, default: str = "Laatste plancyclus bewaakt deze keuze.") -> str:
    text = _text_value(value, default)
    lower = text.lower()
    if "negative" in lower and "price" in lower:
        return "Er wordt een gunstig prijsmoment verwacht."
    if "battery" in lower and ("target" in lower or "below" in lower):
        return "De batterij zit nog onder het gewenste doel."
    if "reserve" in lower:
        return "De batterijreserve blijft beschermd."
    if "solar" in lower or "pv" in lower or "surplus" in lower:
        return "Later wordt meer zonne-opwek verwacht."
    if "price" in lower:
        return "De huidige stroomprijs is nog niet gunstig genoeg."
    if "degraded" in lower or "forecast" in lower or "prognose" in lower:
        return "Een deel van de voorspelling is beperkt beschikbaar."
    if "no plan" in lower or "geen plan" in lower:
        return "Er is nog geen bruikbare plancyclus beschikbaar."
    return text


def _display_power(payload: dict[str, Any], *keys: str, pv_generation: bool = False) -> dict[str, Any]:
    for key in keys:
        if key in payload:
            return sanitize_power_kw(payload.get(key), pv_generation=pv_generation)
    return sanitize_power_kw(None)


def _timeline_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    windows = payload.get("plan_windows")
    if not isinstance(windows, list):
        windows = payload.get("timeline")
    if not isinstance(windows, list):
        windows = []

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(windows[:96]):
        if not isinstance(item, dict):
            continue
        action = _text_value(item.get("kind") or item.get("action"), "hold")
        lower = action.lower()
        if "charge" in lower or "laden" in lower:
            tone = "charge"
        elif "discharge" in lower or "export" in lower or "ontladen" in lower:
            tone = "discharge"
        elif "cheap" in lower or "negative" in lower:
            tone = "cheap"
        elif "expensive" in lower or "peak" in lower:
            tone = "expensive"
        else:
            tone = "hold"
        start = _text_value(item.get("start") or item.get("time"), f"{index:02d}:00")
        end = _text_value(item.get("end") or item.get("until"), "")
        normalized.append(
            {
                "start": start,
                "end": end,
                "time": start,
                "action": _action_text(action),
                "reason": _reason_text(
                    item.get("reason"),
                    "Laatste plancyclus bewaakt deze keuze.",
                ),
                "tone": tone,
                "source_count": 1,
                "exact_indices": [index],
            }
        )
    if normalized:
        merged: list[dict[str, Any]] = []
        for entry in normalized:
            previous = merged[-1] if merged else None
            if (
                previous
                and previous["action"] == entry["action"]
                and previous["tone"] == entry["tone"]
                and previous["reason"] == entry["reason"]
            ):
                previous["end"] = entry.get("end") or entry.get("start") or previous.get("end")
                previous["source_count"] += 1
                previous["exact_indices"].extend(entry["exact_indices"])
                continue
            merged.append(dict(entry))

        total = max(1, sum(int(item["source_count"]) for item in merged))
        for item in merged:
            end = item.get("end")
            item["time"] = f'{item["start"]} -> {end}' if end else item["start"]
            item["width"] = str(max(10, round(int(item["source_count"]) / total * 100, 1)))
        return merged[:12]
    return [
        {
            "time": "nu",
            "start": "nu",
            "end": "",
            "action": _action_text(payload.get("decision")),
            "reason": _reason_text(
                payload.get("decision_reason"),
                "Geen planregels beschikbaar.",
            ),
            "tone": "hold",
            "width": "18",
            "source_count": 1,
            "exact_indices": [],
        }
    ]


def _reasons(payload: dict[str, Any]) -> list[str]:
    values = [
        payload.get("decision_reason"),
        payload.get("predbat_summary"),
        payload.get("degraded_text"),
    ]
    return [_reason_text(value, "") for value in values if _text_value(value, "")]


def _forecast_text(degraded: Any) -> str:
    return "Voorspelling beperkt" if degraded else "Voorspelling actief"


def _market_text(value: Any) -> str:
    return "Marktdata actief" if value not in (None, "", "unknown", "unavailable", "none", "None", "—") else "Marktdata onbekend"


def _mode_text(value: Any) -> str:
    lower = _text_value(value, "observer actief").lower()
    if "shadow" in lower:
        return "Schaduw actief"
    if "comparison" in lower or "vergelijk" in lower:
        return "Vergelijkingsmodus"
    if "active" in lower:
        return "Actief bewaakt"
    return "Observer actief"


def _status_text(value: Any, default: str) -> str:
    text = _text_value(value, default)
    lower = text.lower()
    if "reserve" in lower and ("protect" in lower or "bescherm" in lower):
        return "Reserve beschermd"
    if "no active faults" in lower or "geen stor" in lower:
        return "Geen storingen"
    if "read-only" in lower or "write protection" in lower:
        return "Aansturing beveiligd. Deze cockpit is alleen-lezen."
    if lower == "valid":
        return "Geldig"
    if lower == "degraded":
        return "Beperkt"
    if lower == "blocked":
        return "Geblokkeerd"
    return text


def build_layout_view(payload: dict[str, Any], layout_mode: str) -> dict[str, Any]:
    mode = effective_layout_mode(layout_mode)
    compact = mode == "mobile"
    tablet = mode == "tablet"
    timeline = _timeline_entries(payload)
    strategy = _strategy_text(payload)
    price = _float_value(payload.get("grid_price") or payload.get("price_now"))
    solar = _display_power(payload, "pv_power_kw", "pv_now_kw", pv_generation=True)
    house = _display_power(payload, "household_load_kw", "home_load_kw")
    battery = _display_power(payload, "battery_power_kw")
    grid = _display_power(payload, "grid_power_kw")
    soc = sanitize_percent(payload.get("soc_percent") or payload.get("battery_soc_percent"))
    return {
        "schema_version": "energy_brain.ui.layout.v2",
        "layout": mode,
        "layout_preference": layout_mode if layout_mode in {"auto", "mobile", "tablet", "desktop"} else "auto",
        "observer_only": True,
        "density": "compact" if compact else "balanced" if tablet else "wide",
        "viewport": {
            "mobile_first": True,
            "breakpoints": {
                "mobile_max": 767,
                "tablet_min": 768,
                "tablet_max": 1199,
                "desktop_min": 1200,
            },
        },
        "responsive": {
            "mobile_first": True,
            "breakpoints": {
                "mobile_max": 767,
                "tablet_min": 768,
                "tablet_max": 1199,
                "desktop_min": 1200,
            },
        },
        "sections": [
            {
                "type": "powerflow_hero",
                "title": "Energy Brain",
                "status": "Observer actief",
                "strategy": strategy,
                "soc_percent": soc["value"],
                "soc_label": soc["label"],
                "soc_known": soc["known"],
                "solar_kw": solar["value"],
                "solar_label": solar["label"],
                "solar_known": solar["known"],
                "house_kw": house["value"],
                "house_label": house["label"],
                "house_known": house["known"],
                "battery_kw": battery["value"],
                "battery_label": battery["label"],
                "battery_known": battery["known"],
                "grid_kw": grid["value"],
                "grid_label": grid["label"],
                "grid_known": grid["known"],
                "data_quality": {
                    "clamped": [
                        name
                        for name, value in {
                            "zon": solar,
                            "huis": house,
                            "batterij": battery,
                            "net": grid,
                            "batterij-SOC": soc,
                        }.items()
                        if value["clamped"]
                    ],
                    "unknown": [
                        name
                        for name, value in {
                            "zon": solar,
                            "huis": house,
                            "batterij": battery,
                            "net": grid,
                            "batterij-SOC": soc,
                        }.items()
                        if not value["known"]
                    ],
                },
                "price": price,
                "decision": strategy,
                "updated": _text_value(payload.get("last_update"), "laatste cyclus"),
            },
            {
                "type": "planner_summary",
                "title": "Wat denkt Energy Brain nu?",
                "mode": _mode_text(payload.get("mode")),
                "execution": _text_value(payload.get("execution"), "Geen aansturing"),
                "headline": strategy,
                "confidence": _percent_value(payload.get("forecast_confidence")),
                "expected_savings": _money_value(
                    payload.get("expected_savings")
                    or payload.get("delta_vs_baseline")
                    or payload.get("savings")
                ),
                "next_action_time": timeline[0]["time"] if timeline else "volgende cyclus",
                "entries": timeline,
                "source_entry_count": len(payload.get("plan_windows") or payload.get("timeline") or []),
            },
            {
                "type": "explainability",
                "title": "Waarom wacht Energy Brain?",
                "reasons": _reasons(payload),
            },
            {
                "type": "safety",
                "title": "Systeemstatus",
                "observer_state": _mode_text(payload.get("shadow_state") or payload.get("mode")),
                "forecast_valid": _forecast_text(payload.get("degraded")),
                "market_status": _market_text(payload.get("grid_price") or payload.get("price_now")),
                "planner_status": "Plan actief" if timeline else "Plan beperkt",
                "reserve_status": _status_text(payload.get("reserve_status"), "Reserve beschermd"),
                "fault_status": _status_text(payload.get("fault_status"), "Geen storingen"),
                "last_update": _text_value(payload.get("last_update"), "laatste cyclus"),
                "readonly": True,
                "blocked_reason": _status_text(
                    payload.get("execution_blocked_reason"),
                    "Aansturing beveiligd. Deze cockpit is alleen-lezen.",
                ),
            },
            {
                "type": "battery_status",
                "title": "Batterijstatus",
                "soc_percent": soc["value"],
                "soc_label": soc["label"],
                "battery_kw": battery["value"],
                "battery_label": battery["label"],
                "updated": _text_value(payload.get("last_update"), "laatste cyclus"),
            },
        ],
    }


def build_layout(layout_mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    return build_layout_view(payload, layout_mode)
