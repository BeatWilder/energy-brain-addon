from __future__ import annotations

from energy_brain.v2000.read_only_tesla_cockpit import (
    build_read_only_cockpit_payload,
    forecast_layperson_summary,
    render_tesla_cockpit_html,
)


def test_forecast_layperson_summary_turns_tables_into_plain_cards():
    payload = build_read_only_cockpit_payload(
        {
            "snapshot": {
                "grid_price": 0.2475,
                "pv_power_kw": 3.462,
                "household_load_kw": 2.957,
                "battery_soc": 87.2,
            },
            "valid_cycle": True,
        }
    )

    summary = forecast_layperson_summary(payload)

    assert "meaning" in summary
    titles = {card["title"] for card in summary["cards"]}
    assert titles == {"Stroomprijs", "Zon", "Huisverbruik", "Batterijplan"}
    assert any(card["value"] in {"Veel zon", "Redelijke zon", "Weinig zon"} for card in summary["cards"])
    battery_cards = [card for card in summary["cards"] if card["title"] == "Batterijplan"]
    assert len(battery_cards) == 1
    assert battery_cards[0]["value"] in {
        "Batterij laden met zon",
        "Bijna vol, laden begrenzen",
        "Vasthouden bij bijna vol",
        "Alleen observeren",
    }
    assert battery_cards[0]["detail"]


def test_forecast_tab_opens_with_plain_language_not_raw_tables():
    html = render_tesla_cockpit_html(
        {
            "snapshot": {
                "grid_price": 0.2475,
                "pv_power_kw": 3.462,
                "household_load_kw": 2.957,
                "battery_soc": 87.2,
            },
            "valid_cycle": True,
        }
    )

    assert "Komende uren samengevat" in html
    assert "Forecast in gewone taal" in html
    assert "Stroomprijs" in html
    assert "Huisverbruik" in html
    assert "Batterijplan" in html
    assert "Technische details tonen" in html


def test_forecast_raw_tables_are_still_available_inside_technical_details():
    html = render_tesla_cockpit_html(
        {
            "snapshot": {
                "grid_price": 0.2475,
                "pv_power_kw": 3.462,
                "household_load_kw": 2.957,
                "battery_soc": 87.2,
            },
            "valid_cycle": True,
        }
    )

    assert "<details>" in html
    assert "Price Forecast Panel" in html
    assert "PV Forecast Panel" in html
    assert "Load Forecast Panel" in html
    assert "Latest Cycle Table" in html
    assert "forecast-card-human" in html
