from energy_brain.ui.powerflow_v2.styles import render_powerflow_v2_css

def render_powerflow_v2(grid_flow: str = "idle", battery_flow: str = "idle"):
    grid_label = {
        "importing": "Import",
        "exporting": "Export",
    }.get(grid_flow, "Stand-by")
    battery_label = {
        "charging": "Laden",
        "discharging": "Levert",
    }.get(battery_flow, "Stand-by")
    return f"""
<style>
{render_powerflow_v2_css()}
</style>

<div class="pf-v2" aria-label="Realtime energiestroom" data-grid-flow="{grid_flow}" data-battery-flow="{battery_flow}">
  <div class="pf-caption">Energiestroom</div>

  <div class="pf-node pf-solar">
    <span>Zon</span>
    <em>Live kW</em>
  </div>

  <div class="pf-node pf-home">
    <span>Huis</span>
    <em>Verbruik</em>
  </div>

  <div class="pf-node pf-grid">
    <span>Net</span>
    <em>{grid_label}</em>
  </div>

  <div class="pf-node pf-battery">
    <i class="pf-battery-shell" aria-hidden="true"><b></b></i>
    <span>Batterij</span>
    <em>{battery_label}</em>
  </div>

</div>
"""
