from __future__ import annotations

from io import BytesIO

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


def _handler_for_path(path: str) -> CapturingHandler:
    handler = object.__new__(CapturingHandler)
    handler.path = path
    handler.headers_sent = {}
    handler.ended = False
    handler.wfile = BytesIO()
    return handler


def test_ingress_path_normalization_handles_sidebar_variants():
    handler = object.__new__(CapturingHandler)

    cases = {
        "/": "/",
        "/new-ui": "/new-ui",
        "/new-ui/": "/new-ui",
        "/api/hassio_ingress/testtoken": "/",
        "/api/hassio_ingress/testtoken/": "/",
        "/api/hassio_ingress/testtoken/new-ui": "/new-ui",
        "/api/hassio_ingress/testtoken/new-ui/": "/new-ui",
        "/api/hassio_ingress/testtoken//new-ui//": "/new-ui",
        "/some/prefix/api/hassio_ingress/testtoken/new-ui": "/new-ui",
        "http://homeassistant.local/api/hassio_ingress/testtoken/new-ui": "/new-ui",
        "/api/hassio_ingress/testtoken/legacy-ui": "/legacy-ui",
    }

    for raw_path, normalized_path in cases.items():
        assert handler._normalize_ingress_path(raw_path) == normalized_path


def test_ingress_root_serves_new_ui_without_redirect():
    handler = _handler_for_path("/")

    handler.do_GET()

    assert handler.status == 200
    assert "Location" not in handler.headers_sent
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert handler.ended is True
    assert b"Energy Brain" in handler.wfile.getvalue()


def test_literal_hassio_ingress_root_serves_new_ui_without_redirect():
    handler = _handler_for_path("/api/hassio_ingress/testtoken/")

    handler.do_GET()

    assert handler.status == 200
    assert "Location" not in handler.headers_sent
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert b"Energy Brain" in handler.wfile.getvalue()


def test_literal_hassio_ingress_root_without_trailing_slash_serves_new_ui_without_redirect():
    handler = _handler_for_path("/api/hassio_ingress/testtoken")

    handler.do_GET()

    assert handler.status == 200
    assert "Location" not in handler.headers_sent
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert b"Energy Brain" in handler.wfile.getvalue()


def test_new_ui_route_still_serves_new_ui():
    handler = _handler_for_path("/new-ui?layout=mobile")

    handler.do_GET()

    assert handler.status == 200
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert b"layout-mobile" in handler.wfile.getvalue()


def test_literal_hassio_ingress_new_ui_route_still_serves_new_ui():
    handler = _handler_for_path("/api/hassio_ingress/testtoken/new-ui?layout=mobile")

    handler.do_GET()

    assert handler.status == 200
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert b"layout-mobile" in handler.wfile.getvalue()


def test_ingress_prefixed_new_ui_variant_still_serves_new_ui():
    handler = _handler_for_path("/supervisor/api/hassio_ingress/testtoken/new-ui/?layout=mobile")

    handler.do_GET()

    assert handler.status == 200
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert b"layout-mobile" in handler.wfile.getvalue()


def test_legacy_ui_route_still_serves_legacy_dashboard():
    handler = _handler_for_path("/legacy-ui")

    handler.do_GET()

    assert handler.status == 200
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert b"SOC trajectory mini-chart" in handler.wfile.getvalue()
    assert b"layout-desktop" not in handler.wfile.getvalue()


def test_literal_hassio_ingress_legacy_ui_route_still_serves_legacy_dashboard():
    handler = _handler_for_path("/api/hassio_ingress/testtoken/legacy-ui")

    handler.do_GET()

    assert handler.status == 200
    assert handler.headers_sent["Content-Type"] == "text/html; charset=utf-8"
    assert b"SOC trajectory mini-chart" in handler.wfile.getvalue()
    assert b"layout-desktop" not in handler.wfile.getvalue()
