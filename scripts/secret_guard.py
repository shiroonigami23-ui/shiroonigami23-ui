#!/usr/bin/env python3
"""Lightweight secret guard for Shiro-Nexus.

Scans tracked text files for common credential patterns.
Returns non-zero if potential leaks are found.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = [
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub Token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("OpenAI Key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("Private Key Block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Password Assignment", re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9!@#$%^&*()_+\-={}:;,.?]{8,}")),
]

TEXT_SUFFIXES = {".md", ".txt", ".json", ".yml", ".yaml", ".env", ".py", ".ts", ".tsx", ".js", ".php", ".ini"}


def tracked_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    files = []
    for rel in out.splitlines():
        p = ROOT / rel
        if p.suffix.lower() in TEXT_SUFFIXES and p.is_file():
            files.append(p)
    return files


def main() -> int:
    findings = []
    for p in tracked_files():
        text = p.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in PATTERNS:
            if pattern.search(text):
                findings.append((label, p))

    if not findings:
        print("Secret guard: OK (no obvious credential patterns found)")
        return 0

    print("Secret guard: potential leaks detected")
    for label, path in findings:
        print(f"- {label}: {path.relative_to(ROOT)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
