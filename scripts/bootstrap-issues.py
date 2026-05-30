#!/usr/bin/env python3
"""Bootstrap Epic/Story/Task issues for the Sweetspot AI Architecture planning repo.

Reads inline data extracted from docs/ai-arch-scope.md and creates the full
three-level hierarchy via the GitHub REST API (sub_issues endpoint, GA 2025).

Usage:
    python3 scripts/bootstrap-issues.py                # do it
    python3 scripts/bootstrap-issues.py --dry-run      # print what would happen

Requirements:
    - gh CLI authenticated as a user with write access to the repo
    - Labels and milestones already created (run bootstrap-labels.sh and
      bootstrap-milestones.sh first)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

REPO = "david-kokkilic-sweetspot/sweetspot-platform"


# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

# Each epic has: title, body, labels, milestone, stories[]
# Each story has: title, body, labels, milestone, tasks[]
# Each task has: title, body (with subtasks as markdown checkboxes), labels, milestone
#
# Body strings use plain markdown. Cross-references use #N placeholders that are
# left for humans to fill in after creation — the issue numbers aren't known in
# advance, and that level of cross-linking is well-served by the Tasks/Sub-issues
# UI once everything exists.

def task(tid, title, subtasks, labels, milestone, depends=None, body_extra=""):
    sub_md = "\n".join(f"- [ ] {s}" for s in subtasks)
    dep = f"\n\n**Depends on:** {depends}" if depends else ""
    extra = f"\n\n{body_extra}" if body_extra else ""
    body = (
        f"_Source: docs/ai-arch-scope.md — Task {tid}_\n\n"
        f"## Subtasks\n{sub_md}"
        f"{dep}{extra}"
    )
    return {"title": f"Task {tid}: {title}", "body": body, "labels": labels, "milestone": milestone}


def story(sid, title, body_intro, tasks, labels, milestone):
    body = (
        f"_Source: docs/ai-arch-scope.md — Story {sid}_\n\n"
        f"{body_intro}\n\n"
        f"## Tasks\nTracked as sub-issues (see Sub-issues panel)."
    )
    return {"title": f"Story {sid}: {title}", "body": body, "labels": labels, "milestone": milestone, "tasks": tasks}


def epic(eid, title, sprint_range, prs, customer_visible, intro, stories, sprint_label, milestone, extra_labels=None):
    pr_labels = [f"pr:{p}" for p in prs]
    labels = ["type:epic", sprint_label, f"customer-visible:{customer_visible}"] + pr_labels + (extra_labels or [])
    body = (
        f"_Source: docs/ai-arch-scope.md — EPIC {eid}_\n\n"
        f"**Sprint:** {sprint_range}  \n"
        f"**PRs:** {', '.join('PR ' + p for p in prs)}  \n"
        f"**Customer-visible:** {customer_visible}\n\n"
        f"## Goal\n{intro}\n\n"
        f"## Stories\nTracked as sub-issues (see Sub-issues panel)."
    )
    return {"title": f"Epic {eid}: {title}", "body": body, "labels": labels, "milestone": milestone, "stories": stories}


# Label bundles
def slabels(sprint, prs, extra=None):
    return ["type:story", f"sprint:{sprint}"] + [f"pr:{p}" for p in prs] + (extra or [])


def tlabels(sprint, pr, extra=None):
    return ["type:task", f"sprint:{sprint}", f"pr:{pr}"] + (extra or [])


M1 = "Sprint 1 — PR 9"
M2 = "Sprint 2 — PR 10"
M3 = "Sprint 3 — PR 11 + PR 11p"
M4 = "Sprint 4 — PR 12"
M5 = "Sprint 5 — PR 13 + PR 14"


EPICS = [
    epic(
        eid="1",
        title="AI Foundation & Client Wrapper",
        sprint_range="Sprint 1 (Jun 1 – Jun 13 2026)",
        prs=["9"],
        customer_visible="no",
        intro="Set up the AI layer skeleton in the .NET backend. Ship the full client wrapper (logging, retry, validation, content filtering, cost calc), usage logging schema, first 3 context blocks (brand/org/industry), email-generate proof of pattern, multi-tenant isolation, and prompt management.",
        sprint_label="sprint:1",
        milestone=M1,
        stories=[
            story("1.1", "Create AI Project Structure",
                  "Set up the AI layer skeleton within the .NET backend.",
                  labels=slabels(1, ["9"]), milestone=M1, tasks=[
                      task("1.1.1", "Create AI Domain Project", [
                          "Create AI/ namespace structure under src/backend/Core/",
                          "Set up folder structure: Client/, Prompts/, Context/, Knowledge/, Agents/, Schemas/, Usage/",
                          "Create DI registration classes (AddAiServices())",
                      ], labels=tlabels(1, "9"), milestone=M1),
                      task("1.1.2", "AI Configuration Setup", [
                          "Define AI_PROVIDER, AI_REGION, AI_MODEL_DEFAULT environment variables",
                          "Create AiOptions configuration class (provider, region, model defaults, cost tables)",
                          "Per-feature model selection config (Sonnet vs Haiku mapping)",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.1.1"),
                  ]),
            story("1.2", "Client Wrapper Service (IAiClient)",
                  "Central service through which all AI calls flow.",
                  labels=slabels(1, ["9"]), milestone=M1, tasks=[
                      task("1.2.1", "IAiClient Interface & Implementation", [
                          "Define IAiClient interface: Generate({ feature, system, messages, modelClass }) → { content, usage, metadata }",
                          "AnthropicAiClient concrete implementation (Anthropic SDK)",
                          "Provider-agnostic internal contract (cost translation, filtering, retry, validation)",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.1.2"),
                      task("1.2.2", "Retry & Error Handling", [
                          "Transient failure retry with exponential backoff (Polly)",
                          "Permanent failure graceful degradation (template-based fallback)",
                          "Errors are never swallowed, structured logging",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.2.1"),
                      task("1.2.3", "Output Validation", [
                          "Schema-based output validation (C# record types + FluentValidation)",
                          "Parse → validate → retry with corrective prompting on failure",
                          "After 2 failures → typed error return",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.2.1"),
                      task("1.2.4", "Content Filtering", [
                          "PII detection in outputs",
                          "Banned-content checks (profanity, regulated-topic)",
                          "Redaction logging (what was filtered and why)",
                          "Customer-configurable thresholds",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.2.1"),
                  ]),
            story("1.3", "Usage Logging & Cost Tracking",
                  "Mandatory logging on every AI call.",
                  labels=slabels(1, ["9"]), milestone=M1, tasks=[
                      task("1.3.1", "ai_usage Schema Migration", [
                          "Create EF Core migration: add columns user_id, model, latency_ms, success, error_message, created_at",
                          "Add columns: prompt_hash, output_hash, consent_status, data_residency_region, trace_id, content_filter_outcome",
                          "Vendor-neutral SQL (no Supabase-specific syntax)",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.1.1"),
                      task("1.3.2", "Usage Log Service", [
                          "IAiUsageLogger service: log org_id, user_id, feature, model, tokens in/out, cost, latency, success/failure on every call",
                          "Cost calculation service (per-provider pricing tables)",
                          "trace_id audit linkage",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.3.1, Task 1.2.1"),
                  ]),
            story("1.4", "First 3 Context Blocks (brand, org, industry)",
                  "Minimal context blocks needed for email-generate proof.",
                  labels=slabels(1, ["9"]), milestone=M1, tasks=[
                      task("1.4.1", "Context Block Base", [
                          "IContextBlock<T> interface: LoadBlockContextAsync(orgId, options?) → structured context object",
                          "ToPromptString() method on context objects",
                          "Graceful degradation: missing/sparse data → empty stub, never throw",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.1.1"),
                      task("1.4.2", "Brand Context Block", [
                          "Load brand info from brand_settings + color_roles JSONB",
                          "Brand tonality, voice, visual identity access",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.4.1"),
                      task("1.4.3", "Org Context Block", [
                          "Load org info from organizations table",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.4.1"),
                      task("1.4.4", "Industry Context Block", [
                          "Load industry info from industry_template_configs table",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.4.1"),
                  ]),
            story("1.5", "Email-Generate Proof of Pattern",
                  "Run existing email-generate through the new architecture with byte-identical output.",
                  labels=slabels(1, ["9"]), milestone=M1, tasks=[
                      task("1.5.1", "Email-Generate Migration", [
                          "Analyze existing email-generate endpoint",
                          "Re-implement via new client wrapper + context blocks",
                          "Byte-identical output verification (side-by-side test)",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.2.1, Task 1.4.2, Task 1.4.3, Task 1.4.4"),
                      task("1.5.2", "System/Template Field Tags Seed", [
                          "Seed 11 system fields with universal defaults",
                          "Template fields per industry seed framework",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.3.1"),
                  ]),
            story("1.6", "Multi-Tenant Isolation (AI Layer)",
                  "Tenant isolation for AI tables.",
                  labels=slabels(1, ["9"]), milestone=M1, tasks=[
                      task("1.6.1", "Tenant Scoping", [
                          "org_id scope enforcement on all AI tables",
                          "Wrapper reads org_id from authenticated session",
                          "Application-layer tenant filtering",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.2.1, Task 1.3.1"),
                  ]),
            story("1.7", "Prompt Management",
                  "Prompts stored in dedicated files/classes, not inline.",
                  labels=slabels(1, ["9"]), milestone=M1, tasks=[
                      task("1.7.1", "Prompt Storage", [
                          "Per-feature system prompt classes in Prompts/",
                          "Code review checklist prohibiting inline prompts",
                      ], labels=tlabels(1, "9"), milestone=M1, depends="Task 1.1.1"),
                  ]),
        ],
    ),

    epic(
        eid="2",
        title="Unified Email-Content Component",
        sprint_range="Sprint 2 (Jun 16 – Jun 27 2026)",
        prs=["10"],
        customer_visible="yes",
        intro="All branded email generation flows through a single function. Extract AIEmailModal as a shared Angular component. Build unified backend endpoint, wire into journey editor, ship context-aware CTA. Decision checkpoint at Week 4: is the unified component working as keystone?",
        sprint_label="sprint:2",
        milestone=M2,
        extra_labels=["checkpoint:week-4"],
        stories=[
            story("2.1", "Backend Unified Email Endpoint",
                  "All branded email generation from a single endpoint.",
                  labels=slabels(2, ["10"]), milestone=M2, tasks=[
                      task("2.1.1", "Unified Email Generation Service", [
                          "Implement GenerateBrandedEmail({ intent, context, cta?, structuralOptions? }) service",
                          "Support 3 consumers: email editor, journey editor, recommendation action handler",
                          "Headless caller support (API call without rendering modal/UI)",
                      ], labels=tlabels(2, "10"), milestone=M2, depends="PR 9"),
                      task("2.1.2", "Context Type Refactoring", [
                          "Replace emailId with discriminated context: campaign_email | journey_step | standalone",
                          "Context-aware CTA: journey_step + eventId → event registration URL pre-fill",
                          "standalone → user provides or toggles off",
                      ], labels=tlabels(2, "10"), milestone=M2, depends="Task 2.1.1"),
                      task("2.1.3", "BFF Endpoint", [
                          "Create unified email endpoint under src/backend/Core/BackendForFrontend/",
                          "Load context blocks based on kind, compose prompt, call client wrapper",
                      ], labels=tlabels(2, "10"), milestone=M2, depends="Task 2.1.1, Task 2.1.2"),
                  ]),
            story("2.2", "Angular Email Component Extraction",
                  "Extract existing ~300-line AIEmailModal to shared/reusable component.",
                  labels=slabels(2, ["10"]), milestone=M2, tasks=[
                      task("2.2.1", "AIEmailModal Component Refactoring", [
                          "Analyze existing component",
                          "Move to shared component under src/frontend/src/app/shared/",
                          "Update email editor and journey editor integrations",
                      ], labels=tlabels(2, "10"), milestone=M2, depends="Task 2.1.3"),
                      task("2.2.2", "Journey Editor Wire-up", [
                          "Call unified email component from journey editor",
                          "Auto-populate journey step context",
                          "E2E test: journey → AI email generation flow",
                      ], labels=tlabels(2, "10"), milestone=M2, depends="Task 2.2.1"),
                  ]),
        ],
    ),

    epic(
        eid="3",
        title="Agent Migration & Field-Tagging UI",
        sprint_range="Sprint 3 (Jun 30 – Jul 11 2026)",
        prs=["11", "11p"],
        customer_visible="partial",
        intro="Form/event agents stop sending confirmation emails — journeys take over. Agent runtime narrowed to inbound replies. HTML duplication removed. In parallel, ship field-tagging UI: settings page with 3-tier tag rendering, AI suggestion for custom fields, readiness percentage.",
        sprint_label="sprint:3",
        milestone=M3,
        stories=[
            story("3.1", "Form/Event Agent Migration",
                  "Agents stop sending confirmation emails → journeys take over.",
                  labels=slabels(3, ["11"]), milestone=M3, tasks=[
                      task("3.1.1", "Agent Redefinition", [
                          'Apply "Agent" = multi-step, conversational, decision-making entity definition',
                          "Reclassify single-call email senders as handlers/generators",
                      ], labels=tlabels(3, "11"), milestone=M3, depends="PR 10"),
                      task("3.1.2", "Confirmation Email → Journey Migration", [
                          "Move form-agent and event-agent creation logic to journeys",
                          "Journey's first step = confirmation email",
                          "Implement .ics attachment as journey-email feature",
                      ], labels=tlabels(3, "11"), milestone=M3, depends="Task 3.1.1"),
                      task("3.1.3", "Agent Runtime Narrowing", [
                          "Narrow agent runtime: inbound reply handling, multi-turn, registration context only",
                          "Remove HTML generation duplication (email-generate / form-agent / event-agent)",
                          'Simplify agents to "enrol in journey + open inbound thread"',
                      ], labels=tlabels(3, "11"), milestone=M3, depends="Task 3.1.2"),
                  ]),
            story("3.2", "Field-Tagging UI (Settings Page)",
                  "UI for tagging contact fields with semantic labels.",
                  labels=slabels(3, ["11p"]), milestone=M3, tasks=[
                      task("3.2.1", "Field-Tagging Settings Page", [
                          "Create dedicated Angular settings page (/settings/ai-ready equivalent)",
                          "Prominently display readiness percentage",
                          "v1 vocabulary: 8 controlled semantic tags with CHECK constraint",
                      ], labels=tlabels(3, "11p"), milestone=M3, depends="PR 9"),
                      task("3.2.2", "3-Tier Tag Rendering", [
                          "System fields (11): read-only, pre-tagged, universal defaults",
                          "Template fields (per industry): read-only, pre-tagged",
                          "Custom fields: interactive + AI suggestion",
                      ], labels=tlabels(3, "11p"), milestone=M3, depends="Task 3.2.1"),
                      task("3.2.3", "AI Tag Suggestion", [
                          "AI-powered tag suggestion for custom fields",
                          "User accepts or overrides suggestion",
                          "Update ai_suggested_tags in contact_field_definitions table",
                      ], labels=tlabels(3, "11p"), milestone=M3, depends="Task 3.2.2"),
                  ]),
        ],
    ),

    epic(
        eid="4",
        title="Remaining Context Blocks",
        sprint_range="Sprint 4 (Jul 14 – Jul 25 2026)",
        prs=["12"],
        customer_visible="no",
        intro="Build the remaining 7 context block services: methodology, plan, field-semantics, audience, insights, knowledge (generalised from chat-only to all features), assets. Wire up feature → block composition registry. Decision checkpoint at Week 8: has field-tagging UI shipped and are users tagging?",
        sprint_label="sprint:4",
        milestone=M4,
        extra_labels=["checkpoint:week-8"],
        stories=[
            story("4.1", "Methodology & Plan Context Blocks",
                  "Load marketing methodology and plan contexts.",
                  labels=slabels(4, ["12"]), milestone=M4, tasks=[
                      task("4.1.1", "Methodology Context Block", [
                          "Load data from marketing_disciplines, goal_types, programmes, tag_labels tables",
                          "Graceful degradation",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="PR 9 (context block base)"),
                      task("4.1.2", "Plan Context Block", [
                          "Load data from marketing_plans + plan_goals + plan_programmes tables",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="PR 9"),
                  ]),
            story("4.2", "Field-Semantics & Audience Context Blocks",
                  "Load contact field semantics and audience context.",
                  labels=slabels(4, ["12"]), milestone=M4, tasks=[
                      task("4.2.1", "Field-Semantics Context Block", [
                          "Load semantic data from contact_field_definitions extension columns",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="PR 11p (field tags populated)"),
                      task("4.2.2", "Audience Context Block", [
                          "Build audience context from audiences + audience_contacts + field-semantics block",
                          "audience_contexts materialized view/table schema migration",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="Task 4.2.1"),
                  ]),
            story("4.3", "Insights & Knowledge Context Blocks",
                  "Cross-org benchmarks and knowledge base integration.",
                  labels=slabels(4, ["12"]), milestone=M4, tasks=[
                      task("4.3.1", "Insights Context Block", [
                          "Cross-org aggregate benchmarks (privacy-respecting)",
                          'Minimum-N threshold (5-10) — below threshold → return "n/a"',
                          "Cross-org reporting via separate service-role view",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="PR 9"),
                      task("4.3.2", "Knowledge Context Block", [
                          "KB tables — per-org + curated content",
                          "Vector search Top-K, filter by org_id",
                          "Scope enforcement in retrieval function, not caller",
                          "Generalize knowledge block from chat-only to all features",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="PR 9"),
                  ]),
            story("4.4", "Assets Context Block",
                  "Include content assets in AI context.",
                  labels=slabels(4, ["12"]), milestone=M4, tasks=[
                      task("4.4.1", "Assets Context Block", [
                          "Load AI-tagged assets from content_assets table",
                          "Include asset metadata + tag info in context",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="PR 9"),
                  ]),
            story("4.5", "Feature → Block Composition Wiring",
                  "Implement which blocks compose for each feature.",
                  labels=slabels(4, ["12"]), milestone=M4, tasks=[
                      task("4.5.1", "Composition Registry", [
                          "Feature → blocks mapping registry (email-generate, journey-content, form-generate, chat, strategy, insights, recommendation)",
                          "Dynamic block loading based on feature configuration",
                      ], labels=tlabels(4, "12"), milestone=M4, depends="Tasks 4.1.1, 4.1.2, 4.2.2, 4.3.1, 4.3.2, 4.4.1"),
                  ]),
        ],
    ),

    epic(
        eid="5",
        title="Recommendation Actions & Command Centre",
        sprint_range="Sprint 5 (Jul 28 – Aug 15 2026)",
        prs=["13", "14"],
        customer_visible="yes",
        intro='"Build the campaign" action creates real audiences + journeys + AI content. Phase 2 trust progression live. Segment-level hyperpersonalisation. Confidence labelling (Counted vs Suggested). Preview-and-confirm. Today page + Retain dashboard + command palette. Decision checkpoint at Week 10: is recommendation→action producing acceptable content?',
        sprint_label="sprint:5",
        milestone=M5,
        extra_labels=["checkpoint:week-10", "phase:2"],
        stories=[
            story("5.1", "Recommendation Action Handlers",
                  '"Build the campaign" action creates real audiences, journeys, and AI content.',
                  labels=slabels(5, ["13"]), milestone=M5, tasks=[
                      task("5.1.1", "Recommendation Action Schema", [
                          "Add to recommendation_actions: ai_call_trace_id, action_journey_id, action_audience_id",
                          "Add to ai_recommendations: confidence_type, source_signal_id, plan_goal_id, programme_id",
                          "EF Core migration",
                      ], labels=tlabels(5, "13"), milestone=M5, depends="PR 12"),
                      task("5.1.2", "Action Handler Implementation", [
                          '"Build the campaign" action → create real audience',
                          "Create journey with AI content (via unified email component)",
                          "Segment-level hyperpersonalisation (Phase 2): different copy per audience segment",
                      ], labels=tlabels(5, "13", ["phase:2"]), milestone=M5, depends="Task 5.1.1, PR 10"),
                      task("5.1.3", "Confidence Labelling", [
                          'Rules-based = "Counted", AI-generated = "Suggested" distinction',
                          "Display confidence type on recommendation card",
                      ], labels=tlabels(5, "13"), milestone=M5, depends="Task 5.1.2"),
                      task("5.1.4", "Preview-and-Confirm Flow", [
                          "One-click never sends directly",
                          "Preview: audience preview + journey/campaign template + projected impact",
                          "Audit-trail entry on every commit",
                      ], labels=tlabels(5, "13"), milestone=M5, depends="Task 5.1.2"),
                  ]),
            story("5.2", "Today Page (Command Centre)",
                  "Insights revamp customer-facing surfaces.",
                  labels=slabels(5, ["14"]), milestone=M5, tasks=[
                      task("5.2.1", "Today Page (Insights Command Centre)", [
                          "Implement new IA: Today (command centre) / Grow / Engage / Retain / Earn",
                          "Angular routing + page structure",
                      ], labels=tlabels(5, "14"), milestone=M5, depends="PR 13"),
                      task("5.2.2", "Recommendation Cards", [
                          "Insight + Recommendation + Action fused single card component",
                          "Confidence labelling display (Counted vs Suggested)",
                          "Action buttons (preview-and-confirm flow integration)",
                      ], labels=tlabels(5, "14"), milestone=M5, depends="Task 5.2.1, Task 5.1.3"),
                      task("5.2.3", "Retain Dashboard", [
                          "Retain dashboard implementation",
                          "Retention metrics + recommendation integration",
                      ], labels=tlabels(5, "14"), milestone=M5, depends="Task 5.2.1"),
                      task("5.2.4", "Command Palette", [
                          "Quick-action command palette",
                          "Keyboard shortcuts",
                      ], labels=tlabels(5, "14"), milestone=M5, depends="Task 5.2.1"),
                  ]),
            story("5.3", "Launch Readiness — Observability & Compliance",
                  "Pre-launch observability and compliance checklist.",
                  labels=slabels(5, ["14"]), milestone=M5, tasks=[
                      task("5.3.1", "Observability Verification", [
                          "Verify cost tracking per org/feature/month",
                          "Verify latency tracking per feature",
                          "Verify validation retry logging",
                          "Verify trace_id audit linkage end-to-end",
                      ], labels=tlabels(5, "14"), milestone=M5, depends="PR 13"),
                      task("5.3.2", "GDPR Compliance Check", [
                          "Mandatory GDPR requirements checklist",
                          "Verify PII detection in outputs",
                          "Verify content filtering and redaction logging",
                      ], labels=tlabels(5, "14"), milestone=M5, depends="Task 5.3.1"),
                  ]),
        ],
    ),
]


# -----------------------------------------------------------------------------
# gh CLI helpers
# -----------------------------------------------------------------------------

def gh_run(*args: str, input_data: str | None = None, check: bool = True) -> str:
    cmd = ["gh", *args]
    result = subprocess.run(cmd, input=input_data, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.stderr.write(f"gh failed: {' '.join(cmd)}\n{result.stderr}\n")
        sys.exit(1)
    return result.stdout.strip()


def create_issue(title: str, body: str, labels: list[str], milestone: str | None, dry: bool) -> int:
    if dry:
        print(f"  [DRY] would create: {title}")
        print(f"        labels: {','.join(labels)}")
        print(f"        milestone: {milestone}")
        return 0
    args = ["issue", "create", "--repo", REPO, "--title", title, "--body", body]
    for label in labels:
        args.extend(["--label", label])
    if milestone:
        args.extend(["--milestone", milestone])
    url = gh_run(*args)
    return int(url.rsplit("/", 1)[-1])


def link_subissue(parent_no: int, child_no: int, dry: bool) -> None:
    if dry:
        print(f"  [DRY] would link #{child_no} as sub-issue of #{parent_no}")
        return
    child_json = gh_run("api", f"repos/{REPO}/issues/{child_no}")
    child_db_id = json.loads(child_json)["id"]
    gh_run(
        "api",
        f"repos/{REPO}/issues/{parent_no}/sub_issues",
        "-X", "POST",
        "-F", f"sub_issue_id={child_db_id}",
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def count_totals() -> tuple[int, int, int]:
    e = len(EPICS)
    s = sum(len(ep["stories"]) for ep in EPICS)
    t = sum(len(st["tasks"]) for ep in EPICS for st in ep["stories"])
    return e, s, t


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = parser.parse_args()

    e, s, t = count_totals()
    print(f"Will create: {e} Epics, {s} Stories, {t} Tasks in {REPO}")
    if args.dry_run:
        print("(dry run)")
    print()

    for ep in EPICS:
        epic_no = create_issue(ep["title"], ep["body"], ep["labels"], ep["milestone"], args.dry_run)
        print(f"Epic #{epic_no}: {ep['title']}")
        for st in ep["stories"]:
            story_no = create_issue(st["title"], st["body"], st["labels"], st["milestone"], args.dry_run)
            link_subissue(epic_no, story_no, args.dry_run)
            print(f"  Story #{story_no}: {st['title']}")
            for tk in st["tasks"]:
                task_no = create_issue(tk["title"], tk["body"], tk["labels"], tk["milestone"], args.dry_run)
                link_subissue(story_no, task_no, args.dry_run)
                print(f"    Task #{task_no}: {tk['title']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
