from __future__ import annotations

from energy_brain.ui.themes.tokens import css_vars


def render_theme_css() -> str:
    return f"""
    /* Tokens */
    :root {{
      color-scheme: dark;
      {css_vars()}
      --bg: #04070a;
      --surface: rgba(8, 12, 17, 0.62);
      --surface-strong: rgba(12, 18, 25, 0.82);
      --glass: linear-gradient(180deg, rgba(255,255,255,0.044), rgba(255,255,255,0.010));
      --line: rgba(255, 255, 255, 0.052);
      --line-strong: rgba(255, 255, 255, 0.13);
      --text: #f5f8fb;
      --muted: #98a5b2;
      --subtle: #65717e;
      --solar: #ffd166;
      --home: #58e8b6;
      --battery: #65f0a7;
      --grid: #7fc7ff;
      --import: #ff8b5f;
      --export: #ffe083;
      --danger: #ff687c;
      --violet: #c792ff;
      --scene-intensity: 0;
    }}

    * {{ box-sizing: border-box; }}
    html {{ background: var(--bg); }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background:
        radial-gradient(circle at 50% 26%, rgba(88, 232, 182, 0.12), transparent 32rem),
        radial-gradient(circle at 82% 16%, rgba(255, 209, 102, 0.055), transparent 24rem),
        radial-gradient(circle at 12% 76%, rgba(127, 199, 255, 0.055), transparent 23rem),
        linear-gradient(180deg, #071017 0%, #04070a 58%, #020304 100%);
      background-size: auto;
      font-family: var(--font-ui);
      letter-spacing: 0;
      overflow-x: hidden;
    }}
    a {{ color: inherit; }}
    .sr-only {{
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    }}

    /* Layout */
    .shell {{
      width: min(1500px, 100%);
      min-height: 100vh;
      margin: 0 auto;
      padding: var(--shell-pad, 10px);
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: var(--shell-gap, 12px);
    }}
    .topline {{
      position: sticky;
      top: 0;
      z-index: 20;
      min-height: 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 6px 8px;
      border: 0;
      border-radius: 0;
      background: linear-gradient(180deg, rgba(4, 7, 10, 0.76), rgba(4, 7, 10, 0.16));
      backdrop-filter: blur(22px);
    }}
    .brand-block {{ min-width: 0; }}
    .brand {{ font-size: 18px; font-weight: 780; line-height: 1.05; }}
    .eyebrow {{
      color: var(--muted);
      font-size: 10px;
      font-weight: 720;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .dashboard {{
      display: grid;
      grid-template-columns: var(--dashboard-columns, minmax(0, 1fr));
      gap: var(--dashboard-gap, 10px);
      align-items: stretch;
    }}
    .side {{
      display: grid;
      grid-template-columns: var(--side-columns, minmax(0, 1fr));
      grid-auto-rows: max-content;
      gap: var(--dashboard-gap, 10px);
      min-width: 0;
    }}

    /* Controls */
    .layout-switcher {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 3px;
      width: var(--switcher-width, 100%);
      padding: 3px;
      border: 1px solid rgba(255,255,255,0.045);
      border-radius: var(--radius-round);
      background: rgba(255,255,255,0.020);
    }}
    .layout-switcher a, .chip, .quality-chip {{
      min-height: 26px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      text-decoration: none;
      border: 1px solid transparent;
      border-radius: var(--radius-round);
      padding: 5px 9px;
      font-size: 10px;
      font-weight: 720;
      transition: color var(--motion-base), background var(--motion-base), border-color var(--motion-base), box-shadow var(--motion-base), transform var(--motion-fast);
    }}
    .layout-switcher a.active {{
      color: var(--text);
      border-color: rgba(88,232,182,0.3);
      background: rgba(88,232,182,0.09);
      box-shadow: 0 0 20px rgba(88,232,182,0.12), inset 0 1px 0 rgba(255,255,255,0.06);
    }}

    /* Health Strip */
    .health-strip {{
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding: 0 4px;
      border: 0;
      border-radius: 0;
      background: transparent;
      scrollbar-width: none;
    }}
    .energy-state-island {{
      justify-content: center;
      opacity: 0.9;
    }}
    .health-strip-item {{
      position: relative;
      flex: 0 0 auto;
      min-width: 0;
      padding: 6px 10px 6px 24px;
      border: 1px solid rgba(255,255,255,0.052);
      border-radius: var(--radius-round);
      background: rgba(5, 8, 12, 0.46);
      backdrop-filter: blur(18px);
    }}
    .health-strip-item i, .status-dot {{
      position: absolute;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--battery);
      box-shadow: 0 0 16px rgba(101,240,167,0.62);
      animation: dotPulse 2.8s ease-in-out infinite;
    }}
    .health-strip-item i {{ left: 12px; top: 50%; transform: translateY(-50%); }}
    .health-strip-item span, .strategy-metrics span, .health-pill span {{
      display: block;
      color: var(--muted);
      font-size: 10px;
      font-weight: 720;
      text-transform: uppercase;
      letter-spacing: 0.07em;
    }}
    .health-strip-item b {{
      display: block;
      margin-top: 3px;
      overflow: hidden;
      color: var(--text);
      font-size: 10px;
      font-weight: 760;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    /* Panels */
    .hero, .panel {{
      border: 1px solid rgba(255,255,255,0.038);
      border-radius: var(--radius-lg);
      background: var(--glass), rgba(8, 12, 17, 0.40);
      backdrop-filter: blur(26px);
      box-shadow: 0 20px 74px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.045);
    }}
    .hero {{
      position: relative;
      min-height: var(--hero-min, 540px);
      padding: var(--hero-pad, 14px);
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(330px, 1fr) auto;
      background:
        radial-gradient(circle at 50% 50%, rgba(101,240,167,calc(0.08 + var(--scene-intensity) * 0.12)), transparent 30%),
        radial-gradient(circle at 50% 18%, rgba(255,209,102,0.05), transparent 28%),
        linear-gradient(180deg, rgba(255,255,255,0.042), rgba(255,255,255,0.008)),
        rgba(5,8,12,0.62);
      border-color: rgba(255,255,255,0.026);
      box-shadow: 0 30px 110px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.052);
    }}
    .hero:before {{
      content: "";
      position: absolute;
      inset: 12% 9%;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(88,232,182,0.18), transparent 58%), radial-gradient(circle at 40% 35%, rgba(255,209,102,0.12), transparent 44%), radial-gradient(circle at 66% 64%, rgba(127,199,255,0.11), transparent 42%);
      filter: blur(22px);
      opacity: calc(0.42 + var(--scene-intensity) * 0.22);
      animation: liveGlow 7.8s ease-in-out infinite;
      pointer-events: none;
    }}
    .hero-head, .hero-foot {{
      position: relative;
      z-index: 2;
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
    }}
    .hero-head {{
      min-height: 46px;
      align-items: center;
    }}
    .hero-foot {{
      z-index: 4;
      align-items: center;
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 8px;
    }}
    .decision {{
      max-width: 500px;
      margin-top: var(--space-xs);
      font-size: var(--decision-size, 22px);
      line-height: 1.06;
      font-weight: 730;
    }}
    .soc {{ text-align: right; min-width: 84px; }}
    .soc strong {{ display: block; color: var(--battery); font-size: var(--soc-size, 38px); line-height: 0.95; }}
    .quality-chip {{
      min-height: 23px;
      border-color: rgba(255,255,255,0.055);
      background: rgba(255,255,255,0.02);
      color: var(--subtle);
    }}
    .quality-chip i {{
      width: 5px;
      height: 5px;
      margin-right: 6px;
      border-radius: 50%;
      background: currentColor;
      box-shadow: 0 0 10px currentColor;
    }}
    .quality-live {{ color: rgba(101,240,167,0.9); border-color: rgba(101,240,167,0.16); background: rgba(101,240,167,0.045); }}
    .quality-degraded {{ color: rgba(255,209,102,0.9); border-color: rgba(255,209,102,0.16); background: rgba(255,209,102,0.045); }}
    .panel {{ padding: var(--panel-pad, 14px); min-width: 0; }}
    .ambient-panel {{
      border-color: rgba(255,255,255,0.04);
      background: linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.012));
      box-shadow: none;
    }}
    .panel h2 {{ margin: 0; font-size: 18px; line-height: 1.16; font-weight: 760; }}
    .panel p {{ color: var(--muted); margin: 7px 0 0; line-height: 1.42; }}
    .panel-head {{ position: relative; display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }}
    .status-dot {{ position: static; display: inline-block; }}

    /* Powerflow */
    .flow-map {{
      position: relative;
      z-index: 1;
      align-self: center;
      justify-self: center;
      width: min(var(--flow-size, 420px), 100%);
      margin: var(--flow-margin, 0);
      aspect-ratio: 1;
      isolation: isolate;
    }}
    .flow-map:before {{
      content: "";
      position: absolute;
      inset: 7%;
      border-radius: 50%;
      background:
        radial-gradient(circle, transparent 47%, rgba(255,255,255,0.045) 48%, transparent 49%),
        conic-gradient(from 25deg, rgba(88,232,182,0.10), rgba(255,209,102,0.07), rgba(127,199,255,0.09), rgba(88,232,182,0.10));
      opacity: calc(0.22 + var(--scene-intensity) * 0.20);
      pointer-events: none;
    }}
    .flow-svg {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }}
    .flow-svg defs path {{ fill: none; }}
    .flow-backbone, .flow-ribbons, .flow-particles {{ pointer-events: none; }}
    .flow-lane {{
      fill: none;
      stroke: rgba(255,255,255,0.082);
      stroke-width: calc(var(--lane-width) * 1px);
      stroke-linecap: round;
      opacity: calc(0.24 + var(--flow-intensity) * 0.52);
      filter: drop-shadow(0 0 calc(5px + var(--flow-intensity) * 18px) rgba(88,232,182,var(--energy-glow)));
      transition: stroke var(--motion-base), stroke-width var(--motion-base), opacity var(--motion-base), filter var(--motion-base);
    }}
    .flow-lane.tone-solar, .flow-pulse.tone-solar {{ stroke: url(#solar-flow); }}
    .flow-lane.tone-export, .flow-pulse.tone-export {{ stroke: url(#export-flow); }}
    .flow-lane.tone-home, .flow-pulse.tone-home {{ stroke: url(#solar-flow); }}
    .flow-lane.tone-battery, .flow-pulse.tone-battery {{ stroke: url(#grid-flow); }}
    .flow-lane.tone-grid.state-importing, .flow-pulse.tone-grid.state-importing {{ stroke: url(#import-flow); }}
    .flow-lane.tone-grid.state-exporting, .flow-pulse.tone-grid.state-exporting {{ stroke: url(#export-flow); }}
    .flow-lane.state-idle {{ stroke: rgba(255,255,255,0.10); filter: none; opacity: 0.42; }}
    .flow-pulse {{
      fill: none;
      stroke-width: calc((var(--lane-width) * 0.42) * 1px);
      stroke-linecap: round;
      stroke-dasharray: calc(8px + var(--flow-intensity) * 18px) calc(28px - var(--flow-intensity) * 10px);
      animation: flowTravel var(--flow-speed) cubic-bezier(0.26, 0.72, 0.24, 1) infinite, flowPresence var(--flow-speed) ease-in-out infinite;
      opacity: calc(var(--flow-intensity) * 0.68);
      mix-blend-mode: screen;
    }}
    .flow-pulse.state-idle {{ opacity: 0; }}
    .flow-pulse.state-discharging, .flow-pulse.state-exporting {{ animation-timing-function: cubic-bezier(0.2, 0.72, 0.22, 1); }}
    .flow-dot {{
      opacity: 0;
      fill: #f9fff8;
      filter: drop-shadow(0 0 8px rgba(101,240,167,0.66)) drop-shadow(0 0 18px rgba(101,240,167,0.34));
    }}
    .flow-dot.tone-solar, .flow-dot.tone-home {{ fill: #fff0a6; filter: drop-shadow(0 0 8px rgba(255,209,102,0.72)) drop-shadow(0 0 18px rgba(88,232,182,0.32)); }}
    .flow-dot.tone-export {{ fill: #ffe58f; filter: drop-shadow(0 0 8px rgba(255,209,102,0.74)) drop-shadow(0 0 20px rgba(255,209,102,0.34)); }}
    .flow-dot.tone-battery {{ fill: #8fd7ff; }}
    .flow-dot.tone-grid.state-importing {{ fill: #ffad7a; filter: drop-shadow(0 0 8px rgba(255,139,95,0.74)) drop-shadow(0 0 20px rgba(255,139,95,0.34)); }}
    .flow-dot.tone-grid.state-exporting {{ fill: #ffe58f; filter: drop-shadow(0 0 8px rgba(255,209,102,0.74)) drop-shadow(0 0 20px rgba(255,209,102,0.34)); }}
    .junction-aura {{
      fill: url(#junction-glow);
      opacity: calc(0.22 + var(--scene-intensity) * 0.34);
      transform-origin: 210px 210px;
      animation: junctionBreath 7.4s ease-in-out infinite;
    }}
    .junction-core {{
      fill: rgba(249,255,250,0.92);
      filter: drop-shadow(0 0 14px rgba(101,240,167,0.52));
      transform-origin: 210px 210px;
      animation: corePulse 5.8s ease-in-out infinite;
    }}

    /* Nodes */
    .orb {{
      --soc: 0;
      position: absolute;
      inset: var(--orb-inset, 29%);
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: radial-gradient(circle at 40% 30%, rgba(255,255,255,0.16), transparent 25%), radial-gradient(circle, rgba(12,18,24,0.98) 52%, rgba(88,232,182,0.18) 76%, rgba(127,199,255,0.08));
      box-shadow: 0 0 calc(42px + var(--scene-intensity) * 52px) rgba(88,232,182,0.18), inset 0 0 38px rgba(255,255,255,0.045);
      animation: orbPulse 7.6s ease-in-out infinite;
    }}
    .orb:before {{
      content: "";
      position: absolute;
      inset: -18px;
      border-radius: inherit;
      background: conic-gradient(from 0deg, transparent 0 44deg, rgba(101,240,167,0.18) 66deg, transparent 98deg 360deg);
      opacity: calc(0.18 + var(--scene-intensity) * 0.28);
      filter: blur(1px);
      animation: orbIdleDrift 11s linear infinite;
      pointer-events: none;
    }}
    .flow-map[data-orb-state="charging"] .orb,
    .flow-map[data-orb-state="cheap-charging"] .orb {{
      background: radial-gradient(circle at 40% 30%, rgba(255,255,255,0.18), transparent 25%), radial-gradient(circle, rgba(10,18,22,0.98) 51%, rgba(101,240,167,0.25) 74%, rgba(127,199,255,0.10));
      box-shadow: 0 0 calc(50px + var(--scene-intensity) * 64px) rgba(101,240,167,0.24), inset 0 0 42px rgba(101,240,167,0.075);
      animation-name: orbChargePulse;
    }}
    .flow-map[data-orb-state="charging"] .orb:before,
    .flow-map[data-orb-state="cheap-charging"] .orb:before {{
      background: radial-gradient(circle, transparent 54%, rgba(101,240,167,0.20) 59%, transparent 66%);
      animation: orbInward 4.8s ease-in-out infinite;
    }}
    .flow-map[data-orb-state="discharging"] .orb {{
      background: radial-gradient(circle at 40% 30%, rgba(255,255,255,0.16), transparent 25%), radial-gradient(circle, rgba(10,17,24,0.98) 50%, rgba(127,199,255,0.28) 75%, rgba(101,240,167,0.06));
      box-shadow: 0 0 calc(46px + var(--scene-intensity) * 56px) rgba(127,199,255,0.23), inset 0 0 38px rgba(127,199,255,0.075);
    }}
    .flow-map[data-orb-state="discharging"] .orb:before {{
      background: radial-gradient(circle, transparent 57%, rgba(127,199,255,0.26) 62%, transparent 70%);
      animation: orbOutward 3.8s ease-out infinite;
    }}
    .flow-map[data-orb-state="reserve-protected"] .orb {{
      background: radial-gradient(circle at 42% 32%, rgba(255,255,255,0.10), transparent 24%), radial-gradient(circle, rgba(13,15,18,0.98) 52%, rgba(255,139,95,0.22) 76%, rgba(101,240,167,0.06));
      box-shadow: 0 0 36px rgba(255,139,95,0.14), inset 0 0 30px rgba(255,139,95,0.055);
      animation-duration: 9s;
    }}
    .flow-map[data-orb-state="export-mode"] .orb {{
      background: radial-gradient(circle at 42% 32%, rgba(255,255,255,0.17), transparent 25%), radial-gradient(circle, rgba(18,16,10,0.98) 51%, rgba(255,209,102,0.33) 75%, rgba(255,241,168,0.12));
      box-shadow: 0 0 calc(54px + var(--scene-intensity) * 68px) rgba(255,209,102,0.26), inset 0 0 40px rgba(255,209,102,0.075);
    }}
    .flow-map[data-orb-state="export-mode"] .orb:before {{
      background: conic-gradient(from 12deg, transparent 0 32deg, rgba(255,209,102,0.34) 54deg, transparent 86deg 360deg);
      animation: orbExportHalo 4.4s linear infinite;
    }}
    .orb:after {{
      content: "";
      position: absolute;
      inset: -9px;
      border-radius: inherit;
      border: 1px solid rgba(101,240,167,0.18);
      box-shadow: 0 0 42px rgba(101,240,167,0.14);
      animation: orbitBreath 6.4s ease-in-out infinite;
    }}
    .orb-ring {{
      position: absolute;
      inset: 9px;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,0.12);
      background: radial-gradient(circle, rgba(255,255,255,0.06), transparent 62%);
    }}
    .orb-soc-ring {{
      position: absolute;
      inset: -2px;
      border-radius: inherit;
      background: conic-gradient(from -90deg, #65f0a7 calc(var(--soc) * 1%), rgba(255,255,255,0.075) 0);
      mask: radial-gradient(circle, transparent 63%, #000 64% 70%, transparent 71%);
      animation: orbChargeBreath 5.8s ease-in-out infinite;
      pointer-events: none;
    }}
    .reserve-band {{
      position: absolute;
      inset: 15px;
      border-radius: 50%;
      background: conic-gradient(from 198deg, rgba(255,139,95,0.48) 0 38deg, transparent 38deg 360deg);
      mask: radial-gradient(circle, transparent 61%, #000 62% 69%, transparent 70%);
      opacity: 0.22;
      pointer-events: none;
    }}
    .flow-map[data-orb-state="reserve-protected"] .reserve-band {{ opacity: 0.82; }}
    .orb-core {{ position: relative; z-index: 2; text-align: center; }}
    .orb-core span, .orb-core em {{ display: block; color: var(--muted); font-size: 10px; font-style: normal; }}
    .orb-core b {{ display: block; margin: 2px 0 4px; font-size: var(--orb-value-size, 34px); line-height: 1; }}
    .node {{
      --node-intensity: 0;
      position: absolute;
      width: var(--node-size, 82px);
      min-height: var(--node-size, 82px);
      padding: var(--node-pad, 12px 8px);
      border: 1px solid rgba(255,255,255,0.064);
      border-radius: 50%;
      display: grid;
      place-items: center;
      align-content: center;
      text-align: center;
      background: radial-gradient(circle at 35% 24%, rgba(255,255,255,0.10), transparent 28%), radial-gradient(circle at 50% 58%, rgba(8,12,17,0.86), rgba(8,12,17,0.50) 62%, rgba(255,255,255,0.022));
      box-shadow: 0 12px 30px rgba(0,0,0,0.20), inset 0 1px 0 rgba(255,255,255,0.052), 0 0 calc(8px + var(--node-intensity) * 24px) rgba(101,240,167,0.08);
      overflow: hidden;
      transition: opacity var(--motion-base), border-color var(--motion-base), transform var(--motion-base), box-shadow var(--motion-base);
      animation: nodeBreathe 5.6s ease-in-out infinite;
    }}
    .node:before {{
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: conic-gradient(from 140deg, var(--node-ring), rgba(255,255,255,0.05), var(--node-ring));
      opacity: calc(0.18 + var(--node-intensity) * 0.28);
      mask: radial-gradient(circle, transparent 57%, #000 58% 69%, transparent 70%);
      animation: nodeHalo 6.8s ease-in-out infinite;
      pointer-events: none;
    }}
    .node i {{
      position: absolute;
      inset: 10px;
      border-radius: inherit;
      background: radial-gradient(circle at 50% 16%, var(--node-ring), transparent 50%);
      opacity: calc(0.15 + var(--node-intensity) * 0.26);
      pointer-events: none;
    }}
    .node span {{ position: relative; color: var(--muted); font-size: var(--node-label-size, 9px); font-weight: 720; text-transform: uppercase; letter-spacing: 0.06em; }}
    .node b {{ position: relative; display: block; min-height: 1em; margin-top: 3px; font-size: var(--node-value-size, 13px); line-height: 1.04; }}
    .node.unknown {{
      opacity: 0.34;
      border-style: solid;
      filter: grayscale(0.42);
      box-shadow: 0 10px 28px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.045);
    }}
    .node.unknown:before, .node.unknown i {{ opacity: 0.08; }}
    .node.unknown b {{ display: none; }}
    .node-solar {{ top: 0; left: 50%; transform: translateX(-50%); }}
    .node-home {{ right: 0; top: 50%; transform: translateY(-50%); }}
    .node-battery {{ left: 0; top: 50%; transform: translateY(-50%); }}
    .node-grid {{ bottom: 0; left: 50%; transform: translateX(-50%); }}
    .node-grid.state-exporting b {{ color: var(--export); }}
    .node-grid.state-importing b {{ color: var(--import); }}
    .node-battery.state-discharging b {{ color: var(--grid); }}
    .node-battery.state-charging b {{ color: var(--battery); }}

    .intent-orbit {{
      width: 100%;
      margin: 0;
      padding: 0;
      list-style: none;
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-start;
      gap: 6px;
    }}
    .intent-orbit li, .telemetry-pill {{
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: var(--radius-round);
      background: rgba(4,8,12,0.32);
      box-shadow: 0 8px 20px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.035);
      backdrop-filter: blur(18px);
      color: var(--text);
      font-size: 9px;
      font-weight: 740;
      padding: 5px 7px;
      white-space: nowrap;
    }}
    .intent-orbit li:before {{
      content: "";
      display: inline-block;
      width: 6px;
      height: 6px;
      margin-right: 7px;
      border-radius: 50%;
      background: var(--battery);
      box-shadow: 0 0 12px rgba(101,240,167,0.55);
      vertical-align: 1px;
    }}
    .micro-telemetry {{
      width: 100%;
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
    }}
    .telemetry-pill {{
      color: var(--muted);
      font-size: 9px;
      padding: 5px 8px;
    }}
    .telemetry-pill b {{
      color: var(--text);
      margin-right: 5px;
      font-size: 9px;
    }}

    /* Timeline */
    .strategy-why {{ color: var(--muted); margin: 10px 0 0; font-size: 14px; line-height: 1.42; }}
    .strategy-metrics {{
      display: grid;
      grid-template-columns: var(--metric-columns, 1fr);
      gap: var(--space-sm);
      margin: 13px 0;
    }}
    .strategy-metrics div, .health-pill {{
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: var(--radius-md);
      background: rgba(255,255,255,0.026);
      padding: 9px;
    }}
    .strategy-metrics b, .health-pill b {{ display: block; margin-top: 3px; font-size: 14px; }}
    .horizon {{
      margin: 13px 0 8px;
      border: 1px solid rgba(255,255,255,0.055);
      border-radius: var(--radius-md);
      background: linear-gradient(180deg, rgba(255,255,255,0.038), rgba(255,255,255,0.012)), rgba(3,6,9,0.34);
      overflow: hidden;
    }}
    .horizon-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-sm);
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255,255,255,0.055);
    }}
    .horizon-head span {{ color: var(--text); font-size: 13px; font-weight: 760; }}
    .horizon-head b {{ color: var(--muted); font-size: 11px; font-weight: 680; }}
    .horizon-grid {{
      position: relative;
      display: grid;
      grid-template-columns: repeat(24, minmax(10px, 1fr));
      min-height: 104px;
      padding: 9px 8px 17px;
      gap: 2px;
    }}
    .horizon-grid:before {{
      content: "";
      position: absolute;
      left: 10px;
      right: 10px;
      bottom: 32px;
      height: 18px;
      border-top: 1px solid rgba(255,139,95,0.34);
      border-bottom: 1px solid rgba(255,139,95,0.16);
      background: rgba(255,139,95,0.05);
      pointer-events: none;
    }}
    .horizon-hour {{ position: relative; min-width: 0; border-radius: 5px; background: rgba(255,255,255,0.035); overflow: hidden; }}
    .horizon-hour.unknown {{ opacity: 0.32; }}
    .horizon-hour span {{ position: absolute; left: 50%; bottom: 3px; transform: translateX(-50%); color: var(--subtle); font-size: 9px; }}
    .horizon-hour i {{ position: absolute; left: 20%; right: 20%; bottom: 23px; height: calc(var(--soc) * 0.62px); border-radius: 999px 999px 3px 3px; background: linear-gradient(180deg, rgba(101,240,167,0.92), rgba(88,232,182,0.3)); box-shadow: 0 0 16px rgba(101,240,167,0.18); }}
    .horizon-hour b {{ position: absolute; left: 0; right: 0; top: calc(84px - var(--price) * 0.74px); height: 2px; background: rgba(255,209,102,0.82); box-shadow: 0 0 12px rgba(255,209,102,0.28); }}
    .horizon-hour.unknown i, .horizon-hour.unknown b {{ display: none; }}
    .horizon-hour.tone-charge {{ background: linear-gradient(180deg, rgba(101,240,167,0.2), rgba(255,255,255,0.025)); }}
    .horizon-hour.tone-discharge {{ background: linear-gradient(180deg, rgba(127,199,255,0.18), rgba(255,255,255,0.025)); }}
    .horizon-hour.tone-cheap {{ background: linear-gradient(180deg, rgba(88,232,182,0.16), rgba(255,255,255,0.025)); }}
    .horizon-hour.tone-expensive {{ background: linear-gradient(180deg, rgba(255,139,95,0.18), rgba(255,255,255,0.025)); }}
    .horizon-legend {{ display: flex; flex-wrap: wrap; gap: 7px; padding: 0 11px 10px; }}
    .horizon-legend span {{ border: 1px solid rgba(255,255,255,0.06); border-radius: var(--radius-round); color: var(--muted); background: rgba(255,255,255,0.026); padding: 5px 8px; font-size: 10px; font-weight: 720; }}
    .timeline {{
      min-height: 86px;
      display: flex;
      align-items: stretch;
      gap: 6px;
      overflow-x: auto;
      padding: 8px 2px 12px;
      scrollbar-width: thin;
    }}
    .timeline-block {{
      flex: 0 0 calc(var(--span) * 1%);
      min-width: 112px;
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: var(--radius-md);
      padding: 9px;
      background: rgba(255,255,255,0.04);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
    }}
    .timeline-block span {{ color: var(--muted); font-size: 11px; }}
    .timeline-block b {{ display: block; margin-top: 9px; font-size: 13px; line-height: 1.2; }}
    .tone-charge, .tone-cheap {{ background: linear-gradient(180deg, rgba(88,232,182,0.22), rgba(88,232,182,0.045)); border-color: rgba(88,232,182,0.28); }}
    .tone-discharge {{ background: linear-gradient(180deg, rgba(127,199,255,0.22), rgba(127,199,255,0.045)); border-color: rgba(127,199,255,0.28); }}
    .tone-expensive {{ background: linear-gradient(180deg, rgba(255,104,124,0.18), rgba(255,104,124,0.035)); border-color: rgba(255,104,124,0.26); }}
    .plan-list, .reason-stack {{ display: grid; gap: 8px; margin-top: var(--space-sm); }}
    .reason-item {{ border-top: 1px solid var(--line); padding-top: 8px; color: var(--muted); }}
    .reason-item summary {{ cursor: pointer; color: var(--text); font-size: 13px; }}
    .reason-stack p {{ margin: 0; padding: 10px 12px; border: 1px solid rgba(255,255,255,0.075); border-radius: var(--radius-md); background: rgba(255,255,255,0.025); color: var(--text); font-size: 13px; }}
    .compact-reasons p {{ position: relative; padding-left: 28px; }}
    .compact-reasons p:before {{ content: ""; position: absolute; left: 12px; top: 17px; width: 6px; height: 6px; border-radius: 50%; background: var(--battery); box-shadow: 0 0 12px rgba(101,240,167,0.5); }}

    /* Diagnostics */
    .diagnostic-overlay {{
      margin-top: 12px;
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }}
    .diagnostic-overlay summary {{ cursor: pointer; color: var(--muted); font-size: 12px; font-weight: 760; }}
    .diagnostic-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }}
    .diagnostic-grid span {{
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      padding: 8px;
      color: var(--muted);
      background: rgba(255,255,255,0.028);
      font-size: 12px;
    }}
    .diagnostic-grid b {{ display: block; color: var(--text); margin-top: 3px; }}
    .health-row {{ display: grid; grid-template-columns: var(--health-columns, 1fr); gap: var(--space-sm); }}
    .battery-mode {{ border: 1px solid var(--line); border-radius: var(--radius-round); color: var(--muted); background: rgba(255,255,255,0.035); padding: 5px 9px; font-size: 11px; font-weight: 760; }}
    .battery-mode.charging {{ color: var(--battery); border-color: rgba(101,240,167,0.28); background: rgba(101,240,167,0.08); }}
    .battery-mode.discharging {{ color: var(--grid); border-color: rgba(127,199,255,0.28); background: rgba(127,199,255,0.08); }}
    .battery-visual {{ --soc: 0; display: grid; grid-template-columns: 72px minmax(0, 1fr); gap: var(--space-md); align-items: center; margin-top: var(--space-sm); }}
    .battery-shell {{ position: relative; height: 96px; border: 1px solid rgba(255,255,255,0.16); border-radius: 18px; background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)); box-shadow: inset 0 0 24px rgba(255,255,255,0.035), 0 0 34px rgba(101,240,167,0.1); overflow: hidden; }}
    .battery-shell:before {{ content: ""; position: absolute; left: 30%; right: 30%; top: -7px; height: 7px; border-radius: 7px 7px 0 0; background: rgba(255,255,255,0.18); }}
    .battery-shell span {{ position: absolute; left: 8px; right: 8px; bottom: 8px; height: calc(var(--soc) * 1%); border-radius: 12px; background: linear-gradient(180deg, #7fc7ff, #65f0a7); box-shadow: 0 0 28px rgba(101,240,167,0.32); transition: height var(--motion-base); }}
    .battery-visual strong {{ display: block; font-size: var(--battery-value-size, 42px); line-height: 0.95; }}
    .battery-visual p {{ margin-top: 7px; }}
    .battery-meta, .metric-row {{ display: flex; justify-content: space-between; gap: var(--space-sm); margin-top: var(--space-md); color: var(--muted); font-size: 12px; }}
    .metric-row {{ border-top: 1px solid var(--line); padding-top: var(--space-sm); }}
    .metric-row b {{ color: var(--text); text-align: right; }}
    .error-page {{ min-height: 100vh; display: grid; place-items: center; padding: var(--space-lg); }}
    .error-page .panel {{ max-width: 520px; }}

    /* Responsive: canonical viewport engine writes body[data-viewport]. */
    body[data-viewport="mobile"] {{
      --shell-pad: 7px;
      --shell-gap: 7px;
      --dashboard-columns: minmax(0, 1fr);
      --dashboard-gap: 7px;
      --switcher-width: 100%;
      --hero-min: min(590px, calc(100vh - 112px));
      --hero-pad: 12px;
      --flow-size: min(402px, calc(100vw - 18px));
      --flow-margin: -6px 0 -2px;
      --node-size: 76px;
      --node-pad: 10px 7px;
      --node-label-size: 9px;
      --node-value-size: 12px;
      --orb-inset: 29%;
      --orb-value-size: 33px;
      --decision-size: 20px;
      --soc-size: 29px;
      --panel-pad: 12px;
      --metric-columns: 1fr;
      --health-columns: 1fr;
      --battery-value-size: 36px;
    }}
    body[data-viewport="mobile"] .topline {{ align-items: flex-start; flex-direction: column; }}
    body[data-viewport="mobile"] .brand-block {{ display: none; }}
    body[data-viewport="mobile"] .layout-switcher {{ display: none; }}
    body[data-viewport="mobile"] .energy-state-island {{
      justify-content: flex-start;
      mask-image: linear-gradient(90deg, #000 88%, transparent);
    }}
    body[data-viewport="mobile"] .health-strip-item:nth-child(n+4) {{ display: none; }}
    body[data-viewport="mobile"] .hero-foot {{ gap: 8px; }}
    body[data-viewport="mobile"] .side {{
      grid-template-columns: minmax(0, 1fr);
    }}
    body[data-viewport="mobile"] .battery-panel,
    body[data-viewport="mobile"] .health-panel {{
      display: none;
    }}

    body[data-viewport="tablet"] {{
      --shell-pad: 16px;
      --shell-gap: 12px;
      --dashboard-columns: minmax(0, 1fr) minmax(320px, 0.9fr);
      --dashboard-gap: 12px;
      --switcher-width: auto;
      --hero-min: 590px;
      --hero-pad: 20px;
      --flow-size: 510px;
      --node-size: 96px;
      --node-pad: 13px 9px;
      --node-label-size: 10px;
      --node-value-size: 16px;
      --orb-inset: 29%;
      --orb-value-size: 42px;
      --decision-size: 30px;
      --soc-size: 42px;
      --panel-pad: 16px;
      --metric-columns: repeat(3, minmax(0, 1fr));
      --health-columns: repeat(2, minmax(0, 1fr));
      --battery-value-size: 44px;
    }}

    body[data-viewport="desktop"] {{
      --shell-pad: 28px;
      --shell-gap: 14px;
      --dashboard-columns: minmax(0, 1.38fr) minmax(390px, 0.82fr);
      --dashboard-gap: 24px;
      --switcher-width: auto;
      --hero-min: calc(100vh - 132px);
      --hero-pad: 28px;
      --flow-size: 620px;
      --node-size: 106px;
      --node-pad: 15px 11px;
      --node-label-size: 11px;
      --node-value-size: 18px;
      --orb-inset: 29%;
      --orb-value-size: 54px;
      --decision-size: 36px;
      --soc-size: 52px;
      --panel-pad: 18px;
      --metric-columns: repeat(3, minmax(0, 1fr));
      --health-columns: repeat(2, minmax(0, 1fr));
      --battery-value-size: 52px;
    }}
    body[data-viewport="desktop"] .strategy-panel {{ position: sticky; top: 24px; }}
    body[data-viewport="desktop"] .node:hover {{
      transform: translateY(-50%) scale(1.045);
      border-color: rgba(255,255,255,0.24);
      box-shadow: 0 22px 58px rgba(0,0,0,0.34), 0 0 calc(24px + var(--node-intensity) * 44px) rgba(101,240,167,0.2);
    }}
    body[data-viewport="desktop"] .node-solar:hover,
    body[data-viewport="desktop"] .node-grid:hover {{ transform: translateX(-50%) scale(1.045); }}

    /* Animation */
    @keyframes flowTravel {{ from {{ stroke-dashoffset: 0; }} to {{ stroke-dashoffset: -96; }} }}
    @keyframes flowPresence {{ 0%, 100% {{ opacity: calc(var(--flow-intensity) * 0.18); }} 20%, 72% {{ opacity: calc(var(--flow-intensity) * 0.70); }} }}
    @keyframes orbPulse {{ 0%, 100% {{ transform: scale(1); filter: brightness(1); }} 50% {{ transform: scale(1.01); filter: brightness(1.04); }} }}
    @keyframes orbChargePulse {{ 0%, 100% {{ transform: scale(1); filter: brightness(1.02); }} 48% {{ transform: scale(1.024); filter: brightness(1.08); }} }}
    @keyframes orbChargeBreath {{ 0%, 100% {{ opacity: 0.64; transform: scale(0.994); }} 50% {{ opacity: 0.92; transform: scale(1.01); }} }}
    @keyframes orbitBreath {{ 0%, 100% {{ opacity: 0.28; transform: scale(0.992); }} 50% {{ opacity: 0.58; transform: scale(1.01); }} }}
    @keyframes orbIdleDrift {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    @keyframes orbInward {{ 0% {{ opacity: 0; transform: scale(1.18); }} 36% {{ opacity: 0.72; }} 100% {{ opacity: 0; transform: scale(0.82); }} }}
    @keyframes orbOutward {{ 0% {{ opacity: 0.58; transform: scale(0.86); }} 100% {{ opacity: 0; transform: scale(1.28); }} }}
    @keyframes orbExportHalo {{ from {{ transform: rotate(0deg) scale(1.02); }} to {{ transform: rotate(360deg) scale(1.02); }} }}
    @keyframes liveGlow {{ 0%, 100% {{ opacity: 0.68; transform: scale(0.98); }} 50% {{ opacity: 1; transform: scale(1.03); }} }}
    @keyframes dotPulse {{ 0%, 100% {{ opacity: 0.62; transform: scale(0.94); }} 50% {{ opacity: 0.9; transform: scale(1.06); }} }}
    @keyframes junctionBreath {{ 0%, 100% {{ opacity: 0.24; transform: scale(0.96); }} 50% {{ opacity: 0.62; transform: scale(1.04); }} }}
    @keyframes corePulse {{ 0%, 100% {{ opacity: 0.62; transform: scale(0.9); }} 50% {{ opacity: 0.9; transform: scale(1.08); }} }}
    @keyframes nodeHalo {{ 0%, 100% {{ opacity: 0.18; transform: scale(0.99); }} 50% {{ opacity: 0.38; transform: scale(1.01); }} }}
    @keyframes nodeBreathe {{ 0%, 100% {{ filter: brightness(1); }} 50% {{ filter: brightness(1.035); }} }}

    @media (prefers-reduced-motion: reduce) {{
      *, *:before, *:after {{
        animation-duration: 1ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
      }}
      .flow-particles, .flow-ribbons {{ display: none; }}
      .flow-lane {{ opacity: 0.78; }}
    }}
    """
