# Tasks: AI Architecture — Core Substrate + Feature Migration

**Scope:** AI architecture build-out for the launch milestone. All phases ship this milestone in sequence:
substrate first (Epic 1), unified email component second (Epic 2), agent cleanup + field-tagging third
(Epic 3), remaining context blocks + surface parity fourth (Epic 4), recommendation actions + command
centre last (Epic 5). Pre-production: no live customers, so backward compat constraints do not apply.

**Source of truth:** `ai-architecture-strategy-v2.md` (architecture) · `ai-architecture-requirements_EN.md`
(requirements index) · `ai-arch-scope.md` (scope log) · `deop-ai-roadmap-2026-06-10.md` (roadmap alignment).
This file does not restate those documents — it references and tracks them.

**Not in this file:** Prompt content; specific UI design specs; Salesforce/CRM adapter pattern; field-mapping
UI; non-AI infrastructure concerns; pricing and packaging decisions.

**Format:** [ID] Description  
- One line per task: what + how, briefly. No code.  
- ✅ = shipped; ☐ = not started; (🔜 Click) = owned by Click engineering.  
- Single Deop developer, worked top to bottom in order unless noted otherwise.

---

## Architecture in one line

Provider-agnostic AI pipeline (`SSP.AI`) with `IAiClient` / `ITenantAiClient` as the single entry point;
composable context blocks (`IContextBlock<TContext>`) feed every feature prompt; every call is
logged to `ai_usage` with cost, latency, trace ID, and content-filter outcome; Azure AI Foundry
adapter ships alongside Anthropic direct as the post-launch migration path.

---

## Pipeline note

The AI pipeline is layered in a fixed order — all cross-cutting concerns live in `AiClientBase`, not in
feature code. The boundary is strict: feature callers build a request and read a result; the pipeline owns
everything in between.

```
caller → IAiClient.GenerateAsync
  → [1] Tenant isolation (AccountId + UserId auto-injected; no call without AccountId)
  → [2] Model resolution (Sonnet / Haiku / Opus → provider deployment names via Ai:Models)
  → [3] Spend-cap check (DailyAiSpendCapEnforcer — blocks BEFORE any provider cost)
  → [4] Content filtering — input (PII detection + banned-term check)
  → [5] Provider call (Azure Foundry primary; Anthropic legacy; swap = change Ai:Provider config)
  → [6] Retry with exponential backoff (Polly v8 — transient 408/429/5xx; permanent 4xx short-circuits)
  → [7] Content filtering — output (PII redact; banned-term reject/redact; outcome saved as JSONB)
  → [8] Schema validation + corrective-prompt retry (FluentValidation; up to Ai:OutputValidation:MaxAttempts)
  → [9] Fallback (per-feature template fallback via Ai:Fallback; IsFallback = true on result)
  → [10] Usage logged to ai_usage (one row per call — success, fallback, or failure; never skipped)
```

---

## Context block contract

Every context block implements `IContextBlock<TContext>` with two members: `Exists` (bool — false when
data is missing or sparse) and `ToPromptString()` (the prompt-facing string fragment, empty when `Exists = false`).
Blocks are read-only and side-effect-free. The prompt string includes only fields the LLM should reason
about — visual/renderer fields (brand colours, fonts, logos) are exposed as typed properties on the
context object and stay out of `ToPromptString()`.

---

## Why no per-feature AI code

Without the unified pipeline, every route would hand-roll retries, cost calculation, content filtering,
usage logging, and provider calls independently. Three concrete duplication patterns already existed
before this work: branded HTML email building implemented three times (email-generate, form-agent,
event-agent); brand-loading code per route; direct Anthropic SDK calls everywhere. The pipeline eliminates
all three: one place for retries, one place for logging, one place for provider swap. A model migration
touches one file. A bug in brand reasoning gets fixed once.

---

## Why Web Agent is the only product agent

"Agent" was overloaded in the codebase. Form-agent and event-agent triggers were single-call AI
invocations misnamed as agents — they sent a confirmation email and enrolled the contact; no conversation,
no state. Chat agent (multi-turn inbound replies) is a genuine agent. The cleanup separates:
- **Creation** → journeys (confirmation email = first journey step, AI-generated)
- **Runtime** → Web Agent (handles inbound replies, multi-turn, stateful)

This eliminates the HTML-building duplication between email-generate / form-agent / event-agent
and gives "agent" an architectural meaning.

---

## Why the BrandContext is tonal only

Colours, fonts, and logos do not belong in the LLM prompt — they are renderer inputs, not reasoning inputs.
Sending hex values to the model wastes tokens and produces no value. The `BrandContext.ToPromptString()`
therefore includes only: brand voice description, tone tags, values list, and tagline. Visual fields
(palette, logo URL, font stacks, color roles) are exposed as typed properties on the `BrandContext` object
for deterministic renderers and HTML builders to consume directly.

---

## Known risks / edge cases (read before Phase 3)

- **Azure AI Foundry deployment names are placeholders.** `AzureFoundryAiClient` is code-complete
  but the `appsettings` deployment names (`foundry-sonnet-deployment` etc.) are stubs. No live Azure
  check has been run. Before enabling `AI_PROVIDER=azure-foundry`, confirm: deployment names, pricing
  table values, model feature parity (prompt caching, vision), and EU region config. Covered in T019.

- **Spend cap is per-day, not per-call.** `DailyAiSpendCapEnforcer` reads the org's daily cap and blocks
  before the provider call. The cap resets at midnight UTC. No per-call limit. Per-send and per-feature
  concurrency limits are not yet implemented — retrograde from launch if the first org hits the daily cap
  unexpectedly.

- **Corrective-prompt retry burns tokens.** Each validation failure costs a full re-generation. At
  `MaxAttempts = 2`, worst case is 3 provider calls per user action. Prompts that reliably fail
  validation on the first attempt indicate a prompt that needs tuning, not a higher retry budget.
  Track via `ai_usage` retry patterns post-launch.

- **Field-semantics block returns sparse data until custom fields are tagged.** System and template
  fields are seeded. Custom fields require the field-tagging UI (T037) before the audience block
  has real semantic data. Phase 2 recommendations lose depth if this UI ships late.

- **No contact-change events in the current SSP backend.** The outbound trigger for recommendation
  actions (Epic 5) requires net-new event emission. This is a coordination item with the SSP.Audience.Api
  owners — covered in Epic 5 scope.

- **Invisible Sprint 4.** Epic 4 (context blocks + surface parity wiring) produces no customer-visible
  output. Communicate this to the team — it is expected, not a failure mode. The value surfaces
  in Epic 5 when recommendation actions use fully-composed context.

- **Week 6 checkpoint is a real gate.** If no friendly customer sees Phase 1 email features by week 6,
  Phase 2 recommendation content is being built without feedback. Prioritise the friendly customer
  introduction before Sprint 4 starts.

---

## Phase 0: Prerequisites (resolved)

**Purpose:** Architectural decisions needed before building.

- ✅ **T001** Decide provider strategy: Anthropic direct at launch, Azure AI Foundry as a post-launch
  migration. Adapter code ships in Epic 1 so the migration is a config change, not a rewrite. _Resolved
  (2026-06-10): launch on Anthropic direct. Foundry adapter included for post-launch readiness only
  unless explicitly promoted to launch dependency._

- ✅ **T002** Confirm agent taxonomy: Web Agent (inbound conversation) is the only customer-facing agent
  type. Form/event "agents" are confirmation handlers — their email work moves to journeys. Strategy,
  insights, form, landing-page, event, profile, social, and inbound-classification AI are
  workflows/generators/classifiers, not product agents. _Resolved (2026-06-10): per deop-ai-roadmap._

**Checkpoint:** Provider strategy settled. Agent taxonomy settled. Build can start.

---

## Phase 1: AI Foundation & Client Wrapper (Epic 1 / PR 9)

**Purpose:** Build the provider-agnostic AI pipeline, first context blocks, usage logging, and
field-semantics data layer. No new customer-visible features — existing email-generate output
is byte-identical after migration.

**Delivery state:** 334 unit tests green. Epic 1 in review (PR #111). Deop scope complete.

- ✅ **T003** Create `SSP.AI` project structure: folders for `Client/`, `Context/`, `Prompts/`, `Schemas/`,
  `Usage/`, `Agents/`. Wire `DI` extensions. Follow existing `SSP.*.Api` pattern.

- ✅ **T004** Configure `Ai:` appsettings section: `Provider`, `BaseUrl`, `ApiKey`, `Models` (Sonnet/Haiku/Opus
  → deployment names), `CostTable` (per-model input/output pricing), `Retry`, `OutputValidation`,
  `Fallback`, `ContentFiltering`, `SpendCap`. Schema in `appsettings.schema.json`.

- ✅ **T005** Build `IAiClient` interface and `AnthropicAiClient` implementation. Provider-neutral request
  (`AiGenerateRequest`) and result (`AiGenerateResult`, `AiUsage`, `AiGenerateMetadata`). Cross-cutting
  seam interfaces (`IAiCostCalculator`, `IAiContentFilter`, `IAiRetryPolicy`, `IAiOutputValidator`,
  `IAiModelResolver`) as pass-through defaults, replaced by follow-on tasks.

- ✅ **T006** Retry & error handling: `PollyAiRetryPolicy` with exponential backoff + jitter. Transient
  classifier (408/429/5xx = retry; permanent 4xx = short-circuit). `IAiFallbackResponder` seam;
  `TemplateAiFallbackResponder` returns `IsFallback = true` result from `Ai:Fallback` template table.

- ✅ **T007** Output validation: `SchemaAiOutputValidator` routes by feature key into registered
  `IContextBlock`-paired `AbstractValidator<TSchema>`. Corrective-prompt retry loop in `AiClientBase`
  bounded by `Ai:OutputValidation:MaxAttempts` (default 2). Markdown-fence stripping defensive pass.

- ✅ **T008** Content filtering: `ConfigurableAiContentFilter` with `PiiDetector` (email, phone, SSN,
  CC-pattern, IPv4) and `BannedTermDetector` (config-driven, word-bounded, severity-classified).
  Per-feature action overrides (reject/redact/off) for both input and output. Filter outcomes logged
  at `Information` — matched substrings never logged.

- ✅ **T009** `ai_usage` schema migration: new `ssp.ai_usage` table with compliance column set —
  `account_id` (NOT NULL, CASCADE), `user_id` (nullable, SET NULL), `feature`, `model`, token counts,
  `cost_usd`, `latency_ms`, `success`, `error_message`, `prompt_hash`, `output_hash`, `consent_status`,
  `data_residency_region`, `trace_id`, `content_filter_outcome` (JSONB). Indexes: account FK companion,
  account+created_at rollup, trace_id lookup.

- ✅ **T010** Usage log service: `IAiUsageLogger` seam + `AiUsageLogger` implementation following
  `AuditService` safe-write pattern. SHA-256 `prompt_hash` and `output_hash` via `AiUsageHasher`.
  Wired into `AiClientBase` finally-block so one row always writes — success, fallback, or failure —
  and a logger fault never poisons the AI result.

- ✅ **T011** Context block base: `IAiContext` interface (`Exists` bool + `ToPromptString() → string`).
  Convention: `Exists = false` → `ToPromptString()` returns `string.Empty`; callers concatenate
  unconditionally. Visual/renderer fields exposed as typed properties, not included in prompt string.

- ✅ **T012** Brand context block (`BrandContext`): loads `brand_settings` — voice description, tone
  tags, values, tagline. Visual fields (palette, `color_roles`, logo URL, fonts) exposed as properties
  for renderers. `ToPromptString()` omits them.

- ✅ **T013** Org context block (`OrgContext`): loads `accounts` — org name, industry key, address, locale,
  timezone.

- ✅ **T014** Industry context block (`IndustryContext`): loads `industry_template_configs` — industry key,
  vocabulary, recurring-value labels, member noun.

- ✅ **T015** Email-generate proof of pattern: migrate `/api/email/generate` (or equivalent BFF route)
  to call through `IAiClient` + compose `BrandContext + OrgContext + IndustryContext`. Output is
  byte-identical to pre-migration; this is the pattern all subsequent features follow.

- ✅ **T016** System/template field tag seed: migrate `contact_field_definitions` — seed `field_tags`
  for 11 system fields (universal defaults) and all membership-template fields (per-industry defaults)
  as a content migration. Custom fields left for field-tagging UI (T037).

- ✅ **T017** Multi-tenant isolation: `ITenantAiClient` wraps `IAiClient` and auto-injects `AccountId`
  + `UserId` from the authenticated session. `ValidateRequest` fails fast on `AccountId == Guid.Empty`.
  All context block reads scoped by `AccountId`. No AI call exists without a tenant.

- ✅ **T018** Prompt management: extract system prompts from inline route code to
  `SSP.AI/Prompts/<Feature>/` files as named builder classes. Route code composes blocks +
  calls the builder; no prompt strings inline in API handlers.

- ✅ **T019** Spend cap enforcement: `DailyAiSpendCapEnforcer` reads the org's daily cap from config
  (default value in `Ai:SpendCap`; per-org override in DB). Blocks before the provider call. Records
  the blocked attempt in `ai_usage` (success = false, error = "spend_cap_exceeded").

- ✅ **T019a** Persist content filter outcome: structured JSONB outcome from `ConfigurableAiContentFilter`
  (PII categories, banned-term hits with severity, action taken) persisted to `ai_usage.content_filter_outcome`
  for AI Act explainability. Previously written as null.

- ✅ **T020** Azure AI Foundry provider adapter: `AzureFoundryAiClient` behind the same `IAiClient`
  contract. Provider selection via `Ai:Provider` / `AI_PROVIDER` env var (`anthropic` = default;
  `azure-foundry` = Foundry). `ModelClass.Opus` added for reasoning-heavy workflows. Deployment-name
  placeholder stubs in `appsettings.common.json` — must be replaced with live values before enabling.

**Capture-surface data layer (Story 1.8 — hotfix track):**

- ✅ **T021** Industry template configs table: `industry_template_configs` — EF Core entity, migration,
  reader. Deop-owned (Account FK dependency).

- ✅ **T022** Account schema gap + organisation-setup fields: `accounts` table additions for org-setup
  BFF. Data layer only.

- ✅ **T023** `organisation_profile` + `voice_samples` data layer: tables, EF Core entities, migrations.

- ✅ **T024** `kb_documents` + `kb_chunks` + Foundry embeddings: tables with pgvector `embedding` column
  (3072 dims, `text-embedding-3-large`). Embedding generation via Azure Foundry embeddings adapter.
  Data layer only — upload workflow in T027.

- ☐ **T025** `brand_settings` coordination: read-only access for Deop context blocks. Click engineering
  owns the table. Deop needs confirmed column names and read path. _Blocked on Click confirmation._ [#83]

**Launch context blocks (Story 1.9 — shipped):**

- ✅ **T026** Profile context block (`ProfileContext`): loads `organisation_profile` + `voice_samples` —
  audience description, tier names, up to 5 voice exemplars.

- ✅ **T027** Event context block (`EventContext`): loads event-specific data — event title, date, location,
  registration URL. Used for event journey email generation.

- ✅ **T028** Brief context block (`BriefContext`): loads campaign brief data — intent, audience description,
  key messages. Used when a brief is attached to a generation call.

- ✅ **T029** Contact fields context block (`ContactFieldsContext`): loads `contact_field_definitions` with
  their tags — available merge tags and their semantic meanings for copy generation.

- ✅ **T030** Knowledge context block (`KnowledgeContext`): loads `kb_chunks` via pgvector similarity search
  scoped by `account_id` — top-K relevant chunks for the prompt. Curated (shared) and org-scoped content.
  Generalised from chat-agent-only to all features.

- ✅ **T031** Form generation feature (Task 1.9.1): `POST /forms/generate` → validated `GeneratedFormDefinition`
  (3–12 fields, 9 type values, snake_case keys). Persisted to `forms.definition_json`. Composes
  `BrandContext + OrgContext + IndustryContext (+ ProfileContext optional)`. Corrective-prompt retry
  via `FormGenerateOutputValidator`. [#88]

**BFF write endpoints (Story 1.8 follow-up — in flight):**

- ✅ **T032** Organisation-setup BFF endpoint: `POST/PUT` for org-setup data via the data layer from T022.
  [#84]

- ✅ **T033** Organisation-profile + voice-samples BFF endpoints: CRUD endpoints for profile and voice
  samples. [#85]

- ✅ **T034** KB document upload + ingest workflow + search endpoint: upload pipeline (chunking +
  embedding generation via Foundry), `POST /kb/documents`, `GET /kb/search`. [#86]

- ✅ **T034a** HNSW similarity index on `kb_chunk.embedding`: `ivfflat` or `hnsw` index for sub-100ms
  top-K search on a large chunks table. [#87]

**Launch readiness (Story 1.10 — in flight):**

- ☐ **T035** `/AI/README.md` handover documentation: developer-facing README for `SSP.AI` —
  architecture, how to add a context block, how to add a feature, how to run tests. [#93]

- ☐ **T036** Foundry model spike + 1-page memo: live Azure check against Foundry endpoint — confirm
  deployment name convention, model parity (prompt caching, vision support), pricing, EU region
  availability. Required before Foundry can be promoted to launch dependency. [#94]

**Checkpoint:** A tenant can call any AI feature through a single pipeline that logs cost, enforces
spend caps, filters content, validates output, and degrades gracefully. Pipeline is provider-agnostic
and swappable to Foundry via config.

---

## Phase 2: Unified Email-Content Component (Epic 2 / PR 10)

**Purpose:** Extract and generalise the existing `AIEmailModal` / email generation into a unified
component callable from the email editor, journey editor, and recommendation action handlers.
First customer-visible AI feature (journey emails can be AI-generated with brand + context).

**Delivery state:** Deop backend scope (Stories 2.1 + 2.3) complete. Click scope (Story 2.2) next.

**Deop scope — shipped:**

- ✅ **T037** Unified email generation service (`BrandedEmailGenerator`): function callable from any
  surface — `generateBrandedEmail({ intent, context, cta?, structuralOptions? }) → { subject,
  previewText, body_html, suggested_cta, derived_from_context }`. Composes context blocks based
  on `GenerationContext` kind. Validates output against `EmailOutputSchema`. [#27]

- ✅ **T038** `GenerationContext` discriminated union: `campaign_email | journey_step | standalone`.
  `journey_step` with `eventId` → CTA pre-filled from event's `registration_url`. Headless callers
  (recommendation handlers) use the API directly without the modal. [#28]

- ✅ **T039** Unified email BFF endpoint: `POST /bff/accounts/{id}/emails/generate`. Returns discriminated
  result (`Success`, `InvalidRequest`, `ProviderFailed`, `MalformedOutput`, `EmptyOutput`) — headless-first,
  no exceptions for expected failures. [#29]

- ✅ **T040** Integration contract + hand-off documentation: `unified-email-integration-contract.md` in
  `Core/AI/docs/`. Curl stubs for Click testing without Angular UI (the Week-4 gate). [#98]

**Click scope — next:**

- 🔜 **T041** Angular `AIEmailModal` component refactoring: extract the existing ~300-line inline modal
  into a shared Angular component. Swap `emailId` prop for the `GenerationContext` discriminated
  union. Calls `POST …/emails/generate`. [#31]

- 🔜 **T042** Journey editor wire-up: wire `AIEmailModal` into the journey editor for per-email-step
  generation with journey step context → CTA pre-fill from event. [#32]

**Merge order:** Land Epic 1 (PR #111) → then one Epic 2 PR (Deop 2.1/2.3 + Click 2.2 together).

**Checkpoint:** A journey step email can be AI-generated in the journey editor with brand + event
context. CTA pre-fills from event registration URL. Headless curl stubs pass.

---

## Phase 3: Web Agent Cleanup & Field-Tagging UI (Epic 3 / PR 11 + PR 11p)

**Purpose:** Clean up the agent taxonomy (Web Agent only), migrate confirmation emails to journeys,
and ship the field-tagging settings UI so custom contact fields get semantic labels. These are the
two structural changes that unblock full audience block richness in Phase 4.

**Dependency:** Phase 2 must be complete — confirmation emails move to journey steps, which requires
the unified email component (T037) to exist.

- ☐ **T043** Product agent definition (Web Agent Only): document and enforce the definition — Web Agent
  (multi-turn inbound conversation handler) is the only customer-facing agent type. Rename/deprecate
  any route or service that violates this. [#35]

- ☐ **T044** Confirmation email → journey migration: form-agent and event-agent triggers stop sending
  AI confirmation emails. A journey (automatically created by the form/event) takes over — its first
  step is the confirmation email, generated via the unified component (T037). Form-agent and
  event-agent retain only: enrol the contact in the journey + open the Web Agent conversation thread
  for inbound replies. [#36]

- ☐ **T045** Web Agent / inbox runtime narrowing: ensure the Web Agent only handles inbound replies
  (the runtime case). Remove any creation-time email sending still in the Web Agent path after T044. [#37]

- ☐ **T046** Field-tagging settings page at `/dashboard/settings/ai-ready`: three-tier display —
  system fields (pre-tagged, read-only with "system" label), template fields (pre-tagged, read-only
  with "template" label), custom fields (interactive — AI-suggested tags shown for user to accept/override).
  Shows readiness percentage prominently. [#39]

- ☐ **T047** 3-tier tag rendering: implement the visual distinction between system / template / custom
  tiers in the settings UI. Read-only tiers have no edit affordance; custom fields have tag picker. [#40]

- ☐ **T048** AI tag suggestion for custom fields: on settings page load, request AI-suggested `field_tags`
  for any custom field with `ai_suggested_tags` null. Store result in `contact_field_definitions.ai_suggested_tags`.
  User accepts or overrides — accepted tags write to `field_tags`. [#41]

**Checkpoint:** No customer-facing form-agent or event-agent email sending; confirmation emails are
journey steps. Admin can tag custom contact fields; field-tagging page shows ~80% pre-tagged state
for a typical org.

---

## Phase 4: Context Blocks + AI Surface Parity Wiring (Epic 4 / PR 12)

**Purpose:** Build the remaining context blocks (methodology, plan, insights, audience, assets) and
wire every major AI surface to the full block composition the architecture envisions. Non-customer-facing
— this is the substrate that makes Epic 5 rich.

**Dependency:** Field-tagging UI (T046–T048) must be shipped — the field-semantics and audience
blocks depend on tagged custom fields returning meaningful data.

**Checkpoint dependency:** End-of-week-8 gate — if field-tagging UI is not shipping with users
actually tagging, decide: extend two weeks, or ship Phase 4 with sparse audience context.

- ☐ **T049** Methodology context block (`MethodologyContext`): loads `marketing_disciplines`,
  `goal_types`, `programmes`, `tag_labels` — active framework content for the org's vertical. [#44]

- ☐ **T050** Plan context block (`PlanContext`): loads `marketing_plans` + `plan_goals` + `plan_programmes` —
  active plan, current goals and targets, performance vs target. [#45]

- ☐ **T051** Field-semantics context block (`FieldSemanticsContext`): loads `contact_field_definitions`
  with `field_tags` — what each field means in business terms. Consumes data seeded in T016 and
  tagged by customers via T046–T048. [#47]

- ☐ **T052** Audience context block (`AudienceContext`): loads `audiences` + `audience_contacts` +
  field-semantics (T051) — recipient description in semantic terms ("active members renewing within
  90 days"). Degrades gracefully when field-semantics data is sparse. Depends on T051. [#48]

- ☐ **T053** Insights context block (`InsightsContext`): cross-org aggregate benchmarks scoped by industry.
  Minimum-N threshold enforced (5–10) — returns "n/a" below threshold to prevent single-org identification. [#50]

- ☐ **T054** Assets context block (`AssetsContext`): exposes `content_assets` table (AI-tagged images,
  videos, audio, files) to AI features — filterable by `tags`, content type, semantic search. Image
  assets have AI-generated `description` + `tags`; non-image assets have user-supplied names only
  (full analysis = v2). [#53]

- ☐ **T055** Feature → block composition registry: defines which blocks compose for each feature key
  (matches the composition table in §6.3 of the strategy doc). Central registry, not per-route decisions.
  Composition changes in one file. [#55]

**AI surface parity wiring (Story 4.6):**

- ☐ **T056** Forms v2 generation + refinement wiring: wire the form generation feature (T031) to the
  full block composition from the registry. Add refinement (edit-with-AI for an existing form).
  [#73, GitHub: Task 4.6.1]

- ☐ **T057** Forms v2 field mapping wiring: wire form field definitions to the field-semantics block
  so AI-suggested field labels use industry vocabulary. [#74, GitHub: Task 4.6.2]

- ☐ **T058** Landing page generation, refinement, and layout switching wiring: `POST /landing-pages/generate`
  returning a structured layout JSON. Compose `BrandContext + OrgContext + IndustryContext`. Layout
  switching: AI picks from available layout templates based on intent. [#75, GitHub: Task 4.6.3]

- ☐ **T059** Events create-with-AI surface contract: define the API contract for AI-assisted event
  creation (name, description, dates, CTA suggestions). Block composition: brand + org + industry +
  event context. [#76, GitHub: Task 4.6.4]

- ☐ **T060** Web Agent context and knowledge wiring: wire `KnowledgeContext` (T030) + `BrandContext` +
  `OrgContext` + `IndustryContext` into the Web Agent conversation handler. Agent responses should
  reflect org voice and leverage KB content. [#77, GitHub: Task 4.6.5]

- ☐ **T061** Profile research, insights ask, social generate, and inbound-classification contracts:
  define API contracts and block compositions for four secondary AI surfaces — profile research,
  free-text analytics query ("ask Insights"), social post generation, and inbound message classification.
  [#78, GitHub: Task 4.6.6]

- ☐ **T062** AI feature key and invariant registry: documented list of every feature key used in
  `ai_usage`, with the expected block composition, model class, and schema. The "no feature goes
  unregistered" invariant. [#79, GitHub: Task 4.6.7]

**Checkpoint:** Every major AI surface is wired to a full block composition via the registry.
End-of-week-8 gate: is field-tagging UI driving real custom-field tags? If yes, continue to Epic 5.
If not, decide whether to defer audience-block richness.

---

## Phase 5: Recommendation Actions & Command Centre (Epic 5 / PR 13 + PR 14)

**Purpose:** Wire the Insights command centre ("Today" page) to real AI-generated audiences, journeys,
and email content via the unified component. Phase 2 of the trust-building progression: customer
clicks "Build the campaign" → system creates audience, generates journey, populates each email step
with brand-aware AI content → opens preview. Explicit confirm before anything sends.

**Dependency:** All context blocks (Phase 4) must be complete — recommendation action handlers compose
all available blocks.

**Checkpoint dependency:** End-of-week-10 gate — if recommendation-to-action flow produces poor
content, allocate prompt-tuning time before PR 14 surfaces it to customers.

- ☐ **T063** Recommendation action schema: extend `recommendation_actions` table — `ai_call_trace_id`,
  `action_journey_id`, `action_audience_id`. Define the discriminated result type for action commits. [#58]

- ☐ **T064** Action handler implementation: `POST /recommendations/{id}/commit` → creates audience,
  creates journey with AI-generated email steps via the unified component, writes audit entry.
  All context blocks flow in. Segment-level hyperpersonalisation enabled here (Phase 2). [#59]

- ☐ **T065** Confidence labelling: `ai_recommendations` extension — `confidence_type` ('counted' | 'suggested'),
  `source_signal_id`, `plan_goal_id`, `programme_id`. Counted = rules-based ("we counted 412 lapsed");
  suggested = AI-generated ("we think Tuesday morning would lift opens"). Conflating these erodes trust. [#60]

- ☐ **T066** Preview-and-confirm flow: the action handler returns a structured preview (audience count,
  journey template, projected impact, AI-generated email previews). Customer reviews and confirms.
  One-click never sends. Audit-trail entry written on confirm. [#61]

- ☐ **T067** Today page (Insights command centre): new `/dashboard/insights` route — prioritised
  recommendation feed, mini calendar widget, AI palette input. New front door of the product. [#63]

- ☐ **T068** Recommendation cards: card UI composing insight + recommendation + action. Preview-and-confirm
  flow wired in. Confidence label ("Counted" / "Suggested") displayed on card. [#64]

- ☐ **T069** Retain dashboard: membership-specific retention view — at-risk members, lapsed cohort,
  win-back, renewal pipeline. [#65]

- ☐ **T070** Command palette (⌘K): free-text analytical query against Insights data. [#66]

- ☐ **T071** Observability verification: confirm `ai_usage` is capturing cost / latency / retry counts
  per feature. Identify any feature not routing through the pipeline. [#68]

- ☐ **T072** GDPR compliance check: lawful-basis documentation, data-subject rights wiring,
  `ai_usage` retention policy, DPA template ready. [#69]

**Checkpoint:** Customer can click "Build the campaign" on a recommendation card → audience is created,
journey is generated with AI email content, preview opens, customer confirms. Nothing sends until
explicit confirm. Audit trail written.

---

## Timeline

One Deop developer (Deop scope) + Click developer (Click scope / Story 2.2), roughly in parallel from
Sprint 2 onward. Sprints are ~2 weeks. Checkpoint weeks are real gates — commit or adjust scope.

| Sprint | Scope | Deop outcome | Click outcome |
|--------|-------|--------------|---------------|
| 1 | Phase 1 (Epic 1) | 334-test AI substrate; email-generate proof; 9 context blocks; form generation | — |
| 2 | Phase 2 (Epic 2) | Backend unified email endpoint + integration contract delivered | Angular `AIEmailModal` refactor + journey editor wire-up |
| 3 | Phase 3 (Epic 3) | Web Agent cleanup, confirmation emails → journeys, field-tagging UI | — |
| 4 | Phase 4 (Epic 4) | Remaining context blocks + AI surface parity wiring | — |
| 5 | Phase 5 (Epic 5) | Recommendation action handlers, preview-and-confirm | Today page + Retain dashboard + ⌘K palette |

**Checkpoint weeks:**
- **End of week 4 (after Epic 2):** Is the unified email-content component the right keystone?
  If struggling, cut journey-content integration to v2 and lean on templates.
- **End of week 8 (after Epic 4 start):** Is field-tagging UI driving real custom-field tags?
  If not, decide whether to extend or ship Phase 2 recommendations with sparse audience context.
- **End of week 10 (after Epic 5 / PR 13):** Is the recommendation-to-action flow producing
  acceptable content? If poor quality, allocate prompt-tuning time before PR 14 surfaces it.

---

## Critical path

`T005 (IAiClient) → T015 (email proof) → T037 (unified email component) → T064 (action handlers)` is the
main trunk. Everything else serves this path or runs parallel to it.

- **Field-semantics data** → `T052 (AudienceContext)` → `T064 (action handler depth)`.
  Custom-field tagging (T046–T048) is the real gate on audience block richness.
- **T037 (unified email component)** → `T044 (confirmation email migration)` — journeys need the
  component before form/event agents can hand off.
- **All context blocks** → `T064 (action handlers)` — recommendation handlers compose everything.

---

## Dependencies & execution order

- **Phase 1 → everything:** The `IAiClient` pipeline and first three context blocks must exist before
  any Phase 2–5 feature.
- **T015 (email proof) → T037 (unified component):** Proof-of-pattern establishes the block composition
  idiom the unified component codifies.
- **T031 (form generation) → T056 (forms v2 parity wiring):** Form generation feature must exist before
  refinement wiring adds on top.
- **T037 (unified email component) → T044 (confirmation email migration):** Agents can only hand off
  confirmation email responsibility once the unified component exists.
- **T046–T048 (field-tagging UI) → T051 (field-semantics block) → T052 (audience block):** Field
  semantics block returns meaningful data for custom fields only after tagging UI ships and customers tag.
- **All Phase 4 blocks → T064 (action handlers):** Recommendation handlers need methodology, plan,
  insights, audience, assets context to produce rich content.
- **T063 (action schema) → T064 (action handler) → T065 (confidence labelling) → T066 (preview-confirm):**
  In order within Epic 5.
- **Epic 5 (PR 13) → Epic 5 (PR 14):** Recommendation action handlers must pass the end-of-week-10
  content quality gate before surfacing on the Today page.

---

## Open questions

Carried — not resolved here:

- **Foundry launch dependency.** Does Azure AI Foundry need to be a launch dependency, or does Anthropic
  direct ship at launch and Foundry migrates post-launch? T036 (Foundry spike memo) produces the
  input for this decision. Current assumption: post-launch.

- **Email refinement (edit-with-AI) scope.** Launch or v1.1? The unified component supports it architecturally
  but no task is scoped. Decide before Epic 2 merges.

- **Email import scope.** Post-launch deferral confirmed, or promoted? Decide before Epic 2 merges.

- **Segment-level hyperpersonalisation definition.** How many segment variants does T064 generate
  per recommendation action at launch? Uncapped variants = uncapped AI cost per send. A per-send
  variant cap must be set before T064 ships.

- **KB ingestion UX.** How does the customer add content to the org-scoped KB? File upload, URL scrape,
  manual paste? Each is a different surface. Needs a dedicated planning conversation before Epic 4.

- **Tag vocabulary expansion.** When B2B / non_profit / wealth_management ship, does the 8-tag
  vocabulary grow globally or per-vertical? Product decision — no impact on Epic 3 scope.

- **Non-image asset AI analysis.** PDF, video, and audio assets have no `description` or `tags` today —
  only user-supplied names. Include in assets block at v1 or explicitly defer?

- **`audience_contexts` materialised view.** The strategy mentions an optional materialised view of
  "audience X means semantically Y." Include in Phase 4 for audience block performance, or defer?

- **Per-send and per-feature concurrency limits.** Spend cap is per-day-per-org today. Per-send variant
  cap and per-feature concurrency limits are not yet scoped. Retrofit risk if the first surprise AI
  invoice arrives.
