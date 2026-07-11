# AI Core Status & Email Feature — Meeting Script

**Date:** 2026-07-02
**Meeting:** _"Hello all, Let's meet and discuss the current status of AI core, and next steps for Email feature. Thanks Vishnu"_
**Owner (this brief):** DEOP
**Format:** ~30–40 min, screen-share + walkthrough
**Repos:** code = `Click-Development/sweetspot` · planning = `david-kokkilic-sweetspot/sweetspot-platform`

---

## TL;DR

1. **AI core substrate (SSP.AI) is production-ready.** Provider-agnostic pipeline, 9 context blocks, Azure Foundry adapter + embeddings, spend caps, content filtering, usage logging — **334 unit tests green.** Epic 1 in review (PR #111).
2. **Two AI features already run on the substrate:** email generation and form generation — proving the architecture works end-to-end.
3. **Email backend is delivered.** DEOP's scope is done (Stories 2.1 + 2.3). Next step is Click's: Story 2.2 (Angular `AIEmailModal` refactor + journey editor wire-up).
4. **June-10 conflict-report gaps are all closed.**
5. **Decisions needed:** (a) Foundry launch vs post-launch, (b) email refinement + import scope.

---

# STEP-BY-STEP MEETING SCRIPT

---

## Step 1 — Opening & Agenda (2 min)

> "Thanks Vishnu. Two topics today: **(1)** where the AI core stands — what we built, what's proven, and what's left; **(2)** email feature — what's delivered, what's next, and who does what. I'll show real code, real JSON, and real test results."

---

## Step 2 — AI Core Architecture Overview (5 min)

📂 **Open:** `src/backend/Core/AI/README.md`

> "We built a single, provider-agnostic AI layer called SSP.AI. Every AI feature in the platform — email, forms, future chat agent — calls through the same pipeline. No per-feature duplication."

**Show the pipeline diagram:**

```
caller → IAiClient / ITenantAiClient
  → [1] Tenant isolation (AccountId + UserId auto-injected)
  → [2] Model resolution (Sonnet / Haiku / Opus → deployment names)
  → [3] Spend-cap check (blocks BEFORE any provider cost)
  → [4] Content filtering — input (PII, banned terms)
  → [5] Provider call (Azure Foundry primary; Anthropic legacy)
  → [6] Retry with exponential backoff (Polly v8)
  → [7] Content filtering — output
  → [8] Schema validation + corrective-prompt retry
  → [9] Fallback (per-feature template fallbacks)
  → [10] Usage + cost + latency logged to ai_usage
```

> "Key point: switching from Anthropic to Azure Foundry required zero changes in any feature code. The pipeline handles everything."

**Show the provider config:**

```json
{
  "Ai": {
    "Provider": "azure-foundry",
    "BaseUrl": "<Foundry endpoint>",
    "Models": {
      "Sonnet": "foundry-sonnet-deployment",
      "Haiku": "foundry-haiku-deployment",
      "Opus": "foundry-opus-deployment"
    },
    "Embeddings": {
      "Provider": "azure-foundry",
      "ModelDeployment": "foundry-text-embedding-3-large",
      "Dimensions": 3072,
      "BatchSize": 96
    },
    "CostTable": {
      "foundry-sonnet-deployment": { "InputPer1k": 0.003, "OutputPer1k": 0.015 },
      "foundry-haiku-deployment":  { "InputPer1k": 0.00025, "OutputPer1k": 0.00125 },
      "foundry-opus-deployment":   { "InputPer1k": 0.015, "OutputPer1k": 0.075 }
    }
  }
}
```

---

## Step 3 — Context Blocks: The Composable Knowledge Layer (5 min)

📂 **Open:** `SSP.AI/Context/Brand/BrandContext.cs` → `SSP.AI/Context/Org/OrgContext.cs`

> "Every AI feature is context-aware through composable blocks. Each block loads tenant data, formats it for the prompt, and degrades gracefully if the data is missing. We shipped 9 blocks — the full launch catalogue."

**The 9-block catalogue:**

| # | Block | Source Table | What It Provides |
|---|-------|-------------|------------------|
| 1 | **Brand** | `brand_settings` | Voice, tone tags, values, tagline (tonal only — colours/fonts never go to the LLM) |
| 2 | **Org** | `accounts` | Organisation name, industry, address, locale, timezone |
| 3 | **Industry** | `industry_template_configs` | Domain vocabulary, recurring-value labels |
| 4 | **Profile** | `organisation_profile` + `voice_samples` | Audience description, tier names, up to 5 voice exemplars |
| 5 | **Knowledge** | `kb_documents` + `kb_chunks` | Customer-uploaded docs, chunked & embedded via Foundry `text-embedding-3-large` (3072 dims), pgvector similarity search |
| 6 | **Field Semantics** | `contact_field_definitions` | 8 semantic labels so AI reasons about CRM fields |
| 7 | **Event** | event data | Event-specific context for event marketing features |
| 8 | **Brief** | campaign brief data | Campaign brief context for content generation |
| 9 | **Contact Fields** | contact field definitions | Available merge tags and their meanings |

> "Each block implements `IContextBlock<TContext>`. The contract is: load the data, return a typed context with `Exists` flag and `ToPromptString()`. Missing data? Returns an empty stub — never crashes the AI call."

**Show how features compose different blocks:**

| Feature | Blocks Composed |
|---------|-----------------|
| **email-generate** | brand + org + industry + audience + plan + assets + knowledge |
| **form-generate** | brand + org + industry (+ profile optional) |
| journey-content | brand + org + industry + journey-context + audience + plan + assets |
| chat agent | brand + org + industry + knowledge + conversation history |

---

## Step 4 — Proof: Form Generation Feature (5 min)

📂 **Open:** `SSP.AI/Prompts/FormGenerate/FormGeneratePromptBuilder.cs`
📂 **Then:** `SSP.AI/Schemas/FormGenerate/FormGenerateOutput.cs`

> "Let me show you a concrete feature running on the substrate — form generation. User gives a free-text brief, the AI returns a validated form definition."

**Request:**

```json
POST /forms/generate

{
  "description": "membership renewal form with payment frequency choice",
  "titleHint": "Renew Your Membership"
}
```

**Response (201 Created):**

```json
{
  "formId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Membership Renewal",
  "definition": {
    "title": "Membership Renewal",
    "description": "Renew your membership and continue enjoying exclusive benefits with Acme Fitness.",
    "submit_label": "Renew Now",
    "success_message": "Thank you for renewing! You'll receive a confirmation email shortly.",
    "fields": [
      {
        "key": "full_name",
        "label": "Full Name",
        "type": "text",
        "required": true,
        "placeholder": "Enter your full name",
        "help_text": null,
        "options": null
      },
      {
        "key": "email",
        "label": "Email Address",
        "type": "email",
        "required": true,
        "placeholder": "you@example.com",
        "help_text": "We'll send your renewal confirmation here",
        "options": null
      },
      {
        "key": "membership_type",
        "label": "Membership Type",
        "type": "select",
        "required": true,
        "placeholder": null,
        "help_text": "Select the membership tier you'd like to renew",
        "options": [
          { "value": "individual", "label": "Individual" },
          { "value": "family", "label": "Family" },
          { "value": "corporate", "label": "Corporate" },
          { "value": "student", "label": "Student" }
        ]
      },
      {
        "key": "renewal_period",
        "label": "Renewal Period",
        "type": "select",
        "required": true,
        "options": [
          { "value": "annual", "label": "Annual" },
          { "value": "quarterly", "label": "Quarterly" },
          { "value": "monthly", "label": "Monthly" }
        ]
      },
      {
        "key": "phone",
        "label": "Phone Number",
        "type": "phone",
        "required": false,
        "placeholder": "+1 (555) 000-0000"
      },
      {
        "key": "comments",
        "label": "Additional Comments",
        "type": "textarea",
        "required": false,
        "placeholder": "Anything you'd like us to know?"
      }
    ]
  },
  "createdAt": "2026-06-25T12:00:00Z"
}
```

> "This output goes through FluentValidation — field types constrained to 9 allowed values, keys must be snake_case, 3-12 fields, all string limits enforced. If the AI returns invalid JSON, the corrective-prompt loop retries automatically. Same pipeline as email, same guarantees."

---

## Step 5 — Proof: Email Generation Feature (5 min)

📂 **Open:** `SSP.AI/Email/BrandedEmailGenerator.cs`
📂 **Then:** `src/backend/Core/AI/docs/unified-email-integration-contract.md`

> "Second feature on the substrate — branded email generation. This is the one Vishnu specifically asked about."

**Request:**

```json
POST /bff/accounts/{accountId}/emails/generate

{
  "intent": "Invite lapsed members to our spring gala",
  "contextKind": "journey_step",
  "journeyStepId": "11111111-1111-1111-1111-111111111111",
  "eventId": "33333333-3333-3333-3333-333333333333",
  "cta": {
    "enabled": true,
    "url": null,
    "text": null
  },
  "structuralOptions": {
    "recipientSegmentDescription": "lapsed members, 6+ months inactive",
    "emailPurpose": "re-engagement"
  }
}
```

**Response (200 OK):**

```json
{
  "subject": "Your seat at the spring gala is waiting",
  "previewText": "Two minutes to RSVP — we saved you a place",
  "htmlContent": "<p>…inner HTML only, no <html>/<head>/<body> wrapper…</p>",
  "contextKind": "journey_step",
  "resolvedCtaUrl": "https://events.example.com/reg/42",
  "generatedAt": "2026-06-25T12:00:00Z"
}
```

**Context discriminator — 3 modes:**

| `contextKind` | Required id | CTA behaviour |
|---|---|---|
| `campaign_email` | `campaignEmailId` | No auto CTA |
| `journey_step` | `journeyStepId` | `eventId` → pre-fills CTA from event registration URL |
| `standalone` | — | Caller-supplied CTA or none |

> "The generator returns a discriminated result: `Success`, `InvalidRequest`, `ProviderFailed`, `MalformedOutput`, `EmptyOutput` — headless-first, no exceptions for expected failures. Generation is transient — we return subject / preview / html; the campaign or journey persists it through its own save path."

**Curl proof (runs without any Angular UI):**

```bash
# Journey step with event → CTA pre-fill
curl -i -X POST "https://<bff>/bff/accounts/{accountId}/emails/generate" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-TOKEN: <csrf>" --cookie "<session>" \
  -d '{ "intent": "Invite members to the gala", "contextKind": "journey_step",
        "journeyStepId": "11111111-1111-1111-1111-111111111111",
        "eventId": "33333333-3333-3333-3333-333333333333" }'
```

> "These curl stubs are the Week-4 DEOP gate — they pass independently of the Angular UI, so Click is unblocked today."

---

## Step 6 — Completeness & Quality Proof (3 min)

> "Let me quickly cover the numbers and the gap closure."

**Epic 1 delivery summary:**

| Story | What | Status |
|---|---|---|
| 1.2 — AI client wrapper | `IAiClient`, retry, validation, content filtering | ✅ shipped |
| 1.2.5 — Azure Foundry adapter | `AzureFoundryAiClient` + embeddings adapter | ✅ shipped |
| 1.3 — Usage & cost | `ai_usage` table, spend-cap enforcement, content-filter persistence | ✅ shipped |
| 1.4 — Context blocks (base) | brand · org · industry blocks | ✅ shipped |
| 1.5 — Email-generate proof | First feature on the substrate | ✅ shipped |
| 1.6 / 1.7 — Tenancy + prompts | Multi-tenant AI layer, prompt management | ✅ shipped |
| 1.8 — §5.10 data layer | Industry configs, org profiles, voice samples, KB docs + Foundry embeddings | ✅ shipped |
| 1.9 — Launch context blocks | profile · event · brief · contact-fields + form generation | ✅ shipped |
| 1.10 — Launch readiness | Handover README, Foundry memo, hour sign-off | ✅ shipped |

**Test growth:** 259 → 319 → **334 green unit tests** across the AI suite.

**June-10 conflict-report — every gap closed:**

| Gap flagged | Resolution |
|---|---|
| Spend-cap check missing before provider call | ✅ `DailyAiSpendCapEnforcer` blocks pre-provider |
| `content_filter_outcome` written as `null` | ✅ Structured JSONB outcome persisted |
| No `Opus` / reasoning model class | ✅ `ModelClass` = Sonnet / Haiku / **Opus** |
| No Azure AI Foundry provider | ✅ `AzureFoundryAiClient` + embeddings shipped |
| Old loaders at risk of being dropped | ✅ Shipped as first-class blocks |

---

## Step 7 — Email Next Steps & Ownership (3 min)

> "So what's left for email?"

| Party | Scope | Status |
|---|---|---|
| **DEOP** | Story 2.1 (backend unified email endpoint) + Story 2.3 (integration contract & hand-off) | ✅ **Done** |
| **Click** | Story 2.2 (Angular `AIEmailModal` refactor + journey-editor wire-up) | 🔜 **Next** |

**Click's work (Story 2.2):**

1. **2.2.1** — Extract the existing ~300-line `AIEmailModal` into a shared Angular component calling `POST …/emails/generate`.
2. **2.2.2** — Wire it into the journey editor (journey-step context → CTA pre-fill from the event).
3. Branch from the epic branch, merge back into it.

**Merge order:** Land Epic 1 (PR #111) first → then one Epic 2 PR (DEOP 2.1/2.3 + Click 2.2 together).

---

## Step 8 — Key Files Reference (show during Q&A if needed) (1 min)

| Area | Key files |
|------|-----------|
| **AI core entry** | `src/backend/Core/AI/README.md` |
| **Pipeline** | `SSP.AI/Client/AiClientBase.cs`, `AzureFoundryAiClient.cs`, `AnthropicAiClient.cs` |
| **Context blocks** | `SSP.AI/Context/{Brand,Org,Industry,Profile,Event,Brief,ContactFields,Knowledge}/` |
| **Email generator** | `SSP.AI/Email/BrandedEmailGenerator.cs`, `EmailGenerationContext.cs` |
| **Email contract** | `Core/AI/docs/unified-email-integration-contract.md` |
| **Form generator** | `SSP.AI/Prompts/FormGenerate/FormGeneratePromptBuilder.cs` |
| **Form schema** | `SSP.AI/Schemas/FormGenerate/FormGenerateOutput.cs` |
| **Usage logging** | `SSP.AI/Usage/AiUsageLogger.cs` |
| **Spend cap** | `SSP.AI/Client/DailyAiSpendCapEnforcer.cs` |
| **Content filter** | `SSP.AI/Client/ConfigurableAiContentFilter.cs` |
| **DI composition** | `SSP.AI/Extensions/ServiceCollectionExtensions.cs` |

---

## Step 9 — Decisions to Lock (4 min)

1. **Foundry: launch or post-launch?** Adapter code is shipped, but deployment names/pricing/residency need a live-Azure check. Do we block launch on Foundry, or ship on Anthropic and switch post-launch?

2. **Model-class routing** — Confirm `Opus`/reasoning for recommendation/strategy work, or keep everything on Sonnet/Haiku for cost.

3. **Email refinement (edit-with-AI)** — Launch scope or v1.1?

4. **Email import** — Confirm as post-launch deferral or promote.

5. **Confirmation emails** — Confirm: form/event confirmations become journey email steps (no separate Form/Event agent).

---

## Step 10 — Open Floor & Anticipated Q&A (3 min)

- **"Is the core actually done or just designed?"** → 334 green tests, handover README shipped, June-10 gaps all closed. Production-ready.
- **"When can we ship email end-to-end?"** → As soon as Story 2.2 (Click) lands; then one Epic 2 PR after Epic 1 merges.
- **"Are we on Anthropic or Foundry at launch?"** → Anthropic direct today; Foundry adapter is code-complete but needs live-Azure config. Decision needed today.
- **"What about form generation?"** → Already running on the substrate. Click builds the form editor UI against the JSON contract we deliver.
- **"What about refinement / import?"** → Not in current slice; needs launch-vs-v1.1 decision.

---

## Action Items (fill in during the call)

| # | Decision / Action | Owner | Due |
|---|---|---|---|
| 1 | Foundry launch vs post-launch decision | | |
| 2 | Email refinement — launch or v1.1 | | |
| 3 | Email import — post-launch deferral confirmed / promoted | | |
| 4 | Story 2.2 (Angular `AIEmailModal` + journey wire-up) kickoff | Click | |
| 5 | Merge order confirmed: Epic 1 PR #111 → then Epic 2 PR | | |
| 6 | Story 1.8 BFF write endpoints + HNSW index scheduling | DEOP | |

---

_Sources: `docs/ai-arch-scope.md` · `docs/deop/epic-1-ai-foundation-client-wrap.md` · `docs/deop/epic-2-unified-email-component.md` · `docs/deop-ai-roadmap-2026-06-10.md` · `docs/ai-foundry-rebuild-conflict-report-2026-06-10.md` · `src/backend/Core/AI/README.md` · `src/backend/Core/AI/docs/unified-email-integration-contract.md` · `docs/form-generation.md`. Status reflects DEOP doc-logs (build + test verified) as of 2026-07-02._
