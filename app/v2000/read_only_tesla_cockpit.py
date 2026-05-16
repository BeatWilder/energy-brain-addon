"""Compatibility wrapper for the V2000 read-only Tesla cockpit.

Runtime add-on code imports from energy_brain.v2000 so the Docker/add-on
package layout remains self-contained. This app.v2000 module is kept only for
research/versioned compatibility and tests that still reference app.v2000.
"""

from energy_brain.v2000.read_only_tesla_cockpit import (  # noqa: F401
    build_read_only_cockpit_payload,
    render_tesla_cockpit_html,
)
