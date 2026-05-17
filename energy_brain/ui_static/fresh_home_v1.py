
from __future__ import annotations

from typing import Any

def render_fresh_home_v1(data: dict[str, Any] | None = None) -> str:
    return '''
<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Energy Brain EMS</title>

<style>

body{
    margin:0;
    background:#030b14;
    color:white;
    font-family:Arial,sans-serif;
}

.hero{
    padding:60px;
    text-align:center;
}

.logo{
    width:180px;
    height:180px;
    margin:auto;
    border-radius:50%;
    display:flex;
    justify-content:center;
    align-items:center;
    font-size:88px;
    background:#071826;
    box-shadow:
      0 0 20px rgba(0,255,255,.25),
      0 0 60px rgba(0,255,255,.18);

    animation:pulse 4s infinite ease-in-out;
}

@keyframes pulse{
    0%{transform:scale(1)}
    50%{transform:scale(1.06)}
    100%{transform:scale(1)}
}

h1{
    font-size:72px;
    margin-top:40px;
}

.cards{
    max-width:1400px;
    margin:auto;
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
    gap:24px;
    padding:30px;
}

.card{
    background:#071826;
    border-radius:24px;
    padding:28px;
    border:1px solid #163349;
}

.bottom{
    display:flex;
    justify-content:center;
    gap:16px;
    padding:30px;
    flex-wrap:wrap;
}

.bottom a{
    color:white;
    text-decoration:none;
    background:#071826;
    padding:14px 22px;
    border-radius:14px;
    border:1px solid #163349;
}

.bottom a:hover{
    border-color:#3df2e3;
}

</style>
</head>

<body>

<section class="hero">

<div class="logo">
🧠
</div>

<h1>
Energy Brain EMS
</h1>

<p>
Slimme energie. Rustige controle.
</p>

</section>

<section class="cards">

<div class="card">
<h2>Batterij</h2>
<p>62%</p>
</div>

<div class="card">
<h2>PV</h2>
<p>1.8 kW</p>
</div>

<div class="card">
<h2>Huis</h2>
<p>0.9 kW</p>
</div>

<div class="card">
<h2>Net</h2>
<p>-0.6 kW</p>
</div>

</section>

<nav class="bottom">
<a href="/">Home</a>
<a href="/cockpit">Cockpit</a>
<a href="/hillview">Hillview</a>
<a href="/api/latest-cycle">Cycle</a>
</nav>

</body>
</html>
'''
