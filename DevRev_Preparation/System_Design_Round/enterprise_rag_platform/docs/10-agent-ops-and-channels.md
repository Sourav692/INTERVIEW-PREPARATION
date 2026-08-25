# Operating agents in production — CI/CD, multi-channel delivery, and real escalation

**What this is:** concept-prep for the "after it works once" questions — DevRev's guide asks directly
about *"CI/CD of AI agents (prompt versioning, A/B testing, rollback)"* and *"workflow automations
across multiple channels."* Nothing in `enterprise_rag_platform` builds this; it's single-channel
(`scripts/ask.py`) and has no versioning/rollback story at all. This doc is the answer to have ready,
built from mechanisms this repo *does* already prove, generalized outward.

---

## 1. CI/CD for AI agents

The uncomfortable truth interviewers are checking for: most teams ship a prompt change the way they'd
ship a config tweak — edit, deploy, hope. That's the failure mode to name explicitly, then describe
the fix.

### Prompt versioning

Treat every prompt (`SYNTHESIS_SYSTEM`, a routing prompt, an agent's system prompt) as an **immutable,
hashed artifact**, not a mutable string in source:

```
prompt_id: synthesis_system
version: v14
content_hash: 8f2a1c...
created_at: ...
eval_report: { groundedness: 0.94, leak_rate: 0.0, refusal_acc: 0.88 }
status: canary(10%) | promoted | rolled_back
```

This is the same instinct as this repo's content-hash incremental sync (`ingest/freshness.py`) —
change detection by hash, not by trusting a timestamp or a human's memory of what changed.

### The gate before promotion

Reuse the exact eval harness this repo already has, unchanged in shape:

- **Security gate**: `leak_rate` must still be exactly 0 against the new prompt version — this is a
  hard block, not a review comment, for the same reason it's a hard block in this repo's evaluation
  design (`docs/01-theory.md` §9: *"a leak is an incident."*)
- **Quality gate**: groundedness / refusal-accuracy must not regress past a threshold vs. the current
  production version, on the same golden set.
- **A new prompt version that fails either gate never reaches canary**, let alone full promotion.

### Canary / shadow rollout

- **Shadow first**: run the new prompt version alongside production on live traffic, log both outputs,
  compare offline — zero user-facing risk.
- **Canary next**: a small percentage of traffic (or a small set of low-risk tenants) actually sees the
  new version; watch the same metrics live, not just at gate time.
- **Promote or roll back** based on that — and rollback has to be **instant and cheap**: swap which
  version a request routes to, not a redeploy. The version that was live five minutes ago is still
  sitting there, untouched, ready to take traffic again.

### A/B testing

Two prompt versions serve concurrently, split by a stable key (user id or tenant id, not random per
request — so a given user always experiences one consistent behavior). The metrics that matter here
are the same three families this repo already separates: retrieval-side (unaffected by a prompt
change), generation-side (groundedness, refusal accuracy), and the security gate (which must be
identical — zero — across both arms, not something you're "testing" a difference on).

## 2. Multi-channel delivery

The same core agent (this repo's RAG graph, or the multi-agent system in
[doc 09](09-multi-agent-orchestration.md)) has to serve a chat widget, Slack, email, and an API — and
those are not the same problem wearing different clothes.

| Channel | Latency expectation | Output shape | Consequence for design |
| --- | --- | --- | --- |
| **Live chat widget** | Sub-second first token | Short, conversational, streamed | Needs token streaming; synthesis can't wait for the full answer before showing anything |
| **Slack** | A few seconds is fine | Slightly more structured (can use blocks/links) | Can afford one extra retrieval pass (e.g. `enterprise` strategy) that a live-typing UI can't |
| **Email / async ticket reply** | Minutes is fine | Longer-form, more formal tone, no streaming needed | This is where the **drafting agent** ([doc 09](09-multi-agent-orchestration.md) §2) earns its keep — same underlying answer, very different prose |
| **API** | Caller-defined | Structured JSON, not prose | No "drafting" step at all — the raw grounded answer plus citations, machine-readable |

**The architecture implication:** don't fork the agent per channel. One core (retrieve → ground →
cite → refuse) behind a **channel adapter layer** that only touches two things: (1) how much latency
budget it has — which retrieval strategy and how much fan-out is affordable — and (2) how the same
grounded answer gets formatted for that channel's expectations. The ABAC/security layer is identical
across every channel, on purpose — a channel is a UI decision, never a permissions decision.

## 3. Human-in-the-loop escalation as a real workflow

This repo's guardrail rule (`docs/01-theory.md` §8) is: *"refuse cleanly and escalate to a human. Never
hint that withheld material exists."* That's the right *policy*. It says nothing yet about the
*mechanism* — and DevRev's product is literally a ticketing system, so "escalate" needs to cash out
into something concrete, not a refusal string.

**What escalation has to actually do:**

1. **Create or update a ticket**, not just return a message — the case needs to exist somewhere a
   human will see it, in the queue that owns this kind of question.
2. **Attach the working context** — the original question, what was retrieved (even if insufficient),
   why it was judged insufficient or why access was denied, and the principal's scope. The human
   should not have to start from zero, and should not have to re-ask the user what they already said.
3. **Route to the right owner** — a security-denied question and a "no document covers this" question
   go to different queues (security/compliance vs. content-gap backlog) — conflating them either
   spams a security queue with content gaps, or under-reports actual denials that need review.
4. **Never leak the reason for a security refusal into the ticket's visible fields** if that ticket is
   later visible to a broader audience than the original request was — the escalation record itself
   is subject to the same ABAC as the original question. An internal note explaining *why* access was
   denied can itself be a disclosure if it's visible to the wrong audience.
5. **Feed back into eval.** Every escalation is a labeled example: either "the system should have been
   able to answer this" (a retrieval/content gap — becomes a backlog item for whoever owns that source)
   or "the system correctly refused" (a true negative, evidence the security gate is working, not a
   failure to fix). This is the online-signal gap this repo's own coverage map already names as ❌
   (`docs/07` §4.5, "online signals... no production feedback loop") — escalation volume and its
   resolution outcome is exactly that missing signal, sourced for free from a mechanism the product
   already has.

---

## What to say if asked directly

*"None of my RAG project's demos show CI/CD or multi-channel delivery — it's a single-shot CLI. But
the mechanisms generalize cleanly: the same golden-set eval harness that gates a release in my project
becomes the gate a new prompt version has to pass before canary, and the same 'leak_rate must be zero'
rule that blocks a release there blocks a prompt promotion here too — it doesn't get softer just
because it's now an A/B test. For channels, I'd keep one core agent and put a thin adapter layer in
front that only changes latency budget and output formatting — never the security layer, because a
channel is a UI decision, not a permissions decision. And for escalation, 'refuse and escalate' has to
mean something concrete: create a ticket, attach the context, route it to the right queue, and — this
is the part people usually skip — feed the outcome back into eval, because every escalation is a free
labeled example of either a content gap or a correctly-working refusal."*
