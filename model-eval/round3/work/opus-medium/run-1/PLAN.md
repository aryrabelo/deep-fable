# PLAN — J-Space Cognition Suite V3.6 landing page

## Section list (top to bottom)

1. **Nav** — sticky, minimal: logo mark + wordmark, links to How it works / Benchmarks /
   Install, GitHub star count, "View on GitHub" button.
2. **Hero** — full-viewport. Real-time 3D piece as background/centerpiece, headline,
   one-line description, version + license + star badges, two CTAs (View on GitHub,
   Read the README).
3. **What it is** — short explainer paragraph pulled from NOTES.md ("What it is"),
   plus the four-part structure (entry / modules / references / controller) as a
   4-card row, and the design-principle quote ("Dense on the inside...").
4. **How it works** — the three operating modes (`fast` / `full` / `loop`) as a
   3-column comparison, plus the seven core mechanisms as a compact grid/table.
5. **Benchmarks** — the real model-comparison table (HLE, Terminal Bench, NL2Repo,
   CyberGym, DeepSWE, Toolathlon-Verified, Agents' Last Exam, AutomationBench) rendered
   as horizontal bar rows for DeepSeek V4-Flash-0731 vs. +J-Space, with the full
   comparator row values on hover/secondary text; plus the two efficiency numbers
   (2.53× speed, 2.21× token cost) as large stat callouts. Footnote on evaluation
   context + link to the capability-realization report.
6. **Install / usage** — the 5-step manual install sequence, the verify commands, and
   the three invocation forms (`/j-space`, `$j-space`, direct request). Rendered as a
   terminal-style code block sequence.
7. **Structure** — collapsed file tree of the repo (from NOTES.md), nine modules and
   three references listed as tags/chips.
8. **Footer** — license (Apache-2.0), DOI, repo stats, links to: GitHub repo, companion
   capability report, Zenodo record, README (zh-CN). Small "Sources" note pointing at
   which facts came from which fetched page.

## 3D concept

**Concept: "Global Workspace Stage."** J-Space's own operating metaphor is a managed
cognitive workspace with a broadcast hub and selectively-loaded modules — literally a
small stage where only one or two things are lit and "broadcast" at a time, while the
rest waits in the dark. The hero 3D piece renders this directly instead of an abstract
generic "AI orb":

- A central glowing icosahedron **core** = the broadcast hub / workspace.
- **Nine small nodes** orbiting the core at slightly different radii/speeds = the nine
  modules, each selectively loaded.
- Thin animated **connection lines** from the core to each node, pulsing at staggered
  intervals = broadcast events (only a couple lit brighter at any moment, echoing
  "selective loading" rather than "everything active at once").
- Slow autonomous rotation (time-driven) plus **pointer parallax** (camera/group tilts
  toward the cursor) and a **scroll-linked** camera pull-back into the next section, so
  the piece reacts on all three channels the brief allows (pointer, scroll, time).
- Particle starfield background, dark navy/near-black, kept sparse so it reads as
  premium, not decorative noise.

This is a literal, on-theme visual rather than a stock "neural network sphere" — it
maps 1:1 onto the entry → modules → broadcast structure documented in NOTES.md, so it
is defensible as "why it fits," not just aesthetically dark-and-3D.

Implementation: three.js r1xx via CDN (`unpkg`/`jsdelivr` ESM build), one `<canvas>`,
~250 lines of inline module script in `index.html` plus optionally `site/assets/scene.js`.
No external model/texture files — everything is procedural geometry (`IcosahedronGeometry`,
`SphereGeometry` for nodes, `BufferGeometry` lines, `Points` for the starfield) so there
are zero placeholder assets.

## Color & typography system

**Palette** (dark, premium, single accent):
- Background: `#05070c` → `#0b0f1a` (subtle vertical gradient)
- Surface / cards: `#0f1420` with 1px `#1c2436` border
- Primary text: `#e8ecf5`
- Secondary text: `#8b93a7`
- Accent (the "broadcast" color, used for the 3D core glow, links, stat numbers,
  active states): `#5eead4` (teal) with a secondary warm accent `#f5a962` (amber) used
  sparingly for the "+J-Space" delta values in benchmark rows, so improvement reads as
  "lit up" against the muted baseline.
- Borders/dividers: `#1c2436`

**Typography**: system-font stack for body copy (`-apple-system, "Segoe UI", Inter,
sans-serif` fallback chain — no external font request required, but layer in
"Space Grotesk" + "IBM Plex Mono" from Google Fonts CDN for headings/numbers/code to get
a distinct technical-editorial voice without inventing a custom font).
- Display/headings: **Space Grotesk**, tight tracking, 600–700 weight.
- Body: system sans stack, 400/500, 1.6 line-height.
- Numbers/stats/code/version strings: **IBM Plex Mono**, tabular figures, used for every
  benchmark score, version string, and install command so factual data is visually
  distinct from prose.

## Facts → sections mapping (from NOTES.md)

- **Hero**: repo name/version (V3.6), one-line description, Apache-2.0 badge, DOI badge,
  star count (2,547).
- **What it is**: "model-agnostic inference-time control system..." paragraph; entry /
  9 modules / 3 references / optional controller structure; design-principle quote.
- **How it works**: `fast`/`full`/`loop` table; seven core-mechanisms table.
- **Benchmarks**: full model-comparison table + efficiency table (2.53×, 2.21×) +
  evaluation-context footnote (DeepSeek Harness minimal mode, `max` effort,
  `temperature=1.0`, `top_p=0.95`) + link to capability-realization report.
- **Install/usage**: 5-step manual install, verify_suite.py / unittest commands, three
  invocation forms, entry-gate auto-selection note.
- **Structure**: repo file tree, module filenames, reference filenames.
- **Footer**: license text, DOI (10.5281/zenodo.21977271), links to all four fetched
  sources, Zenodo publish date (Aug 17, 2026) and release history string
  (V1 → ... → V3.6).
