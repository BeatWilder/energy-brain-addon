from __future__ import annotations

from energy_brain.ui.themes.tokens import css_vars


def render_theme_css() -> str:
    return f"""
.flow-map::after{{
content:'ENERGY_BRAIN_RUNTIME_MARKER_991';
position:absolute;
left:8px;
bottom:8px;
font-size:10px;
color:#ff0066;
z-index:99999;
pointer-events:none;
}}
    /* Tokens */
    :root {{
      color-scheme: dark;
      {{css_vars()}}
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
      --native-blur: blur(20px) saturate(1.08);
    }}

    * {{ box-sizing: border-box; }}
    html {{ background: var(--bg); }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background:
        radial-gradient(circle at 50% 24%, rgba(88, 232, 182, 0.028), transparent 42rem),
        radial-gradient(circle at 82% 18%, rgba(255, 209, 102, 0.008), transparent 30rem),
        radial-gradient(circle at 12% 76%, rgba(127, 199, 255, 0.014), transparent 30rem),
        linear-gradient(180deg, #071017 0%, #04070a 58%, #020304 100%);
      background-size: auto;
      font-family: var(--font-ui);
      letter-spacing: 0;
      overflow-x: hidden;
    }}
    body:has(.living-scene[data-energy-state="scarcity"]) {{
      background:
        radial-gradient(circle at 50% 28%, rgba(127, 199, 255, 0.052), transparent 31rem),
        radial-gradient(circle at 80% 20%, rgba(255, 139, 95, 0.034), transparent 24rem),
        linear-gradient(180deg, #05080d 0%, #030508 62%, #010203 100%);
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
      gap: var(--shell-gap, 16px);
    }}
    .topline {{
      position: sticky;
      top: 0;
      z-index: 20;
      min-height: 42px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 6px 8px;
      border: 0;
      border-radius: 0;
      background: linear-gradient(180deg, rgba(4, 7, 10, 0.54), rgba(4, 7, 10, 0.06));
      backdrop-filter: blur(22px);
      -webkit-backdrop-filter: blur(22px);
    }}
    .brand-block {{ min-width: 0; }}
    .brand {{ font-size: 18px; font-weight: 700; line-height: 1.05; }}
    .eyebrow {{
      color: rgba(152,165,178,0.58);
      font-size: 10px;
      font-weight: 620;
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
      gap: 8px;
      overflow-x: auto;
      padding: 0 6px;
      border: 0;
      border-radius: 0;
      background: transparent;
      scrollbar-width: none;
    }}
    .energy-state-island {{
      justify-content: center;
      opacity: 0.48;
    }}
    .health-strip-item {{
      position: relative;
      flex: 0 0 auto;
      min-width: 0;
      padding: 5px 10px 5px 23px;
      border: 1px solid rgba(255,255,255,0.006);
      border-radius: var(--radius-round);
      background: rgba(5, 8, 12, 0.045);
      backdrop-filter: var(--native-blur);
      -webkit-backdrop-filter: var(--native-blur);
    }}
    .health-strip-item i, .status-dot {{
      position: absolute;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--battery);
      box-shadow: 0 0 6px rgba(101,240,167,0.18);
      animation: dotPulse 8s ease-in-out infinite;
    }}
    .health-strip-item i {{ left: 12px; top: 50%; transform: translateY(-50%); }}
    .health-strip-item span, .strategy-metrics span, .health-pill span {{
      display: block;
      color: rgba(152,165,178,0.62);
      font-size: 10px;
      font-weight: 640;
      text-transform: uppercase;
      letter-spacing: 0.07em;
    }}
    .health-strip-item b {{
      display: block;
      margin-top: 3px;
      overflow: hidden;
      color: var(--text);
      font-size: 10px;
      font-weight: 680;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    /* Panels */
    .hero, .panel {{
      border: 1px solid rgba(255,255,255,0.004);
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, rgba(255,255,255,0.014), rgba(255,255,255,0.001)), rgba(8, 12, 17, 0.22);
      backdrop-filter: var(--native-blur);
      -webkit-backdrop-filter: var(--native-blur);
      box-shadow: 0 10px 30px rgba(0,0,0,0.13), inset 0 1px 0 rgba(255,255,255,0.008);
    }}
    .hero {{
      position: relative;
      min-height: var(--hero-min, 540px);
      padding: var(--hero-pad, 14px);
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(330px, 1fr) auto;
      background:
        radial-gradient(circle at 50% 50%, rgba(101,240,167,calc(0.020 + var(--scene-intensity) * 0.038)), transparent 34%),
        radial-gradient(circle at 50% 18%, rgba(255,209,102,0.010), transparent 31%),
        linear-gradient(180deg, rgba(255,255,255,0.012), rgba(255,255,255,0.001)),
        rgba(5,8,12,0.62);
      border-color: rgba(255,255,255,0.004);
      box-shadow: 0 18px 60px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.014);
    }}
    .hero[data-energy-state="scarcity"] {{
      background:
        radial-gradient(circle at 50% 50%, rgba(127,199,255,0.055), transparent 31%),
        radial-gradient(circle at 50% 18%, rgba(255,139,95,0.035), transparent 26%),
        linear-gradient(180deg, rgba(255,255,255,0.032), rgba(255,255,255,0.006)),
        rgba(4,7,11,0.72);
      box-shadow: 0 28px 96px rgba(0,0,0,0.46), inset 0 1px 0 rgba(255,255,255,0.04);
    }}
    .hero[data-price-state="cheap"] {{
      border-color: rgba(88,232,182,0.075);
    }}
    .hero[data-price-state="expensive"] {{
      border-color: rgba(255,139,95,0.080);
    }}
    .hero:before {{
      content: "";
      position: absolute;
      inset: 12% 9%;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(88,232,182,0.11), transparent 60%), radial-gradient(circle at 40% 35%, rgba(255,209,102,0.065), transparent 45%), radial-gradient(circle at 66% 64%, rgba(127,199,255,0.070), transparent 43%);
      filter: blur(26px);
      opacity: calc(0.10 + var(--scene-intensity) * 0.06);
      animation: liveGlow 30s ease-in-out infinite;
      pointer-events: none;
    }}
    .hero-head, .hero-foot {{
      position: relative;
      z-index: 2;
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
    }}
    .hero-head {{
      min-height: 50px;
      align-items: center;
    }}
    .hero-foot {{
      z-index: 4;
      align-items: center;
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 12px;
    }}
    .decision {{
      max-width: 500px;
      margin-top: var(--space-xs);
      font-size: var(--decision-size, 22px);
      line-height: 1.06;
      font-weight: 620;
    }}
    .soc {{ text-align: right; min-width: 84px; opacity: 0.84; }}
    .soc strong {{ display: block; color: var(--battery); font-size: var(--soc-size, 38px); line-height: 0.95; font-weight: 680; }}
    .quality-chip {{
      min-height: 23px;
      border-color: rgba(255,255,255,0.055);
      background: rgba(255,255,255,0.02);
      color: rgba(152,165,178,0.70);
    }}
    .quality-chip i {{
      width: 5px;
      height: 5px;
      margin-right: 6px;
      border-radius: 50%;
      background: currentColor;
      box-shadow: 0 0 10px currentColor;
    }}
    .quality-degraded {{ color: rgba(255,209,102,0.9); border-color: rgba(255,209,102,0.16); background: rgba(255,209,102,0.045); }}
    .panel {{ padding: var(--panel-pad, 14px); min-width: 0; }}
    .ambient-panel {{
      border-color: transparent;
      background: linear-gradient(180deg, rgba(255,255,255,0.010), rgba(255,255,255,0.001));
      box-shadow: none;
    }}
    .panel h2 {{ margin: 0; font-size: 18px; line-height: 1.16; font-weight: 620; }}
    .panel p {{ color: rgba(152,165,178,0.58); margin: 7px 0 0; line-height: 1.42; }}
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
      transform: translateZ(0);
    }}
    .flow-map:before {{
      content: "";
      position: absolute;
      inset: 8%;
      border-radius: 50%;
      background:
        radial-gradient(circle, transparent 47%, rgba(255,255,255,0.045) 48%, transparent 49%),
        conic-gradient(from 25deg, rgba(88,232,182,0.10), rgba(255,209,102,0.07), rgba(127,199,255,0.09), rgba(88,232,182,0.10));
      opacity: calc(0.055 + var(--scene-intensity) * 0.045);
      pointer-events: none;
    }}
    .hero[data-energy-state="scarcity"] .flow-map:before {{ opacity: 0.18; }}
    .hero[data-price-state="cheap"] .flow-map:before {{
      background:
        radial-gradient(circle, transparent 47%, rgba(255,255,255,0.040) 48%, transparent 49%),
        conic-gradient(from 25deg, rgba(88,232,182,0.14), rgba(127,199,255,0.10), rgba(88,232,182,0.14));
    }}
    .hero[data-price-state="expensive"] .flow-map:before {{
      background:
        radial-gradient(circle, transparent 47%, rgba(255,255,255,0.040) 48%, transparent 49%),
        conic-gradient(from 25deg, rgba(255,209,102,0.10), rgba(255,139,95,0.08), rgba(127,199,255,0.07), rgba(255,209,102,0.10));
    }}
    .flow-svg {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }}
    .flow-svg defs path {{ fill: none; }}
    .flow-backbone, .flow-ribbons, .flow-particles {{ pointer-events: none; }}
    .flow-lane {{
      fill: none;
      stroke: rgba(255,255,255,0.050);
      stroke-width: calc(var(--lane-width) * 1px);
      stroke-linecap: round;
      stroke-linejoin: round;
      opacity: calc(0.14 + var(--flow-intensity) * 0.20);
      filter: drop-shadow(0 0 calc(1px + var(--flow-intensity) * 3px) rgba(88,232,182,var(--energy-glow)));
      transition: stroke var(--motion-base), stroke-width var(--motion-base), opacity var(--motion-base), filter var(--motion-base);
    }}
    .flow-lane.tone-solar, .flow-pulse.tone-solar {{ stroke: url(#solar-flow); }}
    .flow-lane.tone-export, .flow-pulse.tone-export {{ stroke: url(#export-flow); }}
    .flow-lane.tone-home, .flow-pulse.tone-home {{ stroke: url(#solar-flow); }}
    .flow-lane.tone-battery, .flow-pulse.tone-battery {{ stroke: url(#grid-flow); }}
    .flow-lane.tone-grid.state-importing, .flow-pulse.tone-grid.state-importing {{ stroke: url(#import-flow); }}
    .flow-lane.tone-grid.state-exporting, .flow-pulse.tone-grid.state-exporting {{ stroke: url(#export-flow); }}
    .flow-lane.state-idle {{ stroke: rgba(255,255,255,0.052); filter: none; opacity: 0.22; }}
    .flow-pulse {{
      fill: none;
      stroke-width: calc((var(--lane-width) * 0.24) * 1px);
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-dasharray: calc(10px + var(--flow-intensity) * 8px) calc(50px - var(--flow-intensity) * 5px);
      animation: flowTravel var(--flow-speed) cubic-bezier(0.28, 0.70, 0.28, 1) infinite, flowPresence var(--flow-speed) ease-in-out infinite;
      opacity: calc(var(--flow-intensity) * 0.18);
      mix-blend-mode: screen;
    }}
    .flow-pulse.state-idle {{ opacity: 0; }}
    .flow-pulse.state-discharging, .flow-pulse.state-exporting {{ animation-timing-function: cubic-bezier(0.2, 0.72, 0.22, 1); }}
    .flow-dot {{
      opacity: 0;
      fill: #f9fff8;
      filter: drop-shadow(0 0 3px rgba(101,240,167,0.20)) drop-shadow(0 0 6px rgba(101,240,167,0.08));
    }}
    .flow-dot.tone-solar, .flow-dot.tone-home {{ fill: #fff0a6; filter: drop-shadow(0 0 3px rgba(255,209,102,0.24)) drop-shadow(0 0 6px rgba(88,232,182,0.07)); }}
    .flow-dot.tone-export {{ fill: #ffe58f; filter: drop-shadow(0 0 3px rgba(255,209,102,0.25)) drop-shadow(0 0 6px rgba(255,209,102,0.08)); }}
    .flow-dot.tone-battery {{ fill: #8fd7ff; }}
    .flow-dot.tone-grid.state-importing {{ fill: #ffad7a; filter: drop-shadow(0 0 3px rgba(255,139,95,0.24)) drop-shadow(0 0 6px rgba(255,139,95,0.07)); }}
    .flow-dot.tone-grid.state-exporting {{ fill: #ffe58f; filter: drop-shadow(0 0 3px rgba(255,209,102,0.25)) drop-shadow(0 0 6px rgba(255,209,102,0.08)); }}
    .junction-aura {{
      fill: url(#junction-glow);
      opacity: calc(0.070 + var(--scene-intensity) * 0.075);
      transform-origin: 210px 210px;
      animation: junctionBreath 10.5s ease-in-out infinite;
    }}
    .junction-core {{
      fill: rgba(249,255,250,0.78);
      filter: drop-shadow(0 0 6px rgba(101,240,167,0.16));
      transform-origin: 210px 210px;
      animation: corePulse 8.5s ease-in-out infinite;
    }}

    /* Nodes */
    .orb {{
      --soc: 0;
      position: absolute;
      inset: var(--orb-inset, 29%);
      border-radius: 50%;
      display: grid;
      place-items: center;
      background:
        radial-gradient(circle at 38% 26%, rgba(255,255,255,0.12), transparent 17%),
        radial-gradient(circle at 62% 74%, rgba(127,199,255,0.030), transparent 34%),
        radial-gradient(circle, rgba(13,18,24,0.99) 52%, rgba(88,232,182,0.052) 78%, rgba(127,199,255,0.020));
      box-shadow:
        0 18px 40px rgba(0,0,0,0.25),
        0 0 calc(12px + var(--scene-intensity) * 18px) rgba(88,232,182,0.070),
        inset 0 1px 0 rgba(255,255,255,0.085),
        inset 0 -20px 36px rgba(0,0,0,0.18);
      animation: orbPulse 24s ease-in-out infinite;
    }}
    .orb:before {{
      content: "";
      position: absolute;
      inset: -6px;
      border-radius: inherit;
      background:
        radial-gradient(ellipse at 38% 18%, rgba(255,255,255,0.12), transparent 19%),
        conic-gradient(from 12deg, transparent 0 60deg, rgba(101,240,167,0.036) 72deg, transparent 92deg 360deg);
      opacity: calc(0.060 + var(--scene-intensity) * 0.055);
      filter: blur(0.4px);
      animation: orbIdleDrift 48s linear infinite;
      pointer-events: none;
    }}
    .flow-map[data-orb-state="charging"] .orb,
    .flow-map[data-orb-state="cheap-charging"] .orb {{
      background:
        radial-gradient(circle at 38% 26%, rgba(255,255,255,0.14), transparent 17%),
        radial-gradient(circle at 62% 74%, rgba(127,199,255,0.036), transparent 33%),
        radial-gradient(circle, rgba(10,18,22,0.99) 52%, rgba(101,240,167,0.088) 78%, rgba(127,199,255,0.026));
      box-shadow:
        0 18px 40px rgba(0,0,0,0.25),
        0 0 calc(14px + var(--scene-intensity) * 24px) rgba(101,240,167,0.085),
        inset 0 1px 0 rgba(255,255,255,0.095),
        inset 0 -22px 40px rgba(0,0,0,0.17);
      animation-name: orbChargePulse;
    }}
    .flow-map[data-orb-state="charging"] .orb:before,
    .flow-map[data-orb-state="cheap-charging"] .orb:before {{
      background: radial-gradient(circle, transparent 57%, rgba(101,240,167,0.080) 61%, transparent 68%);
      animation: orbInward 16s ease-in-out infinite;
    }}
    .flow-map[data-orb-state="discharging"] .orb {{
      background:
        radial-gradient(circle at 38% 27%, rgba(255,255,255,0.17), transparent 18%),
        radial-gradient(circle at 64% 74%, rgba(127,199,255,0.085), transparent 31%),
        radial-gradient(circle, rgba(10,17,24,0.99) 50%, rgba(127,199,255,0.135) 75%, rgba(101,240,167,0.028));
      box-shadow:
        0 18px 42px rgba(0,0,0,0.26),
        0 0 calc(20px + var(--scene-intensity) * 30px) rgba(127,199,255,0.12),
        inset 0 1px 0 rgba(255,255,255,0.13),
        inset 0 -24px 44px rgba(0,0,0,0.18);
    }}
    .flow-map[data-orb-state="discharging"] .orb:before {{
      background: radial-gradient(circle, transparent 58%, rgba(127,199,255,0.12) 63%, transparent 70%);
      animation: orbOutward 8.2s ease-out infinite;
    }}
    .flow-map[data-orb-state="reserve-protected"] .orb {{
      background: radial-gradient(circle at 42% 32%, rgba(255,255,255,0.10), transparent 24%), radial-gradient(circle, rgba(13,15,18,0.98) 52%, rgba(255,139,95,0.22) 76%, rgba(101,240,167,0.06));
      box-shadow: 0 0 28px rgba(255,139,95,0.10), inset 0 0 28px rgba(255,139,95,0.045);
      animation-duration: 12s;
    }}
    .flow-map[data-orb-state="export-mode"] .orb {{
      background: radial-gradient(circle at 42% 32%, rgba(255,255,255,0.15), transparent 25%), radial-gradient(circle, rgba(18,16,10,0.99) 51%, rgba(255,209,102,0.25) 75%, rgba(255,241,168,0.080));
      box-shadow: 0 0 calc(40px + var(--scene-intensity) * 54px) rgba(255,209,102,0.20), inset 0 0 36px rgba(255,209,102,0.060);
    }}
    .flow-map[data-orb-state="export-mode"] .orb:before {{
      background: conic-gradient(from 12deg, transparent 0 34deg, rgba(255,209,102,0.22) 54deg, transparent 84deg 360deg);
      animation: orbExportHalo 12s linear infinite;
    }}
    .orb:after {{
      content: "";
      position: absolute;
      inset: -9px;
      border-radius: inherit;
      border: 1px solid rgba(255,255,255,0.060);
      box-shadow: 0 0 12px rgba(101,240,167,0.036);
      animation: orbitBreath 24s ease-in-out infinite;
    }}
    .orb-ring {{
      position: absolute;
      inset: 9px;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,0.055);
      background:
        radial-gradient(ellipse at 38% 24%, rgba(255,255,255,0.068), transparent 26%),
        radial-gradient(circle, rgba(255,255,255,0.022), transparent 63%);
    }}
    .orb-soc-ring {{
      position: absolute;
      inset: -2px;
      border-radius: inherit;
      background: conic-gradient(from -90deg, rgba(101,240,167,0.48) calc(var(--soc) * 1%), rgba(255,255,255,0.028) 0);
      mask: radial-gradient(circle, transparent 68%, #000 69% 70.5%, transparent 71.5%);
      animation: orbChargeBreath 22s ease-in-out infinite;
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
    .flow-map[data-orb-state="reserve-protected"] .reserve-band {{ opacity: 0.62; }}
    .orb-core {{ position: relative; z-index: 2; text-align: center; }}
    .orb-core span, .orb-core em {{ display: block; color: rgba(152,165,178,0.54); font-size: 10px; font-style: normal; font-weight: 520; }}
    .orb-core b {{ display: block; margin: 2px 0 4px; font-size: var(--orb-value-size, 34px); line-height: 1; font-weight: 680; }}
    .node {{
      --node-intensity: 0;
      position: absolute;
      width: var(--node-size, 82px);
      min-height: var(--node-size, 82px);
      padding: var(--node-pad, 12px 8px);
      border: 1px solid rgba(255,255,255,0.010);
      border-radius: 50%;
      display: grid;
      place-items: center;
      align-content: center;
      text-align: center;
      background: radial-gradient(circle at 35% 24%, rgba(255,255,255,0.08), transparent 28%), radial-gradient(circle at 50% 58%, rgba(8,12,17,0.80), rgba(8,12,17,0.42) 62%, rgba(255,255,255,0.016));
      box-shadow: 0 7px 15px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.018), 0 0 calc(1px + var(--node-intensity) * 4px) rgba(101,240,167,0.020);
      overflow: hidden;
      transition: opacity var(--motion-base), border-color var(--motion-base), transform var(--motion-base), box-shadow var(--motion-base);
      animation: nodeBreathe 22s ease-in-out infinite;
    }}
    .node-solar {{
      background:
        radial-gradient(circle at 50% 31%, rgba(255,209,102,0.205), transparent 34%),
        radial-gradient(circle at 50% 58%, rgba(42,29,8,0.82), rgba(8,12,17,0.46) 66%, rgba(255,209,102,0.036));
      box-shadow: 0 10px 22px rgba(0,0,0,0.14), inset 0 1px 0 rgba(255,255,255,0.036), 0 0 calc(4px + var(--node-intensity) * 10px) rgba(255,209,102,0.064);
    }}
    .node-home {{
      background:
        radial-gradient(circle at 45% 30%, rgba(255,255,245,0.130), transparent 32%),
        radial-gradient(circle at 50% 58%, rgba(20,22,22,0.86), rgba(8,12,17,0.48) 64%, rgba(255,255,245,0.030));
      box-shadow: 0 10px 22px rgba(0,0,0,0.14), inset 0 1px 0 rgba(255,255,255,0.036), 0 0 calc(3px + var(--node-intensity) * 8px) rgba(255,255,245,0.042);
    }}
    .node-battery {{
      background:
        radial-gradient(circle at 46% 30%, rgba(101,240,167,0.140), transparent 32%),
        radial-gradient(circle at 50% 58%, rgba(9,22,18,0.90), rgba(8,12,17,0.48) 64%, rgba(101,240,167,0.035));
      box-shadow: 0 10px 23px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.036), 0 0 calc(4px + var(--node-intensity) * 10px) rgba(101,240,167,0.060);
    }}
    .node-grid {{
      background:
        radial-gradient(circle at 50% 30%, rgba(127,199,255,0.135), transparent 32%),
        radial-gradient(circle at 50% 58%, rgba(8,17,25,0.90), rgba(8,12,17,0.48) 65%, rgba(127,199,255,0.038));
      box-shadow: 0 10px 23px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.040), 0 0 calc(9px + var(--node-intensity) * 11px) rgba(127,199,255,0.095);
    }}
    .node:before {{
      content: "";
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: conic-gradient(from 140deg, var(--node-ring), rgba(255,255,255,0.05), var(--node-ring));
      opacity: calc(0.040 + var(--node-intensity) * 0.075);
      mask: radial-gradient(circle, transparent 57%, #000 58% 69%, transparent 70%);
      animation: nodeHalo 16s ease-in-out infinite;
      pointer-events: none;
    }}
    .node i {{
      position: absolute;
      inset: 10px;
      border-radius: inherit;
      background: radial-gradient(circle at 50% 16%, var(--node-ring), transparent 50%);
      opacity: calc(0.060 + var(--node-intensity) * 0.075);
      pointer-events: none;
    }}
    .node i:before,
    .node i:after {{
      content: "";
      position: absolute;
      left: 50%;
      top: 38%;
      transform: translate(-50%, -50%);
      pointer-events: none;
    }}
    .node-solar i:before {{
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: rgba(255,209,102,0.92);
      box-shadow: 0 0 12px rgba(255,209,102,0.48);
    }}
    .node-solar i:after {{
      width: 32px;
      height: 32px;
      border-radius: 50%;
      border: 1px dashed rgba(255,209,102,0.42);
    }}
    .node-home i:before {{
      width: 25px;
      height: 17px;
      top: 42%;
      border: 1px solid rgba(255,255,245,0.72);
      border-top: 0;
      border-radius: 2px 2px 4px 4px;
    }}
    .node-home i:after {{
      width: 21px;
      height: 21px;
      top: 30%;
      border-left: 1px solid rgba(255,255,245,0.72);
      border-top: 1px solid rgba(255,255,245,0.72);
      transform: translate(-50%, -50%) rotate(45deg);
    }}
    .node-battery i:before {{
      width: 27px;
      height: 15px;
      border: 1px solid rgba(101,240,167,0.74);
      border-radius: 4px;
      box-shadow: inset 15px 0 0 rgba(101,240,167,0.42);
    }}
    .node-battery i:after {{
      width: 3px;
      height: 7px;
      left: calc(50% + 16px);
      border-radius: 0 2px 2px 0;
      background: rgba(101,240,167,0.74);
    }}
    .node-grid i:before {{
      width: 30px;
      height: 22px;
      background:
        linear-gradient(rgba(127,199,255,0.72), rgba(127,199,255,0.72)) 50% 0 / 1px 100% no-repeat,
        linear-gradient(rgba(127,199,255,0.72), rgba(127,199,255,0.72)) 0 50% / 100% 1px no-repeat,
        linear-gradient(90deg, transparent 0 18%, rgba(127,199,255,0.40) 18% 22%, transparent 22% 78%, rgba(127,199,255,0.40) 78% 82%, transparent 82%);
      border: 1px solid rgba(127,199,255,0.44);
      border-radius: 5px;
    }}
    .node span {{ position: relative; margin-top: 21px; color: rgba(152,165,178,0.72); font-size: var(--node-label-size, 9px); font-weight: 660; text-transform: uppercase; letter-spacing: 0.055em; }}
    .node b {{ position: relative; display: block; min-height: 1em; margin-top: 3px; font-size: var(--node-value-size, 13px); line-height: 1.04; font-weight: 760; }}
    .node.unknown {{
      opacity: 0.34;
      border-style: solid;
      filter: grayscale(0.42);
      box-shadow: 0 10px 28px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.045);
    }}
    .node.unknown:before, .node.unknown i {{ opacity: 0.08; }}
    .node.unknown b {{ display: none; }}
    .node-solar {{ top: 2%; left: 50%; transform: translateX(-50%); }}
    .node-home {{ right: 2%; top: 50%; transform: translateY(-50%); }}
    .node-battery {{
      bottom: 2%;
      left: 50%;
      top: auto;
      transform: translateX(-50%);
    }}

    .node-grid {{
      left: 2%;
      top: 50%;
      bottom: auto;
      transform: translateY(-50%);
    }}
    

    /* ===== FINAL POWERFLOW POSITIONS ===== */

    .flow-map .node-solar{{
      top:2% !important;
      left:50% !important;
      right:auto !important;
      bottom:auto !important;
      transform:translateX(-50%) !important;
    }}

    .flow-map .node-home{{
      right:2% !important;
      top:50% !important;
      left:auto !important;
      bottom:auto !important;
      transform:translateY(-50%) !important;
    }}

    .flow-map .node-grid{{
      left:50% !important;
      bottom:2% !important;
      top:auto !important;
      right:auto !important;
      transform:translateX(-50%) !important;
    }}

    .flow-map .node-battery{{
      left:2% !important;
      top:50% !important;
      bottom:auto !important;
      right:auto !important;
      transform:translateY(-50%) !important;
    }}

.node-grid.state-exporting b {{ color: var(--export); }}
    .node-grid.state-importing b {{ color: var(--import); }}
    .node-battery.state-discharging b {{ color: var(--grid); }}
    .node-battery.state-charging b {{ color: var(--battery); }}
    .node-solar span {{ color: rgba(255,209,102,0.74); }}
    .node-home span {{ color: rgba(255,255,245,0.66); }}
    .node-battery span {{ color: rgba(101,240,167,0.70); }}
    .node-grid span {{ color: rgba(127,199,255,0.70); }}

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
      border: 1px solid rgba(255,255,255,0.026);
      border-radius: var(--radius-round);
      background: rgba(4,8,12,0.070);
      box-shadow: 0 4px 10px rgba(0,0,0,0.05), inset 0 1px 0 rgba(255,255,255,0.012);
      backdrop-filter: blur(18px) saturate(1.1);
      -webkit-backdrop-filter: blur(18px) saturate(1.1);
      color: var(--text);
      font-size: 9px;
      font-weight: 620;
      padding: 5px 8px;
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
      box-shadow: 0 0 6px rgba(101,240,167,0.24);
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
      color: rgba(152,165,178,0.58);
      font-size: 9px;
      padding: 5px 8px;
    }}
    .telemetry-pill b {{
      color: rgba(245,248,251,0.86);
      margin-right: 5px;
      font-size: 9px;
    }}

    /* Timeline */
    .intelligence-strip {{
      border-color: rgba(255,255,255,0.006);
      background:
        radial-gradient(circle at 20% 0%, rgba(101,240,167,0.020), transparent 24rem),
        linear-gradient(180deg, rgba(255,255,255,0.010), rgba(255,255,255,0.001));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.010);
    }}
    .strategy-why {{ color: rgba(152,165,178,0.70); margin: 10px 0 0; font-size: 14px; line-height: 1.42; }}
    .strategy-metrics {{
      display: grid;
      grid-template-columns: var(--metric-columns, 1fr);
      gap: var(--space-sm);
      margin: 12px 0;
    }}
    .strategy-metrics div, .health-pill {{
      border: 1px solid rgba(255,255,255,0.036);
      border-radius: var(--radius-md);
      background: rgba(255,255,255,0.012);
      padding: 9px;
    }}
    .strategy-metrics b, .health-pill b {{ display: block; margin-top: 3px; font-size: 14px; }}
    .semantic-grid, .comfort-grid, .control-grid {{
      display: grid;
      grid-template-columns: var(--semantic-columns, repeat(3, minmax(0, 1fr)));
      gap: 8px;
      margin: 12px 0;
    }}
    .semantic-grid span, .comfort-row, .control-row {{
      min-width: 0;
      border: 1px solid rgba(255,255,255,0.030);
      border-radius: var(--radius-md);
      background: rgba(255,255,255,0.010);
      padding: 9px;
      color: rgba(152,165,178,0.68);
      font-size: 11px;
      line-height: 1.25;
    }}
    .semantic-grid b, .comfort-row span, .control-row span {{
      display: block;
      margin-bottom: 4px;
      color: rgba(152,165,178,0.58);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
    }}
    .comfort-row b, .control-row b {{
      display: block;
      overflow-wrap: anywhere;
      color: var(--text);
      font-size: 13px;
      line-height: 1.22;
      font-weight: 680;
    }}
    .comfort-panel {{
      background:
        radial-gradient(circle at 88% 8%, rgba(255,209,102,0.026), transparent 16rem),
        linear-gradient(180deg, rgba(255,255,255,0.010), rgba(255,255,255,0.001));
    }}
    .thermostat-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0 12px;
    }}
    .thermostat-preview {{
      min-width: 0;
      border: 1px solid rgba(255,255,255,0.018);
      border-radius: 20px;
      background:
        radial-gradient(circle at 50% 12%, rgba(255,214,136,0.050), transparent 44%),
        linear-gradient(180deg, rgba(255,255,255,0.026), rgba(255,255,255,0.006)),
        rgba(4,8,12,0.18);
      padding: 14px 12px 12px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.030), 0 18px 42px rgba(0,0,0,0.18);
      backdrop-filter: blur(18px) saturate(1.08);
      -webkit-backdrop-filter: blur(18px) saturate(1.08);
    }}
    .thermostat-top {{ display:grid; place-items:center; min-height:16px; }}
    .thermostat-top span {{
      display:block;
      color:rgba(245,248,251,0.68);
      font-size:10px;
      font-weight:680;
      text-transform:uppercase;
      letter-spacing:0.10em;
    }}
    .thermostat-dial {{
      width:132px;
      height:132px;
      margin:10px auto 8px;
      border-radius:50%;
      display:grid;
      place-items:center;
      background:
        radial-gradient(circle at 50% 50%, rgba(5,8,12,0.99) 62%, transparent 63%),
        conic-gradient(from -90deg, rgba(255,213,132,0.44) calc(var(--temp-ring) * 1%), rgba(255,255,255,0.030) 0);
      box-shadow:0 0 24px rgba(255,213,132,0.055), inset 0 0 24px rgba(255,255,255,0.014);
    }}
    .thermostat-dial div {{ text-align:center; }}
    .thermostat-dial strong {{ display:block; color:var(--text); font-size:34px; line-height:.96; font-weight:660; }}
    .thermostat-dial span, .thermostat-dial em {{ display:block; margin-top:6px; color:rgba(152,165,178,0.62); font-size:11px; font-style:normal; font-weight:560; }}
    .thermostat-dial em {{ margin-top:3px; color:rgba(255,213,132,0.52); font-size:10px; }}
    .thermostat-entity {{ color:rgba(152,165,178,0.36); font-size:9px; text-align:center; overflow-wrap:anywhere; }}
    .thermostat-controls {{ display:grid; grid-template-columns:repeat(2,44px); justify-content:center; gap:18px; margin-top:12px; }}
    .thermostat-controls span {{ display:grid; place-items:center; width:44px; height:34px; border:0; border-radius:999px; color:rgba(245,248,251,0.78); background:linear-gradient(180deg, rgba(255,255,255,0.054), rgba(255,255,255,0.016)); box-shadow:inset 0 1px 0 rgba(255,255,255,0.055), 0 0 22px rgba(255,213,132,0.040), 0 10px 24px rgba(0,0,0,0.16); font-size:18px; font-weight:640; }}
    .controls-panel {{
      background:
        radial-gradient(circle at 8% 0%, rgba(127,199,255,0.020), transparent 15rem),
        linear-gradient(180deg, rgba(255,255,255,0.010), rgba(255,255,255,0.001));
    }}
    .thermal-chip {{
      border: 1px solid rgba(255,209,102,0.12);
      border-radius: var(--radius-round);
      color: rgba(255,209,102,0.82);
      background: rgba(255,209,102,0.034);
      padding: 5px 9px;
      font-size: 10px;
      font-weight: 740;
      max-width: 160px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .horizon {{
      margin: 13px 0 8px;
      border: 1px solid rgba(255,255,255,0.014);
      border-radius: var(--radius-md);
      background: linear-gradient(180deg, rgba(255,255,255,0.010), rgba(255,255,255,0.001)), rgba(3,6,9,0.09);
      overflow: hidden;
    }}
    .horizon-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-sm);
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255,255,255,0.020);
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
      border-top: 1px solid rgba(255,139,95,0.16);
      border-bottom: 1px solid rgba(255,139,95,0.070);
      background: rgba(255,139,95,0.020);
      pointer-events: none;
    }}
    .horizon-grid:after {{
      content: "";
      position: absolute;
      left: 8px;
      top: 10px;
      bottom: 18px;
      width: 1px;
      background: linear-gradient(180deg, transparent, rgba(245,248,251,0.34), transparent);
      box-shadow: 0 0 8px rgba(127,199,255,0.10);
      pointer-events: none;
    }}
    .horizon-hour {{ position: relative; min-width: 0; border-radius: 5px; background: rgba(255,255,255,0.018); overflow: hidden; }}
    .horizon-hour.unknown {{ opacity: 0.32; }}
    .horizon-hour span {{ position: absolute; left: 50%; bottom: 3px; transform: translateX(-50%); color: var(--subtle); font-size: 9px; }}
    .horizon-hour i {{ position: absolute; left: 20%; right: 20%; bottom: 23px; height: calc(var(--soc) * 0.62px); border-radius: 999px 999px 3px 3px; background: linear-gradient(180deg, rgba(101,240,167,0.66), rgba(88,232,182,0.18)); box-shadow: 0 0 7px rgba(101,240,167,0.08); }}
    .horizon-hour b {{ position: absolute; left: 0; right: 0; top: calc(84px - var(--price) * 0.74px); height: 2px; background: rgba(255,209,102,0.50); box-shadow: 0 0 6px rgba(255,209,102,0.12); }}
    .horizon-hour.unknown i, .horizon-hour.unknown b {{ display: none; }}
    .horizon-hour.tone-charge {{ background: linear-gradient(180deg, rgba(101,240,167,0.105), rgba(255,255,255,0.012)); }}
    .horizon-hour.tone-discharge {{ background: linear-gradient(180deg, rgba(127,199,255,0.095), rgba(255,255,255,0.012)); }}
    .horizon-hour.tone-cheap {{ background: linear-gradient(180deg, rgba(88,232,182,0.085), rgba(255,255,255,0.012)); }}
    .horizon-hour.tone-expensive {{ background: linear-gradient(180deg, rgba(255,139,95,0.090), rgba(255,255,255,0.012)); }}
    .horizon-legend {{ display: flex; flex-wrap: wrap; gap: 7px; padding: 0 11px 10px; }}
    .horizon-legend span {{ border: 1px solid rgba(255,255,255,0.034); border-radius: var(--radius-round); color: rgba(152,165,178,0.74); background: rgba(255,255,255,0.014); padding: 5px 8px; font-size: 10px; font-weight: 720; }}
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
      border: 1px solid rgba(255,255,255,0.034);
      border-radius: var(--radius-md);
      padding: 9px;
      background: rgba(255,255,255,0.020);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.030);
    }}
    .timeline-block span {{ color: var(--muted); font-size: 11px; }}
    .timeline-block b {{ display: block; margin-top: 9px; font-size: 13px; line-height: 1.2; }}
    .tone-charge, .tone-cheap {{ background: linear-gradient(180deg, rgba(88,232,182,0.22), rgba(88,232,182,0.045)); border-color: rgba(88,232,182,0.28); }}
    .tone-discharge {{ background: linear-gradient(180deg, rgba(127,199,255,0.22), rgba(127,199,255,0.045)); border-color: rgba(127,199,255,0.28); }}
    .tone-expensive {{ background: linear-gradient(180deg, rgba(255,104,124,0.18), rgba(255,104,124,0.035)); border-color: rgba(255,104,124,0.26); }}
    .plan-list, .reason-stack {{ display: grid; gap: 8px; margin-top: var(--space-sm); }}
    .reason-item {{ border-top: 1px solid var(--line); padding-top: 8px; color: var(--muted); }}
    .reason-item summary {{ cursor: pointer; color: var(--text); font-size: 13px; }}
    .reason-stack p {{ margin: 0; padding: 10px 12px; border: 1px solid rgba(255,255,255,0.034); border-radius: var(--radius-md); background: rgba(255,255,255,0.012); color: var(--text); font-size: 13px; }}
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
      --shell-pad: max(10px, env(safe-area-inset-left));
      --shell-gap: 12px;
      --dashboard-columns: minmax(0, 1fr);
      --dashboard-gap: 8px;
      --switcher-width: 100%;
      --hero-min: min(614px, calc(100vh - 70px));
      --hero-pad: 18px;
      --flow-size: min(382px, calc(100vw - 38px));
      --flow-margin: 4px 0 8px;
      --node-size: 74px;
      --node-pad: 10px 7px;
      --node-label-size: 9px;
      --node-value-size: 12px;
      --orb-inset: 29%;
      --orb-value-size: 33px;
      --decision-size: 15px;
      --soc-size: 28px;
      --panel-pad: 12px;
      --metric-columns: 1fr;
      --semantic-columns: 1fr;
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
    body[data-viewport="mobile"] .health-strip-item:nth-child(n+3) {{ display: none; }}
    body[data-viewport="mobile"] .health-strip-item b {{ max-width: 112px; }}
    body[data-viewport="mobile"] .hero-foot {{ gap: 9px; }}
    body[data-viewport="mobile"] .side {{
      grid-template-columns: minmax(0, 1fr);
    }}
    body[data-viewport="mobile"] .battery-panel,
    body[data-viewport="mobile"] .health-panel {{
      display: none;
    }}
    body[data-viewport="mobile"] .strategy-panel {{
      margin-top: -2px;
      border-radius: 18px;
    }}
    body[data-viewport="mobile"] .strategy-metrics,
    body[data-viewport="mobile"] .semantic-grid,
    body[data-viewport="mobile"] .timeline,
    body[data-viewport="mobile"] .plan-list,
    body[data-viewport="mobile"] .metric-row {{
      display: none;
    }}
    body[data-viewport="mobile"] .horizon {{
      margin-bottom: 0;
      border-left-color: transparent;
      border-right-color: transparent;
    }}
    body[data-viewport="mobile"] .micro-telemetry {{
      opacity: 0.46;
    }}
    body[data-viewport="mobile"] .intent-orbit {{
      gap: 5px;
    }}

    body[data-viewport="tablet"] {{
      --shell-pad: 16px;
      --shell-gap: 16px;
      --dashboard-columns: minmax(0, 1fr) minmax(320px, 0.9fr);
      --dashboard-gap: 16px;
      --switcher-width: auto;
      --hero-min: 590px;
      --hero-pad: 22px;
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
      --semantic-columns: repeat(3, minmax(0, 1fr));
      --health-columns: repeat(2, minmax(0, 1fr));
      --battery-value-size: 44px;
    }}

    body[data-viewport="desktop"] {{
      --shell-pad: 28px;
      --shell-gap: 18px;
      --dashboard-columns: minmax(0, 1.38fr) minmax(390px, 0.82fr);
      --dashboard-gap: 26px;
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
      --semantic-columns: repeat(3, minmax(0, 1fr));
      --health-columns: repeat(2, minmax(0, 1fr));
      --battery-value-size: 52px;
    }}
    body[data-viewport="desktop"] .strategy-panel {{ position: sticky; top: 24px; }}
    body[data-viewport="desktop"] .node:hover {{
      transform: translateY(-50%) scale(1.014);
      border-color: rgba(255,255,255,0.075);
      box-shadow: 0 14px 34px rgba(0,0,0,0.18), 0 0 calc(7px + var(--node-intensity) * 14px) rgba(101,240,167,0.070);
    }}
    body[data-viewport="desktop"] .node-solar:hover,
    

    /* ===== HARD POWERFLOW OVERRIDE ===== */

    .flow-map .node-solar{{
      top:2% !important;
      left:50% !important;
      right:auto !important;
      bottom:auto !important;
      transform:translateX(-50%) !important;
    }}

    .flow-map .node-home{{
      right:2% !important;
      top:50% !important;
      left:auto !important;
      bottom:auto !important;
      transform:translateY(-50%) !important;
    }}

    .flow-map .node-battery{{
      bottom:2% !important;
      left:50% !important;
      top:auto !important;
      right:auto !important;
      transform:translateX(-50%) !important;
    }}

    .flow-map .node-grid{{
      left:50% !important;
      bottom:2% !important;
      top:auto !important;
      right:auto !important;
      transform:translateX(-50%) !important;
    }}


body[data-viewport="desktop"] .node-grid:hover {{ transform: translateX(-50%) scale(1.014); }}

    /* Animation */
    @keyframes flowTravel {{ from {{ stroke-dashoffset: 10; }} to {{ stroke-dashoffset: -112; }} }}
    @keyframes flowPresence {{ 0%, 100% {{ opacity: calc(var(--flow-intensity) * 0.035); }} 24%, 64% {{ opacity: calc(var(--flow-intensity) * 0.20); }} }}
    @keyframes orbPulse {{ 0%, 100% {{ transform: scale(1); filter: brightness(1); }} 50% {{ transform: scale(1.0008); filter: brightness(1.005); }} }}
    @keyframes orbChargePulse {{ 0%, 100% {{ transform: scale(1); filter: brightness(1.001); }} 48% {{ transform: scale(1.003); filter: brightness(1.012); }} }}
    @keyframes orbChargeBreath {{ 0%, 100% {{ opacity: 0.28; transform: scale(1); }} 50% {{ opacity: 0.40; transform: scale(1.001); }} }}
    @keyframes orbitBreath {{ 0%, 100% {{ opacity: 0.07; transform: scale(0.999); }} 50% {{ opacity: 0.12; transform: scale(1.001); }} }}
    @keyframes orbIdleDrift {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    @keyframes orbInward {{ 0% {{ opacity: 0; transform: scale(1.12); }} 36% {{ opacity: 0.34; }} 100% {{ opacity: 0; transform: scale(0.88); }} }}
    @keyframes orbOutward {{ 0% {{ opacity: 0.30; transform: scale(0.90); }} 100% {{ opacity: 0; transform: scale(1.18); }} }}
    @keyframes orbExportHalo {{ from {{ transform: rotate(0deg) scale(1.02); }} to {{ transform: rotate(360deg) scale(1.02); }} }}
    @keyframes liveGlow {{ 0%, 100% {{ opacity: 0.16; transform: scale(0.999); }} 50% {{ opacity: 0.26; transform: scale(1.003); }} }}
    @keyframes dotPulse {{ 0%, 100% {{ opacity: 0.22; transform: scale(0.995); }} 50% {{ opacity: 0.36; transform: scale(1.006); }} }}
    @keyframes junctionBreath {{ 0%, 100% {{ opacity: 0.06; transform: scale(0.998); }} 50% {{ opacity: 0.12; transform: scale(1.005); }} }}
    @keyframes corePulse {{ 0%, 100% {{ opacity: 0.22; transform: scale(0.995); }} 50% {{ opacity: 0.34; transform: scale(1.006); }} }}
    @keyframes nodeHalo {{ 0%, 100% {{ opacity: 0.035; transform: scale(1); }} 50% {{ opacity: 0.085; transform: scale(1.001); }} }}
    @keyframes nodeBreathe {{ 0%, 100% {{ filter: brightness(1); }} 50% {{ filter: brightness(1.003); }} }}

    @media (prefers-reduced-motion: reduce) {{
      *, *:before, *:after {{
        animation-duration: 1ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
      }}
      .flow-particles, .flow-ribbons {{ display: none; }}
      .flow-lane {{ opacity: 0.78; }}
    }}
    

/* ===== HARDE FINAL POWERFLOW OVERRIDE ===== */

.flow-map .node-solar{{
  top:2% !important;
  left:50% !important;
  right:auto !important;
  bottom:auto !important;
  transform:translateX(-50%) !important;
}}

.flow-map .node-home{{
  right:2% !important;
  top:50% !important;
  left:auto !important;
  bottom:auto !important;
  transform:translateY(-50%) !important;
}}

.flow-map .node-grid{{
  left:2% !important;
  top:50% !important;
  right:auto !important;
  bottom:auto !important;
  transform:translateY(-50%) !important;
}}

.flow-map .node-battery{{
  left:50% !important;
  bottom:2% !important;
  top:auto !important;
  right:auto !important;
  transform:translateX(-50%) !important;
}}

"""