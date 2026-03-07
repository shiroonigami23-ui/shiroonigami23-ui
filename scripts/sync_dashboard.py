#!/usr/bin/env python3
"""Sync Shiro-Nexus project docs from GitHub metadata.

Generated outputs:
- generated/STATUS.md
- generated/SHOWCASE.md
- generated/ARCHITECTURE_CARDS.md
- README.md dynamic portfolio block (between markers)

Usage:
  python scripts/sync_dashboard.py

Optional environment:
  GITHUB_TOKEN=ghp_xxx
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "projects.json"
README_PATH = ROOT / "README.md"
STATUS_PATH = ROOT / "generated" / "STATUS.md"
SHOWCASE_PATH = ROOT / "generated" / "SHOWCASE.md"
CARDS_PATH = ROOT / "generated" / "ARCHITECTURE_CARDS.md"

README_START = "<!-- AUTO_PORTFOLIO_START -->"
README_END = "<!-- AUTO_PORTFOLIO_END -->"


def github_get(url: str) -> Dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "shiro-nexus-sync-script",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        return {"_error": f"HTTP {exc.code}", "_url": url}
    except URLError as exc:
        return {"_error": f"Network error: {exc.reason}", "_url": url}


def fmt_iso(ts: str | None) -> str:
    if not ts:
        return "-"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return ts


def status_badge(archived: bool, pushed_at: str | None) -> str:
    if archived:
        return "ARCHIVED"
    if not pushed_at:
        return "UNKNOWN"
    try:
        dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - dt).days
        if age_days <= 14:
            return "ACTIVE"
        if age_days <= 60:
            return "WARM"
        return "STALE"
    except ValueError:
        return "UNKNOWN"


def build_row(owner: str, project: Dict[str, Any]) -> Dict[str, Any]:
    repo = project["repo"]
    meta = github_get(f"https://api.github.com/repos/{owner}/{repo}")

    base = {
        "name": project["name"],
        "repo": repo,
        "category": project.get("category", "-"),
        "criticality": project.get("criticality", "-"),
        "description": project.get("description", ""),
        "stack": project.get("stack", "-"),
        "audience": project.get("audience", "-"),
        "local_path": project.get("local_path", ""),
        "repo_url": f"https://github.com/{owner}/{repo}",
        "readme_url": f"https://github.com/{owner}/{repo}#readme",
    }

    if "_error" in meta:
        return {
            **base,
            "status": "ERROR",
            "visibility": "-",
            "branch": "-",
            "last_push": "-",
            "stars": "-",
            "issues": "-",
            "forks": "-",
            "language": "-",
            "topics": [],
            "homepage": "",
            "health": meta["_error"],
        }

    return {
        **base,
        "status": status_badge(bool(meta.get("archived", False)), meta.get("pushed_at")),
        "visibility": "private" if meta.get("private") else "public",
        "branch": meta.get("default_branch", "-"),
        "last_push": fmt_iso(meta.get("pushed_at")),
        "stars": meta.get("stargazers_count", 0),
        "issues": meta.get("open_issues_count", 0),
        "forks": meta.get("forks_count", 0),
        "language": meta.get("language") or "-",
        "topics": meta.get("topics", []),
        "homepage": meta.get("homepage") or "",
        "health": "ok",
    }


def render_status(rows: List[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Shiro Nexus Status Dashboard",
        "",
        f"Generated: {now}",
        "",
        "## Portfolio Health",
        "",
        "| Project | Category | Criticality | Status | Visibility | Branch | Last Push | Stars | Open Issues |",
        "|---|---|---|---|---|---|---|---:|---:|",
    ]

    for r in rows:
        lines.append(
            f"| [{r['name']}]({r['repo_url']}) | {r['category']} | {r['criticality']} | {r['status']} | {r['visibility']} | {r['branch']} | {r['last_push']} | {r['stars']} | {r['issues']} |"
        )

    lines.extend(["", "## Local Linking", ""])
    for r in rows:
        path = r["local_path"] or "(not configured)"
        lines.append(f"- **{r['name']}**: `{path}`")

    lines.extend(["", "## Notes", ""])
    errors = [r for r in rows if r["health"] != "ok"]
    if not errors:
        lines.append("- No API errors detected during sync.")
    else:
        for r in errors:
            lines.append(f"- {r['name']}: {r['health']}")

    lines.extend([
        "",
        "## Operations",
        "",
        "```powershell",
        "python scripts/sync_dashboard.py",
        "```",
    ])
    return "\n".join(lines) + "\n"


def render_showcase(rows: List[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    categories = sorted({r["category"] for r in rows})
    lines = [
        "# Shiro Nexus Project Showcase",
        "",
        "Visitor-friendly map of the Shiro engineering ecosystem.",
        "",
        f"Generated: {now}",
        "",
    ]

    for category in categories:
        lines.extend([f"## {category}", ""])
        subset = sorted([r for r in rows if r["category"] == category], key=lambda r: (r["criticality"], r["name"]))
        for r in subset:
            topics = ", ".join(r["topics"]) if r["topics"] else "-"
            homepage = r["homepage"] if r["homepage"] else "-"
            lines.extend([
                f"### [{r['name']}]({r['repo_url']})",
                f"- Purpose: {r['description'] or 'No description provided.'}",
                f"- Audience: {r['audience']}",
                f"- Status: **{r['status']}** | Criticality: **{r['criticality']}** | Visibility: **{r['visibility']}**",
                f"- Stack: {r['stack']}",
                f"- Tech signal: language **{r['language']}** | stars **{r['stars']}** | forks **{r['forks']}** | open issues **{r['issues']}**",
                f"- Topics: {topics}",
                f"- Last push: {r['last_push']} | Branch: `{r['branch']}`",
                f"- README: [Open]({r['readme_url']})",
                f"- Homepage: {homepage}",
                "",
            ])

    lines.extend([
        "## Security Note",
        "",
        "- Generated content does not embed tokens or credentials.",
        "- Use environment variable `GITHUB_TOKEN` only during runtime.",
    ])
    return "\n".join(lines) + "\n"


def render_cards(rows: List[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Architecture Cards",
        "",
        f"Generated: {now}",
        "",
        "Compact architecture snapshots for each tracked repository.",
        "",
    ]

    for r in sorted(rows, key=lambda x: (x["category"], x["name"])):
        lines.extend([
            f"## {r['name']}",
            f"- Repo: {r['repo_url']}",
            f"- Category: {r['category']} | Criticality: {r['criticality']} | Status: {r['status']}",
            f"- Primary language: {r['language']} | Visibility: {r['visibility']}",
            f"- Purpose: {r['description']}",
            f"- Stack: {r['stack']}",
            f"- Audience: {r['audience']}",
            "- System Flow:",
            "  1. Input/Data sources enter project workflows.",
            "  2. Core logic/services process and produce outputs.",
            "  3. Outputs are exposed via UI/docs/APIs for users and collaborators.",
            "",
        ])

    return "\n".join(lines) + "\n"


def render_readme_block(rows: List[Dict[str, Any]]) -> str:
    lines = [
        README_START,
        "## Live Portfolio Snapshot",
        "",
        "| Project | Category | Status | Last Push |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| [{r['name']}]({r['repo_url']}) | {r['category']} | {r['status']} | {r['last_push']} |")
    lines.extend([
        "",
        "Generated docs:",
        "- [Status Dashboard](./generated/STATUS.md)",
        "- [Project Showcase](./generated/SHOWCASE.md)",
        "- [Architecture Cards](./generated/ARCHITECTURE_CARDS.md)",
        README_END,
    ])
    return "\n".join(lines)


def patch_readme(readme_text: str, block: str) -> str:
    pattern = re.compile(re.escape(README_START) + r".*?" + re.escape(README_END), re.S)
    if pattern.search(readme_text):
        return pattern.sub(block, readme_text)
    suffix = "\n\n" if not readme_text.endswith("\n") else "\n"
    return readme_text + suffix + block + "\n"


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"Missing config file: {CONFIG_PATH}", file=sys.stderr)
        return 1

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    owner = data["owner"]
    projects = data["projects"]

    rows = [build_row(owner, p) for p in projects]
    rows.sort(key=lambda r: (r["criticality"], r["name"]))

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(render_status(rows), encoding="utf-8")
    SHOWCASE_PATH.write_text(render_showcase(rows), encoding="utf-8")
    CARDS_PATH.write_text(render_cards(rows), encoding="utf-8")

    readme = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else "# Shiro Nexus\n"
    README_PATH.write_text(patch_readme(readme, render_readme_block(rows)), encoding="utf-8")

    print(f"Wrote {STATUS_PATH}")
    print(f"Wrote {SHOWCASE_PATH}")
    print(f"Wrote {CARDS_PATH}")
    print(f"Updated {README_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
