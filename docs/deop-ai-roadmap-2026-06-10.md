# Deop AI Roadmap Alignment — 2026-06-10

## Purpose

This report aligns the Sweetspot planning roadmap with the Deop Azure AI Foundry handover and the Brand Kit / Assets handoff. It is a roadmap view, not an implementation PR.

## Decisions Applied

1. Phase 1 continues with the provider-agnostic `IAiClient` contract. Anthropic direct remains the current launch-provider assumption unless Azure AI Foundry becomes an explicit launch dependency.
2. Brand Kit is consumed through `BrandContext`. Tonal fields go into prompts. Visual fields go to deterministic renderers.
3. Assets are consumed as enriched metadata only. Raw files and semantic asset search are out of scope until embeddings / pgvector exist.
4. Product agent taxonomy is now explicit: **Web Agent is the only customer-facing agent type**.
5. Form/event "agents" are legacy handler names. Their confirmation-email work moves to journeys.
6. Strategy, insights, form, landing-page, event, profile, social, and inbound-classification AI work are workflows/generators/classifiers, not product agents.

## Roadmap Changes

### Sprint 1 / PR 9

Foundation remains valid. The prior work is not dead.

Required emphasis:

- Spend cap must block before provider invocation.
- Content-filter outcomes must be persisted, not only computed.
- Azure AI Foundry migration is tracked as `Task 1.2.5: Azure AI Foundry Provider Adapter` — GitHub #80, not hidden inside context blocks.
- Context blocks must use a typed `Exists` convention and `ToPromptString()`.
- Brand visual fields must not be dumped into prompts.

### Sprint 3 / PR 11

Renamed from agent migration to Web Agent cleanup plus form/event confirmation migration.

Expected result:

- No customer-facing Form Agent.
- No customer-facing Event Agent.
- Confirmation emails are journey email steps.
- Web Agent / inbox conversation handling is the only remaining agent-style runtime.

### Sprint 4 / PR 12

Expanded from context blocks only to context blocks plus AI surface parity wiring.

New visible story:

- `Story 4.6: Prototype AI Surface Parity Wiring` — GitHub #72

New tasks:

- `Task 4.6.1: Forms v2 Generation + Refinement Wiring` — GitHub #73
- `Task 4.6.2: Forms v2 Field Mapping Wiring` — GitHub #74
- `Task 4.6.3: Landing Page Generation, Refinement, and Layout Switching Wiring` — GitHub #75
- `Task 4.6.4: Events Create-with-AI Surface Contract` — GitHub #76
- `Task 4.6.5: Web Agent Context and Knowledge Wiring` — GitHub #77
- `Task 4.6.6: Profile Research, Insights Ask, Social Generate, and Inbound Classification Contracts` — GitHub #78
- `Task 4.6.7: AI Feature Key and Invariant Registry` — GitHub #79

## Next Steps From Current Position

1. Finish Story 1.4 using the revised Brand / Org / Industry context contracts.
2. Keep Story 1.3 open until spend-cap enforcement and persisted content-filter outcomes are implemented.
3. Keep Azure AI Foundry as a provider-adapter task unless it is explicitly promoted to launch dependency.
4. Do not build multiple agent product surfaces. Use Web Agent only.
5. When reaching PR 12, use Story 4.6 as the Deop parity checklist before PR 13 starts.
6. Before PR 13, confirm which Story 4.6 surfaces are launch-critical and which are explicit post-launch deferrals.

## Risk Notes

- The roadmap is now more honest but heavier. PR 12 is the pressure point.
- Forms v2 and landing pages were previously easy to miss because they were only mentioned in composition tables.
- Deop handover treats prototype behaviour as the contract; if the team cannot deliver all surfaces by launch, the deferral must be explicit.
- Azure AI Foundry remains a provider decision, not something hidden inside context-block work.
