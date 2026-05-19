from __future__ import annotations


def render_powerflow_v2_styles() -> str:
    return """
.ebpfv2-root{
  position:relative;
  width:100%;
  height:420px;

  margin:0 auto 18px auto;

  border-radius:34px;
  overflow:hidden;

  background:
    radial-gradient(circle at center,
      rgba(70,140,255,0.16),
      rgba(0,0,0,0) 58%
    ),
    linear-gradient(
      180deg,
      rgba(10,14,20,0.98),
      rgba(4,6,10,1)
    );

  border:1px solid rgba(255,255,255,0.06);

  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.04),
    0 30px 60px rgba(0,0,0,0.35);
}

.ebpfv2-center{
  position:absolute;

  left:50%;
  top:50%;

  width:18px;
  height:18px;

  border-radius:999px;

  transform:translate(-50%,-50%);

  background:white;

  box-shadow:
    0 0 12px rgba(255,255,255,1),
    0 0 40px rgba(90,170,255,0.65);
}

.ebpfv2-line{
  position:absolute;
  background:rgba(255,255,255,0.92);
  box-shadow:0 0 14px rgba(120,190,255,0.7);
}

.ebpfv2-line-top{
  left:50%;
  top:108px;

  width:3px;
  height:84px;

  transform:translateX(-50%);
}

.ebpfv2-line-bottom{
  left:50%;
  bottom:108px;

  width:3px;
  height:84px;

  transform:translateX(-50%);
}

.ebpfv2-line-left{
  left:108px;
  top:50%;

  width:104px;
  height:3px;

  transform:translateY(-50%);
}

.ebpfv2-line-right{
  right:108px;
  top:50%;

  width:104px;
  height:3px;

  transform:translateY(-50%);
}

.ebpfv2-node{
  position:absolute;

  width:104px;
  height:104px;

  border-radius:999px;

  display:flex;
  align-items:center;
  justify-content:center;

  color:white;

  font-size:22px;
  font-weight:700;

  border:1px solid rgba(255,255,255,0.08);

  backdrop-filter:blur(20px);

  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.06),
    0 20px 40px rgba(0,0,0,0.38);
}

.ebpfv2-solar{
  left:50%;
  top:28px;

  transform:translateX(-50%);

  background:
    linear-gradient(
      180deg,
      rgba(255,220,120,1),
      rgba(255,170,40,0.82)
    );
}

.ebpfv2-home{
  right:28px;
  top:50%;

  transform:translateY(-50%);

  background:
    linear-gradient(
      180deg,
      rgba(90,240,220,0.96),
      rgba(0,150,130,0.78)
    );
}

.ebpfv2-grid{
  left:28px;
  top:50%;

  transform:translateY(-50%);

  background:
    linear-gradient(
      180deg,
      rgba(120,190,255,0.96),
      rgba(60,110,255,0.78)
    );
}

.ebpfv2-battery{
  left:50%;
  bottom:28px;

  transform:translateX(-50%);

  background:
    linear-gradient(
      180deg,
      rgba(120,255,180,0.98),
      rgba(20,170,90,0.82)
    );
}

@media (max-width:700px){

  .ebpfv2-root{
    height:360px;
  }

  .ebpfv2-node{
    width:86px;
    height:86px;
    font-size:19px;
  }

  .ebpfv2-line-top{
    top:92px;
    height:66px;
  }

  .ebpfv2-line-bottom{
    bottom:92px;
    height:66px;
  }

  .ebpfv2-line-left{
    left:92px;
    width:72px;
  }

  .ebpfv2-line-right{
    right:92px;
    width:72px;
  }
}
"""
