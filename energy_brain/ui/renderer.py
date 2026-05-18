from __future__ import annotations

from typing import Any

from energy_brain.ui.components.topbar import render_topbar
from energy_brain.ui.components.powerflow import render_powerflow
from energy_brain.ui.components.timeline import render_timeline
from energy_brain.ui.components.explainability import render_explainability


def render_layout(layout: dict[str, Any]) -> str:
    sections = layout.get("sections", [])

    html_parts: list[str] = []

    html_parts.append("""
    <style>
      body {
        margin: 0;
        padding: 0;
        background: #070b14;
        color: #f3f6fb;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      }

      .container {
        padding: 24px;
      }

      .grid {
        display: grid;
        grid-template-columns: 1.2fr 1fr 0.9fr;
        gap: 20px;
        margin-top: 20px;
      }

      .card {
        background: #101826;
        border-radius: 22px;
        padding: 20px;
        box-shadow:
          0 0 0 1px rgba(255,255,255,0.04),
          0 20px 40px rgba(0,0,0,0.35);
      }

      .title {
        font-size: 15px;
        opacity: 0.7;
        margin-bottom: 10px;
      }

      .big {
        font-size: 42px;
        font-weight: 700;
      }

      .pill {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        background: #1a2436;
        margin: 4px;
      }

      .power-number {
        font-size: 28px;
        font-weight: 700;
      }

      .ok {
        color: #5df2a5;
      }

      .warn {
        color: #ffcc66;
      }

      .bad {
        color: #ff6b6b;
      }
    </style>
    """)

    html_parts.append('<div class="container">')

    for section in sections:
        if section.get("type") == "topbar":
            html_parts.append(render_topbar(section))
            continue

        left = section.get("left", {})
        center = section.get("center", {})
        right = section.get("right", [])

        html_parts.append('<div class="grid">')

        html_parts.append(render_powerflow(left))
        html_parts.append(render_timeline(center))

        html_parts.append('<div>')

        for item in right:
            if item.get("type") == "explainability":
                html_parts.append(render_explainability(item))
            else:
                html_parts.append(f"""
                <div class="card">
                  <pre>{item}</pre>
                </div>
                """)

        html_parts.append('</div>')
        html_parts.append('</div>')

    html_parts.append('</div>')

    return "".join(html_parts)
