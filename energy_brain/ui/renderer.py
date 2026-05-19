from __future__ import annotations

import html
from typing import Any

from energy_brain.ui.components.responsive import (
    render_explainability_panel,
    render_battery_panel,
    render_health_strip,
    render_planner_summary,
    render_powerflow_hero,
    render_safety_panel,
)
from energy_brain.ui.layout_router import build_layout_view
from energy_brain.ui.state.layout_state import effective_layout_mode, select_layout_mode
from energy_brain.ui.themes.tesla_fusion import render_theme_css


def render_layout(layout_mode: str, payload: dict[str, Any]) -> str:
    preference = select_layout_mode({"layout": layout_mode})
    mode = effective_layout_mode(preference)
    layout = build_layout_view(payload, preference)
    sections = layout.get("sections", [])
    right_sections = [
        section
        for section in sections
        if section.get("type") not in {"powerflow_hero", "safety"}
    ]
    hero = next(
        (section for section in sections if section.get("type") == "powerflow_hero"),
        {},
    )
    safety = next((section for section in sections if section.get("type") == "safety"), {})

    labels = {
        "auto": "Automatisch",
        "mobile": "Mobiel",
        "tablet": "Tablet",
        "desktop": "Desktop",
    }
    links = "".join(
        f'<a href="?layout={name}" data-layout-option="{name}" class="layout-link layout-link-{name} {"active" if name == preference else ""}">{labels[name]}</a>'
        for name in ("auto", "mobile", "tablet", "desktop")
    )

    html_parts: list[str] = [
        "<!DOCTYPE html>",
        f'<html lang="nl"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Energy Brain</title>",
        f"<style>{render_theme_css()}</style>",
        f'</head><body class="layout-{html.escape(mode, quote=True)} preference-{html.escape(preference, quote=True)}" data-layout-preference="{html.escape(preference, quote=True)}">',
        '<main class="shell">',
        '<header class="topline">',
        '<div><div class="brand">Energy Brain</div><div class="eyebrow">Autonoom energie besturingssysteem</div></div>',
        f'<nav class="layout-switcher" aria-label="Layoutkeuze">{links}</nav>',
        "</header>",
        render_health_strip(safety),
        '<div class="dashboard">',
        render_powerflow_hero(hero),
        '<div class="side">',
    ]

    for section in right_sections:
        section_type = section.get("type")
        if section_type == "planner_summary":
            html_parts.append(render_planner_summary(section))
            continue
        if section_type == "battery_status":
            html_parts.append(render_battery_panel(section))
            continue
        if section_type == "explainability":
            html_parts.append(render_explainability_panel(section))
            continue

    html_parts.extend(
        [
            render_safety_panel(safety),
            "</div>",
            "</div>",
            "</main>",
            f"<script>{_layout_script()}</script>",
            "</body></html>",
        ]
    )

    return "".join(html_parts)


def _layout_script() -> str:
    return """
(() => {
  const key = "energy-brain.layout";
  const allowed = new Set(["auto", "mobile", "tablet", "desktop"]);
  const params = new URLSearchParams(window.location.search);
  const query = params.get("layout");
  if (allowed.has(query)) localStorage.setItem(key, query);

  const stored = localStorage.getItem(key);
  const preference = allowed.has(query) ? query : (allowed.has(stored) ? stored : document.body.dataset.layoutPreference || "auto");
  document.body.dataset.layoutPreference = preference;

  function viewportLayout() {
    const width = window.innerWidth || document.documentElement.clientWidth || 0;
    if (width >= 1200) return "desktop";
    if (width >= 768) return "tablet";
    return "mobile";
  }

  function applyLayout() {
    const effective = preference === "auto" ? viewportLayout() : preference;
    document.body.classList.remove("layout-auto", "layout-mobile", "layout-tablet", "layout-desktop");
    document.body.classList.add(`layout-${effective}`);
    document.body.dataset.effectiveLayout = effective;
    document.querySelectorAll("[data-layout-option]").forEach((item) => {
      item.classList.toggle("active", item.dataset.layoutOption === preference);
    });
  }

  applyLayout();
  window.addEventListener("resize", applyLayout, {passive: true});
})();
"""


def render_error_page(message: str = "Nieuwe UI niet beschikbaar") -> str:
    safe_message = html.escape(message, quote=True)
    return (
        "<!DOCTYPE html><html lang=\"nl\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<style>{render_theme_css()}</style><title>Energy Brain</title></head>"
        "<body><main class=\"error-page\"><section class=\"panel\">"
        "<h2>Energy Brain UI niet beschikbaar</h2>"
        f"<p>{safe_message}</p>"
        "<p>De alleen-lezen webserver blijft actief.</p>"
        "</section></main></body></html>"
    )
