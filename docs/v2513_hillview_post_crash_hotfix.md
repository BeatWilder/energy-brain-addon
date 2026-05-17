# V2513 Hillview POST Crash Hotfix

Fixes a crash in the Hillview control POST result page.

Cause:

- the POST handler used a local variable named `html`
- this shadowed the imported Python `html` module
- `html.escape(...)` then failed while rendering the result page
- Safari showed a broken network connection

Fix:

- rename the local page variable
- compute escaped JSON before composing the page
- keep guarded control allowlist unchanged

Safety:

- no planner changes
- no controller changes
- no main runtime changes
- no broad write surface added
- only the existing guarded Hillview control endpoint remains
