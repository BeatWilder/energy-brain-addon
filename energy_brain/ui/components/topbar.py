from __future__ import annotations


def render_topbar(data: dict) -> str:
    title = data.get("title", "Energy Brain")

    return f"""
    <div style="
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-bottom:20px;
    ">
      <div style="font-size:32px;font-weight:700;">
        {title}
      </div>

      <div class="pill">
        Alleen observeren
      </div>
    </div>
    """
