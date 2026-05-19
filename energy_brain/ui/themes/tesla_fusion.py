from __future__ import annotations


def render_theme_css() -> str:
    return """
:root{
  --bg:#081018;
  --panel:#101922;
  --text:#f4f7fb;
}

html,body{
  margin:0;
  padding:0;
  background:var(--bg);
  color:var(--text);
  font-family:
    Inter,
    system-ui,
    sans-serif;
}

body{
  min-height:100vh;
}

.shell{
  width:min(1600px,96vw);
  margin:0 auto;
  padding:16px;
}

.topline{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:18px;
}

.brand{
  font-size:28px;
  font-weight:800;
}

.eyebrow{
  opacity:.7;
  font-size:12px;
  letter-spacing:.08em;
  text-transform:uppercase;
}

.dashboard{
  display:grid;
  grid-template-columns:minmax(0,1.3fr) minmax(320px,.7fr);
  gap:18px;
}

.side{
  display:flex;
  flex-direction:column;
  gap:18px;
}

.panel,
.hero{
  background:var(--panel);
  border-radius:28px;
  border:1px solid rgba(255,255,255,.06);
  overflow:hidden;
}

.layout-switcher{
  display:flex;
  gap:8px;
}

.layout-link{
  color:white;
  text-decoration:none;
  padding:8px 12px;
  border-radius:999px;
  background:rgba(255,255,255,.06);
}

.health-strip{
  margin-bottom:18px;
}

.error-page{
  padding:40px;
}

@media (max-width:900px){

  .dashboard{
    grid-template-columns:1fr;
  }

  .shell{
    width:100%;
    padding:10px;
    box-sizing:border-box;
  }
}
"""
