from __future__ import annotations


DESIGN_TOKENS = {
    "spacing": {
        "xs": "6px",
        "sm": "10px",
        "md": "16px",
        "lg": "24px",
        "xl": "34px",
    },
    "radius": {
        "sm": "6px",
        "md": "8px",
        "lg": "8px",
        "round": "999px",
    },
    "typography": {
        "family": 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        "letter_spacing": "0",
    },
    "glow": {
        "solar": "rgba(255, 209, 102, 0.42)",
        "home": "rgba(88, 232, 182, 0.34)",
        "battery": "rgba(101, 240, 167, 0.42)",
        "grid": "rgba(127, 199, 255, 0.42)",
        "danger": "rgba(255, 104, 124, 0.34)",
    },
    "motion": {
        "fast": "160ms",
        "base": "320ms",
        "slow": "1200ms",
        "flow": "2600ms",
    },
    "elevation": {
        "panel": "0 22px 70px rgba(0, 0, 0, 0.38)",
        "hero": "0 30px 110px rgba(0, 0, 0, 0.45)",
    },
}


def css_vars() -> str:
    return """
      --space-xs: 6px;
      --space-sm: 10px;
      --space-md: 16px;
      --space-lg: 24px;
      --space-xl: 34px;
      --radius-sm: 6px;
      --radius-md: 8px;
      --radius-lg: 8px;
      --radius-round: 999px;
      --font-ui: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --motion-fast: 160ms;
      --motion-base: 320ms;
      --motion-slow: 1200ms;
      --motion-flow: 2600ms;
      --shadow-panel: 0 22px 70px rgba(0, 0, 0, 0.38);
      --shadow-hero: 0 30px 110px rgba(0, 0, 0, 0.45);
    """
