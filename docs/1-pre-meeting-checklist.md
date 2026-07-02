# Pre-Meeting Checklist (Do These Before the Call)

**Time needed:** ~30 min  
**Meeting with:** Farron (Click team)

---

## 1. Push the branch & confirm it's visible (5 min)

```bash
cd repostories/sweetspot
git push origin deop/feature/story-1.9.1-form-generation
```

Share this link with Farron before the call:  
`https://github.com/david-kokkilic-sweetspot/sweetspot-platform/compare/deop/feature/story-1.9.1-form-generation`

Also share issue #88:  
`https://github.com/david-kokkilic-sweetspot/sweetspot-platform/issues/88`

---

## 2. Open key files in your editor ready to screen-share (5 min)

Have these tabs open in VS Code / Rider — you'll walk through them in order:

| # | File | Why |
|---|------|-----|
| 1 | `docs/ai-architecture-strategy-v2.md` line ~423 | Feature→Block composition table |
| 2 | `SSP.AI/Context/Brand/BrandContext.cs` | Show a context block |
| 3 | `SSP.AI/Context/Org/OrgContext.cs` | Show org context |
| 4 | `SSP.AI/Prompts/FormGenerate/FormGeneratePromptBuilder.cs` | The prompt builder |
| 5 | `SSP.AI/Prompts/FormGenerate/FormGeneratePromptInput.cs` | What goes into the prompt |
| 6 | `SSP.AI/Schemas/FormGenerate/FormGenerateOutput.cs` | **The output JSON contract** |
| 7 | `SSP.AI/Schemas/FormGenerate/FormGenerateOutputValidator.cs` | FluentValidation rules |
| 8 | `SSP.Admin.Api/Services/Forms/FormGenerateWorkflow.cs` | End-to-end orchestration |
| 9 | `SSP.Admin.Api.Models/Forms/FormGenerateRequest.cs` | API request |
| 10 | `SSP.Admin.Api.Models/Forms/FormGenerateResponse.cs` | API response |

---

## 3. Prepare the example JSON output (5 min)

Copy the example JSON from `3-after-meeting-doc.md` (the post-meeting doc) into a scratch file or clipboard — you'll show it during the demo.

---

## 4. Have the architecture diagram mentally ready (5 min)

The flow to explain:

```
SPA → POST /forms/generate (BFF) → Admin API
  → Load context blocks (brand + org + industry + profile) in parallel
  → FormGeneratePromptBuilder composes system prompt
  → IAiClient.GenerateAsync (schema validation + corrective retry)
  → Deserialize → FluentValidation → Persist to forms table
  → Return { form_id, title, definition, created_at }
  → SPA navigates to /forms/{form_id}
```

---

## 5. Review Farron's questions and your talking points (10 min)

| Farron's Question | Your Answer |
|---|---|
| "Are you taking the AI generation aspect fully?" | Yes — Task 1.9.1 is under DEOP scope. Click owns the form editor UI, form templates, and form rendering. DEOP owns the AI generation endpoint that produces the JSON. |
| "What will the output JSON look like?" | Show `FormGenerateOutput.cs` — it's a typed C# record mirroring a `GeneratedFormDefinition` contract. Walk through the example JSON. |
| "Will you work on DB storage?" | Yes — the workflow already persists to the `forms` table (form_id, account_id, title, definition_json, prompt). The form_id is returned so the SPA can navigate. |
| "Will you work on display?" | No — display/rendering is Click's domain (the form editor/builder). DEOP returns structured JSON; Click renders it. |
| "Just generating the JSON?" | Generation + validation + persistence + returning `form_id`. Not rendering or editing. |
| "Context blocks — how do they work?" | Show `BrandContext.cs` → `ToPromptString()`. Each block loads tenant data, formats it for the prompt. Blocks compose independently (brand + org + industry for forms). |
| "Is there a branch?" | Yes — `deop/feature/story-1.9.1-form-generation` (share the compare link). |
