# Contributing — PR ↔ Issue Linkage Convention

This repo holds planning issues. The code lives in [`Click-Development/sweetspot`](https://github.com/Click-Development/sweetspot) and [`sweetspot2026/orbit`](https://github.com/sweetspot2026/orbit). PRs opened in those repos should always link back to the relevant issue(s) here so the GitHub Project shows progress end-to-end.

## PR Description Template

When opening a PR in a code repo for any of the planned PRs (PR 9 – PR 14), include these references in the PR body:

```
Tracks david-kokkilic-sweetspot/sweetspot-platform#<EPIC_NO>
Tracks david-kokkilic-sweetspot/sweetspot-platform#<STORY_NO>
Closes david-kokkilic-sweetspot/sweetspot-platform#<TASK_NO_1>
Closes david-kokkilic-sweetspot/sweetspot-platform#<TASK_NO_2>
...
```

### What each keyword does

- **`Tracks owner/repo#N`** — informational link only. GitHub renders a back-reference on issue `#N`. Does not close anything on merge. Use for Epic and Story relationships.
- **`Closes owner/repo#N`** — official close keyword. When the PR merges, issue `#N` is automatically closed and the PR is recorded as the resolver. Use for Task issues that the PR fully completes.

Other accepted close keywords: `Fixes`, `Resolves` (interchangeable with `Closes`).

## Adding the PR to the Project

After opening the PR:

1. Open the PR page on GitHub.
2. Right sidebar → **Projects** → select **Sweetspot AI Architecture**.
3. On the Project board, set the PR's custom fields: `PR`, `Sprint`, `Epic`, `Phase`, `Status`.

If the Project has an auto-add workflow configured for the source repo, this step happens automatically.

## Cross-Repo Permissions

`david-kokkilic-sweetspot` needs at least triage-level access on the source repo to attach PRs to a personally-owned Project. READ-only access is enough to add the PR to the project view but not to modify custom fields. Verify before opening real PRs:

```bash
gh repo view Click-Development/sweetspot --json viewerPermission
```

If permission is below WRITE, request access from the org admin or have someone with WRITE attach the PR.

## Editing Scope

The canonical scope document is [`docs/ai-arch-scope.md`](./docs/ai-arch-scope.md). When the scope changes:

- **Adding a new task** — edit the doc, open an issue manually, link it to the right Story as a sub-issue.
- **Renaming a PR or splitting an Epic** — edit the doc, rename the existing issue, update labels.
- **Major restructure** — discuss before regenerating; bootstrap scripts are one-shot and not designed to be re-run on an existing repo.
