# Epic 2 — Unified Email-Content Component

Progress log for Epic 2 — Unified Email-Content Component, covering the Deop-owned Stories 2.1 (Backend Unified Email Endpoint) and 2.3 (Integration Contract & Hand-Off). Story 2.2 (Angular `AIEmailModal` extraction) is Click engineering's and is tracked on the Click timeline. Authoritative scope: `docs/ai-arch-scope.md` §3 and EPIC 2 Stories 2.1 + 2.3. Each completed `Task x.y.z` is appended below in chronological order; earlier entries are not edited.

All Story 2.1 + 2.3 work landed on the `deop/feature/unified-email-content-component` epic branch in the code repo (`Click-Development/sweetspot`), built via nested story → epic merges. The epic branch is **not** merged into `deop/integration` while PR #111 (Epic 1) is under review — it merges in a single PR once that review settles.

---

## Task 2.1.1 — Unified Email Generation Service

Implemented `IBrandedEmailGenerator` / `BrandedEmailGenerator` in `SSP.AI/Email/` as the single function for all branded email generation (scope §3.1). The generator loads the brand / org / industry context blocks for the account, composes the prompt through the existing `IEmailGeneratePromptBuilder`, and routes the call through `IAiClient` under the shared `email-generate` feature key — so model selection, schema validation, content filtering, usage logging, and the daily spend cap all apply identically to every caller and no per-surface HTML-generation duplication is introduced (scope §4.4).

The service is headless-first (scope §3.6): it returns a discriminated `BrandedEmailGenerationResult` (`Success` / `InvalidRequest` / `ProviderFailed` / `MalformedOutput` / `EmptyOutput`) rather than throwing for expected failures, so future recommendation action handlers and the BFF workflow can branch without try/catch. It is registered transient in `AddAiServices` so each resolution gets a fresh transient `IAiClient` (preserving HttpClient handler rotation). Output deserialisation uses the snake_case naming policy because the `email-generate` schema (`subject` / `preview_text` / `html_content`) carries no `[JsonPropertyName]` attributes.

Verified with `dotnet build Core/SSP.Core.sln` clean and 15 dedicated generator unit tests green (covering request validation, the three context kinds, CTA resolution, provider/malformed/empty failure paths, markdown-fence stripping, and cancellation propagation) within the 334-test SSP.AI suite.

---

## Task 2.1.2 — Context Type Refactoring + Context-Aware CTA

Replaced the prototype's opaque `emailId` with a discriminated `EmailGenerationContext` (scope §3.3): `EmailGenerationKind` of `CampaignEmail`, `JourneyStep`, or `Standalone`, with static factory methods that make invalid kind/identifier combinations unconstructable and a generator-side `ValidateContext` that re-enforces the invariants (campaign requires a campaign id, journey requires a step id, standalone forbids all parent ids) as defence in depth.

Context-aware CTA resolution follows scope §3.4: for a `JourneyStep` that names an `EventId`, the generator loads the event block and pre-fills the CTA from `EventContext.RegistrationUrl`; an explicit caller URL always wins over the event-derived one; a `Standalone` caller supplies its own URL or toggles the CTA off via `EmailCtaOptions.Enabled = false`. The event block is loaded only for the journey-step-with-event case, and the resolved URL is surfaced back on the result as `ResolvedCtaUrl` for UI verification.

Verified by the CTA-focused subset of the generator tests: event pre-fill, explicit-URL override, toggled-off suppression, the standalone path skipping the event block entirely, and the journey-step path passing the correct `EventId` through `EventContextOptions`.

---

## Task 2.1.3 — BFF Endpoint

Exposed the generator over HTTP following the established Forms vertical slice. `POST /bff/accounts/{accountId}/emails/generate` lands on a dedicated `EmailGenerationController` (kept separate from the existing `EmailsController`, which proxies email *jobs* to the Email API, because this endpoint targets a different downstream and concern). It is guarded by `[ValidateCsrf]` + `[SessionAuthorize(Roles = "admin,globalAdmin")]` and proxies through `IEmailGenerationApiClient` to the Admin API, preserving downstream status codes faithfully.

On the Admin side, `EmailGenerationController` delegates to `EmailGenerateWorkflow`, a thin adapter that parses the string context discriminator, maps the primitive request models (`SSP.Admin.Api.Models.Emails`, free of any SSP.AI dependency) onto the SSP.AI domain request, invokes the generator, and maps the discriminated result to HTTP: `Success` → 200, `InvalidRequest` → 400, and the upstream-AI failures (`ProviderFailed` / `MalformedOutput` / `EmptyOutput`) → 502. Generation is transient — no row is persisted; the owning campaign or journey persists the content through its own save path. Both API clients are registered in their respective `Program.cs`.

Verified with `dotnet build Core/SSP.Core.sln` clean and 6 `EmailGenerateWorkflow` unit tests green (unknown context kind → 400, blank intent → 400, success → 200 with echoed context kind, journey-step `EventId` mapping, generator-invalid → 400, provider-failed → 502).

---

## Task 2.3.1 — Hand-Off Contract Documentation

Authored `src/backend/Core/AI/docs/unified-email-integration-contract.md` so Click engineering can build and integrate the Story 2.2 Angular component against the BFF endpoint without a Deop engineer present. The document specifies the endpoint, auth model, full request/response JSON shapes, the context-discriminator table with its required/forbidden identifiers, the context-aware CTA resolution table, and the error-code semantics (400/401/502/500) with the error-body shape and retry guidance.

It also documents the headless caller pattern (injecting `IBrandedEmailGenerator` for in-process generation with no HTTP or modal) and provides four runnable curl integration-test stubs — standalone, journey-step CTA pre-fill, CTA toggled off, and a validation error — that Click can execute against the BFF endpoint. These stubs double as the Week-4 decision-checkpoint Deop-gate verification: they pass independently of the Angular UI, so the contract is unblocked even if Story 2.2 has not started.

This completes Deop's EPIC 2 scope. Remaining EPIC 2 work (Story 2.2 — Angular `AIEmailModal` refactor + journey-editor wire-up + E2E) is Click engineering's, to be branched from the epic branch and merged back into it so all EPIC 2 merge conflicts resolve at the epic level, away from `deop/integration`.
