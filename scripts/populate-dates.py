#!/usr/bin/env python3
"""Set Start Date / End Date on every Project (v2) item based on Sprint label.

Mapping derived from the revised Sprint Calendar (2026-05-29):
  sprint:1 -> 2026-06-01 .. 2026-06-12
  sprint:2 -> 2026-06-15 .. 2026-06-26
  sprint:3 -> 2026-06-29 .. 2026-07-10
  sprint:4 -> 2026-07-13 .. 2026-07-24
  sprint:5 -> 2026-07-27 .. 2026-08-01
"""
from __future__ import annotations

import json
import subprocess
import sys

REPO = "david-kokkilic-sweetspot/sweetspot-platform"
OWNER = "david-kokkilic-sweetspot"
PROJECT_NUMBER = "1"
PROJECT_ID = "PVT_kwHOENN7U84BZMPv"

START_FIELD_ID = "PVTF_lAHOENN7U84BZMPvzhUM0rM"
END_FIELD_ID = "PVTF_lAHOENN7U84BZMPvzhUM0rQ"

SPRINT_DATES = {
    "1": ("2026-06-01", "2026-06-12"),
    "2": ("2026-06-15", "2026-06-26"),
    "3": ("2026-06-29", "2026-07-10"),
    "4": ("2026-07-13", "2026-07-24"),
    "5": ("2026-07-27", "2026-08-01"),
}


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"FAILED: gh {' '.join(args)}\n{r.stderr}\n")
        sys.exit(1)
    return r.stdout.strip()


def main():
    # Need the Project item IDs paired with the underlying issue numbers and labels.
    # Issue labels come from the repo; item-issue mapping comes from the project.
    issues = json.loads(gh("issue", "list", "--repo", REPO, "--limit", "200",
                            "--state", "all", "--json", "number,labels"))
    issue_sprint = {}
    for i in issues:
        for lab in i["labels"]:
            if lab["name"].startswith("sprint:"):
                issue_sprint[i["number"]] = lab["name"].split(":", 1)[1]
                break

    items = json.loads(gh("project", "item-list", PROJECT_NUMBER,
                          "--owner", OWNER, "--format", "json", "--limit", "200"))["items"]
    print(f"Setting dates on {len(items)} items...")

    skipped = 0
    for it in items:
        item_id = it["id"]
        content = it.get("content", {})
        issue_no = content.get("number")
        title = content.get("title", "?")
        if not issue_no:
            print(f"  skip (no issue): {title}")
            skipped += 1
            continue
        sprint = issue_sprint.get(issue_no)
        if not sprint or sprint not in SPRINT_DATES:
            print(f"  skip #{issue_no} (no sprint label): {title}")
            skipped += 1
            continue
        start, end = SPRINT_DATES[sprint]
        gh("project", "item-edit",
           "--id", item_id, "--project-id", PROJECT_ID,
           "--field-id", START_FIELD_ID, "--date", start)
        gh("project", "item-edit",
           "--id", item_id, "--project-id", PROJECT_ID,
           "--field-id", END_FIELD_ID, "--date", end)
        print(f"  #{issue_no} [{start} → {end}] {title}")

    print(f"\nDone. {len(items) - skipped} updated, {skipped} skipped.")


if __name__ == "__main__":
    main()
