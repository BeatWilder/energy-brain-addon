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
    radial-gradient(circle at 50% 49%, rgba(101,240,167,.22), transparent 18%),
    radial-gradient(circle at 50% 49%, rgba(127,199,255,.11), transparent 33%),
    radial-gradient(circle at 50% 12%, rgba(255,209,102,.13), transparent 31%),
    radial-gradient(circle at 14% 52%, rgba(127,199,255,.12), transparent 30%),
    radial-gradient(circle at 86% 52%, rgba(88,232,182,.12), transparent 30%),
    linear-gradient(180deg, rgba(255,255,255,.038), rgba(255,255,255,.004)),
    rgba(4,7,10,.72);
  border:1px solid rgba(255,255,255,.055);
  box-shadow:var(--shadow-hero, 0 30px 110px rgba(0,0,0,.45)), inset 0 1px 0 rgba(255,255,255,.06);
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
    radial-gradient(circle, rgba(245,248,251,.95) 0 3px, transparent 4px),
    radial-gradient(circle, rgba(101,240,167,.18), rgba(101,240,167,.07) 41%, transparent 62%),
    conic-gradient(from -32deg, rgba(101,240,167,.98) 0 108deg, rgba(127,199,255,.76) 108deg 156deg, rgba(255,255,255,.08) 156deg 360deg);
  box-shadow:
    0 0 26px rgba(101,240,167,.35),
    0 0 68px rgba(88,232,182,.20),
    inset 0 0 0 15px rgba(4,7,10,.90),
    inset 0 0 0 17px rgba(255,255,255,.08),
    inset 0 0 44px rgba(101,240,167,.20);
  animation:pf-v2-charge 7.5s linear infinite, pf-v2-pulse 4.8s ease-in-out infinite;
}

.pf-v2::after{
  z-index:0;
  inset:0;
  background:
    linear-gradient(90deg, transparent 8%, rgba(127,199,255,.10) 36%, rgba(245,248,251,.36) 50%, rgba(88,232,182,.12) 64%, transparent 92%),
    linear-gradient(180deg, transparent 8%, rgba(255,209,102,.13) 31%, rgba(245,248,251,.30) 50%, rgba(101,240,167,.16) 70%, transparent 92%),
    radial-gradient(circle at 50% 50%, rgba(245,248,251,.22), transparent 2px),
    repeating-conic-gradient(from 0deg at 50% 50%, rgba(255,255,255,.13) 0 4deg, transparent 4deg 16deg);
  mask:
    linear-gradient(90deg, transparent 10%, #000 32% 68%, transparent 90%),
    linear-gradient(180deg, transparent 10%, #000 30% 72%, transparent 91%),
    radial-gradient(circle at 50% 50%, #000 0 38%, transparent 39%);
  mask-composite:add;
  -webkit-mask:
    linear-gradient(90deg, transparent 10%, #000 32% 68%, transparent 90%),
    linear-gradient(180deg, transparent 10%, #000 30% 72%, transparent 91%),
    radial-gradient(circle at 50% 50%, #000 0 38%, transparent 39%);
  -webkit-mask-composite:source-over;
  opacity:.82;
  filter:blur(.2px);
  animation:pf-v2-flow 4.2s linear infinite;
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
    radial-gradient(circle at 50% 24%, rgba(255,255,255,.105), transparent 35%),
    linear-gradient(180deg, rgba(18,27,36,.94), rgba(5,9,14,.94));
  border:1px solid rgba(255,255,255,.12);
  color:var(--pf-text);
  box-shadow:0 18px 38px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.10);
  backdrop-filter:blur(18px) saturate(1.12);
  -webkit-backdrop-filter:blur(18px) saturate(1.12);
}

.pf-node::before{
  content:"";
  position:absolute;
  inset:-5px;
  border-radius:inherit;
  border:1px solid var(--pf-node-line);
  box-shadow:0 0 24px var(--pf-node-glow);
  opacity:.78;
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
  text-shadow:0 1px 12px rgba(0,0,0,.42);
}

.pf-solar{
  left:50%;
  top:7%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-solar);
  --pf-node-line:rgba(255,209,102,.52);
  --pf-node-glow:rgba(255,209,102,.24);
}

.pf-home{
  right:7%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-home);
  --pf-node-line:rgba(88,232,182,.50);
  --pf-node-glow:rgba(88,232,182,.23);
}

.pf-grid{
  left:7%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-grid);
  --pf-node-line:rgba(127,199,255,.50);
  --pf-node-glow:rgba(127,199,255,.24);
}

.pf-battery{
  left:50%;
  bottom:7%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-battery);
  --pf-node-line:rgba(101,240,167,.54);
  --pf-node-glow:rgba(101,240,167,.26);
}

@keyframes pf-v2-charge{
  to{ transform:translate(-50%, -50%) rotate(360deg); }
}

@keyframes pf-v2-pulse{
  0%,100%{ opacity:.88; }
  50%{ opacity:1; }
}

@keyframes pf-v2-flow{
  from{ background-position:0 0, 0 0, 0 0, 0 0; }
  to{ background-position:42px 0, 0 42px, 0 0, 70px 0; }
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
