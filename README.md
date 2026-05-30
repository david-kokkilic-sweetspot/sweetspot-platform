# Sweetspot Platform — Planning & AI Architecture

This repository is the **planning and documentation hub** for the Sweetspot platform AI architecture rollout. It is the source of truth for epics, stories, tasks, and the Jun 1 – Aug 15 2026 implementation timeline.

The actual application code lives in separate repositories that are intentionally **not** tracked here.

## Layout

```
docs/                   AI architecture strategy + scope (canonical)
.github/ISSUE_TEMPLATE/  Epic / Story / Task issue templates
scripts/                One-shot bootstrap scripts (labels, milestones, issues)
repostories/            Local clones of the actual code repos (gitignored)
```

## Linked Code Repositories

| Repo | URL | Role |
|------|-----|------|
| `Click-Development/sweetspot` | https://github.com/Click-Development/sweetspot | Angular SPA + .NET 10 BFF — primary target for AI architecture work |
| `sweetspot2026/orbit` | https://github.com/sweetspot2026/orbit | Legacy reference (Next.js + Supabase) — strategy origin |

These repos are not embedded as git submodules. They are cloned locally under `repostories/` for convenience but excluded via `.gitignore` so this repo stays planning-only.

## Project Management

Issues in this repo follow a three-level hierarchy:

- **Epic** (`type:epic`) — Sprint-sized scope (5 total)
- **Story** (`type:story`) — A feature within an Epic (sub-issue of Epic, 17 total)
- **Task** (`type:task`) — Engineering work within a Story (sub-issue of Story, 39 total)
- **Subtask** — Markdown checkboxes inside a Task body

These are tracked on a user-level GitHub Project (v2) under `david-kokkilic-sweetspot`. The Project includes items from this repo **and** PRs from the linked code repositories — so progress is visible end-to-end on one board.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the convention used to link PRs in code repos back to issues here.

## Source of Truth

The canonical scope document is [`docs/ai-arch-scope.md`](./docs/ai-arch-scope.md). The bootstrap scripts in `scripts/` derive labels, milestones, and issues directly from that document's structure. If scope changes, edit the doc and re-run the relevant bootstrap script (idempotent for labels/milestones; issues are one-shot).
