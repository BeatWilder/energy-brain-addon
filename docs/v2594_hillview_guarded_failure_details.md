# V2594 Hillview Guarded Failure Details

This hotfix improves failed Hillview guarded control feedback.

Before:

- The UI could show only a generic blocked message.
- The exact failing service/entity/value was not visible.

Now:

- Failed guarded writes carry domain, service, entity_id, payload and value/option context.
- Inline feedback can show the exact failed guard context.
- Planner/controller/main remain untouched.

Safety:

- No new Home Assistant control surface is added.
- Existing allowlist remains unchanged.
- The change only improves diagnostics and user feedback.
