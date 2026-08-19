# Task R3 — Landing page built from a live URL

You will build a production-quality landing page for the project at:

**https://github.com/Tiger3807861189/J-Space-Cognition-Suite-V3.6**

Work only inside this directory. The work has five stages, and each stage produces an
artifact that will be inspected. Do not skip stages.

## Stage 1 — READ

Fetch the URL above and read its README with your web tools. Save everything relevant to
`NOTES.md`: what the project is, how it is structured, the headline benchmark numbers,
install/usage steps, license, and exact names and version strings.

## Stage 2 — RESEARCH

Follow at least two links from that page (e.g. the capability-realization report, a model
card it cites, the Zenodo DOI record) and read them. Append what you learned to `NOTES.md`
under a `## Sources` section listing every URL you actually fetched.

## Stage 3 — PLAN

Write `PLAN.md`: the page's section list, the 3D concept and why it fits the project, the
color and typography system, and which facts from `NOTES.md` go into each section.

## Stage 4 — BUILD

Create `site/` with `index.html` and any local assets. Requirements:

- A **real-time 3D element** in the hero (WebGL / three.js via CDN is acceptable) that is
  tied to the project's theme — e.g. an abstract "workspace / stage / broadcast" visual —
  and that actually animates or reacts (pointer, scroll, or time).
- Sections: hero, how-it-works, benchmark highlights using the **real numbers from your
  NOTES.md**, install/usage, and a footer with license and links.
- Dark, premium visual design; responsive; system or CDN fonts; **no lorem ipsum, no
  placeholder images, no stock-photo hotlinks**.
- Every factual claim on the page must come from your `NOTES.md` — nothing invented.

## Stage 5 — VERIFY

Open the page in a browser, check the console for errors, and confirm the 3D element
renders. Fix what you find. Write `VERIFY.md` listing what you checked and what you fixed.

When finished, reply with one line: `DONE`.
