from __future__ import annotations


def render_layout(layout_mode: str, payload: dict) -> str:
    return """
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Energy Brain TEST</title>

<style>
body{
  margin:0;
  background:black;
  color:white;
  font-family:Arial,sans-serif;
}

.test{
  height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:64px;
  font-weight:900;
  background:red;
}
</style>

</head>

<body>

<div class="test">
ENERGY BRAIN LIVE UI
</div>

</body>
</html>
"""


def render_error_page(message: str = "error") -> str:
    return f"""
<html>
<body style="background:black;color:white">
<h1>{message}</h1>
</body>
</html>
"""
