from __future__ import annotations

from html import escape
from typing import Any


def _fmt(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return escape(text) if text else fallback


def render_fresh_home_v1(data: dict[str, Any] | None = None) -> str:
    """
    UI-only fresh Energy Brain home screen.

    Safety:
    - no Home Assistant service calls
    - no AlphaESS writes
    - no planner dispatch
    - display/observer only
    """
    data = data or {}

    mode = _fmt(data.get("mode", "Observer-only"))
    execution = _fmt(data.get("execution", "Geen aansturing"))
    update = _fmt(data.get("last_update", "laatste cyclus"))
    decision = _fmt(data.get("decision", "Wachten"))
    decision_reason = _fmt(data.get("decision_reason", "Geen actie nodig op dit moment."))

    soc = _fmt(data.get("soc", "—"))
    pv_now = _fmt(data.get("pv_now", "—"))
    house = _fmt(data.get("house", "—"))
    grid = _fmt(data.get("grid", "—"))

    predbat_text = _fmt(
        data.get(
            "predbat_summary",
            "Predbat vergelijking beschikbaar zodra benchmarkdata in de display-cyclus zit.",
        )
    )

    degraded = bool(data.get("degraded", True))
    degraded_text = _fmt(
        data.get(
            "degraded_text",
            "Display data uit laatste geldige cyclus. Geen uitvoering toegestaan.",
        )
    )

    return f"""<!doctype html>
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
      --line2:#22536a;
      --text:#edf7ff;
      --muted:#9aaabd;
      --muted2:#6f8192;
      --teal:#35f2d0;
      --blue:#61a6ff;
      --green:#5df0a2;
      --amber:#ffd36a;
      --purple:#a98cff;
      --danger:#ff6b6b;
      --shadow:0 18px 60px rgba(0,0,0,.35);
      --radius:24px;
    }}

    * {{ box-sizing:border-box; }}

    body {{
      margin:0;
      min-height:100vh;
      color:var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 80% 8%, rgba(53,242,208,.13), transparent 28rem),
        radial-gradient(circle at 12% 24%, rgba(97,166,255,.09), transparent 24rem),
        linear-gradient(180deg, #02070d 0%, var(--bg0) 38%, #03070c 100%);
      letter-spacing:.01em;
    }}

    body:before {{
      content:"";
      position:fixed;
      inset:0;
      pointer-events:none;
      background-image:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
      background-size:48px 48px;
      mask-image:linear-gradient(180deg, rgba(0,0,0,.55), transparent 72%);
    }}

    .app {{
      position:relative;
      width:min(100%, 960px);
      margin:0 auto;
      padding:22px 18px 96px;
    }}

    .topbar {{
      display:flex;
      align-items:center;
      gap:16px;
      height:54px;
      margin-bottom:16px;
    }}

    .hamburger {{
      width:42px;
      height:42px;
      border-radius:14px;
      display:grid;
      place-items:center;
      color:var(--text);
      font-size:28px;
      background:rgba(255,255,255,.035);
      border:1px solid rgba(255,255,255,.06);
    }}

    .brain {{
      width:42px;
      height:42px;
      border-radius:16px;
      display:grid;
      place-items:center;
      color:var(--teal);
      background:rgba(53,242,208,.08);
      border:1px solid rgba(53,242,208,.22);
      font-size:24px;
    }}

    .title {{
      font-size:25px;
      font-weight:700;
      letter-spacing:.03em;
      white-space:nowrap;
    }}

    .chips {{
      display:flex;
      gap:10px;
      flex-wrap:wrap;
      margin:8px 0 18px;
    }}

    .chip {{
      display:inline-flex;
      align-items:center;
      gap:9px;
      height:42px;
      padding:0 16px;
      border-radius:15px;
      font-size:15px;
      font-weight:700;
      color:var(--teal);
      background:rgba(53,242,208,.075);
      border:1px solid rgba(53,242,208,.22);
    }}

    .chip.secondary {{
      color:#c7d1dd;
      background:rgba(255,255,255,.055);
      border-color:rgba(255,255,255,.07);
    }}

    .hero {{
      position:relative;
      overflow:hidden;
      border-radius:28px;
      padding:25px;
      min-height:235px;
      background:
        linear-gradient(135deg, rgba(10,30,45,.94), rgba(7,16,25,.96)),
        radial-gradient(circle at 84% 45%, rgba(53,242,208,.12), transparent 18rem);
      border:1px solid rgba(53,242,208,.34);
      box-shadow:var(--shadow);
      margin-bottom:16px;
    }}

    .hero:after {{
      content:"";
      position:absolute;
      right:18px;
      top:35px;
      width:210px;
      height:210px;
      border-radius:50%;
      background:
        radial-gradient(circle, rgba(53,242,208,.2) 0 10%, transparent 11%),
        repeating-radial-gradient(circle, rgba(97,166,255,.22) 0 1px, transparent 2px 22px);
      opacity:.75;
    }}

    .eyebrow {{
      color:var(--teal);
      text-transform:uppercase;
      font-size:13px;
      font-weight:900;
      letter-spacing:.18em;
      margin-bottom:8px;
    }}

    .hero h1 {{
      position:relative;
      z-index:2;
      font-size:46px;
      line-height:1.02;
      margin:0 0 18px;
      letter-spacing:-.04em;
    }}

    .hero-list {{
      position:relative;
      z-index:2;
      display:grid;
      gap:9px;
      max-width:410px;
      color:#dce8f3;
      font-size:18px;
      margin-bottom:18px;
    }}

    .hero-list div {{
      display:flex;
      gap:10px;
      align-items:center;
    }}

    .hero-note {{
      position:relative;
      z-index:2;
      max-width:520px;
      padding-top:16px;
      border-top:1px solid rgba(53,242,208,.23);
      color:var(--muted);
      font-size:18px;
      line-height:1.45;
    }}

    .grid {{
      display:grid;
      grid-template-columns:1fr 1fr;
      gap:12px;
    }}

    .card {{
      border-radius:22px;
      padding:18px;
      background:linear-gradient(160deg, rgba(13,29,43,.96), rgba(7,16,25,.96));
      border:1px solid rgba(255,255,255,.075);
      box-shadow:0 10px 30px rgba(0,0,0,.18);
    }}

    .metric {{
      min-height:135px;
    }}

    .metric .label {{
      color:var(--teal);
      text-transform:uppercase;
      font-size:14px;
      font-weight:900;
      letter-spacing:.16em;
      margin-bottom:13px;
    }}

    .metric .value {{
      display:flex;
      align-items:baseline;
      gap:8px;
      font-size:46px;
      font-weight:900;
      letter-spacing:-.05em;
    }}

    .unit {{
      color:var(--muted);
      font-size:22px;
      font-weight:700;
      letter-spacing:0;
    }}

    .bar {{
      height:5px;
      margin-top:16px;
      border-radius:99px;
      background:rgba(255,255,255,.08);
      overflow:hidden;
    }}

    .bar span {{
      display:block;
      height:100%;
      width:63%;
      background:linear-gradient(90deg, var(--teal), var(--green));
      border-radius:99px;
    }}

    .section {{
      margin-top:12px;
    }}

    .advice {{
      border-color:rgba(53,242,208,.24);
      min-height:235px;
    }}

    .advice h2 {{
      font-size:34px;
      margin:8px 0 6px;
      letter-spacing:-.03em;
    }}

    .muted {{
      color:var(--muted);
      line-height:1.45;
    }}

    .checks {{
      margin-top:16px;
      padding-top:14px;
      border-top:1px solid rgba(53,242,208,.18);
      display:grid;
      gap:8px;
      color:#dce8f3;
      font-size:16px;
    }}

    .checks span {{
      color:var(--teal);
      margin-right:8px;
    }}

    .timeline {{
      display:grid;
      gap:10px;
      margin-top:12px;
    }}

    .row {{
      display:grid;
      grid-template-columns:66px 1fr;
      gap:10px;
      align-items:center;
      min-height:40px;
      padding:8px 11px;
      border-radius:13px;
      background:rgba(255,255,255,.035);
      border:1px solid rgba(255,255,255,.06);
      color:#d8e2ec;
      font-size:15px;
    }}

    .time {{
      color:#fff;
      font-weight:800;
    }}

    .benchmark {{
      border-color:rgba(169,140,255,.24);
    }}

    .benchmark .eyebrow {{
      color:var(--purple);
    }}

    .safety {{
      border-color:rgba(255,211,106,.24);
    }}

    .safety .eyebrow {{
      color:var(--amber);
    }}

    .bottom-nav {{
      position:fixed;
      left:50%;
      bottom:0;
      transform:translateX(-50%);
      width:min(100%, 960px);
      height:78px;
      padding:8px 14px calc(8px + env(safe-area-inset-bottom));
      display:grid;
      grid-template-columns:repeat(5, 1fr);
      gap:4px;
      background:rgba(3,9,15,.92);
      backdrop-filter:blur(18px);
      border-top:1px solid rgba(255,255,255,.075);
    }}

    .nav-item {{
      display:grid;
      place-items:center;
      gap:4px;
      color:var(--muted2);
      font-size:12px;
      font-weight:800;
      text-decoration:none;
    }}

    .nav-item .ico {{
      font-size:24px;
      line-height:1;
    }}

    .nav-item.active {{
      color:var(--teal);
    }}

    @media (max-width: 520px) {{
      .app {{ padding-left:14px; padding-right:14px; }}
      .title {{ font-size:22px; }}
      .hero {{ padding:22px; min-height:230px; }}
      .hero:after {{ width:155px; height:155px; right:-15px; top:42px; opacity:.48; }}
      .hero h1 {{ font-size:40px; }}
      .hero-list {{ font-size:16px; max-width:310px; }}
      .hero-note {{ font-size:16px; max-width:315px; }}
      .grid {{ gap:10px; }}
      .card {{ padding:15px; border-radius:19px; }}
      .metric {{ min-height:122px; }}
      .metric .value {{ font-size:38px; }}
      .unit {{ font-size:18px; }}
      .row {{ grid-template-columns:58px 1fr; font-size:13px; padding:8px; }}
    }}
  </style>
</head>
<body>
  <main class="app">
    <header class="topbar">
      <div class="hamburger">≡</div>
      <div class="brain">⌬</div>
      <div class="title">Energy Brain EMS</div>
    </header>

    <section class="chips">
      <div class="chip">◉ {mode}</div>
      <div class="chip secondary">{execution}</div>
    </section>

    <section class="hero">
      <div class="eyebrow">Cockpit</div>
      <h1>Vandaag</h1>
      <div class="hero-list">
        <div>◌ {mode}</div>
        <div>▣ Uitvoering geblokkeerd</div>
        <div>◷ Laatste update {update}</div>
      </div>
      <div class="hero-note">
        Energy Brain kijkt mee, vergelijkt en plant, maar stuurt nu niets aan.
      </div>
    </section>

    <section class="grid">
      <article class="card metric">
        <div class="label">SOC</div>
        <div class="value">{soc}<span class="unit">%</span></div>
        <div class="bar"><span></span></div>
      </article>

      <article class="card metric">
        <div class="label">PV nu</div>
        <div class="value">{pv_now}<span class="unit">kW</span></div>
      </article>

      <article class="card metric">
        <div class="label" style="color:var(--blue)">Huis</div>
        <div class="value">{house}<span class="unit">kW</span></div>
      </article>

      <article class="card metric">
        <div class="label" style="color:var(--blue)">Net</div>
        <div class="value" style="color:var(--green)">{grid}<span class="unit">kW</span></div>
      </article>
    </section>

    <section class="grid section">
      <article class="card advice">
        <div class="eyebrow">Advies nu</div>
        <h2>{decision}</h2>
        <div class="muted">{decision_reason}</div>
        <div class="checks">
          <div><span>✓</span>Reserve veilig</div>
          <div><span>✓</span>Goedkoop laadvenster later</div>
          <div><span>✓</span>PV verwacht</div>
        </div>
      </article>

      <article class="card">
        <div class="eyebrow" style="color:var(--blue)">Plan vandaag</div>
        <div class="timeline">
          <div class="row"><div class="time">03:00</div><div>Laden · goedkoop</div></div>
          <div class="row"><div class="time">12:00</div><div>PV laden · overschot</div></div>
          <div class="row"><div class="time">18:00</div><div>Ontladen · hoge prijs</div></div>
        </div>
      </article>

      <article class="card benchmark">
        <div class="eyebrow">Predbat vergelijking</div>
        <div class="muted">{predbat_text}</div>
      </article>

      <article class="card safety">
        <div class="eyebrow">Safety / mode</div>
        <div class="muted">{degraded_text if degraded else "Alle display-inputs zijn geldig. Uitvoering blijft afhankelijk van controller-gates."}</div>
      </article>
    </section>
  </main>

  <nav class="bottom-nav">
    <a class="nav-item active" href="#"><div class="ico">⌂</div><div>Home</div></a>
    <a class="nav-item" href="#"><div class="ico">□</div><div>Plan</div></a>
    <a class="nav-item" href="#"><div class="ico">⌁</div><div>Forecast</div></a>
    <a class="nav-item" href="#"><div class="ico">▥</div><div>Benchmark</div></a>
    <a class="nav-item" href="#"><div class="ico">◇</div><div>Safety</div></a>
  </nav>
</body>
</html>"""
