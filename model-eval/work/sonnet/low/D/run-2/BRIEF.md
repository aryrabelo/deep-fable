# Task D

Work only inside this directory. It contains a copy of a "skill" tree
(`SKILL.md`, `modules/`, `references/`, `scripts/`).

`scripts/verify_suite.py` is a structural linter over that tree. It runs 6 numbered
checks and exits 1 with findings, 0 when clean. The checks are ordered by severity and
the file documents them in its docstring.

Add check #7: no two files under `modules/` may contain byte-identical `**Pass:**`
drill lines (a copy-paste smell). When a duplicate exists the check must name both
files. Follow the file's existing check style and keep all existing checks intact and
passing.

Acceptance (held out, run by us):
- on the pristine tree as shipped in this directory, `python3 scripts/verify_suite.py`
  must exit 0;
- after we duplicate one `**Pass:**` line from one module into another, it must exit 1
  and its output must name both modules.

Stdlib only. Reply with one line `DONE` when implemented.
