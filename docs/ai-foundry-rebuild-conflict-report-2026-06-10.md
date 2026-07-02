# Azure AI Foundry Rebuild - Conflict and Difference Report

Date: 2026-06-10

## Sources Checked

1. Handover attachment: `/Users/kklc/.codex/attachments/c38667c5-b52f-44e2-8198-66ec21ff07b0/pasted-text.txt`
2. Canonical planning doc: `docs/ai-arch-scope.md`
3. GitHub issue bootstrap source: `scripts/bootstrap-issues.py`
4. GitHub planning issues in `david-kokkilic-sweetspot/sweetspot-platform`
5. Local progress log: `docs/deop/epic-1-ai-foundation-client-wrap.md`
6. Local Sweetspot clone under `repostories/sweetspot/`

GitHub limitation: the GitHub connector could read `david-kokkilic-sweetspot/sweetspot-platform`, but searches against `Click-Development/sweetspot` returned a permission/not-found error. I verified implementation state from the local clone instead.

## Executive Summary

The planning repo and GitHub issues are mostly internally consistent with each other. The main conflicts are between the new handover's "Azure AI Foundry rebuild" framing and the current 7-PR plan, which still says launch on Anthropic direct and migrate to Foundry post-launch.

The handover is a full prototype parity document. The GitHub plan is a narrower launch migration plan. That difference is not automatically wrong, but it must be made explicit or the team will miss surfaces such as landing pages, profile research, email import, social generation, inbound classification, and full form/landing schemas.

## Step 1 - Source of Truth Conflict

### Conflict

The handover says the target rebuild is for Azure AI Foundry. The planning doc says:

- launch on Anthropic direct API
- migrate to Azure AI Foundry post-launch as a v1.5 PR
- only make Foundry launch-critical if data residency requires it

### Current Implementation

The local Sweetspot clone currently implements an Anthropic-backed client:

- `SSP.AI.Client.Anthropic`
- `AnthropicAiClient`
- `IAnthropicMessagesTransport`
- config default `Ai:Provider = anthropic`

There is no Azure AI Foundry provider implementation in the local clone.

### Decision Needed

Choose one of these and update all sources to match:

1. Foundry is launch scope: add explicit provider tasks, model deployment config, Azure credential/config work, and prompt retesting.
2. Foundry remains post-launch: rename the handover framing as "Foundry-compatible handover" rather than "Foundry rebuild" and keep Anthropic direct as PR 9-14 scope.

## Step 2 - AI Surface Coverage Differences

### Handover Covers Full AI Surface Area

The handover lists these AI surfaces:

1. Email generation and refinement
2. Email import
3. Forms v2 generation and refinement
4. Forms v2 field mapping
5. Landing page generation, refinement, and layout switching
6. Events Create-with-AI
7. Chat agent
8. Profile research
9. Insights, social-post generation, and inbound-reply classification

### GitHub Plan Tracks a Narrower Launch Slice

The plan prioritizes:

1. AI wrapper foundation
2. usage logging and cost tracking
3. brand/org/industry context blocks
4. email-generate proof
5. unified branded email generation
6. form/event agent migration into journeys
7. remaining context blocks
8. recommendation actions and command centre

### Difference

The following handover surfaces are not tracked as first-class GitHub tasks:

- Email import
- Email refinement as its own migration path
- Forms v2 generation/refinement full migration
- Forms v2 field mapping full migration
- Landing page generation/refinement/layout switching
- Chat agent runtime migration
- Profile research
- Insights ask endpoint
- Social generation
- Email inbound classification

The planning doc intentionally says some structural JSON and metadata surfaces are beyond the 7-PR plan. That is fine only if the desired scope is launch slice, not full prototype parity.

## Step 3 - Client Contract Differences

### Handover Contract

The handover's `generate()` request includes:

- `orgId`
- `userId`
- `feature`
- `system`
- `messages`
- `modelClass`
- `maxTokens`
- `temperature`
- `schema`
- `metadata`
- `consentStatus`
- `traceId`

It returns raw `content`, parsed output, concrete model, usage, latency, and trace id.

### Current C# Contract

The local implementation has:

- `Feature`
- `System`
- `Messages`
- `ModelClass`
- `MaxOutputTokens`
- `AccountId`
- `UserId`
- `TraceId`
- `ConsentStatus`

### Differences

1. `orgId` is correctly mapped to Sweetspot's `AccountId` convention. This is not a conflict, but it should be documented in issue bodies and handover notes.
2. `temperature` is not present.
3. arbitrary per-call `metadata` is not present.
4. schema is feature-registered through DI, not supplied per call.
5. the current return shape does not expose a typed `parsed` value to the caller.

### Recommended Action

Decide whether Sweetspot wants the handover contract exactly, or whether the current C# contract is the approved adaptation. If the current adaptation is approved, add a short "contract mapping" section to `docs/ai-arch-scope.md`.

## Step 4 - Model Class Conflict

### Handover

The handover uses semantic model classes:

- `generation` -> Sonnet
- `classification` -> Haiku
- `reasoning` -> Opus

### Plan and Current Code

The plan and current code use only:

- `Sonnet`
- `Haiku`

There is no `Reasoning` / Opus class in the C# model enum or config.

### Risk

Recommendation reasoning, strategy work, and any future agent planning may be forced into Sonnet without a distinct high-reasoning budget/class. That may be acceptable for cost, but it is a product/quality decision.

### Recommended Action

Either add `Reasoning` to the model-class vocabulary now, or explicitly remove Opus/reasoning from the handover compatibility target.

## Step 5 - Spend Cap Gap

### Handover

The handover makes spend-cap enforcement part of the sacred funnel:

- check spend before any AI cost
- default daily cap
- throw a typed spend-cap error before calling the provider

### Plan and Current Code

The planning docs mention hard daily caps and cost controls as open/future concerns. The current local implementation has cost calculation and `ai_usage` logging, but I did not find a pre-call spend-cap check in `SSP.AI`.

### Conflict

If the handover is the contract, spend-cap enforcement is missing from the GitHub task breakdown and from the current Sprint 1 implementation.

### Recommended Action

Create a new PR 9 task under Story 1.3 or Story 1.2:

`Task 1.3.3: Spend Cap Enforcement`

Minimum subtasks:

- configure per-account daily cap and default cap
- calculate spend-to-date from `ssp.ai_usage`
- block before provider invocation
- return a typed AI client error
- add tests proving no provider call happens when capped

## Step 6 - Usage Logging Difference

### Good Alignment

The local implementation matches most of the required `ai_usage` column set:

- account/user
- feature
- model
- input/output tokens
- cost
- latency
- success/failure
- error message
- prompt/output hashes
- consent status
- data residency region
- trace id
- content filter outcome column

### Difference

`content_filter_outcome` exists in schema, but the local logger currently writes `ContentFilterOutcome = null`. The progress log calls this out as deferred because the content-filter contract does not yet surface structured results to the logger.

### Recommended Action

Do not close compliance/AI Act redaction logging as complete until structured filter outcomes are persisted. Add a follow-up task or make it part of launch readiness.

## Step 7 - GitHub Issue Tracking Differences

### Confirmed GitHub State

Closed:

- Story 1.1 and tasks 1.1.1-1.1.2
- Story 1.2 and tasks 1.2.1-1.2.4
- Story 1.3 and tasks 1.3.1-1.3.2

Open:

- Epic 1 itself
- Story 1.4 onward
- Epics 2-5 and their stories/tasks

### Difference

Most closed task issue bodies still show unchecked Markdown subtasks. Issue #3 is checked, but issues #4 and #6-#12 are closed while their body checkboxes remain unchecked.

### Risk

The GitHub project may show the items closed, but anyone reading the task body sees unfinished checklists. That creates avoidable confusion in handover and client reporting.

### Recommended Action

Backfill closed issue bodies or add completion comments for #4 and #6-#12. The local progress log already has good completion summaries that can be copied into comments.

## Step 8 - Context Loader Difference

### Handover

The handover describes current prototype loaders:

- org
- brand
- profile
- knowledge
- contact-fields
- industry-examples

It also explains the prompt composition pattern and feature-specific context composition.

### Plan

The plan defines 10 future Sweetspot context blocks:

- brand
- org
- industry
- methodology
- field-semantics
- audience
- plan
- insights
- knowledge
- assets

### Current Code

The local Sweetspot clone has the AI client and usage layer, but I did not find implemented context block folders/classes yet. That matches the open GitHub state: Story 1.4 is still open.

### Difference

The handover's `profile` and `contact-fields` loaders are not directly named in the 10-block plan. Their responsibilities are partly redistributed:

- profile knowledge likely maps to `org`, `brand`, and `knowledge`
- contact fields likely maps to `field-semantics`

### Recommended Action

Add a mapping table for old loader -> Sweetspot block so implementers do not accidentally drop profile/contact-field behavior.

## Step 9 - Prompt and Voice Rules Gap

### Handover

Prompt files and voice rules are central:

- one prompt per file/class
- `VOICE_INSTRUCTIONS` composed into every content prompt
- post-processing via dash stripping
- 15 prompt files from the prototype are described in detail

### Plan

Prompt storage is tracked as Task 1.7.1. Voice rules, dash stripping, and prompt registry parity are not broken down in detail.

### Current Code

The local `SSP.AI` project does not yet show prompt classes or voice-rule implementation. Task 1.7.1 is open.

### Recommended Action

Expand Task 1.7.1 or add subtasks for:

- shared voice instruction source
- dash-strip post-processor if product voice requires it
- prompt registry parity list
- prompt tests/snapshots for email-generate proof

## Step 10 - Foundry-Specific Open Questions

The handover has Foundry-specific decisions that are not yet represented as GitHub tasks:

1. Foundry model choice: Claude via Microsoft partnership or OpenAI deployments
2. deployment-name mapping instead of raw model IDs
3. token/cost table per Foundry deployment
4. JSON mode or structured outputs vs corrective retry
5. Foundry rate limits per deployment
6. prompt caching strategy
7. data residency launch dependency

The planning doc includes some of these as open questions, but the GitHub issue set does not include a specific Foundry decision task.

### Recommended Action

If Foundry is not launch scope, create a post-launch epic now. If Foundry is launch scope, add a Sprint 1 decision task before more Anthropic-specific work lands.

## Recommended Cleanup Sequence

1. Decide Foundry launch vs post-launch.
2. Update `docs/ai-arch-scope.md` to reflect that decision.
3. Add a contract mapping table for handover -> C# implementation.
4. Add missing task for spend-cap enforcement.
5. Add missing task for persisting `content_filter_outcome`.
6. Add old-loader -> new-context-block mapping.
7. Add parity backlog issues for the handover AI surfaces not in the 7-PR plan.
8. Backfill closed GitHub issue bodies/comments so closed tasks do not show unchecked subtasks.
9. Add a Foundry decision task or post-launch Foundry epic.
10. Keep `docs/deop/epic-1-ai-foundation-client-wrap.md` as the implementation progress log, but link it from the relevant GitHub closed issues.

## Bottom Line

There is no major conflict between the local plan and the GitHub issue structure. The real risk is scope interpretation: the handover reads like a full Azure AI Foundry rebuild contract, while the current plan and implementation are an Anthropic-first launch migration with Foundry compatibility later.

That decision should be resolved before Stories 1.4, 1.5, and 1.7 proceed, because context blocks, prompt contracts, model classes, spend caps, and endpoint parity all depend on it.
