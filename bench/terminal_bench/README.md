# Terminal-Bench adapter

Lets [Terminal-Bench](https://github.com/laude-institute/terminal-bench) (`terminal-bench` on
PyPI, tested against `0.2.18`) drive the `omp` CLI (`@oh-my-pi/pi-coding-agent`) inside its
Docker task containers, with the arm (`jspace` / `none` / `placebo`) selected by env var.

## Files

- `omp_agent.py` — `OmpAgent(AbstractInstalledAgent)`, resolved by Terminal-Bench via
  `--agent-import-path bench.terminal_bench.omp_agent:OmpAgent`. Reads `DEEP_FABLE_ARM` at
  construction, resolves the addendum via `bench.arms.arms.arm_prompt`, and runs
  `omp --model … --thinking … --append-system-prompt <file> --no-session --auto-approve --print <instruction>`
  inside the container.
- `omp-setup.sh.j2` — container install script (curl-installs bun, `bun install -g
  @oh-my-pi/pi-coding-agent`). Rendered and copied into the container by the base class before
  the run commands execute.
- `subset.txt` — 12 curated task ids, one per line, with an inline `# reason` comment.
- `run.py` — driver: resolves the subset, either writes synthetic `--dry-run` records or shells
  out to `tb run` and converts its `results.json` into the shared JSONL schema.

## Real API, not memory

Read straight from the installed package
(`uv run --with terminal-bench python -c "import terminal_bench; print(terminal_bench.__file__)"`,
cached under `~/.cache/uv/archive-v0/…/site-packages/terminal_bench/`):

- `terminal_bench/agents/installed_agents/abstract_installed_agent.py` — `AbstractInstalledAgent`,
  the base class every installed-CLI adapter subclasses. Abstract members: `_env` (property),
  `_install_agent_script_path` (property), `_run_agent_commands(instruction) -> list[TerminalCommand]`.
  `perform_task` (concrete, lines 108–179) copies the install script into the container, sources
  an env-setup file built from `_env`, runs the install script, then sends each `TerminalCommand`
  from `_run_agent_commands`.
- `terminal_bench/agents/installed_agents/codex/codex_agent.py` (`CodexAgent`) and
  `terminal_bench/agents/installed_agents/claude_code/claude_code_agent.py` (`ClaudeCodeAgent`) —
  the two closest shipped adapters; `OmpAgent` copies their shape (env dict with the provider API
  key, a Jinja2 `*-setup.sh.j2` template installing the CLI via nvm+npm, one `TerminalCommand`
  running the CLI non-interactively over the instruction).
- `terminal_bench/agents/agent_factory.py` — `AgentFactory.get_agent_from_import_path`
  (lines 64–79) does exactly `module_name, class_name = import_path.split(":", 1)` then
  `importlib.import_module(module_name)` / `getattr`. This is what makes
  `--agent-import-path bench.terminal_bench.omp_agent:OmpAgent` work without registering
  anywhere in the installed package — confirmed by constructing the agent through
  `AgentFactory.get_agent(import_path=…)` directly (see Verification below).
- `terminal_bench/cli/tb/runs.py` (`create`, lines 98–403) — the `tb run` CLI. Relevant flags:
  `-t/--task-id` (repeatable), `-d/--dataset-path`, `-m/--model`, `--agent-import-path`,
  `--output-path`, `--run-id`. `agent` and `agent_import_path` are mutually exclusive
  (`runs.py:360-361`).
- `terminal_bench/harness/models.py` — `TrialResults` (`task_id`, `is_resolved`,
  `total_input_tokens`, `total_output_tokens`, `agent_started_at`/`agent_ended_at`,
  `failure_mode`) and `BenchmarkResults` (`results: list[TrialResults]`).
- `terminal_bench/harness/harness.py` — `_results_output_path` (line 185-186) is
  `output_path/run_id/results.json`; `_write_results` (line 830-831) dumps `BenchmarkResults`
  there. `run.py`'s `live_records()` parses exactly this file.
- No divergence from the documented API was found — `AbstractInstalledAgent` and
  `AgentFactory.get_agent_from_import_path` behave exactly as their docstrings/signatures say.

`omp` itself: installed on this machine via `bun install -g @oh-my-pi/pi-coding-agent`
(`~/.bun/bin/omp -> …/@oh-my-pi/pi-coding-agent/dist/cli.js`, `omp --version` → `omp/17.3.8`).
`omp --help` confirms every flag the adapter uses: `--model`, `--thinking`,
`--append-system-prompt=<value>` ("Append text or file contents to the system prompt"),
`-p/--print` ("Non-interactive mode: process prompt and exit"), `--no-session`, `--auto-approve`.

## Task ids

`tb datasets download -d "terminal-bench-core==0.1.1"` (the version compatible with
terminal-bench `0.2.18`; `head` and `0.1.0` are also listed by `tb datasets list --name
terminal-bench-core` but `0.1.0` requires `<0.2.4`) pulls **80 real tasks**, each with a
`task.yaml` carrying `difficulty` (12 easy / 44 medium / 24 hard) and `category` (9 categories:
software-engineering, system-administration, security, debugging, file-operations,
data-science, model-training, games, scientific-computing). The full 80-id list and its
per-task difficulty/category is reproducible with the command above — not reproduced here to
avoid a stale copy drifting from the registry.

### The 12-task selection (`subset.txt`)

| task id | difficulty | category | why |
|---|---|---|---|
| `hello-world` | easy | file-operations | near-zero-cost smoke test: build, run, grade, all wired before spending on anything harder |
| `csv-to-parquet` | easy | data-science | easy tier, different category, small container |
| `fix-permissions` | easy | system-administration | easy tier, classic unix task, cheap container |
| `extract-safely` | easy | security | easy tier security, distinct failure surface |
| `modernize-fortran-build` | easy | software-engineering | easy tier build-toolchain flavor, no heavy qemu/kernel image |
| `conda-env-conflict-resolution` | medium | debugging | medium-tier environment-resolution debugging |
| `fix-git` | medium | software-engineering | medium-tier git internals |
| `openssl-selfsigned-cert` | medium | security | medium security, distinct from the easy security task |
| `jupyter-notebook-server` | medium | data-science | medium, service-oriented data-science task |
| `chess-best-move` | medium | games | only reasonably-sized games task (the others are hard); adds an uncovered category |
| `swe-bench-fsspec` | medium | debugging | real SWE-bench-derived task embedded in terminal-bench |
| `intrusion-detection` | hard | system-administration | sole hard-tier representative |

Deliberately excluded: `build-linux-kernel-qemu`, `build-initramfs-qemu`, `build-tcc-qemu`,
`pytorch-model-cli*`, `train-fasttext`, `qemu-*` — these pull much larger base images and/or
run much longer, which is disproportionate for a calibration set whose only job is to prove the
harness works and to measure per-task cost, not to be exhaustive.

## Scope limitation — read before citing a number from this subset

**This 12-task subset is for harness validation and cost calibration. It is not statistically
powered to measure the J-Space skill's effect.** With 12 paired trials, McNemar's exact test
(the comparison method mandated by the shared contract — never a two-proportion z-test) can
only detect effect sizes on the order of **35-40 percentage points** at conventional power/alpha
with any plausible number of discordant pairs. The upstream repo's claimed +7 to +16pp gains
are roughly 3-5x smaller than what 12 tasks can resolve. Confirming or refuting a claim that
size requires the full 80-task dataset, run multiple times per arm, with discordant-pair counts
reported alongside the McNemar p-value every time a verdict is stated.

## Disk / time / cost

**Unmeasured for actual task containers** — this task's constraints forbid pulling per-task
Docker images or running `tb run` (that would need Docker builds, a live `OPENROUTER_API_KEY`,
and money). What was measured, from work actually done while building this adapter:

- `tb datasets download -d "terminal-bench-core==0.1.1"` (task specs only — Dockerfiles,
  `docker-compose.yaml`, tests, no base images pulled): ~59s over the network, 80 task
  directories, no image pull.
- `uv run --with terminal-bench …` first invocation: 119 packages, ~340ms env resolve
  (uv's package cache warm) to ~17s cold; terminal-bench's own dependency tree pulls
  `litellm`, `pandas`, `pyarrow`, `streamlit`, `boto3`/`botocore`, `anthropic`, `openai` —
  none of this repo's own dependency, just terminal-bench's.

Before running the subset for real, budget for: 12x `docker compose build` (base images vary
per task, typically Ubuntu/Debian + task-specific tooling — some pull large images, e.g. any
task with a full Linux toolchain), plus `curl | bash` for bun and `bun install -g
@oh-my-pi/pi-coding-agent` inside every container (network egress per container, not reused
across tasks since each task gets a fresh container).

## Arm selection

`DEEP_FABLE_ARM` (`jspace` | `none` | `placebo`, default `none`) is read once at `OmpAgent.__init__`
and resolved through `bench.arms.arms.arm_prompt`, then base64-encoded into the container's env
(`DEEP_FABLE_SYSTEM_PROMPT_B64`) and written to `/installed-agent/append-system-prompt.txt`
before `omp --append-system-prompt` reads it. `DEEP_FABLE_MODEL` / `DEEP_FABLE_THINKING`
override the defaults (`openrouter/deepseek/deepseek-v4-flash-0731`, `max`) the same way; an
explicit `--model` on `tb run` (passed through as the `model_name` constructor kwarg) takes
priority over the env var.

## Reproduce

```bash
# Harness validation only — no model, no Docker, no cost:
uv run bench/terminal_bench/run.py --arm jspace --dry-run
uv run bench/terminal_bench/run.py --arm none --dry-run
uv run bench/terminal_bench/run.py --arm placebo --dry-run
# -> appends to bench/results/terminal_bench-<UTC-ISO8601>.jsonl

# Real run (money, Docker, time — orchestrator decision only):
tb datasets download -d "terminal-bench-core==0.1.1" --output-dir ~/.cache/terminal-bench-core-0.1.1
OPENROUTER_API_KEY=... uv run bench/terminal_bench/run.py \
  --arm jspace \
  --dataset-path ~/.cache/terminal-bench-core-0.1.1
```

Repeat with `--run-idx 2`, `3`, … for multiple trials per arm — `run.py` runs the subset once
per invocation; repeated invocations are how paired counts accumulate for McNemar's test.
