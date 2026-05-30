#!/usr/bin/env python3
"""Set Start Date / End Date on every Project (v2) item with intra-sprint scheduling.

Epic   -> spans the full sprint (overarching bar).
Story  -> spans min(task.start)..max(task.end) of its tasks.
Task   -> distributed chronologically within the sprint's business days,
          ordered by task ID, so the Roadmap shows a real timeline rather
          than every task on the same bar.

Sprint business days (Mon-Fri, weekends skipped):
  sprint:1 -> Jun  1-12 (10 days)   Sprint 1
  sprint:2 -> Jun 15-26 (10 days)   Sprint 2
  sprint:3 -> Jun 29 - Jul 10 (10)  Sprint 3
  sprint:4 -> Jul 13-24 (10 days)   Sprint 4
  sprint:5 -> Jul 27-31 (5 days)    Sprint 5 (Aug 1 Sat = dev cutoff, non-working)
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys

REPO = "david-kokkilic-sweetspot/sweetspot-platform"
OWNER = "david-kokkilic-sweetspot"
PROJECT_NUMBER = "1"
PROJECT_ID = "PVT_kwHOENN7U84BZMPv"

START_FIELD_ID = "PVTF_lAHOENN7U84BZMPvzhUM0rM"
END_FIELD_ID = "PVTF_lAHOENN7U84BZMPvzhUM0rQ"

SPRINTS: dict[str, tuple[dt.date, dt.date]] = {
    "1": (dt.date(2026, 6, 1),  dt.date(2026, 6, 12)),
    "2": (dt.date(2026, 6, 15), dt.date(2026, 6, 26)),
    "3": (dt.date(2026, 6, 29), dt.date(2026, 7, 10)),
    "4": (dt.date(2026, 7, 13), dt.date(2026, 7, 24)),
    "5": (dt.date(2026, 7, 27), dt.date(2026, 7, 31)),
}

ID_PAT = re.compile(r"^(Epic|Story|Task)\s+(\d+(?:\.\d+){0,2}):")


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(f"FAILED: gh {' '.join(args)}\n{r.stderr}\n")
        sys.exit(1)
    return r.stdout.strip()


def business_days(start: dt.date, end: dt.date) -> list[dt.date]:
    days, d = [], start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    return days


def parse_issue_meta(title: str, labels: list[dict]) -> dict:
    m = ID_PAT.match(title)
    if not m:
        return {}
    kind, id_str = m.group(1), m.group(2)
    parts = tuple(int(p) for p in id_str.split("."))
    meta = {"kind": kind, "id_str": id_str, "id_tuple": parts, "epic": str(parts[0])}
    if kind == "Story":
        meta["story_id"] = id_str
    elif kind == "Task":
        meta["story_id"] = f"{parts[0]}.{parts[1]}"
    for lab in labels:
        n = lab["name"]
        if n.startswith("sprint:"):
            meta["sprint"] = n.split(":", 1)[1]
            break
    return meta


def schedule(issues: list[dict]) -> dict[int, tuple[dt.date, dt.date]]:
    """Return issue_number -> (start, end)."""
    by_sprint_tasks: dict[str, list[dict]] = {s: [] for s in SPRINTS}
    by_sprint_stories: dict[str, list[dict]] = {s: [] for s in SPRINTS}
    epics: list[dict] = []

    for i in issues:
        meta = i.get("_meta", {})
        if not meta:
            continue
        s = meta.get("sprint")
        if meta["kind"] == "Task" and s in by_sprint_tasks:
            by_sprint_tasks[s].append(i)
        elif meta["kind"] == "Story" and s in by_sprint_stories:
            by_sprint_stories[s].append(i)
        elif meta["kind"] == "Epic":
            epics.append(i)

    out: dict[int, tuple[dt.date, dt.date]] = {}

    # Tasks: distribute within sprint business days in ID order.
    for sprint, tasks in by_sprint_tasks.items():
        if not tasks:
            continue
        days = business_days(*SPRINTS[sprint])
        n_days = len(days)
        n_tasks = len(tasks)
        duration = max(1, n_days // n_tasks)
        stride = n_days / n_tasks
        tasks.sort(key=lambda t: t["_meta"]["id_tuple"])
        for i, t in enumerate(tasks):
            start_idx = min(int(i * stride), n_days - duration)
            end_idx = min(start_idx + duration - 1, n_days - 1)
            out[t["number"]] = (days[start_idx], days[end_idx])

    # Stories: span their tasks.
    task_by_story: dict[str, list[dict]] = {}
    for tasks in by_sprint_tasks.values():
        for t in tasks:
            sid = t["_meta"]["story_id"]
            task_by_story.setdefault(sid, []).append(t)
    for stories in by_sprint_stories.values():
        for s in stories:
            sid = s["_meta"]["id_str"]
            child_tasks = task_by_story.get(sid, [])
            if not child_tasks:
                continue
            starts = [out[t["number"]][0] for t in child_tasks if t["number"] in out]
            ends = [out[t["number"]][1] for t in child_tasks if t["number"] in out]
            if starts and ends:
                out[s["number"]] = (min(starts), max(ends))

    # Epics: full sprint range.
    for e in epics:
        sprint = e["_meta"].get("sprint")
        if sprint in SPRINTS:
            out[e["number"]] = SPRINTS[sprint]

    return out


def main():
    issues = json.loads(gh("issue", "list", "--repo", REPO, "--limit", "200",
                           "--state", "all", "--json", "number,title,labels"))
    for i in issues:
        i["_meta"] = parse_issue_meta(i["title"], i["labels"])

    scheduled = schedule(issues)

    items = json.loads(gh("project", "item-list", PROJECT_NUMBER,
                          "--owner", OWNER, "--format", "json", "--limit", "200"))["items"]

    # Map issue number -> Project item ID
    issue_to_item: dict[int, str] = {}
    for it in items:
        c = it.get("content", {})
        if c.get("type") == "Issue" and c.get("number") is not None:
            issue_to_item[c["number"]] = it["id"]

    print(f"Scheduling {len(scheduled)} items "
          f"({sum(1 for i in issues if i.get('_meta', {}).get('kind') == 'Epic')} epics, "
          f"{sum(1 for i in issues if i.get('_meta', {}).get('kind') == 'Story')} stories, "
          f"{sum(1 for i in issues if i.get('_meta', {}).get('kind') == 'Task')} tasks)")

    issues_by_no = {i["number"]: i for i in issues}
    for issue_no in sorted(scheduled.keys(), key=lambda n: issues_by_no[n]["_meta"]["id_tuple"]):
        start, end = scheduled[issue_no]
        item_id = issue_to_item.get(issue_no)
        if not item_id:
            print(f"  skip #{issue_no} (no Project item)")
            continue
        gh("project", "item-edit", "--id", item_id, "--project-id", PROJECT_ID,
           "--field-id", START_FIELD_ID, "--date", start.isoformat())
        gh("project", "item-edit", "--id", item_id, "--project-id", PROJECT_ID,
           "--field-id", END_FIELD_ID, "--date", end.isoformat())
        kind = issues_by_no[issue_no]["_meta"]["kind"]
        print(f"  #{issue_no} [{start} → {end}] {kind} {issues_by_no[issue_no]['_meta']['id_str']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
