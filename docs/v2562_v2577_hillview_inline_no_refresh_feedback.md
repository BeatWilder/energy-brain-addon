# V2562-V2577 Hillview Inline No-Refresh Feedback

This phase changes Hillview dispatch controls from full-page form submit to inline JavaScript feedback.

Before:

- clicking save/on/off caused a page navigation or redirect
- Home Assistant ingress could scroll back to the top

Now:

- the form uses `fetch()` with `event.preventDefault()`
- confirmation appears inline above the dispatch form
- the page does not reload
- scroll position remains unchanged

Safety:

- guarded allowlist unchanged
- only Hillview dispatch helpers can be written
- no planner/controller/main runtime changes
- normal HTML form POST fallback still exists if JavaScript is unavailable
