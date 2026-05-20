def render_powerflow_v2_css() -> str:
    return """
.pf-v2{
  position:relative;
  width:100%;
  height:clamp(322px, 64vw, 406px);
  min-height:322px;
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
    radial-gradient(circle at 50% 48%, rgba(105,227,154,.105), transparent 23%),
    radial-gradient(circle at 50% 15%, rgba(244,201,109,.085), transparent 22%),
    radial-gradient(circle at 10% 48%, rgba(125,196,255,.075), transparent 24%),
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
  width:clamp(110px, 29vw, 154px);
  height:clamp(174px, 45vw, 224px);
  transform:translate(-50%, -50%);
  border-radius:22px;
  background:
    linear-gradient(180deg, transparent 0 34%, rgba(105,227,154,.15) 34% 100%),
    linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.018)),
    linear-gradient(180deg, rgba(20,32,39,.80), rgba(6,11,15,.92));
  border:1px solid rgba(216,226,236,.20);
  box-shadow:
    0 22px 58px rgba(0,0,0,.38),
    0 0 30px rgba(105,227,154,var(--pf-active-battery)),
    inset 0 1px 0 rgba(255,255,255,.12),
    inset 0 -24px 34px rgba(37,160,95,.18);
}

.pf-v2::after{
  z-index:0;
  inset:0;
  background:
    radial-gradient(circle at 50% 50%, rgba(245,250,255,.46) 0 2px, transparent 3px),
    linear-gradient(180deg, transparent 18%, rgba(244,201,109,.58) 18% 41%, transparent 41%),
    linear-gradient(90deg, transparent 17%, rgba(125,196,255,.42) 17% 41%, transparent 41%),
    linear-gradient(90deg, transparent 59%, rgba(255,204,122,.46) 59% 83%, transparent 83%),
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
  opacity:.64;
}

.pf-caption{
  position:absolute;
  z-index:3;
  left:clamp(16px, 5vw, 24px);
  top:11px;
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
  width:clamp(78px, 20vw, 102px);
  min-height:clamp(78px, 20vw, 102px);
  height:auto;
  aspect-ratio:1;
  border-radius:999px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:4px;
  background:
    radial-gradient(circle at 50% 16%, rgba(255,255,255,.10), transparent 35%),
    linear-gradient(180deg, rgba(19,27,35,.86), rgba(8,13,18,.94));
  border:1px solid rgba(255,255,255,.13);
  color:var(--pf-text);
  box-shadow:
    0 13px 26px rgba(0,0,0,.28),
    0 0 18px var(--pf-node-glow),
    inset 0 1px 0 rgba(255,255,255,.09);
  backdrop-filter:blur(16px) saturate(1.05);
  -webkit-backdrop-filter:blur(16px) saturate(1.05);
}

.pf-node::before{
  content:"";
  position:absolute;
  inset:-2px;
  border-radius:inherit;
  border:1px solid var(--pf-node-line);
  box-shadow:0 0 12px var(--pf-node-glow);
  opacity:.70;
}

.pf-node::after{
  content:"";
  position:absolute;
  width:6px;
  height:6px;
  left:50%;
  top:14px;
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
  font-size:clamp(11px, 2.35vw, 13px);
  line-height:1.05;
  font-weight:690;
  letter-spacing:0;
  text-align:center;
  text-shadow:0 1px 8px rgba(0,0,0,.32);
}

.pf-node em{
  position:relative;
  z-index:1;
  color:var(--pf-node-color);
  font-size:clamp(11px, 2.45vw, 13px);
  line-height:1.08;
  font-style:normal;
  font-weight:720;
  text-align:center;
  opacity:.94;
}

.pf-solar{
  left:50%;
  top:8.5%;
  transform:translateX(-50%);
  --pf-node-color:var(--pf-solar);
  --pf-node-line:rgba(244,201,109,.38);
  --pf-node-glow:rgba(244,201,109,.18);
}

.pf-home{
  right:4%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-home);
  --pf-node-line:rgba(255,204,122,.32);
  --pf-node-glow:rgba(255,204,122,.14);
}

.pf-grid{
  left:4%;
  top:50%;
  transform:translateY(-50%);
  --pf-node-color:var(--pf-grid);
  --pf-node-line:rgba(125,196,255,.35);
  --pf-node-glow:rgba(125,196,255,.16);
}

.pf-battery{
  left:50%;
  top:50%;
  width:clamp(128px, 34vw, 164px);
  min-height:clamp(188px, 48vw, 236px);
  aspect-ratio:auto;
  padding:clamp(17px, 4vw, 23px) 11px 13px;
  border-radius:25px;
  transform:translate(-50%, -50%);
  --pf-node-color:var(--pf-battery);
  --pf-node-line:rgba(105,227,154,.38);
  --pf-node-glow:rgba(105,227,154,.22);
}

.pf-battery::after{
  display:none;
}

.pf-battery span{
  margin-top:3px;
  color:rgba(245,248,251,.88);
  font-size:clamp(11px, 2.3vw, 13px);
  font-weight:650;
}

.pf-battery em{
  color:rgba(105,227,154,.98);
  font-size:clamp(11px, 2.45vw, 13px);
  font-weight:730;
}

.pf-battery strong{
  position:relative;
  z-index:1;
  display:block;
  margin-top:7px;
  color:rgba(135,245,169,.98);
  font-size:clamp(30px, 8vw, 42px);
  line-height:.92;
  font-weight:760;
  letter-spacing:0;
  text-shadow:
    0 0 18px rgba(105,227,154,.28),
    0 1px 10px rgba(0,0,0,.42);
}

.pf-battery-shell{
  position:relative;
  z-index:1;
  display:block;
  width:clamp(56px, 15vw, 74px);
  height:clamp(98px, 25vw, 132px);
  border-radius:14px;
  border:1px solid rgba(216,226,236,.30);
  background:
    linear-gradient(90deg, rgba(255,255,255,.10), transparent 22%, rgba(255,255,255,.035) 60%, rgba(255,255,255,.09)),
    linear-gradient(180deg, rgba(255,255,255,.12), transparent 20%),
    linear-gradient(180deg, rgba(13,24,29,.72), rgba(5,10,13,.78));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.14),
    inset 0 -18px 30px rgba(10,22,18,.58),
    inset 10px 0 18px rgba(255,255,255,.035),
    0 0 24px rgba(105,227,154,.15);
  overflow:hidden;
}

.pf-battery-shell::before{
  content:"";
  position:absolute;
  left:34%;
  right:34%;
  top:-1px;
  height:7px;
  border-radius:0 0 3px 3px;
  background:rgba(216,226,236,.24);
}

.pf-battery-shell::after{
  content:"";
  position:absolute;
  left:10px;
  top:17px;
  width:15px;
  height:3px;
  border-radius:999px;
  background:rgba(255,255,255,.12);
  box-shadow:
    0 9px 0 rgba(255,255,255,.075),
    0 18px 0 rgba(255,255,255,.045);
}

.pf-battery-shell b{
  position:absolute;
  left:8px;
  right:8px;
  bottom:8px;
  height:56%;
  border-radius:10px;
  background:
    linear-gradient(180deg, rgba(170,255,195,.98), rgba(67,218,125,.86) 45%, rgba(29,137,78,.78)),
    linear-gradient(90deg, rgba(255,255,255,.18), transparent 45%, rgba(255,255,255,.06));
  box-shadow:
    0 0 22px rgba(105,227,154,.28),
    inset 0 1px 0 rgba(255,255,255,.23);
  animation:pf-battery-breathe 4.8s ease-in-out infinite;
}

.pf-battery-shell b::after{
  content:"";
  position:absolute;
  left:0;
  right:0;
  top:0;
  height:42%;
  border-radius:inherit;
  background:linear-gradient(180deg, rgba(255,255,255,.20), transparent);
  opacity:.75;
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
  opacity:.74;
}

.pf-v2[data-grid-flow="importing"] .pf-grid,
.pf-v2[data-grid-flow="exporting"] .pf-grid,
.pf-v2[data-battery-flow="charging"] .pf-solar,
.pf-v2[data-battery-flow="charging"] .pf-battery,
.pf-v2[data-battery-flow="discharging"] .pf-battery,
.pf-v2[data-battery-flow="discharging"] .pf-home{
  box-shadow:
    0 14px 28px rgba(0,0,0,.28),
    0 0 23px var(--pf-node-glow),
    inset 0 1px 0 rgba(255,255,255,.10);
}

.pf-v2 .pf-solar::before,
.pf-v2 .pf-grid::before,
.pf-v2 .pf-home::before{
  opacity:.54;
}

.pf-v2[data-battery-flow="charging"] .pf-solar::before,
.pf-v2[data-battery-flow="charging"] .pf-battery::before,
.pf-v2[data-battery-flow="discharging"] .pf-battery::before,
.pf-v2[data-battery-flow="discharging"] .pf-home::before,
.pf-v2[data-grid-flow="importing"] .pf-grid::before,
.pf-v2[data-grid-flow="exporting"] .pf-grid::before{
  opacity:.84;
}

.pf-v2 .pf-solar span::after,
.pf-v2 .pf-grid span::after,
.pf-v2 .pf-home span::after{
  content:"";
  position:absolute;
  display:block;
  pointer-events:none;
  opacity:.46;
}

.pf-v2 .pf-solar span::after{
  left:50%;
  top:calc(100% + 17px);
  width:3px;
  height:clamp(50px, 12vw, 72px);
  border-radius:999px;
  transform:translateX(-50%);
  background:
    radial-gradient(circle, var(--pf-solar) 0 1.5px, transparent 2.4px) 0 0/3px 16px repeat-y;
  filter:drop-shadow(0 0 5px rgba(244,201,109,.46));
  animation:pf-flow-down 1.9s linear infinite;
}

.pf-v2 .pf-grid span::after{
  right:calc(-1 * clamp(62px, 17vw, 94px));
  top:50%;
  width:clamp(62px, 17vw, 94px);
  height:3px;
  transform:translateY(-50%);
  border-radius:999px;
  background:
    radial-gradient(circle, var(--pf-grid) 0 1.5px, transparent 2.4px) 0 0/16px 3px repeat-x;
  filter:drop-shadow(0 0 5px rgba(125,196,255,.44));
  animation:pf-flow-right 2.05s linear infinite;
}

.pf-v2 .pf-home span::after{
  left:calc(-1 * clamp(62px, 17vw, 94px));
  top:50%;
  width:clamp(62px, 17vw, 94px);
  height:3px;
  transform:translateY(-50%);
  border-radius:999px;
  background:
    radial-gradient(circle, var(--pf-home) 0 1.5px, transparent 2.4px) 0 0/16px 3px repeat-x;
  filter:drop-shadow(0 0 5px rgba(255,204,122,.42));
  animation:pf-flow-right 1.95s linear infinite;
}

.pf-v2[data-battery-flow="idle"] .pf-solar span::after,
.pf-v2[data-grid-flow="idle"] .pf-grid span::after{
  opacity:.14;
  animation-duration:4.2s;
}

.pf-v2[data-battery-flow="idle"] .pf-home span::after{
  opacity:.18;
  animation-duration:3.8s;
}

.pf-v2[data-grid-flow="exporting"] .pf-grid span::after{
  animation-name:pf-flow-left;
}

.pf-v2[data-battery-flow="charging"] .pf-home span::after{
  opacity:.22;
}

.pf-v2[data-battery-flow="discharging"] .pf-solar span::after{
  opacity:.18;
}

.pf-v2[data-battery-flow="discharging"] .pf-home span::after{
  opacity:.76;
}

.pf-v2[data-battery-flow="charging"] .pf-solar span::after{
  opacity:.78;
}

.pf-v2[data-battery-flow="charging"] .pf-battery-shell b{
  height:63%;
}

.pf-v2[data-battery-flow="discharging"] .pf-battery-shell b{
  height:47%;
  background:
    linear-gradient(180deg, rgba(125,196,255,.95), rgba(105,227,154,.80) 48%, rgba(38,142,94,.78)),
    linear-gradient(90deg, rgba(255,255,255,.16), transparent 45%, rgba(255,255,255,.05));
}

@keyframes pf-v2-flow{
  0%,100%{ opacity:.72; }
  50%{ opacity:.86; }
}

@keyframes pf-flow-down{
  from{ background-position:0 -16px; }
  to{ background-position:0 16px; }
}

@keyframes pf-flow-right{
  from{ background-position:-16px 0; }
  to{ background-position:16px 0; }
}

@keyframes pf-flow-left{
  from{ background-position:16px 0; }
  to{ background-position:-16px 0; }
}

@keyframes pf-battery-breathe{
  0%,100%{ filter:saturate(1); opacity:.88; }
  50%{ filter:saturate(1.12); opacity:1; }
}

@media (max-width: 620px){
  .pf-v2{
    height:336px;
    min-height:336px;
    border-radius:var(--radius-lg, 8px);
  }

  .pf-home{ right:3%; }
  .pf-grid{ left:3%; }
  .pf-solar{ top:8%; }

  .pf-caption{
    left:14px;
    top:12px;
    font-size:11px;
  }
}

@media (max-width: 390px){
  .pf-v2{
    height:326px;
    min-height:326px;
  }

  .pf-node{
    width:74px;
    min-height:74px;
  }

  .pf-battery{
    width:118px;
    min-height:178px;
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
