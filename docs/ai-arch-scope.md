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

## Handover Alignment — 2026-06-10 (updated 2026-06-16 for v2 brief)

The Azure AI Foundry handover and the Brand Kit / Assets handoff clarify how the PR plan should be interpreted before starting Story 1.4. The v2 scope brief (`sweetspot-ai-deop-scope-brief-v2.docx`, 2026-06-16) locks four decisions captured in this section.

### Provider scope — LOCKED

**Azure AI Foundry is the launch provider.** Microsoft funds this engagement specifically to land sweetspot on Foundry; the substrate is built on Foundry from day one. Anthropic-direct remains as a **legacy adapter** for handover continuity and is removed post-launch (Anthropic removal trigger: Foundry sustained at 100% prod traffic with acceptable error rate for ≥30 days — exact threshold tracked separately).

`Task 1.2.5: Azure AI Foundry Provider Adapter` is **launch-blocking** (not provider-readiness). Both `IAiClient` implementations (`AzureFoundryAiClient`, `AnthropicAiClient`) live in `src/backend/Core/AI/SSP.AI/Client/`; runtime selection is config-driven via `Ai:Provider`. **Code default** in `ServiceCollectionExtensions.NormalizeProvider` is `azure-foundry` (flipped 2026-06-16); `AnthropicAiClient` is marked `[Obsolete]` with file-scoped CS0618 suppressions at the sanctioned legacy registration and test sites.

**Open deployment-config item (not code):** `appsettings.common.json` still pins `Ai:Provider="anthropic"` with `BaseUrl=https://api.anthropic.com` and Anthropic model IDs. Flipping `Ai:Provider` to `azure-foundry` in deployed environments requires a coordinated change to `Ai:BaseUrl` (Foundry endpoint), `Ai:Models` (Foundry deployment names), and the `Ai:ApiKey` Key Vault references in `appsettings.partial.{env}.json` (currently `AiAnthropicApiKey`). Tracked as a deployment/infrastructure task — not part of EPIC 1 code scope.

### AI substrate ownership — LOCKED (Option A)

**Option A: .NET native in SSP.** Confirmed per v2 brief §8.1 and the existing Sprint 1 implementation:

- The AI substrate lives inside the Sweetspot .NET backend under `src/backend/Core/AI/SSP.AI/`.
- Context loaders read tenant data through internal EF Core-backed services and repository conventions.
- No external API contracts (e.g. `GET /brand/context`) are exposed for substrate consumption.

Option B (Node microservice) is out of scope — kept as historical reference only.

### Brand Kit consumption

Brand Kit maps to the `brand` context block. The block must expose a typed context object with two responsibilities:

- Prompt-facing tonal fields: `voice_description`, `tone_tags`, `values`, `one_liner`, and `exists`.
- Renderer-facing visual fields: colors, fonts, logos, resolved color roles, `email_footer_html`, and template banners.

`ToPromptString()` must include only the prompt-facing tonal fields. Visual fields are passed to deterministic renderers and template engines; they must not be dumped into the LLM prompt.

**Ownership:** `brand_settings` table, EF Core migration, and write API endpoints are owned **end-to-end by Click engineering** (v2 brief §5.10). Deop consumes through the `IBrandKitReader` seam only — no Deop-side migration or write path for this table. Schema coordination conversation in week 2; until the schema lands, the reader returns null and the block degrades gracefully.

### Assets consumption

Assets are consumed as **pre-enriched metadata**, not raw prompt material. The enrichment flow is:

`Upload → Blob Storage → Queue → Assets Processor → GPT-4o → DB metadata`

The usable asset metadata is `ai_description`, `dominant_colors`, `suggested_use`, `tone`, and `is_analysed`. AI features may use selected enriched asset metadata as a tone/content reference, but semantic "find me the best asset" behavior is deferred until embeddings / pgvector are available.

Image-only enrichment is in scope for this plan. Document, video, and audio enrichment are deferred unless a new explicit task is added.

### AI surface parity — launch vs v1.1

The v2 scope brief narrows Deop's launch deliverables to **three customer-shipping AI features**. Web Agent and the broader surface contracts move to v1.1.

**Launch (in EPIC 1 / PR 9 + targeted hotfixes):**

| Surface | Roadmap treatment |
|---------|-------------------|
| Email generation, refinement | PR 9 keystone path — `EmailGeneratePromptBuilder` + `EmailGenerateOutput` schema. |
| Form generation | Deliverable 5.6 (v2 brief). Composes brand + org + industry; returns structured form JSON. |
| Contact-field semantic tagging | Deliverable 5.7. Haiku-class classification + generation; returns `{description, tags[]}`. |

**v1.1 / post-launch backlog (out of EPIC 1 scope):**

| Surface | Status |
|---------|--------|
| Web Agent (website chatbot) | v1.1. Per v2 brief, Web Agent is the **only** product-facing agent type — no `form-agent`, `event-agent`, `strategy-agent`, `insights-agent`. |
| Forms v2 generation, refinement, field mapping | v1.1 — moved from PR 12. |
| Landing page generation, refinement, layout switching | v1.1 — moved from PR 12. |
| Events Create-with-AI | v1.1 — moved from PR 12. |
| Profile research | v1.1 backlog (onboarding accelerator). |
| Insights ask, social generation, inbound classification | v1.1 backlog. |
| Recommendation action handlers, Today page, Retain dashboard, command palette | v1.1 — entire EPIC 5 deferred. |
| Methodology / Plan / Audience / Insights / Assets context blocks | v1.1 — only brand/org/industry/profile/event/brief/contact-fields/knowledge/field-semantics blocks (9 total per v2 brief §4.2) are in launch scope. |

The roadmap language must not imply multiple product agent types.

### Prototype loader mapping

| Prototype loader | Sweetspot context target | Planning note |
|------------------|--------------------------|---------------|
| `loadBrandContext` | `BrandContext` | Split prompt tonal fields from renderer visual fields. |
| `loadOrgContext` | `OrgContext` | Use Sweetspot account/org conventions; include compliance basics needed by generated content. |
| `loadIndustryContext` | `IndustryContext` | Gracefully fall back to defaults when no industry config exists. |
| `loadProfileContext` | `BrandContext` + future `KnowledgeContext` | Voice/profile facts must not be lost; decide exact split during prompt migration. |
| `loadContactFieldsContext` | future `FieldSemanticsContext` | Field/tag/merge-token behavior belongs with PR 11p/PR 12 field semantics. |
| `loadKnowledgeContext` | future `KnowledgeContext` | Generalise from chat-only to all eligible features in PR 12. |
| asset library access | future `AssetsContext` | Load selected enriched metadata only; semantic search waits for embeddings. |
| `industry-examples` | frontend/helper data | Not a core server-side AI context block unless later feature work proves it is needed. |

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
- [ ] **1.10** Spend-cap enforcement: check per-account daily AI spend before provider invocation; blocked calls must not call the provider or incur cost.
- [ ] **1.11** Persist structured content-filter outcomes to `ai_usage.content_filter_outcome`; schema-only support is not sufficient for launch compliance.

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
| 2.4 | brand | Brand Kit read contract (`brand_settings`, color roles, profile/voice fields, template banners) | 164 |
| 2.5 | org | `organizations` table | 165 |
| 2.6 | industry | `industry_template_configs` table | 166 |
| 2.7 | methodology | `marketing_disciplines`, `goal_types`, `programmes`, `tag_labels` | 167 |
| 2.8 | field-semantics | `contact_field_definitions` extension columns | 168 |
| 2.9 | audience | `audiences` + `audience_contacts` + field-semantics | 169 |
| 2.10 | plan | `marketing_plans` + `plan_goals` + `plan_programmes` | 170 |
| 2.11 | insights | Cross-org aggregate benchmarks (privacy-respecting) | 171 |
| 2.12 | knowledge | KB tables — per-org + curated, vector search Top-K | 172 |
| 2.13 | assets | `content_assets` enriched metadata (`ai_description`, `dominant_colors`, `suggested_use`, `tone`, `is_analysed`) | 173 |

### Feature → Block Composition

| Feature | Blocks Composed | Line |
|---------|----------------|------|
| email-generate | brand + org + industry + audience + plan + selected enriched assets + (optional) knowledge | 421 |
| journey-content | brand + org + industry + journey-context + audience + plan + assets | 422 |
| form-generate | brand + org + industry | 423 |
| Web Agent | brand + org + industry + knowledge + conversation history | 424 |
| strategy workflow | brand + org + industry + methodology + plan + insights + knowledge | 425 |
| insights workflow | org + industry + methodology + plan + insights + knowledge | 426 |
| recommendation action | all of the above + signal context + recommendation reasoning | 427 |

### Brand and Assets Rules

- [ ] **2.14** Brand visual fields are renderer inputs, not prompt text. `BrandContext.ToPromptString()` includes tonal fields only.
- [ ] **2.15** Assets context contains selected enriched metadata only; do not load raw files, full libraries, or unanalysed assets into prompts.
- [ ] **2.16** Semantic asset search is deferred until embeddings / pgvector exist. Until then, features may use explicit user-selected assets or simple metadata filters.

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

- [ ] **4.1** "Agent" = customer-visible Web Agent: multi-step, conversational, decision-making website/chat experience. Single-call email senders, form generators, event generators, strategy workflows, and insights workflows are handlers/generators/workflows, not product agent types. (L201)
- [ ] **4.2** Form-agent and event-agent **creation** logic (confirmation email) moves to journeys. Journey's first step = confirmation email. .ics attachment becomes a journey-email feature. (L205)
- [ ] **4.3** Runtime conversation handling, where needed, routes through the Web Agent / inbox conversation model rather than separate Form Agent or Event Agent product surfaces. (L207)
- [ ] **4.4** HTML generation duplication (email-generate / form-agent / event-agent) disappears. (L209)
- [ ] **4.5** After PR 11, no customer-facing Form Agent or Event Agent remains. The only named product agent type is Web Agent unless product explicitly approves another.

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
  WebAgent/      — Website/chat agent turn handling
  Workflows/     — Strategy, insights, event, landing, and form AI workflows/generators
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
- [ ] **14.2** Azure AI Foundry provider adapter is tracked explicitly in Task 1.2.5. It remains provider-readiness/post-launch unless Deop or Click Engineering confirms Foundry is a launch dependency. (L653)
- [ ] **14.3** Environment variables for provider selection: `AI_PROVIDER`, `AI_REGION`, `AI_MODEL_DEFAULT` — config-driven, not hardcoded. (L635)
- [ ] **14.4** `data_residency_region` column logged from day one. (L637)

---

## 15. MIGRATION — 7 PR Sequence

> **Important:** The original PR plan assumes Next.js file paths. Below is the intent — actual implementation paths will be in the Sweetspot Angular + .NET repo structure.

| PR | Name | Scope | Customer-visible? | Line |
|----|------|-------|-------------------|------|
| PR 9 | Foundation + email-generate proof | AI client wrapper service (full — retry, model selection, output validation, content filtering, cost calc), usage logging, spend-cap enforcement, persisted content-filter outcomes, context blocks (brand, org, industry). Migrate email-generate as byte-identical proof of pattern. Extend ai_usage schema. Seed system/template field tags. | No | 459 |
| PR 10a | Unified email backend + contract (Deop) | Unified email generation service, context type refactoring, BFF endpoint, headless caller support, integration contract & hand-off documentation. | Partial — headless callers work | 460 |
| PR 10b | Angular email component (Click) | AIEmailModal refactor to shared component, journey editor wire-up, E2E tests. Depends on PR 10a. | Yes — journey emails AI-generated | 460 |
| PR 11 | Web Agent cleanup + form/event confirmation migration | Form/event confirmation senders stop being treated as agents → journeys take over. Runtime conversation handling routes through Web Agent / inbox conversation model. HTML duplication gone. | Partial | 461 |
| PR 11p | Field-tagging UI | Settings page for tagging contact fields with semantic labels. System fields read-only, template fields read-only, custom fields interactive + AI suggestion. Readiness %. | Yes | 462 |
| PR 12 | Context blocks + AI surface parity wiring | Build remaining 7 context block services. Knowledge block generalised from Web Agent-only to all eligible features. Add explicit surface wiring tasks for Forms v2, field mapping, landing pages, Events Create-with-AI, Web Agent, profile research, insights/social/inbound classification, and feature-key registry. | No — substrate | 463 |
| PR 13 | Recommendation action handlers | "Build the campaign" action creates real audiences, real journeys with AI content. Phase 2 live. Segment-level hyperpersonalisation. | Yes — Phase 2 | 464 |
| PR 14 | Today page + Retain dashboard + command palette | Insights revamp customer-facing surfaces. | Yes — launch-ready | 465 |

### Dependencies (L469-475)

```
PR 9 ──→ everything
PR 10 ──→ PR 11 (Web Agent cleanup + confirmation handler migration), PR 13 (action handlers)
PR 11p ──→ field-semantics block, audience block, Phase 2 depth
PR 12 ──→ PR 13 (rich contextual AI content)
PR 13 ──→ PR 14 (Today page) + Phase 2 trust progression
```

### Decision Checkpoints

- [ ] **Week 4 (after PR 10a):** Deop gate: Is the unified email BFF endpoint complete and tested (headless callers verified)? Click gate: Has Click engineering started Angular integration? If Deop passes but Click hasn't started → headless/API mode works, lean on templates for UI-triggered generation. (L481)
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
- [ ] **Q6** Web Agent brand strategy: system message only or re-injected per turn? Recommendation: system message only. (L689)
- [x] **Q7** Product agent taxonomy: **RESOLVED — Web Agent only.** Form/event/strategy/insights are handlers, generators, or workflows unless product explicitly approves a new customer-facing agent type. Web Agent gets the full brand block by default; dial back per-agent if over-styling emerges. (L691)

### Data & Context
- [ ] **Q8** Tag vocabulary expansion for B2B/non_profit/wealth_management: global or per-vertical? Product decision. (L697)
- [ ] **Q9** KB ingestion UX: file upload, URL scrape, manual notes, bulk paste? (L699)
- [ ] **Q10** KB content types at launch: docs, web pages, plain text, all? (L701)
- [ ] **Q11** Curated knowledge content sourcing: internal, partner, AI+human review? Product decision. (L703)
- [ ] **Q12** KB retrieval: always-on or selective? Recommendation: always-on, then optimise. (L705)
- [ ] **Q13** Asset auto-suggestion: auto-propose or user-invoked? Recommendation: auto-suggest in Phase 2. (L707)
- [x] **Q14** Non-image asset AI analysis (PDF, video, audio): **RESOLVED — deferred.** Phase 1 assumes image-only enrichment output (`ai_description`, `dominant_colors`, `suggested_use`, `tone`, `is_analysed`). Document, video, and audio enrichment require a new explicit task. (L709)

### Compliance & Infrastructure
- [ ] **Q15** SOC 2 readiness timeline: target audit window? (L713)
- [ ] **Q16** EU AI Act risk classification: confirm with legal review pre-launch. (L715)
- [ ] **Q17** Data residency at launch: do early customers require EU-region? If yes → Azure AI Foundry becomes launch dependency. (L717)
- [ ] **Q18** Cost controls: per-org daily spend cap is now PR 9 follow-up scope; per-feature concurrency limit and alerting threshold remain open. (L719)
- [ ] **Q19** Deop consumption mode: Phase 1 assumes in-process .NET context loaders (Option A). If Deop requires a Node microservice (Option B), define `GET /brand/context` and enriched asset API contracts before implementation.

---

## SUMMARY

| Category | Item Count |
|----------|-----------|
| Client wrapper requirements | 11 |
| Context block requirements | 16 + rules |
| Unified email component | 6 |
| Agent redefinition | 5 |
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
| Open questions | 19 |

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
PR 10a (Deop) ──→ PR 10b (Click, Angular UI), PR 11 (Web Agent cleanup), PR 13 (action handlers)
PR 10b (Click) ──→ depends on PR 10a + Story 2.3 hand-off docs
PR 11p ──→ field-semantics block, audience block, Phase 2 depth
PR 12 ──→ PR 13 (rich contextual AI content)
PR 13 ──→ PR 14 (Today page) + Phase 2 trust progression
```

### Sprint Calendar (revised 2026-06-16 — v2 brief alignment)

| Sprint | Start (Mon) | End (Fri) | PRs | Focus |
|--------|-------------|-----------|-----|-------|
| Sprint 1 | 2026-06-01 | 2026-06-12 | PR 9 | Foundation + Client Wrapper — _shipped_ |
| Sprint 2 | 2026-06-15 | 2026-06-26 | PR 10a (Deop) + PR 10b (Click) | Unified Email Backend + Hand-Off Contract (Deop, 4 tasks). Angular UI integration (Click, 2 tasks — Click timeline). |
| Sprint 3 | 2026-06-29 | 2026-07-10 | PR 11 (3.1.1 only) + PR 11p | Field-Tagging UI (3.2.x) + Product Agent Definition (3.1.1). 3.1.2 + 3.1.3 demoted to v1.1 per v2 brief (journey + Web Agent deferred). |
| Sprint 4 | 2026-07-13 | 2026-07-24 | PR 12 (SPLIT) | Launch parts only: 4.2.1 (field-semantics) + 4.2.2 (audience) + 4.3.2 (knowledge) + 4.5.1 (composition registry) + 4.6.5a (knowledge wiring) + 4.6.7 (feature registry). Story 4.1, 4.3.1, 4.4.1, 4.6.1 refinement, 4.6.2/3/4/6 → v1.1 backlog. |
| Sprint 5 | 2026-07-27 | 2026-08-01 | _no PR 13/14_ | EPIC 5 fully v1.1 per v2 brief (Recommendation Actions + Today Page deferred). Pre-Launch Verification Gates (5.3.1 + 5.3.2) run here + into Test & Polish. |
| §5.10 Hotfix track | parallel Sprints 2-4 | — | Story 1.8 (1.8.5/1/2/3 shipped; 1.8.4/6/7/8/9 follow-up) | Capture-surface data layer + BFF endpoints + HNSW per v2 §5.10 + §5.8 |
| **Story 1.9 hotfix** | parallel Sprints 3-4 | — | Story 1.9 PR series | Launch context blocks (profile/event/brief/contact-fields) + form generation feature per v2 §4.2 + §5.6 |
| **Story 1.10** | Sprint 4 | — | Story 1.10 PR series | Launch readiness docs: handover README + Foundry memo + hour sign-off per v2 §5.1 + §5.9 |
| **Pre-Launch Verification Gates** | Sprint 5 + Test & Polish | — | Story 5.3 (reframed) | Observability + GDPR compliance gates per v2 §13 + §5.9 |
| Test & Polish | 2026-08-03 | 2026-08-15 | — | QA, regression fixes, polish — no new feature code |

### Decision Checkpoints
- **Week 4 (after PR 10a):** Deop gate: Is the unified email BFF endpoint complete and tested (headless callers verified)? Click gate: Has Click engineering started Angular integration? If Deop passes but Click hasn't started → headless/API mode works, lean on templates for UI-triggered generation.
- **Week 8 (after PR 12 launch parts):** Have the field-tagging UI + 9 launch context blocks shipped and is the composition registry routing them correctly? If not → tighten Story 1.9 / 4.x scope and prioritise email feature parity.
- **Week 10 (Sprint 5):** Pre-Launch Verification Gates running clean? If not → focus Test & Polish window on gate remediation.

---

## EPIC 1: AI Foundation & Client Wrapper
**Sprint 1 (Jun 1 – Jun 13)**

### Story 1.1: Create AI Project Structure
> Set up the AI layer skeleton within the .NET backend.
> _Status: complete — `src/backend/Core/AI/SSP.AI/` with Client/, Context/, Prompts/, Schemas/, Usage/, Tenancy/, Agents/ folders + `AddAiServices()` DI registration._

**Task 1.1.1: Create AI Domain Project**
- Subtask: Create `AI/` namespace structure under `src/backend/Core/`
- Subtask: Set up folder structure: `Client/`, `Prompts/`, `Context/`, `Knowledge/`, `WebAgent/`, `Workflows/`, `Schemas/`, `Usage/`
- Subtask: Create DI registration classes (`AddAiServices()`)
- Depends on: —

**Task 1.1.2: AI Configuration Setup**
- Subtask: Define `AI_PROVIDER`, `AI_REGION`, `AI_MODEL_DEFAULT` environment variables
- Subtask: Create `AiOptions` configuration class (provider, region, model defaults, cost tables)
- Subtask: Per-feature model selection config (Sonnet vs Haiku mapping)
- Depends on: 1.1.1

### Story 1.2: Client Wrapper Service (IAiClient)
> Central service through which all AI calls flow.
> _Status: complete — `IAiClient`, `AnthropicAiClient` (legacy), `AzureFoundryAiClient` (launch default), Polly retry, FluentValidation, content filtering, spend-cap, usage logging all wired via `AiClientBase` pipeline._

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

**Task 1.2.5: Azure AI Foundry Provider Adapter** _(launch-blocking, complete — `AzureFoundryAiClient` shipped)_
- Subtask: Implement Azure AI Foundry adapter behind `IAiClient` without changing feature callers
- Subtask: Map model classes (`generation`, `classification`, `reasoning`) to Foundry deployment names
- Subtask: Update provider-specific pricing/cost tables for Foundry deployments
- Subtask: Verify usage logging, spend caps, content filtering, validation retries, and graceful fallback still work through the adapter
- Subtask: Add side-by-side quality tests for Anthropic direct vs Foundry output on representative prompts
- Subtask: Flip default provider to `azure-foundry` in `ServiceCollectionExtensions.NormalizeProvider` so launch deployments hit Foundry without env override
- Depends on: 1.2.1, 1.3.2, 1.3.3

### Story 1.3: Usage Logging & Cost Tracking
> Mandatory logging on every AI call.
> _Status: complete — `ai_usage` migration `20260608155642_AddAiUsageTable.cs` (14 columns + composite indices), `AiUsageLogger`, `DailyAiSpendCapEnforcer` pre-call, `Account.DailyAiSpendCapUsd` column (migration `20260611112835`)._

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

**Task 1.3.3: Spend Cap Enforcement**
- Subtask: Add a pre-provider spend-cap check in the AI client pipeline
- Subtask: Support per-account daily cap and a default configured cap
- Subtask: Calculate current-day spend from `ssp.ai_usage` before provider invocation
- Subtask: Return a typed AI client error when capped
- Subtask: Add tests proving capped calls do not invoke the provider
- Depends on: 1.3.2, 1.2.1

**Task 1.3.4: Persist Content Filter Outcome**
- Subtask: Extend the content-filter contract to return structured outcome metadata
- Subtask: Persist PII categories, banned-term categories/severities, action taken, and direction to `ai_usage.content_filter_outcome`
- Subtask: Ensure sensitive matched substrings are never logged or persisted
- Subtask: Add tests for redacted output and rejected input/output paths
- Depends on: 1.3.2, 1.2.4

### Story 1.4: First 3 Context Blocks (brand, org, industry)
> Minimal context blocks needed for email-generate proof.
> _Status: complete — `IContextBlock<T>` base, `BrandContextBlock` (reads via `IBrandKitReader` seam; null until Click's `brand_settings` lands), `OrgContextBlock` (reads `Account`), `IndustryContextBlock` (deterministic defaults until Story 1.8.5 ships `industry_template_configs`). Tonal-only `ToPromptString()`._

**Task 1.4.1: Context Block Base**
- Subtask: `IContextBlock<T>` interface: `LoadBlockContextAsync(accountId, options?)` → structured context object
- Subtask: `ToPromptString()` method on context objects
- Subtask: Graceful degradation: missing/sparse data → empty stub, never throw
- Subtask: Define a shared `Exists` / empty-context convention for all AI context objects
- Subtask: Document the prototype-loader-to-Sweetspot-context mapping from the handover alignment section
- Depends on: 1.1.1

**Task 1.4.2: Brand Context Block**
- Subtask: Load Brand Kit through the internal Phase 1 read path (EF Core-backed service under Option A)
- Subtask: Return typed prompt-facing fields: `voice_description`, `tone_tags`, `values`, `one_liner`, `exists`
- Subtask: Return typed renderer-facing fields: colors, fonts, logos, resolved roles, `email_footer_html`, `template_banners`
- Subtask: Ensure `ToPromptString()` includes tonal fields only and excludes colors, fonts, logos, and raw visual data
- Subtask: Gracefully return `exists = false` / empty tonal context when Brand Kit is missing
- Depends on: 1.4.1

**Task 1.4.3: Org Context Block**
- Subtask: Load Sweetspot account/org identity through existing tenant conventions
- Subtask: Include industry key/template, organisation name, compliance/footer basics, and privacy/contact fields required by generated content
- Subtask: Gracefully fall back when optional org/profile fields are missing
- Depends on: 1.4.1

**Task 1.4.4: Industry Context Block**
- Subtask: Load industry info from `industry_template_configs` table
- Subtask: Include industry vocabulary, recurring-value labels, examples only when server-side consumers need them
- Subtask: Return deterministic defaults when no industry config exists
- Depends on: 1.4.1

### Story 1.5: Email-Generate Proof of Pattern
> Run existing email-generate through the new architecture with byte-identical output.
> _Status: complete on branch `deop/feature/email-generate-migration` — `EmailGeneratePromptBuilder`, `EmailGenerateOutput` + `EmailGenerateOutputValidator` registered under feature key `"email-generate"`. System/template field tags seeded (migration `20260615131227`)._

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
> _Status: complete — `Tenancy/` layer (`ITenantAiClient`, `TenantContextBlockLoader`, `DefaultTenantAiContext`) wraps `AccountId` injection per request; all context blocks reject `Guid.Empty`._

**Task 1.6.1: Tenant Scoping**
- Subtask: `org_id` scope enforcement on all AI tables
- Subtask: Wrapper reads `org_id` from authenticated session
- Subtask: Application-layer tenant filtering
- Depends on: 1.2.1, 1.3.1

### Story 1.7: Prompt Management
> Prompts stored in dedicated files/classes, not inline.
> _Status: complete — `IPromptBuilder` base, per-feature prompt builder classes under `SSP.AI/Prompts/<feature>/`._

**Task 1.7.1: Prompt Storage**
- Subtask: Per-feature system prompt classes in `Prompts/`
- Subtask: Code review checklist prohibiting inline prompts
- Depends on: 1.1.1

=== PR 9: Foundation + Email-Generate Proof ===
> **Scope:** AI client wrapper (full — retry, model selection, output validation, content filtering, cost calculation), usage logging, spend-cap enforcement, persisted content-filter outcomes, 3 context blocks (brand/org/industry), email-generate proof, ai_usage schema, system/template field tag seed, multi-tenant isolation, prompt management.
> **Customer-visible:** No
> **Review:** End of Sprint 1 (Jun 13)

---

### Story 1.8: §5.10 Capture-Surface Data Layer (Hotfix Track)
> Added per v2 scope brief §5.10. Deop-owned table schemas, EF Core entities, migrations, and multi-tenant write API endpoints for three of the four capture surfaces. Brand kit excluded — Click engineering owns end-to-end. Industry templates owned by Deop because Account FK depends on them.
>
> Ships as a series of hotfix PRs in parallel with Sprints 2-3, ahead of the data needs of Sprint 2's unified email component.

**Task 1.8.5: `industry_template_configs` Table + Seed** _(prerequisite — FK target)_ — **shipped** (migration `20260616122221_AddIndustryTemplateConfigs`)
- Subtask: Add EF Core entity `IndustryTemplateConfig` (`industry_key` PK, `display_name`, `vocabulary`, `recurring_value_labels`)
- Subtask: Migration adds the table to the Tenant DbContext under the reference-tables group (single-DB join keeps the reader simple — Tenant chosen over Control)
- Subtask: Seed launch industry `membership` plus three starter rows (`b2b`, `nonprofit`, `wealth-management`) via `IndustryTemplateConfigSeedData`
- Subtask: `EfCoreIndustryConfigReader` joins on the seeded table; falls back to `IndustryConfigData.KeyOnly` for industries not yet curated
- Subtask: `IndustryContextBlock` contract unchanged — only the reader body changes
- Depends on: —

**Task 1.8.1: `Account` Schema Gap-Audit + Hotfix Migration** — **data layer shipped** (migration `20260616122749_AddAccountOrganisationSetupFields`); BFF endpoint deferred follow-up
- Subtask: Verified existing columns on `Account` (Tenant DbContext entity): `Industry` (free-text), `Subindustry`, `Revenue`, `EmployeeCount`, `AddressLine1/2`, `City`, `CountryCode`, `RegionId`, `DailyAiSpendCapUsd`
- Subtask: Added missing columns (all nullable for safe production rollout): `IndustryTemplateId` (FK → `industry_template_config.industry_key`, Restrict cascade), `PrivacyUrl`, `Website`, `PostalCode`, `State`, `Timezone`, `Locale`
- Subtask: Backfill plan — populate `IndustryTemplateId` from existing `Industry` free-text via mapping table seeded in Task 1.8.5; deprecate free-text column post-backfill (follow-up hotfix)
- Subtask: `OrgContext` exposes the new tonal fields; `OrgContextBlock` reads `IndustryTemplateId ?? Industry` so the canonical key supersedes the legacy column
- Subtask: BFF write endpoint (`Core/BackendForFrontend/`) for org-setup save — **deferred** to a follow-up commit (BFF → Admin API client → Admin controller pipeline scope)
- Depends on: 1.8.5

**Task 1.8.2: `organisation_profile` + `voice_samples` Tables + Endpoints** — **data layer + reader seam shipped** (migration `20260616124103_AddOrganisationProfileTables`); BFF endpoints deferred follow-up
- Subtask: EF Core entities `OrganisationProfile` (audience description, tier/programme names, terminology preferences) and `VoiceSample` (up to 5 samples per profile, max 8000 chars per sample)
- Subtask: Migration adds both tables with `AccountId` FK Restrict + unique `(account_id)` on profile and composite `(account_id, organisation_profile_id)` on samples; voice_sample cascades on its profile
- Subtask: `IOrganisationProfileReader` + `EfCoreOrganisationProfileReader` seam caps surfaced samples at `OrganisationProfileData.MaxVoiceSamples` (5) ordered by `CreatedAt` descending
- Subtask: BFF write endpoints — **deferred** to a follow-up commit alongside Click's Angular UI work
- Subtask: Voice-sample truncation rule (8000-char max) enforced server-side (entity validation + DB column constraint)
- Depends on: 1.8.1

**Task 1.8.3: `kb_documents` + `kb_chunks` Tables + Foundry Embeddings** — **data layer + embedding adapter shipped** (migration `20260616124826_AddKnowledgeBaseTables`); BFF endpoints + HNSW index deferred follow-up
- Subtask: docker-compose postgres image swapped to `pgvector/pgvector:pg16` (tmpfs reset noted in commit body)
- Subtask: Migration enables `CREATE EXTENSION IF NOT EXISTS vector`, creates `kb_document` (id, AccountId FK Restrict, source_blob_url, source_uri, mime_type, title, ingest_status, ingest_error, token_count_total) and `kb_chunk` (id, AccountId, document_id FK Cascade, chunk_index, chunk_text, `embedding vector(3072)`, token_count) + composite indices
- Subtask: HNSW index on `kb_chunks.embedding` — **deferred**: stock pgvector caps HNSW at ~2000 dims on the `vector` type; addition follows once dimension reduction (request `dimensions=1536` from Foundry) or pgvector 0.7+ halfvec lands. Sequential scan acceptable for launch-volume KBs.
- Subtask: Tenant scope enforced at the workflow layer (Tenant DbContext does not use `.HasQueryFilter()`; this matches the existing convention)
- Subtask: `IEmbeddingClient` + `AzureFoundryEmbeddingClient` (HTTP transport mirroring chat pattern) using `text-embedding-3-large` (3072-dim); batches caller input into `Ai:Embeddings:BatchSize`-sized requests and preserves absolute order via per-item `index`
- Subtask: BFF endpoints — **deferred** to a follow-up commit (KB upload + ingest workflow + similarity search)
- Subtask: Throttle / retry strategy wrapped at the call site via existing `IAiRetryPolicy` (Polly) — landed via DI in the embedding client adapter
- Drive-by: `TenantDbContext.OnModelCreating` ignores `KbChunk.Embedding` under the EF in-memory provider so context-block unit tests still exercise the DbContext (InMemory cannot map the `Pgvector.Vector` CLR type)
- Depends on: 1.8.1

**Task 1.8.4: `brand_settings` Coordination (read-only for Deop)** — _pending Click engineering schema delivery_
- Subtask: Week-2 schema scoping conversation with Click engineering (per v2 brief §5.10)
- Subtask: Verify `IBrandKitReader` contract and `BrandKitData` shape match the schema Click ships
- Subtask: Once Click migration lands, swap `EfCoreBrandKitReader` from null-return to real EF query — only the reader body changes; block and context stay stable
- Subtask: **Do not write a Deop-side migration for `brand_settings`** — Click owns it end-to-end
- Depends on: Click ships the schema

**Task 1.8.6: Organisation-Setup BFF Endpoint** _(follow-up to 1.8.1; launch)_
- Subtask: New `OrganisationSetupController` under `Core/BackendForFrontend/SSP.BackendForFrontend.Api/Controllers/`
- Subtask: `PUT bff/accounts/{accountId:guid}/organisation-setup` — accepts IndustryTemplateId, PrivacyUrl, Website, PostalCode, State, Timezone, Locale (all nullable; partial updates allowed)
- Subtask: Workflow + request/response model + AccountId injection + `[SessionAuthorize(Roles="admin,globalAdmin")]` + `[ValidateCsrf]`
- Subtask: Admin API client + Admin controller + Admin workflow + DTO threading the new columns
- Subtask: Unit tests (entity config, workflow, endpoint smoke for 401/200)
- Depends on: Task 1.8.1 (shipped — data layer)

**Task 1.8.7: Organisation-Profile + Voice-Samples BFF Endpoints** _(follow-up to 1.8.2; launch)_
- Subtask: New `OrganisationProfileController` with endpoints: GET / PUT profile; GET / POST / DELETE voice-samples; voice-sample server-side truncation to 8000 chars enforced before persistence
- Subtask: Workflow + request/response models per endpoint
- Subtask: Admin API client + Admin controller + Admin workflow pipeline
- Subtask: Unit tests (truncation, profile upsert idempotency, voice-sample max-count enforcement, cross-account isolation)
- Depends on: Task 1.8.2 (shipped — data layer + reader seam)

**Task 1.8.8: KB Document Upload + Ingest Workflow + Search Endpoint** _(follow-up to 1.8.3; launch — §5.8 completion)_
- Subtask: BFF `KnowledgeBaseController` — POST documents (blob URL + mime), GET documents list, DELETE document (cascade chunks), POST search (query text → embedding → top-K kb_chunks)
- Subtask: Ingest workflow — chunk source text (fixed ~1000 token chunks), batch-embed via `IEmbeddingClient`, persist chunks with ingest_status transitions (pending → processing → ready/failed)
- Subtask: Search workflow — embed query, cosine-distance top-K query against kb_chunks (sequential scan acceptable; HNSW lands via 1.8.9)
- Subtask: Throttle + retry strategy at ingest pipeline (Polly wrapper around `IEmbeddingClient`)
- Subtask: Unit tests (chunking determinism, ingest pipeline state machine, search endpoint smoke)
- Depends on: Task 1.8.3 (shipped — tables + embedding adapter)

**Task 1.8.9: HNSW Similarity Index on `kb_chunk.embedding`** _(launch — perf gate)_
- Subtask: Decision spike — Foundry text-embedding-3-large `dimensions=1536` vs pgvector 0.7+ halfvec(3072). Document rationale in Task 1.10.2 memo.
- Subtask: Migration adds HNSW index using cosine ops on the chosen embedding column
- Subtask: Verify similarity-search latency on a sample KB (~10k chunks) drops below sequential-scan baseline
- Depends on: Task 1.8.8 (search endpoint to verify), Foundry dim decision

=== PR-Hotfix series for Story 1.8 ===
> **Scope:** v2 scope-brief §5.10 capture-surface data layer + BFF write endpoints + KB ingest/search completion. Nine task hotfix series across Sprints 2-4.
> **Order:** 1.8.5 (FK target) → 1.8.1 (Account hotfix) → 1.8.2 (profile) → 1.8.3 (KB data layer) → 1.8.6 (org-setup BFF) → 1.8.7 (profile BFF) → 1.8.8 (KB BFF + ingest + search) → 1.8.9 (HNSW). 1.8.4 coordination parallel.
> **Customer-visible:** No (data layer + BFF endpoints consumed by Click Angular UIs).
> **Review:** Per PR.
>
> **Status (2026-06-16):** 1.8.5 + 1.8.1 + 1.8.2 + 1.8.3 data layers shipped on `deop/feature/section-5.10-capture-data-layer` (commits `165e533e8`, `1b02bdded`, `7f4106bad`, `77df28121`, merged to `deop/integration` as `93ae58617`). BFF write endpoints (1.8.6/7/8), HNSW index (1.8.9), and brand_settings reader hookup (1.8.4) are upcoming follow-up commits.

---

### Story 1.9: Launch Context Blocks + Form Generation
> Added per v2 scope brief §4.2 (9 launch context blocks) + §5.6 (form generation feature). Closes the gap left by PR 12's blanket v1.1 deferral — these five tasks ship the remaining launch-required context blocks plus the form generation feature, all as a hotfix track running in parallel with Sprints 3-4.
>
> The §4.2 nine-block requirement is satisfied by: brand (Story 1.4 shipped) + org (Story 1.4 shipped) + industry (Story 1.4 shipped) + profile (Task 1.9.2) + event (Task 1.9.3) + brief (Task 1.9.4) + contact-fields (Task 1.9.5) + knowledge (Task 4.3.2 promoted) + field-semantics (Task 4.2.1 promoted).

**Task 1.9.1: Form Generation Feature (basic)** — _launch_
- Subtask: New `/forms/generate` BFF endpoint composing brand + org + industry context for structured form JSON output
- Subtask: New `FormGeneratePromptBuilder` + `FormGenerateOutput` schema under `SSP.AI/Prompts/FormGenerate/` + `SSP.AI/Schemas/FormGenerate/`, validated via `IAiOutputValidator`
- Subtask: Persist generated form via the forms table; return form_id for client navigation
- Subtask: Feature key `form-generate` registered in the AI feature registry (Task 4.6.7)
- Subtask: Unit tests for prompt builder + schema validation; integration test for end-to-end generation
- Depends on: PR 9 wrapper, PR 9 brand/org/industry blocks

**Task 1.9.2: ProfileContextBlock** — _launch_
- Subtask: New `ProfileContextBlock` under `SSP.AI/Context/Profile/` consuming `IOrganisationProfileReader` (seam shipped in Story 1.8.2)
- Subtask: Typed `ProfileContext` record with `Exists`, audience description, tier names, programme names, terminology preferences, voice samples (top 5)
- Subtask: `ToPromptString()` formats as tonal/audience hints under `## Profile`
- Subtask: Graceful degradation (no profile row → `ProfileContext.Empty`); never throws
- Subtask: DI registration in `AddAiServices`
- Subtask: Unit tests (empty path, populated path, voice-sample cap)
- Depends on: Task 1.8.2 (shipped — `IOrganisationProfileReader`)

**Task 1.9.3: EventContextBlock** — _launch_
- Subtask: New `EventContextBlock` under `SSP.AI/Context/Event/` reading `events` table via `ITenantDbContextFactory`
- Subtask: Parameter-driven via `AiContextOptions.EventId`; returns event name, date, location, registration URL
- Subtask: Typed `EventContext` record + `ToPromptString()` under `## Event`
- Subtask: Graceful degradation when no event_id or event missing
- Subtask: DI registration; unit tests
- Depends on: PR 9 context block base; events table (existing)

**Task 1.9.4: BriefContextBlock** — _launch_
- Subtask: New `BriefContextBlock` under `SSP.AI/Context/Brief/` reading `event_briefs` table (or equivalent) via `ITenantDbContextFactory`
- Subtask: Loads positioning, key messages, target audience for the given event_id; pairs with `EventContextBlock`
- Subtask: Typed `BriefContext` record + `ToPromptString()` under `## Brief`
- Subtask: Graceful degradation; DI registration; unit tests
- Depends on: Task 1.9.3 (event id context); event briefs table (existing or to be confirmed with Click)

**Task 1.9.5: ContactFieldsContextBlock** — _launch_
- Subtask: New `ContactFieldsContextBlock` under `SSP.AI/Context/ContactFields/` reading `contact_field_definitions` (system + template + custom) via `ITenantDbContextFactory`
- Subtask: Surfaces merge tags + usage guidance so AI-generated copy uses tags that resolve at send time
- Subtask: Typed `ContactFieldsContext` record + `ToPromptString()` under `## Contact Fields`
- Subtask: Graceful degradation when account has no custom fields
- Subtask: DI registration; unit tests
- Subtask: Coordinate with Task 4.2.1 (Field-Semantics block) — this block surfaces tag definitions while 4.2.1 surfaces semantic metadata (field tags)
- Depends on: PR 11p field tagging UI (Task 1.5.2 system/template tag seed; Task 3.2.x customer tags)

=== PR-Hotfix series for Story 1.9 ===
> **Scope:** Five-task hotfix series shipping the remaining launch context blocks + the form generation feature in parallel with Sprints 3-4.
> **Order:** 1.9.1 (form gen — independent) parallel with 1.9.2 (profile) → 1.9.3 (event) → 1.9.4 (brief) → 1.9.5 (contact fields). 1.9.5 depends on PR 11p field-tagging completion.
> **Customer-visible:** Yes (form generation 1.9.1); no (context blocks 1.9.2-5).
> **Review:** Per PR.

---

### Story 1.10: Launch Readiness Documentation
> Added per v2 scope brief §5.1 (Foundry model spike + memo) + §5.9 (handover documentation). These are documentation-only deliverables — not feature code — but explicit v2 launch requirements without which the engagement cannot be considered complete.

**Task 1.10.1: `/AI/README.md` Handover Documentation** — _launch (Sprint 4)_
> v2 brief §5.9: "A README in the SSP repo at `/AI/README.md` describes: how the wrapper is called, what context blocks exist, how to add a new feature, the cost model, the model selection logic, the spend cap, the retry behaviour, the schema validation contract. The Click engineering team can onboard a new engineer to the substrate using this document plus the prototype, without a Deop person in the room."
- Subtask: README at `src/backend/Core/AI/README.md` (or repo equivalent) covering wrapper API contract, context block catalogue (9 blocks + composition registry), feature key registry reference, cost/spend-cap model, retry behaviour, schema validation contract, content filtering invariants, multi-tenant isolation rules
- Subtask: Cross-reference Pre-Launch Verification Gates (Gates 5.3.1 + 5.3.2) so the README serves as the onboarding entry point for Click long-term substrate owner
- Subtask: Click engineering review + sign-off
- Depends on: PR 9 shipped, Story 1.8 shipped, Story 1.9 shipped, Task 4.6.7 (Feature Key Registry) shipped

**Task 1.10.2: Foundry Model Spike + 1-Page Memo** — _launch (Sprint 4)_
> v2 brief §5.1: "Foundry integration: model availability spike and SDK selection. Confirmed which Foundry-hosted models map to the prototype's generation / classification / reasoning model classes (Sonnet-class, Haiku-class, Opus-class). Confirmed the SDK. One-page memo lands in the SSP repo with the model strings the wrapper will use."
- Subtask: Spike — verify Foundry-hosted deployment names for Sonnet-class / Haiku-class / Opus-class equivalents; document capacity / rate limits per region
- Subtask: Confirm embedding deployment dimensions decision (3072 vs 1536) tied to Task 1.8.9 HNSW prerequisite
- Subtask: 1-page memo at `docs/ai-foundry-models-launch-memo.md` covering: deployment name table, region/residency, rate limits, fallback model strategy, cost-table reference
- Subtask: Cross-reference into Task 1.10.1 README + Task 4.6.7 Feature Registry
- Depends on: Task 1.2.5 shipped (Foundry adapter)

**Task 1.10.3: §5.10 Hour Estimate Sign-off** — _launch (Sprint 1-4 ongoing)_
> v2 brief §5.10 lists rough hour estimates for Story 1.8 (organisation setup 8h + organisation profile 14h + KB 8h, brand kit 0h). With added Tasks 1.8.6/7/8/9 (~42h follow-up) plus Story 1.9 (~38h) plus Story 1.10 (~14h) the total launch backlog grew. Deop signs off on final estimates against the 545.5h budget; v1.1 demoted tasks (Stories 5.1/5.2 + EPIC 4 demotions) free hours.
- Subtask: Tabulate all launch task estimates (Stories 1.x + 2.x + 3.x + promoted 4.x + 1.9 + 1.10) against the 545.5h budget
- Subtask: Tabulate v1.1 demoted task hours as the offset (released budget)
- Subtask: Net budget delta — confirm launch fits within 545.5h or escalate
- Subtask: Sign-off captured in `docs/ai-arch-scope.md` Sprint Calendar trailer + this task entry
- Depends on: Reclassification of Stories 1.8/1.9/1.10 + Stories 3.1/4.x/5.x complete (this scope-doc edit)

=== PR-Hotfix series for Story 1.10 ===
> **Scope:** Three-task documentation + spike series finalising launch readiness per v2 §5.1 + §5.9.
> **Order:** 1.10.2 (Foundry memo — Sprint 1 ideally; late is acceptable) → 1.10.1 (handover README, depends on shipped features) → 1.10.3 (hour sign-off, ongoing tabulation).
> **Customer-visible:** No (documentation).
> **Review:** Per task.

---

## EPIC 2: Unified Email-Content Component
**Sprint 2 (Jun 16 – Jun 27)**

### Ownership Split (updated 2026-06-23)

| Owner | Stories | Scope | Hours |
|-------|---------|-------|-------|
| **Deop** | Story 2.1 + Story 2.3 | Unified email generation service, context type refactoring, BFF endpoint, integration contract & hand-off docs | 26h |
| **Click engineering** | Story 2.2 | AIEmailModal Angular refactor, journey editor wire-up (depends on Deop Story 2.1 + 2.3 delivery) | 16h |

**Rationale:** Deop's contracted scope covers AI architecture and backend services. Angular UI component work (Story 2.2) is frontend development outside Deop's scope — ownership follows the same pattern as Brand Kit (Click end-to-end, Deop consumes through seam) and Story 1.8 BFF endpoints (Deop delivers backend, Click consumes via Angular UIs).

---

### Story 2.1: Backend Unified Email Endpoint _(Deop)_
> All branded email generation from a single headless-first endpoint.
> _Status: complete — `IBrandedEmailGenerator`/`BrandedEmailGenerator` in `SSP.AI/Email/` (discriminated `EmailGenerationContext` + context-aware CTA), exposed via `POST /bff/accounts/{accountId}/emails/generate` → Admin `EmailGenerateWorkflow`. Routes through the shared `email-generate` feature key. Shipped on `deop/feature/unified-email-content-component`; 15 generator + 6 workflow tests green._

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

### Story 2.3: Integration Contract & Hand-Off Documentation _(Deop)_
> Provide Click engineering with everything needed to integrate Story 2.2 against the BFF endpoint without Deop in the room.
> _Status: complete — `src/backend/Core/AI/docs/unified-email-integration-contract.md` (endpoint + request/response shapes, error codes, context discriminator + CTA tables, headless caller pattern, four curl integration-test stubs). Doubles as the Week-4 Deop-gate verification._

**Task 2.3.1: Hand-Off Contract Documentation**
- Subtask: Define unified email BFF endpoint contract (request/response shapes, error codes)
- Subtask: Document headless caller pattern (API call without rendering modal/UI)
- Subtask: Provide integration test stubs Click can run against the BFF endpoint
- Subtask: Document context type discriminator behavior (`campaign_email | journey_step | standalone`)
- Subtask: Document context-aware CTA behavior per context kind
- Depends on: 2.1.3

---

### Story 2.2: Angular Email Component Extraction _(Click engineering — UI integration)_
> Extract existing ~300-line AIEmailModal to shared/reusable component. **Ownership: Click engineering.** Depends on Deop delivering Story 2.1 BFF endpoint + Story 2.3 integration contract.

**Task 2.2.1: AIEmailModal Component Refactoring** — _Click engineering_
- Subtask: Analyze existing component
- Subtask: Move to shared component under `src/frontend/src/app/shared/`
- Subtask: Update email editor and journey editor integrations
- Depends on: Story 2.3 (hand-off contract delivered by Deop)

**Task 2.2.2: Journey Editor Wire-up** — _Click engineering_
- Subtask: Call unified email component from journey editor
- Subtask: Auto-populate journey step context
- Subtask: E2E test: journey → AI email generation flow
- Depends on: 2.2.1

---

=== PR 10a: Unified Email Backend + Integration Contract (Deop) ===
> **Scope:** Unified email generation service, context type refactoring, BFF endpoint, headless caller support, integration contract documentation.
> **Customer-visible:** Partial — headless callers (recommendation action handlers) work; UI-triggered generation awaits PR 10b.
> **Review:** End of Sprint 2 (Jun 27)
> **Independently deployable:** Yes — headless callers function without the Angular UI.

=== PR 10b: Angular Email Component Integration (Click engineering) ===
> **Scope:** AIEmailModal refactor to shared component, journey editor wire-up, E2E tests.
> **Customer-visible:** Yes — journey emails can be AI-generated via UI.
> **Depends on:** PR 10a delivered + Story 2.3 hand-off documentation.
> **Timeline:** Click engineering schedule (not Deop sprint commitment).

> **🔴 Decision Checkpoint (Week 4):**
> - **Deop gate:** Is the unified email BFF endpoint complete and tested (headless callers verified)?
> - **Click gate:** Has Click engineering started Angular integration against the contract?
> - If Deop gate passes but Click gate hasn't started → fallback remains valid (headless/API mode; lean on templates for UI-triggered generation).

---

## EPIC 3: Web Agent Cleanup & Field-Tagging UI
**Sprint 3 (Jun 30 – Jul 11)**

### Story 3.1: Form/Event Confirmation Handler Migration
> Form/event confirmation senders stop being treated as agents. Web Agent remains the only customer-facing product agent type. **Per v2 scope brief: journey-based migration deferred to v1.1; Click engineering's existing (legacy) confirmation email implementation is preserved at launch.**

**Task 3.1.1: Product Agent Definition (Web Agent Only)** _(launch — organizational clarity)_
- Subtask: Apply "Agent" = Web Agent: customer-facing multi-turn website/chat experience
- Subtask: Reclassify single-call email senders, form generators, event generators, strategy workflows, and insights workflows as handlers/generators/workflows
- Subtask: Update user-facing labels and internal planning language so Form Agent and Event Agent are not treated as product agent types
- Depends on: PR 10

**Task 3.1.2: Confirmation Email → Journey Migration** — **v1.1 (DEMOTED per v2 brief)**
- Rationale: v2 brief §6 defers the journey builder from Aug 15; the confirmation-email-as-journey migration depends on it. Click's existing legacy confirmation email implementation continues to ship form/event confirmations at launch unchanged.
- Subtask: Move form-submission and event-registration confirmation email creation logic to journeys
- Subtask: Journey's first step = confirmation email
- Subtask: Implement .ics attachment as journey-email feature
- Depends on: 3.1.1 + journey builder shipping (v1.1)

**Task 3.1.3: Web Agent / Inbox Runtime Narrowing** — **v1.1 (DEMOTED per v2 brief)**
- Rationale: Web Agent feature itself is v1.1 (brief §6 "Phase 2 AI capabilities"), so the runtime narrowing follows. Legacy Form Agent / Event Agent runtimes stay in place at launch.
- Subtask: Remove separate Form Agent and Event Agent runtime surfaces
- Subtask: Route any needed inbound conversation handling through the Web Agent / inbox conversation model with original registration context
- Subtask: Remove HTML generation duplication (email-generate / form confirmation / event confirmation)
- Subtask: Simplify legacy form/event triggers to "enrol in journey + open conversation thread when needed"
- Depends on: 3.1.2

=== PR 11: Web Agent Cleanup + Form/Event Confirmation Migration ===
> **Scope (revised per v2 brief):** Only Task 3.1.1 (Product Agent Definition — organizational/labelling clarity) lands at launch. Tasks 3.1.2 (Confirmation → Journey) and 3.1.3 (Web Agent Runtime Narrowing) deferred to v1.1 alongside the journey builder and Web Agent feature.
> **Customer-visible:** No (labelling change only at launch).
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

## EPIC 4: Context Blocks + AI Surface Parity Wiring
**Sprint 4 (Jul 14 – Jul 25)**

### Story 4.1: Methodology & Plan Context Blocks — **v1.1 (out of launch scope)**
> Load marketing methodology and plan contexts.
> _v2 brief §4.2 does not list methodology or plan as launch context blocks; both depend on the marketing-plan feature which is post-launch._

**Task 4.1.1: Methodology Context Block** — _v1.1_
- Subtask: Load data from `marketing_disciplines`, `goal_types`, `programmes`, `tag_labels` tables
- Subtask: Graceful degradation
- Depends on: PR 9 (context block base)

**Task 4.1.2: Plan Context Block** — _v1.1_
- Subtask: Load data from `marketing_plans` + `plan_goals` + `plan_programmes` tables
- Depends on: PR 9

### Story 4.2: Field-Semantics & Audience Context Blocks — **launch (PROMOTED per v2 brief)**
> Load contact field semantics and audience context.
> _v2 brief §4.2 lists contact-field-semantics as one of the 9 launch context blocks; audience composition is required by the email-generation feature (brief §5.5)._

**Task 4.2.1: Field-Semantics Context Block** — _launch_
- Subtask: Load semantic data from `contact_field_definitions` extension columns
- Depends on: PR 11p (field tags populated)

**Task 4.2.2: Audience Context Block** — _launch_
- Subtask: Build audience context from `audiences` + `audience_contacts` + field-semantics block
- Subtask: `audience_contexts` materialized view/table schema migration
- Depends on: 4.2.1

### Story 4.3: Insights & Knowledge Context Blocks — **split (Insights v1.1; Knowledge promoted to launch)**
> Cross-org benchmarks and knowledge base integration.

**Task 4.3.1: Insights Context Block** — _v1.1 (out of launch scope per v2 brief §6 "Cross-org analytics, benchmarks, the insights block. Defer to v1.1.")_
- Subtask: Cross-org aggregate benchmarks (privacy-respecting)
- Subtask: Minimum-N threshold (5-10) — below threshold → return "n/a"
- Subtask: Cross-org reporting via separate service-role view
- Depends on: PR 9

**Task 4.3.2: Knowledge Context Block** — **launch (PROMOTED per v2 brief)**
> v2 §4.2 lists knowledge as one of the 9 launch context blocks; §5.8 makes KB infrastructure a launch deliverable. KB tables and the Foundry embedding adapter shipped in Task 1.8.3; this block wires consumption into the AI substrate. Composition registry (4.5.1) routes it to features.
- Subtask: KB tables — per-org + curated content _(shipped Task 1.8.3 — kb_documents / kb_chunks)_
- Subtask: Vector search Top-K, filter by `org_id` _(uses `IEmbeddingClient` shipped in Task 1.8.3; sequential scan acceptable at launch until HNSW lands via Task 1.8.9)_
- Subtask: Scope enforcement in retrieval function, not caller
- Subtask: Generalize knowledge block from Web Agent-only to all eligible features
- Depends on: PR 9, Task 1.8.3 (shipped)

### Story 4.4: Assets Context Block — **v1.1 (out of launch scope)**
> Include content assets in AI context.
> _v2 brief §4.2 does not list assets among the 9 launch context blocks; semantic asset search depends on the assets-enrichment pipeline which is post-launch._

**Task 4.4.1: Assets Context Block** — _v1.1_
- Subtask: Load enriched asset metadata from `content_assets` table
- Subtask: Include only selected analysed metadata: `ai_description`, `dominant_colors`, `suggested_use`, `tone`, `is_analysed`
- Subtask: Exclude raw files, full libraries, and unanalysed assets from prompts
- Subtask: Document that semantic asset search waits for embeddings / pgvector
- Depends on: PR 9

### Story 4.5: Feature → Block Composition Wiring — **launch (PROMOTED per v2 brief)**
> Implement which blocks compose for each feature.
> _Required at launch by v2 §5.4 (nine context blocks) + §5.5/5.6/5.7 features — without the registry, email/form/field-tagging features cannot resolve their context block sets._

**Task 4.5.1: Composition Registry** — _launch_
- Subtask: Feature → blocks mapping registry (email-generate, form-generate, field-tagging at launch; journey-content / Web Agent / strategy / insights / recommendation registered as v1.1 stubs)
- Subtask: Dynamic block loading based on feature configuration
- Depends on: launch context blocks (4.2.1, 4.2.2, 4.3.2, plus new 1.9.2/1.9.3/1.9.4/1.9.5)

### Story 4.6: Prototype AI Surface Parity Wiring
> Make every AI surface from the Deop handover visible in the roadmap. These tasks define prompt/schema/context contracts and decide launch vs post-launch implementation per surface.

**Task 4.6.1: Forms v2 Generation + Refinement Wiring** — **SPLIT (basic generation → Story 1.9.1 launch; refinement → v1.1)**
- _Launch portion absorbed by Task 1.9.1 (basic form generation feature)_
- _v1.1 portion (refinement workflow, broader Forms v2 surface) deferred_
- Subtask: Port the Forms v2 generate/refine prompt contracts into .NET prompt classes — _refinement v1.1; basic generation handled by 1.9.1_
- Subtask: Use brand + org + industry + profile + contact field context — _launch (1.9.1)_
- Subtask: Validate against a typed `GeneratedFormDefinition` contract — _launch (1.9.1)_
- Subtask: Define feature keys for form generation and refinement — _launch for generation key (1.9.1); refinement key v1.1_
- Subtask: Confirm this is a structural JSON generator, not an agent — _organizational, lives in 4.6.7 registry_
- Depends on: 4.5.1, 4.2.1

**Task 4.6.2: Forms v2 Field Mapping Wiring** — _v1.1 (out of launch scope)_
- _Forms v2 broader feature (refinement + field mapping) is v1.1 per v2 brief §6_
- Subtask: Preserve exact-match and synonym mapping before the AI call
- Subtask: Use AI only for unresolved captured-form fields
- Subtask: Return `map_existing`, `create_new`, or `dont_capture` with confidence per field
- Subtask: Batch unmapped fields into one classification call
- Subtask: Define the `forms_v2_field_mapping` feature key and model class
- Depends on: 4.2.1

**Task 4.6.3: Landing Page Generation, Refinement, and Layout Switching Wiring** — _v1.1 (out of launch scope)_
- _Landing page generation is v1.1 per v2 brief §6_
- Subtask: Port landing-page generate/refine/fill-missing-block prompt contracts
- Subtask: Use relaxed generation schemas and server-stamped IDs for page blocks
- Subtask: Preserve the rule that AI does not emit URLs, page block IDs, or image asset IDs
- Subtask: Preserve layout-switch "missing blocks only" behavior and bag-of-blocks storage model
- Subtask: Define feature keys for generation, refinement, and layout switch
- Depends on: 4.5.1, 4.4.1

**Task 4.6.4: Events Create-with-AI Surface Contract** — _v1.1 (out of launch scope)_
- _Events Create-with-AI is v1.1 per v2 brief §6_
- Subtask: Define event field extraction contract with nullable operational basics and marketing brief fields
- Subtask: Define event journey structure contract for Invitations, Confirm, and Followup journeys
- Subtask: Preserve `cta_intent` indirection so AI never emits raw URLs
- Subtask: Preserve slot-based scaffold rendering for event invitations and HTML rendering for followups
- Subtask: Define feature keys for event extraction, journey structure, invite content, followup content, and regeneration
- Depends on: PR 10, 4.5.1

**Task 4.6.5: Web Agent Context and Knowledge Wiring** — **SPLIT (knowledge wiring → launch; Web Agent runtime → v1.1)**
- _Knowledge wiring portion required at launch (composition of brand+org+industry+knowledge for the launch knowledge block). Web Agent feature itself is v1.1; runtime + chat surface deferred._
- Subtask: Rename customer-facing chat agent references to Web Agent — _organizational, launch (handled by 3.1.1)_
- Subtask: Compose brand + org + industry + knowledge + conversation history — _launch portion: brand+org+industry+knowledge composition wiring; conversation history wiring v1.1_
- Subtask: Preserve response-length configuration and fallback-message behavior — _v1.1 (Web Agent runtime)_
- Subtask: Confirm Web Agent is the only customer-facing product agent type — _organizational, launch_
- Depends on: 4.3.2 (launch), 4.5.1 (launch)

**Task 4.6.6: Profile Research, Insights Ask, Social Generate, and Inbound Classification Contracts** — _v1.1 (out of launch scope)_
- _All four workflows are v1.1 per v2 brief §6_
- Subtask: Document profile research as an onboarding extraction workflow with nullable per-field outputs
- Subtask: Document insights ask as org-data Q&A with tenant-scoped context and traceable usage
- Subtask: Document social generation as a content-generation workflow using the shared voice floor
- Subtask: Document inbound classification as a classification workflow with explicit feature key and model class
- Subtask: Mark each workflow as launch, post-launch, or explicit product deferral before PR 13 starts
- Depends on: 4.5.1

**Task 4.6.7: AI Feature Key and Invariant Registry** — **launch (PROMOTED per v2 brief)**
> Required at launch by v2 §5.9 (handover documentation). The registry is the structured surface from which the handover doc derives — without it the README cannot exhaustively describe feature keys, model classes, and invariants.
- Subtask: Create a single registry of feature keys, model classes, prompt class, schema contract, context composition, and launch/deferred status for every AI surface
- Subtask: Include the handover invariants: every call logs usage, spend cap before provider call, voice floor on content prompts, dash stripping on text output, schema validation, server-stamped IDs, no AI-emitted URLs, graceful failure, org/account scope on every call
- Subtask: Add Forms v2 feature keys that are TBD in the handover
- Subtask: Use the registry as the PR 13 readiness gate
- Depends on: launch features (1.5.1 email, 1.9.1 form, 3.2.3 field-tagging, 4.3.2 knowledge wiring, 4.2.1 field-semantics)

=== PR 12 (SPLIT per v2 brief): Launch parts + v1.1 backlog ===
> **Launch parts (Sprint 4 in-scope):** Task 4.2.1 (Field-Semantics Block), 4.2.2 (Audience Context), 4.3.2 (Knowledge Block), 4.5.1 (Composition Registry), 4.6.1 launch portion (basic form gen, absorbed by Story 1.9.1), 4.6.5 launch portion (knowledge wiring), 4.6.7 (Feature Key Registry). These plus the new Story 1.9 launch context blocks (profile/event/brief/contact-fields) complete the v2 §4.2 nine-block requirement.
> **v1.1 backlog (deferred):** Story 4.1 (Methodology/Plan), Task 4.3.1 (Insights), Task 4.4.1 (Assets), Task 4.6.1 refinement, 4.6.2 (Forms v2 field mapping), 4.6.3 (Landing pages), 4.6.4 (Events Create-with-AI), 4.6.5 v1.1 portion (Web Agent runtime + chat surface), 4.6.6 (Profile research / Insights ask / Social / Inbound).
> **Customer-visible:** No — substrate/infrastructure.
> **Review:** End of Sprint 4 (Jul 25)
> **🔴 Decision Checkpoint (Week 8):** Has the field-tagging UI shipped and are users tagging?

---

## EPIC 5: Recommendation Actions & Command Centre — **v1.1 (entire epic, except Story 5.3 reframed as launch gate)**
**Sprint 5 (Jul 28 – Aug 15)** — _Stories 5.1 + 5.2 deferred to v1.1 per v2 brief §6 "Phase 2 AI capabilities. Recommendation handlers, hyperpersonalisation per recipient, the Today / Plan command centre — all v1.1 and beyond." Story 5.3 reframed as Pre-Launch Verification Gates (see below)._

### Story 5.1: Recommendation Action Handlers — _v1.1_
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

### Story 5.2: Today Page (Command Centre) — _v1.1_
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

=== PR 14: Today Page + Retain Dashboard + Command Palette === — _v1.1_
> **Scope:** Insights command centre, Today page, recommendation cards, Retain dashboard, command palette. Deferred to v1.1 per v2 brief §6.
> **Customer-visible:** Yes (post-launch).
> **Review:** Post-launch (v1.1)

---

## Pre-Launch Verification Gates (cross-cutting, Sprint 5 + Test & Polish)

> Story 5.3 reframed: these are not feature tasks but **launch acceptance gates** run in parallel with development. Per v2 brief §13 (compliance) + §5.9 (handover), every gate must pass before Aug 15 launch. Owned by Deop + Click engineering jointly.

**Gate 5.3.1: Observability Verification** — _launch gate (Sprint 5 + Test & Polish)_
- Verify cost tracking per org/feature/month from `ai_usage` aggregate queries
- Verify latency tracking per feature surfaces in the cost dashboard
- Verify validation-retry logging (corrective-prompt loop traces present)
- Verify `trace_id` audit linkage end-to-end (BFF request → `ai_usage` row → application log)
- Depends on: Story 1.3 (shipped), Story 1.10.1 handover doc references this gate

**Gate 5.3.2: GDPR Compliance Check** — _launch gate (Sprint 5 + Test & Polish)_
- Mandatory GDPR requirements checklist (data residency, consent capture, right-to-erasure on `ai_usage`)
- Verify PII detection in outputs (Task 1.2.4 content filter exercised on a representative prompt set)
- Verify content filtering and redaction logging populates `ai_usage.content_filter_outcome`
- Verify spend-cap enforcement under runaway conditions
- Depends on: Story 1.3 + Task 1.2.4 (shipped), Story 1.10.1 handover doc references this gate

---

## Implementation Summary

| Sprint | Dates | PR | Epic | Customer-Visible |
|--------|-------|----|------|-------------------|
| Sprint 1 | Jun 1–13 | PR 9 | Foundation & Client Wrapper | ❌ |
| Sprint 2 | Jun 16–27 | PR 10a (Deop) + PR 10b (Click) | Unified Email Backend + Angular UI | Partial (Deop) / ✅ (Click) |
| Sprint 3 | Jun 30 – Jul 11 | PR 11 + PR 11p | Web Agent Cleanup + Field-Tagging | Partial / ✅ |
| Sprint 4 | Jul 14–25 | PR 12 | Context Blocks + Surface Parity Wiring | ❌ |
| Sprint 5 | Jul 28 – Aug 15 | PR 13 + PR 14 | Recommendations + Today Page | ✅ / ✅ |

| Metric | Count |
|--------|-------|
| Epics | 5 |
| Stories | 20 |
| Tasks | 55 |
| PRs | 7 |
| Decision Checkpoints | 3 |

## Risk Notes
- **R1:** Form/event agent deprecation → if live customers exist, deprecation becomes a migration concern
- **R2:** Field-tagging UI is UX-heavy, must feel manageable for orgs with 40+ fields
- **R3:** Prompt tuning: plan 2-3 days side-by-side testing for each migrated surface
- **R4:** Weeks 5-8 are invisible: nothing customer-facing moves — this is expected, communicate it
- **R5:** Customer feedback loop: if no friendly sees Phase 1 by week 6, Phase 2 is built in the dark
