from __future__ import annotations

from typing import Any


def render_fresh_home_v1(data: dict[str, Any] | None = None) -> str:
    data = data or {}

    soc = data.get("soc_percent", 62)
    pv = data.get("pv_kw", 1.8)
    house = data.get("house_kw", 0.9)
    grid = data.get("grid_kw", -0.6)

    decision = data.get("decision", "Wachten")
    decision_reason = data.get(
        "decision_reason",
        "Accu-reserve behouden tot goedkoper laadmoment."
    )

    predbat_text = data.get(
        "predbat_text",
        "Planning volgt Predbat-referentiegedrag in observer-mode."
    )

    degraded = bool(data.get("degraded", False))
    degraded_text = data.get(
        "degraded_text",
        "Sommige databronnen ontbreken."
    )

    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Energy Brain EMS</title>

<style>
:root{{
  --bg:#050b12;
  --card:#0d1722;
  --line:#1d3243;
  --text:#eef6ff;
  --muted:#9fb3c8;
  --teal:#52ffe0;
  --blue:#6bb8ff;
  --yellow:#ffd76a;
  --green:#7dffb3;
}}

*{{
  box-sizing:border-box;
}}

body{{
  margin:0;
  background:
    radial-gradient(circle at top,#0f2740 0%,#050b12 60%);
  color:var(--text);
  font-family:
    Inter,
    system-ui,
    sans-serif;
}}

.shell{{
  width:min(1500px,96vw);
  margin:auto;
  padding:28px;
}}

.hero{{
  position:relative;
  overflow:hidden;
  border:1px solid rgba(82,255,224,.16);
  border-radius:34px;
  background:
    linear-gradient(
      180deg,
      rgba(13,27,40,.96),
      rgba(6,15,24,.98)
    );
  padding:42px;
  margin-bottom:26px;
  min-height:320px;
}}

.logo-wrap{{
  position:absolute;
  right:40px;
  top:34px;
}}

.logo{{
  width:150px;
  height:150px;
  border-radius:50%;
  position:relative;
  display:flex;
  align-items:center;
  justify-content:center;
  background:
    radial-gradient(circle,#102535 20%,#09131d 72%);
  border:1px solid rgba(82,255,224,.25);
  box-shadow:
    0 0 50px rgba(82,255,224,.12);
}}

.logo::before{{
  content:"";
  position:absolute;
  inset:-16px;
  border-radius:50%;
  border:2px solid rgba(82,255,224,.18);
  animation:spin 12s linear infinite;
}}

.logo::after{{
  content:"";
  position:absolute;
  inset:-28px;
  border-radius:50%;
  border:1px solid rgba(107,184,255,.14);
  animation:spinrev 16s linear infinite;
}}

.brain{{
  font-size:72px;
  filter:drop-shadow(0 0 16px rgba(82,255,224,.35));
}}

@keyframes spin{{
  from{{transform:rotate(0deg)}}
  to{{transform:rotate(360deg)}}
}}

@keyframes spinrev{{
  from{{transform:rotate(360deg)}}
  to{{transform:rotate(0deg)}}
}}

.eyebrow{{
  color:var(--teal);
  text-transform:uppercase;
  letter-spacing:.18em;
  font-size:.74rem;
  margin-bottom:12px;
}}

h1{{
  margin:0;
  font-size:clamp(2.5rem,6vw,5rem);
  line-height:1;
}}

.subtitle{{
  max-width:760px;
  margin-top:18px;
  color:var(--muted);
  line-height:1.6;
  font-size:1.06rem;
}}

.hero-buttons{{
  display:flex;
  gap:14px;
  flex-wrap:wrap;
  margin-top:34px;
}}

.button{{
  text-decoration:none;
  color:#061018;
  background:var(--teal);
  padding:14px 22px;
  border-radius:16px;
  font-weight:700;
  transition:.18s;
}}

.button.secondary{{
  background:rgba(255,255,255,.06);
  color:var(--text);
  border:1px solid rgba(255,255,255,.08);
}}

.button:hover{{
  transform:translateY(-2px);
}}

.grid{{
  display:grid;
  gap:22px;
}}

.metrics{{
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
}}

.card{{
  background:rgba(10,19,29,.92);
  border:1px solid var(--line);
  border-radius:28px;
  padding:26px;
  backdrop-filter:blur(18px);
}}

.label{{
  color:var(--muted);
  margin-bottom:12px;
}}

.value{{
  font-size:2.2rem;
  font-weight:800;
}}

.unit{{
  font-size:1rem;
  opacity:.7;
  margin-left:6px;
}}

.section{{
  margin-top:24px;
  grid-template-columns:repeat(auto-fit,minmax(340px,1fr));
}}

.timeline .row{{
  display:flex;
  justify-content:space-between;
  padding:12px 0;
  border-bottom:1px solid rgba(255,255,255,.06);
}}

.timeline .row:last-child{{
  border-bottom:none;
}}

.time{{
  color:var(--teal);
  font-weight:700;
}}

.checks{{
  margin-top:18px;
  display:grid;
  gap:10px;
}}

.checks div{{
  display:flex;
  gap:10px;
  align-items:center;
}}

.muted{{
  color:var(--muted);
  line-height:1.6;
}}

.bottom-nav{{
  position:sticky;
  bottom:0;
  display:flex;
  justify-content:space-around;
  gap:10px;
  margin-top:28px;
  padding:16px;
  border-top:1px solid rgba(255,255,255,.06);
  background:rgba(4,9,14,.92);
  backdrop-filter:blur(20px);
}}

.bottom-nav a{{
  text-decoration:none;
  color:var(--muted);
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:6px;
  font-size:.82rem;
  transition:.18s;
}}

.bottom-nav a:hover{{
  color:var(--teal);
  transform:translateY(-2px);
}}

.bottom-nav a.active{{
  color:var(--teal);
}}

.ico{{
  font-size:1.2rem;
}}

@media (max-width:900px){{
  .hero{{
    padding:28px;
    min-height:auto;
  }}

  .logo-wrap{{
    position:relative;
    right:auto;
    top:auto;
    margin-bottom:24px;
  }}

  .logo{{
    width:110px;
    height:110px;
  }}

  .brain{{
    font-size:52px;
  }}

  .shell{{
    width:100%;
    padding:14px;
  }}
}}
</style>
</head>

<body>

<div class="shell">

<section class="hero">

<div class="logo-wrap">
  <div class="logo">
    <div class="brain">🧠</div>
  </div>
</div>

<div class="eyebrow">
Energy Brain EMS
</div>

<h1>
Slimme energie.<br>
Rustige controle.
</h1>

<div class="subtitle">
Physics-aware EMS voor Home Assistant.
Observer-first architectuur met veilige planner,
timeline reasoning en explainable energiebeslissingen.
</div>

<div class="hero-buttons">
  <a class="button" href="/cockpit">Cockpit openen</a>
  <a class="button secondary" href="/api/energy-brain-cockpit">JSON API</a>
</div>

</section>

<section class="grid metrics">

<article class="card">
  <div class="label">Batterij</div>
  <div class="value">{soc}<span class="unit">%</span></div>
</article>

<article class="card">
  <div class="label">PV</div>
  <div class="value" style="color:var(--yellow)">
    {pv}<span class="unit">kW</span>
  </div>
</article>

<article class="card">
  <div class="label">Huis</div>
  <div class="value" style="color:var(--blue)">
    {house}<span class="unit">kW</span>
  </div>
</article>

<article class="card">
  <div class="label">Net</div>
  <div class="value" style="color:var(--green)">
    {grid}<span class="unit">kW</span>
  </div>
</article>

</section>

<section class="grid section">

<article class="card">
  <div class="eyebrow">Advies nu</div>
  <h2>{decision}</h2>

  <div class="muted">
    {decision_reason}
  </div>

  <div class="checks">
    <div><span>✓</span> Reserve veilig</div>
    <div><span>✓</span> Planner observer-only</div>
    <div><span>✓</span> Controller safety actief</div>
  </div>
</article>

<article class="card">
  <div class="eyebrow">Plan vandaag</div>

  <div class="timeline">
    <div class="row">
      <div class="time">03:00</div>
      <div>Laden goedkoop</div>
    </div>

    <div class="row">
      <div class="time">12:00</div>
      <div>PV overschot</div>
    </div>

    <div class="row">
      <div class="time">18:00</div>
      <div>Ontladen piekprijs</div>
    </div>
  </div>
</article>

<article class="card">
  <div class="eyebrow">Predbat benchmark</div>

  <div class="muted">
    {predbat_text}
  </div>
</article>

<article class="card">
  <div class="eyebrow">Safety</div>

  <div class="muted">
    {degraded_text if degraded else "Alle display-inputs zijn geldig. Controller gates blijven leidend."}
  </div>
</article>

</section>

<nav class="bottom-nav">
  <a class="active" href="/">
    <div class="ico">⌂</div>
    <div>Home</div>
  </a>

  <a href="/cockpit">
    <div class="ico">▣</div>
    <div>Cockpit</div>
  </a>

  <a href="/api/latest-cycle">
    <div class="ico">⌁</div>
    <div>Cycle</div>
  </a>

  <a href="/hillview">
    <div class="ico">◇</div>
    <div>Hillview</div>
  </a>
</nav>

</div>

</body>
</html>
"""
