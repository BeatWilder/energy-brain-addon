from __future__ import annotations

from energy_brain.ui.renderer import render_error_page, render_layout
from energy_brain.ui.state.layout_state import select_layout_mode
from energy_brain.web_ui import EnergyBrainWebUIHandler


class CapturingHandler(EnergyBrainWebUIHandler):
    def send_response(self, code: int, message: str | None = None) -> None:
        self.status = code

    def send_header(self, keyword: str, value: str) -> None:
        self.headers_sent[keyword] = value

    def end_headers(self) -> None:
        self.ended = True


def test_layout_selection_query_param():
    assert select_layout_mode("layout=mobile") == "mobile"
    assert select_layout_mode("layout=tablet") == "tablet"
    assert select_layout_mode("layout=desktop") == "desktop"


def test_layout_selection_defaults_to_desktop():
    assert select_layout_mode("") == "desktop"
    assert select_layout_mode("layout=debug") == "desktop"


def test_renderer_invalid_layout_falls_back_to_desktop():
    html = render_layout("debug", {"soc_percent": 68})

    assert 'class="layout-desktop"' in html
    assert "<pre>" not in html
    assert "Powerflow" in html


def test_renderer_error_page_is_simple_html():
    html = render_error_page("boom")

    assert "Energy Brain UI unavailable" in html
    assert "boom" in html


def test_root_redirects_to_new_ui():
    handler = object.__new__(CapturingHandler)
    handler.path = "/"
    handler.headers_sent = {}
    handler.ended = False

    handler.do_GET()

    assert handler.status == 302
    assert handler.headers_sent["Location"] == "/new-ui"
    assert handler.ended is True
