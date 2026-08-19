# VERIFY — site/index.html

Verified by opening `site/index.html` directly as a `file://` URL in an isolated
Chrome profile (`--user-data-dir` pointed at a scratch directory, DevTools open) and,
separately, in Safari, at a desktop viewport (~1440×900).

## What was checked

1. **Console errors** — opened Chrome DevTools → Console on load.
   - First load (with `--auto-open-devtools-for-tabs`) showed one error: *"Unsafe
     attempt to load URL file:///…/index.html from frame with URL
     file:///…/index.html. 'file:' URLs are treated as unique security origins."*
   - Isolated by reloading the page (`Cmd+R`) with DevTools already open and idle:
     the error did **not** recur — console showed "No Issues" / zero entries. This
     confirmed the message was a one-time artifact of Chrome's own
     `--auto-open-devtools-for-tabs` flag racing its `view-source` frame against the
     page load, not a bug in the page's own script. No fix was needed for this;
     documenting it here since it did appear once during verification.
   - Confirmed no actual JS exceptions from the inline module script, the import map,
     or the three.js CDN import (`https://unpkg.com/three@0.160.0/...`) — a broken
     import would throw a visible `Uncaught TypeError`/`Failed to resolve module
     specifier` in the console, and none appeared on the clean reload.

2. **3D element renders** — confirmed visually across multiple screenshots taken
   seconds apart: the central icosahedron core (with its wireframe shell) rotates
   over time, its emissive glow pulses, and the nine orbiting nodes (teal/amber)
   visibly change position and their connection-line opacity flickers between
   screenshots — i.e. the `requestAnimationFrame` loop is live, not a static frame.

3. **Pointer reactivity** — moved the pointer from one corner of the hero to another
   and re-screenshotted: the node group's tilt/rotation visibly shifted toward the
   new pointer position (parallax), confirming the `pointermove` handler is wired up.

4. **Scroll behavior** — scrolled through the full page (hero → what-it-is → how it
   works → benchmarks → install → structure → footer) and confirmed every section
   renders: nav stays sticky with blur, mechanism table, three operating-mode cards,
   benchmark bars (with their `IntersectionObserver`-driven width transition),
   the two efficiency stat cards, the 5-step install list, the repo tree/module
   chips, and the footer links/sources all render without layout breakage at
   desktop width.

5. **Data correctness spot-check** — every benchmark number rendered on the page
   (`benchData` array in the inline script) was diffed by eye against the "Model
   comparison" table in `NOTES.md`; all nine rows match the DeepSeek V4-Flash-0731 →
   `+ J-Space V3.6` values, and the two stat cards match the efficiency table
   (2.53× speed, 2.21× token cost).

## What was fixed

- **Hero text/3D overlap.** The first render (before any fix) placed the 3D group at
  the world origin, directly under the hero headline — the glowing core sphere sat on
  top of "Nine modules loaded only when earned," hurting legibility. Fixed by:
  - Narrowing `h1.hero-title` from `max-width: 820px` to `560px` so the copy stays in
    the left half of the viewport.
  - Adding a `.hero::before` left-to-right dark gradient overlay (z-index between the
    canvas and the text) for extra contrast insurance.
  - Offsetting the three.js `group` to `position.set(2.6, 0, 0)` so the core and its
    orbiting nodes sit visually to the right of the headline instead of underneath it.
  - Re-verified after the fix: headline is now fully legible at desktop width, with
    the 3D piece occupying the right two-thirds of the hero as intended.

No other console errors, broken links, or layout issues were found during this pass.
