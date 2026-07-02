#!/usr/bin/env bash
# One-shot: create the 5 sprint milestones. Idempotent (skips if title already exists).
# Requires: gh CLI, authenticated as david-kokkilic-sweetspot (or repo admin).
set -euo pipefail

REPO="${REPO:-david-kokkilic-sweetspot/sweetspot-platform}"
OWNER="${REPO%%/*}"
NAME="${REPO##*/}"

create_milestone() {
  local title="$1" due="$2" desc="$3"

  # Check existing
  local existing
  existing=$(gh api "repos/${OWNER}/${NAME}/milestones?state=all" --jq ".[] | select(.title == \"${title}\") | .number" || true)

  if [[ -n "$existing" ]]; then
    echo "  exists (#$existing): $title"
    return
  fi

  echo "  creating: $title"
  gh api "repos/${OWNER}/${NAME}/milestones" \
    -f title="$title" \
    -f due_on="${due}T23:59:59Z" \
    -f description="$desc" \
    --jq '.number' >/dev/null
}

echo "Creating milestones in $REPO..."

create_milestone "Sprint 1 — PR 9"           "2026-06-13" "Foundation + Client Wrapper (Jun 1 – Jun 13). Customer-visible: no."
create_milestone "Sprint 2 — PR 10"          "2026-06-27" "Unified Email Component (Jun 16 – Jun 27). Customer-visible: yes. Decision checkpoint Week 4."
create_milestone "Sprint 3 — PR 11 + PR 11p" "2026-07-11" "Web Agent Cleanup + Field-Tagging UI (Jun 30 – Jul 11). Customer-visible: partial/yes."
create_milestone "Sprint 4 — PR 12"          "2026-07-25" "Context Blocks + AI Surface Parity Wiring (Jul 14 – Jul 25). Customer-visible: no. Decision checkpoint Week 8."
create_milestone "Sprint 5 — PR 13 + PR 14"  "2026-08-15" "Recommendations + Today Page (Jul 28 – Aug 15). Customer-visible: yes. Decision checkpoint Week 10."

echo "Done."
