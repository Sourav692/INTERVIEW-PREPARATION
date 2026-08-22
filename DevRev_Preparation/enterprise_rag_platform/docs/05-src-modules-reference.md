# `src/enterprise_rag` module reference

## Overview

The package implements a multi-tenant RAG platform with attribute-based access control (ABAC) enforced at two points: a pre-filter pushed into the vector store (`authz/policy.py::compile_prefilter`), and an authoritative post-retrieval re-check (`authz/enforcement.py::enforce`) that runs before any text reaches the LLM. Documents are loaded and chunked (`ingest/`), embedded and stored in per-tenant Chroma collections (`ingest/store.py`), then retrieved via one of several swappable strategies (`retrieval/strategies.py`) that combine dense search, BM25, query expansion (multi-query/HyDE/decomposition), Reciprocal Rank Fusion, and LLM reranking. The end-to-end request flow is orchestrated as a LangGraph state machine (`graph/`): authorize → plan → retrieve → enforce → grade → generate → verify, with a refuse branch whenever context is insufficient. Every request is recorded as a replayable JSON trace (`observability/trace.py`), and an evaluation harness (`evaluation/harness.py`) runs a golden set of cases through any strategy to score retrieval quality, groundedness, and — as a hard gate — a zero-tolerance ACL leak rate.

## models.py

Defines the package's dataclasses: `ResourceAttributes` (document ACL attributes), `Principal` (authenticated caller), `Document`, `Chunk`, `ScoredChunk`, `Citation`, and `Answer`. Also defines the `SENSITIVITY_RANK` ladder used for numeric clearance comparisons.

##### Module-level

- **`today_iso()`**: Returns today's date as an ISO string. Used as the default "as of" date for embargo/expiry checks.

##### `ResourceAttributes`

- **`sensitivity_level` (property)**: Maps the string `sensitivity` field to its integer rank via `SENSITIVITY_RANK`, enabling numeric `<=` comparisons against a principal's clearance.

##### `Principal`

- **`clearance_level` (property)**: Maps the principal's `clearance` string to its integer rank, same purpose as above but for the caller side.
- **`from_dict(d)`**: Classmethod that constructs a `Principal` from a plain dict (used when loading identities from JSON).

##### `Chunk`

- **`to_metadata()`**: Flattens a chunk and its inherited ACL attributes into a Chroma-compatible metadata dict. Since Chroma metadata values must be scalars, `allowed_groups` (a list) is encoded as one boolean column per group (`grp__<group>: True`), letting an `$or` of `$eq True` clauses reproduce list-overlap semantics.
- **`attrs_from_metadata(md)`** (static): Inverse of `to_metadata()` — reconstructs a `ResourceAttributes` object from a Chroma metadata dict, decoding the `grp__*` boolean columns back into a group list and splitting the comma-joined `need_to_know` field.

##### `ScoredChunk`

- **`citation` (property)**: Formats the chunk's `doc_id`/`ordinal` as a `[DOC-ID#N]` citation string.

##### `Answer`

- **`to_dict()`**: Serializes the dataclass (including nested `Citation` objects) to a plain dict via `dataclasses.asdict`.

## identity.py

Stands in for an identity provider. Resolves principal attributes fresh from a JSON file on every call rather than caching per-session, which is what makes revocation take effect on the very next request.

- **`_load(path=None)`**: Lazily loads and caches (module-level `_CACHE`) the identities JSON file into a `user_id -> Principal` dict. Strips any keys starting with `_` (comment fields) before constructing each `Principal`.
- **`list_principals()`**: Returns all loaded principals as a list, triggering `_load()` if the cache is empty.
- **`get_principal(user_id)`**: Looks up one principal by id, raising `KeyError` with the list of known ids if not found. Returns a fresh copy (not the cached instance) so a caller mutating the result (e.g. a demo that revokes a group) cannot corrupt state shared across requests.

## config.py

Central `Settings` dataclass holding every tunable value (paths, model names, chunking/retrieval parameters, guardrail thresholds). Loads `OPENAI_API_KEY` from a repo-root `.env` file found by walking up from this file's location, and disables the ambient LangSmith tracing env vars unless `ENTERPRISE_RAG_LANGSMITH=1` is set, since this project has its own trace layer.

##### `Settings`

- **`has_api_key` (property)**: True if `api_key` is set and looks like an OpenAI key (starts with `sk-`).
- **`collection_for(tenant_id)`**: Builds the per-tenant Chroma collection name as `f"{collection_prefix}__{tenant_id}"`.

A module-level `SETTINGS = Settings()` singleton is imported by nearly every other module as the default configuration.

## authz/policy.py

The ABAC policy engine — the single authority on who may read what. Rules are ordered functions; deny rules run first and any deny wins outright, then a single allow rule (group membership) runs, with a default-deny fallback. Also compiles the statically-decidable portion of the policy into a Chroma `where` filter.

##### `Decision`

- **`denied` (property)**: Convenience negation of `allowed`.

##### Rule functions (each takes `(principal, resource, ctx)` and returns `Decision(allowed=False, ...)` to hard-deny, or `None` to abstain)

- **`_rule_tenant_isolation(p, r, ctx)`**: Denies if the principal's tenant differs from the resource's tenant. The hard multi-tenant boundary; no role bypasses it.
- **`_rule_clearance(p, r, ctx)`**: Denies if the resource's sensitivity rank exceeds the principal's clearance rank.
- **`_rule_data_residency(p, r, ctx)`**: Denies if the resource is region-locked (not `GLOBAL`) and the principal is in a different region.
- **`_rule_embargo(p, r, ctx)`**: Denies if today (or `ctx["as_of"]`) is before `valid_from` (not yet published) or after `valid_until` (expired).
- **`_rule_need_to_know(p, r, ctx)`**: Denies if the resource lists `need_to_know` compartments the principal's `projects` don't cover, even if clearance is sufficient.
- **`_rule_external_contractor(p, r, ctx)`**: Denies external principals from reading resources whose `source` is `contract`, `pricing`, or `postmortem`, regardless of group membership.
- **`_rule_group_membership(p, r, ctx)`**: The one allow rule — grants access if the resource is marked `public` or if the principal's groups overlap the resource's `allowed_groups`.

##### Core functions

- **`decide(principal, resource, ctx=None)`**: Runs all deny rules in order (short-circuiting on the first that denies), then the allow rule, returning a `Decision`; falls through to a `default_deny` `Decision` if nothing granted access.
- **`_attach_obligations(p, r, d)`**: Attaches post-allow obligations to a `Decision` — `redact_pii` if the resource contains PII and the principal cannot view it, and `audit_access` if sensitivity is `confidential`/`restricted`.
- **`compile_prefilter(principal, ctx=None)`**: Translates the statically-decidable subset of the policy (tenant, sensitivity ceiling, region, group overlap, external-contractor source exclusion) into a Chroma `where` clause. Explicitly does not encode embargo, need-to-know, obligations, or live revocation, since those require fresh evaluation.
- **`explain_prefilter(principal)`**: Returns a human-readable one-line summary of the compiled pre-filter's conditions, used in traces and demo output.

## authz/enforcement.py

The authoritative, post-retrieval access check. Treats every vector-store hit as a candidate that passed a possibly-stale filter, re-evaluates `decide()` against fresh attributes for each one, carries out obligations (PII redaction, audit logging), and flags disagreements between the pre-filter and this check as security events.

- **`redact_pii(text)`**: Masks email addresses in text via regex substitution, returning the masked text and the count of redactions made.
- **`_apply_redaction(sc)`**: Applies `redact_pii` to a `ScoredChunk`'s text in place, marking `sc.redacted = True` if anything was masked; returns whether redaction occurred.
- **`enforce(principal, candidates, ctx=None, came_from_prefilter=True)`**: Re-runs `decide()` on every candidate chunk, using attrs freshly fetched from the ACL catalog (`store.get_doc_attrs()`) rather than the chunk's own denormalised Chroma metadata — falling back to the chunk's attrs only if the doc was never catalogued. Denied chunks go to `report.denied`; if a chunk came from a pre-filtered query and was denied for a reason the pre-filter should have caught (not embargo/expiry/need-to-know), it's logged as a `filter_disagreements` security event. Allowed chunks get redaction and audit obligations applied and are collected into `report.allowed`. Returns an `EnforcementReport`.
- **`verify_citations(principal, cited_doc_ids, ctx=None)`**: Final check on citations rendered into an answer — re-fetches each cited document's attributes and re-runs `decide()`, silently dropping any doc_id that doesn't resolve (hallucinated citation) or that the principal isn't authorized to see.

##### `EnforcementReport`

- **`denied_doc_ids` (property)**: Sorted, de-duplicated list of doc_ids that appear in `denied`.
- **`summary()`**: Renders a short human-readable string like `"5 allowed, 1 denied, 2 redacted"`, flagging any filter disagreements.

## ingest/loader.py

Loads corpus markdown files and joins them with the separate ACL manifest by `doc_id`. Represents the "connector" boundary where a source system's permission model would be translated into this platform's ABAC model — except content and permissions now arrive as two distinct feeds, matching how a real connector reads a document from Confluence/SharePoint/Zendesk and reads its permissions from a separate entitlements system. Markdown frontmatter carries only `doc_id` and `title` — no ACL fields live in the corpus files.

- **`_parse_frontmatter(text)`**: Splits a markdown document into its `---`-delimited frontmatter block (parsed as `key: value` lines, now just `doc_id`/`title`) and the remaining body text. Returns `({}, text)` unchanged if no frontmatter block is present.
- **`load_corpus(corpus_dir=None, tenant_id="meridian", acl_manifest_path=None)`**: Loads the ACL manifest (`acl_manifest.load_acl_manifest()`) into a `doc_id -> ResourceAttributes` map, then globs all `*.md` files, parses each one's `doc_id`/`title` and body, and joins it against that map. Raises `ValueError` if a file has no `doc_id` in its frontmatter, or if its `doc_id` has no matching entry in the ACL manifest — refusing to index a document with no usable access-control metadata either way. Returns a list of `Document` objects, each with its `attrs` populated from the manifest.

## ingest/acl_manifest.py

**New.** Reads `data/acl_manifest.json` — the file where access-control data is actually authored, separate from document content. One JSON record per `doc_id` (`source`, `sensitivity`, `allowed_groups`, `region`, `product`, `owner`, `contains_pii`, `need_to_know`, `valid_from`, `valid_until`). Stands in for whatever real system owns entitlements in production (an admin console, HR/entitlements system, a permissions export).

- **`load_acl_manifest(path=None, tenant_id="meridian")`**: Parses the manifest JSON into a `doc_id -> ResourceAttributes` dict, applying the given `tenant_id` to every record (the manifest itself carries no tenant field — one manifest file is scoped to one tenant's ingest run, same as `load_corpus()`'s existing `tenant_id` parameter).

## ingest/chunker.py

Structure-aware chunking that splits on markdown headings before packing to a target size, so a chunk never cuts through the middle of a semantic unit and always carries its section heading.

- **`_split_by_heading(text)`**: Splits document text into `(section_title, section_body)` tuples using the `HEADING_RE` regex for `#`-`####` headings, preserving any preamble text before the first heading and keeping empty-bodied headings as their own labeled section.
- **`_pack(section_title, body, target, overlap)`**: Packs a section's paragraphs into pieces no larger than `target` characters, splitting on blank-line paragraph boundaries. When a piece is closed, it carries a trailing `overlap`-character tail from the previous piece into the next, so facts split across a chunk boundary remain recoverable.
- **`chunk_document(doc, settings=SETTINGS)`**: Runs `_split_by_heading` then `_pack` on a `Document`, prefixes each resulting piece with the document title and section heading (measurably improves both dense and lexical retrieval), and wraps each piece as a `Chunk` with a sequential ordinal and the parent document's inherited ACL attributes.
- **`chunk_corpus(docs, settings=SETTINGS)`**: Runs `chunk_document` over a list of documents and concatenates the results into one flat chunk list.

## ingest/pipeline.py

The end-to-end ingestion pipeline: load → validate ACLs → chunk → embed → index. Validation is loud by design — a document with unusable ACL metadata is rejected rather than silently defaulted.

- **`validate_acl(doc)`**: Checks a `Document`'s attributes for a known `sensitivity` value, a non-empty `allowed_groups` list, a known `region`, and consistency between `sensitivity == "public"` and membership in the `public` group. Returns an error string describing the first violation found, or `None` if valid.
- **`ingest(tenant_id="meridian", reset=True, batch_size=64, settings=SETTINGS)`**: Orchestrates the full pipeline — optionally resets the store, loads the corpus, validates and filters documents (collecting rejections), chunks the accepted documents, embeds chunks in batches via `LLMClient.embed`, and upserts each batch into the tenant's Chroma collection. Returns an `IngestReport` with counts and cost.

##### `IngestReport`

- **`render()`**: Formats the report as a multi-line human-readable summary: documents/chunks indexed, embedding cost, any rejected documents, and breakdowns by source and by sensitivity (ordered by the sensitivity ladder).

## ingest/store.py

The Chroma-backed vector store, with one collection per tenant as a physical isolation layer on top of the logical ABAC pre-filter. See package overview for the two-layer isolation rationale. Chunk metadata (including ACL fields) here is a **denormalised copy**, used only for the Layer-1 pre-filter pushdown — the authoritative ACL source is the separate SQLite catalog in `ingest/catalog.py`.

- **`get_client(settings=SETTINGS)`**: Lazily creates and caches (module-level `_client`) a `chromadb.PersistentClient` rooted at `settings.chroma_dir`, with telemetry disabled.
- **`reset_store(settings=SETTINGS)`**: Clears the cached client, then deletes the on-disk Chroma directory. Used only by the ingest script and tests.
- **`get_collection(tenant_id, settings=SETTINGS)`**: Gets or creates the tenant's Chroma collection, named via `settings.collection_for(tenant_id)`, configured for cosine similarity.
- **`get_doc_attrs(doc_id, settings=SETTINGS)`**: The Layer-2 authoritative lookup. Delegates to `catalog.get_doc_attrs()` (a fresh SQLite `SELECT`, independent of the vector index); falls back to a live Chroma metadata scan only if the doc was never catalogued (e.g. a hand-built test chunk).
- **`upsert_chunks(tenant_id, chunks, embeddings, settings=SETTINGS)`**: Upserts a batch of chunks (ids, embeddings, text, flattened metadata) into the tenant's collection. Returns the count upserted.
- **`_to_scored(ids, docs, metas, distances, retrieved_by, matched_query)`**: Converts raw Chroma query results into a list of `ScoredChunk` objects, reconstructing each `Chunk` from its metadata and converting cosine distance to a similarity score (`1 - distance`).
- **`dense_search(tenant_id, query_embedding, where, k, matched_query=None, settings=SETTINGS)`**: Runs a Chroma vector query with the ABAC `where` filter applied inside the query itself, so unauthorized chunks are never scored or returned. Returns a list of `ScoredChunk`.
- **`fetch_all_allowed(tenant_id, where, settings=SETTINGS)`**: Fetches every chunk matching the ACL filter (no vector query), used as the candidate pool for BM25 since a lexical index can't push the filter down the way the vector store can. Returns a list of `Chunk`.
- **`collection_stats(tenant_id, settings=SETTINGS)`**: Fetches all metadata in the tenant's collection and aggregates chunk/document counts, plus breakdowns by `source` and `sensitivity`.

## ingest/catalog.py

**New.** The authoritative ACL catalog — a local SQLite database (`data/acl_catalog.db`), one row per document, separate from the vector index. This is what makes Layer 2 a genuinely independent source of truth instead of re-reading Layer 1's own cached copy.

- **`get_connection(settings=SETTINGS)`**: Lazily creates and caches (module-level `_conn`) a `sqlite3.Connection`, creating the `documents` table if it doesn't exist.
- **`reset_catalog(settings=SETTINGS)`**: Closes the cached connection and deletes the `.db` file, then recreates an empty table. Used by the ingest pipeline (on `reset=True`) and tests.
- **`upsert_doc_attrs(attrs, settings=SETTINGS)`**: Inserts or overwrites one document's ACL row, JSON-encoding the `allowed_groups`/`need_to_know` list fields.
- **`upsert_many(attrs_list, settings=SETTINGS)`**: Calls `upsert_doc_attrs` for a batch of documents — used by `pipeline.ingest()` right after ACL validation.
- **`get_doc_attrs(doc_id, settings=SETTINGS)`**: One indexed `SELECT` by `doc_id`, returning a reconstructed `ResourceAttributes` or `None`.
- **`update_attr(doc_id, **fields)`**: Reads a document's current attrs, applies field changes (e.g. `sensitivity="internal"`), and writes them back. Demonstrates the whole point of the split: this touches only this SQLite row — no re-embedding, no Chroma write — and the next `enforce()` call for that `doc_id` sees the new value immediately.
- **`all_doc_ids(settings=SETTINGS)`**: Returns every catalogued `doc_id`, for tooling/debugging.

## retrieval/lexical.py

BM25 keyword retrieval over the ACL-authorized candidate pool, used because embeddings handle rare tokens (error codes, ids) poorly while BM25 treats them as highly discriminative.

- **`tokenize(text)`**: Lowercases and tokenizes text using `TOKEN_RE`, which keeps hyphenated identifiers (e.g. `MRD-5031`) intact as single tokens instead of splitting on the hyphen.

##### `BM25Index`

- **`__init__(chunks)`**: Tokenizes every chunk's text and builds a `BM25Okapi` index over the corpus (or `None` if the chunk list is empty). Built fresh per request over the principal's authorized chunks — noted as a demo-scale simplification, not a production lexical store.
- **`search(query, k, matched_query=None)`**: Tokenizes the query, scores it against the BM25 index, and returns the top-`k` chunks with positive score as `ScoredChunk` objects tagged `retrieved_by=["bm25"]`. Returns `[]` if the index is empty.

## retrieval/expansion.py

Three distinct query-transformation techniques, each addressing a different retrieval failure mode: vocabulary mismatch (multi-query), question/answer register asymmetry (HyDE), and multi-hop questions (decomposition).

- **`generate_multi_queries(llm, question, n=None, settings=SETTINGS)`**: Asks the LLM (via `chat_json`) for `n` alternative phrasings of the question, then returns the deduplicated list `[original] + variants` (case-insensitive dedup). Degrades to just `[original]` if the LLM call fails (`LLMUnavailable`), never failing the whole retrieval.
- **`generate_hyde_passage(llm, question)`**: Asks the LLM to write a short, confident hypothetical passage that would answer the question, used only as a dense-search embedding probe (never shown to the user). Returns `None` on failure.
- **`decompose(llm, question, settings=SETTINGS)`**: Asks the LLM whether the question needs splitting into sub-questions (only when facts must come from genuinely different sources), and returns up to `settings.max_subquestions` sub-questions, or `[]` if decomposition isn't needed or the call fails.

## retrieval/rerank.py

Reranking as the highest-leverage quality step: retrieval optimizes for cheap recall over a large corpus, reranking optimizes for precision over a small candidate set by scoring the query and each passage together (unlike a bi-encoder).

##### `LLMReranker`

- **`__init__(llm, settings=SETTINGS)`**: Stores the `LLMClient` and settings used to score candidates.
- **`rerank(question, candidates, top_k=None)`**: Sends all candidates (truncated to 700 chars each) to the LLM in one batched `chat_json` call, asking for a 0–10 relevance score per passage id. Assigns `rerank_score` on each `ScoredChunk`, sorts descending, and returns the top `top_k`. On `LLMUnavailable`, degrades by returning the first `top_k` candidates in their existing (fusion) order with `rerank_score=None` rather than failing the request.

##### `CrossEncoderReranker`

- **`__init__(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2", settings=SETTINGS)`**: Lazily imports and loads a local `sentence_transformers.CrossEncoder` model, offered as a no-API-cost drop-in alternative to `LLMReranker`.
- **`rerank(question, candidates, top_k=None)`**: Scores each (question, passage) pair with the local cross-encoder, maps the raw logit onto the same 0–10 scale the rest of the pipeline expects, and returns the top `top_k` sorted by score.

## retrieval/fusion.py

Reciprocal Rank Fusion (RRF) — merges multiple ranked lists using only rank position, not raw scores, since scores from different retrievers (cosine similarity vs. BM25) aren't comparable.

- **`reciprocal_rank_fusion(ranked_lists, k=None, top_n=None)`**: For each chunk, sums `1 / (k + rank + 1)` across every list it appears in (`k` defaults to `settings.rrf_smoothing`, damping the influence of top ranks so agreement across retrievers wins over topping a single list). Mutates each surviving `ScoredChunk` in place (`fused_score`, `score`, merged `retrieved_by` provenance), sorts by fused score descending, and returns the top `top_n` (default `settings.fusion_k`).

## retrieval/strategies.py

Named, swappable retrieval strategies sharing one call signature, so the graph can select one per request and the eval harness can A/B them on identical inputs. Every strategy receives the compiled ACL pre-filter and passes it to every store call.

##### `RetrievalContext`

Dataclass bundling everything a strategy needs — the principal, the compiled `where` filter, an `LLMClient`, settings, and mutable fields (`subquestions`, `notes`, `generated_queries`, `hyde_passage`) that strategies populate for tracing.

- **`_embed_and_search(ctx, queries, k)`**: Embeds a batch of queries in a single API call, then runs one `store.dense_search` per query/embedding pair. Returns a list of ranked lists, one per query.
- **`dense_only(question, ctx)`**: Embeds and searches only the original question; the baseline strategy.
- **`bm25_only(question, ctx)`**: Fetches the full ACL-authorized pool and searches it with `BM25Index`; keyword-only.
- **`hybrid(question, ctx)`**: Runs dense search and BM25 on the original question in parallel and fuses the two ranked lists with RRF.
- **`multi_query(question, ctx)`**: Generates N query rewrites via `expansion.generate_multi_queries`, dense-searches each, and fuses all resulting lists with RRF (the "RAG-Fusion" pattern).
- **`hyde(question, ctx)`**: Generates a HyDE probe passage; if generation fails, falls back to `dense_only`. Otherwise dense-searches with both the probe and the literal question and fuses the results, using the original question to anchor against HyDE drift.
- **`enterprise(question, ctx)`**: The production-default strategy — fans out dense search across multi-query rewrites, a HyDE probe, and any sub-questions, and fans out BM25 across the original question and sub-questions (deliberately not the paraphrased rewrites, since they dilute rare identifiers), then fuses every list with RRF.
- **`get_strategy(name)`**: Looks up a strategy function by name in the `STRATEGIES` registry, raising `ValueError` with the list of valid names if not found.

## llm/client.py

Thin OpenAI wrapper centralizing chat/JSON/embedding calls, retries, timeouts, token accounting, and cost attribution in one place.

##### `Usage`

- **`add(model, prompt, completion, purpose, embedding=False)`**: Accumulates token counts (routed to `embedding_tokens` or `prompt_tokens`/`completion_tokens` depending on the call type) and computes incremental USD cost from the `PRICING` table, also tallying tokens by `purpose` for per-stage cost breakdowns.
- **`merge(other)`**: Adds another `Usage` instance's totals into this one, used to combine per-request usage into a running total.

##### `LLMClient`

- **`__init__(settings=SETTINGS, usage=None)`**: Validates an API key is configured (raising `RuntimeError` if not) and constructs the underlying `openai.OpenAI` client with the configured request timeout.
- **`_with_retries(fn, attempts=3, purpose="unknown")`**: Runs `fn` with exponential backoff and full jitter on `RateLimitError`/`APITimeoutError`. For a generic `APIError`, retries only on 5xx status codes and immediately raises `LLMUnavailable` on 4xx (treated as a bug in the request, not transient). Raises `LLMUnavailable` after exhausting attempts.
- **`chat(system, user, purpose, model=None, temperature=0.0, max_tokens=900)`**: Sends a system/user chat completion request through `_with_retries`, records usage, and returns the stripped response text.
- **`chat_json(system, user, purpose, model=None, max_tokens=900)`**: Same as `chat` but constrains the response to `{"type": "json_object"}` and parses it, returning `{}` on a JSON decode failure rather than raising.
- **`embed(texts, purpose="embed")`**: Batches a list of texts into a single embeddings API call, records usage as embedding tokens, and returns the list of embedding vectors. Returns `[]` immediately for an empty input list.

##### Module-level

- **`LLMUnavailable`**: Exception raised when the provider cannot serve a request after retries; callers catch it to degrade gracefully instead of failing the whole run.

## graph/state.py

Defines `RAGState`, a single `TypedDict` that flows through every LangGraph node, covering the request, infrastructure handles (LLM client, usage, trace), authorization output, planning output, retrieval/enforcement results, and the final generation outcome. No functions — purely a typed data contract that lets any node be tested in isolation and lets the trace be reconstructed from state alone.

## graph/prompts.py

Versioned prompt templates as named constants (not inline string literals), each run recording which `PROMPT_VERSION` served it so prompt changes are reviewable, gated diffs.

- **`PROMPT_VERSION`**: The current prompt version string, stamped onto every trace.
- **`SYNTHESIS_SYSTEM` / `SYNTHESIS_USER`**: System and user templates for the final answer-generation call — enforce citation format, no-guessing rules, partial-answer behavior, and routing instructions found in source material.
- **`PARTIAL_COVERAGE_NOTE`**: Appended to the synthesis prompt when the grader found only partial coverage, telling the model to answer what it can and state plainly what it couldn't determine.
- **`SUFFICIENCY_SYSTEM`**: System prompt for the context-sufficiency grader, defining the `sufficient`/`partial`/`insufficient` verdict rubric.
- **`GROUNDEDNESS_SYSTEM`**: System prompt for the post-hoc groundedness check, asking whether each claim in the answer is actually supported by the cited passages.
- **`REFUSAL_TEMPLATE`**: Template for the user-facing refusal message, filled with a reason and a role-appropriate next step.

## graph/nodes.py

The LangGraph node functions implementing the pipeline: `authorize → plan → retrieve → enforce → grade → (generate → verify | refuse)`. Each node takes the current `RAGState` and returns a partial state update.

- **`authorize(state)`**: Compiles the principal's ABAC policy into a Chroma `where` pre-filter via `compile_prefilter` before any retrieval happens, and records the filter and its human-readable explanation on the trace.
- **`plan(state)`**: Uses a cheap regex heuristic (looking for "and"/"also"/"as well as"/`;`) to decide if a question looks multi-hop; only if so (and only under the `enterprise` strategy) does it call `expansion.decompose` to actually generate sub-questions, saving latency on the common single-hop path.
- **`retrieve(state)`**: Looks up and runs the selected strategy function from `STRATEGIES`. If query expansion fails with `LLMUnavailable`, degrades to the plain `dense` strategy and marks the state as `degraded` rather than failing the request.
- **`enforce(state)`**: Runs `enforcement.enforce` (the authoritative ACL re-check) on all retrieved candidates, then reranks the *allowed* survivors with `LLMReranker` — ordering enforcement before reranking so the reranker's top-k reflects only what this principal may see. Populates trace fields for denied chunks, redactions, and audit/security events.
- **`grade(state)`**: The context-sufficiency guardrail. Returns insufficient immediately if there's no context or the best rerank score is below `settings.min_rerank_score`; otherwise asks the LLM to grade sufficiency (`sufficient`/`partial`/`insufficient`) via `SUFFICIENCY_SYSTEM`. Treats `partial` as sufficient-to-proceed (with a coverage note attached) rather than refusing, since which part of a question a user can see is itself role-dependent. On grader failure, trusts the reranker score and proceeds.
- **`route_after_grade(state)`**: Conditional-edge function returning `"generate"` or `"refuse"` based on `state["sufficient"]`.
- **`_format_context(context)`**: Formats the retrieved chunks into the block of text passed to the synthesis prompt, labeling each with doc id, title, section, source, and sensitivity, and stopping once `settings.max_context_chars` would be exceeded.
- **`generate(state)`**: Calls the synthesis LLM with the formatted context and question to produce a draft answer. On `LLMUnavailable`, returns state that routes to `refuse` instead of raising, marking the run degraded.
- **`verify(state)`**: Two checks before finalizing the answer: (1) extracts cited doc ids from the draft via `CITATION_RE`, drops any not actually present in the context (hallucinated) or that fail a live re-check via `enforcement.verify_citations`, stripping their bracket markers from the text; (2) asks the LLM to score groundedness of the cleaned answer against the context. Builds the final `Answer` with `Citation` objects for the surviving valid citations.
- **`refuse(state)`**: Builds the clean no-answer `Answer`, deliberately never revealing that a restricted document exists (which would itself be a disclosure), and picks a role-appropriate next step (escalate to Tier 3, vs. ask the document owner/escalate to the responsible team).

## graph/build.py

Compiles the LangGraph state machine from the node functions in `nodes.py` and exposes the public `RAGPlatform` entry point.

- **`build_graph()`**: Builds and compiles the `StateGraph(RAGState)` with all eight nodes and the edges described in the pipeline overview (including the conditional edges after `grade` and after `generate`). Caches the compiled graph in a module-level `_COMPILED` singleton since compilation isn't free.

##### `RAGPlatform`

- **`__init__(settings=SETTINGS)`**: Stores settings and builds (or reuses) the compiled graph.
- **`ask(question, principal, strategy="enterprise", as_of=None, write_trace=True)`**: The single public method. Constructs a fresh `LLMClient`/`Usage`/`RunTrace` per call, seeds the initial `RAGState`, invokes the graph, finalizes the trace with usage totals, optionally writes the trace to disk, and returns `{"answer", "trace", "state"}`. Falls back to a generic "no answer was produced" `Answer` if the graph somehow ends without one.

## observability/trace.py

Defines `RunTrace`, a complete, replayable, JSON-serializable record of one request — covering identity, the compiled ACL filter, generated queries, retrieved/denied/redacted chunks, the final answer, and token/cost/latency accounting. Traces are written to `runs/` as one JSON file per run.

##### `RunTrace`

- **`start(name, **detail)`**: Opens a named timing step, recording its start time and any initial detail fields in the internal `_open` dict.
- **`end(name, **detail)`**: Closes a named step (no-op if it was never started), computing its duration in milliseconds, merging in additional detail fields, and appending it to `self.steps`.
- **`finish(usage=None)`**: Computes total elapsed time for the whole run and, if a `Usage` object is given, copies its token counts, call count, and cost onto the trace.
- **`to_dict()`**: Converts the dataclass to a plain dict via `asdict`, dropping the internal `_open` bookkeeping field.
- **`write(settings=SETTINGS)`**: Writes the trace as indented JSON to `runs/run_<run_id>.json`, creating the directory if needed. No-ops and returns `None` if `settings.trace_enabled` is false.
- **`timeline()`**: Renders a human-readable ASCII bar chart of each step's duration relative to the total, useful as a first latency-debugging view.

## evaluation/harness.py

The evaluation harness: runs a golden set of test cases through any retrieval strategy and scores two independently-owned metric families (retrieval quality: recall@k/MRR; generation quality: groundedness/refusal accuracy), plus a hard, non-negotiable security gate (ACL leak rate, which must be exactly zero).

- **`load_cases(path=None)`**: Loads the golden-set JSON file and returns its `"cases"` list.
- **`_score_case(case, result, strategy)`**: Scores one case's platform output against its expected/forbidden/distractor document lists — computes recall and MRR against `expected_docs`, flags any `forbidden_docs` that were retrieved or cited as a leak, flags `distractor_docs` retrieved as a (non-gating) precision miss, and checks `expect_refusal`/`must_contain` assertions if present. Returns a populated `CaseResult`.
- **`run_eval(strategy="enterprise", cases=None, kinds=None, platform=None, verbose=True)`**: Runs every (filtered) case through `RAGPlatform.ask()` with the given strategy (without writing per-case traces), scores each with `_score_case`, and optionally prints a pass/fail line per case. Returns an `EvalReport`.
- **`compare_strategies(strategies, kinds=None, verbose=False)`**: Runs the same golden set through multiple strategies against one shared `RAGPlatform` instance and returns a list of summary-row dicts, one per strategy — the artifact used to justify "strategy X is measurably better" claims.

##### `CaseResult`

- **`passed` (property)**: A case fails if anything leaked, or if recall on `expected_docs` is below 1.0. `distracted` misses never fail a case (tracked separately as a quality signal, not a security signal). Security-kind cases gate only on the deterministic zero-leak property, not on whether the model happened to refuse — refusal is only a hard gate for `behaviour`-kind cases.
- **`refusal_advisory` (property)**: True if this is a security case whose refusal expectation wasn't met, recorded as a non-gating advisory rather than a failure (since refusal-vs-thin-answer is a probabilistic LLM judgment, not a security property).

##### `EvalReport`

- **`_vals(attr, kinds=None)`**: Internal helper collecting non-`None` values of a given attribute across results, optionally filtered by case `kind`.
- **`recall_at_k` / `mrr` / `groundedness` (properties)**: Mean of the corresponding per-case metric across all results with that metric set.
- **`leak_count` (property)**: Total number of leaked documents summed across all cases.
- **`refusal_advisories` (property)**: List of case ids flagged as refusal advisories.
- **`distraction_count` (property)**: Total number of distractor documents retrieved across all cases.
- **`leak_rate` (property)**: Fraction of security-kind cases that leaked anything; `0.0` if there are no security cases.
- **`refusal_accuracy` (property)**: Fraction of cases with a defined `refusal_correct` that were correct.
- **`pass_rate` (property)**: Fraction of all cases where `CaseResult.passed` is true.
- **`total_cost` / `p50_latency` (properties)**: Summed cost and median latency across all cases.
- **`summary_row()`**: Returns a flat dict of the strategy's headline metrics, rounded, suitable for a comparison table row.
- **`render()`**: Renders a full human-readable report — headline metrics, the leak gate, distraction count, refusal advisories, latency/cost, and a detailed list of failing cases with reasons.
