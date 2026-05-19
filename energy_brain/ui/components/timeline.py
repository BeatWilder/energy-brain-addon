from __future__ import annotations

import html


def render_timeline(data: dict) -> str:
    entries = data.get("entries") if isinstance(data.get("entries"), list) else []
    blocks = []
    for entry in entries[:8]:
        if not isinstance(entry, dict):
            continue
        tone = html.escape(str(entry.get("tone", "hold")), quote=True)
        width = html.escape(str(entry.get("width", "16")), quote=True)
        time = html.escape(str(entry.get("time", "nu")), quote=True)
        action = html.escape(str(entry.get("action", "vasthouden")), quote=True)
        blocks.append(
            f'<div class="timeline-block tone-{tone}" style="--span:{width}">'
            f"<span>{time}</span><b>{action}</b></div>"
        )
    body = "".join(blocks) or '<div class="timeline-block tone-hold"><span>nu</span><b>observeren</b></div>'
    return f"""
    <div class="timeline" aria-label="Planningslijn">
      {body}
    </div>
    """


def timeline_component(entries: list[dict] | None = None) -> dict:
    return {
        "type": "planner_timeline",
        "entries": entries or [
            {"time": "nu", "action": "observeren", "tone": "hold", "width": "18"},
        ],
        "animated": True,
    }
