# Multi-agent orchestration — CRM, ticketing, and knowledge base together

**What this is:** concept-prep, not a proven build. DevRev's hiring-manager round asks this almost
verbatim: *"Think about how you'd architect a multi-agent system integrating with CRM, ticketing, and
knowledge base."* This doc is the answer to have ready — including where the line is between "this is
multi-agent" and "this is just one pipeline with several steps," because interviewers will notice if
you blur it.

**Related:** `enterprise_rag_platform` (the knowledge-base leg) · `agent_platform` (deterministic
workflow automation — approvals, idempotency, crash-resume; the discipline this doc borrows for
failure isolation) · [structured data & connectors](08-structured-data-and-connectors.md) (the
CRM/ticketing data-access leg)

---

## 1. What actually makes something "multi-agent"

A single LangGraph pipeline with several nodes — rewrite → retrieve → grade → generate — is **not**
multi-agent. It's one agent with several *steps*. This repo's whole graph (`docs/06`) is that shape,
and it's honest to call it that in an interview rather than overclaim.

**Multi-agent** means multiple **independently-scoped** agents, each with its own responsibility,
its own tools, and its own failure mode — coordinated by something above them, and handing off a
well-defined artifact rather than raw conversation history.

| | Single agent, multi-step (this repo) | Multi-agent |
| --- | --- | --- |
| Who decides what happens next | One fixed graph | A supervisor/orchestrator, or the agents themselves via handoff |
| Tool access | One shared tool surface | Each agent scoped to only what its job needs |
| Failure blast radius | One bad node can fail the whole run | One agent's failure should degrade, not crash, the others |
| State passed forward | Full context accumulates | A defined **handoff contract** — the next agent gets what it needs, not everything |

## 2. A reference architecture for DevRev's world

```
                     customer / support-agent message
                                   |
                                   v
                        ┌────────────────────┐
                        │   TRIAGE AGENT      │   classify: bug report? billing question?
                        │                     │   feature request? "why did X happen"?
                        └──────────┬──────────┘
                                   |
        ┌──────────────────────────┼──────────────────────────┐
        v                          v                          v
┌───────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ ANSWER AGENT    │        │ TICKET AGENT      │        │ ESCALATION AGENT  │
│ (this repo's    │        │ creates/updates   │        │ hands off to a    │
│ RAG graph)      │        │ CRM/ticketing     │        │ human queue with  │
│                 │        │ record via tools  │        │ full context       │
└───────┬─────────┘        └──────────┬────────┘        └──────────┬────────┘
        |                             |                             |
        └──────────────────────────────┴──────────────────────────────┘
                                   v
                        ┌────────────────────┐
                        │   DRAFTING AGENT    │   turns the answer + ticket state into
                        │                     │   a channel-appropriate reply
                        └────────────────────┘
```

- **Triage agent** — the router from [doc 08](08-structured-data-and-connectors.md), generalized: not
  just "structured vs. semantic," but "which specialist owns this at all."
- **Answer agent** — this repo, unchanged. Its job is exactly what it already does: retrieve, ground,
  cite, refuse cleanly.
- **Ticket agent** — owns CRM/ticketing **writes** via a fixed tool surface (`create_ticket`,
  `update_status`, `attach_note`) — never free-form SQL, for the same reason argued in doc 08.
- **Escalation agent** — turns "the answer agent couldn't ground this" into an actual workflow action:
  create a ticket, route to the right queue, attach the retrieved-but-insufficient context so the
  human doesn't start from zero. (See [doc 10](10-agent-ops-and-channels.md) §3 for what "escalate"
  has to mean concretely.)
- **Drafting agent** — separate from the answer agent on purpose: the answer agent's job is *being
  right*; the drafting agent's job is *saying it well for this channel* (a Slack reply, a ticket
  comment, a customer-facing email have different tone/length constraints). Splitting these means a
  tone change never risks touching the grounding logic.

## 3. The handoff contract — the actual hard part

The naive version passes the whole conversation transcript to every agent. That's expensive, leaks
scope (the drafting agent doesn't need the ticket agent's internal tool-call log), and makes it
impossible to reason about what any one agent is allowed to depend on.

The better version: each handoff is a **small, typed object**, not a chat log.

```
TicketAgent → EscalationAgent handoff:
{
  "case_id": "...",
  "question": "...",
  "attempted_answer": {...} | null,
  "why_insufficient": "no passage covered the March 14 EU incident specifically",
  "retrieved_context": [doc_id, ...],   # so the human doesn't start from zero
  "principal": {...}                     # so escalation inherits the SAME ABAC scope, not more
}
```

Two things worth saying explicitly if asked:

1. **ABAC has to travel with the handoff, not get re-derived.** If the ticket agent hands off to
   escalation, escalation must not implicitly gain broader access than the original principal had —
   the same tenant/clearance/region scope rides along, the same way `ResourceAttributes` already rides
   attribute inheritance from document to chunk in this repo.
2. **A handoff is a state transition someone should be able to replay.** This is precisely the
   discipline `agent_platform` already proves for workflow automation — idempotent actions, crash
   mid-run resumes without repeating a completed step. The same properties apply to agent handoffs:
   a retried handoff shouldn't create two tickets; a crash between triage and escalation shouldn't
   silently drop the case.

## 4. Failure isolation

- **Per-agent circuit breaker**, same shape as this repo's LLM `_CircuitBreaker` (3 failures, 30s
  cooldown, half-open trial) — but scoped per agent, so the ticket agent being down doesn't trip the
  answer agent's breaker too.
- **Bounded handoff depth.** Two agents that can hand off to each other risk ping-ponging forever
  ("triage → escalation → triage → ..."). Cap total hops per case and force a terminal state (answered,
  escalated, or failed-safe) past the cap — the multi-agent equivalent of this repo's per-run cost
  budget (`max_cost_per_run_usd`) as a hard stop, not a suggestion.
- **Partial degradation, not full failure.** If the ticket agent's API is down, the answer agent
  should still be able to answer a pure knowledge question — the outage of one specialist shouldn't
  take down specialists that don't depend on it.

## 5. Evaluating a multi-agent system

Same instinct as this repo's evaluation section, extended:

- **Per-agent eval**, not only end-to-end: did triage route correctly? did the ticket agent's tool
  call use the right parameters? did escalation actually attach the retrieved context? A wrong
  end-to-end answer could be any one of these — same reason this repo keeps retrieval and generation
  metrics separate (`docs/01-theory.md` §9), just with more agents to separate.
- **Handoff correctness as its own metric** — did the receiving agent get everything it needed, or did
  it have to re-derive context (a sign the contract is under-specified)?
- **The security gate still applies uniformly.** A leak caused by the escalation agent forwarding
  restricted context to the wrong queue is exactly as much of an incident as a leak in the RAG answer
  — `leak_rate == 0` doesn't get a carve-out because the leak happened between agents instead of inside
  one.

---

## What to say if asked directly

*"I'd keep the answer-generation agent exactly as scoped as my RAG project already proves — retrieval,
grounding, citation, refusal. Multi-agent means putting a triage layer in front that routes to
specialists — a ticket-writing agent, an escalation agent, a drafting agent — each with its own fixed
tool surface, not a shared do-everything toolset. The part I'd be most careful about is the handoff
contract: a small typed object, not the full transcript, and critically, the same ABAC scope has to
travel with the handoff rather than get re-derived — an escalation shouldn't accidentally see more
than the original question was allowed to."*
