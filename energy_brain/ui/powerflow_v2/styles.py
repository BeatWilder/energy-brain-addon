def render_powerflow_v2_css() -> str:
    return """
.pf-v2{
  position:relative;
  width:100%;
  height:clamp(360px, 62vw, 500px);
  min-height:360px;
  overflow:hidden;
  isolation:isolate;
  border-radius:var(--radius-lg, 8px);
  --pf-solar:#f2c66d;
  --pf-home:#d8e2ec;
  --pf-battery:#68d391;
  --pf-grid:#7fb7df;
  --pf-text:var(--text, #f5f8fb);
  --pf-muted:var(--muted, #9aa7b3);
  --flow-intensity:.56;
  --particle-density:4;
  background:
    linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.012)),
    radial-gradient(circle at 50% 56%, rgba(104,211,145,.065), transparent 30%),
    rgba(6,10,14,.94);
  border:1px solid rgba(255,255,255,.075);
  box-shadow:var(--shadow-hero, 0 24px 70px rgba(0,0,0,.38)), inset 0 1px 0 rgba(255,255,255,.055);
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
  top:55%;
  width:clamp(58px, 14vw, 86px);
  height:clamp(104px, 24vw, 142px);
  transform:translate(-50%, -50%);
  border-radius:16px;
  background:
    linear-gradient(180deg, transparent 0 36%, rgba(104,211,145,.82) 36% 100%),
    linear-gradient(180deg, rgba(21,30,38,.94), rgba(8,13,18,.98));
  border:1px solid rgba(216,226,236,.22);
  box-shadow:
    0 18px 42px rgba(0,0,0,.28),
    0 0 28px rgba(104,211,145,.10),
    inset 0 1px 0 rgba(255,255,255,.12),
    inset 0 -18px 28px rgba(27,123,78,.20);
}

.pf-v2::after{
  z-index:0;
  inset:0;
  background:
    radial-gradient(circle at 50% 55%, rgba(216,226,236,.34) 0 3px, transparent 4px),
    radial-gradient(circle at 50% 27%, rgba(242,198,109,.72) 0 3px, transparent 4px),
    radial-gradient(circle at 23% 50%, rgba(127,183,223,.62) 0 3px, transparent 4px),
    radial-gradient(circle at 77% 50%, rgba(216,226,236,.62) 0 3px, transparent 4px),
    radial-gradient(circle at 50% 83%, rgba(104,211,145,.64) 0 3px, transparent 4px),
    linear-gradient(180deg, transparent 20%, rgba(242,198,109,.42) 20% 54%, transparent 54%),
    linear-gradient(90deg, transparent 17%, rgba(127,183,223,.38) 17% 46%, transparent 46%),
    linear-gradient(90deg, transparent 54%, rgba(216,226,236,.32) 54% 83%, transparent 83%),
    linear-gradient(180deg, transparent 56%, rgba(104,211,145,.40) 56% 86%, transparent 86%);
  background-size:
    100% 100%,
    100% 100%,
    100% 100%,
    100% 100%,
    100% 100%,
    2px 100%,
    100% 2px,
    100% 2px,
    2px 100%;
  background-position:center;
  background-repeat:no-repeat;
  opacity:.78;
  animation:pf-v2-flow 9s ease-in-out infinite;
}

.pf-node{
  position:absolute;
  z-index:2;
  width:clamp(68px, 15vw, 94px);
  height:clamp(68px, 15vw, 94px);
  border-radius:999px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:5px;
  background:
    radial-gradient(circle at 50% 16%, rgba(255,255,255,.10), transparent 35%),
    linear-gradient(180deg, rgba(19,27,35,.86), rgba(8,13,18,.94));
  border:1px solid rgba(255,255,255,.13);
  color:var(--pf-text);
  box-shadow:0 14px 28px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.09);
  backdrop-filter:blur(16px) saturate(1.05);
  -webkit-backdrop-filter:blur(16px) saturate(1.05);
}

.pf-node::before{
  content:"";
  position:absolute;
  inset:-3px;
  border-radius:inherit;
  border:1px solid var(--pf-node-line);
  box-shadow:0 0 12px var(--pf-node-glow);
  opacity:.70;
}

.pf-node::after{
  content:"";
  position:absolute;
  width:8px;
  height:8px;
  left:50%;
  top:18px;
  transform:translateX(-50%);
  border-radius:inherit;
  background:var(--pf-node-color);
  box-shadow:0 0 10px var(--pf-node-glow);
  opacity:.86;
}

.pf-node span{
  position:relative;
  z-index:1;
  max-width:90%;
  overflow-wrap:anywhere;
  color:var(--pf-text);
  font-size:clamp(11px, 2.45vw, 13px);
  line-height:1.1;
  font-weight:670;
  letter-spacing:0;
  text-align:center;
  text-shadow:0 1px 8px rgba(0,0,0,.32);
}

.pf-solar{
  left:50%;
  top:8%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-solar);
  --pf-node-line:rgba(242,198,109,.34);
  --pf-node-glow:rgba(242,198,109,.16);
}

.pf-home{
  right:6%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-home);
  --pf-node-line:rgba(216,226,236,.30);
  --pf-node-glow:rgba(216,226,236,.12);
}

.pf-grid{
  left:6%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-grid);
  --pf-node-line:rgba(127,183,223,.32);
  --pf-node-glow:rgba(127,183,223,.14);
}

.pf-battery{
  left:50%;
  bottom:5%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-battery);
  --pf-node-line:rgba(104,211,145,.34);
  --pf-node-glow:rgba(104,211,145,.15);
}

@keyframes pf-v2-flow{
  0%,100%{ opacity:.72; }
  50%{ opacity:.86; }
}

@media (max-width: 620px){
  .pf-v2{
    height:380px;
    min-height:380px;
    border-radius:var(--radius-lg, 8px);
  }

  .pf-home{ right:3%; }
  .pf-grid{ left:3%; }
  .pf-solar{ top:7%; }
  .pf-battery{ bottom:4%; }
}

@media (prefers-reduced-motion: reduce){
  .pf-v2::after{
    animation:none;
  }
}
"""
