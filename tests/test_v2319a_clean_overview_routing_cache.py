from __future__ import annotations

import json
from pathlib import Path

from energy_brain.web_ui import render_dashboard_html
from energy_brain.v2000.read_only_tesla_cockpit import (
    human_next_step_sentence,
    human_step_time_label,
    render_tesla_cockpit_html,
)


def test_querystring_route_parsing_is_used_in_web_ui_source():
    source = Path("energy_brain/web_ui.py").read_text(encoding="utf-8")
    assert "path = self.path.split('?', 1)[0]" in source
    assert 'if path == "/"' in source
    assert 'if path == "/api/tesla-cockpit"' in source
    assert 'if path == "/health"' in source


def test_root_with_query_can_be_interpreted_as_root_path():
    assert "/?cachebust=123".split("?", 1)[0] == "/"
    assert "/?v=024".split("?", 1)[0] == "/"
    assert "/api/tesla-cockpit?cachebust=123".split("?", 1)[0] == "/api/tesla-cockpit"
    assert "/health?cachebust=123".split("?", 1)[0] == "/health"


def test_human_step_time_label_uses_now_for_zero():
    assert human_step_time_label(0) == "nu"
    assert human_step_time_label("0") == "nu"
    assert human_step_time_label(1) == "over ongeveer 1 uur"
    assert human_step_time_label(3) == "over ongeveer 3 uur"


def test_human_next_step_sentence_hold_is_not_awkward():
    sentence = human_next_step_sentence(
        {"plain_planner": {"plan_card_sections": [{"action": "Vasthouden"}]}}
    )
    assert sentence == (
        "Energy Brain kijkt mee. De volgende logische stap is niets veranderen. "
        "Er wordt niets aangestuurd."
    )
    assert "De volgende logische stap is Energy Brain kijkt mee" not in sentence


def test_rendered_html_has_clean_plan_markers_and_no_awkward_sentence():
    html = render_tesla_cockpit_html({})

    assert "Planning in gewone taal" in html
    assert "Vandaag samengevat" in html
    assert "Technische grafiek voor controle" in html
    assert "Niet nodig voor dagelijks gebruik" in html
    assert "De volgende logische stap is Energy Brain kijkt mee" not in html
    assert "over 0 uur" not in html


def test_json_payload_is_raw_parseable_json_not_html_escaped():
    html = render_tesla_cockpit_html({})
    start = html.index('<script id="cockpit-payload"')
    start = html.index(">", start) + 1
    end = html.index("</script>", start)
    raw = html[start:end]

    assert "&quot;" not in raw
    payload = json.loads(raw)
    assert payload["read_only"] is True


def test_legacy_dashboard_renderer_still_returns_html():
    html = render_dashboard_html({})
    assert "<html" in html.lower()
