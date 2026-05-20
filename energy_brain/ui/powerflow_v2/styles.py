def render_powerflow_v2_css() -> str:
    return """
.pf-v2{
  position:relative;
  width:100%;
  height:clamp(338px, 68vw, 430px);
  min-height:338px;
  overflow:hidden;
  isolation:isolate;
  border-radius:var(--radius-lg, 8px);
  --pf-solar:#f4c96d;
  --pf-home:#ffcc7a;
  --pf-battery:#69e39a;
  --pf-grid:#7dc4ff;
  --pf-text:var(--text, #f5f8fb);
  --pf-muted:var(--muted, #9aa7b3);
  --pf-bg:#05090d;
  --flow-intensity:.62;
  --particle-density:3;
  --pf-active-grid:.28;
  --pf-active-battery:.24;
  background:
    radial-gradient(circle at 50% 48%, rgba(105,227,154,.12), transparent 25%),
    radial-gradient(circle at 50% 14%, rgba(244,201,109,.10), transparent 24%),
    radial-gradient(circle at 10% 48%, rgba(125,196,255,.10), transparent 26%),
    linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.012) 42%, rgba(0,0,0,.15)),
    var(--pf-bg);
  border:1px solid rgba(255,255,255,.085);
  box-shadow:
    var(--shadow-hero, 0 24px 70px rgba(0,0,0,.38)),
    inset 0 1px 0 rgba(255,255,255,.065),
    inset 0 -1px 0 rgba(255,255,255,.025);
  color:var(--pf-text);
}

.pf-v2::before,
.pf-v2::after{
  content:"";
  position:absolute;
  pointer-events:none;
}

.pf-v2::before{
  z-index:0;
  left:50%;
  top:50%;
  width:clamp(96px, 25vw, 138px);
  height:clamp(156px, 41vw, 210px);
  transform:translate(-50%, -50%);
  border-radius:22px;
  background:
    linear-gradient(180deg, transparent 0 36%, rgba(105,227,154,.18) 36% 100%),
    linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.018)),
    linear-gradient(180deg, rgba(20,32,39,.80), rgba(6,11,15,.92));
  border:1px solid rgba(216,226,236,.20);
  box-shadow:
    0 22px 58px rgba(0,0,0,.38),
    0 0 34px rgba(105,227,154,var(--pf-active-battery)),
    inset 0 1px 0 rgba(255,255,255,.12),
    inset 0 -24px 34px rgba(37,160,95,.18);
}

.pf-v2::after{
  z-index:0;
  inset:0;
  background:
    radial-gradient(circle at 50% 50%, rgba(245,250,255,.42) 0 3px, transparent 4px),
    linear-gradient(180deg, transparent 18%, rgba(244,201,109,.70) 18% 42%, transparent 42%),
    linear-gradient(90deg, transparent 16%, rgba(125,196,255,.50) 16% 42%, transparent 42%),
    linear-gradient(90deg, transparent 58%, rgba(255,204,122,.56) 58% 84%, transparent 84%),
    radial-gradient(circle at 50% 19%, rgba(244,201,109,.82) 0 3px, transparent 4px),
    radial-gradient(circle at 18% 50%, rgba(125,196,255,.74) 0 3px, transparent 4px),
    radial-gradient(circle at 82% 50%, rgba(255,204,122,.74) 0 3px, transparent 4px);
  background-size:
    100% 100%,
    2px 100%,
    100% 2px,
    100% 2px,
    100% 100%,
    100% 100%,
    100% 100%;
  background-position:center;
  background-repeat:no-repeat;
  opacity:.72;
}

.pf-caption{
  position:absolute;
  z-index:3;
  left:clamp(16px, 5vw, 24px);
  top:12px;
  color:rgba(245,248,251,.82);
  font-size:12px;
  line-height:1;
  font-weight:720;
  letter-spacing:.08em;
  text-transform:uppercase;
}

.pf-node{
  position:absolute;
  z-index:2;
  width:clamp(76px, 19vw, 98px);
  min-height:clamp(76px, 19vw, 98px);
  height:auto;
  aspect-ratio:1;
  border-radius:999px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:3px;
  background:
    radial-gradient(circle at 50% 16%, rgba(255,255,255,.10), transparent 35%),
    linear-gradient(180deg, rgba(19,27,35,.86), rgba(8,13,18,.94));
  border:1px solid rgba(255,255,255,.13);
  color:var(--pf-text);
  box-shadow:
    0 14px 28px rgba(0,0,0,.25),
    0 0 22px var(--pf-node-glow),
    inset 0 1px 0 rgba(255,255,255,.09);
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
  width:7px;
  height:7px;
  left:50%;
  top:15px;
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

.pf-node em{
  position:relative;
  z-index:1;
  color:var(--pf-node-color);
  font-size:clamp(10px, 2.25vw, 12px);
  line-height:1.08;
  font-style:normal;
  font-weight:620;
  text-align:center;
  opacity:.94;
}

.pf-solar{
  left:50%;
  top:10%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-solar);
  --pf-node-line:rgba(244,201,109,.38);
  --pf-node-glow:rgba(244,201,109,.18);
}

.pf-home{
  right:5%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-home);
  --pf-node-line:rgba(255,204,122,.32);
  --pf-node-glow:rgba(255,204,122,.14);
}

.pf-grid{
  left:5%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-grid);
  --pf-node-line:rgba(125,196,255,.35);
  --pf-node-glow:rgba(125,196,255,.16);
}

.pf-battery{
  left:50%;
  top:50%;
  width:clamp(112px, 30vw, 148px);
  min-height:clamp(174px, 44vw, 220px);
  aspect-ratio:auto;
  padding:clamp(18px, 4vw, 24px) 10px 14px;
  border-radius:24px;
  transform:translate(-50%, -50%);
  --pf-node-color:var(--pf-battery);
  --pf-node-line:rgba(105,227,154,.38);
  --pf-node-glow:rgba(105,227,154,.22);
}

.pf-battery::after{
  display:none;
}

.pf-battery span{
  margin-top:5px;
  font-size:clamp(12px, 2.5vw, 14px);
}

.pf-battery em{
  color:rgba(105,227,154,.98);
}

.pf-battery-shell{
  position:relative;
  z-index:1;
  display:block;
  width:clamp(50px, 13vw, 68px);
  height:clamp(94px, 24vw, 126px);
  border-radius:13px;
  border:1px solid rgba(216,226,236,.26);
  background:
    linear-gradient(180deg, rgba(255,255,255,.10), transparent 20%),
    linear-gradient(180deg, rgba(13,24,29,.72), rgba(5,10,13,.78));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.14),
    inset 0 -18px 28px rgba(10,22,18,.55),
    0 0 26px rgba(105,227,154,.17);
  overflow:hidden;
}

.pf-battery-shell::before{
  content:"";
  position:absolute;
  left:36%;
  right:36%;
  top:-1px;
  height:8px;
  border-radius:0 0 3px 3px;
  background:rgba(216,226,236,.24);
}

.pf-battery-shell::after{
  content:"";
  position:absolute;
  left:11px;
  top:18px;
  width:14px;
  height:3px;
  border-radius:999px;
  background:rgba(255,255,255,.12);
  box-shadow:0 10px 0 rgba(255,255,255,.08);
}

.pf-battery-shell b{
  position:absolute;
  left:9px;
  right:9px;
  bottom:9px;
  height:58%;
  border-radius:9px;
  background:
    linear-gradient(180deg, rgba(145,255,180,.95), rgba(42,194,106,.74)),
    linear-gradient(90deg, rgba(255,255,255,.12), transparent 48%);
  box-shadow:
    0 0 24px rgba(105,227,154,.30),
    inset 0 1px 0 rgba(255,255,255,.23);
  animation:pf-battery-breathe 4.8s ease-in-out infinite;
}

.pf-v2[data-battery-flow="charging"]{
  --pf-active-battery:.34;
}

.pf-v2[data-battery-flow="discharging"]{
  --pf-active-battery:.30;
}

.pf-v2[data-grid-flow="importing"],
.pf-v2[data-grid-flow="exporting"]{
  --pf-active-grid:.42;
}

.pf-v2[data-grid-flow="idle"] .pf-grid,
.pf-v2[data-battery-flow="idle"] .pf-battery{
  opacity:.78;
}

.pf-v2[data-grid-flow="importing"] .pf-grid,
.pf-v2[data-grid-flow="exporting"] .pf-grid,
.pf-v2[data-battery-flow="charging"] .pf-solar,
.pf-v2[data-battery-flow="charging"] .pf-battery,
.pf-v2[data-battery-flow="discharging"] .pf-battery,
.pf-v2[data-battery-flow="discharging"] .pf-home{
  box-shadow:
    0 14px 28px rgba(0,0,0,.25),
    0 0 28px var(--pf-node-glow),
    inset 0 1px 0 rgba(255,255,255,.10);
}

.pf-v2 .pf-solar::before,
.pf-v2 .pf-grid::before,
.pf-v2 .pf-home::before{
  opacity:.62;
}

.pf-v2[data-battery-flow="charging"] .pf-solar::before,
.pf-v2[data-battery-flow="charging"] .pf-battery::before,
.pf-v2[data-battery-flow="discharging"] .pf-battery::before,
.pf-v2[data-battery-flow="discharging"] .pf-home::before,
.pf-v2[data-grid-flow="importing"] .pf-grid::before,
.pf-v2[data-grid-flow="exporting"] .pf-grid::before{
  opacity:.88;
}

.pf-v2 .pf-solar span::after,
.pf-v2 .pf-grid span::after,
.pf-v2 .pf-home span::after{
  content:"";
  position:absolute;
  display:block;
  pointer-events:none;
  opacity:.56;
}

.pf-v2 .pf-solar span::after{
  left:50%;
  top:calc(100% + 24px);
  width:4px;
  height:clamp(66px, 15vw, 92px);
  border-radius:999px;
  transform:translateX(-50%);
  background:
    radial-gradient(circle, var(--pf-solar) 0 2px, transparent 3px) 0 0/4px 18px repeat-y;
  filter:drop-shadow(0 0 7px rgba(244,201,109,.58));
  animation:pf-flow-down 1.55s linear infinite;
}

.pf-v2 .pf-grid span::after{
  right:calc(-1 * clamp(82px, 22vw, 126px));
  top:50%;
  width:clamp(82px, 22vw, 126px);
  height:4px;
  transform:translateY(-50%);
  border-radius:999px;
  background:
    radial-gradient(circle, var(--pf-grid) 0 2px, transparent 3px) 0 0/18px 4px repeat-x;
  filter:drop-shadow(0 0 7px rgba(125,196,255,.55));
  animation:pf-flow-right 1.75s linear infinite;
}

.pf-v2 .pf-home span::after{
  left:calc(-1 * clamp(82px, 22vw, 126px));
  top:50%;
  width:clamp(82px, 22vw, 126px);
  height:4px;
  transform:translateY(-50%);
  border-radius:999px;
  background:
    radial-gradient(circle, var(--pf-home) 0 2px, transparent 3px) 0 0/18px 4px repeat-x;
  filter:drop-shadow(0 0 7px rgba(255,204,122,.52));
  animation:pf-flow-right 1.65s linear infinite;
}

.pf-v2[data-battery-flow="idle"] .pf-solar span::after,
.pf-v2[data-grid-flow="idle"] .pf-grid span::after{
  opacity:.18;
  animation-duration:3.8s;
}

.pf-v2[data-battery-flow="idle"] .pf-home span::after{
  opacity:.24;
  animation-duration:3.3s;
}

.pf-v2[data-grid-flow="exporting"] .pf-grid span::after{
  animation-name:pf-flow-left;
}

.pf-v2[data-battery-flow="charging"] .pf-home span::after{
  opacity:.28;
}

.pf-v2[data-battery-flow="discharging"] .pf-solar span::after{
  opacity:.24;
}

.pf-v2[data-battery-flow="discharging"] .pf-home span::after{
  opacity:.82;
}

.pf-v2[data-battery-flow="charging"] .pf-solar span::after{
  opacity:.88;
}

.pf-v2[data-battery-flow="charging"] .pf-battery-shell b{
  height:62%;
}

.pf-v2[data-battery-flow="discharging"] .pf-battery-shell b{
  height:46%;
  background:linear-gradient(180deg, rgba(125,196,255,.95), rgba(105,227,154,.74));
}

@keyframes pf-v2-flow{
  0%,100%{ opacity:.72; }
  50%{ opacity:.86; }
}

@keyframes pf-flow-down{
  from{ background-position:0 -18px; }
  to{ background-position:0 18px; }
}

@keyframes pf-flow-right{
  from{ background-position:-18px 0; }
  to{ background-position:18px 0; }
}

@keyframes pf-flow-left{
  from{ background-position:18px 0; }
  to{ background-position:-18px 0; }
}

@keyframes pf-battery-breathe{
  0%,100%{ filter:saturate(1); opacity:.88; }
  50%{ filter:saturate(1.12); opacity:1; }
}

@media (max-width: 620px){
  .pf-v2{
    height:354px;
    min-height:354px;
    border-radius:var(--radius-lg, 8px);
  }

  .pf-home{ right:3%; }
  .pf-grid{ left:3%; }
  .pf-solar{ top:9%; }

  .pf-caption{
    left:14px;
    top:12px;
    font-size:11px;
  }
}

@media (max-width: 390px){
  .pf-v2{
    height:340px;
    min-height:340px;
  }

  .pf-node{
    width:72px;
    min-height:72px;
  }

  .pf-battery{
    width:106px;
    min-height:166px;
  }

  .pf-node span{
    font-size:11px;
  }

  .pf-node em{
    font-size:10px;
  }
}

@media (prefers-reduced-motion: reduce){
  .pf-v2::after,
  .pf-battery-shell b,
  .pf-v2 .pf-solar span::after,
  .pf-v2 .pf-grid span::after,
  .pf-v2 .pf-home span::after{
    animation:none;
  }
}
"""
