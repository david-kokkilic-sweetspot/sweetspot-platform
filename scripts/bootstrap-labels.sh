#!/usr/bin/env bash
# One-shot: create labels in the planning repo. Idempotent (uses --force to update existing).
# Requires: gh CLI, authenticated as david-kokkilic-sweetspot (or repo admin).
set -euo pipefail

REPO="${REPO:-david-kokkilic-sweetspot/sweetspot-platform}"

create() {
  local name="$1" color="$2" desc="$3"
  echo "  label: $name"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force >/dev/null
}

echo "Creating labels in $REPO..."

# Hierarchy
create "type:epic"   "6B2FBE" "Top-level scope. Parent of Stories."
create "type:story"  "1F6FEB" "Feature within an Epic. Parent of Tasks."
create "type:task"   "0E8A4F" "Engineering work within a Story."

# Sprint
create "sprint:1" "FBCA04" "Sprint 1 (Jun 1 – Jun 13 2026)"
create "sprint:2" "FBCA04" "Sprint 2 (Jun 16 – Jun 27 2026)"
create "sprint:3" "FBCA04" "Sprint 3 (Jun 30 – Jul 11 2026)"
create "sprint:4" "FBCA04" "Sprint 4 (Jul 14 – Jul 25 2026)"
create "sprint:5" "FBCA04" "Sprint 5 (Jul 28 – Aug 15 2026)"

# PR
create "pr:9"   "C5DEF5" "PR 9 — Foundation + email-generate proof"
create "pr:10"  "C5DEF5" "PR 10 — Unified email-content component"
create "pr:11"  "C5DEF5" "PR 11 — Web Agent cleanup + form/event confirmation migration"
create "pr:11p" "C5DEF5" "PR 11p — Field-tagging UI"
create "pr:12"  "C5DEF5" "PR 12 — Context blocks + AI surface parity wiring"
create "pr:13"  "C5DEF5" "PR 13 — Recommendation action handlers"
create "pr:14"  "C5DEF5" "PR 14 — Today page + Retain dashboard + command palette"

# Phase
create "phase:1" "EDEDED" "Phase 1 — Rules-based recommendations"
create "phase:2" "EDEDED" "Phase 2 — AI-generated content, plan-aware"
create "phase:3" "EDEDED" "Phase 3 — Routine autonomy (post-launch)"
create "phase:4" "EDEDED" "Phase 4 — Plan self-execution (future)"

# Customer-visible
create "customer-visible:yes"     "2EA043" "Customer-facing change"
create "customer-visible:no"      "9E9E9E" "Substrate / infrastructure only"
create "customer-visible:partial" "F7C548" "Partially customer-visible"

# Decision checkpoints
create "checkpoint:week-4"  "D93F0B" "Decision checkpoint — Week 4 (after PR 10)"
create "checkpoint:week-8"  "D93F0B" "Decision checkpoint — Week 8 (after PR 12)"
create "checkpoint:week-10" "D93F0B" "Decision checkpoint — Week 10 (after PR 13)"

echo "Done."
