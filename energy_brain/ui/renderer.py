from __future__ import annotations

import html
from typing import Any

from energy_brain.ui.components.responsive import (
    render_explainability_panel,
    render_planner_summary,
    render_powerflow_hero,
    render_safety_panel,
)
from energy_brain.ui.layout_router import build_layout_view
from energy_brain.ui.state.layout_state import select_layout_mode
from energy_brain.ui.themes.tesla_fusion import render_theme_css


def render_layout(layout_mode: str, payload: dict[str, Any]) -> str:
    mode = select_layout_mode({"layout": layout_mode})
    layout = build_layout_view(payload, mode)
    sections = layout.get("sections", [])
    right_sections = [section for section in sections if section.get("type") != "powerflow_hero"]
    hero = next(
        (section for section in sections if section.get("type") == "powerflow_hero"),
        {},
    )

    links = "".join(
        f'<a href="/new-ui?layout={name}" class="{"active" if name == mode else ""}">{name.title()}</a>'
        for name in ("mobile", "tablet", "desktop")
    )

    html_parts: list[str] = [
        "<!DOCTYPE html>",
        f'<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Energy Brain</title>",
        f"<style>{render_theme_css()}</style>",
        f'</head><body class="layout-{html.escape(mode, quote=True)}">',
        '<main class="shell">',
        '<header class="topline">',
        '<div><div class="brand">Energy Brain</div><div class="eyebrow">Read-only EMS cockpit</div></div>',
        f'<nav class="layout-switcher" aria-label="Layout selector">{links}</nav>',
        "</header>",
        '<div class="dashboard">',
        render_powerflow_hero(hero),
        '<div class="side">',
    ]

    for section in right_sections:
        section_type = section.get("type")
        if section_type == "planner_summary":
            html_parts.append(render_planner_summary(section))
            continue
        if section_type == "explainability":
            html_parts.append(render_explainability_panel(section))
            continue
        if section_type == "safety":
            html_parts.append(render_safety_panel(section))

    html_parts.extend(["</div>", "</div>", "</main>", "</body></html>"])

    return "".join(html_parts)


def render_error_page(message: str = "New UI unavailable") -> str:
    safe_message = html.escape(message, quote=True)
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<style>{render_theme_css()}</style><title>Energy Brain</title></head>"
        "<body><main class=\"error-page\"><section class=\"panel\">"
        "<h2>Energy Brain UI unavailable</h2>"
        f"<p>{safe_message}</p>"
        "<p>The read-only web server is still running.</p>"
        "</section></main></body></html>"
    )
