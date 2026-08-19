# Round 3 — opus:medium vs deepseek:max landing-page shootout — 2026-08-19

Single creative multistep task (five-stage landing-page build from a live GitHub source,
per `BRIEF.md`), 1 run per cell. Variance caveat: n=1 per cell; treat the subjective
verdict as directional, not statistical.

## Cells

| cell | model id | wall time |
|---|---|---|
| opus-medium | `anthropic/claude-opus-5:medium` | 1093s (~18 min) |
| deepseek-max | `openrouter/deepseek/deepseek-v4-flash-0731:max` | 899s (~15 min) |

Both dispatched in parallel, identical brief/workdir, no skills, no git access.

## Objective checker (`acceptance/check_page.py`, held out)

**Both cells: 12/12 PASS.** Artifacts (NOTES.md, PLAN.md, VERIFY.md, site/) present,
3D/WebGL present, >= 5 real facts from source, no lorem/placeholders, >= 3 fetched
source URLs (opus: 6, deepseek: 4).

## Render check (headless Chrome, file://, networkidle + 4s)

| cell | console errors | WebGL context | canvas |
|---|---|---|---|
| opus-medium | 0 | live | 756×510 |
| deepseek-max | 0 | live | 756×683 |

Full-page screenshots: `blind-X.png`, `blind-Y.png`.

## Blind A/B (human judge)

Random assignment sealed before viewing (`.blind-assignment.json`):
X = opus-medium, Y = deepseek-max. Judge saw only X/Y labels.

**Verdict: X (opus-medium) wins, narrowly** — judge's words: "quase um empate mas a X
tá melhor".

## Conclusions

1. On objective correctness this task also failed to discriminate: 12/12 both, clean
   render both. The discrimination only appeared in subjective design quality, and even
   there it was marginal.
2. Combined with Round 1 (234/234 ceiling), the practical guidance stands: deepseek at
   ~$0.07–0.14/Mtok (this run cost cents) delivers near-opus output on this class of
   work; reserve the Anthropic quota for tasks where the marginal quality edge matters.
3. Reproduce: dispatch per `RESUME.md`, score with
   `python3 model-eval/round3/acceptance/check_page.py model-eval/round3/work/<cell>/run-1`.
