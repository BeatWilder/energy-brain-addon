# V2546-V2561 Hillview Stay-On-Control Anchor

This phase improves the Hillview / AlphaESS control UX.

Before:

- POST redirected back to `/hillview`
- browser returned to the top of the page

Now:

- the dispatch control card has a stable anchor
- POST redirects to `/hillview?...#hillview-dispatch-control`
- after save/on/off, the browser returns to the dispatch control card

Safety:

- guarded allowlist unchanged
- no new Home Assistant write surface
- no planner/controller/main runtime changes
