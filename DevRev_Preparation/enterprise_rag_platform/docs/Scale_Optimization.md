# Scale & Latency Optimization — from a 22-doc demo to 20M documents

This project's flagship corpus is 22 docs / 86 chunks, run locally against a single-process
ChromaDB collection. That's intentional — it keeps the ACL/security mechanism provable and cheap
to demo. But interviewers will always push past the demo with "fine, now what if the customer has
20M documents?" This doc is the honest, structured answer: what breaks first, what the fix is, and
which fixes this codebase already proves the *pattern* for (even at toy scale) vs. which are
verbal-only because no local demo can honestly show them.

Status key used throughout: **✅ proven in this repo** (small scale, same mechanism) · **🔧 verbal /
architecture-only** (correct answer, not buildable as an honest local demo) · **❌ not applicable**.

See also: `docs/06-architecture-end-to-end.md` (pipeline), `docs/07-system-design-coverage-map.md`
(§4.6 already has a short version of the 10M-chunk-cost answer this doc expands on),
`docs/03-theory-databricks.md` (the Lakehouse rebuild, which is the actual answer to "how do you
run this at 20M docs" — Vector Search + UC, not ChromaDB).

---

## 1. What breaks first at 20M documents (assume ~4 chunks/doc → ~80M chunks)

Walk the pipeline in order and ask "what falls over here first":

| Stage | Breaks because | First symptom |
|---|---|---|
| **Ingestion** | Single-process embedding loop; no dedup; no incremental sync at this volume | Days-long ingest run, re-embedding unchanged docs on every re-run |
| **Vector index** | ChromaDB (single-node, in-process) has no answer for 80M vectors | OOM, or unusably slow index build |
| **ACL/ABAC filtering** | Per-tenant collection scan and per-chunk attribute check don't shard | Query latency grows with corpus size, not with result size |
| **BM25 lexical index** | Built fresh over `fetch_all_allowed()` per query (`retrieval/lexical.py`) | Rebuilding a keyword index per request is O(allowed pool), fine at 86 chunks, fatal at 80M |
| **Reranking** | `LLMReranker.rerank()` calls an LLM per candidate | Reranking even 50 candidates per query at 20M-doc traffic volumes = huge $ and latency |
| **Metadata / audit store** | In-memory `RunTrace` / audit_events, no persistent queryable store | Audit trail unqueryable at scale, compliance risk |
| **Cost** | Every uncached embed/generate call is billed per token | Linear cost growth with corpus size and query volume |

The single biggest architectural fact: **this is not one scaling problem, it's three** — ingestion
throughput, retrieval-at-query-time latency, and per-tenant isolation overhead — and each needs a
different fix.

---

## 2. Scaling ingestion to 20M documents

**Current state (this repo):** `scripts/ingest.py` — single process, synchronous embed loop,
content-hash incremental sync (`demo_incremental_sync.py`, ✅ proven) that skips unchanged docs.

**At 20M docs:**

1. **Parallelize embedding, don't serialize it.** Fan out documents across workers (Spark
   `mapPartitions`, or a job queue / Ray / multiprocessing pool locally) — embedding is
   embarrassingly parallel per-document. ✅ *pattern proven*: the incremental-sync content-hash
   check is the exact mechanism that makes re-runs cheap; it just needs to run inside parallel
   workers instead of a `for` loop.
2. **Batch embedding calls.** Never call the embedding API one chunk at a time — batch 100s of
   chunks per request to amortize per-request overhead; OpenAI/most embedding APIs support this
   natively.
3. **Chunking as a separate, parallelizable stage from embedding.** Chunking is CPU-bound and
   cheap; embedding is API-bound and the expensive step. Decoupling them means you can over-provision
   chunking workers relative to embedding workers.
4. **Idempotent, resumable ingestion.** A 20M-doc ingest job *will* be interrupted. Content-hash
   dedup (already in this repo) plus a per-document ingestion-status ledger (queued / embedded /
   indexed / failed) means a restart only reprocesses what didn't finish — not the whole corpus.
5. **Dead-letter / poison-pill handling.** At 20M docs, some fraction will fail to parse (corrupt
   PDF, unsupported encoding, empty doc). Route failures to a dead-letter queue with the error
   reason, don't let one bad doc stall the batch.
6. **On Databricks specifically** (`docs/03-theory-databricks.md`): this becomes a Lakeflow
   Declarative Pipeline — Auto Loader ingesting raw docs incrementally, a Spark UDF wrapping the
   embedding call (batched, with `ai_query`/foundation-model endpoints if using Databricks-hosted
   embeddings), writing to a Delta table, synced into a Vector Search index. This is the actual
   production answer, not a variant of the local ChromaDB script. 🔧

**Ingestion throughput math to have ready:** if embedding throughput is ~500 chunks/sec (typical
batched-API ballpark at reasonable parallelism), 80M chunks ≈ 160,000 seconds ≈ ~44 hours
single-threaded-equivalent. With 50-way parallelism, that's under an hour. This is the number to
say out loud — it shows you think in throughput-per-worker × worker-count, not "it'll be slow."

---

## 3. Scaling the vector index itself

**Current state:** ChromaDB, single collection per tenant, in-process / on-disk, fine to ~10^5–10^6
vectors.

**At 20M docs (~80M vectors), ChromaDB in this configuration is the wrong tool.** The honest answer:

| Option | When to pick it |
|---|---|
| **Databricks Vector Search** | Already Unity-Catalog-governed, syncs from Delta, scales to hundreds of millions of vectors, integrates ACL via UC row filters — this is what `docs/03`/`notebooks/04` build. Natural fit given this repo already has a Databricks-native twin. |
| **Managed vector DB at scale** (Pinecone, Weaviate, Milvus/Zilliz, Qdrant, pgvector on a sharded Postgres) | If not on Databricks — pick one with native sharding, replica read scaling, and metadata-filtered ANN search. |
| **Self-hosted sharded ANN** (FAISS/HNSW behind a routing layer) | Only if you need full control and have the ops capacity — not usually the right tradeoff for a 20M-doc *enterprise* deployment. |

Key mechanisms any of these need to provide at this scale:

1. **Approximate nearest neighbor (ANN), not exact search.** HNSW or IVF-based indexes trade a small
   recall hit for orders-of-magnitude speedup — non-negotiable past ~1M vectors.
2. **Sharding by tenant (or tenant-hash).** This repo already isolates tenants into separate
   collections (`tenant_isolation` rule, `docs/07`) — that pattern is exactly what makes horizontal
   sharding trivial: each shard is a tenant or tenant-group, queries never need to fan out across
   tenants because a request is always scoped to one tenant already. ✅ *isolation model proven*,
   🔧 *sharding infra itself not built locally*.
2b. **Metadata filtering pushed into the ANN index**, not applied post-hoc. Filtering allowed
   chunks *after* the top-K vector search comes back is how you silently lose recall (the true
   top-K allowed result may not be in the pre-filter top-K). Production vector DBs support
   filtered ANN search natively — filter-then-search or search-with-filter, not search-then-filter.
   This is a real gap to call out even in the current small-scale code if asked directly.
3. **Replica reads.** Query traffic scales independently of index-build traffic — read replicas
   absorb query load while writes/upserts go to a primary.
4. **Tiered storage / hot-cold split.** Recently-queried or recently-added embeddings stay in the
   fast index; cold, rarely-queried vectors move to cheaper storage and rehydrate on demand. 🔧
   (already called out in `docs/07`'s §4.6 answer — this doc is the expanded version).

---

## 4. Scaling ACL/ABAC enforcement

This is the part of the system this repo is *actually* strong on, and it's worth being precise
about what scales for free vs. what needs new work.

- ✅ **Scales for free:** tenant isolation via separate collections/indexes — a query is always
  scoped to one tenant's shard, so adding tenants adds shards, not query-time cost.
- ✅ **Scales for free:** ACL re-check after retrieval (`nodes.enforce()`) is O(candidates), not
  O(corpus) — candidates are already bounded by top-K, so this doesn't grow with document count.
- 🔧 **Needs new work at scale:** if the vector DB can't push ACL/ABAC attribute filters *into* the
  ANN search itself (ties to point 2b above), you either (a) over-fetch top-K·N and filter down —
  wasteful and can still under-fill results, or (b) maintain per-principal or per-attribute-combo
  materialized sub-indexes — expensive to maintain but fast to query. Databricks Vector Search and
  most serious vector DBs support filtered search natively; this is a "does the vendor support it"
  question to ask, not something to build.
- 🔧 **Live ACL changes at scale:** this repo proves the *mechanism* (`demo_acl_catalog_update.py`
  — a policy-table update takes effect with zero reindex, because enforcement checks the policy
  catalog at query time, not at index time) ✅. At 20M docs the same mechanism holds — enforcement
  cost depends on candidate count, not corpus size — so this is one of the few things that
  genuinely scales without new engineering.

---

## 5. Latency optimization — the customer-facing number that actually matters

Break latency down by pipeline stage (`docs/06` §3, the LangGraph pipeline) and attack each one:

| Stage | Latency lever | Status here |
|---|---|---|
| **Query rewriting / decompose / multi-query / HyDE** | Route to a small, fast model (`fast_model` vs `synthesis_model` in `config.py`) — never use the large model for anything that isn't final synthesis | ✅ proven, this is the exact existing pattern |
| **Retrieval (dense/BM25/hybrid)** | ANN search is sub-linear by construction; keep top-K small going into rerank | ✅ ANN via ChromaDB HNSW at small scale, same principle at large scale |
| **Reranking** | Use a small/cheap reranker model (or a cross-encoder, not a full LLM call) since it only needs a relevance judgment, not reasoning | 🔧 identified gap — `LLMReranker` currently uses a full LLM call; swapping to a lightweight cross-encoder or a cheaper model is the fix |
| **Generation/synthesis** | This is the one stage that legitimately needs the strong model — don't try to cheapen it | — |
| **Repeated/near-duplicate questions** | Cache at both the embedding layer and the full-response layer | ✅ proven — `llm/client.py::embed()` in-process cache; `graph/nodes.py::generate()` response cache keyed on `(question, ACL filter, exact context, coverage note)` |
| **Circuit breaker / timeout on LLM calls** | Fail fast on a genuine outage instead of hanging every request behind a slow/dead dependency | ✅ proven — `llm/client.py::_CircuitBreaker`, trips after 3 consecutive failures, 30s cooldown, half-open trial |
| **Network round-trips** | Batch what can be batched (embedding calls); parallelize independent LLM calls (e.g. multi-query rephrasings) instead of serial `await`s | 🔧 partially — worth explicitly checking whether `generate_multi_queries()` fan-out is issued concurrently |
| **Cold-start on first query per tenant** | Keep hot indexes warm; avoid lazy-loading a tenant's collection only on first request | 🔧 not built — a real prod concern (index warm-up / connection pooling) |

### The five-lever answer to "how do you get p95 latency down at scale" (interview-ready, verbal)

1. **Model routing by difficulty** — small/cheap model for rewriting, HyDE, grading, reranking;
   large model reserved for final synthesis only. *Already proven in this repo* via
   `fast_model`/`synthesis_model`.
2. **Aggressive early filtering** — ACL/tenant/ABAC filtering happens before the expensive
   reranking step, so reranking only ever runs over an already-small, already-authorized candidate
   set. The bigger the corpus, the more this filter is doing the work.
3. **Caching** — embeddings and full responses, keyed precisely enough (question + ACL filter +
   context) that a cache hit is only ever served for a truly identical, freshly-re-enforced
   situation. Never re-embed or re-generate the same thing twice.
4. **Parallelize independent LLM calls** — multi-query rephrasing, HyDE generation, and per-tenant
   requests are independent of each other; issue them concurrently, don't serialize what doesn't
   need to be serial.
5. **Push filtering into the index, not after it** — filtered ANN search (point 2b above) so you
   never over-fetch-then-discard; this is a latency win as much as a correctness one.

### p50/p95/p99 framing to have ready

Interviewers often want you to reason about tail latency, not just the average:

- **p50** is dominated by the happy path: cache hit, or a fast dense-retrieval + small-model
  rewrite + synthesis call.
- **p95/p99** is dominated by cache misses on cold/rare queries, multi-hop decomposition (extra
  LLM round-trips), and reranking over a larger-than-usual candidate set (a broad question that
  matches many chunks before ACL narrows it).
- **The circuit breaker is a p99 tool, not a p50 tool** — its whole job is bounding the worst case
  (a dependency outage) rather than improving the typical case. Say this explicitly if asked "does
  caching fix your tail latency" — it doesn't, caching fixes the *median*; timeouts/circuit
  breakers/fallback-to-smaller-model fix the *tail*.

---

## 6. Cost at 20M documents — the other half of "scale"

Interviewers frequently pair the latency question with a cost question. Five levers, same
prioritization as the §4.6 answer in `docs/07`, restated here for completeness:

1. Model routing by difficulty (✅ proven pattern).
2. Aggressive prefiltering before the expensive rerank step (✅ proven pattern).
3. Embedding + response caching, never pay to re-embed or re-generate the same thing twice (✅ proven).
4. Tiered storage — hot embeddings in the fast index, cold ones rehydrated on demand (🔧 verbal).
5. A smaller/cheaper reranker model, since reranking runs on every request but only needs a
   relevance judgment (🔧 identified gap, see §5 table above).

One number worth having ready: at 20M docs / ~80M chunks, even a one-time embedding pass at
$0.0001-ish per 1K tokens (roughly what small embedding models cost) times an average chunk size
means the *one-time* ingestion cost is real money but tractable (low-to-mid four figures USD,
order-of-magnitude) — the ongoing cost that actually matters is *query-time* generation cost times
query volume, which is why caching and model routing (levers 1–3) dominate the cost conversation,
not the one-time ingest cost.

---

## 7. Other scale/optimization points worth knowing cold for the interview

- **Multi-tenancy at scale ≠ one big index with a tenant_id filter.** This repo already does the
  right thing (separate collection per tenant) — say *why*: a shared index with a metadata filter
  means noisy-neighbor problems (one huge tenant's index rebuild/query load degrades every other
  tenant) and a filter that's easy to get wrong once, catastrophic if wrong. Per-tenant sharding
  makes the blast radius of a bug or an outage one tenant, not all of them.
- **Noisy-neighbor / per-tenant rate limiting already exists** (`authz/rate_limit.py`) — say this
  is exactly the mechanism that has to hold at scale: a fixed-window per-tenant counter checked
  *before* any LLM client is constructed, so a rate-limited request costs $0, not just "returns an
  error after doing the work anyway."
- **Reindexing strategy for schema/embedding-model changes.** At 20M docs, re-embedding everything
  because you upgraded the embedding model is a multi-day, multi-thousand-dollar operation — the
  answer is a blue/green index (build the new index alongside the old, cut traffic over once
  backfilled, never a big-bang in-place migration).
- **Backpressure, not unbounded queues.** Ingestion and query paths both need backpressure —
  an unbounded ingestion queue at 20M docs will OOM the queue itself before it OOMs the index.
  Per-run cost/token budget enforcement (`max_cost_per_run_usd`, already ✅ in this repo) is the
  query-path analog of the same instinct — halt-and-escalate rather than let one runaway request
  (or one runaway ingest job) consume unbounded resources.
- **Observability has to scale with the corpus, not just the query volume.** `RunTrace` is
  currently in-memory/per-run; at scale this needs to land in a queryable store (a Delta table, a
  proper APM backend) so "which tenant is driving cost/latency regressions" is answerable without
  grepping logs.
- **Drift detection at scale.** `docs/07` already flags this as an open gap: rerun the eval
  harness on a schedule, diff the summary row (leak_count, refusal_acc, groundedness) against the
  last run, alert on regression. At 20M docs and real production traffic, this stops being a nice
  idea and becomes how you catch a retrieval-quality regression before a customer does.
- **Know the difference between "scales" and "scales linearly."** ANN retrieval, ACL enforcement
  post-retrieval, and per-tenant sharding all scale *sub-linearly or flat* with corpus size — say
  this explicitly, it's the strongest answer to "does this fall over at 20M docs": the mechanisms
  that make correctness possible at 22 docs (tenant isolation, policy-catalog-at-query-time ACL
  checks, candidate-bounded reranking) are the *same* mechanisms that make it scale — nothing about
  going from 22 docs to 20M documents requires re-architecting the security model, only swapping
  the storage/index layer underneath it.
