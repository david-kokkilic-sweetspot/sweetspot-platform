---
title: Industry System — Architect Brief
document: Product brief for the data architect
---

```
Industry System — architect brief
```

Product brief for the data architect designing sweetspot’s industry template engine.

#### Document status

- Author: Stephi (product)
- Audience: data architect designing the Industry System
- This is a brief, not a PRD. You’ll write the PRD; this captures product intent, current state, launch bar, and the questions I need your input on.
- Prerequisite reading: Glossary and Core Concepts (sections 1, 3, 6, 7 especially)
## 1. What I’m asking you to design

sweetspot’s Industry System is the engine that lets one organisation’s workspace feel native to their sector while another organisation’s workspace feels native to a completely different one. Same product, different shape per industry. At launch we ship one industry (membership organisations); over time we add more (B2B, wealth management, non-profit, etc.).

The system spans several layers: data model, content seeding, vocabulary mappings, AI prompt context, and migration tooling. It is foundational to sweetspot’s positioning as “industry-shaped marketing” rather than “generic marketing tool with industry templates bolted on.”

Your job is to design this engine end to end: the data model, the seeding strategy, the vocabulary system, the AI integration shape, and the migration tooling. You also own the resulting PRD; this brief is the input.

## 2. Why industry matters — the product strategy

The reason industry is foundational, not cosmetic:

- Customers expect their tools to speak their language. A membership organisation says “members” not “customers.” A wealth firm says “clients” not “contacts.” Generic copy reads as someone-else’s product, however polished.
- AI output quality depends on context. Without industry vocabulary, AI-generated emails produce bland, sector-neutral text or hallucinate a sector from the org’s name. With industry vocabulary, the same AI produces copy that sounds like an industry insider wrote it.
- Seeded content is the difference between “useful in 5 minutes” and “useful after 5 weeks of setup.” An industry template lands a customer with the right fields, segments, journeys, forms, and email templates already in place. Onboarding becomes review-and-edit, not build-from-scratch.
- Benchmarks need industry scope to be useful. “Your open rate vs other membership orgs of your size” is meaningful; “your open rate vs all sweetspot customers” is not.
**Note: Industry is parallel to brand, not downstream of it.**

Brand is org-specific identity (voice, colours, logo, sender info). Industry is industry-shaped advice (vocabulary, methodology, benchmarks, seeded content). Both feed the AI context layer; neither owns the other. A membership org with a playful brand voice and a membership org with a formal brand voice share an industry template but have different brand kits.

## 3. The central architectural ask (aspiration)

**Note: Adding a new industry template should require no application code changes.**

Aspiration: product creates content (vocabulary mappings, template field definitions, seed segments, seed journeys, seed forms, AI prompt fragments). The engine consumes that content. A new template ships through a content migration, not an engineering deploy.

This is the design goal that distinguishes a content-driven engine from a code-driven one. The content-driven version costs more upfront and pays back many times over.

I’m framing this as aspiration, not requirement, because you may identify surfaces where pure content-driven is not realistic for launch. If so, the request is: name those surfaces explicitly, describe what makes them code-driven, estimate the cost of converting them post-launch, and we’ll make a deliberate trade-off together.

What I want to avoid is a quietly half-content-driven engine where adding a template still costs engineering hours but no one realises until the second template is being built.

This is the single most important architectural conversation between you and me. Most other decisions follow from how we land this one.

## 4. What exists today

A code-verified inventory of what is partially built. Each item should be read by you in the actual code before being treated as truth.

### 4.1 Settings layer (substantially done)

- Settings page captures template_key on the organizations table. Code at /app/dashboard/settings/organisation/page.tsx.
- Two enum values shipped today: membership_org and b2b. Legacy column industry_template fallback is implemented.
- Lock rule enforced: template_key only switchable while contacts.count = 0 AND journeys.count = 0.
- Full coverage of the settings page in PRD_Organisation_Settings.docx (separate handover doc).
### 4.2 AI context layer (partial, code-driven)

- Architecture envisions an industry context block at /lib/ai/context/industry.ts that reads from an industry_template_configs table.
- In practice, the email-generate route currently inlines industry vocabulary as ctx.orgType + ctx.memberNouns rather than reading from a vocabulary table. This is the canonical example of the gap between aspiration and reality. Verify in /app/api/email/generate/.
- Other AI routes (form-agent, event-agent, journey/create-from-*) have similar inlining patterns. Worth a code audit before designing the replacement.
### 4.3 Membership content (substantially seeded)

- Marketing framework v1 for membership is seeded: 12 schema tables with RLS, 5 disciplines, 5 goal types, 13 programmes, 8 tag labels.
- Plan workspace UI live end-to-end for membership orgs (creation, goals, programmes, performance).
- Membership template fields are seeded with pre-tagged field-semantics (member_since, renewal_date, lifecycle indicators).
- This is real content shipped via migration files. It will need to either become the reference seed for the new content-driven engine, or be re-imported into the new system.
### 4.4 Field semantics (partial)

- contact_field_definitions has columns: description, field_tags (with CHECK constraint to 8 controlled tag values for v1), ai_suggested_tags.
- Three-tier field structure exists: system fields (universal, pre-tagged), template fields (industry-seeded, pre-tagged), custom fields (org-created, user-tagged with AI suggestions).
- Field-tagging UI (at /dashboard/settings/ai-ready per the architecture doc) is on the launch backlog but not yet built.
### 4.5 Brand role assignments (done, parallel concern)

- 8-role system live (heading, body, link, cta_bg, cta_text, canvas, callout_bg, divider).
- brand_settings.color_roles JSONB column populated, role-aware email generation working in /api/email/generate.
- Mention here because brand and industry both feed the AI context layer and are easily conflated. They are parallel.
### 4.6 Benchmarks and insights (not for launch)

- Architecture envisions industry-scoped benchmarks (avg open rate for membership orgs of size X) computed from cross-org aggregates with a minimum-N privacy threshold.
- None of this is built. Insights surface for membership at launch will use seeded recommendations and customer’s own data, not cross-org benchmarks.
## 5. Launch bar

At go-live we ship one industry: membership organisations. The engine must be designed so that adding the second industry (likely B2B or wealth_management) after launch is product work, not engineering work.

### 5.1 What must work for membership at launch

| Surface | What must be true at launch | Current state |
| --- | --- | --- |
| Settings | Customer picks membership_org at signup; locked once data exists; switchable only by support thereafter. | Settings page mostly built (see Org Settings PRD). |
| Vocabulary | UI labels and AI output use membership vocabulary (members, renewal, etc.). | Partial. Some inlined, some hardcoded. |
| Template fields | Membership-specific fields (member_since, renewal_date, membership_tier) pre-seeded on each new membership workspace, pre-tagged with field-semantics. | Substantially seeded for membership. |
| Seed segments | A starter set of membership segments (active, renewing in 90 days, lapsed) available immediately. | Verify in code. |
| Seed journeys | Welcome onboarding, renewal nurture, re-engagement journeys exist as templates customers can activate. | Verify in code; partly tied to recipe and create-from-* routes. |
| Seed forms | Membership signup form available in the form library. | Verify in code. |
| Seed email templates | Newsletter, event invite, announcement templates work with membership voice. | Partial. Email templates spec exists (post-launch). |
| AI prompts | Industry context block fed into every relevant AI route, sourced from a single place (not inlined per-route). | Aspirational; current state is per-route inline. |
| Migration tooling | When a new template is added, existing workspaces remain stable; new workspaces can be seeded. | Not built. |

### 5.2 What does NOT need to work for membership at launch

- Cross-org benchmarks scoped by industry. Phase 2.
- Self-service template switching after data exists. Support-only path.
- Per-template recommendation engines tuned to industry signals. Phase 2.
- Industry-specific compliance overlays (e.g. FINRA for wealth management). Phase 2 and tied to the wealth template specifically.
## 6. Strategic constraints

Things that are fixed and you cannot change without escalating to product.

### 6.1 Naming and schema

- The canonical column is organizations.template_key (text). Legacy column industry_template exists and the code reads template_key with industry_template fallback. Plan a migration to retire industry_template.
- Valid template_key values at launch: membership_org. Phase 2 values to accommodate: b2b, wealth_management, non_profit. The schema must allow extension without ALTER COLUMN.
- template_key may be null when workspace_model = contacts_only (current code) but this is under review (open question Q3 in Org Settings PRD). Confirm with product before designing around it.
- workspace_model and template_key are independent concepts. Do not couple them. See Glossary section 2.
### 6.2 Multi-tenant isolation

- Industry template content (seed segments, seed journeys, etc.) is shared across organisations — not org-scoped. The content is curated by sweetspot.
- But the materialised seeds in a customer’s workspace ARE org-scoped. When a membership org signs up, the seed content is copied into their workspace with their org_id; thereafter it is their data.
- This split (shared template content vs org-scoped materialised seeds) is foundational. Get it right.
- Cross-org benchmark queries (Phase 2) must enforce minimum-N to prevent identifying a single org. Standard pattern.
### 6.3 Immutability

- template_key is effectively immutable once data exists in a workspace. UI locks; server-side save enforces. Internal support tooling is the only path to override.
- This means migrations that change a template’s shape must be backward-compatible with existing customer data. You cannot rename a template field column after it ships if a customer’s journey or segment depends on it.
- This constraint shapes the engine more than any other. Design for additive-only template evolution.
### 6.4 What is NOT a constraint

- You are free to design the industry_template_configs table (or whatever you call it) however makes sense. The current code does not yet read from it consistently.
- You can deprecate or rename the inline ctx.orgType / ctx.memberNouns pattern. It is gap, not contract.
- You can pick the storage format for content (YAML, JSON, database rows, CMS) as long as it supports the aspiration in section 3.
- You can propose changes to how AI prompts are composed if the current pattern blocks the design. Coordinate with whoever owns the AI architecture.
## 7. Design dimensions I’d like your view on

These are the questions I need your input on. Each shapes the engine in a different direction. No right answer; I want your honest take given the constraints.

**7.1 Where does template content live?**

Options I can see:

- (a) Database tables: industry_templates, industry_template_fields, industry_template_segments, industry_template_journeys, etc. Content edited via SQL migrations or an internal admin UI.
- (b) YAML/JSON in the repo: each template is a folder of files. Content edited in code reviews. Compiled into seed data at deploy time.
- (c) Headless CMS (Sanity, Contentful): content edited by product without an engineering deploy. Probably overkill for the launch but interesting for v2.
- (d) Hybrid: small canonical metadata (name, key, supported features) in DB; bulk content (fields, segments, journeys) in YAML.
Cost factor: editability by product without engineering involvement is the design goal but engineering ergonomics matter too. What’s your lean given the team you’re joining?

**7.2 How is vocabulary mapped?**

AI prompts need industry vocabulary. Today: inlined per-route. Tomorrow: where does the AI route look up “what does this org call their audience?”

- (a) A vocabulary table with abstract keys (audience.singular, audience.plural, lifecycle.start, lifecycle.end) and per-template values.
- (b) Prompt fragments per template, composed into the system prompt by the AI context layer.
- (c) Both: structured vocabulary for UI labels, prompt fragments for AI.
This decision feeds the AI context block design at /lib/ai/context/industry.ts. Worth designing in concert with whoever owns the AI architecture.

**7.3 How are seeds applied?**

When a new membership_org signs up, the seed content must be materialised into their workspace. When a new template ships, existing workspaces on other templates must not be affected. Options:

- (a) Application-layer seed: a service runs on org creation and inserts the seed content as rows. Easy to reason about; some code per surface.
- (b) Database-layer seed: stored procedures or migration scripts run on org creation. Tighter to the data; harder to test.
- (c) Lazy seed: content is materialised the first time the customer touches a surface. Defers cost; adds a “first-touch” hidden state.
My lean is (a) but you may have a strong view from Azure conventions.

**7.4 How do template updates propagate to existing customers?**

Three months after launch, you improve the membership welcome journey. Existing membership customers have already materialised the old version into their workspaces. Do they get the update?

- (a) No — once materialised, content belongs to the customer. Updates only affect new orgs.
- (b) Yes, opt-in — customers see a notification: “The membership journey has been updated; preview and apply?”
- (c) Yes, automatic — only if the customer hasn’t modified the content; otherwise no.
My lean is (a) for launch (simplest), (b) for v2 (better UX). What’s yours?

**7.5 How is migration to a new template handled?**

This is the question I care about most because it shapes whether “temporary template” is a real possibility (see section 8).

Scenario: a customer is on membership_org. Six months in, we ship wealth_management. The customer asks to switch. What does that involve?

- Renaming template_key from membership_org to wealth_management.
- Migrating their template fields (member_since on a wealth org becomes client_since?).
- Migrating their segments (“active members” becomes what?).
- Migrating their journeys (renewal nurture means a different cadence in wealth).
- Updating AI vocabulary in any drafts in progress.
My honest take: full automatic migration is not realistic. Some manual remapping is unavoidable. The engine should support a guided migration (an internal tool) rather than an automatic one. Your view?

**7.6 How do we test that the engine is really content-driven?**

The simplest acceptance test: “can a non-engineer add a new template?” Concretely, the launch readiness test would be: someone in product (not the architect) adds a stub template called test_industry with three template fields, two seed segments, one seed journey, and a vocabulary mapping. The new template appears in the settings picker and a new org created on it is materially different from a membership org. Zero engineering hours.

If this test passes, the aspiration in section 3 is met. If it doesn’t, we know exactly what needs more work.

## 8. Out of scope for launch

- Additional templates beyond membership. Phase 2 priorities: B2B, wealth management, non-profit. Schema must accommodate them; content seeds do not need to exist at launch.
- “Temporary/stopgap” generic template for non-membership customers. Currently under product discussion; if it ships it ships as Phase 2 once the architect-led engine is in place.
- Cross-org benchmarks scoped by industry.
- Self-service template switching on a populated workspace.
- CMS-based content editing (option 7.1c). Architect can recommend for v2.
- Automatic propagation of template content updates to existing customers (section 7.4).
- Customer-specific templates (“we built a custom template just for this strategic account”). Phase 2+.
## 9. What the PRD you write should cover

Once you’ve absorbed this brief and looked at the code, write the Industry System PRD following the structure in PRD_Template.docx (separate handover doc). At minimum it should cover:

- Feature description, glossary references, status summary.
- Data model: tables, columns, relationships, indexes, multi-tenant isolation per table.
- Content layer: how templates are defined, where they live, how they’re edited.
- Seeding: how new orgs get their content; how template updates propagate (if at all).
- Vocabulary system: how AI and UI access industry vocabulary.
- AI integration: how the industry context block composes into prompts.
- Migration tooling: support staff workflow for switching a customer’s template after data exists.
- Phase 2 considerations: extensibility, the temporary-template question, benchmarks.
- Stack-specific risks for the Angular + Azure rebuild (see PRD template section 15).
## 10. How we’ll work together

- This brief is your starting point. I expect pushback on the aspiration in section 3 (some of it will be “this isn’t achievable in the timeline”) and pushback on individual design decisions. That’s the conversation.
- First milestone: an outline of the PRD with your initial design direction. Should take a week of part-time work or 2-3 days of focused work.
- We sync on the outline before you write the full PRD. That’s where I push back on you.
- Full PRD draft after the outline is agreed. Probably 25-35 pages.
- Review with the lead engineer of the handover team before final hand-off. They have to build it; their pushback matters.
## 11. Reference materials

- Glossary and Core Concepts (handover doc).
- PRD Template (handover doc).
- PRD_Organisation_Settings (handover doc) — covers the settings layer of industry.
- Architecture doc: sweetspot-ai-architecture-strategy-v2 (in project).
- AI System Architecture doc (in project) — covers context blocks broadly.
- Repo: github.com/sweetspot2026/orbit
- Relevant files in the code: /app/api/email/generate/, /lib/ai/context/, the migration files seeding membership v1 framework content.
## 12. Closing

This is one of the most strategically important pieces of sweetspot. Done well, it positions the product to scale to many industries with minimal engineering capacity per new industry. Done half-well, it creates expensive maintenance debt and limits how fast we can address non-membership demand.

I trust your design instincts here. The brief gives you the product context, the constraints, and the questions I want your view on. The shape of the engine is yours to design.

Read the glossary first. Then this. Then the Org Settings PRD. Then the code. Then come back to me with the questions in section 7 and your initial direction. We sync from there.
