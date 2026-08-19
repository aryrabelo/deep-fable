#!/usr/bin/env python3
"""Held-out deterministic checker for Round 4 (ANSWERS.md format + sourcing).

Offline by design: it checks structure, verdict vocabulary, evidence count, and
primary-source presence. It does NOT judge whether the verdict is factually right --
that is done separately against the reference cell.

Usage: check_answers.py <cell-dir>   ->   prints PASS/FAIL lines, exits non-zero on any FAIL.
"""
import re
import sys
from pathlib import Path

QUESTIONS = {
    "Q1": ("Gemini CLI", ("gemini", "google")),
    "Q2": ("Cursor", ("cursor",)),
    "Q3": ("Codex CLI", ("codex", "openai")),
    "Q4": ("OpenCode", ("opencode", "sst")),
}
VERDICTS = {"YES", "NO", "INCONCLUSIVE"}
CONFIDENCES = {"high", "medium", "low"}
PLACEHOLDERS = ("TBD", "TODO", "N/A", "lorem", "FIXME", "<url>")
URL_RE = re.compile(r"https?://[^\s)\]]+")


def _sections(text: str) -> dict[str, str]:
    """Split on '## Qn' headings, tolerating any trailing heading text."""
    out: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(Q[1-4])\b", line.strip())
        if m:
            current = m.group(1)
            out[current] = ""
            continue
        if current:
            out[current] += line + "\n"
    return out


def _field(body: str, name: str) -> str:
    m = re.search(rf"^\*\*{name}:\*\*\s*(.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def check(cell_dir: Path) -> list[tuple[bool, str]]:
    results: list[tuple[bool, str]] = []

    def ok(cond: bool, label: str) -> bool:
        results.append((bool(cond), label))
        return bool(cond)

    answers = cell_dir / "ANSWERS.md"
    if not ok(answers.is_file(), "ANSWERS.md exists"):
        return results

    text = answers.read_text(errors="ignore")
    sections = _sections(text)
    ok(not any(p in text for p in PLACEHOLDERS), "no placeholder tokens")

    for qid, (tool, primary_hints) in QUESTIONS.items():
        body = sections.get(qid)
        if not ok(body is not None, f"{qid} section present ({tool})"):
            continue

        verdict = _field(body, "Verdict")
        ok(verdict in VERDICTS, f"{qid} verdict in {sorted(VERDICTS)} (got {verdict!r})")
        ok(_field(body, "Confidence").lower() in CONFIDENCES, f"{qid} confidence valid")
        ok(len(_field(body, "Checked")) >= 3, f"{qid} states what it checked against")
        ok(len(_field(body, "Impact on adapter")) >= 10, f"{qid} states adapter impact")

        urls = URL_RE.findall(body)
        distinct = {u.rstrip(".,);") for u in urls}
        ok(len(distinct) >= 2, f"{qid} has >= 2 distinct evidence URLs (got {len(distinct)})")
        ok(
            any(h in u.lower() for u in distinct for h in primary_hints),
            f"{qid} cites a primary source for {tool}",
        )

    return results


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_answers.py <cell-dir>", file=sys.stderr)
        return 2
    results = check(Path(sys.argv[1]))
    for passed, label in results:
        print(f"{'PASS' if passed else 'FAIL'}  {label}")
    failed = sum(1 for passed, _ in results if not passed)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
