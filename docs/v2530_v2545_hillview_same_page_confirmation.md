# V2530-V2545 Hillview Same-Page Confirmation

This phase changes the Hillview control POST flow.

Before:

- POST returned a separate result page
- user had to navigate back manually

Now:

- POST redirects back to `/hillview`
- `/hillview` shows a same-page confirmation banner
- blocked actions show a same-page blocked message
- successful actions show a same-page processed message

Safety:

- guarded allowlist unchanged
- no planner/controller/main runtime changes
- no broad Home Assistant write surface added
- only Hillview dispatch helper controls remain enabled behind `hillview_controls_enabled`
