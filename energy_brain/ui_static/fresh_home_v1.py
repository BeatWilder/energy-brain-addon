from __future__ import annotations

from html import escape
from typing import Any


def _fmt(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return escape(text) if text else fallback


def _logo(kind: str = "hero") -> str:
    cls = "eb-logo eb-logo-small" if kind == "small" else "eb-logo eb-logo-hero"
    return f'''
<div class="{cls}" aria-hidden="true">
  <svg viewBox="0 0 240 240" focusable="false">
    <defs>
      <filter id="eb_glow" x="-70%" y="-70%" width="240%" height="240%">
        <feGaussianBlur stdDeviation="3.2" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <radialGradient id="eb_core" cx="50%" cy="50%" r="58%">
        <stop offset="0%" stop-color="#35f2d0" stop-opacity=".25"/>
        <stop offset="58%" stop-color="#35f2d0" stop-opacity=".07"/>
        <stop offset="100%" stop-color="#35f2d0" stop-opacity="0"/>
      </radialGradient>
    </defs>

    <circle class="eb-core" cx="120" cy="120" r="78" fill="url(#eb_core)"/>

    <g class="eb-orbit eb-orbit-slow">
      <circle cx="120" cy="120" r="94" fill="none" stroke="rgba(97,166,255,.46)" stroke-width="1.7"/>
      <circle cx="120" cy="120" r="70" fill="none" stroke="rgba(97,166,255,.28)" stroke-width="1.3"/>
      <circle cx="120" cy="120" r="106" fill="none" stroke="rgba(97,166,255,.38)" stroke-width="1.3" stroke-dasharray="2 7"/>
      <circle class="eb-dot" cx="120" cy="28" r="4.8"/>
      <circle class="eb-dot" cx="120" cy="212" r="4.8"/>
      <circle class="eb-dot" cx="28" cy="120" r="4.8"/>
      <circle class="eb-dot" cx="212" cy="120" r="4.8"/>
      <circle class="eb-dot eb-dot-soft" cx="62" cy="48" r="4"/>
      <circle class="eb-dot eb-dot-soft" cx="190" cy="72" r="4"/>
      <circle class="eb-dot eb-dot-soft" cx="182" cy="184" r="4"/>
      <circle class="eb-dot eb-dot-soft" cx="54" cy="172" r="4"/>
    </g>

    <g class="eb-orbit eb-orbit-fast">
      <path d="M36 120h23" stroke="rgba(97,166,255,.55)" stroke-width="1.6" stroke-linecap="round"/>
      <path d="M181 120h23" stroke="rgba(97,166,255,.55)" stroke-width="1.6" stroke-linecap="round"/>
      <path d="M120 36v23" stroke="rgba(97,166,255,.55)" stroke-width="1.6" stroke-linecap="round"/>
      <path d="M120 181v23" stroke="rgba(97,166,255,.55)" stroke-width="1.6" stroke-linecap="round"/>
      <circle cx="28" cy="120" r="8" fill="none" stroke="rgba(97,166,255,.82)" stroke-width="3.5"/>
      <circle cx="212" cy="120" r="8" fill="none" stroke="rgba(97,166,255,.82)" stroke-width="3.5"/>
      <circle cx="120" cy="28" r="8" fill="none" stroke="rgba(97,166,255,.82)" stroke-width="3.5"/>
      <circle cx="120" cy="212" r="8" fill="none" stroke="rgba(97,166,255,.82)" stroke-width="3.5"/>
    </g>

    <g class="eb-brain" filter="url(#eb_glow)">
      <path d="M113 70 C101 61 82 65 78 82 C61 81 49 93 50 111 C39 121 42 143 60 149 C60 168 74 178 91 174 C102 181 115 174 115 160 L115 80 C115 76 115 73 113 70Z"
            fill="none" stroke="#35f2d0" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>
      <path d="M127 70 C139 61 158 65 162 82 C179 81 191 93 190 111 C201 121 198 143 180 149 C180 168 166 178 149 174 C138 181 125 174 125 160 L125 80 C125 76 125 73 127 70Z"
            fill="none" stroke="#35f2d0" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>
      <path d="M120 76v92" stroke="#35f2d0" stroke-width="5" stroke-linecap="round"/>

      <path d="M70 120h28l21 16" stroke="#35f2d0" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M86 96l24-18" stroke="#35f2d0" stroke-width="4" stroke-linecap="round"/>
      <path d="M98 120v34" stroke="#35f2d0" stroke-width="4" stroke-linecap="round"/>
      <path d="M170 120h-28l-21 16" stroke="#35f2d0" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M154 96l-24-18" stroke="#35f2d0" stroke-width="4" stroke-linecap="round"/>
      <path d="M142 120v34" stroke="#35f2d0" stroke-width="4" stroke-linecap="round"/>

      <circle class="eb-node" cx="70" cy="120" r="7"/>
      <circle class="eb-node" cx="86" cy="96" r="6"/>
      <circle class="eb-node" cx="110" cy="78" r="6"/>
      <circle class="eb-node" cx="98" cy="120" r="6"/>
      <circle class="eb-node" cx="98" cy="154" r="6"/>
      <circle class="eb-node" cx="170" cy="120" r="7"/>
      <circle class="eb-node" cx="154" cy="96" r="6"/>
      <circle class="eb-node" cx="130" cy="78" r="6"/>
      <circle class="eb-node" cx="142" cy="120" r="6"/>
      <circle class="eb-node" cx="142" cy="154" r="6"/>
    </g>
  </svg>
</div>
'''


def render_fresh_home_v1(display_data: dict[str, Any] | None = None) -> str:
    data = display_data or {}

    mode = _fmt(data.get("mode", "Observer-only"))
    execution = _fmt(data.get("execution", "Geen aansturing"))
    last_update = _fmt(data.get("last_update", "laatste cyclus"))
    soc = _fmt(data.get("soc", "—"))
    pv_now = _fmt(data.get("pv_now", "—"))
    house = _fmt(data.get("house", "—"))
    grid = _fmt(data.get("grid", "—"))
    decision = _fmt(data.get("decision", "Wachten"))
    decision_reason = _fmt(data.get("decision_reason", "Geen actie nodig op dit moment."))
    predbat_summary = _fmt(data.get("predbat_summary", "Predbat laadt eerder, Energy Brain wacht langer op PV."))
    degraded_text = _fmt(data.get("degraded_text", "Display data uit laatste geldige cyclus. Geen uitvoering toegestaan."))

    logo_small = _logo("small")
    logo_hero = _logo("hero")

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>Energy Brain EMS</title>
  <style>
    :root {{
      --bg0:#050b12;
      --bg1:#07131d;
      --card:#0b1824;
      --card2:#0d1d2b;
      --line:#1a3345;
      --line2:#244c63;
      --text:#eef6fb;
      --muted:#91a7b8;
      --teal:#35f2d0;
      --blue:#61a6ff;
      --green:#61d88d;
      --yellow:#ffd36a;
      --purple:#a78bfa;
      --danger:#ff7a7a;
      --shadow:0 18px 60px rgba(0,0,0,.35);
      --radius:24px;
    }}

    * {{ box-sizing:border-box; }}

    body {{
      margin:0;
      min-height:100vh;
      color:var(--text);
      background:
        radial-gradient(circle at 24% -8%, rgba(53,242,208,.16), transparent 26rem),
        radial-gradient(circle at 90% 12%, rgba(97,166,255,.12), transparent 28rem),
        linear-gradient(145deg, var(--bg0), var(--bg1));
      font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      letter-spacing:.015em;
      overflow-x:hidden;
    }}

    body:before {{
      content:"";
      position:fixed;
      inset:0;
      background-image:
        linear-gradient(rgba(255,255,255,.024) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.024) 1px, transparent 1px);
      background-size:46px 46px;
      mask-image:linear-gradient(to bottom, rgba(0,0,0,.8), transparent 82%);
      pointer-events:none;
    }}

    .app {{
      width:min(1180px,100%);
      margin:0 auto;
      padding:20px 18px 92px;
    }}

    .top {{
      position:sticky;
      top:0;
      z-index:10;
      margin:-20px -18px 18px;
      padding:18px 18px 14px;
      display:flex;
      align-items:center;
      gap:18px;
      background:rgba(5,11,18,.76);
      border-bottom:1px solid rgba(255,255,255,.08);
      backdrop-filter:blur(16px);
    }}

    .menu {{
      font-size:28px;
      color:var(--text);
      opacity:.95;
    }}

    .brand {{
      display:flex;
      align-items:center;
      gap:14px;
      font-size:24px;
      font-weight:780;
      letter-spacing:.08em;
    }}

    .chips {{
      display:flex;
      gap:12px;
      flex-wrap:wrap;
      margin:16px 0 18px;
    }}

    .chip {{
      display:inline-flex;
      align-items:center;
      gap:9px;
      padding:10px 16px;
      border-radius:14px;
      background:rgba(13,29,43,.88);
      border:1px solid rgba(255,255,255,.08);
      color:var(--muted);
      font-weight:700;
      letter-spacing:.08em;
    }}

    .chip.good {{
      color:var(--teal);
      border-color:rgba(53,242,208,.24);
      background:rgba(53,242,208,.065);
    }}

    .grid {{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:16px;
    }}

    .card {{
      position:relative;
      overflow:hidden;
      background:linear-gradient(155deg, rgba(13,29,43,.93), rgba(7,18,29,.94));
      border:1px solid rgba(71,117,147,.45);
      border-radius:var(--radius);
      box-shadow:var(--shadow);
    }}

    .hero {{
      grid-column:1 / -1;
      min-height:238px;
      padding:30px 32px;
    }}

    .hero:after {{
      content:"";
      position:absolute;
      right:24px;
      top:30px;
      width:245px;
      height:245px;
      border-radius:50%;
      background:radial-gradient(circle, rgba(53,242,208,.12), transparent 70%);
      pointer-events:none;
    }}

    .eyebrow {{
      color:var(--teal);
      font-size:14px;
      font-weight:900;
      letter-spacing:.24em;
      text-transform:uppercase;
      margin-bottom:8px;
    }}

    h1 {{
      margin:0 0 16px;
      font-size:52px;
      line-height:1;
      letter-spacing:-.04em;
    }}

    .hero-list {{
      display:grid;
      gap:8px;
      font-size:24px;
      color:var(--text);
    }}

    .hero-list span {{
      color:var(--muted);
      margin-right:12px;
    }}

    .hero-text {{
      max-width:640px;
      margin-top:22px;
      padding-top:18px;
      border-top:1px solid rgba(255,255,255,.14);
      color:var(--muted);
      font-size:22px;
      line-height:1.35;
    }}

    .metric {{
      min-height:146px;
      padding:24px 28px;
      display:grid;
      grid-template-columns:88px 1fr;
      gap:18px;
      align-items:center;
    }}

    .metric .label {{
      position:absolute;
      top:20px;
      left:24px;
      font-size:15px;
      font-weight:900;
      letter-spacing:.18em;
      color:var(--teal);
      text-transform:uppercase;
    }}

    .metric .icon {{
      margin-top:28px;
      color:#dce8f0;
      opacity:.9;
      font-size:50px;
    }}

    .metric .value {{
      margin-top:28px;
      font-size:58px;
      font-weight:820;
      letter-spacing:-.04em;
      white-space:nowrap;
    }}

    .metric .unit {{
      font-size:28px;
      font-weight:650;
      color:var(--muted);
      margin-left:6px;
    }}

    .socbar {{
      position:absolute;
      left:28px;
      right:28px;
      bottom:22px;
      height:6px;
      border-radius:999px;
      background:rgba(255,255,255,.08);
      overflow:hidden;
    }}

    .socbar span {{
      display:block;
      height:100%;
      width:min(100%, max(0%, {soc}%));
      background:linear-gradient(90deg, var(--teal), #5ceea1);
      box-shadow:0 0 18px rgba(53,242,208,.45);
    }}

    .advice, .plan, .predbat, .safety {{
      min-height:190px;
      padding:24px 28px;
    }}

    .advice h2 {{
      margin:8px 0 8px;
      font-size:36px;
    }}

    .advice p, .predbat p, .safety p {{
      margin:0;
      color:var(--text);
      font-size:20px;
      line-height:1.38;
    }}

    .ticks {{
      margin-top:18px;
      padding-top:16px;
      border-top:1px solid rgba(255,255,255,.12);
      display:grid;
      gap:8px;
      color:#d7e4ec;
      font-size:19px;
    }}

    .ticks div:before {{
      content:"✓";
      display:inline-grid;
      place-items:center;
      width:22px;
      height:22px;
      margin-right:10px;
      border-radius:50%;
      border:1px solid rgba(53,242,208,.65);
      color:var(--teal);
      font-size:14px;
    }}

    .plan-list {{
      margin-top:16px;
      display:grid;
      gap:10px;
    }}

    .plan-row {{
      display:grid;
      grid-template-columns:80px 1fr;
      align-items:center;
      gap:14px;
      padding:10px 14px;
      border:1px solid rgba(255,255,255,.10);
      border-radius:12px;
      color:#dce8f0;
      background:rgba(0,0,0,.12);
      font-size:18px;
    }}

    .plan-row time {{
      color:var(--text);
      font-size:24px;
    }}

    .predbat {{
      border-color:rgba(167,139,250,.38);
    }}

    .predbat .eyebrow {{
      color:var(--purple);
    }}

    .safety {{
      border-color:rgba(255,211,106,.42);
    }}

    .safety .eyebrow {{
      color:var(--yellow);
    }}

    .eb-logo {{
      position:relative;
      display:grid;
      place-items:center;
      flex:0 0 auto;
      color:var(--teal);
      filter:drop-shadow(0 0 16px rgba(53,242,208,.22));
    }}

    .eb-logo svg {{
      display:block;
      width:100%;
      height:100%;
      overflow:visible;
    }}

    .eb-logo-small {{
      width:48px;
      height:48px;
    }}

    .eb-logo-hero {{
      position:absolute;
      right:30px;
      top:12px;
      width:270px;
      height:270px;
      z-index:1;
      opacity:.86;
      pointer-events:none;
    }}

    .eb-core {{
      animation:ebPulse 3.8s ease-in-out infinite;
    }}

    .eb-brain {{
      animation:ebBrainGlow 3.2s ease-in-out infinite;
      transform-origin:120px 120px;
    }}

    .eb-orbit {{
      transform-origin:120px 120px;
    }}

    .eb-orbit-slow {{
      animation:ebOrbitSlow 28s linear infinite;
    }}

    .eb-orbit-fast {{
      animation:ebOrbitFast 17s linear infinite reverse;
    }}

    .eb-dot, .eb-node {{
      fill:currentColor;
      color:var(--teal);
      animation:ebNodePulse 2.8s ease-in-out infinite;
    }}

    .eb-dot {{
      color:var(--blue);
    }}

    .eb-dot-soft {{
      opacity:.74;
      animation-delay:.7s;
    }}

    @keyframes ebOrbitSlow {{
      from {{ transform:rotate(0deg); }}
      to {{ transform:rotate(360deg); }}
    }}

    @keyframes ebOrbitFast {{
      from {{ transform:rotate(0deg); }}
      to {{ transform:rotate(360deg); }}
    }}

    @keyframes ebPulse {{
      0%,100% {{ opacity:.48; transform:scale(.985); }}
      50% {{ opacity:.95; transform:scale(1.035); }}
    }}

    @keyframes ebBrainGlow {{
      0%,100% {{ opacity:.90; }}
      50% {{ opacity:1; }}
    }}

    @keyframes ebNodePulse {{
      0%,100% {{ opacity:.72; }}
      50% {{ opacity:1; }}
    }}

    .bottom {{
      position:fixed;
      left:0;
      right:0;
      bottom:0;
      z-index:20;
      display:grid;
      grid-template-columns:repeat(5, 1fr);
      gap:2px;
      padding:10px 14px max(10px, env(safe-area-inset-bottom));
      background:rgba(5,11,18,.86);
      border-top:1px solid rgba(255,255,255,.10);
      backdrop-filter:blur(18px);
    }}

    .tab {{
      display:grid;
      place-items:center;
      gap:4px;
      color:rgba(238,246,251,.55);
      font-size:14px;
      text-decoration:none;
    }}

    .tab b {{
      font-size:27px;
      line-height:1;
    }}

    .tab.active {{
      color:var(--teal);
    }}

    @media (max-width:760px) {{
      .app {{
        padding:14px 12px 88px;
      }}

      .top {{
        margin:-14px -12px 14px;
        padding:14px 14px 11px;
      }}

      .brand {{
        font-size:21px;
        letter-spacing:.09em;
      }}

      .grid {{
        grid-template-columns:1fr 1fr;
        gap:12px;
      }}

      .hero {{
        min-height:246px;
        padding:24px 22px;
      }}

      .hero h1 {{
        font-size:43px;
      }}

      .hero-list {{
        font-size:21px;
      }}

      .hero-text {{
        max-width:72%;
        font-size:20px;
      }}

      .eb-logo-hero {{
        width:178px;
        height:178px;
        right:0;
        top:34px;
        opacity:.72;
      }}

      .metric {{
        grid-template-columns:72px 1fr;
        min-height:132px;
        padding:22px 20px;
      }}

      .metric .icon {{
        font-size:42px;
      }}

      .metric .value {{
        font-size:48px;
      }}

      .metric .unit {{
        font-size:24px;
      }}

      .advice, .plan, .predbat, .safety {{
        min-height:172px;
        padding:22px 20px;
      }}

      .advice h2 {{
        font-size:32px;
      }}
    }}

    @media (max-width:520px) {{
      .grid {{
        grid-template-columns:1fr;
      }}

      .hero-text {{
        max-width:100%;
        padding-right:118px;
      }}

      .eb-logo-hero {{
        width:142px;
        height:142px;
        right:-6px;
        top:58px;
        opacity:.7;
      }}

      .metric {{
        grid-template-columns:78px 1fr;
      }}
    }}

    @media (prefers-reduced-motion:reduce) {{
      .eb-core,
      .eb-brain,
      .eb-orbit-slow,
      .eb-orbit-fast,
      .eb-dot,
      .eb-node {{
        animation:none !important;
      }}
    }}
  </style>
</head>
<body>
  <main class="app">
    <header class="top">
      <div class="menu">☰</div>
      {logo_small}
      <div class="brand">Energy Brain EMS</div>
    </header>

    <section class="chips">
      <div class="chip good">◉ {mode}</div>
      <div class="chip">{execution}</div>
    </section>

    <section class="grid">
      <section class="card hero">
        <div class="eyebrow">Cockpit</div>
        <h1>Vandaag</h1>
        {logo_hero}
        <div class="hero-list">
          <div><span>◉</span>{mode}</div>
          <div><span>▣</span>Uitvoering geblokkeerd</div>
          <div><span>◷</span>Laatste update {last_update}</div>
        </div>
        <div class="hero-text">Energy Brain kijkt mee, vergelijkt en plant, maar stuurt nu niets aan.</div>
      </section>

      <section class="card metric">
        <div class="label">SOC</div>
        <div class="icon">▣</div>
        <div class="value">{soc}<span class="unit">%</span></div>
        <div class="socbar"><span></span></div>
      </section>

      <section class="card metric">
        <div class="label">PV nu</div>
        <div class="icon">▤</div>
        <div class="value">{pv_now}<span class="unit">kW</span></div>
      </section>

      <section class="card metric">
        <div class="label" style="color:var(--blue)">Huis</div>
        <div class="icon">⌂</div>
        <div class="value">{house}<span class="unit">kW</span></div>
      </section>

      <section class="card metric">
        <div class="label" style="color:var(--blue)">Net</div>
        <div class="icon">♜</div>
        <div class="value" style="color:var(--green)">{grid}<span class="unit">kW</span></div>
      </section>

      <section class="card advice">
        <div class="eyebrow">Advies nu</div>
        <h2>{decision}</h2>
        <p>{decision_reason}</p>
        <div class="ticks">
          <div>Reserve veilig</div>
          <div>Goedkoop laadvenster later</div>
          <div>PV verwacht</div>
        </div>
      </section>

      <section class="card plan">
        <div class="eyebrow" style="color:var(--blue)">Plan vandaag</div>
        <div class="plan-list">
          <div class="plan-row"><time>03:00</time><span>Laden · goedkoop</span></div>
          <div class="plan-row"><time>12:00</time><span>PV laden · overschot</span></div>
          <div class="plan-row"><time>18:00</time><span>Ontladen · hoge prijs</span></div>
        </div>
      </section>

      <section class="card predbat">
        <div class="eyebrow">Predbat vergelijking</div>
        <p>{predbat_summary}</p>
      </section>

      <section class="card safety">
        <div class="eyebrow">Safety / mode</div>
        <p>Degraded mode:<br>{degraded_text}</p>
      </section>
    </section>
  </main>

  <nav class="bottom">
    <a class="tab active" href="/"><b>⌂</b><span>Home</span></a>
    <a class="tab" href="/cockpit"><b>▣</b><span>Plan</span></a>
    <a class="tab" href="/api/latest-cycle"><b>⌁</b><span>Forecast</span></a>
    <a class="tab" href="/api/energy-brain-cockpit"><b>▥</b><span>Benchmark</span></a>
    <a class="tab" href="/hillview"><b>⌵</b><span>Safety</span></a>
  </nav>
</body>
</html>'''
