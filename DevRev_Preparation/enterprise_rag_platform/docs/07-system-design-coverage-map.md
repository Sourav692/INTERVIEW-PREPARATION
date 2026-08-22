# System Design Coverage Map — what this project proves vs. what's cheat-sheet only

**What this is:** every pointer named in `../../DevRev-SystemDesign-Prep.docx` §4 ("Problem Type B —
Enterprise RAG with Access Control") and the relevant parts of §6 (cross-cutting concerns), checked
against what `enterprise_rag_platform` actually implements — not what the docs merely describe.

**Why this matters for the interview:** for a ✅ item you can say *"I built this — let me show you"*
and point at a running demo. For a ❌ item you are speaking from the cheat sheet, not the code —
know the difference before the round so you don't overclaim what the demo proves.

**Legend:** ✅ covered and runnable · 🟡 partial (the concept exists, scaled down or simplified) · ❌ not built

**The "To close this gap" column** on every ❌/🟡 row below tells you what it would actually take:
- **Code — low/moderate/large** effort: a real codebase change, roughly sized
- **Data/content only**: no architecture change, just more authored examples
- **Verbal only**: infeasible or out of scope to genuinely demo locally (production infra, real scale) — answer from the prep doc, and say so if asked whether it's built. Where this applies, the table also carries a **"What to say"** column with the actual answer to give, worded ready to speak.

---

## §4.3 — Access Control Patterns (the doc's core ask)

| Pointer | Status | Where | To close this gap |
|---|---|---|---|
| Pre-filter as the recommended default | ✅ | `authz/policy.py::compile_prefilter()` — Layer 1 | — |
| Post-filter rejected explicitly, with reasons | ✅ | Module docstrings argue this directly — a ready-made trade-off answer | — |
| Per-tenant index partitioning | ✅ | One Chroma collection per tenant (physical isolation) | — |
| Per-security-group partitioning | ❌ | Only per-tenant partitioning exists, not per-group indexes | **Code — large.** `store.py::get_collection()` would need to key on `(tenant_id, group)` instead of just `tenant_id`, and every retrieval strategy would need to fan out across the principal's group-collections and merge results. This is also the pattern the prep doc itself frames as the *exception* ("when tenants are few, large, and regulated"), not the default — so it's reasonable to leave this as a verbal alternative unless asked to build it. |
| Re-check against source of truth before citing | ✅ | `authz/enforcement.py::verify_citations()` — Layer 2, reads the SQLite ACL catalog fresh | — |
| LLM never the enforcement point | ✅ | Proven, not just claimed — prompt-injection test in the eval suite | — |
| ACLs as group identifiers, not resolved user lists (no reindex on membership change) | ✅ | `scripts/demo_access_control.py::live_revocation_demo()` (principal side) + `scripts/demo_acl_catalog_update.py` (document side) | — |

This is the strongest section — every named pattern is not just discussed but **runnable**.

---

## §4.2 — Ingestion Pipeline

| Pointer | Status | Notes | To close this gap |
|---|---|---|---|
| Multi-source connectors (Confluence, SharePoint, Jira, Zendesk...) | ❌ | One synthetic markdown corpus + one ACL manifest; only one "connector" pattern is modeled | **Code — moderate.** Doesn't require real API integrations — the interview-credible version is a *second* synthetic connector (e.g. a JSON "ticket export" or a differently-shaped mock source) that produces `Document`/`ResourceAttributes` through a different parsing path than `loader.py`, proving the normalization step is real and not hardcoded to one file format. |
| Incremental sync / CDC / delta tokens | ❌ | Ingest is full reset + reload only | **Code — moderate.** Add a `source_updated_at`/content-hash field per document; `pipeline.ingest()` would skip re-chunking/re-embedding any doc whose hash is unchanged since the last run, only touching what actually changed. |
| Common Document schema (content, URI, tenant, timestamps, ACL descriptor) | 🟡 | `Document`/`ResourceAttributes` cover content/URI/tenant/ACL; no ingest timestamps | **Code — low.** Add `ingested_at`/`source_updated_at` fields to `ResourceAttributes` (or a small companion dataclass) and populate them in `loader.py`/`pipeline.py`. |
| Structure-aware chunking + overlap + parent-doc linkage | ✅ | `ingest/chunker.py` — heading-based split, overlap, `doc_id` back-link | — |
| Embed + upsert with tenant/ACL metadata on every chunk | ✅ | `ingest/store.py::upsert_chunks()` | — |
| Dead-letter queue + per-source freshness metrics | ❌ | No DLQ, no "last successful sync" signal | **Code — low-moderate.** `pipeline.IngestReport.rejected` already half-exists as a rudimentary DLQ (it collects validation failures); extending it to persist per-source "last successful sync" timestamps and a queryable rejected-docs table is a small, natural extension rather than new architecture. |

---

## §4.4 — Retrieval Quality

| Pointer | Status | Notes | To close this gap |
|---|---|---|---|
| Hybrid dense + BM25 | ✅ | `retrieval/lexical.py`, `hybrid`/`enterprise` strategies | — |
| Reranking over a large candidate pool | 🟡 | Reranking is real (`LLMReranker` + swappable `CrossEncoderReranker`), but the pool is ~12-24 candidates, not the doc's "top 50-100" | **Code — trivial.** Bump `dense_k`/`bm25_k`/`fusion_k` in `config.py`. The mechanism is already correct; this is a config value, not a design gap — worth knowing so you don't overstate the effort if asked. |
| Query rewriting / decomposition for multi-hop | ✅ | `retrieval/expansion.py` — multi-query, HyDE, decompose | — |
| History-aware rewriting for conversational queries | ❌ | Single-turn only, no conversation memory | **Code — moderate.** `RAGState`/`RAGPlatform.ask()` would need a `conversation_history` parameter threaded into `expansion.py`'s prompts (multi-query/decompose/HyDE all currently only see the current question), plus somewhere to persist history across turns (today each `ask()` call is stateless). |
| Metadata filters as first-class (source, recency, doc type) | 🟡 | These fields exist as ACL/classification metadata, but aren't exposed as user-facing query filters | **Code — low.** The fields already live in Chroma metadata; add an optional `filters` dict to `RetrievalContext`/`ask()` that gets merged into the `where` clause alongside the ACL pre-filter — the plumbing for pushing a `where` clause into `store.dense_search()` already exists, this just adds a second source of clauses. |
| Always cite; prefer refusal over a fluent guess | ✅ | `grade`/`refuse` graph nodes, citation verification | — |

---

## §4.5 — Evaluation

| Pointer | Status | Notes | To close this gap | What to say (verbal-only rows) |
|---|---|---|---|---|
| recall@k, MRR (retrieval) vs. groundedness (generation) kept separate | ✅ | `evaluation/harness.py` — two explicit metric families | — | — |
| nDCG | ❌ | Only recall@k/MRR | **Code — low.** A pure formula addition to `evaluation/harness.py::_score_case()`/`CaseResult` — needs graded relevance per expected doc (currently binary expected/not-expected), so the golden-set schema would also need a relevance-grade field per `expected_docs` entry, not just the scoring function. | — |
| Golden set of 100-300 real customer questions | 🟡 | The golden-set *mechanism* is real; only 22 synthetic cases, not real customer questions at that scale | **Data/content only.** No code change — `data/golden_set.json` just needs more authored cases. Since there's no real customer, this specific gap can only ever be closed with more synthetic cases, not "real" ones — worth naming that limit if asked directly. | — |
| Permission-specific eval suite (personas × restricted content) | ✅ | `security`-kind cases, `leak_rate` — the hard release gate | — | — |
| LLM-as-judge calibrated against human labels | 🟡 | LLM-as-judge is used (grading, groundedness); no calibration-against-human-labels step | **Code — moderate.** Would need a small script that samples N graded cases, has a human (you) label them, and computes agreement (accuracy or Cohen's kappa) between the judge's score and the human label — a new, self-contained script, not a change to the graph itself. | — |
| Online signals (thumbs up/down, escalation rate, unanswered-query clustering) | ❌ | This is an offline eval harness only, no production feedback loop | **Verbal only**, mostly. This needs a live serving surface (an API/UI capturing feedback) that doesn't exist at all in this project — genuinely out of scope for a local demo. If you want *some* code signal, a `record_feedback(run_id, rating)` stub appended to `RunTrace`/a feedback JSONL file is a low-effort gesture, but it won't demonstrate the clustering/escalation-rate part. | *"In production, every answer would capture a thumbs up/down and citation click-through, tied to the same `run_id` the trace already produces. Escalation-to-human rate becomes a proxy for retrieval failure — if it climbs, retrieval or grading regressed before anyone files a ticket. Refused/unanswered questions get embedded and clustered periodically; a cluster is a content gap, and it becomes a backlog item for whoever owns that source system, not a dead end for the user. I'd reuse the golden-set harness's `EvalReport` shape for this — same metrics, sourced from live traffic instead of a fixed case list — rather than building a second, separate metrics system."* |

---

## §4.6 — Likely Follow-Ups

| Follow-up | Status | To close this gap | What to say (verbal-only rows) |
|---|---|---|---|
| "How fast does a permission change propagate?" | ✅ Directly demoed — event-driven, zero reindex, both principal-side and document-side | — | — |
| "Retrieval returns nothing — what does the user see?" | ✅ Covered — explicit refusal path, never a silent empty answer | — | — |
| "Cost at 10M chunks?" | ❌ Not demonstrated — this is a 22-doc/86-chunk toy corpus; answer from the cheat sheet, not the code | **Verbal only**, in the main — no local demo can honestly show 10M-chunk economics. The one *piece* of this that is a tractable code change is response/embedding caching (see the caching row below); building that would let you show the cache-hit mechanism even though it can't prove behavior at real scale. | *"Five levers, in order of impact: (1) route by difficulty — a small/cheap model for query rewriting, HyDE, grading, and reranking, the large model reserved only for final synthesis — this platform already does exactly that with `fast_model` vs `synthesis_model`, so the pattern is proven, just not the scale. (2) Aggressive Layer-1 prefiltering already shrinks the candidate pool before the expensive reranking step runs — the bigger the corpus, the more that filter is doing. (3) Cache embeddings and full responses for repeated/near-duplicate questions — never pay to re-embed or re-generate the same thing twice. (4) Tiered storage — hot, recently-queried embeddings stay in the fast index; cold ones move to cheaper storage and get rehydrated on demand. (5) A smaller, cheaper model specifically for reranking, since it runs on every request but only needs a relevance judgment, not full reasoning."* |
| "Same fact, conflicting sources — which wins?" | ❌ Not built — no source-authority/recency conflict resolution | **Code — moderate.** Would need a new, non-ACL dimension on `ResourceAttributes` (e.g. `authority_rank` or reuse `valid_from`/recency), a rule for picking a winner when multiple retrieved chunks answering the same sub-claim disagree, and a change to `SYNTHESIS_SYSTEM`/`generate()` to surface the conflict rather than silently pick one. Also needs a golden case that actually contains a contradiction, which the current 22-doc corpus does not. | — |

---

## Relevant §6 Cross-Cutting Concerns

| Area | Status | Where / note | To close this gap |
|---|---|---|---|
| Tenant ID enforced at data layer, not app code | ✅ | `tenant_isolation` rule, per-tenant Chroma collection | — |
| Data residency (region-locking) | ✅ | `data_residency` rule | — |
| Noisy-neighbour controls (per-tenant rate limits/budgets) | ❌ | Not built | **Code — moderate.** A per-tenant token/request counter (in-memory dict or the SQLite catalog DB) checked at the top of `RAGPlatform.ask()`, raising/refusing once a tenant exceeds its window — needs a rate-limit policy (fixed window vs. token bucket) decided first. |
| Prompt injection defense | ✅ | Architectural — demoed in the eval suite (S07) | — |
| PII detection/redaction | ✅ | `redact_pii` obligation | — |
| Full audit trail | ✅ | `audit_events`, `observability/trace.py::RunTrace` | — |
| Secrets manager for connector credentials | ❌ N/A | No real external connectors exist to have credentials | **N/A until connectors exist.** Only becomes a real gap once the multi-source-connectors item (§4.2) is built; not independently actionable before that. |
| Full run tracing (prompt version, tokens, latency, cost) | ✅ | `RunTrace` — extensive | — |
| Alerting on drift, per-tenant dashboards | ❌ | Not built | **Code — large**, and mostly out of scope for a Python backend demo — real dashboards/alerting normally mean wiring to Prometheus/Grafana or similar, not something to build from scratch here. A cheap, code-only gesture: a script that reruns `evaluation/harness.py` on a schedule and diffs the summary row against the last run, flagging if `leak_count`/`refusal_acc`/`groundedness` moved past a threshold — demonstrates the *concept* of drift detection without a real dashboard. |
| Model routing by difficulty (small model for routing, large for synthesis) | ✅ | `config.py` — `fast_model` vs `synthesis_model`, literally this pattern | — |
| Caching (embeddings/retrieval/response) | ❌ | Not built | **Code — low-moderate.** Lowest-effort, highest-payoff gap on this list. An in-process dict cache keyed on the embedding input text in `llm/client.py::embed()` (identical questions/chunks re-embedded for free) and a response cache keyed on `(question, compiled_where_hash)` in `graph/nodes.py` are both small, self-contained additions that don't touch the security-critical path. |
| Circuit breakers / timeouts / bulkheads | ❌ | LLM unavailability degrades gracefully (`LLMUnavailable`), but no circuit-breaker pattern | **Code — moderate.** `llm/client.py` already retries and raises `LLMUnavailable` on failure; a circuit breaker would add a rolling failure counter that trips to "open" (skip calling the API, degrade immediately) for a cooldown window after N consecutive failures, rather than retrying every single request during an outage. |
| Per-run cost/token budget enforcement | 🟡 | Cost is tracked per run; no enforced ceiling | **Code — low.** `Usage`/`RunTrace` already accumulate `cost_usd`/tokens live during a run; a check after each `llm.chat`/`llm.embed` call in `graph/nodes.py` comparing running cost against a `SETTINGS.max_cost_per_run` and short-circuiting to `refuse` would close this — the measurement plumbing already exists, only the enforcement branch is missing. |

---

## Punch list — code-change gaps, sorted by effort

Everything below is a **Code** row from the tables above, grouped by size, for whenever there's time
to close a few before the interview. Data-only, N/A, and verbal-only gaps are omitted — they aren't
codebase work.

**Trivial / low effort**
- Bump `dense_k`/`bm25_k`/`fusion_k` in `config.py` so reranking sees a realistic-sized pool (§4.4)
- Add `ingested_at`/`source_updated_at` fields to `ResourceAttributes` (§4.2)
- Add an nDCG calculation to `evaluation/harness.py` (needs a relevance-grade field on golden-set cases first) (§4.5)
- Enforce a per-run cost ceiling using the `Usage`/`RunTrace` numbers that already exist (§6)

**Low-moderate effort**
- Extend `IngestReport.rejected` into a real per-source last-sync + rejected-docs record (§4.2)
- In-process caching: embed-call cache in `llm/client.py`, response cache in `graph/nodes.py` (§6)
- Expose non-ACL metadata (`source`, recency, doc type) as an optional user-facing retrieval filter (§4.4)

**Moderate effort**
- A second synthetic connector (different file format) to prove the ingestion normalization step generalizes (§4.2)
- Content-hash-based incremental sync in `pipeline.ingest()` (§4.2)
- Conversation history threaded into `expansion.py`/`RAGState` for multi-turn query rewriting (§4.4)
- A calibration script comparing LLM-judge scores against hand-labeled cases (§4.5)
- Per-tenant rate limiting in `RAGPlatform.ask()` (§6)
- A circuit breaker around LLM calls in `llm/client.py` (§6)
- Source-authority/recency conflict resolution — new attribute + synthesis prompt change + a contradiction-bearing golden case (§4.6)

**Large / likely out of scope for this demo**
- Per-security-group index partitioning (§4.3) — also not the doc's recommended default
- Real alerting/dashboards (§6) — normally external infra (Prometheus/Grafana), not custom-built here

---

## The one-paragraph interview framing

This project gives a *provably correct, runnable* answer for the single hardest thing the prep doc
calls out — *"the signal is whether a user can be shown a chunk they are not allowed to read"* —
including the Layer 1/Layer 2 split, live revocation on both the principal side and the document
side, and a real separate ACL catalog to point at when asked *"where does the source of truth
live?"* It does **not** demonstrate multi-source ingestion, scale, caching, or production
observability/alerting — for those, the honest answer is to speak from `DevRev-SystemDesign-Prep.docx`
§4/§6/§8 directly, not imply the demo proves them too.

---

## See also

- `../../DevRev-SystemDesign-Prep.docx` — the source prep document this map is checked against
- `04-security-checks-reference.md` — every ABAC field/rule/persona worked in detail
- `05-src-modules-reference.md` — every function in `src/enterprise_rag`
- `06-architecture-end-to-end.md` — the full pipeline, diagrammed end to end
- `QA.md` — running log of conceptual Q&A from prep sessions
