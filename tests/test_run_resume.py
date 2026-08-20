"""Tests for the --resume and --jobs infrastructure in bench/aider_polyglot/run.py.

No agent invocation happens here — these drive load_completed(), filter_resume(),
and emit() directly, which is exactly what the acceptance criteria ask for.
"""
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bench.aider_polyglot.run import (  # noqa: E402
    _session_dispatch,
    emit,
    filter_resume,
    load_completed,
)


@dataclass(frozen=True)
class FakeEx:
    """Minimal stand-in for Exercise — filter_resume only needs .task_id."""
    task_id: str


# --------------------------------------------------------------------------
# load_completed
# --------------------------------------------------------------------------


def test_load_completed_missing_file_is_empty(tmp_path):
    assert load_completed(tmp_path / "nope.jsonl") == set()


def test_load_completed_dry_run_row_does_not_count(tmp_path):
    out = tmp_path / "out.jsonl"
    out.write_text(json.dumps({"task_id": "python/acronym", "arm": "jspace", "run_idx": 1,
                                "notes": "dry-run"}) + "\n")
    assert load_completed(out) == set()


def test_load_completed_real_row_counts(tmp_path):
    out = tmp_path / "out.jsonl"
    real = {"task_id": "python/acronym", "arm": "jspace", "run_idx": 1, "passed": True, "notes": ""}
    out.write_text(json.dumps(real) + "\n")
    assert load_completed(out) == {("python/acronym", "jspace", 1)}


def test_load_completed_skip_row_counts():
    """A `skip: <reason>` row (missing toolchain) is a real record — retrying
    it on this host can't succeed either, so --resume must treat it as done."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "out.jsonl"
        skip = {"task_id": "cpp/leap", "arm": "none", "run_idx": 1, "notes": "skip: no cmake"}
        out.write_text(json.dumps(skip) + "\n")
        assert load_completed(out) == {("cpp/leap", "none", 1)}


def test_load_completed_mixed_file_and_malformed_trailing_line(tmp_path):
    out = tmp_path / "out.jsonl"
    lines = [
        json.dumps({"task_id": "python/acronym", "arm": "jspace", "run_idx": 1, "notes": ""}),
        json.dumps({"task_id": "python/bowling", "arm": "jspace", "run_idx": 1, "notes": "dry-run"}),
        json.dumps({"task_id": "go/leap", "arm": "none", "run_idx": 2, "notes": "skip: no go"}),
        '{"task_id": "truncated by a kill -9',  # not valid JSON — must not raise
    ]
    out.write_text("\n".join(lines) + "\n")
    assert load_completed(out) == {
        ("python/acronym", "jspace", 1),
        ("go/leap", "none", 2),
    }


# --------------------------------------------------------------------------
# filter_resume — "--resume skipping the right units"
# --------------------------------------------------------------------------


def test_filter_resume_skips_exactly_completed_units():
    ex_a, ex_b = FakeEx("python/acronym"), FakeEx("go/leap")
    units = [
        (ex_a, "jspace", 1, "model", "thinking", True, ""),
        (ex_a, "none", 1, "model", "thinking", True, ""),
        (ex_b, "jspace", 1, "model", "thinking", True, ""),
        (ex_b, "jspace", 2, "model", "thinking", True, ""),
    ]
    completed = {("python/acronym", "jspace", 1), ("go/leap", "jspace", 1)}

    remaining = filter_resume(units, completed)

    assert remaining == [
        (ex_a, "none", 1, "model", "thinking", True, ""),
        (ex_b, "jspace", 2, "model", "thinking", True, ""),
    ]


def test_filter_resume_no_completed_keeps_everything():
    ex_a = FakeEx("python/acronym")
    units = [(ex_a, "jspace", 1, "m", "t", True, "")]
    assert filter_resume(units, set()) == units


# --------------------------------------------------------------------------
# emit() thread safety — concurrent writers, every line still valid JSON
# --------------------------------------------------------------------------


def test_emit_concurrent_writes_produce_valid_jsonl(tmp_path):
    out = tmp_path / "concurrent.jsonl"
    lock = threading.Lock()
    n_writers = 8
    n_per_writer = 25

    def write_many(worker_id):
        with out.open("a") as fh:
            for i in range(n_per_writer):
                emit(fh, lock=lock, task_id=f"w{worker_id}/{i}", arm="jspace", run_idx=1,
                     notes="dry-run")

    # ponytail: one open() per worker rather than a single shared handle —
    # matches how main()'s "with out_path.open('a')" is used by every
    # ThreadPoolExecutor worker in practice (they share one fh); opening
    # per-worker here is a stricter test since 'a' mode + os-level append is
    # what actually has to be safe under concurrent writers.
    with ThreadPoolExecutor(max_workers=n_writers) as pool:
        futures = [pool.submit(write_many, i) for i in range(n_writers)]
        for f in futures:
            f.result()

    lines = out.read_text().splitlines()
    assert len(lines) == n_writers * n_per_writer
    seen = set()
    for line in lines:
        rec = json.loads(line)  # raises if any write interleaved / corrupted a line
        seen.add((rec["task_id"], rec["arm"], rec["run_idx"]))
    assert len(seen) == n_writers * n_per_writer  # every record intact, none merged/lost


def test_emit_concurrent_writes_shared_filehandle(tmp_path):
    """Same as above but with one shared fh (main()'s actual usage shape)."""
    out = tmp_path / "shared.jsonl"
    lock = threading.Lock()
    n_writers = 6
    n_per_writer = 20

    with out.open("a") as fh:
        def write_many(worker_id):
            for i in range(n_per_writer):
                emit(fh, lock=lock, task_id=f"w{worker_id}/{i}", arm="none", run_idx=1, notes="")

        with ThreadPoolExecutor(max_workers=n_writers) as pool:
            futures = [pool.submit(write_many, i) for i in range(n_writers)]
            for f in futures:
                f.result()

    lines = out.read_text().splitlines()
    assert len(lines) == n_writers * n_per_writer
    for line in lines:
        json.loads(line)


# --------------------------------------------------------------------------
# _session_dispatch — the Round 3 fallback detector
# --------------------------------------------------------------------------


def _write_transcript(tmp_path, records) -> Path:
    p = tmp_path / "t.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in records))
    return p


def test_session_dispatch_reads_model_and_thinking(tmp_path):
    p = _write_transcript(tmp_path, [
        {"type": "session_start", "cwd": "/x"},
        {"type": "model_change", "model": "kimi-code/k3", "resolvedModelIsFallback": False},
        {"type": "thinking_level_change", "thinkingLevel": "max"},
        {"type": "message", "message": {"usage": {"input": 10}}},
    ])
    assert _session_dispatch(p) == ("kimi-code/k3", False, "max")


def test_session_dispatch_flags_fallback(tmp_path):
    # The Round 3 failure: asked for one model, harness resolved another.
    p = _write_transcript(tmp_path, [
        {"type": "model_change", "model": "anthropic/claude-sonnet-5",
         "resolvedModelIsFallback": True},
        {"type": "thinking_level_change", "thinkingLevel": "medium"},
    ])
    model, is_fallback, thinking = _session_dispatch(p)
    assert (model, is_fallback, thinking) == ("anthropic/claude-sonnet-5", True, "medium")


def test_session_dispatch_tolerates_missing_records_and_bad_lines(tmp_path):
    p = tmp_path / "t.jsonl"
    p.write_text('{"type":"session_start"}\nnot json at all\n')
    assert _session_dispatch(p) == (None, False, None)


def test_only_selects_named_tasks_and_rejects_unknown(tmp_path):
    """--only is purposive selection, so both halves matter: the named ids
    must be exactly what runs, and a typo must fail loudly rather than
    silently running a different set."""
    import subprocess

    cache = REPO_ROOT / "bench" / "aider_polyglot" / ".cache" / "polyglot-benchmark"
    if not cache.is_dir():
        import pytest
        pytest.skip("polyglot-benchmark not cached; --only needs discovery")

    def run(only):
        return subprocess.run(
            [sys.executable, "bench/aider_polyglot/run.py", "--dry-run", "--only", only,
             "--arms", "ds-plain", "--out", str(tmp_path / "o.jsonl")],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )

    ok = run("rust/acronym,python/list-ops")
    assert ok.returncode == 0, ok.stderr
    assert "--only: 2 exercise(s)" in ok.stdout

    bad = run("rust/acronym,python/does-not-exist")
    assert bad.returncode == 2
    assert "python/does-not-exist" in bad.stderr
