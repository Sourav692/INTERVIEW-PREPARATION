# DevRev System Design Round — Study Guide

**Scope:** every document across the three prep projects (`enterprise_rag_platform`, `agent_platform`,
`delivery_framework_platform`) plus `cross_cutting_prep/`, read in the order that builds understanding
correctly — architecture and access control first, then cross-cutting concerns that assume you already
have that vocabulary, then the lower-priority third project, then a final consolidation pass.

**Deliberately excluded:** every `.ipynb` notebook in every project (`notebooks/02-hands-on.ipynb` and
its parts) — this is a system design round, not the coding round, and notebooks are execution artifacts,
not architecture reading. Also excluded from the core path (marked optional below): each project's
`03-src-modules-reference.md`-style file-by-file reference, and the Databricks-twin docs — useful for
"show me the code" follow-ups, not for building the mental model itself.

**How this maps to the source prep doc:** `DevRev-SystemDesign-Prep.docx` now has an inline
"→ Read:" pointer under nearly every bullet in §3–§8, naming exactly which document below covers it.
Use this guide to decide *reading order*; use those inline pointers while re-reading the prep doc
itself to jump straight to the right document for any one line.

---

## Phase 0 — Orientation (~30 min, do this first)

| # | Read | Covers |
| --- | --- | --- |
| 1 | `Interview_prep_guide_-_Forward_Deployed_Architect__DevRev.pdf` (parent folder) | The whole hiring process — all rounds, not just system design. Sets overall expectations. |
| 2 | `DevRev-SystemDesign-Prep.docx` §1 (The Round) and §2 (The Answer Framework) | Format, the five assessed signals, the 60-minute time budget, and the repeatable 6-step whiteboard structure. This is process, not a project — no doc maps to it, internalize it directly from the source. |
| 3 | `enterprise_rag_platform/docs/fde-first-ten-minutes.html` (open in a browser) | A field-ready checklist of clarifying questions to ask in the first ten minutes — operationalizes §2 Step 1 (Clarify and Scope). |

**Goal of this phase:** walk in knowing the 6-step structure cold, and have 3–4 clarifying questions
ready before you touch a diagram.

---

## Phase 1 — Problem Type B: Enterprise RAG with Access Control (§4)

**Why first:** ranked #2 in the prep doc's own priority order (§9), and the project with the deepest,
most-proven build in the series.

| # | Read | Covers |
| --- | --- | --- |
| 1 | `enterprise_rag_platform/README.md` | The business case — why access control is the whole problem, framed as one running example (the Vertex Financial question) |
| 2 | `enterprise_rag_platform/docs/01-theory.md` | The core theory: ABAC vs. ACL, the two-layer pre-filter/post-check trick, hybrid search, evaluation design, guardrails on the way out. Covers §4.1–§4.6 almost entirely, plus the retrieval-side half of §6.2 (prompt injection / "the LLM is never the enforcement point") |
| 3 | `enterprise_rag_platform/docs/04-security-checks-reference.md` | Every access-control rule worked through with real examples per persona — the concrete companion to §4.3's three patterns |
| 4 | `enterprise_rag_platform/docs/06-architecture-end-to-end.md` | The actual pipeline, diagrammed end to end — this is what you draw on the whiteboard for §4's reference architecture |
| 5 | `enterprise_rag_platform/docs/07-system-design-coverage-map.md` | Proven-vs-verbal checked directly against §4 — for every pointer, know whether you can demo it or only speak from the doc |
| 6 | `enterprise_rag_platform/docs/Scale_Optimization.md` | §4.6's follow-ups in depth: cost at 10M+ chunks, chunking by document format, the vector-store row of §8's trade-off table |
| 7 | `enterprise_rag_platform/docs/08-structured-data-and-connectors.md` | Extends §4.2 ingestion to structured CRM/ticketing data and connector orchestration at real scale — the sharpest DevRev-specific angle in the whole series |
| 8 | `enterprise_rag_platform/INTERVIEW_SCRIPT.md` | The rehearsed whiteboard script tying all of the above into one telling |

**Optional, only with time to spare:** `docs/03-theory-databricks.md` and
`INTERVIEW_SCRIPT_DATABRICKS.md` (the Databricks/Lakehouse twin — a real production answer to "what if
this weren't Chroma"), `docs/05-src-modules-reference.md` (code-level reference, more relevant to a
coding-round follow-up than architecture), `docs/QA.md` (your own running Q&A log — good for a last
personal skim, not first-pass reading).

---

## Phase 2 — Problem Type A: AI Agent Platform (§3)

**Why second:** ranked #3 in §9, and closest to DevRev's own product surface, so expect depth
follow-ups here specifically.

| # | Read | Covers |
| --- | --- | --- |
| 1 | `agent_platform/README.md` | The business case — three checkable safety properties instead of a slide |
| 2 | `agent_platform/docs/01-theory.md` | The project's thesis: deterministic control flow around probabilistic reasoning. Covers §3.4 directly |
| 3 | `agent_platform/docs/02-architecture-end-to-end.md` | The reference architecture, diagrammed — covers §3.2 layer by layer |
| 4 | `agent_platform/docs/04-system-design-coverage-map.md` | Proven-vs-verbal checked against §3.1, §3.2, §3.3, §3.5 — the non-technical-user problem, the determinism/control split, and likely follow-ups |
| 5 | `agent_platform/docs/05-security-tenancy-and-observability-gaps.md` | The §6/§8 material specific to agent platforms: prompt injection for tool-calling agents (the defining new threat), egress control, tenant isolation as an architecture decision, drift alerting, cost attribution, and the "default to one agent" trade-off |
| 6 | `agent_platform/INTERVIEW_SCRIPT.md` | The rehearsed whiteboard script |

**Optional:** `docs/03-src-modules-reference.md` (code reference).

---

## Phase 3 — Cross-Cutting Concerns and Agent CI/CD (§6, §7)

**Why here, not earlier:** these apply across all three projects and assume you already have the RAG
and agent-platform vocabulary in your head — read them after Phases 1–2, not before.

| # | Read | Covers |
| --- | --- | --- |
| 1 | `cross_cutting_prep/01-identity-secrets-and-tenant-fairness.md` | §6.1 (multi-tenancy, encryption, queue fairness) and the identity/secrets half of §6.2 |
| 2 | `cross_cutting_prep/02-observability-standards-and-failure-patterns.md` | §6.3 (standard tracing, dashboards, cost attribution) and §6.4 (failure handling: multi-provider failover, graceful degradation, bulkheads, a real kill switch) |
| 3 | `enterprise_rag_platform/docs/10-agent-ops-and-channels.md` | §7 (Agent CI/CD: prompt versioning, canary/shadow rollout, A/B testing) and the multi-channel-delivery half of §6.5, plus escalation-as-a-real-workflow |
| 4 | `cross_cutting_prep/03-cost-latency-cicd-rigor-and-build-vs-buy.md` | The remaining §6.5/§7/§8 items: semantic caching, token streaming, nightly regression runs, statistical rigor in A/B testing, unit-level prompt testing, and build-vs-buy as its own decision |
| 5 | `enterprise_rag_platform/docs/09-multi-agent-orchestration.md` | Directly answers the hiring-manager round's "architect a multi-agent system integrating with CRM, ticketing, and knowledge base" — bridges Phases 1, 2, and 3 into one architecture |

**Goal of this phase:** by the end of it, every §6/§7/§8 bullet in the prep doc has a home — this is
where "raise it unprompted" material lives.

---

## Phase 4 — Problem Type C: Delivery Framework (§5)

**Why last of the three projects:** ranked #7 in §9 — lower likelihood as a full whiteboard question,
more likely as a follow-up or a founder's-mentality story.

| # | Read | Covers |
| --- | --- | --- |
| 1 | `delivery_framework_platform/README.md` | The business case — a productised delivery process, not heroics |
| 2 | `delivery_framework_platform/docs/01-theory.md` | The theory behind the seven-stage, gated pipeline |
| 3 | `delivery_framework_platform/docs/02-architecture-end-to-end.md` | The pipeline diagram — this is what you draw for §5.2 |
| 4 | `delivery_framework_platform/docs/04-system-design-coverage-map.md` | Proven-vs-verbal against §5 in full, plus §7's rollback/canary material applied to this pipeline |
| 5 | `delivery_framework_platform/docs/05-security-gate-depth-and-tenant-scale.md` | What a gate's evidence should actually require, credential handling during an engagement, data residency for engagement artifacts, and the portfolio-scale question reframed as a tenancy decision |
| 6 | `delivery_framework_platform/INTERVIEW_SCRIPT.md` | The rehearsed whiteboard script |

**Optional:** `docs/03-src-modules-reference.md` (code reference).

---

## Phase 5 — Final Consolidation (day before / morning of)

| # | Do this | Why |
| --- | --- | --- |
| 1 | Read `DevRev-SystemDesign-Prep.docx` §8 (Trade-Off Cheat Sheet) top to bottom | Every row now has a "→ Read:" pointer to where it's argued in depth — go row by row and say the default + when-you'd-switch from memory before checking the pointer |
| 2 | Re-skim the three coverage maps' punch lists (`enterprise_rag_platform/docs/07`, `agent_platform/docs/04`, `delivery_framework_platform/docs/04`) | Know exactly what's ✅ built, 🟡 partial, or ❌ verbal-only in each project, so you never overclaim what a demo proves |
| 3 | Read `DevRev-SystemDesign-Prep.docx` §9 (Suggested Preparation Order) and §10 (Quick-Reference Checklist) | The final self-check against the guide's own priorities |
| 4 | Re-open `enterprise_rag_platform/docs/fde-first-ten-minutes.html` | The clarifying-questions cheat sheet, one more time, right before the round |

---

## Section-to-document map (quick lookup)

| Prep doc section | Primary document(s) |
| --- | --- |
| §1 The Round | Read directly from the prep doc — no project document maps to process/format |
| §2 The Answer Framework | Read directly from the prep doc; operationalized by `fde-first-ten-minutes.html` |
| §3 Problem Type A (Agent Platform) | `agent_platform/docs/01, 02, 04` |
| §4 Problem Type B (Enterprise RAG) | `enterprise_rag_platform/docs/01, 04-security-checks-reference, 06, 07, Scale_Optimization, 08` |
| §5 Problem Type C (Delivery Framework) | `delivery_framework_platform/docs/01, 02, 04, 05` |
| §6.1 Multi-Tenancy | `cross_cutting_prep/01` |
| §6.2 Security | `enterprise_rag_platform/docs/01` (retrieval side) + `agent_platform/docs/05` (tool-calling side) + `cross_cutting_prep/01` (identity/secrets) |
| §6.3 Observability | `cross_cutting_prep/02` |
| §6.4 Failure Handling | `cross_cutting_prep/02` |
| §6.5 Cost and Latency | `enterprise_rag_platform/docs/10` (channels) + `cross_cutting_prep/03` (caching, streaming) |
| §7 Agent CI/CD | `enterprise_rag_platform/docs/10` + `cross_cutting_prep/03` |
| §8 Trade-Off Cheat Sheet | Every row individually pointed to inline in the prep doc itself; see Phase 5 |
| §9 Suggested Preparation Order | Read directly from the prep doc — this guide's phase order already follows it |
| §10 Quick-Reference Checklist | Read directly from the prep doc |
| *(bridging all three)* Multi-agent + CRM/ticketing/KB integration | `enterprise_rag_platform/docs/09-multi-agent-orchestration.md` |
