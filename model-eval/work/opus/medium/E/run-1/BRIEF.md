# Task E

Work only inside this directory.

`jspace.py` is a session-state ledger CLI (stdlib only) with subcommands `note`, `seam`,
`ship`, `resume`, registered via argparse subparsers in `main()` and dispatched there.
It keeps state under `.jspace/` in the CURRENT working directory, and it never exits
non-zero just because state is missing — a missing ledger prints zeros/empty state and
still exits 0.

Add a `stats` subcommand that prints exactly one line:

    verified=<n> open=<n> core=<n>

computed from the ledger book (count of verified checkpoints, open questions, and live
core entries). With no `.jspace/` state at all it must print `verified=0 open=0 core=0`
and exit 0. Follow the file's existing subcommand pattern.

Acceptance (held out, run by us): in a fresh empty directory, `stats` exits 0 and its
stdout matches `^verified=\d+ open=\d+ core=\d+$`; after `note --goal g --next n`,
`stats` still matches and exits 0.

Reply with one line `DONE` when implemented.
