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
