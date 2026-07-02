# Form Generation — Technical Reference for Click Team

**Feature:** Task 1.9.1 — Form Generation (basic)  
**Scope:** v2 brief §5.6  
**Issue:** https://github.com/david-kokkilic-sweetspot/sweetspot-platform/issues/88  
**Branch:** `deop/feature/story-1.9.1-form-generation`  
**Status:** ✅ Merged into `deop/integration`

---

## 1. What This Feature Does

The form-generate feature takes a free-text brief (e.g., "membership renewal form with payment frequency choice") and produces a structured JSON form definition using AI. The definition is validated, persisted to the `forms` table, and the form_id is returned so the SPA can navigate to the form editor.

**DEOP owns:** AI generation endpoint, prompt composition, context blocks, output schema validation, DB persistence.  
**Click owns:** Form editor UI, form rendering, form templates, user-facing display.

---

## 2. API Contract

### Request

```
POST /forms/generate
Content-Type: application/json
```

```json
{
  "description": "membership renewal form with payment frequency choice",
  "titleHint": "Renew Your Membership"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `description` | string | ✅ | 1–2000 chars. Free-text brief describing the form. |
| `titleHint` | string | ❌ | Max 120 chars. Optional title suggestion. |

### Response (201 Created)

```json
{
  "formId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Membership Renewal",
  "definition": { ... },
  "createdAt": "2026-06-25T12:00:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `formId` | UUID | Persisted form ID — use for `/forms/{formId}` navigation. |
| `title` | string | AI-generated form title (echoed for convenience). |
| `definition` | object | The full validated form definition (see §3 below). |
| `createdAt` | ISO 8601 | UTC timestamp of creation. |

---

## 3. Output JSON Schema — `GeneratedFormDefinition`

This is the shape of the `definition` field in the response. It's also what's stored verbatim in `forms.definition_json`.

### Top-level fields

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | ✅ | Max 120 chars |
| `description` | string | ✅ | Max 400 chars. Introductory text shown above the form. |
| `submit_label` | string | ✅ | Max 32 chars. Submit button text. |
| `success_message` | string | ✅ | Max 200 chars. Confirmation message after submission. |
| `fields` | array | ✅ | 3–12 field objects (see below). |

### Field object

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `key` | string | ✅ | Max 64 chars. `snake_case` ASCII only (`^[a-z][a-z0-9_]*$`). Stable identifier. |
| `label` | string | ✅ | Max 120 chars. Human-readable label. |
| `type` | string | ✅ | One of: `text`, `email`, `phone`, `number`, `textarea`, `select`, `multiselect`, `checkbox`, `date` |
| `required` | boolean | ✅ | Whether the field is mandatory. |
| `placeholder` | string | ❌ | Max 120 chars. |
| `help_text` | string | ❌ | Max 200 chars. One-line guidance. |
| `options` | array | Conditional | **Required** when type is `select` or `multiselect`. 2–12 option objects. |

### Option object (for select / multiselect fields)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `value` | string | ✅ | Max 64 chars. Programmatic value. |
| `label` | string | ✅ | Max 64 chars. Display label. |

---

## 4. Complete Example Output

**Brief:** "membership renewal form with payment frequency choice"  
**Organisation:** Acme Fitness (membership industry)

```json
{
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
      "placeholder": null,
      "help_text": null,
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
      "placeholder": "+1 (555) 000-0000",
      "help_text": null,
      "options": null
    },
    {
      "key": "comments",
      "label": "Additional Comments",
      "type": "textarea",
      "required": false,
      "placeholder": "Anything you'd like us to know?",
      "help_text": null,
      "options": null
    }
  ]
}
```

---

## 5. How Context Blocks Work

Context blocks are the composable data layer that feeds every AI feature. Each block:

1. **Loads** tenant-specific data from the DB (e.g., brand settings, org info)
2. **Formats** it as a structured context object with typed properties
3. **Renders** it as a prompt string segment via `ToPromptString()`
4. **Degrades gracefully** — returns `Exists = false` with an empty stub when data is missing

### Blocks used by form-generate

| Block | Source | What it provides | Prompt section |
|-------|--------|-----------------|----------------|
| **BrandContext** | `brand_settings` | Voice description, tone tags, values, tagline | `## Brand Voice` |
| **OrgContext** | `accounts` | Org name, industry, address, locale, timezone | `## Organisation` |
| **IndustryContext** | `industry_template_configs` | Industry key, vocabulary, recurring-value labels | Industry-specific vocabulary |
| **ProfileContext** _(optional)_ | `organisation_profiles` | Audience description, tier names, voice samples | `## Profile` |

### How the prompt is composed

```
┌─────────────────────────────────────────────────────┐
│ SYSTEM PROMPT                                       │
│                                                     │
│ [1] Opener: "You are an expert form designer for    │
│     {org_name}, a {industry} organisation whose     │
│     audience is referred to as '{member_noun}'..."  │
│                                                     │
│ [2] ## Brand Voice                                  │
│     - Voice: warm and direct, slightly playful      │
│     - Tone: friendly, energetic, candid             │
│     - Values: transparency, customer-first          │
│     - Tagline: Your fitness journey starts here     │
│                                                     │
│ [3] ## Industry                                     │
│     (industry vocabulary and context)               │
│                                                     │
│ [4] ## Profile (optional)                           │
│     (audience description, voice exemplars)          │
│                                                     │
│ [5] ## OUTPUT SCHEMA                                │
│     (exact JSON contract the AI must follow)        │
│                                                     │
│ [6] ## CONSTRAINTS                                  │
│     - 3-12 fields                                   │
│     - snake_case keys                               │
│     - No payment/signatures unless requested        │
│     - JSON only, no markdown                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ USER MESSAGE                                        │
│                                                     │
│ Generate a form for this brief.                     │
│                                                     │
│ Brief: membership renewal with payment frequency    │
│ Suggested title: Renew Your Membership              │
│                                                     │
│ Respond ONLY with the JSON object.                  │
└─────────────────────────────────────────────────────┘
```

### Block composition per feature (full table)

| Feature | Blocks Composed |
|---------|-----------------|
| **form-generate** | brand + org + industry (+ profile optional) |
| email-generate | brand + org + industry + audience + plan + assets + knowledge |
| journey-content | brand + org + industry + journey-context + audience + plan + assets |
| chat agent | brand + org + industry + knowledge + conversation history |

---

## 6. Validation Pipeline

The output goes through a multi-layer validation pipeline before persistence:

1. **AI client pipeline** — the model's output is parsed and validated against the `FormGenerateOutput` schema. If validation fails, the pipeline sends a **corrective prompt** back to the model with the validation errors and retries (up to 2 attempts).

2. **FluentValidation** (`FormGenerateOutputValidator`) enforces:
   - `title` not empty, ≤120 chars
   - `submit_label` not empty, ≤32 chars
   - 3–12 fields
   - Field `key` matches `^[a-z][a-z0-9_]*$` (snake_case)
   - Field `type` is one of 9 allowed values
   - `select`/`multiselect` fields have 2–12 options
   - All string length limits enforced

3. **Markdown fence stripping** — defensive parser removes ```` ```json ``` ```` fences if the model accidentally includes them.

---

## 7. Database Storage

The generated form is persisted to the `forms` table:

| Column | Value |
|--------|-------|
| `id` | New UUID (returned as `formId`) |
| `account_id` | Authenticated tenant account |
| `prompt` | The original brief text |
| `title` | AI-generated title |
| `definition_json` | The full validated JSON (§4 above) stored verbatim |
| `feature_key` | `"form-generate"` |
| `created_at` | UTC timestamp |
| `updated_at` | UTC timestamp |

---

## 8. What's Not in Scope (v1)

| Feature | Status | Notes |
|---------|--------|-------|
| Form refinement (edit-with-AI) | v1.1 | Old Task 4.6.1 split |
| Conditional fields / logic | v1.1+ | Not in the JSON schema yet |
| File upload fields | Not planned | Excluded by prompt constraints |
| Payment fields | Not planned | Excluded by prompt constraints |
| Form rendering / editor UI | Click scope | Click builds the form builder |
| Form templates | Click scope | Click owns templates |
| CSS / theme generation | Not in scope | Brand visual fields available on BrandContext for Click to use directly |

---

## 9. Key Files Reference

| File | Purpose |
|------|---------|
| `SSP.AI/Schemas/FormGenerate/FormGenerateOutput.cs` | Output JSON C# record |
| `SSP.AI/Schemas/FormGenerate/FormGenerateOutputValidator.cs` | FluentValidation rules |
| `SSP.AI/Prompts/FormGenerate/FormGeneratePromptBuilder.cs` | Prompt composition |
| `SSP.AI/Prompts/FormGenerate/FormGeneratePromptInput.cs` | Prompt builder input |
| `SSP.AI/Context/Brand/BrandContext.cs` | Brand context block |
| `SSP.AI/Context/Org/OrgContext.cs` | Org context block |
| `SSP.AI/Context/Industry/IndustryContext.cs` | Industry context block |
| `SSP.AI/Context/Profile/ProfileContext.cs` | Profile context block |
| `SSP.Admin.Api/Services/Forms/FormGenerateWorkflow.cs` | End-to-end orchestration |
| `SSP.Admin.Api.Models/Forms/FormGenerateRequest.cs` | API request model |
| `SSP.Admin.Api.Models/Forms/FormGenerateResponse.cs` | API response model |

---

## 10. Questions? Contact

- **DEOP (AI substrate):** David Kokkilic
- **Issue tracker:** #88 and subtasks
- **Branch:** `deop/feature/story-1.9.1-form-generation` (merged into `deop/integration`)
