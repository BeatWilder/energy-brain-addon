def render_powerflow_v2_css() -> str:
    return """
.pf-v2{
  position:relative;
  width:100%;
  height:420px;
  border-radius:28px;
}

.pf-node{
  position:absolute;
  width:92px;
  height:92px;
  border-radius:999px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  background:rgba(18,22,30,0.92);
  border:1px solid rgba(255,255,255,0.08);
  color:white;
}

.pf-solar{
  left:50%;
  top:8%;
  transform:translateX(-50%);
}

.pf-home{
  right:8%;
  top:50%;
  transform:translateY(-50%);
}

.pf-grid{
  left:8%;
  top:50%;
  transform:translateY(-50%);
}

.pf-battery{
  left:50%;
  bottom:8%;
  transform:translateX(-50%);
}
"""
