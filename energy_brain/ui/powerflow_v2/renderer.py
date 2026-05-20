import html

from energy_brain.ui.powerflow_v2.styles import render_powerflow_v2_css


def _esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def render_powerflow_v2(
    grid_flow: str = "idle",
    battery_flow: str = "idle",
    *,
    solar_label: str = "Live kW",
    home_label: str = "Verbruik",
    grid_label: str | None = None,
    battery_label: str | None = None,
    soc_label: str = "Stand-by",
):
    grid_label = {
        "importing": "Import",
        "exporting": "Export",
    }.get(grid_flow, "Stand-by") if grid_label is None else grid_label
    battery_label = {
        "charging": "Laden",
        "discharging": "Levert",
    }.get(battery_flow, "Stand-by") if battery_label is None else battery_label
    return f"""
<style>
{render_powerflow_v2_css()}
</style>

<div class="pf-v2" aria-label="Realtime energiestroom" data-grid-flow="{_esc(grid_flow)}" data-battery-flow="{_esc(battery_flow)}">
  <div class="pf-caption">Energiestroom</div>

  <div class="pf-node pf-solar">
    <span>Zon</span>
    <em>{_esc(solar_label)}</em>
  </div>

  <div class="pf-node pf-home">
    <span>Huis</span>
    <em>{_esc(home_label)}</em>
  </div>

  <div class="pf-node pf-grid">
    <span>Net</span>
    <em>{_esc(grid_label)}</em>
  </div>

  <div class="pf-node pf-battery">
    <i class="pf-battery-shell" aria-hidden="true"><b></b></i>
    <strong>{_esc(soc_label)}</strong>
    <span>Batterij</span>
    <em>{_esc(battery_label)}</em>
  </div>

</div>
"""
