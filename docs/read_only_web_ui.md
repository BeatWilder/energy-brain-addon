# Energy Brain Read-Only Web UI

The Energy Brain Home Assistant add-on includes a lightweight read-only web UI starting in add-on version `0.1.14`.

The UI is an observer dashboard for the latest Energy Brain cycle. It is intended for inspecting planner output, current telemetry, and controller decision state without exposing any control surface.

## What It Shows

The dashboard at `/` renders a polished dark overview of the latest cycle from:

```text
/data/energy_brain_cycles.jsonl
```

It shows:

- Cycle status and `valid_cycle`.
- Add-on mode, including observer mode.
- Battery state of charge.
- PV power.
- Household load.
- Grid price.
- Controller approval and execute state.
- Execution attempted state.
- Plan cost values: `expected_cost`, `baseline_cost`, and `delta_vs_baseline`.
- SOC trajectory mini-chart.
- Battery setpoint mini-bars.
- The first 24 planner steps in a compact table.
- Reason badges for planner step explanations.

Only the first 24 planner steps are displayed in the compact table. The JSON API remains the source for the summarized latest-cycle payload.

Negative `savings_vs_baseline` or `delta_vs_baseline` can happen during PV charging, export, or other context-dependent planning situations. A negative value does not automatically mean unsafe behavior; it means the selected plan is more expensive than the baseline under the current cost model for that cycle.

## Startup Inside The Add-On

The add-on starts the web UI from `run.sh` before starting the main EMS loop:

```sh
python3 -m energy_brain.web_ui &
exec python3 -m energy_brain.main
```

By default, the UI uses:

```text
ENERGY_BRAIN_UI_HOST=0.0.0.0
ENERGY_BRAIN_UI_PORT=8099
ENERGY_BRAIN_HISTORY_PATH=/data/energy_brain_cycles.jsonl
```

The add-on listens on:

```text
0.0.0.0:8099
```

The add-on port mapping exposes:

```text
8099/tcp
```

## Access

From a browser on the same network as Home Assistant:

```text
http://homeassistant.local:8099/
```

or:

```text
http://<home-assistant-ip>:8099/
```

From inside the Home Assistant host or a shell that can reach the add-on port:

```sh
curl http://localhost:8099/health
curl http://localhost:8099/api/latest-cycle
```

If IPv6 localhost resolution causes a connection reset or refused connection, force IPv4:

```sh
curl -4 http://localhost:8099/health
```

## Endpoints

The UI exposes these read-only GET endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | HTML dashboard |
| `GET` | `/health` | Health check JSON |
| `GET` | `/api/latest-cycle` | Latest summarized cycle JSON |

Health check:

```sh
curl http://localhost:8099/health
```

Expected shape:

```json
{"read_only": true, "status": "ok"}
```

Latest cycle:

```sh
curl http://localhost:8099/api/latest-cycle
```

If `/data/energy_brain_cycles.jsonl` is missing, empty, contains invalid final JSON, or does not contain a valid object, `/api/latest-cycle` returns a safe fallback:

```json
{
  "message": "No valid cycle available",
  "status": "safe",
  "valid_cycle": false
}
```

## Safety Guarantees

The web UI is read-only by design.

It does not:

- Add POST endpoints.
- Call Home Assistant services.
- Perform AlphaESS writes.
- Perform IR heating writes.
- Dispatch commands.
- Execute battery control.
- Bypass the planner or controller.
- Act as a Device Controller.

The UI reads `/data/energy_brain_cycles.jsonl` and renders a summarized view. It does not write Home Assistant state, call services, or change battery/IR devices.

`controller.execute=false` and `execution.attempted=false` are expected in observer mode. They mean the controller did not execute a write action for that cycle.

The UI must not become a control surface without a separate safety design. Any future write-capable feature needs an explicit safety model, review, and tests outside this read-only dashboard.

## Testing

Run the full test suite:

```sh
python3 -m pytest -q
```

Run the dedicated read-only web UI smoke script:

```sh
tools/run_web_ui_readonly_smoke.sh
```

The smoke script runs the UI tests and checks UI-related files for forbidden control/write strings.

Useful manual route checks:

```sh
curl http://localhost:8099/health
curl http://localhost:8099/api/latest-cycle
curl -i http://localhost:8099/
```

Manual read-only method check:

```sh
curl -i -X POST http://localhost:8099/api/latest-cycle
```

Expected result: `405 Method Not Allowed` JSON with `"read_only": true`.

Before merging UI changes, verify protected runtime files were not changed:

```sh
git diff -- energy_brain/planner.py energy_brain/controller.py energy_brain/main.py
```

Expected result: no output for UI-only changes.

## Troubleshooting

If the dashboard does not load:

- Check the add-on version is `0.1.14` or newer.
- Restart the add-on after updating.
- Check add-on logs for:

```text
Energy Brain read-only UI listening
```

- Confirm port `8099` is exposed and reachable.
- Try the health check:

```sh
curl http://localhost:8099/health
```

- If localhost resolves to IPv6 and the request resets or is refused, use:

```sh
curl -4 http://localhost:8099/health
```

If the UI shows `No valid cycle available`:

- Check whether `/data/energy_brain_cycles.jsonl` exists.
- Check that the file is not empty.
- Check that the latest non-empty line is valid JSON.
- Check add-on logs for the main EMS cycle and history write messages.

If the dashboard shows observer mode with `controller.execute=false` and `execution.attempted=false`, that is expected for observer mode and confirms no write action was attempted.
