from energy_brain.ui.powerflow_v2.styles import render_powerflow_v2_css

def render_powerflow_v2():
    return f"""
<style>
{render_powerflow_v2_css()}
</style>

<div class="pf-v2">

  <div class="pf-node pf-solar">
    <span>Zon</span>
  </div>

  <div class="pf-node pf-home">
    <span>Huis</span>
  </div>

  <div class="pf-node pf-grid">
    <span>Net</span>
  </div>

  <div class="pf-node pf-battery">
    <span>Batterij</span>
  </div>

</div>
"""
