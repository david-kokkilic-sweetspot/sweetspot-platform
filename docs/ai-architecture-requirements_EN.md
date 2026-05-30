# AI Architecture Strategy v2 — Requirements List

> Extracted line-by-line from `ai-architecture-strategy-v2.md`.
> Each requirement is numbered, quoted from the source, and tagged with its origin section.

---

## A. ARCHITECTURE — Client Wrapper (`/lib/ai/client.ts`)

### A1 — Single entry point for all AI calls
> "Every AI call goes through this wrapper. Direct calls to anthropic.messages.create outside `/lib/ai/client.ts` are a code-review red flag."
- **Section:** 6.2

### A2 — Provider abstraction
> "generate({ feature, system, messages, model_class }) → { content, usage, metadata }. Internally translates to Anthropic today, Azure AI Foundry post-migration, others if needed. Single point of swap."
- **Section:** 6.2

### A3 — Mandatory logging on every AI call
> "every call writes to `ai_usage` with `org_id`, `user_id`, feature, model, tokens in/out, cost, latency, success/failure, content hash, consent status, data residency region, trace ID. Non-negotiable: without it there is no cost visibility and no compliance audit trail."
- **Section:** 6.2

### A4 — Error handling with graceful degradation
> "transient failures retry with backoff. Permanent failures degrade gracefully with a feature-appropriate fallback (template-based content instead of AI-generated). Errors must surface, never swallowed."
- **Section:** 6.2

### A5 — Per-feature model selection
> "a single place to decide Sonnet vs Haiku per feature. Premium features (strategy, complex generation) use Sonnet; high-volume or latency-sensitive features (chat suggestions, classification) use Haiku."
- **Section:** 6.2

### A6 — Output validation with Zod schemas
> "when a feature provides a zod schema, the wrapper parses, validates, and retries with corrective prompting on failure. After N (default 2) failures returns a typed error."
- **Section:** 6.2

### A7 — Content filtering (PII + banned content)
> "PII detection in outputs, banned-content checks, redaction logging. Baked in from the start because it is far easier than retrofitting."
- **Section:** 6.2

### A8 — Provider-agnostic internal contract
> "not 'the Anthropic SDK wrapper'. The internal contract is provider-agnostic. Cost translation, content filtering, retry behaviour, validation all happen at this layer regardless of provider."
- **Section:** 9.2

### A9 — Provider-specific cost tables
> "The cost calculation in `/lib/ai/usage/cost.ts` must support provider-specific pricing tables."
- **Section:** 9.3

---

## B. ARCHITECTURE — Composable Context Blocks (`/lib/ai/context/`)

### B1 — Block function signature
> "Each block exports a function with this signature: `loadBlockContext(orgId: string, options?: BlockOptions): Promise<BlockContext>`"
- **Section:** 6.3

### B2 — Structured return with `.toPromptString()`
> "Where `BlockContext` is a structured object with field accessors and a .toPromptString() method, so consuming routes can either drop the full block into a prompt or pick specific fields they need."
- **Section:** 6.3

### B3 — Graceful degradation
> "Blocks must degrade gracefully when their data source is missing or sparse — return empty or a minimal stub, never throw."
- **Section:** 4.1

### B4 — No side effects
> "Blocks must not have side effects — reading and formatting only."
- **Section:** 4.1

### B5 — Block dependency awareness
> "Blocks may depend on other blocks (audience depends on field-semantics)."
- **Section:** 4.1

### B6 — Ten context blocks to build
> "brand, org, industry, methodology, field-semantics, audience, plan, insights, knowledge, assets"
- **Section:** 4.1 (table)

### B7 — Brand block sources
> "brand: `brand_settings` table + `color_roles` JSONB — Voice, palette, logo, sender info, role assignments (heading/body/CTA/etc.)"
- **Section:** 4.1

### B8 — Org block sources
> "org: organizations table — Org name, type, physical address, privacy URL"
- **Section:** 4.1

### B9 — Industry block sources
> "industry: industry_template_configs table — Vertical-specific tone, audience vocabulary, regulatory conventions"
- **Section:** 4.1

### B10 — Methodology block sources
> "methodology: marketing_disciplines, goal_types, programmes, tag_labels tables — Active framework content for the org's vertical"
- **Section:** 4.1

### B11 — Field-semantics block sources
> "field-semantics: Field-semantics extension on `contact_field_definitions` — What each contact field means in business terms"
- **Section:** 4.1

### B12 — Audience block sources
> "audience: audiences + audience_contacts + field-semantics — Recipient description in semantic terms ('active members renewing within 90 days'). For Phase 3+ hyperpersonalisation, also exposes per-recipient depth."
- **Section:** 4.1

### B13 — Plan block sources
> "plan: marketing_plans + plan_goals + plan_programmes — Active plan, current goals and targets, performance vs target"
- **Section:** 4.1

### B14 — Insights block sources
> "insights: Computed benchmarks from cross-org aggregates (privacy-respecting) — Industry-scoped benchmarks"
- **Section:** 4.1

### B15 — Knowledge block sources
> "knowledge: KB tables in Supabase (per-org and curated) — Top-K relevant chunks via vector search for the prompt. Org-scoped customer content plus Sweetspot curated content."
- **Section:** 4.1

### B16 — Assets block sources
> "assets: `content_assets` table (existing infrastructure, AI-tagged on upload) — Available images, videos, audio, files filterable by tags, content type, and semantic search."
- **Section:** 4.1

### B17 — Feature-to-block composition map
> email-generate: brand + org + industry + audience + plan + assets + (optional) knowledge
> journey-content: brand + org + industry + journey-context + audience + plan + assets
> form-generate: brand + org + industry
> chat agent: brand + org + industry + knowledge + conversation history
> strategy agent: brand + org + industry + methodology + plan + insights + knowledge
> insights-agent: org + industry + methodology + plan + insights + knowledge
> recommendation action: all of the above + signal context + recommendation reasoning
- **Section:** 6.3

---

## C. ARCHITECTURE — Unified Email-Content Component

### C1 — Single function for all branded email generation
> "A function callable from any surface that needs to produce a branded HTML email body. Three consumers at launch: the email editor (standalone), the journey editor (per email step), the recommendation action handler."
- **Section:** 6.4

### C2 — Function signature
> "`generateBrandedEmail({ intent, context, cta?, structuralOptions? }): Promise<{ subject, previewText, body_html, suggested_cta, derived_from_context }>`"
- **Section:** 6.4

### C3 — `AIEmailModal` prop contract refactor
> "replace `emailId` with a structured context object: `type GenerationContext = | { kind: 'campaign_email'; emailId: string } | { kind: 'journey_step'; journeyStepId: string; journeyId: string; eventId?: string; recipeId?: string; audienceId?: string } | { kind: 'standalone' }`"
- **Section:** 4.5

### C4 — Extract `AIEmailModal` to shared component
> "The current `AIEmailModal` component (≈300 lines, inline in the email send detail page today) … It needs a prop-contract refactor (from `emailId` to a `context` object) to support being called from outside the email editor"
- **Section:** 4.5

### C5 — Context-aware CTA derivation
> "when `kind === 'journey_step'` and `eventId` is present, the modal opens with the CTA URL pre-filled from the event's registration_url … For `standalone`, behaviour matches today: the user provides the CTA or toggles it off."
- **Section:** 4.5

### C6 — Unified backend route
> "The modal passes the context to a unified backend route. The route loads the appropriate context blocks based on the `kind` and feature-specific arguments, composes the prompt, calls the client wrapper, returns the result."
- **Section:** 4.5

### C7 — Headless callers supported
> "Headless callers (e.g. recommendation action handlers committing without further review) call the underlying API directly without rendering the modal."
- **Section:** 6.4

---

## D. ARCHITECTURE — Agent Redefinition

### D1 — Agent = multi-step, conversational, decision-making entity
> "an agent is a multi-step, conversational, decision-making entity. Single-call email senders are not agents — they are handlers or generators."
- **Section:** 4.3

### D2 — Form/event agent creation moves to journeys
> "Creation — moves to the journey. The journey's first step is the confirmation email, AI-generated with brand and event context. Including the .ics attachment as a journey-email feature, not an agent-specific feature."
- **Section:** 4.3

### D3 — Agent runtime stays for inbound
> "Runtime — stays with the agent. The agent handles inbound replies from the registrant, multi-turn, with context of the original registration."
- **Section:** 4.3

### D4 — Eliminate HTML-build duplication
> "the HTML-building duplication between email-generate / form-agent / event-agent disappears"
- **Section:** 4.3

---

## E. ARCHITECTURE — Asset-Shape Framework

### E1 — Three asset shapes
> "Branded HTML content — Customer-facing copy in branded HTML emails or pages"
> "Structural JSON — Schema or graph data the editor renders, brand-light"
> "Metadata — Short identifiers and descriptions"
- **Section:** 4.2

### E2 — Two creation paths per feature
> "every content-bearing feature has two creation paths producing the same shape of output … Pick template = start from a curated point. Pick AI = describe what you want, AI fills everything in. Both go through brand + industry context. Both are editable inline after creation."
- **Section:** 4.2

---

## F. ARCHITECTURE — Target Library Structure

### F1 — Directory structure under `/lib/ai/`
> ```
> /lib/ai/
>   client.ts, index.ts
>   /prompts/ — Per-feature system prompts as files, not inline in routes
>   /context/ — Composable context blocks (brand, org, industry, methodology, field-semantics, audience, plan, insights, knowledge, assets)
>   /knowledge/ — KB / RAG layer
>   /agents/ — Multi-step agent loops
>   /schemas/ — zod schemas for structured AI outputs
>   /usage/ — log.ts, cost.ts
> ```
- **Section:** 6.1

### F2 — Prompts as separate files
> "Per-feature system prompts as files, not inline in routes"
- **Section:** 6.1

---

## G. ARCHITECTURE — Hyperpersonalisation

### G1 — Segment-level (Phase 2, launch target)
> "AI produces a single email with audience-segment-tailored copy. Different copy for different lifecycle stages or tenure tiers within the same send. Assets are AI-suggested from the library based on context. Marketer reviews in preview before send."
- **Section:** 4.6

### G2 — Per-recipient (Phase 3+, post-launch)
> "AI generates unique content per recipient. Subject line, body copy, asset selection, CTA all consider this specific recipient … The send pipeline composes per-recipient at delivery time."
- **Section:** 4.6

### G3 — Cost control patterns required before Phase 3
> "Variant-based hybrid — AI generates N (e.g. 8) variants up front; per-recipient logic at send time picks the best match."
> "Per-section variants — for newsletters, AI generates a small number of variants per section."
> "Hard daily and per-send caps — per-org daily AI spend cap, per-send variant count cap, alerting at thresholds."
- **Section:** 4.6

---

## H. DATA — Schema Changes

### H1 — `ai_usage` table extension (PR 9)
> "Add columns: `user_id`, model, latency_ms, success, `error_message`, created_at, `prompt_hash`, `output_hash`, `consent_status`, `data_residency_region`, `trace_id`, `content_filter_outcome`"
- **Section:** 8.1

### H2 — `contact_field_definitions` population (PR 11p)
> "Already extended in earlier migration with `description`, `field_tags`, `ai_suggested_tags`. UI populates this."
- **Section:** 8.1

### H3 — `audience_contexts` new table/view (PR 12)
> "Optional materialised view of 'audience X means semantically Y' derived from filters + field-semantics. May be view or table."
- **Section:** 8.1

### H4 — `recommendation_actions` extension (PR 13)
> "Existing table extended: `ai_call_trace_id`, `action_journey_id`, `action_audience_id`"
- **Section:** 8.1

### H5 — `ai_recommendations` extension (PR 14)
> "Add: `confidence_type` ('counted' | 'suggested'), `source_signal_id`, `plan_goal_id`, `programme_id`"
- **Section:** 8.1

### H6 — Vendor-neutral SQL for all migrations
> "avoid Supabase-specific syntax where possible. Stick to ANSI Postgres."
- **Section:** 9.2

---

## I. DATA — Multi-Tenant Isolation

### I1 — All tables scoped by `org_id` with RLS
> "Every table has `org_id` and is protected by RLS via the `profiles.id` = `auth.uid()` pattern. AI-related additions follow the same pattern without exception."
- **Section:** 8.2

### I2 — No AI call without `org_id`
> "The wrapper reads `org_id` from the authenticated session and uses it as the scoping primitive for every context block read. No AI call exists without an `org_id`."
- **Section:** 8.2

### I3 — Knowledge retrieval scoped by `org_id`
> "vector search must filter by `org_id` for org-scoped content. Curated content is shared. The retrieval function enforces the scope, not the caller."
- **Section:** 8.2

### I4 — Benchmark minimum-N threshold
> "Must enforce a minimum-N threshold (5-10) to prevent identifying a single org. The block returns 'n/a' below threshold."
- **Section:** 8.2

### I5 — Cross-org reporting via separate service-role view
> "`ai_usage` is scoped per org. Cross-org reporting (for internal use) goes through a separate service-role view, not the customer-facing query."
- **Section:** 8.2

---

## J. DATA — Field-Semantics

### J1 — Three-tier field tagging
> "System fields (11, universal): Pre-tagged with universal defaults, seeded as content in PR 9. Read-only — no per-org override."
> "Template fields (per industry): Pre-tagged per industry, seeded as content alongside the framework. Read-only — no per-org override."
> "Custom fields (org-created): User tags during onboarding or later. AI suggests tags based on field name, type, and (where available) sample data. User confirms or overrides."
- **Section:** 8.3

### J2 — Seed system-field default tags (PR 9)
> "Seed system-field and membership-template-field default tags (small content migration)."
- **Section:** 7.1

### J3 — Field-tagging UI at `/dashboard/settings/ai-ready` (PR 11p)
> "Customer-facing UI at `/dashboard/settings/ai-ready` for tagging contact fields with semantic labels. Simpler than originally framed because system fields are pre-tagged … and template fields are pre-tagged per industry."
- **Section:** 7.1

### J4 — AI-suggested tags for custom fields
> "AI suggests tags based on field name, type, and (where available) sample data. User confirms or overrides."
- **Section:** 8.3

### J5 — Readiness percentage display
> "Shows readiness percentage prominently."
- **Section:** 7.1

### J6 — 8-tag controlled vocabulary for v1
> "`field_tags` (array of semantic tags with CHECK constraint to 8 controlled vocabulary values for v1)"
- **Section:** 8.3

---

## K. UI/UX — Insights Command Centre

### K1 — New IA: Today / Grow / Engage / Retain / Earn
> "Today — command centre at `/dashboard/insights`. Prioritised recommendation feed, mini calendar widget, AI palette input."
> "Grow — acquisition. Engage — channel performance. Retain — at-risk members. Earn — subscription revenue."
- **Section:** 3.3

### K2 — Recommendation card = Insight + Recommendation + Action
> "All three live on a single recommendation card with a preview-and-confirm flow."
- **Section:** 3.3

### K3 — Preview-and-confirm is non-negotiable
> "One-click never sends. Every commit shows the audience preview, the journey or campaign template, projected impact, and writes an audit-trail entry."
- **Section:** 3.3

### K4 — Confidence labelling: "Counted" vs "Suggested"
> "rules-based recommendations are labelled 'Counted' (we counted 412 lapsed); AI-generated recommendations are labelled 'Suggested' (we think a Tuesday morning send would lift opens). Conflating these erodes trust."
- **Section:** 3.3

### K5 — Recommendation action handler flow (PR 13)
> "Wire the Today-page command centre's 'Build the campaign' action to create real audiences, real journeys with AI content via the unified component."
- **Section:** 7.1

### K6 — Today page + Retain dashboard + ⌘K palette (PR 14)
> "The customer-facing surfaces of the Insights revamp. Today as command centre. Retain dashboard for membership. ⌘K analytical palette."
- **Section:** 7.1

---

## L. TRUST — Phase Progression

### L1 — Phase 1 (launch): Rules-based recommendations + explicit confirm
> "Surfaces rules-based recommendations; preview shows exact audience and content. Explicit confirm each time."
- **Section:** 3.4

### L2 — Phase 2 (launch): AI-generated content + plan-aware recommendations
> "Generates content for journeys and programmes; recommendation copy references plan goals; CTAs context-aware. Confirms one-click on content, still previews audience."
- **Section:** 3.4

### L3 — Phase 3 (post-launch): Routine actions auto-execute (opted-in, audited, undoable)
> "Routine actions execute without confirm — opted in, audited, undoable. Novel or risky actions still preview."
- **Section:** 3.4

### L4 — Phase 4 (future): Plan executes autonomously within user-set limits
> "Plan executes itself within autonomy limits the user set. User intervenes by exception."
- **Section:** 3.4

---

## M. MIGRATION — PR Sequence

### M1 — PR 9: Foundation + email-generate proof
> "Build `/lib/ai/client.ts`, `/lib/ai/usage/log.ts`, `/lib/ai/context/`{brand,org,industry}.ts. Migrate `/api/email/generate` as byte-identical proof of pattern. Extend `ai_usage` schema. Seed system-field and membership-template-field default tags."
- **Section:** 7.1

### M2 — PR 10: Unified email-content component
> "Extract `AIEmailModal` to a shared component. Refactor prop contract from emailId to `GenerationContext`. Build the unified backend route. Wire the modal into the journey editor for per-email-step generation. Includes context-aware CTA derivation."
- **Section:** 7.1

### M3 — PR 11: Form/event agent migration
> "Form-agent and event-agent triggers stop sending confirmation emails. Journeys take over (confirmation as first journey step). Agent triggers narrow to 'enrol in journey + open conversation thread for inbound'. The HTML-build duplication disappears."
- **Section:** 7.1

### M4 — PR 11p: Field-tagging UI
> "Customer-facing UI at `/dashboard/settings/ai-ready` for tagging contact fields with semantic labels."
- **Section:** 7.1

### M5 — PR 12: Context blocks (methodology, plan, insights, audience, assets)
> "Build `/lib/ai/context/`{methodology,plan,insights,audience,field-semantics,assets}.ts. Knowledge block generalised from chat-only to all features."
- **Section:** 7.1

### M6 — PR 13: Recommendation action handlers with AI content
> "Wire the Today-page command centre's 'Build the campaign' action to create real audiences, real journeys with AI content via the unified component. Phase 2 of the trust progression lights up here. Segment-level hyperpersonalisation enabled."
- **Section:** 7.1

### M7 — PR 14: Today page + Retain dashboard + ⌘K palette
> "The customer-facing surfaces of the Insights revamp."
- **Section:** 7.1

---

## N. MIGRATION — Decision Points

### N1 — End of week 4 checkpoint
> "is the unified email-content component working well enough to be the keystone? If yes, continue. If struggling, cut journey-content integration to v2 and lean on templates for launch."
- **Section:** 7.3

### N2 — End of week 8 checkpoint
> "is field-tagging UI shipping with users actually tagging? If not, audience block returns sparse data and Phase 2 recommendations lose half their power."
- **Section:** 7.3

### N3 — End of week 10 checkpoint
> "is the recommendation-to-action flow producing acceptable content? If yes, ship. If output quality is poor, allocate prompt-tuning time before PR 14 surfaces it."
- **Section:** 7.3

---

## O. MIGRATION — Risks

### O1 — Pre-production assumption
> "the cleanup assumes no live customers using form-agents or event-agents today."
- **Section:** 7.4

### O2 — Field-tagging UX complexity
> "the screen has to feel manageable for orgs with 40+ contact fields, suggest tags reasonably, and not punish someone for not tagging perfectly."
- **Section:** 7.4

### O3 — Prompt tuning post-migration
> "every route migrated to the unified component is a moment where output quality might shift. Plan 2-3 days of side-by-side testing per surface after migration."
- **Section:** 7.4

### O4 — Invisible weeks 5-8
> "the dangerous window where motivation dips because nothing customer-facing is moving."
- **Section:** 7.4

### O5 — Customer feedback loop
> "if no friendly customer sees Phase 1 features by week 6, Phase 2 is being built in the dark."
- **Section:** 7.4

---

## P. OBSERVABILITY

### P1 — Cost tracking per org per feature per month
> "supports usage-based pricing if it lands and supports cost-aware feature prioritisation."
- **Section:** 8.4

### P2 — Latency tracking per feature
> "needed to identify slow surfaces before customer complaints."
- **Section:** 8.4

### P3 — Retry tracking
> "every validation retry logged. Pattern of retries on the same prompt indicates a prompt that needs tuning."
- **Section:** 8.4

### P4 — Failure tracking
> "`error_message` column captures the failure mode."
- **Section:** 8.4

### P5 — Audit linkage via `trace_id`
> "`trace_id` links a single user action (e.g. 'user clicked Build the campaign on recommendation X') to all downstream AI calls. Required for the AI Act's 'explain why this was done' obligation."
- **Section:** 8.4

---

## Q. COMPLIANCE

### Q1 — GDPR mandatory at launch
> "Lawful basis for processing, data subject rights, breach notification, DPA. Already mandatory for UK-based product serving EU customers."
- **Section:** 9.1

### Q2 — SOC 2 Type 2 within 12 months
> "The gateway certification for enterprise sales."
- **Section:** 9.1

### Q3 — EU AI Act transparency obligations
> "Transparency obligations for 'limited risk' AI (which the recommendation engine likely is); higher obligations if anything classified as 'high risk'."
- **Section:** 9.1

### Q4 — ISO 42001 within 18 months
> "AI management system standard. Becoming enterprise ask in 2026."
- **Section:** 9.1

### Q5 — PII detection in outputs
> "outputs scanned for accidental disclosure of email addresses, phone numbers, or other PII not present in the input."
- **Section:** 9.4

### Q6 — Banned-content filters
> "basic profanity and regulated-topic detection. Customer-configurable thresholds."
- **Section:** 9.4

### Q7 — Redaction logging
> "when content is blocked or modified, log what was filtered and why. Required for the AI Act's explainability obligations."
- **Section:** 9.4

### Q8 — Content filtering centralised at client wrapper
> "filtering happens at the client wrapper, after the model returns and before content is delivered to the consuming route."
- **Section:** 9.4

---

## R. INFRASTRUCTURE — Forward-Looking

### R1 — Launch on Anthropic direct
> "launch on Anthropic direct with the wrapper in place."
- **Section:** 9.3

### R2 — Migrate to Azure AI Foundry post-launch
> "Migrate to Azure AI Foundry as a v1.5 PR once the launch is stable and the feature parity has been confirmed."
- **Section:** 9.3

### R3 — Configuration-driven provider selection
> "Environment variables — separate AI_PROVIDER (anthropic | azure_foundry | etc.), AI_REGION, AI_MODEL_DEFAULT, etc. Configuration-driven, not coded."
- **Section:** 9.2

### R4 — Log data residency region from day one
> "`ai_usage` `data_residency_region` column — even if today every call goes to anthropic.com, log the region from day one."
- **Section:** 9.2

---

## S. OPEN QUESTIONS (require decision)

### S1 — Client wrapper scope at PR 9
> "Minimal version (logging + retries + per-feature model selection) or full version (also validation + content filter + cost calculation) at PR 9? Recommendation: minimal for PR 9."
- **Section:** 10.1

### S2 — Prompt extraction strategy
> "Extract prompts to `/lib/ai/prompts/` as exported strings/functions, or compose context blocks into routes in-place? Recommendation: extract."
- **Section:** 10.1

### S3 — Context block return shape
> "String fragment or structured object with formatting methods? Recommendation: structured object with .toPromptString() and individual getters."
- **Section:** 10.1

### S4 — `ai_usage` column finalisation
> "Confirm the full target column set with the data architect before PR 9 schema migration lands."
- **Section:** 10.1

### S5 — Per-template brand-role overrides
> "Stored on `campaign_emails` or template? Defer to v2 or include in PR 10? Recommendation: defer."
- **Section:** 10.2

### S6 — Chat brand inclusion strategy
> "Multi-turn chat — brand in system message only, or re-injected per turn? Recommendation: system message only."
- **Section:** 10.2

### S7 — Agent brand depth
> "full block by default, dial back per-agent if over-styling emerges."
- **Section:** 10.2

### S8 — Tag vocabulary expansion strategy
> "As B2B / non_profit / wealth_management ship, the 8-tag vocabulary grows. Global-with-vertical-overrides or fully per-vertical?"
- **Section:** 10.3

### S9 — KB ingestion UX
> "How does the customer add content to the org-scoped KB? File upload, URL scrape, manual notes, bulk paste?"
- **Section:** 10.3

### S10 — KB content types at launch
> "Which formats are supported in v1? Docs, web pages, plain text, all of the above?"
- **Section:** 10.3

### S11 — Curated knowledge content sourcing
> "Who authors Sweetspot's editorial KB layer? Internal team, partner-sourced, or AI-generated and human-reviewed?"
- **Section:** 10.3

### S12 — Always-on vs selective KB retrieval
> "Always-on is simpler but token-expensive. Selective requires a classifier. Recommendation: start always-on."
- **Section:** 10.3

### S13 — Asset auto-suggestion in AI generation
> "should the AI auto-propose assets from the library, or wait for the user to invite asset selection? Default proposal: auto-suggest in Phase 2."
- **Section:** 10.3

### S14 — Non-image asset AI analysis
> "Should PDFs, videos, and audio files also be analysed? v2 conversation."
- **Section:** 10.3

### S15 — SOC 2 readiness timeline
> "What is the target audit window?"
- **Section:** 10.4

### S16 — EU AI Act risk classification confirmation
> "Worth a legal review to confirm before launch and to scope what disclosure UX is required."
- **Section:** 10.4

### S17 — Data residency at launch
> "Do early customers require EU-region processing for AI calls? If yes, Azure AI Foundry migration moves to launch dependency."
- **Section:** 10.4

### S18 — Cost controls
> "Per-org daily spend cap, per-feature concurrency limit, alerting threshold. Easy to add now, painful to retrofit."
- **Section:** 10.4

---

## SUMMARY

| Category | Count |
|----------|-------|
| Architecture requirements | 30 |
| Data / schema requirements | 17 |
| UI/UX requirements | 6 |
| Trust / phase requirements | 4 |
| Migration PRs | 7 |
| Decision checkpoints | 3 |
| Risks | 5 |
| Observability requirements | 5 |
| Compliance requirements | 8 |
| Infrastructure requirements | 4 |
| Open questions requiring decision | 18 |
| **Total** | **107** |
