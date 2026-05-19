from __future__ import annotations

from energy_brain.ui.viewport.viewport_breakpoints import BREAKPOINTS


def render_viewport_runtime() -> str:
    bp = BREAKPOINTS
    return f"""
(() => {{
  const key = "energy-brain.layout";
  const allowed = new Set(["auto", "mobile", "tablet", "desktop"]);
  const mobileMax = {bp.mobile_max};
  const tabletMax = {bp.tablet_max};
  const params = new URLSearchParams(window.location.search);
  const query = params.get("layout");
  if (allowed.has(query)) localStorage.setItem(key, query);

  function preference() {{
    const stored = localStorage.getItem(key);
    const declared = document.body.dataset.layoutPreference || "auto";
    return allowed.has(query) ? query : (allowed.has(stored) ? stored : declared);
  }}

  function modeForWidth() {{
    const width = window.innerWidth || document.documentElement.clientWidth || 0;
    if (width > tabletMax) return "desktop";
    if (width > mobileMax) return "tablet";
    return "mobile";
  }}

  function applyViewport() {{
    const pref = preference();
    const mode = pref === "auto" ? modeForWidth() : pref;
    document.body.dataset.layoutPreference = pref;
    document.body.dataset.viewport = mode;
    document.body.dataset.viewportDensity = mode === "desktop" ? "command" : (mode === "tablet" ? "operational" : "native");
    document.body.classList.remove("layout-auto", "layout-mobile", "layout-tablet", "layout-desktop");
    document.body.classList.add(`layout-${{mode}}`);
    document.querySelectorAll("[data-layout-option]").forEach((item) => {{
      item.classList.toggle("active", item.dataset.layoutOption === pref);
    }});
  }}

  applyViewport();
  window.addEventListener("resize", applyViewport, {{passive: true}});
}})();
"""
