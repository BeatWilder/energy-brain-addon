from __future__ import annotations

from energy_brain.ui.themes.tokens import css_vars


def render_theme_css() -> str:
    return f"""
    :root {{
      color-scheme: dark;
      {css_vars()}
      --bg: #05070a;
      --bg-soft: #0a0f14;
      --panel: rgba(15, 20, 27, 0.76);
      --panel-strong: rgba(20, 27, 36, 0.92);
      --line: rgba(255, 255, 255, 0.105);
      --line-strong: rgba(255, 255, 255, 0.18);
      --text: #f5f8fb;
      --muted: #93a0ad;
      --subtle: #65717f;
      --solar: #ffd166;
      --home: #58e8b6;
      --battery: #65f0a7;
      --grid: #7fc7ff;
      --import: #ff8b5f;
      --export: #ffd166;
      --violet: #c792ff;
      --danger: #ff687c;
      --hairline: rgba(255, 255, 255, 0.075);
    }}

    * {{ box-sizing: border-box; }}
    html {{ background: var(--bg); }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background:
        radial-gradient(circle at 48% 16%, rgba(88, 232, 182, 0.16), transparent 28rem),
        radial-gradient(circle at 82% 8%, rgba(127, 199, 255, 0.12), transparent 25rem),
        linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px),
        linear-gradient(180deg, rgba(255,255,255,0.014) 1px, transparent 1px),
        linear-gradient(180deg, #080c11 0%, #05070a 56%, #030406 100%);
      background-size: auto, auto, 72px 72px, 72px 72px, auto;
      font-family: var(--font-ui);
      letter-spacing: 0;
    }}
    a {{ color: inherit; }}

    .shell {{
      width: min(1480px, 100%);
      min-height: 100vh;
      margin: 0 auto;
      padding: var(--space-md);
      display: grid;
      grid-template-rows: auto 1fr;
      gap: 14px;
    }}
    .topline {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      min-height: 46px;
      padding: 6px 8px;
      position: sticky;
      top: 0;
      z-index: 20;
      border: 1px solid rgba(255, 255, 255, 0.055);
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, rgba(5, 7, 10, 0.86), rgba(5, 7, 10, 0.56));
      backdrop-filter: blur(18px);
    }}
    .brand-block {{ min-width: 0; }}
    .brand {{ font-size: 18px; font-weight: 760; line-height: 1.05; }}
    .eyebrow {{
      color: var(--muted);
      font-size: 10px;
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: 0.09em;
    }}
    .layout-switcher {{
      display: inline-flex;
      gap: 2px;
      padding: 3px;
      border: 1px solid var(--line);
      border-radius: var(--radius-round);
      background: rgba(255, 255, 255, 0.026);
    }}
    .layout-switcher a, .chip {{
      min-height: 30px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      text-decoration: none;
      border: 1px solid transparent;
      border-radius: var(--radius-round);
      padding: 5px 9px;
      font-size: 11px;
      font-weight: 680;
      transition: color var(--motion-base), background var(--motion-base), border-color var(--motion-base), box-shadow var(--motion-base), transform var(--motion-fast);
    }}
    .layout-switcher a:hover {{
      color: var(--text);
      background: rgba(255, 255, 255, 0.045);
    }}
    .layout-switcher a.active {{
      color: var(--text);
      border-color: rgba(88, 232, 182, 0.28);
      background: rgba(88, 232, 182, 0.085);
      box-shadow: 0 0 18px rgba(88, 232, 182, 0.11), inset 0 1px 0 rgba(255, 255, 255, 0.055);
    }}
    .health-strip {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.025));
      box-shadow: 0 16px 50px rgba(0, 0, 0, 0.2);
      padding: 8px;
      scrollbar-width: none;
    }}
    .health-strip-item {{
      position: relative;
      flex: 0 0 auto;
      min-width: 128px;
      padding: 9px 12px 9px 28px;
      border: 1px solid rgba(255, 255, 255, 0.075);
      border-radius: var(--radius-round);
      background: rgba(6, 10, 14, 0.72);
    }}
    .health-strip-item i {{
      position: absolute;
      left: 12px;
      top: 50%;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--battery);
      box-shadow: 0 0 16px rgba(101, 240, 167, 0.62);
      transform: translateY(-50%);
      animation: dotPulse 2.8s ease-in-out infinite;
    }}
    .health-strip-item span {{
      display: block;
      color: var(--muted);
      font-size: 10px;
      font-weight: 720;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .health-strip-item b {{
      display: block;
      margin-top: 3px;
      overflow: hidden;
      color: var(--text);
      font-size: 12px;
      font-weight: 720;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .dashboard {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
      align-items: stretch;
    }}
    .side {{ display: grid; gap: 14px; }}
    .hero, .panel {{
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.022)), var(--panel);
      backdrop-filter: blur(22px);
      box-shadow: 0 18px 58px rgba(0, 0, 0, 0.34);
    }}
    .hero {{
      min-height: 620px;
      padding: 28px;
      position: relative;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(330px, 1fr) auto;
      background:
        radial-gradient(circle at 50% 48%, rgba(101, 240, 167, 0.12), transparent 34%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.025)),
        rgba(8, 12, 17, 0.78);
      box-shadow: 0 34px 120px rgba(0, 0, 0, 0.52), inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }}
    .hero:before {{
      content: "";
      position: absolute;
      inset: 10% 7%;
      border-radius: 50%;
      background:
        radial-gradient(circle, rgba(88, 232, 182, 0.2), transparent 58%),
        radial-gradient(circle at 40% 35%, rgba(127, 199, 255, 0.14), transparent 46%);
      filter: blur(14px);
      animation: liveGlow 5s ease-in-out infinite;
      pointer-events: none;
    }}
    .hero-head, .hero-foot {{
      position: relative;
      z-index: 2;
      display: flex;
      justify-content: space-between;
      gap: var(--space-md);
      align-items: flex-start;
    }}
    .decision {{
      max-width: 760px;
      margin-top: var(--space-xs);
      font-size: clamp(30px, 7vw, 62px);
      line-height: 1;
      font-weight: 760;
    }}
    .soc {{ text-align: right; min-width: 92px; }}
    .soc strong {{ display: block; color: var(--battery); font-size: clamp(34px, 10vw, 64px); line-height: 0.95; }}

    .flow-map {{
      position: relative;
      z-index: 1;
      align-self: center;
      justify-self: center;
      width: min(560px, 100%);
      aspect-ratio: 1;
    }}
    .flow-svg {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }}
    .flow-lane {{
      --flow: 0;
      fill: none;
      stroke: rgba(255, 255, 255, 0.13);
      stroke-width: calc(4px + (var(--flow) * 5px));
      stroke-linecap: round;
      filter: drop-shadow(0 0 calc(var(--flow) * 18px) rgba(88, 232, 182, 0.22));
      transition: stroke-width var(--motion-base), opacity var(--motion-base);
    }}
    .flow-lane.active, .flow-lane.charging {{ stroke: rgba(101, 240, 167, calc(0.18 + var(--flow) * 0.26)); }}
    .flow-lane.discharging, .flow-lane.reverse {{ stroke: rgba(127, 199, 255, calc(0.18 + var(--flow) * 0.26)); }}
    .flow-lane.exporting {{ stroke: rgba(255, 209, 102, calc(0.2 + var(--flow) * 0.3)); }}
    .flow-lane.importing {{ stroke: rgba(255, 139, 95, calc(0.2 + var(--flow) * 0.3)); }}
    .flow-lane.discharging, .flow-lane.reverse {{ filter: drop-shadow(0 0 calc(var(--flow) * 18px) rgba(127, 199, 255, 0.24)); }}
    .flow-lane.exporting {{ filter: drop-shadow(0 0 calc(var(--flow) * 18px) rgba(255, 209, 102, 0.28)); }}
    .flow-lane.importing {{ filter: drop-shadow(0 0 calc(var(--flow) * 18px) rgba(255, 139, 95, 0.28)); }}
    .flow-pulse {{
      --flow: 0;
      fill: none;
      stroke-width: calc(2px + (var(--flow) * 2px));
      stroke-linecap: round;
      stroke-dasharray: 2 18;
      animation: flowShimmer calc(3800ms - (var(--flow) * 1600ms)) linear infinite;
      opacity: 0;
    }}
    .flow-pulse.active, .flow-pulse.charging {{
      opacity: 1;
      stroke: url(#solar-flow);
    }}
    .flow-pulse.discharging, .flow-pulse.reverse {{
      opacity: 1;
      stroke: url(#grid-flow);
      animation-direction: reverse;
    }}
    .flow-pulse.importing {{
      opacity: 1;
      stroke: url(#import-flow);
    }}
    .flow-pulse.exporting {{
      opacity: 1;
      stroke: url(#export-flow);
      animation-direction: reverse;
    }}
    .orb {{
      --soc: 0;
      position: absolute;
      inset: 28%;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background:
        conic-gradient(var(--battery) calc(var(--soc) * 1%), rgba(255, 255, 255, 0.08) 0),
        radial-gradient(circle, rgba(12, 18, 24, 0.96) 58%, rgba(88, 232, 182, 0.26));
      box-shadow: 0 0 90px rgba(88, 232, 182, 0.24), inset 0 0 34px rgba(255, 255, 255, 0.05);
      animation: orbPulse 4.2s ease-in-out infinite;
    }}
    .orb:after {{
      content: "";
      position: absolute;
      inset: -10px;
      border-radius: inherit;
      border: 1px solid rgba(101, 240, 167, 0.18);
      box-shadow: 0 0 42px rgba(101, 240, 167, 0.14);
      animation: orbitBreath 6.4s ease-in-out infinite;
    }}
    .orb-ring {{
      position: absolute;
      inset: 9px;
      border-radius: 50%;
      border: 1px solid rgba(255, 255, 255, 0.12);
      background: radial-gradient(circle, rgba(255, 255, 255, 0.06), transparent 62%);
    }}
    .reserve-band {{
      position: absolute;
      inset: 15px;
      border-radius: 50%;
      background: conic-gradient(from 198deg, rgba(255, 139, 95, 0.48) 0 38deg, transparent 38deg 360deg);
      mask: radial-gradient(circle, transparent 61%, #000 62% 69%, transparent 70%);
      opacity: 0.72;
      pointer-events: none;
    }}
    .orb-core {{ position: relative; text-align: center; }}
    .orb-core span, .orb-core em {{ display: block; color: var(--muted); font-size: 11px; font-style: normal; }}
    .orb-core b {{ display: block; margin: 2px 0 4px; font-size: clamp(32px, 8vw, 54px); line-height: 1; }}
    .node {{
      position: absolute;
      width: 118px;
      min-height: 62px;
      padding: 10px 11px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: rgba(6, 9, 13, 0.84);
      box-shadow: 0 0 34px rgba(0, 0, 0, 0.22);
      transition: opacity var(--motion-base), border-color var(--motion-base), transform var(--motion-base), background var(--motion-base);
    }}
    .node span {{ color: var(--muted); font-size: 12px; }}
    .node b {{ display: block; margin-top: 2px; font-size: 20px; line-height: 1.1; }}
    .node.unknown {{
      opacity: 0.58;
      border-style: dashed;
      filter: grayscale(0.2);
    }}
    .node.unknown b {{ color: var(--muted); }}
    .node-solar {{ top: 2%; left: 50%; transform: translateX(-50%); border-color: rgba(255, 209, 102, 0.28); }}
    .node-home {{ right: 0; top: 50%; transform: translateY(-50%); border-color: rgba(88, 232, 182, 0.26); }}
    .node-battery {{ left: 0; top: 50%; transform: translateY(-50%); border-color: rgba(101, 240, 167, 0.24); }}
    .node-grid {{ bottom: 2%; left: 50%; transform: translateX(-50%); border-color: rgba(127, 199, 255, 0.24); }}
    .node-grid.exporting b {{ color: var(--export); }}
    .node-grid.importing b {{ color: var(--import); }}
    .node-battery.discharging b {{ color: var(--grid); }}
    .node-battery.charging b {{ color: var(--battery); }}
    .particle {{
      position: absolute;
      z-index: 3;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.82);
      box-shadow: 0 0 18px rgba(101, 240, 167, 0.72);
      opacity: 0.38;
      pointer-events: none;
      animation: particleDrift 5.8s ease-in-out infinite;
    }}
    .particle-a {{ left: 50%; top: 20%; animation-delay: -0.8s; }}
    .particle-b {{ right: 22%; top: 50%; animation-delay: -2.1s; box-shadow: 0 0 18px rgba(255, 209, 102, 0.74); }}
    .particle-c {{ left: 23%; top: 52%; animation-delay: -3.4s; box-shadow: 0 0 18px rgba(127, 199, 255, 0.74); }}
    .particle-d {{ left: 50%; bottom: 21%; animation-delay: -4.7s; box-shadow: 0 0 18px rgba(255, 139, 95, 0.74); }}
    .quality-chip {{
      min-height: 30px;
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: var(--radius-round);
      color: var(--muted);
      background: rgba(255, 255, 255, 0.035);
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 680;
    }}
    .quality-live {{
      color: var(--battery);
      border-color: rgba(101, 240, 167, 0.25);
      background: rgba(101, 240, 167, 0.08);
    }}

    .panel {{ padding: 18px; }}
    .panel h2 {{ margin: 0; font-size: 20px; line-height: 1.14; }}
    .panel p {{ color: var(--muted); margin: 7px 0 0; line-height: 1.42; }}
    .panel-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
    .status-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--battery);
      box-shadow: 0 0 18px rgba(101, 240, 167, 0.62);
      animation: dotPulse 2.6s ease-in-out infinite;
    }}
    .strategy-why {{
      color: var(--muted);
      margin: 10px 0 0;
      font-size: 14px;
      line-height: 1.42;
    }}
    .strategy-metrics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--space-sm);
      margin: 13px 0;
    }}
    .strategy-metrics div, .health-pill {{
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: rgba(255, 255, 255, 0.035);
      padding: 9px;
    }}
    .strategy-metrics span, .health-pill span {{ display: block; color: var(--muted); font-size: 11px; }}
    .strategy-metrics b, .health-pill b {{ display: block; margin-top: 3px; font-size: 14px; }}
    .timeline {{
      min-height: 86px;
      display: flex;
      align-items: stretch;
      gap: 6px;
      overflow-x: auto;
      padding: 8px 2px 12px;
      scrollbar-width: thin;
    }}
    .horizon {{
      margin: 13px 0 8px;
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.02)),
        rgba(3, 6, 9, 0.46);
      overflow: hidden;
    }}
    .horizon-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: var(--space-sm);
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
    }}
    .horizon-head span {{ color: var(--text); font-size: 13px; font-weight: 760; }}
    .horizon-head b {{ color: var(--muted); font-size: 11px; font-weight: 680; }}
    .horizon-grid {{
      position: relative;
      display: grid;
      grid-template-columns: repeat(24, minmax(14px, 1fr));
      min-height: 112px;
      padding: 10px 9px 18px;
      gap: 3px;
    }}
    .horizon-grid:before {{
      content: "";
      position: absolute;
      left: 10px;
      right: 10px;
      bottom: 32px;
      height: 18px;
      border-top: 1px solid rgba(255, 139, 95, 0.34);
      border-bottom: 1px solid rgba(255, 139, 95, 0.16);
      background: rgba(255, 139, 95, 0.05);
      pointer-events: none;
    }}
    .horizon-hour {{
      position: relative;
      min-width: 0;
      border-radius: 5px;
      background: rgba(255, 255, 255, 0.035);
      overflow: hidden;
    }}
    .horizon-hour.unknown {{
      opacity: 0.32;
    }}
    .horizon-hour span {{
      position: absolute;
      left: 50%;
      bottom: 3px;
      transform: translateX(-50%);
      color: var(--subtle);
      font-size: 9px;
    }}
    .horizon-hour i {{
      position: absolute;
      left: 20%;
      right: 20%;
      bottom: 23px;
      height: calc(var(--soc) * 0.62px);
      border-radius: 999px 999px 3px 3px;
      background: linear-gradient(180deg, rgba(101, 240, 167, 0.92), rgba(88, 232, 182, 0.3));
      box-shadow: 0 0 16px rgba(101, 240, 167, 0.18);
    }}
    .horizon-hour b {{
      position: absolute;
      left: 0;
      right: 0;
      top: calc(84px - var(--price) * 0.74px);
      height: 2px;
      background: rgba(255, 209, 102, 0.82);
      box-shadow: 0 0 12px rgba(255, 209, 102, 0.28);
    }}
    .horizon-hour.unknown i,
    .horizon-hour.unknown b {{
      display: none;
    }}
    .horizon-hour.tone-charge {{ background: linear-gradient(180deg, rgba(101, 240, 167, 0.2), rgba(255, 255, 255, 0.025)); }}
    .horizon-hour.tone-discharge {{ background: linear-gradient(180deg, rgba(127, 199, 255, 0.18), rgba(255, 255, 255, 0.025)); }}
    .horizon-hour.tone-cheap {{ background: linear-gradient(180deg, rgba(88, 232, 182, 0.16), rgba(255, 255, 255, 0.025)); }}
    .horizon-hour.tone-expensive {{ background: linear-gradient(180deg, rgba(255, 139, 95, 0.18), rgba(255, 255, 255, 0.025)); }}
    .horizon-legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      padding: 0 11px 10px;
    }}
    .horizon-legend span {{
      border: 1px solid var(--line);
      border-radius: var(--radius-round);
      color: var(--muted);
      background: rgba(255, 255, 255, 0.035);
      padding: 5px 8px;
      font-size: 10px;
      font-weight: 720;
    }}
    .timeline-block {{
      flex: 0 0 calc(var(--span) * 1%);
      min-width: 92px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      padding: 9px;
      background: rgba(255, 255, 255, 0.04);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }}
    .timeline-block span {{ color: var(--muted); font-size: 11px; }}
    .timeline-block b {{ display: block; margin-top: 9px; font-size: 13px; line-height: 1.2; }}
    .tone-charge, .tone-cheap {{ background: linear-gradient(180deg, rgba(88, 232, 182, 0.22), rgba(88, 232, 182, 0.045)); border-color: rgba(88, 232, 182, 0.28); }}
    .tone-discharge {{ background: linear-gradient(180deg, rgba(127, 199, 255, 0.22), rgba(127, 199, 255, 0.045)); border-color: rgba(127, 199, 255, 0.28); }}
    .tone-expensive {{ background: linear-gradient(180deg, rgba(255, 104, 124, 0.18), rgba(255, 104, 124, 0.035)); border-color: rgba(255, 104, 124, 0.26); }}
    .plan-list {{ display: grid; gap: 8px; margin-top: var(--space-sm); }}
    .reason-item {{
      border-top: 1px solid var(--line);
      padding-top: 8px;
      color: var(--muted);
    }}
    .reason-item summary {{ cursor: pointer; color: var(--text); font-size: 13px; }}
    .reason-stack {{ display: grid; gap: 8px; }}
    .reason-stack p {{
      margin: 0;
      padding: 10px 12px;
      border: 1px solid var(--hairline);
      border-radius: var(--radius-md);
      background: rgba(255, 255, 255, 0.025);
      color: var(--text);
      font-size: 13px;
    }}
    .compact-reasons p {{
      position: relative;
      padding-left: 28px;
    }}
    .compact-reasons p:before {{
      content: "";
      position: absolute;
      left: 12px;
      top: 17px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--battery);
      box-shadow: 0 0 12px rgba(101, 240, 167, 0.5);
    }}
    .health-row {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-sm); }}
    .battery-panel {{
      overflow: hidden;
    }}
    .battery-mode {{
      border: 1px solid var(--line);
      border-radius: var(--radius-round);
      color: var(--muted);
      background: rgba(255, 255, 255, 0.035);
      padding: 5px 9px;
      font-size: 11px;
      font-weight: 760;
    }}
    .battery-mode.charging {{ color: var(--battery); border-color: rgba(101, 240, 167, 0.28); background: rgba(101, 240, 167, 0.08); }}
    .battery-mode.discharging {{ color: var(--grid); border-color: rgba(127, 199, 255, 0.28); background: rgba(127, 199, 255, 0.08); }}
    .battery-visual {{
      --soc: 0;
      display: grid;
      grid-template-columns: 88px minmax(0, 1fr);
      gap: var(--space-md);
      align-items: center;
      margin-top: var(--space-sm);
    }}
    .battery-shell {{
      position: relative;
      height: 118px;
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.018));
      box-shadow: inset 0 0 24px rgba(255, 255, 255, 0.035), 0 0 34px rgba(101, 240, 167, 0.1);
      overflow: hidden;
    }}
    .battery-shell:before {{
      content: "";
      position: absolute;
      left: 30%;
      right: 30%;
      top: -7px;
      height: 7px;
      border-radius: 7px 7px 0 0;
      background: rgba(255, 255, 255, 0.18);
    }}
    .battery-shell span {{
      position: absolute;
      left: 8px;
      right: 8px;
      bottom: 8px;
      height: calc(var(--soc) * 1%);
      border-radius: 12px;
      background: linear-gradient(180deg, #7fc7ff, #65f0a7);
      box-shadow: 0 0 28px rgba(101, 240, 167, 0.32);
      transition: height var(--motion-base);
    }}
    .battery-visual strong {{
      display: block;
      font-size: clamp(36px, 8vw, 54px);
      line-height: 0.95;
    }}
    .battery-visual p {{
      margin-top: 7px;
    }}
    .battery-meta {{
      display: flex;
      justify-content: space-between;
      gap: var(--space-sm);
      margin-top: var(--space-md);
      color: var(--muted);
      font-size: 12px;
    }}
    .metric-row {{
      display: flex;
      justify-content: space-between;
      gap: var(--space-md);
      border-top: 1px solid var(--line);
      padding-top: var(--space-sm);
      margin-top: var(--space-md);
    }}
    .metric-row span {{ color: var(--muted); }}
    .metric-row b {{ text-align: right; }}
    .error-page {{ min-height: 100vh; display: grid; place-items: center; padding: var(--space-lg); }}
    .error-page .panel {{ max-width: 520px; }}

    body.layout-mobile .shell {{ padding: 8px; gap: 8px; }}
    body.layout-mobile .topline {{ align-items: flex-start; flex-direction: column; }}
    body.layout-mobile .layout-switcher {{ width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    body.layout-mobile .health-strip {{ margin-inline: -2px; }}
    body.layout-mobile .hero {{ min-height: 448px; padding: 14px; grid-template-rows: auto 1fr auto; }}
    body.layout-mobile .flow-map {{ width: min(390px, 100%); }}
    body.layout-mobile .node {{ width: 98px; min-height: 56px; padding: 8px 9px; }}
    body.layout-mobile .node b {{ font-size: 17px; }}
    body.layout-mobile .strategy-metrics {{ grid-template-columns: 1fr; }}
    body.layout-mobile .health-row {{ grid-template-columns: 1fr; }}
    body.layout-mobile .panel {{ padding: 14px; }}
    body.layout-mobile .decision {{ font-size: clamp(25px, 8vw, 36px); }}
    body.layout-mobile .timeline {{ min-height: 92px; }}
    body.layout-mobile .horizon-grid {{ min-height: 104px; grid-template-columns: repeat(24, minmax(10px, 1fr)); padding: 9px 8px 17px; gap: 2px; }}
    body.layout-mobile .battery-visual {{ grid-template-columns: 72px minmax(0, 1fr); }}
    body.layout-mobile .battery-shell {{ height: 96px; }}

    body.layout-tablet .shell {{ width: min(980px, 100%); }}
    body.layout-tablet .dashboard {{ grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr); }}
    body.layout-tablet .side {{ grid-template-columns: 1fr; }}
    body.layout-tablet .planner {{ grid-column: auto; }}

    body.layout-desktop .shell {{ padding: 28px; }}
    body.layout-desktop .dashboard {{ grid-template-columns: minmax(0, 1.35fr) minmax(390px, 0.85fr); gap: var(--space-lg); }}
    body.layout-desktop .side {{ grid-template-rows: auto minmax(0, 1fr) auto; }}
    body.layout-desktop .hero {{ min-height: calc(100vh - 116px); }}
    body.layout-desktop .strategy-panel {{ position: sticky; top: 24px; }}

    @media (max-width: 767px) {{
      .shell {{ padding: 8px; gap: 8px; }}
      .topline {{ align-items: flex-start; flex-direction: column; }}
      .layout-switcher {{ width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); }}
      .health-strip {{ margin-inline: -2px; }}
      .dashboard {{ grid-template-columns: 1fr; }}
      .hero {{ min-height: 448px; padding: 14px; }}
      .flow-map {{ width: min(390px, 100%); }}
      .decision {{ font-size: clamp(25px, 8vw, 36px); }}
      .soc strong {{ font-size: 36px; }}
      .strategy-metrics, .health-row {{ grid-template-columns: 1fr; }}
      .panel {{ padding: 14px; }}
      .timeline {{ min-height: 92px; }}
      .horizon-grid {{ min-height: 104px; grid-template-columns: repeat(24, minmax(10px, 1fr)); padding: 9px 8px 17px; gap: 2px; }}
    }}
    @media (min-width: 768px) and (max-width: 1199px) {{
      .shell {{ width: min(980px, 100%); }}
      .dashboard {{ grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr); }}
      .side {{ grid-template-columns: 1fr; }}
      .planner {{ grid-column: auto; }}
    }}
    @media (min-width: 1200px) {{
      .shell {{ padding: 28px; }}
      .dashboard {{ grid-template-columns: minmax(0, 1.35fr) minmax(390px, 0.85fr); gap: var(--space-lg); }}
      .hero {{ min-height: calc(100vh - 116px); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *:before, *:after {{ animation-duration: 1ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; }}
    }}
    @keyframes flowShimmer {{
      from {{ stroke-dashoffset: 0; }}
      to {{ stroke-dashoffset: -80; }}
    }}
    @keyframes orbPulse {{
      0%, 100% {{ transform: scale(1); filter: brightness(1); }}
      50% {{ transform: scale(1.018); filter: brightness(1.08); }}
    }}
    @keyframes orbitBreath {{
      0%, 100% {{ opacity: 0.42; transform: scale(0.985); }}
      50% {{ opacity: 0.82; transform: scale(1.018); }}
    }}
    @keyframes liveGlow {{
      0%, 100% {{ opacity: 0.7; transform: scale(0.98); }}
      50% {{ opacity: 1; transform: scale(1.03); }}
    }}
    @keyframes dotPulse {{
      0%, 100% {{ opacity: 0.72; transform: scale(0.92); }}
      50% {{ opacity: 1; transform: scale(1.12); }}
    }}
    @keyframes particleDrift {{
      0%, 100% {{ transform: translate3d(0, 0, 0) scale(0.86); opacity: 0.18; }}
      35% {{ transform: translate3d(10px, -12px, 0) scale(1); opacity: 0.48; }}
      70% {{ transform: translate3d(-8px, 8px, 0) scale(0.92); opacity: 0.3; }}
    }}
    """
