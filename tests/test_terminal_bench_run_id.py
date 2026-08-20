"""make_run_id() feeds `docker compose -p` through Terminal-Bench's --run-id.

An invalid project name kills every container build *before* the agent runs,
and terminal-bench records that as `unknown_agent_error` — indistinguishable in
results.json from the model genuinely failing the task. So the constraint is
worth a test rather than a comment.
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bench.terminal_bench.run import make_run_id  # noqa: E402

# docker compose: lowercase alphanumerics, hyphens, underscores; must start
# with a letter or number.
COMPOSE_PROJECT_NAME = re.compile(r"\A[a-z0-9][a-z0-9_-]*\Z")


def test_run_id_is_a_valid_docker_compose_project_name():
    now = datetime(2026, 8, 20, 9, 7, 9, tzinfo=timezone.utc)
    for arm in ("jspace", "none", "placebo"):
        run_id = make_run_id(arm, now)
        assert COMPOSE_PROJECT_NAME.match(run_id), run_id


def test_run_id_rejects_the_iso_stamp_that_broke_the_smoke_test():
    """Regression lock: the original f"{arm}-%Y%m%dT%H%M%SZ" produced
    `none-20260820T090709Z`, which compose refused."""
    now = datetime(2026, 8, 20, 9, 7, 9, tzinfo=timezone.utc)
    assert "T" not in make_run_id("none", now)
    assert "Z" not in make_run_id("none", now)
    assert make_run_id("none", now) == "none-20260820-090709"


def test_run_ids_differ_by_second_so_runs_do_not_collide():
    a = make_run_id("jspace", datetime(2026, 8, 20, 9, 7, 9, tzinfo=timezone.utc))
    b = make_run_id("jspace", datetime(2026, 8, 20, 9, 7, 10, tzinfo=timezone.utc))
    assert a != b
