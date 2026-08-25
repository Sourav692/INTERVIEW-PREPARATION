# Structured data, query routing, and connector orchestration at scale

**What this is:** the gap this repo doesn't close. `enterprise_rag_platform` proves ABAC-secured
retrieval over *documents*. It does not prove anything about DevRev's actual data shape — issues,
tickets, parts, accounts — which are **structured records**, not chunks of prose. This doc is
concept-prep for that gap: no code here to point at, only the architecture to describe out loud.

**Why this is the sharpest DevRev-specific angle:** DevRev's own interview guide names the RAG
problem as *"a RAG-based system that pulls from multiple enterprise data sources"* and, separately,
asks candidates to architect *"a multi-agent system integrating with CRM, ticketing, and knowledge
base."* Both sentences point at the same seam: a real deployment is never pure document RAG. It's
document RAG **plus** a system of record.

---

## 1. Why plain vector search fails on this data

> *"How many P1 tickets did Acme file last week?"*

Embed that question, search a vector index of ticket text, and you get **the most semantically
similar tickets** — not a count. Vector search answers *"which things are like this,"* never *"how
many,"* *"which is most recent,"* or *"sum this field."* Those are aggregate/filter operations, and no
amount of better embeddings fixes that — it's a category mismatch, not a retrieval-quality problem.

| Question shape | Right tool | Wrong tool (and why it fails) |
| --- | --- | --- |
| "Why did Acme's ingestion break in March?" | Semantic RAG over docs/postmortems | — |
| "How many P1 tickets did Acme file last week?" | Structured query (SQL / API) | Vector search returns *similar* tickets, not a count |
| "What's the status of ticket TKX-4821?" | Direct record lookup by ID | RAG treats an ID like any other token — wasteful and imprecise |
| "Summarize the resolution pattern across all P1 billing tickets this quarter" | **Both** — structured filter, then semantic summarization over the filtered set | Either alone is wrong: pure SQL can't summarize prose; pure RAG can't reliably scope to "this quarter's P1 billing tickets" |

---

## 2. Reference architecture: a router in front of retrieval

```
                         ┌──────────────────────┐
   question  ──────────> │   INTENT ROUTER      │
                         └──────────┬───────────┘
                                    |
              ┌─────────────────────┼─────────────────────┐
              v                     v                     v
     ┌────────────────┐   ┌─────────────────┐   ┌────────────────────┐
     │  STRUCTURED     │   │  SEMANTIC        │   │  HYBRID             │
     │  (SQL / tool     │   │  (existing RAG)  │   │  filter, then RAG   │
     │  call on CRM/    │   │                  │   │  over the filtered  │
     │  ticketing API)  │   │                  │   │  set                │
     └────────────────┘   └─────────────────┘   └────────────────────┘
              |                     |                     |
              └─────────────────────┴─────────────────────┘
                                    v
                          same ABAC layer, same as this repo
```

**The router is the new component.** Two honest ways to build it:

1. **Rule-based / heuristic first pass** — cheap, deterministic, catches the obvious cases: a
   question containing "how many," "count," "list all," or a ticket-ID pattern (`TKX-\d+`) routes
   structured. Fast and free, but brittle on phrasing it hasn't seen.
2. **LLM intent classifier** — a small, cheap model call (same tier as this repo's `fast_model` for
   rewrite/decompose) that outputs one of `{structured, semantic, hybrid}` plus, for structured/hybrid,
   the extracted filters (tenant, date range, priority, product). More robust to phrasing, costs one
   small LLM call per query — the same "route by difficulty" lever already used for rewrite/rerank in
   `Scale_Optimization.md` §5.

**Structured path, in turn, is a choice between two mechanisms:**

- **Text-to-SQL** over a read-only, schema-constrained view — fast, but generating correct SQL
  reliably is its own hard problem (needs a fixed, small, well-documented schema; guardrails against
  the model inventing columns; execute-and-validate before trusting the result).
- **Tool-calling against the CRM/ticketing API directly** (`list_tickets(status=, priority=, since=)`)
  — this is exactly the tool-calling loop already practiced for the coding round
  (`Coding_Round/tutorials/03_Agent_Tool_Calling_Loop.md`). Safer than free-form SQL because the tool
  surface is a fixed, reviewed set of operations, not an open query language — usually the better
  default in an enterprise setting where "the model wrote a query that touched every row" is a real
  incident, not a hypothetical.

## 3. Security doesn't get to skip the structured path

The instinct is to think ABAC is "a RAG thing." It isn't — it's a **data access** thing, and
structured queries need the identical discipline this repo already proves for chunks:

- **Row-level security on the structured side** — the exact same rule chain (tenant isolation,
  clearance, region, need-to-know) has to gate SQL rows or API results, not just retrieved chunks. A
  `SELECT COUNT(*) FROM tickets WHERE tenant_id = ?` still needs the tenant clause forced in, the same
  way `dense_search()` forces the ACL `where` clause into every Chroma query in this repo.
- **The pre-filter/post-check split still applies.** Push what the structured store can express (tenant,
  region, clearance level) into the query itself; re-verify anything it can't (need-to-know
  compartments, live revocation) before the result reaches the model or the user.
- **A structured "leak" is still a leak.** A COUNT that includes rows the user can't see, or a
  tool-call result that returns a restricted ticket's subject line, is exactly as much of a security
  incident as a forbidden document surfacing in RAG context — same `leak_rate == 0` gate applies.

## 4. Connector orchestration at scale (the Airdrop problem)

This repo proves the *pattern* for one extra connector: `ingest/loader.py::load_ticket_export()` is a
second, differently-shaped source (`ticket_export_acme.json`, no frontmatter) feeding the same
`pipeline.ingest()` path, into its own tenant. That generalizes cleanly, but "generalizes" is doing a
lot of work once you're talking about dozens of live SaaS sources (Confluence, Zendesk, Salesforce,
Slack, Jira, ServiceNow...) instead of two files.

| What this repo proves at n=2 | What changes at n≈dozens, live |
| --- | --- |
| One `loader.py` function per source, same `Document`/`ResourceAttributes` target schema | A **connector registry** — config-driven, not one bespoke function per source added by hand |
| A single `python scripts/ingest.py` run | Independent per-connector schedules; one connector's outage can't block others |
| Content-hash incremental sync (`freshness.py`) | Same idea, but per-connector **cursors/delta tokens** — most SaaS APIs give you a "changed since X" token; content-hash is the fallback when they don't |
| Dead-letter table for rejected docs (`freshness.py::record_rejection()`) | Same mechanism, **plus connector health** as a first-class signal: is Confluence's OAuth token expired, is Zendesk rate-limiting us, is Salesforce schema drift breaking the mapper |
| One tenant per demo run | **Backfill vs. incremental** as an explicit mode per connector — a newly connected source needs a bounded, resumable backfill job, not "run the sync loop and hope" |

**Concrete things to be ready to say:**

- *"Each connector maps its source's native shape into our common `Document`/`ResourceAttributes`
  schema — a Confluence page and a Zendesk ticket both become the same shape downstream, the same way
  this repo's markdown loader and ticket-export loader both feed the same `pipeline.ingest()`."*
- *"A connector's failure is quarantined per-connector, not global — Zendesk rate-limiting us shouldn't
  stall the Confluence sync."*
- *"Permission data usually comes from the same connector as the content, or from a separate
  entitlements feed (an admin console, an HR system) — this repo already models that split:
  `acl_manifest.py` is explicitly the stand-in for whatever system actually owns entitlements in
  production."*

---

## What to say if asked directly

*"My RAG project proves ABAC-secured retrieval over unstructured documents end to end. The gap I
haven't built — and want to be upfront about — is a router in front of it that recognizes when a
question needs structured data (counts, filters, a specific ticket by ID) instead of semantic search,
and dispatches to a tool call or a constrained text-to-SQL path instead. The same ABAC discipline this
repo proves for chunks — pre-filter what the store can express, post-check what it can't — has to
extend to that structured path too, because a leaked row is exactly as much of an incident as a leaked
document."*
