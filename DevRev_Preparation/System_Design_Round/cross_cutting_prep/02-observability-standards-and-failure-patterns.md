# Observability standards and failure patterns

Cross-cutting topics for any AI platform system design round. None of this needs a codebase — it's
architecture to describe on a whiteboard.

---

## 1. Standard tracing, not a bespoke log format

A trace that captures every step, every retrieved item, every tool call is good — but if it's a
one-off format invented for this project, it only ever works inside that project.

**Why the standard matters, not just the concept of tracing:** the moment a customer wants their own
monitoring tool (Datadog, Honeycomb, whatever they already run) to see your system's activity
alongside their own request traces, a bespoke format means a bespoke integration for every customer.
The industry-standard fix is **OpenTelemetry-style spans** — every unit of work is a span with an ID,
a parent ID (so spans form a tree), and a start/end time, decorated with extra fields specific to your
domain (which prompt version ran, which documents were retrieved, how many tokens were used) as
attributes on that span rather than inventing a new schema. The data you'd already want to capture
doesn't change — only the wire format does, so it's readable by tools that already exist.

## 2. Per-tenant dashboards — a customer-facing surface, not just a developer log

Traces are usually something a developer reads after something goes wrong. In a customer-facing
deployment, the customer needs their own visibility too — recall/accuracy trends, run success rate,
escalation rate, cost — scoped to only their own data.

**What this needs, conceptually:** the underlying data already exists in the trace/run store. A
dashboard is a read-only aggregation layer over that data, scoped by tenant the same way every other
part of the system scopes by tenant. The honest framing: this is a genuine frontend/BI project in its
own right, reasonable to defer — but worth naming as a real requirement rather than leaving it
unmentioned, since a forward-deployed engagement usually needs the customer to see this, not just the
vendor's own team.

## 3. Multi-provider failover

A circuit breaker (stop calling a dependency for a while after it fails repeatedly, then cautiously
retry) handles one specific case: **the same provider, temporarily unavailable.** It does not handle a
different, common case: **that provider being down for an extended outage**, where the right move is
to fail over to a second provider or a smaller fallback model, not just wait it out.

**The mechanism this needs, on top of a circuit breaker:**
- A **provider abstraction** with a primary and at least one registered fallback — not one hardcoded
  client with nowhere to go when it fails.
- **Explicit user-facing degradation.** A fallback model or vendor may answer measurably worse —
  say so, rather than silently serving a worse answer with the same confidence as normal.
- **Make the cost/quality tradeoff a tenant-level choice**, not a silent default — some customers on
  a strict quality bar might prefer to wait and retry the primary rather than get an automatic
  downgrade.

## 4. "Search index down → degrade gracefully, and say so"

A more specific version of the same instinct, worth having as its own concrete answer. If a system
combines two retrieval methods (say, meaning-based search and keyword search) and one of them becomes
unavailable, the fix isn't to fail the whole request — it's to fall back to whichever method still
works, and tell the user the answer used a narrower method than usual. This is usually a small wiring
gap, not a new capability, if both methods already exist independently — the missing piece is the
explicit fallback path at the call site and the disclosure in the response, not a new retrieval
mechanism.

## 5. The bulkhead pattern

Worth knowing as a distinct term from a circuit breaker, because interviewers will notice if you
conflate them:

- A **circuit breaker** protects against a dependency **failing repeatedly** by temporarily stopping
  calls to it.
- A **bulkhead** protects against a dependency being **slow** (not failed) by isolating its resource
  usage — giving it its own small, dedicated pool of connections/threads, so a call that hangs for
  thirty seconds only exhausts its own small pool, never the shared pool every other request (across
  every other customer) also depends on.
- Short version: a circuit breaker asks "is this dependency healthy." A bulkhead asks "even if it
  isn't, can it only hurt itself."

## 6. A genuine kill switch

A staged rollout (draft → test → limited release → full release → fully autonomous) is a **graceful,
deliberate** state change — someone decides to move something forward or back a stage. That's a
different mechanism from what's needed in an actual incident: **an emergency override that stops
everything for a given workflow or tenant, immediately, regardless of what's already running.**

- A kill switch doesn't ask "should this be demoted to a safer stage" — it asks "halt everything for
  this scope, right now," including work already mid-flight, not just new work from starting.
- It has to interrupt **in-flight** execution, not only block new runs — a staged-rollout demotion
  might only affect future authorization checks, letting anything already past that check keep going.
  A real kill switch needs a separate path that can reach in and stop active work too.
- It needs to be fast and simple to pull under pressure — a single flip a human can trigger during an
  incident, not a role-gated, multi-step approval flow. That's the opposite instinct from a staged
  rollout, and worth stating explicitly as such if asked whether they're the same thing.

---

## What to say if asked directly

*"My tracing would capture the right data, but as a custom format it wouldn't be compatible with a
customer's own monitoring stack out of the box — a standard tracing format fixes that by using the
same fields as attributes on standard spans instead of a custom schema. On failure handling: a circuit
breaker handles one provider being temporarily down, but has nowhere to fail over to on its own — a
real deployment needs an explicit fallback provider, and it should tell the user rather than silently
serving a worse answer. And the one thing a well-built staged rollout doesn't give you for free is an
emergency kill switch — a staged rollout is a deliberate, role-gated transition; a kill switch is the
opposite instinct, a fast, blunt override for the moments a staged approval flow is too slow to
matter."*
