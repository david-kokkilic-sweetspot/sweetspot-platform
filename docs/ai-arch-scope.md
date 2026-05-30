---
title: AI Architecture — Scope & Deliverables
source: ai-architecture-strategy-v2.md
created: 2026-05-29
target_repo: sweetspot
stack: Angular SPA + .NET 10 BFF
purpose: Actionable requirements extracted from the strategy doc, with line references.
---

# AI Architecture — Scope & Deliverables

## What This Document Covers

The AI architecture strategy was originally written for the Orbit app (Next.js / Supabase). The decision has changed: **all AI architecture work will now be implemented in the Sweetspot platform repo** — Angular frontend (`src/frontend/`) and .NET backend (`src/backend/`).

This document extracts every deliverable from the strategy, reframed for the Sweetspot stack:

| Layer | Strategy reference | Sweetspot implementation |
|-------|-------------------|--------------------------|
| Client wrapper (`/lib/ai/client.ts`) | Next.js server-side | .NET service in BFF or shared library under `src/backend/Core/` |
| Context blocks (`/lib/ai/context/*.ts`) | TypeScript functions | .NET services/classes in a new AI domain project |
| Unified email component (`AIEmailModal`) | React component | Angular component in `src/frontend/src/app/shared/` or `features/` |
| Database (Supabase + RLS) | Supabase Postgres | PostgreSQL via EF Core (`src/backend/Core/Database/`) |
| Prompt storage (`/lib/ai/prompts/`) | TS files in Next.js | Resource files or service classes in .NET backend |
| API routes (`/api/email/generate`, etc.) | Next.js App Router | BFF API endpoints (`src/backend/Core/BackendForFrontend/`) |

---

## Asset Shapes — Generation Categories (Reference)

> From strategy §4.2 (L184-188). AI generation surfaces split into three output shapes with different brand-awareness requirements. Captured for completeness — the 7-PR sequence prioritises the branded-HTML shape (email) as the keystone.

| Shape | What AI produces | Surfaces | Migration status |
|-------|------------------|----------|------------------|
| Branded HTML content | Customer-facing copy in branded HTML emails/pages | email-generate, journey email step, form/event confirmation | **Primary target** — PR 9, PR 10, PR 11 |
| Structural JSON | Schema/graph data the editor renders, brand-light | forms-generate, journey-generate | Gains brand+org+industry blocks via PR 12; no dedicated wrapper-migration PR |
| Metadata | Short identifiers and descriptions | campaigns-generate | Not scheduled in the 7-PR sequence |

**Note:** `forms-generate`, `journey-generate` (structural JSON) and `campaigns-generate` (metadata) are intentionally not given dedicated migration PRs. They gain context-block awareness once PR 12 lands, but routing them through the client wrapper is a follow-up beyond this plan.

---

## 1. CLIENT WRAPPER — Single Entry Point

All AI calls must flow through a central service. In the Sweetspot stack this becomes an `IAiClient` service (or equivalent) in the .NET backend.

- [ ] **1.1** All AI calls go through this wrapper. Direct SDK calls outside the wrapper are a code-review red flag. (L391)
- [ ] **1.2** Provider abstraction: `Generate({ feature, system, messages, modelClass })` → `{ content, usage, metadata }`. Anthropic today, Azure AI Foundry post-launch. (L395)
- [ ] **1.3** Mandatory logging on every call: `org_id`, `user_id`, feature, model, tokens in/out, cost, latency, success/failure, content hash, consent status, data residency region, trace ID. (L397)
- [ ] **1.4** Error handling: transient failures retry with backoff; permanent failures degrade gracefully (template-based fallback instead of AI). Errors are never swallowed. (L399)
- [ ] **1.5** Per-feature model selection: Sonnet (strategy, complex generation) vs Haiku (chat, classification). Single config point. (L401)
- [ ] **1.6** Output validation via schema (equivalent to Zod in TS): parse, validate, retry with corrective prompting on failure. After 2 failures → typed error. (L403)
- [ ] **1.7** Content filtering: PII detection in outputs, banned-content checks, redaction logging. Baked in from day one. (L405)
- [ ] **1.8** Provider-agnostic internal contract: cost translation, filtering, retry, validation all happen regardless of provider. (L631-632)
- [ ] **1.9** Provider-specific cost tables: support per-provider pricing in the cost calculation service. (L649)

---

## 2. COMPOSABLE CONTEXT BLOCKS — 10 Blocks

Each block is a service/function: `LoadBlockContextAsync(orgId, options?)` → structured context object (L411-412)

The context object exposes field accessors + a `ToPromptString()` method, so consumers can include the full block or pick specific fields. (L415)

### Block Rules
- [ ] **2.1** Graceful degradation: if data source is missing or sparse → return empty/minimal stub, never throw. (L158)
- [ ] **2.2** No side effects: reading and formatting only. (L158)
- [ ] **2.3** Blocks may depend on other blocks (audience depends on field-semantics). (L158)

### The 10 Blocks and Their Sources

| # | Block | Data Source | Line |
|---|-------|-------------|------|
| 2.4 | brand | `brand_settings` + `color_roles` JSONB | 164 |
| 2.5 | org | `organizations` table | 165 |
| 2.6 | industry | `industry_template_configs` table | 166 |
| 2.7 | methodology | `marketing_disciplines`, `goal_types`, `programmes`, `tag_labels` | 167 |
| 2.8 | field-semantics | `contact_field_definitions` extension columns | 168 |
| 2.9 | audience | `audiences` + `audience_contacts` + field-semantics | 169 |
| 2.10 | plan | `marketing_plans` + `plan_goals` + `plan_programmes` | 170 |
| 2.11 | insights | Cross-org aggregate benchmarks (privacy-respecting) | 171 |
| 2.12 | knowledge | KB tables — per-org + curated, vector search Top-K | 172 |
| 2.13 | assets | `content_assets` table — AI-tagged on upload | 173 |

### Feature → Block Composition

| Feature | Blocks Composed | Line |
|---------|----------------|------|
| email-generate | brand + org + industry + audience + plan + assets + (optional) knowledge | 421 |
| journey-content | brand + org + industry + journey-context + audience + plan + assets | 422 |
| form-generate | brand + org + industry | 423 |
| chat agent | brand + org + industry + knowledge + conversation history | 424 |
| strategy agent | brand + org + industry + methodology + plan + insights + knowledge | 425 |
| insights-agent | org + industry + methodology + plan + insights + knowledge | 426 |
| recommendation action | all of the above + signal context + recommendation reasoning | 427 |

---

## 3. UNIFIED EMAIL-CONTENT COMPONENT

- [ ] **3.1** Single function for all branded email generation: `GenerateBrandedEmail({ intent, context, cta?, structuralOptions? })`. 3 consumers: email editor, journey editor, recommendation action handler. (L431, L436-444)
- [ ] **3.2** Existing `AIEmailModal` component (~300 lines) to be extracted and made shared/reusable. In the Sweetspot Angular SPA, this becomes a shared component or service. (L237, L354)
- [ ] **3.3** Context type refactor: instead of `emailId`, use a discriminated context: `campaign_email | journey_step | standalone`. (L242-247)
- [ ] **3.4** Context-aware CTA: if `journey_step` + `eventId` → pre-fill with event's registration URL. If `standalone` → user provides or toggles off. (L252)
- [ ] **3.5** Unified backend endpoint: loads context blocks based on `kind`, composes prompt, calls client wrapper, returns result. (L250)
- [ ] **3.6** Headless callers supported: recommendation action handlers can call the API directly without rendering the modal/UI. (L449)

---

## 4. AGENT REDEFINITION

- [ ] **4.1** "Agent" = multi-step, conversational, decision-making entity. Single-call email senders are handlers/generators, not agents. (L201)
- [ ] **4.2** Form-agent and event-agent **creation** logic (confirmation email) moves to journeys. Journey's first step = confirmation email. .ics attachment becomes a journey-email feature. (L205)
- [ ] **4.3** Agent **runtime** remains: handles inbound replies, multi-turn, with original registration context. (L207)
- [ ] **4.4** HTML generation duplication (email-generate / form-agent / event-agent) disappears. (L209)

---

## 5. TARGET LIBRARY STRUCTURE

In the strategy doc this is `/lib/ai/` (Next.js). For Sweetspot, this maps to a new project or namespace under `src/backend/Core/` — e.g. `SSP.AI` or integrated into the BFF.

**Strategy reference structure (L368-387):**

```
AI layer (to be mapped to .NET):
  Client         — Wrapper service (IAiClient / AiClientService)
  Prompts/       — Per-feature system prompts (resource files or prompt classes)
  Context/       — 10 composable context block services
  Knowledge/     — KB / RAG layer (vector search, embedding)
  Agents/        — Multi-step agent loops (chat, strategy)
  Schemas/       — Output validation schemas (C# record types or FluentValidation)
  Usage/
    Log          — Writes to ai_usage after every call
    Cost         — Token + model → cost calculation
```

- [ ] **5.1** Prompts must live in dedicated files/classes, not inline in endpoint handlers. (L372)

---

## 6. SCHEMA CHANGES

| # | Table | Change | PR | Line |
|---|-------|--------|-----|------|
| 6.1 | `ai_usage` | Add columns: `user_id`, model, latency_ms, success, `error_message`, created_at, `prompt_hash`, `output_hash`, `consent_status`, `data_residency_region`, `trace_id`, `content_filter_outcome` | PR 9 | 521 |
| 6.2 | `contact_field_definitions` | Existing `description`, `field_tags`, `ai_suggested_tags` columns populated via UI | PR 11p | 522 |
| 6.3 | `audience_contexts` (new) | Materialised view or table: "audience X semantically means Y" | PR 12 | 523 |
| 6.4 | `recommendation_actions` | Extension: `ai_call_trace_id`, `action_journey_id`, `action_audience_id` | PR 13 | 524 |
| 6.5 | `ai_recommendations` | New columns: `confidence_type`, `source_signal_id`, `plan_goal_id`, `programme_id` | PR 13 | 525 |
| 6.6 | All migrations must be vendor-neutral SQL (no Supabase-specific syntax) | All | 633 |

**Note:** In the Sweetspot repo, schema changes go through EF Core migrations (`src/backend/Core/Database/`). `ai_recommendations` (6.5) is scheduled in **PR 13** (not PR 14 as in v2 §8.1) because PR 13's confidence labelling needs `confidence_type`.

---

## 7. MULTI-TENANT ISOLATION

- [ ] **7.1** Every table scoped by `org_id`, protected by RLS or application-layer tenant filtering. AI tables are no exception. (L529)
- [ ] **7.2** No AI call exists without an `org_id`. The wrapper reads it from the authenticated session. (L535)
- [ ] **7.3** Knowledge retrieval: vector search filters by `org_id` for org-scoped content. Curated content is shared. Scope enforcement is in the retrieval function, not the caller. (L537)
- [ ] **7.4** Benchmarks: minimum-N threshold (5-10) to prevent identifying a single org. Below threshold → return "n/a". (L539)
- [ ] **7.5** Cross-org reporting goes through a separate service-role view, not customer-facing queries. (L541)

---

## 8. FIELD-SEMANTICS — 3-Tier Tagging

- [ ] **8.1** System fields (11): pre-tagged with universal defaults, seeded in PR 9. Read-only, no per-org override. (L559)
- [ ] **8.2** Template fields (per industry): pre-tagged per industry, seeded with framework. Read-only, no per-org override. (L560)
- [ ] **8.3** Custom fields (org-created): user tags them, AI suggests, user accepts or overrides. (L561)
- [ ] **8.4** Field-tagging UI: dedicated settings page (equivalent to `/dashboard/settings/ai-ready`). Shows readiness percentage prominently. (L462)
- [ ] **8.5** v1 vocabulary: 8 controlled semantic tags with CHECK constraint. (L549)

---

## 9. INSIGHTS COMMAND CENTRE

- [ ] **9.1** New IA: Today (command centre) / Grow / Engage / Retain / Earn. (L117-125)
- [ ] **9.2** Recommendation card = Insight + Recommendation + Action fused on a single card. (L127-133)
- [ ] **9.3** Preview-and-confirm: one-click never sends. Every commit shows audience preview + journey/campaign template + projected impact + audit-trail entry. (L135)
- [ ] **9.4** Confidence labelling: rules-based = "Counted", AI-generated = "Suggested". Conflating these erodes trust. (L137)

---

## 10. TRUST PROGRESSION — 4 Phases

| Phase | What AI does | User role | Line |
|-------|-------------|-----------|------|
| Phase 1 (launch) | Rules-based recommendations, explicit confirm | Approves every time | 145 |
| Phase 2 (launch) | AI-generated content, plan-aware recommendations, context-aware CTA | One-click on content, still previews audience | 146 |
| Phase 3 (post-launch) | Routine actions execute without confirm (opt-in, audited, undoable) | Reviews audit log, sets per-action autonomy | 147 |
| Phase 4 (future) | Plan self-executes within user-set autonomy limits | Exception handler, not approver | 148 |

---

## 11. HYPERPERSONALISATION

- [ ] **11.1** Segment-level (Phase 2, launch): different copy per audience segment within same send. AI-suggested assets. Marketer reviews in preview. (L260)
- [ ] **11.2** Per-recipient (Phase 3+, post-launch): unique subject, body, asset, CTA per individual. Send pipeline composes per-recipient at delivery time. (L261)
- [ ] **11.3** Cost-control patterns must land before Phase 3: variant-based hybrid (N variants, pick best), per-section variants, hard daily + per-send caps. (L271-273)

---

## 12. OBSERVABILITY

- [ ] **12.1** Cost tracking per org, per feature, per month. (L597)
- [ ] **12.2** Latency tracking per feature. (L599)
- [ ] **12.3** Every validation retry logged. (L601)
- [ ] **12.4** Failure tracking: `error_message` column captures failure mode. (L603)
- [ ] **12.5** `trace_id` audit linkage: single user action → all downstream AI calls. Required for EU AI Act "explain why" obligation. (L605)

---

## 13. COMPLIANCE

- [ ] **13.1** GDPR: mandatory at launch. (L617)
- [ ] **13.2** SOC 2 Type 2: path to within 12 months. (L618)
- [ ] **13.3** EU AI Act: transparency obligations, likely "limited risk" classification. (L619)
- [ ] **13.4** ISO 42001: path to within 18 months. (L620)
- [ ] **13.5** PII detection: outputs scanned for accidental disclosure. (L661)
- [ ] **13.6** Banned-content filters: profanity, regulated-topic. Customer-configurable thresholds. (L663)
- [ ] **13.7** Redaction logging: what was filtered and why. AI Act explainability. (L665)
- [ ] **13.8** Filtering happens at the client wrapper layer: after model returns, before delivery to consumer. Centralised, auditable. (L667)

---

## 14. INFRASTRUCTURE — Forward Look

- [ ] **14.1** Launch on Anthropic direct API. (L653)
- [ ] **14.2** Post-launch: migrate to Azure AI Foundry (v1.5 PR). (L653)
- [ ] **14.3** Environment variables for provider selection: `AI_PROVIDER`, `AI_REGION`, `AI_MODEL_DEFAULT` — config-driven, not hardcoded. (L635)
- [ ] **14.4** `data_residency_region` column logged from day one. (L637)

---

## 15. MIGRATION — 7 PR Sequence

> **Important:** The original PR plan assumes Next.js file paths. Below is the intent — actual implementation paths will be in the Sweetspot Angular + .NET repo structure.

| PR | Name | Scope | Customer-visible? | Line |
|----|------|-------|-------------------|------|
| PR 9 | Foundation + email-generate proof | AI client wrapper service (full — retry, model selection, output validation, content filtering, cost calc), usage logging, context blocks (brand, org, industry). Migrate email-generate as byte-identical proof of pattern. Extend ai_usage schema. Seed system/template field tags. | No | 459 |
| PR 10 | Unified email-content component | Extract email generation UI to shared component. Refactor context contract. Build unified backend endpoint. Wire into journey editor. Context-aware CTA. | Yes — journey emails AI-generated | 460 |
| PR 11 | Form/event agent migration | Agents stop sending confirmation emails → journeys take over. Agents narrow to "enrol in journey + open inbound thread". HTML duplication gone. | Partial | 461 |
| PR 11p | Field-tagging UI | Settings page for tagging contact fields with semantic labels. System fields read-only, template fields read-only, custom fields interactive + AI suggestion. Readiness %. | Yes | 462 |
| PR 12 | Context blocks (methodology, plan, insights, audience, assets) | Build remaining 7 context block services. Knowledge block generalised from chat-only to all features. | No — substrate | 463 |
| PR 13 | Recommendation action handlers | "Build the campaign" action creates real audiences, real journeys with AI content. Phase 2 live. Segment-level hyperpersonalisation. | Yes — Phase 2 | 464 |
| PR 14 | Today page + Retain dashboard + command palette | Insights revamp customer-facing surfaces. | Yes — launch-ready | 465 |

### Dependencies (L469-475)

```
PR 9 ──→ everything
PR 10 ──→ PR 11 (agent migration), PR 13 (action handlers)
PR 11p ──→ field-semantics block, audience block, Phase 2 depth
PR 12 ──→ PR 13 (rich contextual AI content)
PR 13 ──→ PR 14 (Today page) + Phase 2 trust progression
```

### Decision Checkpoints

- [ ] **Week 4 (after PR 10):** Is the unified email component working as keystone? If not → cut journey-content to v2, lean on templates. (L481)
- [ ] **Week 8 (after PR 12):** Is field-tagging UI shipped and users tagging? If not → audience block returns sparse data, Phase 2 at half power. (L483)
- [ ] **Week 10 (after PR 13):** Is recommendation→action producing acceptable content? If not → allocate prompt-tuning time before PR 14. (L485)

---

## 16. RISKS

- [ ] **R1** Pre-production assumption: no live customers on form/event agents today. Once friendlies are using them, deprecation becomes a migration concern. (L489)
- [ ] **R2** Field-tagging UI is more UX than engineering. Must feel manageable for orgs with 40+ fields. Underestimate → timeline slips silently. (L491)
- [ ] **R3** Prompt tuning: output quality may shift per migrated surface. Plan 2-3 days side-by-side testing each. (L493)
- [ ] **R4** Weeks 5-8 are invisible: nothing customer-facing moves. Communicate this is expected. (L495)
- [ ] **R5** Customer feedback loop: if no friendly sees Phase 1 by week 6, Phase 2 is built in the dark. (L497)

---

## 17. OPEN QUESTIONS (Decisions Pending)

### Architecture
- [x] **Q1** Client wrapper scope at PR 9: **RESOLVED — full wrapper** (logging + retry + model selection + output validation + content filtering + cost calc) lands in PR 9. Intentional divergence from v2's "minimal for PR 9, expand in PR 11" recommendation — chosen to avoid retrofit cost. (L677)
- [ ] **Q2** Prompt extraction: dedicated files/classes or inline in handlers? Recommendation: extract. (L679)
- [ ] **Q3** Context block return shape: string or structured object? Recommendation: structured + `ToPromptString()`. (L681)
- [ ] **Q4** `ai_usage` column set: finalise with data architect before PR 9 schema migration. (L683)

### Brand & Content
- [ ] **Q5** Per-template brand-role override: on campaign_emails or template? Recommendation: defer to v2. (L687)
- [ ] **Q6** Chat brand strategy: system message only or re-injected per turn? Recommendation: system message only. (L689)
- [ ] **Q7** Agent brand depth: full block or thin slice? Recommendation: full block by default. (L691)

### Data & Context
- [ ] **Q8** Tag vocabulary expansion for B2B/non_profit/wealth_management: global or per-vertical? Product decision. (L697)
- [ ] **Q9** KB ingestion UX: file upload, URL scrape, manual notes, bulk paste? (L699)
- [ ] **Q10** KB content types at launch: docs, web pages, plain text, all? (L701)
- [ ] **Q11** Curated knowledge content sourcing: internal, partner, AI+human review? Product decision. (L703)
- [ ] **Q12** KB retrieval: always-on or selective? Recommendation: always-on, then optimise. (L705)
- [ ] **Q13** Asset auto-suggestion: auto-propose or user-invoked? Recommendation: auto-suggest in Phase 2. (L707)
- [ ] **Q14** Non-image asset AI analysis (PDF, video, audio): v2 conversation. (L709)

### Compliance & Infrastructure
- [ ] **Q15** SOC 2 readiness timeline: target audit window? (L713)
- [ ] **Q16** EU AI Act risk classification: confirm with legal review pre-launch. (L715)
- [ ] **Q17** Data residency at launch: do early customers require EU-region? If yes → Azure AI Foundry becomes launch dependency. (L717)
- [ ] **Q18** Cost controls: per-org daily spend cap, per-feature concurrency limit, alerting threshold. Easy now, painful later. (L719)

---

## SUMMARY

| Category | Item Count |
|----------|-----------|
| Client wrapper requirements | 9 |
| Context block requirements | 13 + rules |
| Unified email component | 6 |
| Agent redefinition | 4 |
| Library structure | 1 |
| Schema changes | 6 |
| Multi-tenant isolation | 5 |
| Field-semantics | 5 |
| Insights command centre | 4 |
| Trust progression phases | 4 |
| Hyperpersonalisation | 3 |
| Observability | 5 |
| Compliance | 8 |
| Infrastructure | 4 |
| Migration PRs | 7 |
| Risks | 5 |
| Open questions | 18 |

---
---

# IMPLEMENTATION PLAN — June 1 to August 15, 2026

## Development Process Overview

### Approach
This plan covers **Jun 1 – Aug 15 2026**, split into **5 development Sprints + a 2-week Test & Polish phase**. Sprints run **Mon–Fri**. Development must be feature-complete by **2026-08-01 (Fri)** — the development cutoff. **Aug 3 (Mon) – Aug 15 (Sat)** is reserved for QA, regression fixes, and polish: no new feature code.

Sprints 1–4 are 2 weeks each (10 working days). **Sprint 5 is compressed to 1 week** (Jul 27 – Aug 1) to free up the 2-week Test & Polish window — this puts significant scope pressure on PR 13 + PR 14, originally scoped to 3 weeks (2 dev + 1 buffer). Scope cuts at the Week-8 checkpoint are likely.

### Development Principles
1. **Layered Construction**: Each PR builds on the previous one's infrastructure. PR 9 is the foundation of everything.
2. **Backend-First**: .NET BFF services are written first, then Angular frontend integration follows.
3. **Incremental Delivery**: Each PR is independently deployable, no breaking changes.
4. **Test-Driven**: Every service ships with unit + integration tests.
5. **Schema-First**: DB migrations are created in the PR's first commit, then services are built on top.

### Dependency Chain
```
PR 9 ──→ everything
PR 10 ──→ PR 11 (agent migration), PR 13 (action handlers)
PR 11p ──→ field-semantics block, audience block, Phase 2 depth
PR 12 ──→ PR 13 (rich contextual AI content)
PR 13 ──→ PR 14 (Today page) + Phase 2 trust progression
```

### Sprint Calendar (revised 2026-05-29)

| Sprint | Start (Mon) | End (Fri) | PRs | Focus |
|--------|-------------|-----------|-----|-------|
| Sprint 1 | 2026-06-01 | 2026-06-12 | PR 9 | Foundation + Client Wrapper |
| Sprint 2 | 2026-06-15 | 2026-06-26 | PR 10 | Unified Email Component |
| Sprint 3 | 2026-06-29 | 2026-07-10 | PR 11 + PR 11p | Agent Migration + Field-Tagging UI |
| Sprint 4 | 2026-07-13 | 2026-07-24 | PR 12 | Remaining Context Blocks |
| Sprint 5 | 2026-07-27 | 2026-08-01 | PR 13 + PR 14 | Recommendation Actions + Today Page (compressed) |
| Test & Polish | 2026-08-03 | 2026-08-15 | — | QA, regression fixes, polish — no new feature code |

### Decision Checkpoints
- **Week 4 (after PR 10):** Is the unified email component working as keystone? If not → cut journey-content to v2, lean on templates.
- **Week 8 (after PR 12):** Has the field-tagging UI shipped and are users tagging? If not → audience block returns sparse data, Phase 2 at half power.
- **Week 10 (after PR 13):** Is recommendation→action producing acceptable content? If not → allocate prompt-tuning time before PR 14.

---

## EPIC 1: AI Foundation & Client Wrapper
**Sprint 1 (Jun 1 – Jun 13)**

### Story 1.1: Create AI Project Structure
> Set up the AI layer skeleton within the .NET backend.

**Task 1.1.1: Create AI Domain Project**
- Subtask: Create `AI/` namespace structure under `src/backend/Core/`
- Subtask: Set up folder structure: `Client/`, `Prompts/`, `Context/`, `Knowledge/`, `Agents/`, `Schemas/`, `Usage/`
- Subtask: Create DI registration classes (`AddAiServices()`)
- Depends on: —

**Task 1.1.2: AI Configuration Setup**
- Subtask: Define `AI_PROVIDER`, `AI_REGION`, `AI_MODEL_DEFAULT` environment variables
- Subtask: Create `AiOptions` configuration class (provider, region, model defaults, cost tables)
- Subtask: Per-feature model selection config (Sonnet vs Haiku mapping)
- Depends on: 1.1.1

### Story 1.2: Client Wrapper Service (IAiClient)
> Central service through which all AI calls flow.

**Task 1.2.1: IAiClient Interface & Implementation**
- Subtask: Define `IAiClient` interface: `Generate({ feature, system, messages, modelClass })` → `{ content, usage, metadata }`
- Subtask: `AnthropicAiClient` concrete implementation (Anthropic SDK)
- Subtask: Provider-agnostic internal contract (cost translation, filtering, retry, validation)
- Depends on: 1.1.2

**Task 1.2.2: Retry & Error Handling**
- Subtask: Transient failure retry with exponential backoff (Polly)
- Subtask: Permanent failure graceful degradation (template-based fallback)
- Subtask: Errors are never swallowed, structured logging
- Depends on: 1.2.1

**Task 1.2.3: Output Validation**
- Subtask: Schema-based output validation (C# record types + FluentValidation)
- Subtask: Parse → validate → retry with corrective prompting on failure
- Subtask: After 2 failures → typed error return
- Depends on: 1.2.1

**Task 1.2.4: Content Filtering**
- Subtask: PII detection in outputs
- Subtask: Banned-content checks (profanity, regulated-topic)
- Subtask: Redaction logging (what was filtered and why)
- Subtask: Customer-configurable thresholds
- Depends on: 1.2.1

### Story 1.3: Usage Logging & Cost Tracking
> Mandatory logging on every AI call.

**Task 1.3.1: ai_usage Schema Migration**
- Subtask: Create EF Core migration: add new columns to `ai_usage` table
  - `user_id`, model, `latency_ms`, success, `error_message`, `created_at`
  - `prompt_hash`, `output_hash`, `consent_status`, `data_residency_region`
  - `trace_id`, `content_filter_outcome`
- Subtask: Vendor-neutral SQL (no Supabase-specific syntax)
- Depends on: 1.1.1

**Task 1.3.2: Usage Log Service**
- Subtask: `IAiUsageLogger` service: log `org_id`, `user_id`, feature, model, tokens in/out, cost, latency, success/failure on every call
- Subtask: Cost calculation service (per-provider pricing tables)
- Subtask: `trace_id` audit linkage
- Depends on: 1.3.1, 1.2.1

### Story 1.4: First 3 Context Blocks (brand, org, industry)
> Minimal context blocks needed for email-generate proof.

**Task 1.4.1: Context Block Base**
- Subtask: `IContextBlock<T>` interface: `LoadBlockContextAsync(orgId, options?)` → structured context object
- Subtask: `ToPromptString()` method on context objects
- Subtask: Graceful degradation: missing/sparse data → empty stub, never throw
- Depends on: 1.1.1

**Task 1.4.2: Brand Context Block**
- Subtask: Load brand info from `brand_settings` + `color_roles` JSONB
- Subtask: Brand tonality, voice, visual identity access
- Depends on: 1.4.1

**Task 1.4.3: Org Context Block**
- Subtask: Load org info from `organizations` table
- Depends on: 1.4.1

**Task 1.4.4: Industry Context Block**
- Subtask: Load industry info from `industry_template_configs` table
- Depends on: 1.4.1

### Story 1.5: Email-Generate Proof of Pattern
> Run existing email-generate through the new architecture with byte-identical output.

**Task 1.5.1: Email-Generate Migration**
- Subtask: Analyze existing email-generate endpoint
- Subtask: Re-implement via new client wrapper + context blocks
- Subtask: Byte-identical output verification (side-by-side test)
- Depends on: 1.2.1, 1.4.2, 1.4.3, 1.4.4

**Task 1.5.2: System/Template Field Tags Seed**
- Subtask: Seed 11 system fields with universal defaults
- Subtask: Template fields per industry seed framework
- Depends on: 1.3.1

### Story 1.6: Multi-Tenant Isolation (AI Layer)
> Tenant isolation for AI tables.

**Task 1.6.1: Tenant Scoping**
- Subtask: `org_id` scope enforcement on all AI tables
- Subtask: Wrapper reads `org_id` from authenticated session
- Subtask: Application-layer tenant filtering
- Depends on: 1.2.1, 1.3.1

### Story 1.7: Prompt Management
> Prompts stored in dedicated files/classes, not inline.

**Task 1.7.1: Prompt Storage**
- Subtask: Per-feature system prompt classes in `Prompts/`
- Subtask: Code review checklist prohibiting inline prompts
- Depends on: 1.1.1

=== PR 9: Foundation + Email-Generate Proof ===
> **Scope:** AI client wrapper (full — retry, model selection, output validation, content filtering, cost calculation), usage logging, 3 context blocks (brand/org/industry), email-generate proof, ai_usage schema, system/template field tag seed, multi-tenant isolation, prompt management.
> **Customer-visible:** No
> **Review:** End of Sprint 1 (Jun 13)

---

## EPIC 2: Unified Email-Content Component
**Sprint 2 (Jun 16 – Jun 27)**

### Story 2.1: Backend Unified Email Endpoint
> All branded email generation from a single endpoint.

**Task 2.1.1: Unified Email Generation Service**
- Subtask: Implement `GenerateBrandedEmail({ intent, context, cta?, structuralOptions? })` service
- Subtask: Support 3 consumers: email editor, journey editor, recommendation action handler
- Subtask: Headless caller support (API call without rendering modal/UI)
- Depends on: PR 9

**Task 2.1.2: Context Type Refactoring**
- Subtask: Replace `emailId` with discriminated context: `campaign_email | journey_step | standalone`
- Subtask: Context-aware CTA: `journey_step` + `eventId` → event registration URL pre-fill
- Subtask: `standalone` → user provides or toggles off
- Depends on: 2.1.1

**Task 2.1.3: BFF Endpoint**
- Subtask: Create unified email endpoint under `src/backend/Core/BackendForFrontend/`
- Subtask: Load context blocks based on `kind`, compose prompt, call client wrapper
- Depends on: 2.1.1, 2.1.2

### Story 2.2: Angular Email Component Extraction
> Extract existing ~300-line AIEmailModal to shared/reusable component.

**Task 2.2.1: AIEmailModal Component Refactoring**
- Subtask: Analyze existing component
- Subtask: Move to shared component under `src/frontend/src/app/shared/`
- Subtask: Update email editor and journey editor integrations
- Depends on: 2.1.3

**Task 2.2.2: Journey Editor Wire-up**
- Subtask: Call unified email component from journey editor
- Subtask: Auto-populate journey step context
- Subtask: E2E test: journey → AI email generation flow
- Depends on: 2.2.1

=== PR 10: Unified Email-Content Component ===
> **Scope:** Shared email generation UI component, context type refactoring, unified backend endpoint, journey editor wire-up, context-aware CTA.
> **Customer-visible:** Yes — journey emails can be AI-generated.
> **Review:** End of Sprint 2 (Jun 27)
> **🔴 Decision Checkpoint (Week 4):** Is the unified email component working as keystone?

---

## EPIC 3: Agent Migration & Field-Tagging UI
**Sprint 3 (Jun 30 – Jul 11)**

### Story 3.1: Form/Event Agent Migration
> Agents stop sending confirmation emails → journeys take over.

**Task 3.1.1: Agent Redefinition**
- Subtask: Apply "Agent" = multi-step, conversational, decision-making entity definition
- Subtask: Reclassify single-call email senders as handlers/generators
- Depends on: PR 10

**Task 3.1.2: Confirmation Email → Journey Migration**
- Subtask: Move form-agent and event-agent creation logic to journeys
- Subtask: Journey's first step = confirmation email
- Subtask: Implement .ics attachment as journey-email feature
- Depends on: 3.1.1

**Task 3.1.3: Agent Runtime Narrowing**
- Subtask: Narrow agent runtime: inbound reply handling, multi-turn, registration context only
- Subtask: Remove HTML generation duplication (email-generate / form-agent / event-agent)
- Subtask: Simplify agents to "enrol in journey + open inbound thread"
- Depends on: 3.1.2

=== PR 11: Form/Event Agent Migration ===
> **Scope:** Agents stop sending confirmation emails, journeys take over. Agent runtime narrowed. HTML duplication removed.
> **Customer-visible:** Partial (agent behavior change)
> **Review:** Mid-Sprint 3 (Jul 7)

### Story 3.2: Field-Tagging UI (Settings Page)
> UI for tagging contact fields with semantic labels.

**Task 3.2.1: Field-Tagging Settings Page**
- Subtask: Create dedicated Angular settings page (`/settings/ai-ready` equivalent)
- Subtask: Prominently display readiness percentage
- Subtask: v1 vocabulary: 8 controlled semantic tags with CHECK constraint
- Depends on: PR 9

**Task 3.2.2: 3-Tier Tag Rendering**
- Subtask: System fields (11): read-only, pre-tagged, universal defaults
- Subtask: Template fields (per industry): read-only, pre-tagged
- Subtask: Custom fields: interactive + AI suggestion
- Depends on: 3.2.1

**Task 3.2.3: AI Tag Suggestion**
- Subtask: AI-powered tag suggestion for custom fields
- Subtask: User accepts or overrides suggestion
- Subtask: Update `ai_suggested_tags` in `contact_field_definitions` table
- Depends on: 3.2.2

=== PR 11p: Field-Tagging UI ===
> **Scope:** Contact field semantic tagging settings page, 3-tier tagging, AI suggestion, readiness %.
> **Customer-visible:** Yes — new settings page.
> **Review:** End of Sprint 3 (Jul 11)

---

## EPIC 4: Remaining Context Blocks
**Sprint 4 (Jul 14 – Jul 25)**

### Story 4.1: Methodology & Plan Context Blocks
> Load marketing methodology and plan contexts.

**Task 4.1.1: Methodology Context Block**
- Subtask: Load data from `marketing_disciplines`, `goal_types`, `programmes`, `tag_labels` tables
- Subtask: Graceful degradation
- Depends on: PR 9 (context block base)

**Task 4.1.2: Plan Context Block**
- Subtask: Load data from `marketing_plans` + `plan_goals` + `plan_programmes` tables
- Depends on: PR 9

### Story 4.2: Field-Semantics & Audience Context Blocks
> Load contact field semantics and audience context.

**Task 4.2.1: Field-Semantics Context Block**
- Subtask: Load semantic data from `contact_field_definitions` extension columns
- Depends on: PR 11p (field tags populated)

**Task 4.2.2: Audience Context Block**
- Subtask: Build audience context from `audiences` + `audience_contacts` + field-semantics block
- Subtask: `audience_contexts` materialized view/table schema migration
- Depends on: 4.2.1

### Story 4.3: Insights & Knowledge Context Blocks
> Cross-org benchmarks and knowledge base integration.

**Task 4.3.1: Insights Context Block**
- Subtask: Cross-org aggregate benchmarks (privacy-respecting)
- Subtask: Minimum-N threshold (5-10) — below threshold → return "n/a"
- Subtask: Cross-org reporting via separate service-role view
- Depends on: PR 9

**Task 4.3.2: Knowledge Context Block**
- Subtask: KB tables — per-org + curated content
- Subtask: Vector search Top-K, filter by `org_id`
- Subtask: Scope enforcement in retrieval function, not caller
- Subtask: Generalize knowledge block from chat-only to all features
- Depends on: PR 9

### Story 4.4: Assets Context Block
> Include content assets in AI context.

**Task 4.4.1: Assets Context Block**
- Subtask: Load AI-tagged assets from `content_assets` table
- Subtask: Include asset metadata + tag info in context
- Depends on: PR 9

### Story 4.5: Feature → Block Composition Wiring
> Implement which blocks compose for each feature.

**Task 4.5.1: Composition Registry**
- Subtask: Feature → blocks mapping registry (email-generate, journey-content, form-generate, chat, strategy, insights, recommendation)
- Subtask: Dynamic block loading based on feature configuration
- Depends on: 4.1.1, 4.1.2, 4.2.2, 4.3.1, 4.3.2, 4.4.1

=== PR 12: Context Blocks (methodology, plan, insights, audience, assets, knowledge, field-semantics) ===
> **Scope:** Remaining 7 context block services. Knowledge block generalized from chat-only to all features. Feature → block composition registry.
> **Customer-visible:** No — substrate/infrastructure.
> **Review:** End of Sprint 4 (Jul 25)
> **🔴 Decision Checkpoint (Week 8):** Has the field-tagging UI shipped and are users tagging?

---

## EPIC 5: Recommendation Actions & Command Centre
**Sprint 5 (Jul 28 – Aug 15)**

### Story 5.1: Recommendation Action Handlers
> "Build the campaign" action creates real audiences, journeys, and AI content.

**Task 5.1.1: Recommendation Action Schema**
- Subtask: Add to `recommendation_actions`: `ai_call_trace_id`, `action_journey_id`, `action_audience_id`
- Subtask: Add to `ai_recommendations`: `confidence_type`, `source_signal_id`, `plan_goal_id`, `programme_id`
- Subtask: EF Core migration
- Depends on: PR 12

**Task 5.1.2: Action Handler Implementation**
- Subtask: "Build the campaign" action → create real audience
- Subtask: Create journey with AI content (via unified email component)
- Subtask: Segment-level hyperpersonalisation (Phase 2): different copy per audience segment
- Depends on: 5.1.1, PR 10

**Task 5.1.3: Confidence Labelling**
- Subtask: Rules-based = "Counted", AI-generated = "Suggested" distinction
- Subtask: Display confidence type on recommendation card
- Depends on: 5.1.2

**Task 5.1.4: Preview-and-Confirm Flow**
- Subtask: One-click never sends directly
- Subtask: Preview: audience preview + journey/campaign template + projected impact
- Subtask: Audit-trail entry on every commit
- Depends on: 5.1.2

=== PR 13: Recommendation Action Handlers ===
> **Scope:** Action handlers create real audiences + journeys + AI content. Phase 2 live. Segment-level hyperpersonalisation. Confidence labelling. Preview-and-confirm.
> **Customer-visible:** Yes — Phase 2 trust progression.
> **Review:** Mid-Sprint 5 (Aug 8)
> **🔴 Decision Checkpoint (Week 10):** Is recommendation→action producing acceptable content?

### Story 5.2: Today Page (Command Centre)
> Insights revamp customer-facing surfaces.

**Task 5.2.1: Today Page (Insights Command Centre)**
- Subtask: Implement new IA: Today (command centre) / Grow / Engage / Retain / Earn
- Subtask: Angular routing + page structure
- Depends on: PR 13

**Task 5.2.2: Recommendation Cards**
- Subtask: Insight + Recommendation + Action fused single card component
- Subtask: Confidence labelling display (Counted vs Suggested)
- Subtask: Action buttons (preview-and-confirm flow integration)
- Depends on: 5.2.1, 5.1.3

**Task 5.2.3: Retain Dashboard**
- Subtask: Retain dashboard implementation
- Subtask: Retention metrics + recommendation integration
- Depends on: 5.2.1

**Task 5.2.4: Command Palette**
- Subtask: Quick-action command palette
- Subtask: Keyboard shortcuts
- Depends on: 5.2.1

### Story 5.3: Launch Readiness — Observability & Compliance
> Pre-launch observability and compliance checklist.

**Task 5.3.1: Observability Verification**
- Subtask: Verify cost tracking per org/feature/month
- Subtask: Verify latency tracking per feature
- Subtask: Verify validation retry logging
- Subtask: Verify `trace_id` audit linkage end-to-end
- Depends on: PR 13

**Task 5.3.2: GDPR Compliance Check**
- Subtask: Mandatory GDPR requirements checklist
- Subtask: Verify PII detection in outputs
- Subtask: Verify content filtering and redaction logging
- Depends on: 5.3.1

=== PR 14: Today Page + Retain Dashboard + Command Palette ===
> **Scope:** Insights command centre, Today page, recommendation cards, Retain dashboard, command palette. Launch-ready surface.
> **Customer-visible:** Yes — launch-ready.
> **Review:** End of Sprint 5 (Aug 15)

---

## Implementation Summary

| Sprint | Dates | PR | Epic | Customer-Visible |
|--------|-------|----|------|-------------------|
| Sprint 1 | Jun 1–13 | PR 9 | Foundation & Client Wrapper | ❌ |
| Sprint 2 | Jun 16–27 | PR 10 | Unified Email Component | ✅ |
| Sprint 3 | Jun 30 – Jul 11 | PR 11 + PR 11p | Agent Migration + Field-Tagging | Partial / ✅ |
| Sprint 4 | Jul 14–25 | PR 12 | Context Blocks | ❌ |
| Sprint 5 | Jul 28 – Aug 15 | PR 13 + PR 14 | Recommendations + Today Page | ✅ / ✅ |

| Metric | Count |
|--------|-------|
| Epics | 5 |
| Stories | 17 |
| Tasks | 39 |
| PRs | 7 |
| Decision Checkpoints | 3 |

## Risk Notes
- **R1:** Form/event agent deprecation → if live customers exist, deprecation becomes a migration concern
- **R2:** Field-tagging UI is UX-heavy, must feel manageable for orgs with 40+ fields
- **R3:** Prompt tuning: plan 2-3 days side-by-side testing for each migrated surface
- **R4:** Weeks 5-8 are invisible: nothing customer-facing moves — this is expected, communicate it
- **R5:** Customer feedback loop: if no friendly sees Phase 1 by week 6, Phase 2 is built in the dark
