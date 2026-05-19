from __future__ import annotations

from energy_brain.ui.themes.tokens import css_vars


def render_theme_css() -> str:
    return f"""
    :root {{
      color-scheme: dark;
      {css_vars()}
      --bg: #05070a;
      --bg-soft: #0a0f14;
      --panel: rgba(15, 20, 27, 0.74);
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
      --violet: #c792ff;
      --danger: #ff687c;
    }}

    * {{ box-sizing: border-box; }}
    html {{ background: var(--bg); }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background:
        radial-gradient(circle at 50% 18%, rgba(88, 232, 182, 0.13), transparent 26rem),
        radial-gradient(circle at 82% 8%, rgba(127, 199, 255, 0.11), transparent 24rem),
        linear-gradient(180deg, #080c11 0%, #05070a 56%, #030406 100%);
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
      gap: var(--space-md);
    }}
    .topline {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: var(--space-md);
      padding: 2px 2px 0;
    }}
    .brand {{ font-size: 20px; font-weight: 700; line-height: 1.1; }}
    .eyebrow {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 650;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }}
    .layout-switcher {{
      display: inline-flex;
      gap: var(--space-xs);
      padding: 4px;
      border: 1px solid var(--line);
      border-radius: var(--radius-round);
      background: rgba(255, 255, 255, 0.035);
    }}
    .layout-switcher a, .chip {{
      min-height: 38px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      text-decoration: none;
      border: 1px solid transparent;
      border-radius: var(--radius-round);
      padding: 8px 12px;
      font-size: 12px;
      font-weight: 680;
      transition: color var(--motion-base), background var(--motion-base), border-color var(--motion-base);
    }}
    .layout-switcher a.active {{
      color: var(--text);
      border-color: rgba(88, 232, 182, 0.35);
      background: rgba(88, 232, 182, 0.1);
      box-shadow: 0 0 24px rgba(88, 232, 182, 0.12);
    }}
    .health-strip {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 1px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background: rgba(255, 255, 255, 0.055);
      box-shadow: 0 16px 50px rgba(0, 0, 0, 0.2);
    }}
    .health-strip-item {{
      min-width: 0;
      padding: 10px 12px;
      background: rgba(6, 10, 14, 0.72);
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
      gap: var(--space-md);
      align-items: stretch;
    }}
    .side {{ display: grid; gap: var(--space-md); }}
    .hero, .panel {{
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.022)), var(--panel);
      backdrop-filter: blur(22px);
      box-shadow: var(--shadow-panel);
    }}
    .hero {{
      min-height: 590px;
      padding: var(--space-lg);
      position: relative;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(330px, 1fr) auto;
      box-shadow: var(--shadow-hero);
    }}
    .hero:before {{
      content: "";
      position: absolute;
      inset: 14% 10%;
      border-radius: 50%;
      background:
        radial-gradient(circle, rgba(88, 232, 182, 0.2), transparent 58%),
        radial-gradient(circle at 40% 35%, rgba(127, 199, 255, 0.14), transparent 46%);
      filter: blur(12px);
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
      font-size: clamp(28px, 8vw, 58px);
      line-height: 0.98;
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
    .flow-lane.active, .flow-lane.charging, .flow-lane.importing {{ stroke: rgba(88, 232, 182, 0.28); }}
    .flow-lane.exporting, .flow-lane.discharging, .flow-lane.reverse {{ stroke: rgba(127, 199, 255, 0.28); }}
    .flow-pulse {{
      --flow: 0;
      fill: none;
      stroke-width: calc(2px + (var(--flow) * 2px));
      stroke-linecap: round;
      stroke-dasharray: 2 18;
      animation: flowShimmer var(--motion-flow) linear infinite;
      opacity: 0;
    }}
    .flow-pulse.active, .flow-pulse.charging, .flow-pulse.importing {{
      opacity: 1;
      stroke: url(#solar-flow);
    }}
    .flow-pulse.exporting, .flow-pulse.discharging, .flow-pulse.reverse {{
      opacity: 1;
      stroke: url(#grid-flow);
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
    .orb-ring {{
      position: absolute;
      inset: 9px;
      border-radius: 50%;
      border: 1px solid rgba(255, 255, 255, 0.12);
      background: radial-gradient(circle, rgba(255, 255, 255, 0.06), transparent 62%);
    }}
    .orb-core {{ position: relative; text-align: center; }}
    .orb-core span, .orb-core em {{ display: block; color: var(--muted); font-size: 11px; font-style: normal; }}
    .orb-core b {{ display: block; margin: 2px 0 4px; font-size: clamp(32px, 8vw, 54px); line-height: 1; }}
    .node {{
      position: absolute;
      min-width: 108px;
      padding: 11px 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: rgba(6, 9, 13, 0.84);
      box-shadow: 0 0 34px rgba(0, 0, 0, 0.22);
    }}
    .node span {{ color: var(--muted); font-size: 12px; }}
    .node b {{ display: block; margin-top: 2px; font-size: 20px; line-height: 1.1; }}
    .node-solar {{ top: 2%; left: 50%; transform: translateX(-50%); border-color: rgba(255, 209, 102, 0.28); }}
    .node-home {{ right: 0; top: 50%; transform: translateY(-50%); border-color: rgba(88, 232, 182, 0.26); }}
    .node-battery {{ left: 0; top: 50%; transform: translateY(-50%); border-color: rgba(101, 240, 167, 0.24); }}
    .node-grid {{ bottom: 2%; left: 50%; transform: translateX(-50%); border-color: rgba(127, 199, 255, 0.24); }}
    .node-grid.exporting b, .node-battery.discharging b {{ color: var(--grid); }}
    .node-grid.importing b, .node-battery.charging b {{ color: var(--battery); }}
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

    .panel {{ padding: var(--space-lg); }}
    .panel h2 {{ margin: 0; font-size: 22px; line-height: 1.12; }}
    .panel p {{ color: var(--muted); margin: 8px 0 0; line-height: 1.45; }}
    .panel-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-sm); }}
    .status-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--battery);
      box-shadow: 0 0 18px rgba(101, 240, 167, 0.62);
      animation: dotPulse 2.6s ease-in-out infinite;
    }}
    .strategy-metrics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: var(--space-sm);
      margin: var(--space-md) 0;
    }}
    .strategy-metrics div, .health-pill {{
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: rgba(255, 255, 255, 0.035);
      padding: 10px;
    }}
    .strategy-metrics span, .health-pill span {{ display: block; color: var(--muted); font-size: 11px; }}
    .strategy-metrics b, .health-pill b {{ display: block; margin-top: 3px; font-size: 14px; }}
    .timeline {{
      min-height: 112px;
      display: flex;
      align-items: stretch;
      gap: 6px;
      overflow-x: auto;
      padding: 8px 2px 12px;
      scrollbar-width: thin;
    }}
    .timeline-block {{
      flex: 0 0 calc(var(--span) * 1%);
      min-width: 98px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      padding: 10px;
      background: rgba(255, 255, 255, 0.04);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }}
    .timeline-block span {{ color: var(--muted); font-size: 11px; }}
    .timeline-block b {{ display: block; margin-top: 12px; font-size: 13px; line-height: 1.2; }}
    .tone-charge, .tone-cheap {{ background: linear-gradient(180deg, rgba(88, 232, 182, 0.22), rgba(88, 232, 182, 0.045)); border-color: rgba(88, 232, 182, 0.28); }}
    .tone-discharge {{ background: linear-gradient(180deg, rgba(127, 199, 255, 0.22), rgba(127, 199, 255, 0.045)); border-color: rgba(127, 199, 255, 0.28); }}
    .tone-expensive {{ background: linear-gradient(180deg, rgba(255, 104, 124, 0.18), rgba(255, 104, 124, 0.035)); border-color: rgba(255, 104, 124, 0.26); }}
    .plan-list {{ display: grid; gap: 8px; margin-top: var(--space-sm); }}
    .reason-item {{
      border-top: 1px solid var(--line);
      padding-top: 10px;
      color: var(--muted);
    }}
    .reason-item summary {{ cursor: pointer; color: var(--text); font-size: 13px; }}
    .reason-stack {{ display: grid; gap: 8px; }}
    .reason-stack p {{
      margin: 0;
      padding: 11px 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: rgba(255, 255, 255, 0.035);
      color: var(--text);
    }}
    .health-row {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-sm); }}
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

    body.layout-mobile .shell {{ padding: 12px; }}
    body.layout-mobile .topline {{ align-items: flex-start; flex-direction: column; }}
    body.layout-mobile .layout-switcher {{ width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); }}
    body.layout-mobile .health-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    body.layout-mobile .hero {{ min-height: 560px; padding: var(--space-md); grid-template-rows: auto 1fr auto; }}
    body.layout-mobile .flow-map {{ width: min(390px, 100%); }}
    body.layout-mobile .node {{ min-width: 96px; padding: 9px 10px; }}
    body.layout-mobile .node b {{ font-size: 17px; }}
    body.layout-mobile .strategy-metrics {{ grid-template-columns: 1fr; }}
    body.layout-mobile .health-row {{ grid-template-columns: 1fr; }}

    body.layout-tablet .shell {{ width: min(980px, 100%); }}
    body.layout-tablet .dashboard {{ grid-template-columns: 1fr; }}
    body.layout-tablet .side {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    body.layout-tablet .planner {{ grid-column: 1 / -1; }}

    body.layout-desktop .shell {{ padding: 28px; }}
    body.layout-desktop .dashboard {{ grid-template-columns: minmax(0, 1.35fr) minmax(390px, 0.85fr); gap: var(--space-lg); }}
    body.layout-desktop .side {{ grid-template-rows: auto minmax(0, 1fr) auto; }}
    body.layout-desktop .hero {{ min-height: calc(100vh - 116px); }}
    body.layout-desktop .strategy-panel {{ position: sticky; top: 24px; }}

    @media (max-width: 767px) {{
      .shell {{ padding: 12px; }}
      .topline {{ align-items: flex-start; flex-direction: column; }}
      .layout-switcher {{ width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); }}
      .health-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .dashboard {{ grid-template-columns: 1fr; }}
      .hero {{ min-height: 560px; padding: var(--space-md); }}
      .flow-map {{ width: min(390px, 100%); }}
      .decision {{ font-size: clamp(28px, 9vw, 40px); }}
      .soc strong {{ font-size: 36px; }}
      .strategy-metrics, .health-row {{ grid-template-columns: 1fr; }}
    }}
    @media (min-width: 768px) and (max-width: 1199px) {{
      .shell {{ width: min(980px, 100%); }}
      .side {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .planner {{ grid-column: 1 / -1; }}
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
    @keyframes liveGlow {{
      0%, 100% {{ opacity: 0.7; transform: scale(0.98); }}
      50% {{ opacity: 1; transform: scale(1.03); }}
    }}
    @keyframes dotPulse {{
      0%, 100% {{ opacity: 0.72; transform: scale(0.92); }}
      50% {{ opacity: 1; transform: scale(1.12); }}
    }}
    """
