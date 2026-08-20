#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["terminal-bench>=0.2.18,<0.3"]
# ///
"""Run the curated Terminal-Bench subset for one arm, append results as JSONL.

Usage:
    uv run bench/terminal_bench/run.py --arm jspace --dry-run
    OPENROUTER_API_KEY=... uv run bench/terminal_bench/run.py \\
        --arm jspace --dataset-path ~/.cache/terminal-bench/terminal-bench-core/0.1.1

`--dry-run` resolves the arm, the model, the subset, and the output path,
writes one synthetic `passed: false, notes: "dry-run"` record per task, and
calls no model and no `tb` subprocess. It exists to prove the wiring (arm
resolution, task listing, JSONL schema) without spending anything.

Without `--dry-run` it shells out to `tb run` with
`--agent-import-path bench.terminal_bench.omp_agent:OmpAgent`, then parses
the aggregate `results.json` Terminal-Bench writes
(terminal_bench/harness/harness.py: `_results_output_path` /
`_write_results`) into the shared JSONL schema. This path needs Docker, a
downloaded dataset, and `OPENROUTER_API_KEY` — it is implemented but never
executed by this task (see README "Scope").
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bench.arms.arms import ARMS, arm_prompt  # noqa: E402

BENCHMARK = "terminal_bench"
HARNESS = "terminal-bench"
DEFAULT_MODEL = "openrouter/deepseek/deepseek-v4-flash-0731"
DEFAULT_THINKING = "max"
SUBSET_PATH = Path(__file__).resolve().parent / "subset.txt"
RESULTS_DIR = REPO_ROOT / "bench" / "results"


def load_subset(path: Path = SUBSET_PATH) -> list[str]:
    task_ids = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            task_ids.append(line)
    return task_ids


def results_path(run_started: datetime) -> Path:
    stamp = run_started.strftime("%Y%m%dT%H%M%SZ")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR / f"{BENCHMARK}-{stamp}.jsonl"


def dry_run_records(task_ids: list[str], arm: str, model: str) -> list[dict]:
    return [
        {
            "benchmark": BENCHMARK,
            "task_id": task_id,
            "arm": arm,
            "run_idx": 1,
            "passed": False,
            "latency_s": 0.0,
            "model": model,
            "harness": HARNESS,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "notes": "dry-run",
        }
        for task_id in task_ids
    ]


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def live_records(
    output_path: Path, run_id: str, arm: str, model: str, run_idx: int
) -> list[dict]:
    """Parse `output_path/run_id/results.json` (a `BenchmarkResults` dump)."""
    raw = json.loads((output_path / run_id / "results.json").read_text())
    records = []
    for trial in raw.get("results", []):
        started = _parse_timestamp(trial.get("agent_started_at"))
        ended = _parse_timestamp(trial.get("agent_ended_at"))
        latency_s = (ended - started).total_seconds() if started and ended else 0.0
        failure_mode = trial.get("failure_mode") or ""
        records.append(
            {
                "benchmark": BENCHMARK,
                "task_id": trial["task_id"],
                "arm": arm,
                "run_idx": run_idx,
                "passed": bool(trial.get("is_resolved")),
                "latency_s": latency_s,
                "model": model,
                "harness": HARNESS,
                "tokens_in": trial.get("total_input_tokens") or 0,
                "tokens_out": trial.get("total_output_tokens") or 0,
                "cost_usd": 0.0,
                "notes": "" if trial.get("is_resolved") else failure_mode,
            }
        )
    return records


def make_run_id(arm: str, now: datetime) -> str:
    """Terminal-Bench passes `--run-id` straight through to `docker compose -p`,
    which rejects anything but lowercase alphanumerics, hyphens and underscores.
    An ISO-style stamp carries uppercase `T`/`Z` and makes every container build
    fail with `invalid project name` before the agent is ever invoked — a
    plumbing failure that terminal-bench reports as `unknown_agent_error`, i.e.
    indistinguishable from a model failure in results.json. Hence lowercase."""
    return f"{arm}-{now.strftime('%Y%m%d-%H%M%S')}".lower()


def run_live(
    task_ids: list[str],
    arm: str,
    model: str,
    thinking: str,
    dataset_path: Path,
    tb_output_path: Path,
    run_idx: int,
    agent_timeout_sec: float,
) -> list[dict]:
    run_id = make_run_id(arm, datetime.now(timezone.utc))
    env = dict(os.environ)
    env["DEEP_FABLE_ARM"] = arm
    env["DEEP_FABLE_MODEL"] = model
    env["DEEP_FABLE_THINKING"] = thinking
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [
        "uv",
        "run",
        "--with",
        "terminal-bench",
        "tb",
        "run",
        "--agent-import-path",
        "bench.terminal_bench.omp_agent:OmpAgent",
        "--dataset-path",
        str(dataset_path),
        "--output-path",
        str(tb_output_path),
        "--run-id",
        run_id,
        "--global-agent-timeout-sec",
        str(agent_timeout_sec),
    ]
    for task_id in task_ids:
        cmd += ["-t", task_id]

    subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=True)
    return live_records(tb_output_path, run_id, arm, model, run_idx)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, choices=ARMS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", default=os.environ.get("DEEP_FABLE_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--agent-timeout-sec", type=float, default=2400.0,
        help="Passed through as tb's --global-agent-timeout-sec. The default "
             "must cover container setup, which is serial and expensive: apt-get "
             "curl/unzip, the bun installer, then `bun install -g "
             "@oh-my-pi/pi-coding-agent` (~600 packages) runs inside every fresh "
             "container, ~11min observed before the agent gets its first token. "
             "terminal-bench's default cut the install off mid-flight and "
             "recorded `agent_timeout` with 0 tokens. "
             "ponytail: raise the ceiling rather than cache the install; bake omp "
             "into a base image if the setup share of wall time starts to hurt.",
    )
    parser.add_argument(
        "--thinking", default=os.environ.get("DEEP_FABLE_THINKING", DEFAULT_THINKING)
    )
    parser.add_argument("--run-idx", type=int, default=1)
    parser.add_argument(
        "--task", default="", metavar="ID1,ID2",
        help="Comma-separated task ids to run instead of subset.txt. Purposive "
             "selection for diagnostics and smoke tests; never a powered estimate.",
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        help="Path to a downloaded terminal-bench-core checkout "
        "(required unless --dry-run; see README)",
    )
    parser.add_argument(
        "--tb-output-path",
        type=Path,
        default=REPO_ROOT / "bench" / "results" / ".tb-runs",
        help="Scratch dir tb writes container logs/results.json into",
    )
    args = parser.parse_args()

    # Fail fast on an unknown arm before touching the filesystem or network.
    arm_prompt(args.arm)

    task_ids = load_subset()
    if args.task:
        task_ids = [t.strip() for t in args.task.split(",") if t.strip()]
        if args.dataset_path is not None:
            known = {p.name for p in args.dataset_path.iterdir() if p.is_dir()}
            unknown = [t for t in task_ids if t not in known]
            if unknown:
                parser.error(f"unknown task id(s) {unknown} in {args.dataset_path}")
        print(f"--task: {len(task_ids)} task(s) (purposive, not subset.txt).")
    started = datetime.now(timezone.utc)
    out_path = results_path(started)

    if args.dry_run:
        records = dry_run_records(task_ids, args.arm, args.model)
    else:
        if args.dataset_path is None:
            parser.error("--dataset-path is required unless --dry-run")
        if "OPENROUTER_API_KEY" not in os.environ:
            parser.error("OPENROUTER_API_KEY must be set for a live run")
        records = run_live(
            task_ids,
            args.arm,
            args.model,
            args.thinking,
            args.dataset_path,
            args.tb_output_path,
            args.run_idx,
            args.agent_timeout_sec,
        )

    with out_path.open("a") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")

    print(f"wrote {len(records)} records to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
