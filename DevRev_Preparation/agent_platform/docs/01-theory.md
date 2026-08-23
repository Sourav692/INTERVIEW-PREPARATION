# Agent Platform — Theory

**Problem prompt (verbatim from the DevRev prep guide):**

> *"Design an AI agent platform for non-technical users to configure workflow automations across
> multiple channels."*

---

## 1. The question behind the question (§3.1)

**The hard part is not running an agent — it's letting a non-technical user define one safely and
predictably.** Anyone can wire an LLM to a tool. The signal being tested is whether you split
*deterministic control flow* from *probabilistic reasoning*, so a user without engineering
background can configure something dependable without writing (or reading) code.

**"Multiple channels" is doing real work in the prompt.** The same logical workflow must fire from
email, chat, Slack, a web form, and a webhook — each with a wildly different payload shape and a
different notion of "what is this about." If channel-specific logic leaks past the first layer of
the system, every subsequent component has to know about every channel, forever. The fix is a
canonical event schema and adapters that translate into it once, at the edge — see §3.2 below.

**Expect follow-ups on testing and containment**, not on the happy path: how does a user try a
workflow before it's live, and how do you stop a bad one mid-flight? Both are answered by the same
mechanism — staged rollout plus a hard step/spend budget — not two separate features.

---

## 2. Reference architecture (§3.2), and what this project builds of it

| Layer | What it does | Built here? |
|---|---|---|
| Channel adapters | Normalise inbound events into one canonical `Event` schema | ✅ `channels.py` |
| Trigger and routing | Match events to workflows; resolve same-event conflicts | ✅ `routing.py` |
| Workflow definition store | Versioned, declarative specs, never raw code | ✅ `workflows.py` |
| Orchestration engine | Durable, checkpointed, resumable step execution | ✅ `orchestrator.py` |
| Agent runtime | Plan → select tool → call → observe → iterate, with a hard step cap | 🟡 the loop shape is real; the "planner" is a fixed step list, not a real LLM choosing dynamically — see `docs/04` |
| Tool registry | Typed tools, JSON-schema args, scopes, destructive flag | ✅ `tools.py` |
| Connector layer | Authenticated per-tenant integrations, secrets vault | ❌ not built — see `docs/04` |
| Policy and guardrail service | Approval gates, spend caps, PII redaction | 🟡 approval gates + spend caps built; PII redaction not built |
| Run store and trace log | Every step, tool call, output persisted | ✅ `observability.py` |

---

## 3. The non-technical user problem (§3.3)

Five ideas, stated as design constraints:

1. **Templates, not a blank canvas** — a library of pre-built workflows to clone and edit, not a
   from-scratch authoring surface.
2. **Natural-language authoring compiles to a reviewable declarative spec** — the user never edits
   the thing that actually executes directly; they edit (or generate) the `WorkflowSpec`, and confirm
   intent before it runs. This project's `WorkflowSpec` is exactly that reviewable spec — built here
   directly in code, standing in for what a visual builder or NL-to-spec compiler would emit.
3. **A dry-run mode with all writes mocked** — this project's `SHADOW` status *is* that mode: the
   guardrail engine refuses to apply any destructive tool's side effect while a workflow is in
   `SHADOW`, unconditionally, regardless of role or approval.
4. **Plain-language run history** — not built here (the trace is a structured log, not natural
   language), but the structured log it's built from is exactly what a plain-language summary would
   be generated *from*.
5. **Staged rollout: draft → test → shadow → live (approved) → autonomous** — built exactly as named,
   as an ordered, role-gated promotion (`workflows.py::promote()`), the same shape as
   `delivery_framework_platform`'s stage gates.

---

## 4. Determinism and control (§3.4)

**This is the section this project is actually about.** Five named controls, all built and tested:

| Control | Where |
|---|---|
| Constrained tool schemas over free-text arguments | `tools.py::validate_args()` — type-checked against a declared schema before execution |
| Idempotency keys on side-effecting calls | `orchestrator.py` — a retried step never applies its side effect twice |
| Max-step and max-cost budgets, halt-and-escalate not loop | `guardrails.py::authorize_step()` — the tighter of the workflow's own budget and the tenant policy's |
| Confirmation gates on destructive actions, configurable per tenant/tool | `guardrails.py` — role-gated approval, an explicit per-tenant allow-list for what autonomous status may skip approval on |
| Split deterministic control flow from probabilistic reasoning | The orchestrator's step sequence is fixed, declarative data; only *which value* goes into an argument is ever templated from the event — the control flow itself is never something an LLM improvises at runtime |

**A subtlety worth stating out loud:** autonomous status does not mean unlimited. A destructive tool
not explicitly allow-listed for autonomous execution still needs a human, even on a fully autonomous
workflow — and a spend cap applies at every status, including autonomous. Autonomy raises the
ceiling on *which* actions can skip approval; it never removes the ceiling itself.

---

## 5. Likely follow-ups (§3.5) — and where each one is actually answered

| Follow-up | Answer, and where |
|---|---|
| A workflow has been running for two hours when the orchestrator restarts — what happens? | `run.next_step_index` is the checkpoint; `orchestrator.resume()` continues from it, never from step 0. Demoed directly — a simulated crash mid-run, then resumed. |
| Two workflows trigger on the same event and conflict | Two mechanisms: `routing.py`'s priority ordering picks one *by design*, and an exclusivity lock on the event's target entity prevents two runs from ever mutating the same entity concurrently, *even if priority were misconfigured*. |
| How does a tenant safely add a custom tool? | Partially answered: schema validation and scoping exist (`ToolDefinition.schema`/`.scopes`); sandboxed execution and a review-before-publish pipeline do not — see `docs/04`. |
| How do you version a workflow that's already live? | `WorkflowStore` keeps every published version; a `Run` pins to `workflow_version` at start, so editing a workflow mid-flight never changes the behaviour of runs already in progress. |

---

## 6. Why this mirrors the other two projects on purpose

Third project in the series, same `Decision(allowed, rule, reason)` shape as the RAG project's
`authz.policy.decide()` and the delivery framework's `gates.py::sign_off()`:

| Concept here | Concept in `delivery_framework_platform` | Concept in `enterprise_rag_platform` |
|---|---|---|
| `guardrails.py::authorize_step()` | `gates.py::sign_off()` | `authz/policy.py::decide()` |
| Staged workflow rollout (`workflows.py::promote()`) | Staged engagement pipeline (`engine.py::advance_stage()`) | Layer 1 pre-filter / Layer 2 authoritative re-check |
| Entity lock in `routing.py` | Per-engagement single mutable state | Per-tenant Chroma collection isolation |
| `observability.py` | `observability.py` | `observability/trace.py::RunTrace` |

The point, stated once for all three: **access control, delivery gates, and workflow guardrails are
the same kind of problem wearing three different hats** — a named rule decides, deny overrides, and
the reason is never "because I said so."

---

## See also

- `02-architecture-end-to-end.md` — the pipeline, diagrammed end to end
- `03-src-modules-reference.md` — every function in `src/agent_platform`
- `04-system-design-coverage-map.md` — checked against the prep doc, gap by gap
- `notebooks/02-hands-on.ipynb` — build and run it
- `../INTERVIEW_SCRIPT.md` — the whiteboard script
