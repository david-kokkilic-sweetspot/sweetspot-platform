# §5.10 Hour Sign-off — Launch Backlog Tabulation

**Task 1.10.3 deliverable.** Source: v2 scope brief `sweetspot-ai-deop-scope-brief-v2.docx` §5 Deliverables + §5.10 Data capture surfaces; scope doc reclassifications applied 2026-06-16 (commit `2a59cf4` on planning hub `main`).

Hours marked **shipped** are already implemented on `deop/integration` of the SSP repo. Hours marked **planned** are still pending; sum of `planned` is the remaining launch effort.

---

## Budget anchor (v2 brief)

| Bucket | Hours | Notes |
|---|---|---|
| Cloud / AI engineer hours | **545.5** | David Kokkilic + Ahmet Fatih Cengiz |
| Solution Architect | **50** | drawn down on demand |
| **Total funded** | **595.5** | Microsoft via Deop; $0 to sweetspot |

Hours below are cloud/AI engineer hours only (the 545.5 bucket).

---

## A. Launch backlog — by Story

### EPIC 1 — Sprint 1 (PR 9), shipped

| Task | Title | Status | Hours | Source |
|---|---|---|---|---|
| 1.1.x | AI project structure + DI | shipped | ~10 | Story 1.1 |
| 1.2.1 | IAiClient + AnthropicAiClient | shipped | ~16 | Story 1.2 |
| 1.2.2 | Polly retry + fallback | shipped | ~12 | Story 1.2 |
| 1.2.3 | FluentValidation schema retry | shipped | ~12 | Story 1.2 |
| 1.2.4 | PII + banned-content filter | shipped | ~14 | Story 1.2 |
| 1.2.5 | Azure Foundry adapter | shipped | ~16 | Story 1.2 (launch-blocking) |
| 1.3.1 | ai_usage migration | shipped | ~6 | Story 1.3 |
| 1.3.2 | Usage logger | shipped | ~8 | Story 1.3 |
| 1.3.3 | Spend-cap enforcer | shipped | ~10 | Story 1.3 |
| 1.3.4 | Content-filter outcome persistence | shipped | ~6 | Story 1.3 |
| 1.4.1 | IContextBlock base | shipped | ~4 | Story 1.4 |
| 1.4.2 | BrandContextBlock + reader seam | shipped | ~10 | Story 1.4 |
| 1.4.3 | OrgContextBlock | shipped | ~8 | Story 1.4 |
| 1.4.4 | IndustryContextBlock | shipped | ~6 | Story 1.4 |
| 1.5.1 | Email-generate migration | shipped | ~16 | Story 1.5 |
| 1.5.2 | System/template field tags seed | shipped | ~6 | Story 1.5 |
| 1.6.1 | Multi-tenant isolation (Tenancy/) | shipped | ~12 | Story 1.6 |
| 1.7.1 | Prompt management base | shipped | ~8 | Story 1.7 |
| **EPIC 1 subtotal** | | **shipped** | **~180h** | |

### EPIC 1 — Story 1.8 §5.10 Hotfix track

| Task | Title | Status | Hours | Source |
|---|---|---|---|---|
| 1.8.5 | industry_template_configs + reader | shipped | ~10 | Story 1.8 |
| 1.8.1 | Account schema gap (7 columns + FK) | shipped | ~10 | v2 §5.10 (org setup 8h base + 2h promote) |
| 1.8.2 | organisation_profile + voice_samples data layer | shipped | ~14 | v2 §5.10 (profile 14h) |
| 1.8.3 | KB tables + Foundry embedding adapter | shipped | ~14 | v2 §5.10 (KB 8h) + adapter premium |
| 1.8.4 | brand_settings coordination (read-only) | planned | ~2 | Click ownership; Deop-side trivial |
| 1.8.6 | Organisation-setup BFF endpoint | planned | **8** | follow-up to 1.8.1 |
| 1.8.7 | Organisation-profile + voice-samples BFF | planned | **14** | follow-up to 1.8.2 |
| 1.8.8 | KB document upload + ingest workflow + search BFF | planned | **16** | follow-up to 1.8.3 + v2 §5.8 |
| 1.8.9 | HNSW similarity index | planned | **4** | perf gate, dim decision dependent |
| **Story 1.8 subtotal** | | mixed | **shipped ~48h + planned ~44h** | |

### EPIC 2 — Sprint 2 (PR 10)

| Task | Title | Status | Hours |
|---|---|---|---|
| 2.1.1 | Unified email generation service | planned | 10 |
| 2.1.2 | Context type refactoring | planned | 6 |
| 2.1.3 | BFF endpoint | planned | 8 |
| 2.2.1 | AIEmailModal refactor | planned | 10 |
| 2.2.2 | Journey editor wire-up | planned | 6 |
| **EPIC 2 subtotal** | | planned | **40h** |

### EPIC 3 — Sprint 3 (PR 11 + PR 11p)

| Task | Title | Status | Hours |
|---|---|---|---|
| 3.1.1 | Product agent definition (Web Agent only) | planned | 4 |
| 3.2.1 | Field-tagging settings page | planned | 12 |
| 3.2.2 | 3-tier tag rendering | planned | 10 |
| 3.2.3 | AI tag suggestion endpoint | planned | 10 |
| **EPIC 3 subtotal (launch portion)** | | planned | **36h** |
| 3.1.2 | Confirmation Email → Journey | _v1.1_ | — |
| 3.1.3 | Web Agent runtime narrowing | _v1.1_ | — |

### Story 1.9 — Launch Context Blocks + Form Generation (parallel Sprints 3-4)

| Task | Title | Hours |
|---|---|---|
| 1.9.1 | Form generation feature (basic) | 12 |
| 1.9.2 | ProfileContextBlock | 6 |
| 1.9.3 | EventContextBlock | 6 |
| 1.9.4 | BriefContextBlock | 6 |
| 1.9.5 | ContactFieldsContextBlock | 8 |
| **Story 1.9 subtotal** | | **38h** |

### EPIC 4 — Sprint 4 (PR 12 split, launch parts only)

| Task | Title | Status | Hours |
|---|---|---|---|
| 4.2.1 | Field-Semantics ContextBlock | promoted | 10 |
| 4.2.2 | Audience ContextBlock | promoted | 12 |
| 4.3.2 | Knowledge ContextBlock (consumes 1.8.3 adapter) | promoted | 10 |
| 4.5.1 | Composition Registry | promoted | 14 |
| 4.6.5a | Knowledge wiring (launch portion of 4.6.5) | split-launch | 6 |
| 4.6.7 | Feature Key + Invariant Registry | promoted | 12 |
| **EPIC 4 subtotal (launch portion)** | | planned | **64h** |

### Story 1.10 — Launch Readiness Documentation (Sprint 1 + Sprint 4)

| Task | Title | Hours |
|---|---|---|
| 1.10.1 | /AI/README.md handover doc | 8 |
| 1.10.2 | Foundry model spike + memo | 4 |
| 1.10.3 | §5.10 hour sign-off (this document) | 2 |
| **Story 1.10 subtotal** | | **14h** |

### Pre-Launch Verification Gates (Sprint 5 + Test & Polish)

| Gate | Title | Hours |
|---|---|---|
| 5.3.1 | Observability verification | 4 |
| 5.3.2 | GDPR compliance check | 4 |
| **Verification gates subtotal** | | **8h** |

---

## B. Hour summary — launch backlog

| Bucket | Hours |
|---|---|
| EPIC 1 shipped (Sprint 1 PR 9 baseline) | ~180h |
| Story 1.8 shipped | ~48h |
| **Shipped subtotal** | **~228h** |
| Story 1.8 planned (1.8.4/6/7/8/9) | ~44h |
| EPIC 2 (Sprint 2) | 40h |
| EPIC 3 launch portion (Sprint 3) | 36h |
| Story 1.9 (Sprints 3-4 parallel) | 38h |
| EPIC 4 launch portion (Sprint 4) | 64h |
| Story 1.10 (Sprint 4) | 14h |
| Pre-Launch Verification Gates (Sprint 5 + T&P) | 8h |
| **Planned subtotal** | **244h** |
| **Launch backlog grand total** | **~472h** |

Remaining headroom against 545.5h budget: **~73.5h** (~13% buffer).

---

## C. v1.1 demoted task hours (freed budget)

| Task | Title | Original estimate | Freed |
|---|---|---|---|
| 3.1.2 | Confirmation Email → Journey | ~16h | ✅ |
| 3.1.3 | Web Agent Runtime Narrowing | ~12h | ✅ |
| 4.1.1 | Methodology ContextBlock | ~8h | ✅ |
| 4.1.2 | Plan ContextBlock | ~6h | ✅ |
| 4.3.1 | Insights ContextBlock | ~8h | ✅ |
| 4.4.1 | Assets ContextBlock | ~8h | ✅ |
| 4.6.1 (refinement portion) | Forms v2 refinement | ~8h | ✅ |
| 4.6.2 | Forms v2 field mapping | ~12h | ✅ |
| 4.6.3 | Landing page wiring | ~16h | ✅ |
| 4.6.4 | Events Create-with-AI wiring | ~14h | ✅ |
| 4.6.5b (Web Agent runtime portion) | Web Agent runtime + chat | ~10h | ✅ |
| 4.6.6 | Profile research / Insights ask / Social / Inbound contracts | ~16h | ✅ |
| EPIC 5 (Stories 5.1 + 5.2) | Recommendation handlers + Today page | ~80h | ✅ |
| **v1.1 freed total** | | **~214h** | |

The 214h freed by v1.1 demotions absorbs the 44h of new §5.10 follow-up tasks + 38h Story 1.9 + 14h Story 1.10 (= 96h new launch work) with **~118h surplus** still available for buffer / Solution Architect coordination / Test & Polish remediation.

---

## D. Sign-off conclusion

**Launch fits within 545.5h budget.** Net delta vs original (pre-v2-reclassification) plan:
- Removed from launch: ~214h (v1.1 demotions)
- Added to launch: ~96h (1.8 follow-ups + Stories 1.9 + 1.10)
- **Net reduction in launch hours: ~118h** — released as buffer

Recommendation: keep buffer reserved for (a) Foundry rate-limit remediation on KB ingest, (b) Click coordination on brand_settings + form/event confirmation, (c) Pre-Launch Verification Gate remediation in Test & Polish.

**Open follow-up:** Solution Architect 50h budget tracked separately; this document does not enumerate. SA hours expected to be spent on Foundry decisions, dimensions decision (1.8.9 / 1.10.2), and verification-gate sign-off.

---

## E. References

- v2 scope brief: `sweetspot-ai-deop-scope-brief-v2.docx` §5 + §5.10
- Scope doc: `docs/ai-arch-scope.md` (commit `2a59cf4` on planning hub `main`)
- Story 1.8 execution: `deop/integration` of `repostories/sweetspot/` (commits `165e533e8`, `1b02bdded`, `7f4106bad`, `77df28121`, merge `93ae58617`)
- Story 1.9 + 1.10 + Story 1.8 follow-up issues: GitHub Issues #81-#95
