def render_powerflow_v2_css() -> str:
    return """
.pf-v2{
  position:relative;
  width:100%;
  height:clamp(360px, 62vw, 520px);
  min-height:360px;
  overflow:hidden;
  isolation:isolate;
  border-radius:var(--radius-lg, 8px);
  --pf-solar:#ffd166;
  --pf-home:#58e8b6;
  --pf-battery:#65f0a7;
  --pf-grid:#7fc7ff;
  --pf-text:var(--text, #f5f8fb);
  --pf-muted:var(--muted, #98a5b2);
  background:
    radial-gradient(circle at 50% 50%, rgba(101,240,167,.095), transparent 24%),
    radial-gradient(circle at 50% 16%, rgba(255,209,102,.052), transparent 34%),
    radial-gradient(circle at 12% 55%, rgba(127,199,255,.055), transparent 32%),
    radial-gradient(circle at 88% 55%, rgba(88,232,182,.05), transparent 32%),
    linear-gradient(180deg, rgba(255,255,255,.026), rgba(255,255,255,.003)),
    rgba(4,7,10,.78);
  border:1px solid rgba(255,255,255,.055);
  box-shadow:var(--shadow-hero, 0 30px 110px rgba(0,0,0,.45)), inset 0 1px 0 rgba(255,255,255,.045);
  color:var(--pf-text);
}

.pf-v2::before,
.pf-v2::after{
  content:"";
  position:absolute;
  pointer-events:none;
}

.pf-v2::before{
  z-index:1;
  left:50%;
  top:50%;
  width:clamp(132px, 24vw, 190px);
  aspect-ratio:1;
  transform:translate(-50%, -50%);
  border-radius:999px;
  background:
    radial-gradient(circle, rgba(245,248,251,.82) 0 2px, transparent 3px),
    radial-gradient(circle, rgba(8,13,18,.96) 0 56%, transparent 57%),
    conic-gradient(from -28deg, rgba(101,240,167,.90) 0 86deg, rgba(127,199,255,.40) 86deg 116deg, rgba(255,255,255,.07) 116deg 360deg);
  box-shadow:
    0 0 18px rgba(101,240,167,.20),
    0 0 42px rgba(88,232,182,.09),
    inset 0 0 0 14px rgba(4,7,10,.93),
    inset 0 0 0 16px rgba(255,255,255,.055),
    inset 0 0 34px rgba(101,240,167,.10);
  animation:pf-v2-charge 18s linear infinite, pf-v2-pulse 8s ease-in-out infinite;
}

.pf-v2::after{
  z-index:0;
  inset:0;
  background:
    linear-gradient(90deg, transparent 12%, rgba(127,199,255,.06) 36%, rgba(245,248,251,.13) 50%, rgba(88,232,182,.06) 64%, transparent 88%),
    linear-gradient(180deg, transparent 13%, rgba(255,209,102,.055) 32%, rgba(245,248,251,.11) 50%, rgba(101,240,167,.065) 70%, transparent 88%),
    radial-gradient(circle at 50% 50%, rgba(245,248,251,.16), transparent 2px);
  mask:
    linear-gradient(90deg, transparent 13%, #000 38% 62%, transparent 87%),
    linear-gradient(180deg, transparent 14%, #000 36% 69%, transparent 88%),
    radial-gradient(circle at 50% 50%, #000 0 25%, transparent 28%);
  mask-composite:add;
  -webkit-mask:
    linear-gradient(90deg, transparent 13%, #000 38% 62%, transparent 87%),
    linear-gradient(180deg, transparent 14%, #000 36% 69%, transparent 88%),
    radial-gradient(circle at 50% 50%, #000 0 25%, transparent 28%);
  -webkit-mask-composite:source-over;
  opacity:.48;
  filter:blur(.1px);
  animation:pf-v2-flow 12s ease-in-out infinite;
}

.pf-node{
  position:absolute;
  z-index:2;
  width:clamp(82px, 16vw, 112px);
  height:clamp(82px, 16vw, 112px);
  border-radius:999px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:4px;
  background:
    radial-gradient(circle at 50% 22%, rgba(255,255,255,.075), transparent 36%),
    linear-gradient(180deg, rgba(17,25,33,.92), rgba(5,9,14,.95));
  border:1px solid rgba(255,255,255,.095);
  color:var(--pf-text);
  box-shadow:0 16px 34px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.075);
  backdrop-filter:blur(18px) saturate(1.12);
  -webkit-backdrop-filter:blur(18px) saturate(1.12);
}

.pf-node::before{
  content:"";
  position:absolute;
  inset:-5px;
  border-radius:inherit;
  border:1px solid var(--pf-node-line);
  box-shadow:0 0 18px var(--pf-node-glow);
  opacity:.58;
}

.pf-node::after{
  content:"";
  position:absolute;
  inset:9px;
  border-radius:inherit;
  border:1px solid rgba(255,255,255,.055);
  opacity:.9;
}

.pf-node span{
  position:relative;
  z-index:1;
  max-width:90%;
  overflow-wrap:anywhere;
  color:var(--pf-text);
  font-size:clamp(12px, 2.7vw, 15px);
  line-height:1.05;
  font-weight:780;
  letter-spacing:0;
  text-align:center;
  text-shadow:0 1px 10px rgba(0,0,0,.34);
}

.pf-solar{
  left:50%;
  top:7%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-solar);
  --pf-node-line:rgba(255,209,102,.38);
  --pf-node-glow:rgba(255,209,102,.14);
}

.pf-home{
  right:7%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-home);
  --pf-node-line:rgba(88,232,182,.36);
  --pf-node-glow:rgba(88,232,182,.13);
}

.pf-grid{
  left:7%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-grid);
  --pf-node-line:rgba(127,199,255,.36);
  --pf-node-glow:rgba(127,199,255,.14);
}

.pf-battery{
  left:50%;
  bottom:7%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-battery);
  --pf-node-line:rgba(101,240,167,.40);
  --pf-node-glow:rgba(101,240,167,.15);
}

@keyframes pf-v2-charge{
  to{ transform:translate(-50%, -50%) rotate(360deg); }
}

@keyframes pf-v2-pulse{
  0%,100%{ opacity:.82; }
  50%{ opacity:.94; }
}

@keyframes pf-v2-flow{
  from{ background-position:0 0, 0 0, 0 0; }
  to{ background-position:24px 0, 0 24px, 0 0; }
}

@media (max-width: 620px){
  .pf-v2{
    height:390px;
    min-height:390px;
    border-radius:var(--radius-lg, 8px);
  }

  .pf-home{ right:4%; }
  .pf-grid{ left:4%; }
  .pf-solar{ top:6%; }
  .pf-battery{ bottom:6%; }
}

@media (prefers-reduced-motion: reduce){
  .pf-v2::before,
  .pf-v2::after{
    animation:none;
  }
}
"""
