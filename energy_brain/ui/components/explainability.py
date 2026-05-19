from __future__ import annotations

import html


def render_explainability(data: dict) -> str:
    reasons = data.get("reasons", [])

    items = "".join(
        f'<div class="reason-chip">{html.escape(str(reason), quote=True)}</div>'
        for reason in reasons
    )

    return f"""
    <div class="explain-compact">
      <div class="eyebrow">Waarom</div>
      <div class="reason-stack">{items}</div>
    </div>
    """
