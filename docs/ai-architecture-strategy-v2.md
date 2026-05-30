# Sweetspot

## AI architecture strategy

### Reference document for technical review

**Status:** Draft v2 — updated to reflect amendments around contact field tier structure, `AIEmailModal` reuse for journey email generation, asset context block, and hyperpersonalisation scope. For review with data architect and partner engineering reviewers. 

**Audience:** Engineers and architects new to the codebase. Assumes no prior Sweetspot context. Pairs with the existing architecture and migration spec documents in the repository. 

**Scope:** Captures the AI architecture decisions, the current state of the system, the target state, the migration plan to get there, and the forward-looking infrastructure and compliance requirements. 

**Out of scope:** Specific prompt content; UI design specifications; CRM adapter pattern (covered separately); non-AI infrastructure concerns; pricing and packaging. 

## 1. Executive summary

Sweetspot is an AI-first, CRM-agnostic marketing automation product for membership organisations. The product positions itself against tools like HubSpot and Mailchimp by being opinionated per industry — codifying marketing methodology, benchmarks, and best practices for a specific vertical rather than offering a generic configurable platform. 

The "AI-first" claim rests on three interlocking pillars: a codified methodology layer per industry (what good marketing looks like), an AI-readiness layer that makes contact data semantically legible (so the AI understands what fields mean), and a composable context substrate that feeds every AI feature with the same brand, industry, plan, audience, and methodology data. 

Today, AI features are independently implemented across different routes — each reading its own narrow slice of brand and industry data, each duplicating its HTML-building logic, none of them composing the available context the way the architecture envisions. This document describes the path from that state to a unified, composable, compliance-ready AI substrate that the product's strategic ambition requires. 

The migration is sequenced over 10-15 weeks and is the foundation for two converging product threads: (a) launching the recommendation-driven command-centre vision where Insights drives action, not just reporting, and (b) eventually meeting enterprise compliance and security standards including SOC 2 Type 2, GDPR, the EU AI Act, and supporting infrastructure migration to Azure with AI Foundry as the model provider. 

#### Why this document exists

**Three reasons:** 

Onboarding context for new technical reviewers. The existing architecture and migration spec documents in the repository assume familiarity with prior decisions. This document captures that prior context in one place. 

Decisions that affect the data layer. The data architect needs visibility into the schema implications (new tables, extended schemas, RLS patterns) before code lands. 

A defensible "AI-first" claim at the architecture level. Partners and customers doing technical diligence should see a coherent design, not a collection of independent AI calls. 

#### Document map

Sections 2-3 establish product and strategic context. Section 4 describes the architecture model. Section 5 audits current state. Section 6 describes target state. Section 7 lays out the migration plan. Sections 8-9 address data architecture and compliance specifically. Section 10 captures open questions. Section 11 is the glossary. 

## 2. Product context

### 2.1 What Sweetspot is

Sweetspot is a marketing automation product for membership organisations. The customer is a marketing lead at a membership-based organisation (professional associations, trade bodies, member-driven non-profits, faith organisations, etc.) who is responsible for acquisition, renewal, engagement, and event programming. They typically have a small team and either no formal CRM or a lightweight one. Today they juggle this work across spreadsheets, email platforms, project tools, and their CRM if they have one. 

Sweetspot replaces that fragmented stack with a single product that covers acquisition, renewal, lapsed re-engagement, event and conference promotion, donor cultivation, content programming, and attribution. It deliberately does not extend into sales pipeline management, deal forecasting, service ticketing, CMS, or generic RevOps workflow. The marketer is the user; the salesperson is not. 

### 2.2 Why "AI-first" is a real claim

Three things together make the AI-first positioning defensible rather than marketing language: 

- **Methodology and content per vertical.** For membership orgs (v1), Sweetspot ships with 5 marketing disciplines, 5 goal types, 13 programme templates, and 8 field-semantic `tags` as authored, curated content. This is not AI-generated. The AI walks customers through a known, opinionated methodology rather than inventing strategy. 

- **AI-readiness layer (field semantics).** Contact fields are tagged with what they mean in business terms (renewal_date is a renewal signal, last_login_at is an engagement signal, lifecycle_stage is a journey indicator). Without this layer the AI is a chatbot wrapped around a database; with it the AI can reason about renewals, engagement, and lifecycle. 

- **CRM-agnostic adapter.** Customers without a CRM can use Sweetspot as system of record. Customers with a CRM connect through an adapter pattern, never replaced. Lowers switching cost and adoption friction. 

### 2.3 Launch profile

Launch is membership-only, in 3-4 months. B2B framework (based on the Volaris growth playbook) is queued for v2 pending IP confirmation. Non-profit and wealth-management verticals exist as architecture stubs only. 

Pre-production today. Active customer conversations and demos are happening, and one or two friendly customers will be working closely with the team during the launch window, but no customer accounts are provisioned yet. This affects migration risk: schema and code changes do not need to support backward compatibility with live customer configurations during the cleanup work described here. 

Infrastructure migration to GitHub Enterprise, Postgres on Azure, Azure-hosted application, and Azure AI Foundry as the model provider is anticipated post-launch (v2 or later). The architecture decisions in this document are made with that migration in mind, so the design does not need to be rewritten when the migration happens. 

### 2.4 What is already AI-ready

Several pieces of the substrate this document describes are already partly built. Calling them out here so reviewers do not assume everything is greenfield: 

- **Asset library with AI tagging.** The asset management feature exists (`content_assets` table, folder structure, search). Image uploads are automatically analysed by `/api/content/analyse` and given AI-generated descriptions and `tags`. The infrastructure for an asset context block is therefore mostly in place — what is missing is exposing it to other AI features. 

- **Contact field tier structure.** Contact fields already split into three tiers in the contacts settings UI: 11 system fields (universal, hardcoded), template fields (industry-seeded, can be hidden but not deleted), and custom fields (user-created with full CRUD and CRM mapping). The field-semantics extension columns (`description`, `field_tags`, `ai_suggested_tags`) exist on `contact_field_definitions` but are not yet surfaced in any UI. 

- **Marketing framework v1 (membership).** 12 schema tables with RLS, 5 disciplines, 5 goal types, 13 programmes, 8 tag labels seeded. Plan workspace UI live end-to-end (creation, goals, programmes, performance). 

- **Brand role assignments.** 8-role system (heading, body, link, cta_bg, cta_text, canvas, callout_bg, divider) live, with `brand_settings`.`color_roles` JSONB column. Role-aware email generation working in `/api/email/generate`. 

- **AI email generation modal.** The `AIEmailModal` component (currently inline in the email send detail page) is substantially reusable for journey email steps. It needs a prop-contract refactor (from `emailId` to a `context` object) to support being called from outside the email editor — but the UI, the generate-review-edit-confirm flow, and the inline contentEditable preview all transfer. 

The migration in this document leans on these foundations rather than rebuilding them. 

## 3. The strategic foundation

The AI architecture serves a specific product strategy. Understanding the strategy is necessary to understand why the architecture is shaped the way it is. 

### 3.1 Industry is the foundational layer

Every Sweetspot organisation is bound to an industry template at sign-up (today: membership, b2b, non_profit, wealth_management). Industry drives four distinct downstream things: 

- **Vocabulary.** Member vs customer vs client vs donor. "Renewal date" vs "subscription end" vs "contract end". Industry-specific terminology that surfaces throughout the UI and AI prompts. 

- **Methodology.** The marketing framework (disciplines, goal types, programme templates, KPIs) that powers the strategy/plan workspace. This is curated content, not AI-generated. 

- **Benchmarks.** Industry-scoped comparison data — average open rates, average member tenure, average renewal cadence — used in Insights to ground recommendations. 

- **Recommended defaults.** Goal types, signals, audience shapes, programme suggestions that pre-populate the customer's workspace based on what is known to work in their vertical. 

Industry is parallel to brand in the architecture, not downstream of it. Brand is org-specific identity (voice, colours, logo). Industry is industry-shaped advice. Both feed the AI context layer but neither owns the other. 

### 3.2 The marketing plan as a quarterly playbook

A marketing plan is a customer's instantiation of a framework for a specific period (typically a quarter). The plan contains: 

- **Goals** — committed outcomes (acquisition, renewal lift, event fill, re-engagement, etc.) with target, baseline, deadline, current pacing. 

- **Programmes** — coherent execution units within a goal. A programme binds an audience definition, one or more tactics (each tied to a journey, campaign, or content brief), a schedule, programme-level KPIs that roll up to goal KPIs, and a status (draft/active/paused/completed). A programme is the unit of activation. 

- **Performance vs target** — computed pacing that becomes the source of plan-health signals. 

One active plan per organisation per period. Older plans are retained for retrospective analysis and seeding the next plan. The plan pins to a framework version at creation so updating the framework does not retroactively change live plans. 

The architecturally important point: the plan is the "why" that organises everything else. AI calls that know the active plan can reference "your Q3 acquisition goal" in their output. Without plan context, AI output is generic. 

### 3.3 Insights as command centre, not reporting

The Insights surface is being redesigned around outcomes rather than data sources. The new IA: 

- **Today** — command centre at `/dashboard/insights`. Prioritised recommendation feed, mini calendar widget, AI palette input. The new front door of the product. 

- **Grow** — acquisition: leads, prospects, funnel velocity, source attribution. 

- **Engage** — channel performance: email, web, events, agents. 

- **Retain** — at-risk members, lapsed cohort, win-back, renewal pipeline. The membership-template work primarily lands here. 

- **Earn** — subscription revenue, renewal revenue, ARPU, LTV, revenue by segment. A board metric for an association currently absent from the product. 

The conceptual move is to separate three things currently tangled and re-fuse them into one primitive:  

- **Insight** — a fact ("412 lapsed members, 23% still open emails") 

- **Recommendation** — what to do ("re-engage them with a nurture journey") 

- **Action** — actually doing it (create audience, build journey, enrol contacts, start sending) 

All three live on a single recommendation card with a preview-and-confirm flow. One-click never sends. Every commit shows the audience preview, the journey or campaign template, projected impact, and writes an audit-trail entry. 

Confidence honesty is non-negotiable: rules-based recommendations are labelled "Counted" (we counted 412 lapsed); AI-generated recommendations are labelled "Suggested" (we think a Tuesday morning send would lift opens). Conflating these erodes trust. 

### 3.4 The trust-building progression

Insights becoming a true command centre — where the AI runs the plan and the marketer intervenes by exception — is a long-term ambition, not the launch target. Trust in AI must be built incrementally. Each stage earns the next. Skipping erodes trust, often unrecoverably. 

| Stage | What AI does | User involvement | Trust ask |
| --- | --- | --- | --- |
| Phase 1 (launch) | Surfaces rules-based recommendations; preview shows exact audience and content | Explicit confirm each time | Low — user controls everything |
| Phase 2 (launch) | Generates content for journeys and programmes; recommendation copy references plan goals; CTAs context-aware | Confirms one-click on content, still previews audience | Medium — trusts content, verifies audience |
| Phase 3 (post-launch) | Routine actions execute without confirm — opted in, audited, undoable. Novel or risky actions still preview | Reviews audit log, sets autonomy per action type | High — trusts judgement on what is routine |
| Phase 4 (future) | Plan executes itself within autonomy limits the user set. User intervenes by exception | Exception handler, not approver | Maximum — earned through phase 2 and 3 |

## 4. The AI architecture model

Four ideas underpin the architecture. Each is described below. 

### 4.1 Composable context blocks

Every AI call assembles its prompt from a stack of reusable context blocks, each encapsulating one dimension of organisational understanding. Features differ in which blocks they compose, not in how the blocks themselves work. 

A context block is a function that takes an `org_id` (and feature-specific arguments where needed) and returns a string fragment formatted for prompt consumption. Blocks may depend on other blocks (audience depends on field-semantics). Blocks must degrade gracefully when their data source is missing or sparse — return empty or a minimal stub, never throw. Blocks must not have side effects — reading and formatting only. 

The nine ten blocks defined today: 

| Block | Source of truth | What it provides |
| --- | --- | --- |
| brand | `brand_settings` table + `color_roles` JSONB | Voice, palette, logo, sender info, role assignments (heading/body/CTA/etc.) |
| org | organizations table | Org name, type, physical address, privacy URL |
| industry | industry_template_configs table | Vertical-specific tone, audience vocabulary, regulatory conventions |
| methodology | marketing_disciplines, goal_types, programmes, tag_labels tables | Active framework content for the org's vertical (disciplines, programmes, KPIs) |
| field-semantics | Field-semantics extension on `contact_field_definitions` | What each contact field means in business terms — the AI-readiness foundation |
| audience | audiences + audience_contacts + field-semantics | Recipient `description` in semantic terms ("active members renewing within 90 days"). For Phase 3+ hyperpersonalisation, also exposes per-recipient depth (`tags`, last activity, lifecycle stage). |
| plan | marketing_plans + plan_goals + plan_programmes | Active plan, current goals and targets, performance vs target |
| insights | Computed benchmarks from cross-org aggregates (privacy-respecting) | Industry-scoped benchmarks ("avg open rate for membership orgs of size X is Y") |
| knowledge | KB tables in Supabase (per-org and curated) | Top-K relevant chunks via vector search for the prompt. Org-scoped customer content (style guide, past campaigns, FAQ, product pages) plus Sweetspot curated content (best practices, playbooks). |
| assets | `content_assets` table (existing infrastructure, AI-tagged on upload) | Available images, videos, audio, files filterable by `tags`, content type, and semantic search. Lets AI reference specific assets in generated output (e.g. selecting the right image for a newsletter section). |

Consequences of this pattern: a new context block becomes available to every feature simultaneously. A change to brand voice ripples through every AI surface in one edit. A model migration touches one file (the client wrapper). A bug in audience reasoning gets fixed once, not nine times.

This is the inverse of the current state, in which each route inlines its own version of "what is this org's tone" and the inlined versions drift out of sync. 

### 4.2 The asset-shape framework

A common mistake in earlier planning was to lump all AI generation routes into one "AI surfaces" bucket. They actually split into three categories, each with different requirements: 

| Shape | What AI produces | Examples |
| --- | --- | --- |
| Branded HTML content | Customer-facing copy in branded HTML emails or pages | email-generate, journey email step content, form-agent confirmation, event-agent confirmation |
| Structural JSON | Schema or graph data the editor renders, brand-light | forms-generate (form schema), journey-generate (steps and edges JSON) |
| Metadata | Short identifiers and descriptions | campaigns-generate (name, type, `description`) |

"Good across features" as the baseline: every content-bearing feature has two creation paths producing the same shape of output — a fully-populated, brand-themed, previewable, testable artifact. Pick template = start from a curated point. Pick AI = describe what you want, AI fills everything in. Both go through brand + industry context. Both are editable inline after creation. 

### 4.3 Agent definition: inbound only

"Agent" is currently overloaded in the codebase. Three things called agents are doing different jobs: 

- **Form-agent and event-agent today** — single-call AI invocations that send a confirmation email on form submission or event registration, then enrol the contact in a journey. Not multi-turn. Not stateful. Single-shot AI calls wearing the wrong name. 

- **Chat agent** — multi-turn conversational handler for inbound messages. State, history, decisions. A genuine agent. 

- **Strategy agent (planned)** — Plan-Build-Launch-Learn loop. Multi-step, tool-using, stateful. A genuine agent. 

The target definition: an agent is a multi-step, conversational, decision-making entity. Single-call email senders are not agents — they are handlers or generators. 

The architectural simplification this implies: form-agent and event-agent today mash creation logic (sending a confirmation email) with runtime logic (handling subsequent replies) into one trigger. The cleanup separates them: 

- **Creation** — moves to the journey. The journey's first step is the confirmation email, AI-generated with brand and event context. Including the .ics attachment as a journey-email feature, not an agent-specific feature. 

- **Runtime** — stays with the agent. The agent handles inbound replies from the registrant, multi-turn, with context of the original registration. 

Why this is cleaner: one source of truth for outgoing emails (journeys), agents become what the word implies (ongoing, conversational), the HTML-building duplication between email-generate / form-agent / event-agent disappears, and the distinction between single-call features and multi-step agents finally has architectural meaning. 

### 4.4 Context-aware generation as a principle

Today the user types CTA URLs by hand when generating AI emails. This is a workaround for missing context. The right pattern: the AI knows what surrounds the email being generated, and uses that knowledge. 

AI generating inside a known context (event journey → use event registration URL; form-followup journey → use the form's redirect URL; recipe-based programme → use the recipe's known CTA): the CTA is pre-filled and the user can override. 

AI generating standalone with no surrounding context (a one-off marketing email composed from scratch): ask for the CTA as today, or skip via the toggle. 

The same principle extends beyond CTAs: subject lines that reference the event title, body copy that names the audience, opening hooks that match the trigger reason — all of that flows from the same idea. The unified email-content component does not just take a prompt; it takes the surrounding context object (which journey, which event, which form, which audience, which plan goal). 

This is what makes "AI-first" feel different from "AI button on every form". 

### 4.5 The unified email-content component

The keystone of the architecture cleanup. A single content-generation pattern, callable from multiple surfaces: 

- **The email editor** — standalone generation as today. 

- **The journey editor** — "Generate content for this email step", with the journey's surrounding context flowing in. 

- **Recommendation action handlers** — when a Today-page card commits to a journey, the journey's emails are populated via this component, with the recommendation context flowing in. 

A single implementation, three consumers. This is what unlocks Phase 2 of the trust-building progression: the moment a customer clicks "Build the campaign" on a recommendation card, the system creates an audience, generates a journey, populates each email step with brand-aware AI content via this component, opens preview, and awaits confirm. The component is the runtime that makes that moment intelligent. 

#### Reusing the existing `AIEmailModal`

The current `AIEmailModal` component (≈300 lines, inline in the email send detail page today) provides most of the UI needed: prompt input, AI-prompt suggestions, CTA toggle with URL and label, generate-review-edit-confirm flow, inline contentEditable preview. It is portable. The coupling that needs to change is the prop contract: today it takes an `emailId` (referring to a `campaign_emails` row) and passes that to `/api/email/generate`. For journey email steps the consumer has no `campaign_emails` row — it has a journey step config. 

The clean refactor: replace `emailId` with a structured context object: 

```typescript
type GenerationContext =
  | { kind: 'campaign_email'; emailId: string }
  | { kind: 'journey_step'; journeyStepId: string;
      journeyId: string; eventId?: string;
      recipeId?: string; audienceId?: string }
  | { kind: 'standalone' }
``` 

The modal passes the context to a unified backend route. The route loads the appropriate context blocks based on the `kind` and feature-specific arguments, composes the prompt, calls the client wrapper, returns the result. The modal renders the result for review and editing the same way it does today. 

Context-aware CTA derivation is a natural extension: when `kind === 'journey_step'` and `eventId` is present, the modal opens with the CTA URL pre-filled from the event's registration_url, with a small note ("Pulled from event — edit if needed"). Same for `recipeId` and `audienceId`. For `standalone`, behaviour matches today: the user provides the CTA or toggles it off. 

### 4.6 Hyperpersonalisation

Hyperpersonalisation — emails or newsletters tailored to the individual recipient — sits on top of the unified email-content component and the asset block. The architecture distinguishes between two flavours, mapped to phases of the trust-building progression: 

| Flavour | What it means |
| --- | --- |
| Segment-level (Phase 2, launch) | AI produces a single email with audience-segment-tailored copy. Different copy for different lifecycle stages or tenure tiers within the same send. Assets are AI-suggested from the library based on context. Marketer reviews in preview before send, sees the segment variants, commits or edits. This is the baseline for "AI-first" feeling different from merge tags. |
| Per-recipient (Phase 3+, post-launch) | AI generates unique content per recipient. Subject line, body copy, asset selection, CTA all consider this specific recipient (lifecycle stage, recent engagement, tag membership, custom field values). The send pipeline composes per-recipient at delivery time rather than from a single rendered template. |

Architecture pieces that support hyperpersonalisation:

- **The audience block**, with per-recipient depth. Today's audience descriptor is segment-level ("active members renewing in 90 days"). For per-recipient generation, the block extends to expose contact-level field values to the AI prompt for each recipient.
- **The assets block.** Provides the AI with the available asset library so it can select images, video, or other media appropriate to each recipient or segment.
- **A per-recipient generation mode at send-time.** Required for Phase 3+. The send pipeline calls the unified email-content component per recipient (or per segment-batch) rather than once for the entire send.

⚠️ **Cost is the constraining factor** for per-recipient generation. A 10,000-contact send generating unique content per recipient is 10,000 AI calls. Pricing-aware patterns must land before Phase 3 ships:

- **Variant-based hybrid** — AI generates N (e.g. 8) variants up front; per-recipient logic at send time picks the best match for each contact based on field values. Bounds AI cost regardless of list size.
- **Per-section variants** — for newsletters, AI generates a small number of variants per section; the recipient gets a personalised mix. More expressive than a single template, far cheaper than full per-recipient generation.
- **Hard daily and per-send caps** — per-org daily AI spend cap, per-send variant count cap, alerting at thresholds. Already flagged as a non-negotiable in the client wrapper section.

Launch target: Phase 2 segment-level hyperpersonalisation, with auto-suggested assets, available wherever the unified email-content component is called. Per-recipient hyperpersonalisation is post-launch and gated on the cost-control patterns landing.

## 5. Current state audit

A precise inventory of what exists today across the AI surface area. This is what the cleanup migrates from. 

### 5.1 AI generation surfaces today

| Route | Asset shape | What it produces |
| --- | --- | --- |
| `/api/email/generate` | Branded HTML content | Full HTML email with brand + role-aware CTA. Fully integrated with `brand_settings`. |
| `/api/agents/form/trigger` | Branded HTML content | AI-written confirmation email on form submission. Reads 4 brand fields. |
| `/api/agents/event/trigger` | Branded HTML content | AI-written event confirmation email with .ics attachment. Reads 4 brand fields. |
| `/api/journey/generate` | Structural JSON | Journey steps + edges. Reads industry vocabulary only. No content in emails. |
| `/api/forms/generate` | Structural JSON | Form schema. Reads industry vocabulary only. No brand awareness. |
| `/api/campaigns/generate` | Metadata | Campaign name, type, `description`. No brand awareness. |
| `/api/journey/create-from-recipe` | Deterministic | Stamps out hardcoded recipe content with brand colour injection. No AI call. |
| `/api/journey/create-from-event` | Deterministic | Stamps out pre/post-event journey templates. No AI call. |
| `/api/forms/create-from-template` | Deterministic | Clones a template into a form. No AI call. |

The earlier migration spec lumped journey-generate, forms-generate, and campaigns-generate together with email-generate as priority migration targets. That conflation is incorrect — they are different asset shapes with different requirements. 

### 5.2 Brand awareness across surfaces today

Each route reads its own narrow slice of `brand_settings`. There is no shared abstraction. The slices drift out of sync. 

| Route | Brand fields read |
| --- | --- |
| `/api/email/generate` | Full palette + voice + `color_roles` (role-aware ✓) |
| `/api/agents/form/trigger` | primary_color, logo_url, brand_voice, body_font |
| `/api/agents/event/trigger` | primary_color, logo_url, brand_voice, body_font (plus agent-level sender overrides) |
| `/api/journey/create-from-recipe` | primary_color, logo_url |
| `/api/journey/create-from-event` | primary_color, logo_url, body_font |
| `/api/forms/create-from-template` | primary_color, background_color, text_color, body_font |
| `/api/forms/generate` | None — reads industry_template_configs only |
| `/api/journey/generate` | None |
| `/api/campaigns/generate` | None |

### 5.3 `ai_usage` table today

AI calls are logged through a helper at `/lib/track-ai-usage.ts`. The columns currently being written: 

- `org_id`
- feature (e.g. "emails", "forms", "journeys", "campaigns") 

- input_tokens, output_tokens, total_tokens 

- cost_usd (calculated at log time using hardcoded Sonnet 4 pricing: $3/M input, $15/M output) 

Columns that the architecture envisions but are not currently written: `user_id`, model, latency_ms, success, `error_message`, created_at. A parallel `usage_summaries` table aggregates by feature and period. 

Coverage is incomplete — not every AI call goes through this helper. The cleanup makes logging a non-optional pass-through. 

### 5.4 What is duplicated, what is missing

Three concrete duplications visible in the codebase: 

- Branded HTML email building is implemented at least three times: email-generate, form-agent trigger, event-agent trigger. Each has a slightly different HTML scaffold with the same intent. They drift. 

- Brand-loading code is implemented per route. Each route knows the subset of `brand_settings` it needs and reads it directly via Supabase. 

- Anthropic SDK invocation is direct in every route. No central place for retries, error handling, model selection, or logging consistency. 

Three things missing entirely: 

- A composable context layer. The `/lib/ai/context/` directory described by the architecture doc does not exist. 

- Field-tagging UI. Required to populate the field-semantics extension on custom fields. Without it, custom-field semantics return sparse data. System-field and template-field semantics will be seeded as content (no UI required) so the layer is partially live from day one. 

- Recommendation-driven action handlers. The "preview-and-confirm" flow from Insights to journey-creation does not exist yet. The Today page command centre is designed but not yet built. 

### 5.5 What is already partially in place

The cleanup does not start from zero. Specific pieces that the migration leans on: 

- **Contact field tier structure.** The contacts settings page already implements three tiers — 11 system fields hardcoded in the page, template fields from `contact_field_definitions` where `is_template_field = true`, custom fields where it is false. This is the structure the field-tagging UI builds on, not something to invent. 

- **Asset library with AI tagging.** `content_assets` table with `description`, `tags`, `ai_analysed`, `content_type`, folder support. Image uploads trigger AI analysis that populates `description` and `tags`. Search by name, `description`, or `tags` works. What is missing: the assets context block exposing this data to AI features outside the asset page. 

- **`AIEmailModal` component.** Inline in the email send detail page today (≈300 lines). Provides the entire generate-review-edit-confirm UI flow with inline contentEditable preview. Portable to other surfaces with a prop-contract change from `emailId` to a structured context object. Migration leverages this directly rather than building a new modal. 

- **Marketing framework v1 (membership).** 12 schema tables with RLS, content seeded, Plan workspace UI end-to-end. The methodology and plan context blocks have data to read from day one. 

- **Brand role assignments.** Live in production. Email-generate is already role-aware. The brand context block leverages this and extends to other features. 

## 6. Target state

The cleanup migrates the system to a clearly-layered architecture under `/lib/ai/`, with single sources of truth for each concern. 

### 6.1 Library structure

Target directory shape: 

```
/lib/ai/
  client.ts            — Wrapped AI SDK: logging, retries, model selection, validation, content filter
  index.ts             — Public entry point
  /prompts/            — Per-feature system prompts as files, not inline in routes
    email-generate.ts
    journey-content.ts
    form-generate.ts
    ...
  /context/            — Composable context blocks
    brand.ts, org.ts, industry.ts, methodology.ts,
    field-semantics.ts, audience.ts, plan.ts, insights.ts,
    knowledge.ts, assets.ts
  /knowledge/          — KB / RAG layer (vector search, embedding generation)
  /agents/             — Multi-step agent loops (chat, strategy, future inbound handlers)
  /schemas/            — zod schemas for structured AI outputs
  /usage/
    log.ts             — Writes to ai_usage after every call
    cost.ts            — Token-and-model → cost calculation
``` 

### 6.2 The client wrapper

Every AI call goes through this wrapper. Direct calls to anthropic.messages.create outside `/lib/ai/client.ts` are a code-review red flag. 

Responsibilities: 

- **Provider abstraction** — generate({ feature, system, messages, model_class }) → { content, usage, metadata }. Internally translates to Anthropic today, Azure AI Foundry post-migration, others if needed. Single point of swap. 

- **Logging** — every call writes to `ai_usage` with `org_id`, `user_id`, feature, model, tokens in/out, cost, latency, success/failure, content hash, consent status, data residency region, trace ID. Non-negotiable: without it there is no cost visibility and no compliance audit trail. 

- **Error handling** — transient failures retry with backoff. Permanent failures degrade gracefully with a feature-appropriate fallback (template-based content instead of AI-generated). Errors must surface, never swallowed. 

- **Model selection** — a single place to decide Sonnet vs Haiku per feature. Premium features (strategy, complex generation) use Sonnet; high-volume or latency-sensitive features (chat suggestions, classification) use Haiku. 

- **Output validation** — when a feature provides a zod schema, the wrapper parses, validates, and retries with corrective prompting on failure. After N (default 2) failures returns a typed error. 

- **Content filtering** — PII detection in outputs, banned-content checks, redaction logging. Baked in from the start because it is far easier than retrofitting. 

### 6.3 Context block contracts

Each block exports a function with this signature: 

```typescript
loadBlockContext(orgId: string, options?: BlockOptions): Promise<BlockContext>
``` 

Where `BlockContext` is a structured object with field accessors and a .toPromptString() method, so consuming routes can either drop the full block into a prompt or pick specific fields they need. This avoids forcing every consumer through one rigid string format. 

Block composition for representative features: 

| Feature | Composes |
| --- | --- |
| email-generate | brand + org + industry + audience + plan + assets + (optional) knowledge |
| journey-content (per email step) | brand + org + industry + journey-context + audience + plan + assets |
| form-generate | brand + org + industry |
| chat agent | brand + org + industry + knowledge + conversation history |
| strategy agent | brand + org + industry + methodology + plan + insights + knowledge |
| insights-agent | org + industry + methodology + plan + insights + knowledge |
| recommendation action | all of the above + signal context + recommendation reasoning |

### 6.4 The unified email-content component

A function callable from any surface that needs to produce a branded HTML email body. Three consumers at launch: the email editor (standalone), the journey editor (per email step), the recommendation action handler. 

The signature aligns with the prop-contract refactor of the existing `AIEmailModal` (see Section 4.5). The function takes a structured generation context and a user-supplied intent, and returns a structured result: 

```typescript
generateBrandedEmail({
  intent,         // user description of what the email should achieve
  context,        // GenerationContext: campaign_email | journey_step | standalone
  cta?,           // optional explicit override; otherwise derived from context
  structuralOptions?,
}): Promise<{
  subject, previewText, body_html,
  suggested_cta, derived_from_context
}>
``` 

Internally the function composes the relevant context blocks based on the `kind`: brand and org for every call, plus journey/event/recipe/audience context where applicable, plus assets when imagery is wanted. It calls the client wrapper, validates output against an `EmailOutputSchema`, returns a structured response the consumer renders. 

The `AIEmailModal` is the canonical consumer for surfaces with a user-facing review step. Headless callers (e.g. recommendation action handlers committing without further review) call the underlying API directly without rendering the modal. 

## 7. Migration plan

Sequenced as 7 PRs over 10-15 weeks. Each PR is independently shippable. The order respects data dependencies: foundation before consumers, context blocks before features that need them, context blocks that depend on field-semantics (audience) after the field-tagging UI lands. 

### 7.1 PR sequence and scope

| PR | Name | Scope | Customer-visible? |
| --- | --- | --- | --- |
| 9 | Foundation + email-generate proof | Build `/lib/ai/client.ts`, `/lib/ai/usage/log.ts`, `/lib/ai/context/`{brand,org,industry}.ts. Migrate `/api/email/generate` as byte-identical proof of pattern. Extend `ai_usage` schema with the missing audit fields. Seed system-field and membership-template-field default `tags` (small content migration). | No — email output identical |
| 10 | Unified email-content component | Extract `AIEmailModal` to a shared component. Refactor prop contract from emailId to `GenerationContext` (campaign_email \| journey_step \| standalone). Build the unified backend route. Wire the modal into the journey editor for per-email-step generation. Includes context-aware CTA derivation from event/form/recipe/audience. | Yes — journey emails can be AI-generated with brand + context |
| 11 | Form/event agent migration | Form-agent and event-agent triggers stop sending confirmation emails. Journeys take over (confirmation as first journey step). Agent triggers narrow to "enrol in journey + open conversation thread for inbound". The HTML-build duplication disappears. | Partial — cleaner architecture, observably the same flow |
| 11p | Field-tagging UI | Customer-facing UI at `/dashboard/settings/ai-ready` for tagging contact fields with semantic labels. Simpler than originally framed because system fields are pre-tagged (universal defaults seeded in PR 9) and template fields are pre-tagged per industry (also seeded in PR 9). UI only requires real interaction for custom fields. Shows readiness percentage prominently. | Yes — admin can tag custom fields; sees mostly-complete state at first visit |
| 12 | Context blocks (methodology, plan, insights, audience, assets) | Build `/lib/ai/context/`{methodology,plan,insights,audience,field-semantics,assets}.ts. Field-semantics consumes the data from PR 11p. Audience depends on field-semantics. Assets exposes the existing `content_assets` infrastructure to AI consumers. Knowledge block generalised from chat-only to all features. | No — substrate |
| 13 | Recommendation action handlers with AI content | Wire the Today-page command centre's "Build the campaign" action to create real audiences, real journeys with AI content via the unified component. Each context block flows in (including assets for image selection). Phase 2 of the trust progression lights up here. Segment-level hyperpersonalisation enabled. | Yes — Phase 2 capability live |
| 14 | Today page + Retain dashboard + ⌘K palette | The customer-facing surfaces of the Insights revamp. Today as command centre. Retain dashboard for membership. ⌘K analytical palette. | Yes — launch-ready surfaces |

### 7.2 Dependencies

| Blocker | What it unblocks |
| --- | --- |
| PR 9 foundation | Every subsequent PR (provides the client wrapper and the first context blocks) |
| Field-tagging UI (11p) | Field-semantics block returning useful data, audience block doing real work, Phase 2 recommendation depth |
| Unified email-content component (PR 10) | Journey content (PR 10 itself), form/event agent migration (PR 11 — agents stop building HTML), recommendation action handlers (PR 13) |
| All context blocks (PR 12) | PR 13 action handlers with rich, contextual AI content |
| PR 13 | Phase 2 of the trust-building progression — visible customer value of the cleanup |

### 7.3 Decision points

Three checkpoints built into the schedule — moments to commit or adjust scope: 

- **End of week 4 (after PR 10)** — is the unified email-content component working well enough to be the keystone? If yes, continue. If struggling, cut journey-content integration to v2 and lean on templates for launch. 

- **End of week 8 (after PR 12)** — is field-tagging UI shipping with users actually tagging? If not, audience block returns sparse data and Phase 2 recommendations lose half their power. Decide: extend two weeks for tagging, or ship Phase 2 without rich audience context. 

- **End of week 10 (after PR 13)** — is the recommendation-to-action flow producing acceptable content? If yes, ship. If output quality is poor, allocate prompt-tuning time before PR 14 surfaces it. 

### 7.4 Risk register

Specific risks worth being eyes-open about: 

- **Pre-production assumption** — the cleanup assumes no live customers using form-agents or event-agents today. Once friendlies are using these features, deprecating the confirmation-email-from-agent path becomes a migration concern, not a delete-and-rebuild. 

- **Field-tagging UI is more UX than engineering** — the screen has to feel manageable for orgs with 40+ contact fields, suggest `tags` reasonably, and not punish someone for not tagging perfectly. Underestimate this and the timeline slips silently. 

- **Prompt tuning post-migration** — every route migrated to the unified component is a moment where output quality might shift. Plan 2-3 days of side-by-side testing per surface after migration. 

- **Weeks 5-8 are invisible** — the dangerous window where motivation dips because nothing customer-facing is moving. Worth communicating to the team that this is expected, not a failure mode. 

- **Customer feedback loop** — if no friendly customer sees Phase 1 features by week 6, Phase 2 is being built in the dark. Worth being deliberate about which friendly sees what, when. 

## 8. Data architecture implications

Concerns specifically relevant to the data architect reviewing this document. Schema implications, multi-tenant isolation, audit, and the field-semantics layer that underpins the AI substrate. 

### 8.1 Schema additions and changes

The cleanup requires these schema changes, listed in roughly the order they need to land: 

| PR | Table | Change | Rationale |
| --- | --- | --- | --- |
| 9 | `ai_usage` | Add columns: `user_id`, model, latency_ms, success, `error_message`, created_at, `prompt_hash`, `output_hash`, `consent_status`, `data_residency_region`, `trace_id`, `content_filter_outcome` | Compliance audit trail, not just cost tracking |
| 11p | `contact_field_definitions` | Already extended in earlier migration with `description`, `field_tags`, `ai_suggested_tags`. UI populates this. | AI-readiness layer becomes useful when populated |
| 12 | `audience_contexts` (new) | Optional materialised view of "audience X means semantically Y" derived from filters + field-semantics. May be view or table. | Performance — audience block called frequently |
| 13 | `recommendation_actions` | Existing table extended: `ai_call_trace_id`, `action_journey_id`, `action_audience_id` | Link recommendation commit to the AI calls it triggered |
| 14 | `ai_recommendations` | Existing table. Add: `confidence_type` ('counted' \| 'suggested'), `source_signal_id`, `plan_goal_id`, `programme_id` | Phase 2 surface shows plan-aware recommendations |

### 8.2 Multi-tenant isolation

Every table has `org_id` and is protected by RLS via the `profiles.id` = `auth.uid()` pattern. AI-related additions follow the same pattern without exception: 

- `ai_usage`: RLS by `org_id`. Service role writes from the client wrapper. 

- Field-semantics extension on `contact_field_definitions`: existing table's RLS covers it. 

- Recommendation tables: RLS by `org_id`. 

- Knowledge tables: existing RLS by `org_id`. Curated content is unscoped but ranked. 

The architecturally important point: AI calls execute server-side and use the service-role Supabase client. The wrapper reads `org_id` from the authenticated session and uses it as the scoping primitive for every context block read. No AI call exists without an `org_id`. 

Cross-org data exposure risk surface area, ranked: 

- **Knowledge retrieval** — vector search must filter by `org_id` for org-scoped content. Curated content is shared. The retrieval function enforces the scope, not the caller. 

- **Benchmarks (insights block)** — by design returns cross-org aggregates. Must enforce a minimum-N threshold (5-10) to prevent identifying a single org. The block returns "n/a" below threshold. 

- **Logs and audit trails** — `ai_usage` is scoped per org. Cross-org reporting (for internal use) goes through a separate service-role view, not the customer-facing query. 

### 8.3 Field-semantics as the data substrate

The most strategically important data layer in the architecture. Without it, AI is generic. With it, AI reasons about renewals, engagement, lifecycle stage in industry-specific business terms. 

The schema (already in production): 

`contact_field_definitions` has columns: `description` (free-text business meaning), `field_tags` (array of semantic `tags` with CHECK constraint to 8 controlled vocabulary values for v1), `ai_suggested_tags` (AI-proposed `tags` awaiting human acceptance). 

The 8-tag vocabulary for membership v1: confirm exact values by querying tag_labels table or reviewing the membership_framework_seed_v1 migration. As B2B and other verticals ship, the vocabulary either grows globally or per-vertical (open product decision). 

#### Field-tagging tier structure

Contact fields split into three tiers in the existing contacts settings UI. Field-tagging applies differently to each: 

| Tier | Tagging approach | Why |
| --- | --- | --- |
| System fields (11, universal) | Pre-tagged with universal defaults, seeded as content in PR 9. Read-only — no per-org override. | System fields have universal meaning (email = identity, timezone = communication preference, last_activity = engagement signal). If an org wants the field to mean something different, that is a custom field, not an override. |
| Template fields (per industry) | Pre-tagged per industry, seeded as content alongside the framework. Read-only — no per-org override. | Template fields are the industry's opinionated take on what matters (member_since = lifecycle indicator, renewal_date = renewal signal). Override-able tagging would defeat the purpose of having an opinionated industry template. |
| Custom fields (org-created) | User tags during onboarding or later. AI suggests tags based on field name, type, and (where available) sample data. User confirms or overrides. | Custom fields are by definition org-specific. The org knows what the field means and can tell the AI. AI suggests to lower the friction of bulk-tagging existing custom fields. |

This tier structure means the "field-tagging UI" (PR 11p) is meaningfully simpler than tagging every field from scratch. A typical org sees:

- **System fields:** pre-tagged, displayed as read-only with system label
- **Template fields:** pre-tagged, displayed as read-only with template label
- **Custom fields:** AI-suggested tags shown, user accepts or overrides

Most orgs land on the screen, see ~80% already tagged, and only engage with their own custom additions. This is what makes "AI-ready in 5 minutes" feasible — most of the work is content-seeded ahead of customer engagement, not customer-effort.

Field-semantics is the gateway to several downstream context blocks:

- **Audience block** needs field-semantics to describe segments in business terms ("renewing within 90 days") rather than column-level filters ("renewal_date < now() + 90 days").
- **Insights block** uses field-semantics to know which fields contain signals vs identifiers vs preferences.
- **Phase 2 recommendation handlers** use field-semantics to write copy that references the right concept ("your renewing members" vs "contacts whose renewal_date is approaching").

#### Asset metadata as a parallel substrate

The `content_assets` table already implements a similar pattern for assets: 

- `description` (AI-generated for images on upload via `/api/content/analyse`)
- `tags` (AI-generated string array)
- `ai_analysed` (flag indicating whether AI has processed)
- `content_type` and `mime_type` (image | audio | video | file, plus specific format) 

No schema changes are required for the assets context block. What is needed is the block itself — exposing this data to the AI prompt for other features (email generation, journey content, newsletter composition). For Phase 2 hyperpersonalisation, the block lets AI propose images that match a recipient segment's interests or the email's topic. 

At launch, image assets are AI-tagged automatically. PDF, video, and audio assets are not yet AI-analysed — they have user-supplied names but no `description` or `tags`. Extending AI analysis to non-image content types is a v2 conversation. 

### 8.4 Audit and observability

The extended `ai_usage` table becomes the single source of truth for everything AI-related. Reporting and per-feature analysis run off this table. No additional logging surface. 

Specific observability requirements: 

- Cost tracking per org per feature per month — supports usage-based pricing if it lands and supports cost-aware feature prioritisation. 

- Latency tracking per feature — needed to identify slow surfaces before customer complaints. 

- Retry tracking — every validation retry logged. Pattern of retries on the same prompt indicates a prompt that needs tuning. 

- Failure tracking — `error_message` column captures the failure mode. Aggregated, this shows which prompts are most fragile. 

- Audit linkage — `trace_id` links a single user action (e.g. "user clicked Build the campaign on recommendation X") to all downstream AI calls (audience `description`, journey generation, per-email-step content). Required for the AI Act's "explain why this was done" obligation if any output is challenged. 

## 9. Compliance and infrastructure forward look

Decisions taken now must not preclude meeting enterprise compliance standards or migrating to Azure infrastructure post-launch. 

### 9.1 The compliance standards stack

| Standard | Scope | Applies at launch? |
| --- | --- | --- |
| GDPR (UK + EU) | Lawful basis for processing, data subject rights, breach notification, DPA. Already mandatory for UK-based product serving EU customers. | Yes — mandatory |
| SOC 2 Type 2 | Security, availability, processing integrity, confidentiality, privacy controls. The gateway certification for enterprise sales. | Path to within 12 months — typical enterprise customer ask |
| EU AI Act | Transparency obligations for "limited risk" AI (which the recommendation engine likely is); higher obligations if anything classified as "high risk". | Transparency obligations apply on phased dates — first wave in 2025-2026 |
| ISO 42001 | AI management system standard. New (2023). Becoming enterprise ask in 2026. | Path to within 18 months |
| HIPAA / health data | If any health-adjacent data lands. | Not anticipated for membership orgs |

### 9.2 Infrastructure migration trajectory

| From | To | Cleanup design implication |
| --- | --- | --- |
| GitHub | GitHub Enterprise | None architecturally — ops migration |
| Supabase | Postgres on Azure | RLS and schema portable. Auth, storage, edge functions need replacements. Schema migrations should be vendor-neutral SQL where possible. |
| Vercel | Azure App Service | Next.js portable. Inngest stays SaaS or moves to Azure Functions. Environment-variable patterns should not assume Vercel specifics. |
| Anthropic direct API | Azure AI Foundry | The client wrapper IS the migration interface. Designed for provider swap from the start. |

The cleanup work described in section 7 does not attempt the infrastructure migration. It designs for it. Specifically:

- **Client wrapper as provider abstraction** — not "the Anthropic SDK wrapper". The internal contract is provider-agnostic. Cost translation, content filtering, retry behaviour, validation all happen at this layer regardless of provider.
- **Schema migrations as vendor-neutral SQL** — avoid Supabase-specific syntax where possible. Stick to ANSI Postgres.
- **Environment variables** — separate AI_PROVIDER (anthropic | azure_foundry | etc.), AI_REGION, AI_MODEL_DEFAULT, etc. Configuration-driven, not coded.
- **`ai_usage` `data_residency_region` column** — even if today every call goes to anthropic.com, log the region from day one. When migration happens the column is already there. 

### 9.3 Specifically about Azure AI Foundry

Azure AI Foundry hosts Anthropic models alongside OpenAI, Mistral, and others through a single Azure-native API surface. The expected benefits for Sweetspot: 

- Data residency in EU regions if required by customer 

- Enterprise audit and compliance features integrated with the rest of Azure 

- Single billing surface with the rest of Azure consumption 

- Easier path to procurement for Azure-standard enterprise customers 

Known friction worth checking against current requirements: 

- Model availability lag — new Anthropic model versions typically appear on AI Foundry weeks after the direct API. The launch should not depend on a specific model that is only on direct Anthropic. 

- Feature parity gaps — prompt caching, computer use, and other features may not arrive on AI Foundry on day one. Worth confirming current versions of Claude on AI Foundry support the same generation patterns used today. 

- Pricing — Azure pricing differs from Anthropic direct, sometimes meaningfully. The cost calculation in `/lib/ai/usage/cost.ts` must support provider-specific pricing tables. 

Recommended path: launch on Anthropic direct with the wrapper in place. Migrate to Azure AI Foundry as a v1.5 PR once the launch is stable and the feature parity has been confirmed. 

### 9.4 Content filtering and PII

Output content filtering is a compliance-relevant design choice, not a nice-to-have. Requirements: 

- **PII detection** — outputs scanned for accidental disclosure of email addresses, phone numbers, or other PII not present in the input. Patterns block or flag depending on severity. 

- **Banned-content filters** — basic profanity and regulated-topic detection. Customer-configurable thresholds. 

- **Redaction logging** — when content is blocked or modified, log what was filtered and why. Required for the AI Act's explainability obligations. 

The architectural decision: filtering happens at the client wrapper, after the model returns and before content is delivered to the consuming route. Centralised in one place, auditable, swappable as filter providers improve. 

## 10. Open questions

Decisions that affect the API shape or data model and should be settled up front. Some are technical (data architect can decide). Some are product-strategic (product decides). Some are commercial (customer or partner conversations decide). 

### 10.1 Architecture-level

- **Client wrapper scope.** Minimal version (logging + retries + per-feature model selection) or full version (also validation + content filter + cost calculation) at PR 9? Recommendation: minimal for PR 9, expand in PR 11 when /schemas/ lands. 

- **Prompt extraction strategy.** Extract prompts to `/lib/ai/prompts/` as exported strings/functions, or compose context blocks into routes in-place? Recommendation: extract — strongly. Inline prompts make every change a full-file rewrite. 

- **Context block return shape.** String fragment or structured object with formatting methods? Recommendation: structured object with .toPromptString() and individual getters. Lets routes pick what they need. 

- **`ai_usage` column finalisation.** Confirm the full target column set with the data architect before PR 9 schema migration lands. 

### 10.2 Brand and content

- **Per-template brand-role overrides.** "This specific newsletter uses accent for CTA, not secondary." Stored on `campaign_emails` or template? Defer to v2 or include in PR 10? Recommendation: defer. 

- **Chat brand inclusion strategy.** Multi-turn chat — brand in system message only, or re-injected per turn? Recommendation: system message only with explicit instruction the brand applies to all responses. Cheaper, simpler. 

- **Agent brand depth.** Once agents are inbound-only, do they receive the full brand block or a thin slice? Recommendation: full block by default, dial back per-agent if over-styling emerges. 

### 10.3 Data and context

- **Field-tagging UI v1 scope.** Resolved: separate page at `/dashboard/settings/ai-ready` (not inline on contacts settings). Three-tier display: system fields pre-tagged read-only, template fields pre-tagged read-only, custom fields interactive with AI-suggested `tags`. Multi-tag capability stays in schema but UI defaults to single-tag per field; revisit when real examples surface needing multiple. 

- **Tag vocabulary expansion.** As B2B / non_profit / wealth_management ship, the 8-tag vocabulary grows. Global-with-vertical-overrides or fully per-vertical? Product decision. 

- **KB ingestion UX.** How does the customer add content to the org-scoped KB? File upload, URL scrape ("import our website"), manual notes, bulk paste? Each is a different surface and shapes onboarding. Worth a dedicated planning conversation. 

- **KB content types at launch.** Which formats are supported in v1? Docs, web pages, plain text, all of the above? 

- **Curated knowledge content sourcing.** Who authors Sweetspot's editorial KB layer (best practices, regulatory guidance, industry playbooks)? Internal team, partner-sourced, or AI-generated and human-reviewed? Product decision. 

- **Always-on vs selective KB retrieval.** Always-on is simpler but token-expensive. Selective requires a classifier to decide when KB is relevant. Recommendation: start always-on, optimise after seeing token costs. 

- **Asset auto-suggestion in AI generation.** When generating an email or newsletter, should the AI auto-propose assets from the library, or wait for the user to invite asset selection? Affects UX. Default proposal: auto-suggest in Phase 2, marketer reviews in preview before commit. 

- **Non-image asset AI analysis.** Today only images get AI-generated descriptions and `tags` on upload. Should PDFs, videos, and audio files also be analysed (text extraction for PDFs, transcript for audio/video)? v2 conversation. 

### 10.4 Compliance and infrastructure

- **SOC 2 readiness timeline.** What is the target audit window? This affects how much of the audit infrastructure (logs, controls evidence, access reviews) needs to be in place at launch vs immediately post-launch. 

- **EU AI Act risk classification.** Sweetspot's recommendation engine and Phase 2 content generation are most likely "limited risk" with transparency obligations. Worth a legal review to confirm before launch and to scope what disclosure UX is required. 

- **Data residency at launch.** Do early customers require EU-region processing for AI calls? If yes, Azure AI Foundry migration moves to launch dependency. If no, post-launch is fine. 

- **Cost controls.** Per-org daily spend cap, per-feature concurrency limit, alerting threshold. Easy to add now, painful to retrofit after the first surprise invoice. 

## 11. Glossary

Terms used throughout this document, in alphabetical order. Many are Sweetspot-specific and not standard industry vocabulary. 

**Asset context block.** The `/lib/ai/context/assets.ts` block that exposes the `content_assets` library to AI features. Given an org and a context, returns relevant assets (images, video, audio, files) with their descriptions, `tags`, and URLs so AI can reference specific assets in generated output. Backed by existing AI-tagging infrastructure for image uploads. 

**Agent.** A multi-step, conversational, decision-making entity. Examples: chat agent (handles inbound messages), strategy agent (Plan-Build-Launch-Learn loop). Single-call AI invocations are handlers or generators, not agents. 

**Asset shape.** The category of output an AI route produces. Three shapes: branded HTML content, structural JSON, metadata. Different shapes have different brand-awareness requirements and unification priorities. 

**Brand role.** One of 8 named semantic roles (heading, body, link, cta_bg, cta_text, canvas, callout_bg, divider) mapped to either a palette token or a custom hex. Defined in `brand_settings`.`color_roles` JSONB. 

**Command centre.** The Today page as the new front door of Insights. Prioritised recommendation cards, mini calendar, AI palette. The long-term vision: AI runs the plan, marketer intervenes by exception (Phase 4 of trust progression). 

**Composable context block.** A function returning a structured object that AI features compose into their prompts. One block per dimension of organisational understanding (brand, org, industry, methodology, field-semantics, audience, plan, insights, knowledge). 

**Context-aware generation.** AI generation that receives a surrounding-context object (which journey, which event, which audience, which plan goal) and uses it to pre-fill CTAs, name audiences, reference goals, and adapt copy. 

**Field-semantics.** Tags on contact field definitions that describe what each field means in business terms (renewal signal, engagement signal, lifecycle indicator, etc.). The AI-readiness foundation. 

**Friendly.** A pre-launch customer working closely with the team, providing feedback, before the product is generally available. Distinct from a "paying customer" or "prospect". 

**Goal.** A declared outcome in a marketing plan with target, baseline, deadline, current pacing. Types are framework-driven per industry. 

**Handler.** A single-call AI invocation that responds to a runtime event (form submitted, event registered, inbound reply received). Not multi-step. Today's form-agent and event-agent are handlers misnamed as agents. 

**Hyperpersonalisation, segment-level.** AI produces a single email with multiple audience-segment-tailored variants. Different copy for different lifecycle stages or tenure tiers within the same send. Phase 2, launch target. 

**Hyperpersonalisation, per-recipient.** AI generates unique content per individual recipient — subject, body, assets, CTA all consider that specific contact. Send pipeline composes per-recipient at delivery time. Phase 3+, gated on cost-control patterns. Variant-based hybrid (AI generates N variants, per-recipient logic picks one) is the typical pattern to bound cost. 

**Field-tagging tiers.** Contact fields split into three tiers: system fields (11, universal, hardcoded, pre-tagged read-only), template fields (industry-seeded, pre-tagged read-only), and custom fields (org-created, user `tags` with AI suggestions). Tagging UI is meaningfully simpler than tagging every field from scratch — most fields come pre-tagged. 

**Industry template.** The vertical an organisation is bound to at sign-up (membership, b2b, non_profit, wealth_management). Drives vocabulary, methodology, benchmarks, and defaults. 

**Marketing framework.** Curated, methodology-backed content per industry. Describes how marketing strategy gets done in a vertical. Built on Sense-Decide-Do-Sustain structure. 

**Marketing plan.** A customer's instantiation of a framework for a specific period (typically a quarter). Contains goals, programmes, audience definitions, KPIs, status. 

**Phase 1 / Phase 2.** Trust-building stages. Phase 1: rules-based recommendations, explicit confirm. Phase 2: AI-generated content with confirm, recommendations reference plan goals. Both target launch. 

**Preview-and-confirm.** The non-negotiable design rule for the command centre: one-click never sends. Every action shows audience preview, content preview, projected impact, audit-trail entry on commit. 

**Programme.** A coherent execution unit within a plan goal. Binds an audience, tactics (journey/campaign/content brief), schedule, KPIs, status. The unit of activation. 

**Recommendation card.** The fused primitive on the Today page. Combines insight + recommendation + action in a single card. "Counted" if rules-based, "Suggested" if AI-generated. 

**Unified email-content component.** The single function `generateBrandedEmail`() (and its UI wrapper, the `AIEmailModal`) that any feature needing a branded HTML email body calls. Three consumers at launch: email editor (standalone), journey editor (per email step), recommendation action handler. The `AIEmailModal` exists today inline in the email send detail page; PR 10 extracts it, refactors its prop contract from emailId to a `GenerationContext` object, and adds the unified backend route. 