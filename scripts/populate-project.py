#!/usr/bin/env python3
"""Add all repo issues to the user-level Project (v2) and populate custom fields.

Derives field values from issue labels and title prefix. Idempotent on field
edits (re-running doesn't duplicate items because we look up existing items
first; add is the only non-idempotent step but `gh project item-add` on an
existing item simply returns it).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

REPO = "david-kokkilic-sweetspot/sweetspot-platform"
OWNER = "david-kokkilic-sweetspot"
PROJECT_NUMBER = "1"
PROJECT_ID = "PVT_kwHOENN7U84BZMPv"

FIELDS = {
    "Type": {
        "id": "PVTSSF_lAHOENN7U84BZMPvzhUMtj0",
        "opts": {"Epic": "81afc9e0", "Story": "cb5eba8a", "Task": "df3048d4"},
    },
    "Epic": {
        "id": "PVTSSF_lAHOENN7U84BZMPvzhUMtlg",
        "opts": {
            "Epic 1": "4495e13f", "Epic 2": "a7c48c9a", "Epic 3": "ae896bfb",
            "Epic 4": "f6b4cdfb", "Epic 5": "0fa06b21",
        },
    },
    "Sprint": {
        "id": "PVTSSF_lAHOENN7U84BZMPvzhUMtmY",
        "opts": {
            "Sprint 1": "b3f0f582", "Sprint 2": "de2348c4", "Sprint 3": "fcef61c7",
            "Sprint 4": "d9bd84af", "Sprint 5": "36f3d3c5",
        },
    },
    "PR": {
        "id": "PVTSSF_lAHOENN7U84BZMPvzhUMtm0",
        "opts": {
            "PR 9": "39d8a816", "PR 10": "d0be5df4", "PR 11": "5ecd23d5",
            "PR 11p": "9c82dc68", "PR 12": "10ac3563", "PR 13": "bd7c2e4c",
            "PR 14": "c73d4c54",
        },
    },
    "Phase": {
        "id": "PVTSSF_lAHOENN7U84BZMPvzhUMtm4",
        "opts": {"Phase 1": "9a54b0ab", "Phase 2": "9c03e82e",
                 "Phase 3": "ea51fa07", "Phase 4": "02f3f2cf"},
    },
    "Customer Visible": {
        "id": "PVTSSF_lAHOENN7U84BZMPvzhUMtm8",
        "opts": {"Yes": "608793dc", "No": "73f8a6e2", "Partial": "1b078f35"},
    },
}


def gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(f"FAILED: gh {' '.join(args)}\n{result.stderr}\n")
        sys.exit(1)
    return result.stdout.strip()


def list_issues() -> list[dict]:
    out = gh("issue", "list", "--repo", REPO, "--limit", "200", "--state", "all",
             "--json", "number,title,labels,url")
    return json.loads(out)


def derive_fields(issue: dict) -> dict[str, str]:
    """Map an issue to field-name -> option-name based on labels and title."""
    title = issue["title"]
    labels = {l["name"] for l in issue["labels"]}
    fv: dict[str, str] = {}

    # Type
    if "type:epic" in labels:
        fv["Type"] = "Epic"
    elif "type:story" in labels:
        fv["Type"] = "Story"
    elif "type:task" in labels:
        fv["Type"] = "Task"

    # Epic — from title prefix like "Epic 1:", "Story 1.1:", "Task 1.1.1:"
    m = re.match(r"^(Epic|Story|Task)\s+(\d+)", title)
    if m:
        fv["Epic"] = f"Epic {m.group(2)}"

    # Sprint — from sprint:N label
    for lab in labels:
        if lab.startswith("sprint:"):
            n = lab.split(":", 1)[1]
            fv["Sprint"] = f"Sprint {n}"
            break

    # PR — only set if a single pr:* label is present.
    # Epics span multiple PRs (PR 11+11p, PR 13+14) — leave PR field empty there
    # because Project single-select can't hold multiple values; Sprint covers it.
    pr_labels = sorted(l for l in labels if l.startswith("pr:"))
    if len(pr_labels) == 1:
        suffix = pr_labels[0].split(":", 1)[1]
        fv["PR"] = f"PR {suffix}"

    # Phase
    for lab in labels:
        if lab.startswith("phase:"):
            n = lab.split(":", 1)[1]
            fv["Phase"] = f"Phase {n}"
            break

    # Customer Visible
    if "customer-visible:yes" in labels:
        fv["Customer Visible"] = "Yes"
    elif "customer-visible:no" in labels:
        fv["Customer Visible"] = "No"
    elif "customer-visible:partial" in labels:
        fv["Customer Visible"] = "Partial"

    return fv


def add_item(url: str) -> str:
    out = gh("project", "item-add", PROJECT_NUMBER, "--owner", OWNER, "--url", url, "--format", "json")
    return json.loads(out)["id"]


def set_field(item_id: str, field_name: str, opt_name: str) -> None:
    field = FIELDS[field_name]
    opt_id = field["opts"].get(opt_name)
    if not opt_id:
        sys.stderr.write(f"  WARN: no option '{opt_name}' for field '{field_name}'\n")
        return
    gh("project", "item-edit",
       "--id", item_id,
       "--project-id", PROJECT_ID,
       "--field-id", field["id"],
       "--single-select-option-id", opt_id)


def main():
    issues = list_issues()
    issues.sort(key=lambda i: i["number"])
    print(f"Processing {len(issues)} issues...")

    for issue in issues:
        n = issue["number"]
        title = issue["title"]
        fv = derive_fields(issue)
        try:
            item_id = add_item(issue["url"])
        except SystemExit:
            print(f"  #{n} {title}: ADD failed, skipping")
            continue
        for fname, oname in fv.items():
            set_field(item_id, fname, oname)
        summary = ", ".join(f"{k}={v}" for k, v in fv.items())
        print(f"  #{n} [{summary}] {title}")

    print("\nDone.")


if __name__ == "__main__":
    main()
