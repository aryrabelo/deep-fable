# PLAN — J-Space Cognition Suite V3.6 landing page

## Section list

1. **Hero** — project name, one-line pitch, the 3D element, primary CTAs (GitHub / Zenodo).
2. **How it works** — the three operating passes (`fast` / `full` / `loop`) and the seven
   core mechanisms, presented as a compact operating-model diagram in prose/cards form.
3. **Benchmark highlights** — the model-comparison table (DeepSeek V4-Flash-0731 vs. +
   J-Space V3.6, against GLM-5.3 / Kimi-K3 / Opus-4.8 / Fable 5) plus the efficiency numbers
   (2.53× speed, 2.21× lower token cost).
4. **Install / usage** — Option A (manual install steps + verify command) and the invocation
   pattern (`/j-space`, `$j-space`, direct request), condensed to a scannable numbered list
   and one code block.
5. **Structure** — brief repo-tree callout (entry, 9 modules, 3 references, optional
   controller) so visitors understand what they're installing.
6. **Footer** — license (Apache-2.0), links (GitHub repo, companion capability report,
   Zenodo DOI record), release-history strip (V1 → V3.6), author handle.

## 3D concept and why it fits

**Concept: a "broadcast hub" particle core.** A small luminous nucleus at the center of the
hero with a sparse shell of points/nodes orbiting it, connected by thin dynamically-drawn
lines to a handful of the nearest points — like a live workspace broadcasting shared state to
active branches. On pointer move the nucleus subtly leans toward the cursor (a "directed
focus" cue); the node shell continues a slow independent rotation over time so the scene
always reads as alive, not just reactive.

This maps directly onto vocabulary already in NOTES.md, so nothing is invented for
decoration:
- The **nucleus** = the "broadcast hub" mechanism (one shared source other branches read from).
- The **orbiting nodes** = the nine selectively-loaded modules — only a few are "lit"/close to
  the hub at once, echoing "keeps one or two load-bearing ideas active and externalizes the
  rest."
- The **connecting lines that redraw** = bridge-before-conclusion reasoning / broadcast
  routing — visible, deliberate links rather than a static mesh.
- Slow idle rotation + pointer lean = "first-person agency" (the system tracks and reacts,
  it isn't inert wallpaper).

Implementation: three.js via CDN (`unpkg`/`jsdelivr`), `THREE.Points` for the shell,
`THREE.LineSegments` for a nearest-neighbor connection graph recomputed on an interval,
additive blending for a glow-like premium look, `requestAnimationFrame` loop driven by clock
time + normalized pointer position. No textures/images needed → satisfies "no placeholder
images."

## Color and typography system

**Palette (dark, premium):**
- Background: `#05070c` → `#0b0f1a` vertical gradient (near-black, slight blue undertone).
- Panel/card surface: `#10141f` with 1px `#232a3d` hairline borders.
- Primary accent (the "broadcast" glow): `#7dd3fc` → `#a78bfa` gradient (cyan → violet), used
  for the 3D core, headline highlight, links, table header accents.
- Secondary accent (benchmark deltas / "improvement" values): `#34d399` (green) for
  J-Space-assisted numbers outperforming baseline.
- Body text: `#c7cbd6` on dark surfaces; headings `#f4f5f8`.
- Muted/meta text: `#7c8296`.

**Typography:**
- Headings: `"Space Grotesk"` (Google Fonts CDN) — geometric, technical, fits an
  infra/tooling product.
- Body + table/code: system UI stack (`-apple-system, BlinkMacSystemFont, "Segoe UI",
  Inter, sans-serif`) for body text, and `"JetBrains Mono"` (Google Fonts CDN) for the
  code/CLI snippets, ledger commands, and version strings — reinforces "control system for
  a coding agent."
- Scale: hero H1 ~clamp(2.5rem, 6vw, 4.5rem); section H2 ~2rem; body ~1rem/1.6 line-height;
  monospace blocks ~0.9rem.

## Facts from NOTES.md mapped to sections

- **Hero:** project name "J-Space Cognition Suite V3.6," one-line description ("model-agnostic
  inference-time control system... model weights and training remain unchanged"), design
  principle quote ("Dense on the inside, decodable on demand, clean on the outside"),
  Apache-2.0 badge, GitHub stats (2,547 stars · 165 forks).
- **How it works:** the three-pass table (`fast`/`full`/`loop` + what loads), the seven-row
  core-mechanisms table, and a short line on the optional `jspace.py` controller
  (`.jspace/` state dir, "records and reports state, solution choice remains with the model").
- **Benchmark highlights:** the full model-comparison table (HLE w/o & w/ tools, Terminal
  Bench 2.1, NL2Repo, CyberGym, DeepSWE, Toolathlon-Verified, Agents' Last Exam,
  AutomationBench) and the efficiency table (2.53× speed, 2.21× token-cost improvement),
  plus the evaluation-context caveat sentence so the numbers aren't presented as
  independently audited.
- **Install/usage:** Option A's 5 numbered steps, the `verify_suite.py` command line, and the
  invocation examples (`/j-space`, `$j-space`, or direct request text).
- **Structure:** the repo tree summary (one entry `SKILL.md`, 9 modules, 3 references,
  scripts dir) and the exact file names for modules/references from NOTES.md.
- **Footer:** Apache License 2.0 (with link semantics, no live external link required to
  function), release history string (V1 → V3.6), links to the three fetched Sources (GitHub
  main repo, capability-realization report, Zenodo record `10.5281/zenodo.22004675`
  v3.6.1), author handle `Tiger3807861189`.
