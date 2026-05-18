from __future__ import annotations


def render_explainability(data: dict) -> str:
    reasons = data.get("reasons", [])

    items = "".join(
        f'<div class="pill">{reason}</div>'
        for reason in reasons
    )

    return f"""
    <div class="card">
      <div class="title">Waarom gebeurt dit?</div>

      <div style="margin-top:16px;">
        {items}
      </div>
    </div>
    """
