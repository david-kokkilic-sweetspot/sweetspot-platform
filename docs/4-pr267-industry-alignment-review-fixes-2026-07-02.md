# PR #267 — Industry-System Alignment & Review-Finding Fixes — Meeting Walkthrough

**Date:** 2026-07-02
**Topic:** _Aligning the AI substrate with the merged generic Industry System, and closing the PR #111 architecture-review findings._
**Owner (this brief):** DEOP
**Format:** ~20–30 min, screen-share + PR walkthrough
**Counterpart repos:** code = `Click-Development/sweetspot` · planning/issues = `david-kokkilic-sweetspot/sweetspot-platform`
**PR:** #267 — `deop/story/industry-system-alignment` → `deop/integration` (**open**)
**Branch:** `deop/story/industry-system-alignment` (5 commits on top of a merge of `origin/main`)

---

## 0. TL;DR (read this if nothing else)

1. **Why:** our AI branch forked from `main` on **Jun 2**, *before* Nicholas's generic Industry System merged (PRs #109 / #115). So it had drifted, and a separate architecture review of PR #111 raised 9 findings (F1–F9). This PR fixes both.
2. **What:** two workstreams on one branch — **(A)** align the AI substrate with the canonical Industry System; **(B)** fix the review findings.
3. **Both HIGH blockers are closed:** F2 (captive dependency) and F3 (AI cost undercounting).
4. **Everything is verified:** clean build, ~2,641 unit tests green across 11 suites, fresh pgvector/pg16 DB migration chain applies cleanly, grep closure shows zero traces of the removed parallel system.
5. **Nothing risky happened to shared branches:** exactly one merge (`origin/main` → my story branch). `main` and `deop/integration` were **not** modified — integration happens only through PR #267, which is still open.

---

# PART A — Why this work happened (background)

## A.1 Branch drift

`deop/integration` (our AI Epic-1 line) forked from `main` on **Jun 2, 2026**. Nicholas then spent two weeks building a **generic Industry System**, merged to `main` via **PR #109 (Jun 16)** and **PR #115 (Jun 19)** — after our fork point. So our branch was written against the *old* contact/account shape and had independently grown a parallel industry mechanism.

**Nicholas's system on `main` (the canonical seam):**
- `ssp.industry` — a registry table (`id`, `template_key`, `name`). Only row today: id `1`, key `membership_org`, name "Association".
- `ssp.account.industry_template` — **int FK → `ssp.industry`**. This is the canonical industry signal.
- `ssp.account.industry` — free-text, **deliberately reserved for a different future purpose** (the sector the org operates in). *Not* the industry signal.
- Industries are defined **in code**: `IIndustryTemplate` + registry + materialiser + per-industry satellite table, wired via `AddIndustrySystem()`.
- Contact template fields: `contact_field_definition` is a **partial** store — unedited system/template fields exist only as *virtual defaults*, merged at read time by `ContactFieldDefinitionResolver`.

## A.2 Nicholas's review (his asks)

1. Confirm why `b2b` / `non-profit` / `wealth-management` industries appear — August scope is **membership/association only**; pull them back.
2. Confirm migrations key off `industry_template` (FK → `ssp.industry`), **not** the free-text `industry` column.
3. Review PR #109 → #115, `docs/industry/industry-system.md`, and the `add-industry` skill, then report back.
4. If AI needs industry-specific behaviour, **build on the existing skills** or add one *new* skill for just the AI aspect — no parallel industry logic.
5. Coordinate with Ahmet going forward — the contact record is critical for his work too.

## A.3 Architecture review (PR #111 → findings F1–F9)

A separate review of the AI foundation raised nine findings. The **two HIGH blockers**:
- **F2 (HIGH):** captive dependency — Singleton AI services capturing a Scoped `ITenantDbContextFactory`.
- **F3 (HIGH):** AI spend undercounted on multi-attempt / failure paths.

Plus two MEDIUM (F4 non-atomic spend cap, F5 fail-open output validation) and four LOW (F6–F9).

---

# PART B — What we did, step by step

## Workstream A — Industry-System alignment

### Step A1 — Merge `origin/main` into the story branch
Brought the branch up to date with the merged Industry System. 20 files conflicted; every conflict was resolved with **main's shape as the base** for anything touching industry/contact/account, re-applying only our genuinely-new AI additions on top.

### Step A2 — Remove the parallel industry system
Our branch had unknowingly built a second registry. Deleted:
- `IndustryTemplateConfig` entity + its seed data (`b2b` / `non-profit` / `wealth-management` seeds).
- The `industry_template_config` table + its migration.
- `account.industry_template_id` (**string**) — it name/type-collided with main's `industry_template` (**int FK**).

**Result:** membership/association is the only industry — the correct August scope.

### Step A3 — Re-point the AI industry reader at the canonical seam
Rewrote `EfCoreIndustryConfigReader` to resolve `account.IndustryTemplate` (int FK) → `ssp.industry` (`template_key`, `name`) → a new in-code `IndustryAiProfileCatalogue` keyed by **template key** (`membership_org`), holding membership-only AI vocabulary + recurring-value labels. Unset (`0`) → membership default; unknown id → `IndustryContext.Empty` (never throws). This mirrors Nicholas's in-code `IIndustryTemplate` pattern without touching his seam.

### Step A4 — Drop the free-text `industry` fallback
The reader used to fall back to the free-text `account.industry` column. Removed entirely — that column now means "sector the org works in," not the industry signal. (This was Nicholas's core concern.)

### Step A5 — Fix the virtual-field-blind contact reader
`EfCoreContactFieldsReader` queried `contact_field_definition` **directly**, so under the new virtual-defaults model it would miss membership/system fields until a user edited them — i.e. the AI would silently not see them. It now reads through `ContactFieldDefinitionResolver`, filtering archived fields. Added a regression test proving virtual fields are visible.

### Step A6 — Resolve extra collisions found during the merge (beyond Nicholas's list)
- **Two `OrganisationProfile` entities** mapped to the same table. Kept main's voice/tone entity as the base (keyed by `org_id`), added our 4 AI fields (`AudienceDescription`, `TierNames`, `ProgrammeNames`, `TerminologyPreferences`).
- **Duplicate account columns:** main already had `website / state / postcode / timezone`; our branch re-added them (one with a divergent type). Dropped ours — the only genuinely new account columns are `locale` + `daily_ai_spend_cap_usd`.
- **`FormsController`** — merged both sides' endpoints into one class.
- **`value` field** — dropped our duplicate system-field entry; enriched main's membership template entry instead.

### Step A7 — Consolidate migrations
Folded 10 never-applied migrations into one `AddAiSubstrate` (all one feature area, never shipped to a shared environment). Also added `modelBuilder.HasPostgresExtension("vector")` — EF 9+ runs migrations under a restricted `search_path`, so pgvector must be declared on the model or the chain fails with "type vector does not exist."

### Step A8 — Skill + doc-log
Added a sibling `add-industry-ai` skill (curate profile → one catalogue entry → tests → gate), leaving Nicholas's `add-industry` skill untouched, per his suggestion. Appended a doc-log entry to `docs/deop/task-1.4.4-industry-context-block.md` referencing the new resolution path.

## Workstream B — Review-finding fixes

### Step B-F2 — Captive dependency (HIGH) ✅
The review named 2 offending services; investigation found **8**. Moved every tenant-data-touching service (`AiUsageLogger`, `DailyAiSpendCapEnforcer`, six `EfCore*Reader`s, plus the context blocks holding them) from **Singleton → Scoped**. Pure/stateless stages stay Singleton. Added a DI test that builds the provider with `ValidateScopes = true` against a real Scoped factory and fails on captive lifetimes.

### Step B-F3 — AI cost undercounting (HIGH) ✅
Usage was computed from only the *final* attempt, and total validation failure logged `0`. Now token/cost accumulators update after **every** provider call in the corrective-retry loop; success logs the sum, and the failure path carries the accumulated totals into the audit row (`Success = false`) so real billed tokens are recorded. Tests cover multi-attempt success **and** total failure.

### Step B-F5 — Fail-open validation (MEDIUM) — guarded ✅
Schema-less features still pass through by design, but now: `AiFeatureKeys` constants replace stringly-typed keys; a startup assertion fails fast if any prompt-builder feature lacks an output-schema registration; and the pass-through path logs a warning so typos surface.

### Step B-F8 — Stale comments / naming (LOW) ✅
Fixed a migration `<summary>` (`jsonb` → the actual `text[]`), reworded `prompt_hash`/`output_hash` comments to "write-only audit fingerprint," and normalised the `ai_usage` user-id index name to snake_case.

### Extra (same sweep)
- **Comment-rule scoping** clarified across three mirrors (`src/backend/AGENTS.md`, `.claude/rules/backend-rules.md`, root `CLAUDE.md`): XML `<summary>` on the public/interface surface, plain `//` for non-obvious private helpers.
- **Background-job note** in AGENTS.md: background jobs must use `IAiClient` + an explicit `AiGenerateRequest` (not `ITenantAiClient`, which needs a request scope).

---

# PART C — What we deliberately did NOT do (and why)

None of these block the PR. Each was a conscious decision, documented in code or the PR body.

| # | Finding | Decision | Reason |
|---|---------|----------|--------|
| **F1** | PR is large (packaging) | No action | Integration-packaging PR; will be split per PR-STANDARDS when the production-bound PR is cut |
| **F4** | Spend cap not atomic (MEDIUM) | Kept **soft/best-effort**, documented | Sufficient for August; overshoot is bounded by concurrency × per-call cost. Atomic reservation noted as the upgrade path. F3's fix already makes the sum it reads accurate |
| **F6** | `FieldSemanticTags.Vocabulary` unenforced (LOW) | TODO + note only | No write path validates it yet; enforcement lands when that path does |
| **F7** | `ModelClass` uses Anthropic names; `ITenantAiClient` signature (LOW) | **Deferred — needs team decision** | A capability-tier rename (Standard/Light/Advanced?) ripples into generated config classes + the appsettings schema; the naming is a team call |
| **F9** | PII regex is naive (LOW) | Tradeoff documented, unchanged | Patterns are intentionally broad (prefer false positives so PII never leaks); Luhn/NANP tightening can be added later without changing the public shape |

---

# PART D — Merge & branch mechanics (from where to where)

Exactly **one** merge happened, on the story branch only:

- **Commit `00810cc24`** — merge `origin/main` (tip `d78a12097`) into `deop/story/industry-system-alignment` (which was cut from the tip of `deop/integration`).
- This is a standard "update my feature branch with latest main" merge.

**What was NOT touched:**
- `main` — read only (merged *from*). No push, no commit.
- `deop/integration` — local == remote; nothing pushed, nothing merged. It is only the **target** of PR #267.
- Integration happens **only** through PR #267, which is still **open** — that merge is a reviewer action, not something done here.

```
origin/main ─────────┐  (merge — commit 00810cc24)
                     ▼
deop/integration ──> deop/story/industry-system-alignment ──> PR #267 (OPEN, not merged)
   (base, untouched)   (+ merge main + 5 fix commits)            target: deop/integration
```

---

# PART E — Verification

- **Build:** clean `dotnet build`, 0 errors.
- **Tests:** ~**2,641** unit tests green across 11 suites (AI 323, Admin 520, BFF 668, Audience 364, Forms 263, Assets 210, Agents 157, Settings 80, Email 32, Common 16).
- **Fresh DB:** on a clean pgvector/pg16 container the whole migration chain applies cleanly — parallel table gone, `ai_usage` / KB / voice / brief tables created, `account` gains only `locale` + `daily_ai_spend_cap_usd`, all `ai_usage` indexes snake_case.
- **Grep closure:** zero remaining references to `IndustryTemplateId` (string) or `industry_template_config`.

---

# PART F — Open decisions & coordination

- **F7 naming (team):** agree the capability-tier names before renaming `ModelClass` — it touches generated config + appsettings schema.
- **Contact record (Ahmet):** anything touching the contact record will be coordinated with Nicholas and Ahmet first, per the review.
- **F4 atomic cap:** revisit if a hard spend ceiling (not best-effort) is later required; the reservation approach is the documented upgrade path.

---

_Prepared by DEOP · 2026-07-02 · reference: PR #267, memory `reference-ai-arch-scope`, plan `imdi-repo-sweetspot-projesi-ile-foamy-matsumoto`._
