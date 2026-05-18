from __future__ import annotations


def render_powerflow(data: dict) -> str:
    solar = data.get("solar_kw", 0)
    house = data.get("house_kw", 0)
    battery = data.get("battery_kw", 0)
    grid = data.get("grid_kw", 0)

    return f"""
    <div class="card">
      <div class="title">Tesla-style Powerflow</div>

      <div style="margin-top:20px;">
        <div class="power-number">☀️ {solar:.1f} kW</div>
        <div>Solar</div>
      </div>

      <div style="margin-top:18px;">
        <div class="power-number">🏠 {house:.1f} kW</div>
        <div>House</div>
      </div>

      <div style="margin-top:18px;">
        <div class="power-number">🔋 {battery:.1f} kW</div>
        <div>Battery</div>
      </div>

      <div style="margin-top:18px;">
        <div class="power-number">⚡ {grid:.1f} kW</div>
        <div>Grid</div>
      </div>
    </div>
    """
