# Delivery Framework — Theory

**Problem prompt (verbatim from the DevRev prep guide):**

> *"Design a delivery framework that takes a customer from scoping doc to deployed AI agent in under
> 2 weeks."*

This is the odd one out among the three named problem types. The other two (agent platform, RAG
with access control) are software architecture problems. This one is explicitly named in the prep
guide as different: *"DevRev may hand you a process/operating-model design problem, not only a
software architecture one."* The signal being tested is whether you can design an **operating
model** — inputs, stages, artefacts, gates, metrics — and whether you know the difference between a
repeatable process and a pile of one-off heroics.

That doesn't mean there's nothing to build. §5.1 of the prep guide is explicit: *"Answer it as a
system with inputs, stages, artefacts, gates, and metrics, and draw it as a pipeline on the board."*
A pipeline with gates and metrics is a state machine, and a state machine is code — so
`delivery_framework_platform` builds exactly that: a real, gate-enforcing engagement pipeline, the
same way `enterprise_rag_platform` builds a real, ACL-enforcing retrieval pipeline for Problem
Type B.

---

## 1. The core insight

**The correct answer is a productised delivery process backed by reusable assets — not heroics and
not bespoke code per customer** (§5.1). Two weeks is only achievable if most of what a stage needs
already exists in a library before the engagement starts. The 2-week clock is a *consequence* of
reuse, not a target you hit by working faster.

This gives the whole design one governing question to keep coming back to: **for any given piece of
work in this pipeline, is it pulled from a library, or built from scratch for this customer?** The
ratio between those two is the actual measure of whether the framework works.

---

## 2. The seven stages (§5.2)

| Days | Stage | What has to be true to leave it |
|---|---|---|
| 1-2 | Scoping and qualification | Success metrics are written down and measurable; a customer SME is assigned; the security review has started |
| 3-4 | Data readiness | Sources are connected; access is live and verified |
| 5-7 | Configure, do not code | Assembled from the accelerator library — connectors, prompt templates, tool definitions, guardrail policies |
| 8-9 | Evaluate and iterate | A golden set exists, has been reviewed by the customer's SME, and the measured baseline meets the bar |
| 10-11 | Shadow mode | The agent runs against real traffic but takes no action; humans compare its output to what they'd have done |
| 12-13 | Limited production | The agent acts, with human approval on the loop, and a *tested* rollback path exists |
| 14 | Go/no-go and handover | The agreed success metrics were actually met; if so, a runbook, dashboards, and an owner are handed over |

**The order is not optional.** You cannot configure against data you haven't connected; you cannot
evaluate against a golden set nobody signed off; you cannot go to limited production without a
tested way to undo it. This is exactly why the codebase models stage transitions as a state machine
with hard gates rather than a checklist someone might skip under deadline pressure — see §3.

---

## 3. Gates are the whole point

**"Configure, do not code"** and **"a definition of done that includes observability and a
runbook"** are both, underneath, the same idea: a stage isn't done because time passed, it's done
because a *specific, checkable thing* is true. §5.4 names five hard gates plus the terminal decision:

| Gate | Blocks entry to | Who signs it off |
|---|---|---|
| `security_review_passed` | Data readiness | Security reviewer |
| `data_access_granted` | Configure | Customer SME |
| `golden_set_signed_off` | Evaluate | Customer SME |
| `eval_baseline_met` | Shadow mode | Forward Deployed Architect |
| `rollback_tested` | Limited production | Forward Deployed Architect |
| `success_metrics_met` | *(go/no-go — deploy)* | Executive sponsor |

**This is deliberately the same shape as ABAC access decisions in the RAG project.** A gate
sign-off and a document-access decision are the same kind of thing: a named rule, deny overrides,
an explicit reason, and — critically — **the wrong person cannot sign it off no matter how senior
they are.** The Forward Deployed Architect cannot pass the security gate; only a security reviewer
can. That isn't bureaucracy for its own sake — it's the same "no LLM is ever the enforcement point"
instinct applied to people instead of models: the person closest to the work is not automatically
the person authorized to certify it's safe.

---

## 4. Risk mitigations are checks, not reminders (§5.4)

Four named risks, and the framework's answer to each:

1. **Data access delays** — mitigation: *"start day 1, escalate day 3."* Modeled as an automatic
   check, not a task on someone's to-do list — if the `data_access_granted` gate is still pending on
   day 3, the system raises the escalation itself.
2. **Scope creep** — mitigation: change-control on the signed scope. Any change after intake has to
   go through the same sponsor-level authority that approved the original success metrics.
3. **Unmeasurable success criteria** — mitigation: **refuse to start.** This is the delivery
   framework's version of the RAG project's "refuse to index a document with no usable ACL" — a
   2-week clock started against a success metric nobody can actually measure is a worse outcome than
   never starting the clock. `pipeline.py::intake()` enforces this at the very first step.
4. **No customer SME available** — mitigation: make it a contractual prerequisite. Also enforced at
   intake, for the same reason: three of the six gates require an SME signature, so an engagement
   with no SME is structurally unable to ever finish, and it's better to know that on day 0.

---

## 5. Metrics (§5.4)

| Metric | What it actually tells you |
|---|---|
| Time-to-first-value | How long until the customer saw *anything* real, not just a status update |
| Eval score at handover | The number that was actually true when responsibility transferred |
| Human-approval override rate | Falling over time = trust being earned; flat = the agent isn't ready for less supervision |
| Week-4 retention | Whether the thing that got deployed is still the thing being used a month later |
| *(added here)* Accelerator reuse rate | The direct measure of "productised process" vs. "bespoke heroics" — the governing question from §1, made numeric |

**The honest limit, stated out loud (§5.4):** *"Some engagements should not be two weeks, and
knowing which ones to reject is part of the framework."* Intake refusal is that instinct made
literal — not every request should get a clock started against it.

---

## 6. Why this mirrors the RAG project's shape on purpose

| RAG project (`enterprise_rag_platform`) | Delivery framework (`delivery_framework_platform`) |
|---|---|
| `Principal` / `ResourceAttributes` | `Principal` (role: fda / security_reviewer / customer_sme / sponsor) |
| `authz/policy.py::decide()` — named rules, deny overrides | `gates.py::sign_off()` — named rules, deny overrides |
| Loader refuses a document with no usable ACL | `pipeline.py::intake()` refuses an engagement with no measurable metrics |
| Graph edges encode "authorize first, enforce before generate" | `engine.py::advance_stage()` encodes "no stage without its gates" |
| `observability/trace.py::RunTrace` | `observability.py` — every gate sign-off, escalation, and stage move logged |
| `evaluation/harness.py` — turns a claim into a number | `metrics.py` — turns "the process works" into a number |

The point of building it this way is not novelty — it's that the same interview signal ("I built
this, not just described it") applies to both problem types, using one consistent vocabulary.

---

## See also

- `02-architecture-end-to-end.md` — the pipeline, diagrammed end to end
- `03-src-modules-reference.md` — every function in `src/delivery_framework`
- `04-system-design-coverage-map.md` — checked against the prep doc, gap by gap
- `notebooks/02-hands-on.ipynb` — build and run it
- `../INTERVIEW_SCRIPT.md` — the whiteboard script
