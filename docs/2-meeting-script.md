# Meeting Script — Form Generation Demo for Farron

**Duration:** ~30 min  
**Format:** Screen-share + walkthrough

---

## Step 1: Set the stage (3 min)

> "Thanks for reaching out, Farron. Let me walk you through exactly what I've built and where the boundary between our work sits. I'll show you the code, the output JSON, and how context blocks work — which is the piece you said you were most interested in."

**Key framing:**
- DEOP owns: AI generation backend (prompt composition, AI call, validation, DB persistence)
- Click owns: Form editor UI, form rendering, form templates, user-facing display
- The contract between us: **a JSON object** (the `GeneratedFormDefinition` shape) stored in `definition_json` on the `forms` table

---

## Step 2: Architecture overview — the 30-second version (2 min)

> "Here's how the flow works end-to-end."

Draw or explain this flow:

```
User clicks "Generate with AI" in the form builder
  ↓
SPA sends POST /forms/generate { description: "membership renewal form", title_hint?: "Renew" }
  ↓
BFF → Admin API → FormGenerateWorkflow
  ↓
1. Load 4 context blocks in parallel (brand, org, industry, profile)
2. FormGeneratePromptBuilder composes system prompt from blocks
3. AI client calls the model (with schema validation + corrective retry)
4. Deserialize response → FluentValidation → persist to forms table
5. Return { form_id, title, definition, created_at }
  ↓
SPA navigates to /forms/{form_id} — Click's form editor takes over
```

> "So by the time your form editor loads, the AI-generated definition is already in the DB. You just read it and render it."

---

## Step 3: Context blocks deep dive (5 min) — ⭐ Farron's key interest

> "This is the part you said you were keen to see. Let me show you how context blocks work."

**Show `BrandContext.cs`:**
- Point out the two responsibilities: **prompt-facing** (voice, tone, values, tagline) vs **renderer-facing** (colors, fonts, logos)
- Show `ToPromptString()` — only tonal fields go into the prompt, visual fields are excluded (§2.14)
- Show `BrandContext.Empty` — graceful degradation when no Brand Kit exists
- Show `Exists` property — every block has this

> "Each block is a pure function: give it an account ID, it loads the data, formats it. No side effects, no writes. Degrades gracefully — if a brand kit doesn't exist yet, it returns an empty stub and the prompt still works, just without brand personality."

**Show `OrgContext.cs`:**
- Organisation name, industry, address, locale, timezone
- Same `ToPromptString()` pattern — renders as `## Organisation` with bullet points

> "For form generation, we compose 3 mandatory blocks (brand + org + industry) and 1 optional (profile). The composition table in the strategy doc shows which blocks each feature uses."

**Show the composition table** (strategy-v2.md line ~423):

| Feature | Composes |
|---------|----------|
| email-generate | brand + org + industry + audience + plan + assets + knowledge |
| form-generate | brand + org + industry |
| chat agent | brand + org + industry + knowledge + conversation history |

> "Form-generate is intentionally lighter — it doesn't need audience or plan context, just brand voice and org identity."

---

## Step 4: The prompt builder (5 min)

**Show `FormGeneratePromptBuilder.cs`:**

> "The prompt builder is a pure function — no I/O, no side effects. It takes the context blocks as input and returns a system prompt + user message."

Walk through the sections:
1. **Opener** — role framing: "You are an expert form designer for {org name}, a {industry} organisation..."
2. **Brand block** — `brand.ToPromptString()` injected verbatim
3. **Industry block** — vocabulary, recurring values
4. **Profile block** — audience hints, voice samples (optional)
5. **Output schema** — pinned JSON contract (the exact shape the AI must return)
6. **Constraints** — 3-12 fields, snake_case keys, no payment/signatures unless requested

> "The prompt is deterministic — same inputs always produce the same system prompt. We test this with exact-output assertions in unit tests."

---

## Step 5: The output JSON — ⭐ What Farron asked for (5 min)

**Show `FormGenerateOutput.cs`:**

> "This is the C# record that defines the contract. Let me show you a concrete example of what the AI produces."

Show this example JSON:

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

> "This is validated by FluentValidation before persistence — field types are constrained to 9 allowed values, keys must be snake_case, 3-12 fields, character limits on everything. If the AI produces invalid JSON, the pipeline retries with a corrective prompt automatically."

**Show `FormGenerateOutputValidator.cs`** briefly — point out the allowed types, key regex, option count limits.

---

## Step 6: Persistence & API response (3 min)

**Show `FormGenerateWorkflow.cs`:**

> "After validation, the workflow persists a row in the `forms` table with the definition as JSON, then returns a 201 with the form_id, title, definition, and created_at."

**Show `FormGenerateResponse.cs`:**

> "The form_id is what the SPA uses to navigate to `/forms/{form_id}`. The definition is returned inline so the SPA doesn't need a second round-trip."

---

## Step 7: Boundary clarification — what's yours, what's mine (3 min)

| Aspect | Owner | Status |
|--------|-------|--------|
| AI generation endpoint (`/forms/generate`) | DEOP | ✅ Done |
| Prompt composition + context blocks | DEOP | ✅ Done |
| Output schema + FluentValidation | DEOP | ✅ Done |
| DB persistence (forms table, definition_json) | DEOP | ✅ Done |
| Feature key registration | DEOP | ✅ Done |
| Unit tests (prompt builder + schema validation) | DEOP | ✅ Done |
| Form editor UI / rendering | Click | Click's scope |
| Form templates | Click | Click's scope |
| Form refinement (edit-with-AI) | v1.1 | Deferred |

> "Refinement (edit-with-AI, re-generate individual fields) is deferred to v1.1 — that's the old Task 4.6.1 split. For launch, we generate the full form definition once, and the user edits it manually in your form builder."

---

## Step 8: Open floor (4 min)

> "That's the full picture. What questions do you have? Anything about the JSON shape that doesn't work for your form editor, or fields you'd need that aren't there?"

**Be ready for:**
- "Can we add field X to the JSON?" — Yes, we extend `FormGenerateOutput` and update the prompt + validator. Easy change.
- "What about styling/theme?" — Brand visual fields (colors, fonts) are on the `BrandContext` renderer-facing side. Your form editor can read those from the brand kit directly. The AI doesn't generate CSS.
- "What about conditional fields?" — Not in v1 scope. Could be added to the schema later.
- "How do merge tags work?" — ContactFieldsContextBlock (Task 1.9.5) surfaces merge tags. Not wired into form-generate yet but could be in v1.1.
