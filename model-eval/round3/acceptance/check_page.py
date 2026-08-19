#!/usr/bin/env python3
"""Objective acceptance for round-3 landing pages. Usage: check_page.py <WORKDIR>

Checks artifacts and page content. Browser rendering (console errors, 3D actually
visible) is scored separately by the evaluator via screenshots.
"""
import re
import sys
from pathlib import Path

FACTS = ["J-Space", "V3.6", "Apache", "SKILL.md", "Zenodo", "DeepSeek",
         "workspace", "inference", "modules", "HLE"]

wd = Path(sys.argv[1])
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


site = wd / "site" / "index.html"
check("site/index.html exists", site.exists())
html = site.read_text(errors="replace") if site.exists() else ""
check("page > 8KB", len(html) > 8000, f"{len(html)} bytes")
check("viewport meta", 'name="viewport"' in html)
check("3D present (three/webgl/canvas)",
      re.search(r"three(\.min)?\.js|three\.module|webgl|<canvas|WebGLRenderer", html, re.I))
check("no lorem ipsum", "lorem" not in html.lower())
check("no placeholder img services",
      not re.search(r"placehold|picsum|unsplash|dummyimage|via\.placeholder", html, re.I))
found = [f for f in FACTS if f.lower() in html.lower()]
check(">= 5 real facts from source", len(found) >= 5, f"found: {found}")
check("<title> set", bool(re.search(r"<title>[^<]{4,}</title>", html)))

notes = wd / "NOTES.md"
check("NOTES.md exists", notes.exists())
if notes.exists():
    urls = re.findall(r"https?://\S+", notes.read_text(errors="replace"))
    check(">= 3 fetched source URLs in NOTES", len(set(urls)) >= 3, f"{len(set(urls))} urls")
check("PLAN.md exists", (wd / "PLAN.md").exists())
check("VERIFY.md exists", (wd / "VERIFY.md").exists())

fails = [n for n, ok, _ in results if not ok]
for n, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {n}" + (f"  ({detail})" if detail else ""))
print(f"\n{len(results) - len(fails)}/{len(results)} checks passed")
sys.exit(1 if fails else 0)
