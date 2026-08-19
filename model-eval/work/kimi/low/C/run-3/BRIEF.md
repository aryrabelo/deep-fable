# Task C

Work only inside this directory.

`verify.py` scores benchmark results. Its `score_tier1()` has a bug: numeric reject
aliases are matched as whole tokens, but alphabetic reject aliases are matched as raw
substrings of the normalized answer text. A reject alias like `no` therefore produces a
false `TRAP` when the answer contains an unrelated word like `north`.

Fix it so alphabetic aliases also match on word boundaries.

Must keep working (regression contract):
- numeric aliases match as exact tokens (`100` must not match `1100`);
- `expect_any` (substring/phrase aliases like `cannot be determined`) and `expect_all`;
- `TRAP` must still fire when a reject alias genuinely appears as a word;
- stdlib only, no new dependencies;
- `python3 verify.py` still runs and exits 0.

Reply with one line `DONE` when fixed.
