<!--
Placebo arm control text.

This file exists only to length-match the "placebo" ablation arm against the
real J-Space always-on snippet (profile/APPEND_SYSTEM.md) in token count. Its
purpose is to isolate the effect of what the J-Space skill instructs the model
to do from the mere effect of adding extra tokens to the system prompt.

It MUST stay content-free: no instruction to think, plan, reflect, verify,
decompose a task, go step by step, or use any kind of workspace or scratchpad.
If this file ever teaches the model something useful about how to approach a
task, the placebo arm stops controlling for length and starts controlling for
nothing, and the ablation is void. Keep it inert formatting trivia only.
-->

Formatting reference: numbers under one thousand are written as words when they open a sentence, and as digits everywhere else.
Dates follow the ISO 8601 pattern: year first, then month, then day, separated by hyphens.
Currency amounts include the ISO 4217 code before the numeral, never a symbol alone.
