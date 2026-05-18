from __future__ import annotations


def render_theme_css() -> str:
    return """
    :root {
      color-scheme: dark;
      --bg: #07090d;
      --panel: rgba(18, 23, 31, 0.76);
      --panel-strong: rgba(23, 30, 40, 0.9);
      --line: rgba(255, 255, 255, 0.1);
      --text: #f4f7fb;
      --muted: #8f9aa8;
      --green: #65f0a7;
      --blue: #7fc7ff;
      --amber: #ffd166;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at 50% 34%, rgba(101, 240, 167, 0.14), transparent 28rem),
        linear-gradient(180deg, #0b0f14 0%, var(--bg) 48%, #050609 100%);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
      min-height: 100vh;
    }

    .shell {
      min-height: 100vh;
      padding: 28px;
      display: grid;
      grid-template-rows: auto 1fr;
      gap: 22px;
    }

    .topline {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }

    .brand { font-size: 20px; font-weight: 650; }
    .layout-switcher { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .layout-switcher a, .chip {
      color: var(--text);
      text-decoration: none;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.045);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 12px;
    }
    .layout-switcher a.active { border-color: rgba(101, 240, 167, 0.52); color: var(--green); }

    .dashboard {
      width: min(1280px, 100%);
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1.4fr 0.9fr;
      gap: 18px;
      align-items: stretch;
    }

    .hero, .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      backdrop-filter: blur(18px);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.34);
    }
    .hero {
      min-height: 620px;
      border-radius: 8px;
      padding: 34px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      position: relative;
      overflow: hidden;
    }
    .hero:before {
      content: "";
      position: absolute;
      inset: 18% 15%;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(127, 199, 255, 0.18), transparent 62%);
      filter: blur(10px);
      pointer-events: none;
    }
    .hero-head, .hero-foot, .flow { position: relative; z-index: 1; }
    .hero-head, .hero-foot { display: flex; justify-content: space-between; gap: 18px; align-items: center; }
    .eyebrow { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; }
    .decision { font-size: 34px; font-weight: 680; margin-top: 6px; }
    .soc { text-align: right; }
    .soc strong { display: block; font-size: 46px; line-height: 1; color: var(--green); }
    .flow {
      align-self: center;
      justify-self: center;
      width: min(560px, 100%);
      aspect-ratio: 1;
      display: grid;
      place-items: center;
    }
    .core {
      width: 42%;
      aspect-ratio: 1;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: radial-gradient(circle, rgba(101, 240, 167, 0.22), rgba(16, 23, 29, 0.94) 62%);
      border: 1px solid rgba(101, 240, 167, 0.28);
      box-shadow: 0 0 70px rgba(101, 240, 167, 0.2);
      text-align: center;
    }
    .core span { color: var(--muted); font-size: 12px; }
    .core b { display: block; font-size: 30px; margin-top: 4px; }
    .node {
      position: absolute;
      min-width: 124px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      background: rgba(9, 12, 16, 0.78);
      box-shadow: 0 0 34px rgba(127, 199, 255, 0.08);
    }
    .node b { display: block; font-size: 22px; margin-bottom: 2px; }
    .node span { color: var(--muted); font-size: 12px; }
    .node.solar { top: 4%; left: 50%; transform: translateX(-50%); }
    .node.house { right: 0; top: 50%; transform: translateY(-50%); }
    .node.grid { bottom: 4%; left: 50%; transform: translateX(-50%); }
    .node.battery { left: 0; top: 50%; transform: translateY(-50%); }
    .rail { position: absolute; background: linear-gradient(90deg, transparent, rgba(101, 240, 167, 0.42), transparent); height: 1px; width: 58%; }
    .rail.vertical { transform: rotate(90deg); }
    .side { display: grid; grid-template-rows: auto 1fr auto; gap: 18px; }
    .panel { border-radius: 8px; padding: 22px; }
    .panel h2 { margin: 0 0 16px; font-size: 17px; }
    .plan-list { display: grid; gap: 12px; }
    .plan-item { border-top: 1px solid var(--line); padding-top: 12px; }
    .plan-item:first-child { border-top: 0; padding-top: 0; }
    .plan-time { color: var(--muted); font-size: 12px; }
    .plan-action { font-size: 18px; margin: 3px 0; }
    .panel p { color: var(--muted); margin: 8px 0 0; line-height: 1.45; }
    .metric-row { display: flex; justify-content: space-between; gap: 16px; border-top: 1px solid var(--line); padding-top: 12px; margin-top: 12px; }
    .metric-row span { color: var(--muted); }
    .metric-row b { text-align: right; }
    .error-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
    .error-page .panel { max-width: 520px; }

    body.layout-mobile .shell { padding: 14px; }
    body.layout-mobile .topline { align-items: flex-start; }
    body.layout-mobile .dashboard { grid-template-columns: 1fr; }
    body.layout-mobile .hero { min-height: 520px; padding: 20px; }
    body.layout-mobile .decision { font-size: 26px; }
    body.layout-mobile .soc strong { font-size: 34px; }
    body.layout-mobile .node { min-width: 104px; padding: 10px; }
    body.layout-mobile .node b { font-size: 18px; }
    body.layout-mobile .side { grid-template-rows: auto; }

    body.layout-tablet .dashboard { grid-template-columns: 1fr; max-width: 900px; }
    body.layout-tablet .hero { min-height: 560px; }
    body.layout-tablet .side { grid-template-columns: 1fr 1fr; grid-template-rows: auto; }
    body.layout-tablet .planner { grid-column: 1 / -1; }

    @media (max-width: 760px) {
      .shell { padding: 14px; }
      .topline { align-items: flex-start; flex-direction: column; }
      .dashboard { grid-template-columns: 1fr; }
      .hero { min-height: 520px; padding: 20px; }
      .hero-head, .hero-foot { align-items: flex-start; }
      .decision { font-size: 26px; }
      .soc strong { font-size: 34px; }
      .node { min-width: 104px; padding: 10px; }
      .node b { font-size: 18px; }
    }
    """

