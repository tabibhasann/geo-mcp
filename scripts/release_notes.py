#!/usr/bin/env python3
"""Generate draft release notes from merged PRs since the last tag.

Usage:
    python scripts/release_notes.py [--since-tag v0.3.0] [--output NOTES.md]

Requires ``gh`` (GitHub CLI) to be authenticated.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_last_tag() -> str | None:
    try:
        return run(["git", "describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def get_merged_prs(since_tag: str | None) -> list[dict]:
    cmd = [
        "gh",
        "pr",
        "list",
        "--state",
        "merged",
        "--limit",
        "100",
        "--json",
        "number,title,author,mergedAt",
    ]
    if since_tag:
        cmd += ["--search", f"merged:>={since_tag}"]
    try:
        data = json.loads(run(cmd))
    except (json.JSONDecodeError, subprocess.CalledProcessError):
        return []
    return [
        {
            "number": str(item.get("number", "")),
            "title": item.get("title", ""),
            "author": (item.get("author") or {}).get("login", ""),
            "merged_at": item.get("mergedAt", ""),
        }
        for item in data
    ]


def categorize(prs: list[dict]) -> dict[str, list[dict]]:
    categories: dict[str, list[dict]] = {
        "Breaking Changes": [],
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Maintenance": [],
    }
    for pr in prs:
        title = pr["title"]
        if title.startswith("BREAKING") or title.startswith("!"):
            categories["Breaking Changes"].append(pr)
        elif title.startswith("feat") or title.startswith("add"):
            categories["Features"].append(pr)
        elif title.startswith("fix") or title.startswith("bug"):
            categories["Bug Fixes"].append(pr)
        elif title.startswith("docs") or title.startswith("doc"):
            categories["Documentation"].append(pr)
        else:
            categories["Maintenance"].append(pr)
    return categories


def generate_notes(prs: list[dict], version: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"## [{version}] - {today}", ""]

    cats = categorize(prs)
    for cat_name, items in cats.items():
        if not items:
            continue
        lines.append(f"### {cat_name}")
        for pr in items:
            lines.append(f"- {pr['title']} (#{pr['number']}) @{pr['author']}")
        lines.append("")

    if not prs:
        lines.append("_No merged PRs since last tag._")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate draft release notes.")
    parser.add_argument("--since-tag", default=None, help="Git tag to generate notes from")
    parser.add_argument("--version", default="unreleased", help="Version label for notes")
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    since = args.since_tag or get_last_tag()
    prs = get_merged_prs(since)
    notes = generate_notes(prs, args.version)

    if args.output:
        with open(args.output, "w") as f:
            f.write(notes + "\n")
        print(f"Written to {args.output}")
    else:
        print(notes)


if __name__ == "__main__":
    main()
