
from __future__ import annotations

from typing import Any


def render_fresh_home_v1(data: dict[str, Any] | None = None) -> str:
    d = data or {}

    soc = d.get("soc_percent", 62)
    pv = d.get("pv_kw", 1.8)
    house = d.get("load_kw", 0.9)
    grid = d.get("grid_kw", -0.6)

    return f"""
<!doctype html>
<html lang="nl">
<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Energy Brain EMS</title>

<style>

:root{{
--bg:#040b14;
--bg2:#071624;
--card:#091a2a;
--line:#163349;
--teal:#3df2e3;
--blue:#5ca9ff;
--green:#5ef2a1;
--yellow:#ffd166;
--text:#edf4ff;
--muted:#8ea4bb;
}}

*{{
box-sizing:border-box;
}}

html,body{{
margin:0;
padding:0;
font-family:Inter,system-ui,sans-serif;
background:
radial-gradient(circle at top,#0d2740 0%,#040b14 55%);
color:var(--text);
min-height:100%;
}}

body::before{{
content:"";
position:fixed;
inset:0;
background:
radial-gradient(circle at 20% 20%,rgba(61,242,227,.08),transparent 30%),
radial-gradient(circle at 80% 10%,rgba(92,169,255,.08),transparent 30%);
pointer-events:none;
}}

.wrapper{{
max-width:1500px;
margin:auto;
padding:28px;
}}

.hero{{
display:grid;
grid-template-columns:1.2fr .8fr;
gap:30px;
padding:42px;
border-radius:34px;
background:linear-gradient(180deg,#071826,#05111d);
border:1px solid #18364b;
box-shadow:
0 0 0 1px rgba(255,255,255,.02),
0 0 60px rgba(0,255,255,.05);
overflow:hidden;
position:relative;
}}

.hero::after{{
content:"";
position:absolute;
inset:0;
background:
linear-gradient(90deg,
transparent,
rgba(61,242,227,.03),
transparent);
pointer-events:none;
}}

@media(max-width:1100px){{
.hero{{
grid-template-columns:1fr;
padding:28px;
}}
}}

.eyebrow{{
color:var(--teal);
font-size:12px;
letter-spacing:.25em;
margin-bottom:20px;
}}

h1{{
font-size:82px;
line-height:.92;
margin:0 0 24px;
font-weight:800;
letter-spacing:-0.04em;
}}

@media(max-width:900px){{
h1{{
font-size:54px;
}}
}}

.sub{{
max-width:760px;
font-size:20px;
line-height:1.7;
color:var(--muted);
}}

.actions{{
display:flex;
gap:16px;
margin-top:34px;
flex-wrap:wrap;
}}

.btn{{
padding:16px 26px;
border-radius:18px;
text-decoration:none;
font-weight:700;
transition:.2s;
border:1px solid #214761;
background:#0e2232;
color:white;
}}

.btn:hover{{
transform:translateY(-2px);
border-color:var(--teal);
}}

.btn.primary{{
background:linear-gradient(180deg,#4cf6e7,#2fd8ca);
color:#04131c;
border:none;
box-shadow:0 0 30px rgba(61,242,227,.25);
}}

.logo-wrap{{
display:flex;
justify-content:center;
align-items:center;
position:relative;
}}

.orbit{{
position:relative;
width:340px;
height:340px;
display:flex;
justify-content:center;
align-items:center;
}}

.ring,
.ring2,
.ring3{{
position:absolute;
border-radius:50%;
border:1px solid rgba(61,242,227,.15);
}}

.ring{{
width:220px;
height:220px;
animation:spin 14s linear infinite;
}}

.ring2{{
width:280px;
height:280px;
animation:spinReverse 20s linear infinite;
}}

.ring3{{
width:340px;
height:340px;
animation:spin 28s linear infinite;
}}

.brain-core{{
width:160px;
height:160px;
border-radius:50%;
background:
radial-gradient(circle at top,#102f47 0%,#07121d 70%);
display:flex;
justify-content:center;
align-items:center;
box-shadow:
0 0 25px rgba(61,242,227,.25),
0 0 80px rgba(61,242,227,.14);
animation:pulse 4s infinite ease-in-out;
position:relative;
overflow:hidden;
}}

.brain-core::before{{
content:"";
position:absolute;
inset:0;
background:
radial-gradient(circle at 30% 30%,rgba(61,242,227,.22),transparent 40%);
}}

.brain-svg{{
width:90px;
height:90px;
stroke:var(--teal);
stroke-width:2.2;
fill:none;
filter:drop-shadow(0 0 8px rgba(61,242,227,.8));
}}

.grid{{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
gap:24px;
margin-top:28px;
}}

.card{{
background:
linear-gradient(180deg,#081827,#06131d);
border:1px solid #173449;
border-radius:28px;
padding:28px;
min-height:190px;
position:relative;
overflow:hidden;
}}

.card::before{{
content:"";
position:absolute;
inset:0;
background:
linear-gradient(180deg,
rgba(255,255,255,.02),
transparent 30%);
pointer-events:none;
}}

.label{{
font-size:13px;
letter-spacing:.18em;
text-transform:uppercase;
margin-bottom:20px;
}}

.value{{
font-size:68px;
font-weight:800;
line-height:1;
}}

.unit{{
font-size:26px;
opacity:.7;
margin-left:6px;
}}

.muted{{
color:var(--muted);
line-height:1.6;
}}

.teal{{color:var(--teal)}}
.blue{{color:var(--blue)}}
.green{{color:var(--green)}}
.yellow{{color:var(--yellow)}}

.timeline{{
display:flex;
flex-direction:column;
gap:14px;
margin-top:14px;
}}

.row{{
display:flex;
justify-content:space-between;
padding:12px 14px;
border-radius:14px;
background:#0a1c2a;
border:1px solid #153246;
}}

.time{{
color:var(--teal);
font-weight:700;
}}

.bottom-nav{{
margin-top:32px;
display:flex;
justify-content:center;
gap:18px;
flex-wrap:wrap;
padding-bottom:30px;
}}

.bottom-nav a{{
text-decoration:none;
color:white;
padding:14px 22px;
border-radius:16px;
background:#081827;
border:1px solid #173449;
transition:.2s;
}}

.bottom-nav a:hover{{
transform:translateY(-2px);
border-color:var(--teal);
}}

@keyframes spin{{
from{{transform:rotate(0deg)}}
to{{transform:rotate(360deg)}}
}}

@keyframes spinReverse{{
from{{transform:rotate(360deg)}}
to{{transform:rotate(0deg)}}
}}

@keyframes pulse{{
0%{{transform:scale(1)}}
50%{{transform:scale(1.05)}}
100%{{transform:scale(1)}}
}}

</style>
</head>

<body>

<div class="wrapper">

<section class="hero">

<div>

<div class="eyebrow">
ENERGY BRAIN EMS
</div>

<h1>
Slimme energie.<br>
Rustige controle.
</h1>

<div class="sub">
Physics-aware EMS voor Home Assistant.
Observer-first architectuur met veilige planner,
timeline reasoning en explainable energiebeslissingen.
</div>

<div class="actions">
<a class="btn primary" href="/cockpit">Cockpit openen</a>
<a class="btn" href="/api/energy-brain-cockpit">JSON API</a>
</div>

</div>

<div class="logo-wrap">

<div class="orbit">

<div class="ring"></div>
<div class="ring2"></div>
<div class="ring3"></div>

<div class="brain-core">

<svg class="brain-svg" viewBox="0 0 64 64">
<path d="M22 18
C14 18 10 24 10 30
C10 36 14 42 22 42
C22 48 26 52 32 52
C38 52 42 48 42 42
C50 42 54 36 54 30
C54 24 50 18 42 18
C42 12 38 8 32 8
C26 8 22 12 22 18Z"/>

<path d="M32 12V48"/>
<path d="M22 24L32 30L42 24"/>
<path d="M22 36L32 30L42 36"/>
</svg>

</div>
</div>
</div>

</section>

<section class="grid">

<div class="card">
<div class="label teal">Batterij</div>
<div class="value">{soc}<span class="unit">%</span></div>
</div>

<div class="card">
<div class="label yellow">PV</div>
<div class="value">{pv}<span class="unit">kW</span></div>
</div>

<div class="card">
<div class="label blue">Huis</div>
<div class="value">{house}<span class="unit">kW</span></div>
</div>

<div class="card">
<div class="label green">Net</div>
<div class="value green">{grid}<span class="unit">kW</span></div>
</div>

<div class="card">
<div class="label teal">Advies nu</div>
<div style="font-size:46px;font-weight:800;margin-bottom:14px;">
Wachten
</div>

<div class="muted">
Geen actie nodig op dit moment.
Planner blijft observer-only.
</div>
</div>

<div class="card">
<div class="label blue">Plan vandaag</div>

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
</div>

<div class="card">
<div class="label teal">Predbat benchmark</div>

<div class="muted">
Planning volgt Predbat-referentiegedrag in observer-mode.
</div>
</div>

<div class="card">
<div class="label yellow">Safety</div>

<div class="muted">
Display data uit laatste geldige cyclus.
Geen uitvoering toegestaan.
</div>
</div>

</section>

<nav class="bottom-nav">
<a href="/">Home</a>
<a href="/cockpit">Cockpit</a>
<a href="/hillview">Hillview</a>
<a href="/api/latest-cycle">Cycle</a>
</nav>

</div>

</body>
</html>
"""
