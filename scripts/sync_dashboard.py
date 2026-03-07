#!/usr/bin/env python3
"""Sync Shiro-Nexus project dashboard from GitHub repo metadata.

Usage:
  python scripts/sync_dashboard.py

Optional environment:
  GITHUB_TOKEN=ghp_xxx  (recommended to avoid low unauthenticated rate limits)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "projects.json"
STATUS_PATH = ROOT / "generated" / "STATUS.md"
SHOWCASE_PATH = ROOT / "generated" / "SHOWCASE.md"


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

    if "_error" in meta:
        return {
            "name": project["name"],
            "repo": repo,
            "category": project.get("category", "-"),
            "criticality": project.get("criticality", "-"),
            "status": "ERROR",
            "visibility": "-",
            "branch": "-",
            "last_push": "-",
            "stars": "-",
            "issues": "-",
            "health": meta["_error"],
            "local_path": project.get("local_path", ""),
            "description": project.get("description", ""),
            "repo_url": f"https://github.com/{owner}/{repo}",
            "language": "-",
            "topics": [],
            "homepage": "",
            "forks": 0,
            "readme_url": f"https://github.com/{owner}/{repo}#readme",
        }

    status = status_badge(bool(meta.get("archived", False)), meta.get("pushed_at"))

    return {
        "name": project["name"],
        "repo": repo,
        "category": project.get("category", "-"),
        "criticality": project.get("criticality", "-"),
        "status": status,
        "visibility": "private" if meta.get("private") else "public",
        "branch": meta.get("default_branch", "-"),
        "last_push": fmt_iso(meta.get("pushed_at")),
        "stars": meta.get("stargazers_count", 0),
        "issues": meta.get("open_issues_count", 0),
        "health": "ok",
        "local_path": project.get("local_path", ""),
        "description": project.get("description", ""),
        "repo_url": meta.get("html_url", f"https://github.com/{owner}/{repo}"),
        "language": meta.get("language") or "-",
        "topics": meta.get("topics", []),
        "homepage": meta.get("homepage") or "",
        "forks": meta.get("forks_count", 0),
        "readme_url": f"{meta.get('html_url', f'https://github.com/{owner}/{repo}') }#readme",
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
    for r in rows:
        if r["health"] != "ok":
            lines.append(f"- {r['name']}: {r['health']}")

    if lines[-1] == "":
        lines.append("- No API errors detected during sync.")

    lines.extend([
        "",
        "## Operations",
        "",
        "Refresh dashboard:",
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
        "## How To Navigate",
        "",
        "1. Start with **Shiro-Nexus** as control plane.",
        "2. Move to product repos (`nba-os`, `project-hub`) for platform systems.",
        "3. Explore R&D repos (`Research-Vault`, `MyTorch-MNIST-Elite`) for research/engine work.",
        "",
    ]

    for category in categories:
        lines.extend([f"## {category}", ""])
        category_rows = [r for r in rows if r["category"] == category]
        category_rows.sort(key=lambda r: (r["criticality"], r["name"]))
        for r in category_rows:
            topics = ", ".join(r["topics"]) if r["topics"] else "-"
            homepage = r["homepage"] if r["homepage"] else "-"
            lines.extend(
                [
                    f"### [{r['name']}]({r['repo_url']})",
                    f"- Purpose: {r['description'] or 'No description provided.'}",
                    f"- Status: **{r['status']}** | Criticality: **{r['criticality']}** | Visibility: **{r['visibility']}**",
                    f"- Tech signal: Primary language **{r['language']}** | Stars **{r['stars']}** | Forks **{r['forks']}** | Open issues **{r['issues']}**",
                    f"- Topics: {topics}",
                    f"- Default branch: `{r['branch']}` | Last push: {r['last_push']}",
                    f"- README: [Open]({r['readme_url']})",
                    f"- Homepage: {homepage}",
                    "",
                ]
            )

    lines.extend(
        [
            "## Control-Plane Notes",
            "",
            "- Data is fetched from GitHub API by `scripts/sync_dashboard.py`.",
            "- For private repositories, metadata is visible if your token has access.",
            "- No credentials are stored in repository files.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"Missing config file: {CONFIG_PATH}", file=sys.stderr)
        return 1

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    owner = data["owner"]
    projects = data["projects"]

    rows = [build_row(owner, project) for project in projects]
    rows.sort(key=lambda r: (r["criticality"], r["name"]))

    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(render_status(rows), encoding="utf-8")
    SHOWCASE_PATH.write_text(render_showcase(rows), encoding="utf-8")
    print(f"Wrote {STATUS_PATH}")
    print(f"Wrote {SHOWCASE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
