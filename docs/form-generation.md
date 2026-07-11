# Form Generation — Technical Reference for Click Team

**Feature:** Task 1.9.1 — Form Generation (basic)  
**Scope:** v2 brief §5.6  
**Issue:** https://github.com/david-kokkilic-sweetspot/sweetspot-platform/issues/88  
**Branch:** `deop/feature/story-1.9.1-form-generation`  
**Status:** ✅ Merged into `deop/integration`

---

## 1. What This Feature Does

The form-generate feature takes a free-text brief (e.g., "membership renewal form with payment frequency choice") and produces a structured JSON form definition using AI. Generation is **stateless** — the validated definition is returned for human review; **nothing is persisted**. Persisting a form (and minting its id) is a separate save/publish action owned by Click's Forms feature.

> **Change note (PR #111 review):** originally specced as stateful (persist to `forms`, return `formId`) per v2 brief §5.6. Following review it ships **stateless**, and the endpoint moved to the **Forms API** — aligning with brief §6, where the forms table/CRUD/UI are Click's. The §5.6-vs-§6 statefulness question is Stephi's to ratify.

**DEOP owns:** AI generation endpoint, prompt composition, context blocks, output schema validation.  
**Click owns:** Form editor UI, form rendering, form templates, user-facing display, the `forms` table + persistence.

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

### Response (200 OK)

```json
{
  "title": "Membership Renewal",
  "definition": { ... }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | AI-generated form title (echoed for convenience). |
| `definition` | object | The full validated form definition (see §3 below). |

Generation is stateless — no `formId` / `createdAt` is returned. Persisting the form (and minting its id) is Click's separate save/publish action.

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
| `type` | string | ✅ | One of: `text`, `email`, `phone`, `number`, `textarea`, `select`, `multiselect`, `checkbox`, `date`. For a **mapped** field the server overrides this with the type derived from the contact field (see §3.1). |
| `contact_field_key` | string \| null | ❌ | `snake_case`, max 50 chars (matches `contact_field_definition.field_key varchar(50)`). The non-archived contact field this field binds to. `null` when the field maps to no contact field (e.g. a consent checkbox). The AI must pick a key from the account's available contact fields — it may not invent one. |
| `required` | boolean | ✅ | Whether the field is mandatory. |
| `placeholder` | string | ❌ | Max 120 chars. |
| `help_text` | string | ❌ | Max 200 chars. One-line guidance. |
| `options` | array | Conditional | **Required** when type is `select` or `multiselect`. 2–12 option objects. Dropped (`null`) for contact-bound fields — see §3.1. |
| `options_source` | string \| null | ❌ | `contact_field` (options resolved at render from the bound contact field — no inline options), `static` (AI-authored inline list on an unmapped field), or `null` (field carries no options). |

### Option object (for select / multiselect fields)

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `value` | string | ✅ | Max 64 chars. Programmatic value. |
| `label` | string | ✅ | Max 64 chars. Display label. |

### 3.1 Contact-field binding (server post-processing)

Every generated field binds to the account's contact model. Before the AI call, the workflow loads
the account's **non-archived** `contact_field_definition` rows (plus their non-archived
`contact_field_option` picklist values) via `IContactFieldDefinitionResolver` (filtered to
`!IsArchived`) and injects them into the prompt as an `## AVAILABLE CONTACT FIELDS` list, so the model
maps each field to a real `field_key` rather than inventing one.

After the AI returns and schema validation passes, the workflow rewrites the fields against that same
set:

- **Drift guard** — any field whose `contact_field_key` is non-null but **not** in the account's
  non-archived set is **dropped** (logged at `Warning`). This protects against occasional model drift.
- **Type derivation** — for a mapped field, `type` is forced from the contact field's
  `contact_field_type` (the AI-chosen `type` is overridden). Mapping:

  | contact_field_type | form `type` |
  |--------------------|-------------|
  | Text | `text` |
  | Number | `number` |
  | Date | `date` |
  | Dropdown | `select` |
  | Multi-select | `multiselect` |
  | Checkbox | `checkbox` |
  | URL | `text` |
  | Email | `email` |
  | Phone | `phone` |
  | Long text | `textarea` |

- **Option binding** — for a contact-bound `select` / `multiselect` field, inline `options` are **dropped**
  (set to `null`) and `options_source` is set to `contact_field`; the renderer resolves the picklist from the
  bound contact field at render time (not snapshotted into the definition). An unmapped `select` /
  `multiselect` keeps its AI-authored list with `options_source: static`.
- **Unmapped fields** (`contact_field_key` is `null`) pass through unchanged.
- **Minimum-fields guard** — if fewer than **3** fields survive the binding pass, the request returns
  **HTTP 502** (`"AI returned no fields mapping to your contact model"`).

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
      "contact_field_key": "full_name",
      "required": true,
      "placeholder": "Enter your full name",
      "help_text": null,
      "options": null
    },
    {
      "key": "email",
      "label": "Email Address",
      "type": "email",
      "contact_field_key": "email",
      "required": true,
      "placeholder": "you@example.com",
      "help_text": "We'll send your renewal confirmation here",
      "options": null
    },
    {
      "key": "membership_type",
      "label": "Membership Type",
      "type": "select",
      "contact_field_key": "membership_type",
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
      "contact_field_key": "renewal_period",
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
      "contact_field_key": "phone",
      "required": false,
      "placeholder": "+1 (555) 000-0000",
      "help_text": null,
      "options": null
    },
    {
      "key": "comments",
      "label": "Additional Comments",
      "type": "textarea",
      "contact_field_key": null,
      "required": false,
      "placeholder": "Anything you'd like us to know?",
      "help_text": null,
      "options": null
    }
  ]
}
```

> For `membership_type` and `renewal_period` the `options` shown are illustrative — at runtime they are
> bound authoritatively from each mapped contact field's non-archived `contact_field_option` rows
> (see §3.1). `comments` has `contact_field_key: null`, so it is kept as authored and binds to no
> contact field.

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
   - `contact_field_key`, when present, is `snake_case` and ≤50 chars (`null` is allowed)
   - `select`/`multiselect` fields have 2–12 options
   - All string length limits enforced

3. **Markdown fence stripping** — defensive parser removes ```` ```json ``` ```` fences if the model accidentally includes them.

4. **Contact-field binding** (`FormGenerateWorkflow`) — after schema validation, fields are bound to the account's non-archived contact model: drift keys dropped, `type` derived from `contact_field_type`, `select`/`multiselect` options bound from `contact_field_option`, and a 3-field minimum re-checked (see §3.1). Whether a `contact_field_key` actually **exists** for the account is enforced here, not in FluentValidation, which has no account context.

---

## 7. Persistence

Generation is **stateless** — the `/generate` endpoint persists nothing. The `forms` table and its write path are owned by Click's Forms feature (brief §6); persisting a reviewed definition (and minting `formId`) happens on Click's separate save/publish action. The former DEOP-side `Form` entity, `forms` table, and its migration were removed in PR #111 (a `DropFormsTable` down-migration).

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
| `SSP.Forms.Api/Services/Forms/FormGenerateWorkflow.cs` | End-to-end orchestration |
| `SSP.Forms.Api.Models/Forms/FormGenerateRequest.cs` | API request model |
| `SSP.Forms.Api.Models/Forms/FormGenerateResponse.cs` | API response model |

---

## 10. Questions? Contact

- **DEOP (AI substrate):** David Kokkilic
- **Issue tracker:** #88 and subtasks
- **Branch:** `deop/feature/story-1.9.1-form-generation` (merged into `deop/integration`)
