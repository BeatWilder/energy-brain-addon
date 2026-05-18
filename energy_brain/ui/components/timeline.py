from __future__ import annotations


def render_timeline(data: dict) -> str:
    return """
    <div class="card">
      <div class="title">Planner Timeline</div>

      <div style="
        height:220px;
        border-radius:16px;
        background:linear-gradient(
          180deg,
          rgba(255,255,255,0.04),
          rgba(255,255,255,0.01)
        );
        margin-top:20px;
      "></div>
    </div>
    """
