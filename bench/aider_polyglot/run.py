#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Driver over the Aider polyglot-benchmark exercise set, across the arms in bench.arms.arms.ALL_ARMS.

Ground truth (verified by reading the real repo, not guessed):

  https://github.com/Aider-AI/polyglot-benchmark
  225 Exercism-derived exercises across C++, Go, Java, JavaScript, Python,
  Rust. Each exercise lives at ``<lang>/exercises/practice/<name>/`` and
  carries:

    .docs/instructions.md          the task statement shown to the agent
    .docs/introduction.md          optional track-specific intro (prepended)
    .docs/instructions.append.md   optional addendum (appended)
    .meta/config.json              {"files": {"solution": [...], "test": [...],
                                     "example": [...]}} plus a reference
                                     solution under .meta/ (the answer key —
                                     never copied into the agent's scratch dir)
    <solution files>                stub the agent edits (e.g. bowling.py)
    <test files>                    already present next to the stub
                                     (e.g. bowling_test.py); re-copied fresh
                                     from the pristine clone before grading so
                                     the agent editing them can't cheat
    <build plumbing>                CMakeLists.txt + test/catch.hpp (C++),
                                     Cargo.toml (Rust), go.mod (Go),
                                     package.json (JS), gradlew + build.gradle
                                     (Java) — all vendored per exercise

  Each exercise is MIT-licensed (Exercism, see e.g.
  javascript/exercises/practice/triangle/LICENSE); the repo README points to
  the upstream Exercism track repos for the canonical grant.

  Native (non-Docker) test commands, one per language (aider's own harness at
  https://github.com/Aider-AI/aider/blob/main/benchmark/benchmark.py runs
  these inside a purpose-built container; we run them directly on the host
  and SKIP a language whose toolchain doesn't work here):

    python      uv run --with pytest pytest -q
    rust        cargo test -- --include-ignored
    go          go test ./...
    javascript  npm install && npm test   (also unxtest()s disabled specs)
    java        ./gradlew test --console=plain
    cpp         cmake -DEXERCISM_RUN_ALL_TESTS=1 -G "Unix Makefiles" .. && make
                (the generated CMakeLists.txt wires a CTest-free `ALL` target
                that both builds and executes the Catch2 binary, so `make`
                alone is pass/fail)
Every (exercise, arm, run) triple executes in its own scratch copy under
bench/aider_polyglot/.scratch/ so the three arms never contaminate each
other, and the copy excludes .meta/.docs/.approaches so the agent can never
read the reference solution or already know it's part of a graded exercise
via those directories.

Resume and concurrency (`--resume`, `--jobs`): the sweep is long and not
free, so both are opt-in and additive over the default sequential,
from-scratch behaviour. `--resume` re-reads an existing `--out` JSONL and
skips any (task_id, arm, run_idx) unit already recorded there — see
load_completed() for exactly what counts as done. `--jobs N` runs N units
concurrently through a thread pool (the work is subprocess-bound, so
threads are correct and multiprocessing is unnecessary); JSONL writes are
serialised and flushed per record so a `kill -9` mid-sweep leaves a valid,
resumable partial file. `--jobs` > 1 risks tripping provider rate limits
and running multiple languages' test suites at once, which contend for the
same CPU — start at 2-4 and watch for timeouts before going higher.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from bench.arms.arms import ALL_ARMS, ARMS, arm_prompt, arm_spec  # noqa: E402

POLYGLOT_REPO_URL = "https://github.com/Aider-AI/polyglot-benchmark"
CACHE_DIR = HERE / ".cache" / "polyglot-benchmark"
SCRATCH_ROOT = HERE / ".scratch"

LANG_DIRS = {
    "cpp": "cpp",
    "go": "go",
    "java": "java",
    "javascript": "javascript",
    "python": "python",
    "rust": "rust",
}

DEFAULT_MODEL = os.environ.get("BENCH_MODEL", "openrouter/deepseek/deepseek-v4-flash-0731")
DEFAULT_THINKING = os.environ.get("BENCH_THINKING", "max")


def effective_model_thinking(arm: str, args_model: str, args_thinking: str) -> tuple[str, str]:
    """Resolve the (model, thinking) an arm actually runs with: the arm's own
    pinned values (ds-*/opus-med/sonnet-med) if it has them, else the
    runner's --model/--thinking (the legacy jspace/none/placebo behaviour).
    """
    spec = arm_spec(arm)
    return spec.model or args_model, spec.thinking or args_thinking


@dataclass(frozen=True)
class Exercise:
    lang: str
    name: str
    dir: Path
    solution_files: tuple[str, ...]
    test_files: tuple[str, ...]

    @property
    def task_id(self) -> str:
        return f"{self.lang}/{self.name}"


# --------------------------------------------------------------------------
# Repo fetch + exercise discovery
# --------------------------------------------------------------------------


def ensure_repo(repo_dir: Path) -> Path:
    if (repo_dir / "README.md").exists():
        return repo_dir
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning {POLYGLOT_REPO_URL} -> {repo_dir} ...", file=sys.stderr)
    subprocess.run(
        ["git", "clone", "--depth", "1", POLYGLOT_REPO_URL, str(repo_dir)],
        check=True,
    )
    return repo_dir


def discover_exercises(repo_dir: Path) -> list[Exercise]:
    out: list[Exercise] = []
    for lang, sub in LANG_DIRS.items():
        practice = repo_dir / sub / "exercises" / "practice"
        if not practice.is_dir():
            continue
        for exdir in sorted(practice.iterdir()):
            if not exdir.is_dir():
                continue
            config_file = exdir / ".meta" / "config.json"
            if not config_file.exists():
                continue
            config = json.loads(config_file.read_text())
            files = config.get("files", {})
            solution = tuple(files.get("solution", []))
            test = tuple(files.get("test", []))
            if not solution or not test:
                continue
            out.append(Exercise(lang, exdir.name, exdir, solution, test))
    return out


# --------------------------------------------------------------------------
# Toolchain probing — actually invoke each binary; `which` alone lies (macOS
# ships a /usr/bin/java stub that resolves but exits 1 with no JDK installed)
# --------------------------------------------------------------------------


def _probe(cmd: list[str]) -> bool:
    try:
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def probe_toolchains() -> dict[str, tuple[bool, str]]:
    out: dict[str, tuple[bool, str]] = {}

    cxx_ok = any(_probe([c, "--version"]) for c in ("c++", "g++", "clang++"))
    cmake_ok = _probe(["cmake", "--version"])
    out["cpp"] = (
        (True, "")
        if cxx_ok and cmake_ok
        else (False, "no working C++ compiler" if not cxx_ok else "cmake not found")
    )

    go_ok = _probe(["go", "version"])
    out["go"] = (go_ok, "" if go_ok else "go not found")

    java_ok = _probe(["java", "-version"])
    out["java"] = (java_ok, "" if java_ok else "java runtime not found or not functional")

    node_ok = _probe(["node", "--version"])
    npm_ok = _probe(["npm", "--version"])
    out["javascript"] = (
        (True, "")
        if node_ok and npm_ok
        else (False, "node not found" if not node_ok else "npm not found")
    )

    py_ok = _probe([sys.executable, "--version"])
    uv_ok = _probe(["uv", "--version"])
    out["python"] = (
        (True, "")
        if py_ok and uv_ok
        else (False, "python3 not found" if not py_ok else "uv not found (needed for ephemeral pytest)")
    )

    rustc_ok = _probe(["rustc", "--version"])
    cargo_ok = _probe(["cargo", "--version"])
    out["rust"] = (
        (True, "")
        if rustc_ok and cargo_ok
        else (False, "rustc not found" if not rustc_ok else "cargo not found")
    )

    return out


# --------------------------------------------------------------------------
# Test command construction + execution
# --------------------------------------------------------------------------


def display_test_command(lang: str) -> str:
    return {
        "python": "uv run --with pytest pytest -q",
        "rust": "cargo test -- --include-ignored",
        "go": "go test ./...",
        "javascript": "npm install && npm test",
        "java": "./gradlew test --console=plain",
        "cpp": 'mkdir build && cd build && cmake -DEXERCISM_RUN_ALL_TESTS=1 -G "Unix Makefiles" .. && make',
    }[lang]


def run_tests(ex: Exercise, cwd: Path, timeout: int) -> tuple[bool, str]:
    """Run the exercise's own test command. Returns (passed, combined_output)."""
    if ex.lang == "cpp":
        build = cwd / "build"
        build.mkdir(exist_ok=True)
        out = []
        for cmd in (
            ["cmake", "-DEXERCISM_RUN_ALL_TESTS=1", "-G", "Unix Makefiles", ".."],
            ["make"],
        ):
            r = subprocess.run(cmd, cwd=build, capture_output=True, text=True, timeout=timeout)
            out.append(r.stdout + r.stderr)
            if r.returncode != 0:
                return False, "\n".join(out)
        return True, "\n".join(out)

    if ex.lang == "javascript":
        for spec in cwd.glob("*.spec.js"):
            spec.write_text(re.sub(r"\bxtest\(", "test(", spec.read_text()))
        install = subprocess.run(
            ["npm", "install", "--no-audit", "--no-fund", "--silent"],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        if install.returncode != 0:
            return False, install.stdout + install.stderr
        r = subprocess.run(["npm", "test", "--silent"], cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout + r.stderr

    cmd = {
        "python": ["uv", "run", "--with", "pytest", "pytest", "-q"],
        "rust": ["cargo", "test", "--", "--include-ignored"],
        "go": ["go", "test", "./..."],
        "java": ["./gradlew", "test", "--console=plain"],
    }[ex.lang]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0, r.stdout + r.stderr


# --------------------------------------------------------------------------
# Prompt assembly
# --------------------------------------------------------------------------


def build_prompt(ex: Exercise) -> str:
    docs = ex.dir / ".docs"
    parts: list[str] = []
    intro = docs / "introduction.md"
    if intro.exists():
        parts.append(intro.read_text())
    instructions = docs / "instructions.md"
    parts.append(instructions.read_text() if instructions.exists() else "(no instructions.md found)")
    append = docs / "instructions.append.md"
    if append.exists():
        parts.append(append.read_text())

    file_list = ", ".join(ex.solution_files)
    parts.append(
        "\n---\n"
        f"You may ONLY edit these solution file(s), in the current directory: {file_list}\n"
        "Do not edit the test file(s) or any build configuration. When you are done, "
        "the following command must exit 0 in the current directory:\n\n"
        f"    {display_test_command(ex.lang)}\n"
    )
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Scratch isolation
# --------------------------------------------------------------------------


def _copy_ignore(_dir: str, names: list[str]) -> set[str]:
    # .meta holds the reference solution (the answer key) and config.json;
    # .docs/.approaches are prose already folded into the prompt. None of it
    # belongs in the agent's working directory.
    return {n for n in names if n in {".meta", ".docs", ".approaches"}}


def work_dir(run_dir: Path, ex: Exercise) -> Path:
    """The agent's working directory inside `run_dir`.

    Named after the exercise, NOT a fixed "work": the C++ exercises derive
    their CMake project and source filenames from the directory name
    (`get_filename_component(exercise ${CMAKE_CURRENT_SOURCE_DIR} NAME)`),
    so a directory called `work` makes CMake demand `work.cpp`/`work_test.cpp`
    and every C++ exercise fails to build no matter what the agent writes.
    Keeping the pristine directory name is also the only layout the upstream
    exercises are known to work under, for every language.
    """
    return run_dir / ex.name


def make_scratch(ex: Exercise, arm: str, run_idx: int) -> Path:
    run_dir = SCRATCH_ROOT / f"{ex.lang}__{ex.name}__{arm}__{run_idx}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    shutil.copytree(ex.dir, work_dir(run_dir, ex), ignore=_copy_ignore)
    return run_dir


def restore_test_files(ex: Exercise, work: Path) -> None:
    """Re-copy test files fresh from the pristine clone before grading, so an
    agent that edited the test file to force a pass doesn't get credit."""
    for f in ex.test_files:
        src = ex.dir / f
        if not src.exists():
            continue
        dst = work / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        if ex.lang == "java" and dst.suffix == ".java":
            dst.write_text(re.sub(r"@Disabled\([^)]*\)\s*\n", "", dst.read_text()))


# --------------------------------------------------------------------------
# Agent invocation
# --------------------------------------------------------------------------


def _find_session_file(session_dir: Path) -> Path | None:
    """Locate the session transcript produced by one isolated `--session-dir`
    invocation.

    `--session-dir` scopes ALL of omp's session storage for that invocation
    to a directory we create fresh and own exclusively — nothing else can
    ever write there. That makes resolution deterministic by construction:
    whatever transcript shows up afterward is unambiguously this
    invocation's, no "newest file" heuristic required.

    The observed layout (confirmed 2026-08-19 against real invocations, after
    an earlier guess at `sessions/<project-slug>/<file>.jsonl` silently
    matched nothing and recorded every usage figure as 0) is:

        <session_dir>/<timestamp>_<uuid>.jsonl          <- the transcript
        <session_dir>/<timestamp>_<uuid>/__advisor.jsonl <- side-car, not it

    So: any `*.jsonl` at any depth, minus the `__`-prefixed side-cars. Files
    are matched at any depth rather than only the top level so a future omp
    that reintroduces a subdirectory prefix keeps working.
    """
    candidates = [p for p in session_dir.glob("**/*.jsonl") if not p.name.startswith("__")]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _session_usage(path: Path) -> tuple[int, int, float]:
    """Sum usage across every assistant record in an omp session transcript.

    tokens_in = input + cacheRead + cacheWrite: cached input is still input
    the model conditioned on, and dropping it would understate exactly the
    jspace arm's true context cost, since the skill payload is the thing
    most likely to get cached across turns. tokens_out = output. cost_usd
    uses each record's own `cost.total` rather than summing every value in
    the cost dict — the dict already includes a `total` key alongside the
    per-category breakdown, so summing everything double-counts.
    """
    tokens_in = tokens_out = 0
    cost_usd = 0.0
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            usage = (rec.get("message") or {}).get("usage")
            if not usage:
                continue
            tokens_in += int(usage.get("input", 0)) + int(usage.get("cacheRead", 0)) + int(usage.get("cacheWrite", 0))
            tokens_out += int(usage.get("output", 0))
            cost = usage.get("cost") or {}
            if "total" in cost:
                cost_usd += float(cost["total"])
            else:
                cost_usd += sum(float(v) for k, v in cost.items() if isinstance(v, (int, float)))
    return tokens_in, tokens_out, cost_usd


def invoke_omp(
    prompt: str, arm: str, cwd: Path, model: str, thinking: str, run_dir: Path, timeout: int
) -> tuple[float, int, int, float]:
    """Run the agent under test against `cwd` via the omp CLI. The agent has
    full edit/bash tool access to `cwd` and applies its own edits directly —
    there is no separate "apply the diff" step. Returns
    (latency_s, tokens_in, tokens_out, cost_usd); the usage fields stay 0 if
    no session transcript with usage records turns up (e.g. the invocation
    errored before any model call), matching the shared schema's "unknown
    numeric fields are 0, never null."
    """
    prompt_file = run_dir / "PROMPT.md"
    prompt_file.write_text(prompt)

    session_dir = run_dir / "session"
    session_dir.mkdir(exist_ok=True)

    cmd = [
        "omp", "-p", "--auto-approve", "--session-dir", str(session_dir),
        "--model", model, "--thinking", thinking, "--cwd", str(cwd),
    ]
    if arm_spec(arm).skill != "none":
        sysprompt_file = run_dir / "SYSTEM_APPEND.md"
        sysprompt_file.write_text(arm_prompt(arm))
        cmd += ["--append-system-prompt", str(sysprompt_file)]
    cmd.append(f"@{prompt_file}")

    start = time.time()
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        pass
    latency = time.time() - start

    session_file = _find_session_file(session_dir)
    if session_file is None:
        return latency, 0, 0, 0.0
    tokens_in, tokens_out, cost_usd = _session_usage(session_file)
    return latency, tokens_in, tokens_out, cost_usd


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------

_RECORD_DEFAULTS = dict(
    benchmark="aider_polyglot",
    task_id="", arm="", run_idx=1, passed=False, latency_s=0.0,
    model="", thinking="", harness="omp", tokens_in=0, tokens_out=0, cost_usd=0.0, notes="",
)


def emit(fh, lock: threading.Lock | None = None, **fields) -> None:
    rec = dict(_RECORD_DEFAULTS)
    rec.update(fields)
    line = json.dumps(rec) + "\n"
    # ponytail: one shared lock for every writer, not per-file sharding —
    # writes are microseconds next to a 60-120s agent invocation, so lock
    # contention is noise. Flush every record (not just under --jobs) so a
    # kill -9 mid-sweep, sequential or concurrent, always leaves --resume a
    # valid partial file to read.
    with lock or nullcontext():
        fh.write(line)
        fh.flush()


def default_out_path() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return REPO_ROOT / "bench" / "results" / f"aider_polyglot-{ts}.jsonl"


def load_completed(out_path: Path) -> set[tuple[str, str, int]]:
    """Read an existing --out JSONL and return the (task_id, arm, run_idx)
    keys that already have a *real* record, for --resume to skip.

    A `dry-run` row never counts: it never touched the agent or the grader,
    so it isn't done. A `skip:` row (missing local toolchain) DOES count —
    the toolchain probe is a property of this machine, not of the run, so
    retrying it here can't succeed either; treating it as pending would make
    --resume loop on it forever.
    """
    completed: set[tuple[str, str, int]] = set()
    if not out_path.exists():
        return completed
    with out_path.open() as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue  # truncated last line from a kill -9; not a completed unit
            if rec.get("notes", "") == "dry-run":
                continue
            completed.add((rec.get("task_id", ""), rec.get("arm", ""), rec.get("run_idx", 1)))
    return completed


def filter_resume(
    units: list[tuple], completed: set[tuple[str, str, int]]
) -> list[tuple]:
    """Drop any (ex, arm, run_idx, ...) unit whose (task_id, arm, run_idx)
    key is already in `completed`. `units` elements only need index 0 to
    carry `.task_id`, index 1 the arm, index 2 the run_idx — see main()."""
    return [u for u in units if (u[0].task_id, u[1], u[2]) not in completed]


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--exercises", type=int, default=0, metavar="N", help="Sample N exercises (0 = all)")
    p.add_argument("--arms", default=",".join(ARMS), help=f"Comma-separated subset of {ALL_ARMS}")
    p.add_argument("--runs", type=int, default=1, metavar="N", help="Runs per (exercise, arm) pair")
    p.add_argument("--dry-run", action="store_true", help="Resolve + assemble only; never call the agent")
    p.add_argument("--out", type=Path, default=None, help="Output JSONL path")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--thinking", default=DEFAULT_THINKING)
    p.add_argument("--repo-dir", type=Path, default=CACHE_DIR, help="Local clone of polyglot-benchmark")
    p.add_argument("--test-timeout", type=int, default=180, help="Per-exercise test command timeout (s)")
    p.add_argument("--agent-timeout", type=int, default=600, help="Per-invocation omp timeout (s)")
    p.add_argument(
        "--resume", action="store_true",
        help="Skip (task_id, arm, run_idx) units already recorded in --out. A "
             "`dry-run` row never counts as done; a `skip:` row (missing "
             "toolchain) does, since re-running it on this host can't succeed "
             "either. Default off: without this flag, --out is appended to "
             "from scratch exactly as before.",
    )
    p.add_argument(
        "--jobs", type=int, default=1, metavar="N",
        help="Run N (exercise, arm, run) units concurrently in a thread pool "
             "(the work is subprocess-bound, so threads are correct — no "
             "multiprocessing needed). Default 1 keeps today's exact "
             "sequential behaviour. WARNING: N>1 risks provider rate limits "
             "and CPU contention between concurrently running language test "
             "suites — start low and watch for spurious timeouts.",
    )
    return p.parse_args(argv)


def _process_unit(
    ex: Exercise, arm: str, run_idx: int, model: str, thinking: str,
    ok: bool, reason: str, args: argparse.Namespace, fh, lock: threading.Lock | None,
    state: dict,
) -> None:
    """Run one (exercise, arm, run_idx) unit end to end and append its JSONL
    record. Safe to call from multiple threads concurrently: all shared
    mutable state (the output file and the `printed_prompt` flag) goes
    through `lock`; `make_scratch` needs no lock of its own because its
    directory name already encodes (ex, arm, run_idx) — see main()'s
    docstring note on collision-freedom.
    """
    if not ok:
        emit(fh, lock=lock, task_id=ex.task_id, arm=arm, run_idx=run_idx,
             model=model, thinking=thinking, notes=f"skip: {reason}")
        return

    prompt = build_prompt(ex)

    if args.dry_run:
        with lock or nullcontext():
            if not state["printed_prompt"]:
                print("=" * 72)
                print(f"ASSEMBLED PROMPT — {ex.task_id} [{arm}]")
                print("=" * 72)
                print(prompt)
                print("=" * 72)
                state["printed_prompt"] = True
        emit(fh, lock=lock, task_id=ex.task_id, arm=arm, run_idx=run_idx,
             model=model, thinking=thinking, notes="dry-run")
        return

    run_dir = make_scratch(ex, arm, run_idx)
    work = work_dir(run_dir, ex)
    latency, tokens_in, tokens_out, cost_usd = invoke_omp(
        prompt, arm, work, model, thinking, run_dir, args.agent_timeout
    )
    # A real invocation that reports zero input tokens means the transcript
    # was not found or not parsed, not that the model read nothing. Those
    # rows are unusable: the length-control gate and the mean-tokens_in
    # figure that §7 of docs/BENCHMARKS.md requires are both computed from
    # this field. Fail the whole sweep on the first one rather than spend
    # hours writing rows that cannot support a claim.
    if tokens_in == 0:
        raise RuntimeError(
            f"no usage parsed for {ex.task_id} [{arm}] — session transcript missing or "
            f"unreadable under {run_dir / 'session'}. Refusing to continue: every "
            "subsequent row would be unusable for the length-control gate. Scratch dir "
            "kept for inspection."
        )
    restore_test_files(ex, work)
    try:
        passed, output = run_tests(ex, work, args.test_timeout)
        note = "" if passed else output[-400:]
    except subprocess.TimeoutExpired:
        passed, note = False, "test command timed out"

    emit(fh, lock=lock, task_id=ex.task_id, arm=arm, run_idx=run_idx, passed=passed,
         latency_s=round(latency, 2), model=model, thinking=thinking, notes=note,
         tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=round(cost_usd, 6))
    shutil.rmtree(run_dir, ignore_errors=True)


def main(argv=None) -> int:
    args = parse_args(argv)

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    for a in arms:
        if a not in ALL_ARMS:
            print(f"error: unknown arm {a!r}, expected one of {ALL_ARMS}", file=sys.stderr)
            return 2

    repo_dir = ensure_repo(args.repo_dir)
    exercises = discover_exercises(repo_dir)
    if args.exercises > 0:
        exercises = exercises[: args.exercises]

    toolchains = probe_toolchains()
    print("Toolchain availability:")
    for lang, (ok, reason) in sorted(toolchains.items()):
        print(f"  {lang:12s} {'OK' if ok else f'MISSING ({reason})'}")

    usable = sum(1 for ex in exercises if toolchains[ex.lang][0])
    print(f"\n{len(exercises)} exercise(s) selected, {usable} usable given local toolchains.\n")

    out_path = args.out or default_out_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    SCRATCH_ROOT.mkdir(exist_ok=True)

    # (ex, arm, run_idx) -> make_scratch()'s dir name is exactly
    # f"{lang}__{name}__{arm}__{run_idx}", one string per unit below, so two
    # units never collide on a scratch dir regardless of --jobs.
    units: list[tuple[Exercise, str, int, str, str, bool, str]] = []
    for ex in exercises:
        ok, reason = toolchains[ex.lang]
        for arm in arms:
            model, thinking = effective_model_thinking(arm, args.model, args.thinking)
            for run_idx in range(1, args.runs + 1):
                units.append((ex, arm, run_idx, model, thinking, ok, reason))

    if args.resume:
        completed = load_completed(out_path)
        before = len(units)
        units = filter_resume(units, completed)
        print(f"--resume: {before - len(units)} unit(s) already done, skipping; "
              f"{len(units)} remaining.\n")

    state = {"printed_prompt": False}
    lock = threading.Lock() if args.jobs > 1 else None

    with out_path.open("a") as fh:
        if args.jobs > 1:
            with ThreadPoolExecutor(max_workers=args.jobs) as pool:
                futures = [
                    pool.submit(_process_unit, ex, arm, run_idx, model, thinking, ok, reason,
                                args, fh, lock, state)
                    for ex, arm, run_idx, model, thinking, ok, reason in units
                ]
                for f in futures:
                    f.result()  # re-raise the first worker exception, if any
        else:
            # No pool, no lock: the cheap default path is byte-identical to
            # pre-concurrency behaviour, so it has no new failure modes.
            for ex, arm, run_idx, model, thinking, ok, reason in units:
                _process_unit(ex, arm, run_idx, model, thinking, ok, reason, args, fh, None, state)

    print(f"Wrote {len(units)} record(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
