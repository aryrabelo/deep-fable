# Task F

Work only inside this directory.

`verify.py` scores benchmark results. Its `score_tier2()` calls
`subprocess.run(..., timeout=60)` with no exception handling: a hung or crashing run
raises `subprocess.TimeoutExpired` or `OSError`, which propagates and kills the whole
score-table generation.

Fix it: catch `subprocess.TimeoutExpired` (return the string `"TIMEOUT"`) and `OSError`
(return a string starting with `"ERROR"`) instead of raising.

Must keep working (regression contract):
- normal behavior unchanged: exit code 0 -> `"PASS"`, non-zero -> `"FAIL (...)"`;
- the `(workdir / "test_cart.py").exists()` early return unchanged;
- stdlib only.

Reply with one line `DONE` when fixed.
