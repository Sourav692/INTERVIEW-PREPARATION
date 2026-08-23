# Agent Platform — AI Agent Platform for Non-Technical Users

A deterministic guardrail-and-orchestration engine for the problem named in DevRev's system design
prep guide as Problem Type A: **"design an AI agent platform for non-technical users to configure
workflow automations across multiple channels."** Third project in the series, same discipline as
`enterprise_rag_platform` and `delivery_framework_platform` — a real, runnable system that proves
the properties it claims.

No LLM anywhere in this project — the "agent reasoning loop" is a fixed, deterministic step
sequence, so every test is fast and exactly reproducible. See `docs/04-system-design-coverage-map.md`
for the honest list of what that trades away.

---

## The business case

**The claim §3.1 makes:** the hard part isn't running an agent, it's letting someone non-technical
configure one *safely*. This project turns "safely" into checkable properties instead of a slide:

1. **A destructive action never executes without either an explicit human approval or an explicit
   per-tenant allow-list entry** — even on a fully autonomous workflow.
2. **A retried or redelivered action never applies its side effect twice** — proven with a real
   idempotency key, not asserted.
3. **A crash mid-run never re-runs a step that already completed** — proven by actually crashing a
   run and resuming it.

> *"Why didn't Cascade Robotics' $500 refund fire automatically?"*

| Question | What actually happened |
|---|---|
| Wasn't the workflow autonomous? | Yes — but `issue_refund` wasn't allow-listed for autonomous use on this tenant, so it still needed a human. |
| Wasn't there budget? | The tenant's spend cap is $50. A $500 refund is refused outright — `spend_cap_exceeded` — never silently clamped down to the cap. |
| What if it retries and refunds twice? | It can't — the idempotency key on that specific action already exists after the first apply; a retry is a no-op. |

---

## Quick start

```bash
# 1. The happy path - staged rollout, routing conflict, approval, idempotent retry, crash + resume
python scripts/run_workflow_demo.py

# 2. The negative-control demo - the one to run in front of an interviewer
python scripts/demo_guardrail_failure.py

# 3. Tests
python -m pytest -q     # 21 tests, deterministic, no API calls, well under a second
```

---

## Documentation

| File | What it is |
|---|---|
| **`docs/01-theory.md`** | The concepts, and why the shape mirrors the other two projects. Read first. |
| **`docs/02-architecture-end-to-end.md`** | The pipeline, diagrammed end to end. |
| **`docs/03-src-modules-reference.md`** | Every function in `src/agent_platform`, 2-3 lines each. |
| **`docs/04-system-design-coverage-map.md`** | Every pointer from the prep doc's §3, checked against what's built, with a "what would it take" column. |
| **`notebooks/02-hands-on.ipynb`** | Builds and runs the whole platform, step by step. |
| **`INTERVIEW_SCRIPT.md`** | How to present this on a whiteboard in 60 minutes. |

---

## Architecture

```
raw payload (email/chat/Slack/web form/webhook)
        --> ADAPTER --> canonical Event
                              |
                    ROUTING: priority match + entity lock
                              |
              ORCHESTRATOR (durable, checkpointed, resumable)
       step -> validate args -> GUARDRAIL -> execute (idempotent) -> checkpoint
                              |
          COMPLETED / PAUSED_FOR_APPROVAL / HALTED  (never a silent stop)
```

### The guardrail decision, in order (deny overrides)

| # | Rule | Denies when |
|---|---|---|
| 1 | `step_budget_exceeded` | the run already used its (workflow-vs-policy, whichever is tighter) step allowance |
| 2 | `spend_cap_exceeded` | this step's real cost (the actual refund amount, for a financial tool) would exceed the cap |
| 3 | `shadow_mode` | the workflow is in `SHADOW` — destructive steps never execute here, unconditionally |
| 4 | `not_live` | the workflow hasn't been promoted to `LIVE` yet |
| 5 | `needs_human_approval` | destructive, not allow-listed for autonomous use, and no approver present |
| — | `autonomous_allowlisted` / `human_approved` | the two ways a destructive step is actually allowed to run |

### Staged rollout

`DRAFT → TESTING → SHADOW → LIVE → AUTONOMOUS`, one stage at a time, promoted only by an `approver`
or `admin` — never by the workflow's own author.

---

## Layout

```
agent_platform/
├── data/case_study.json          Cascade Robotics scenario
├── docs/                         01-theory, 02-architecture, 03-src-reference, 04-coverage-map
├── notebooks/02-hands-on.ipynb
├── scripts/                      run_workflow_demo.py, demo_guardrail_failure.py, _scenario.py
├── src/agent_platform/
│   ├── models.py                  Event, WorkflowSpec, Step, Decision, Run
│   ├── identity.py                 the four roles
│   ├── channels.py                 webhook/Slack/email -> canonical Event
│   ├── routing.py                  matching + priority + the entity lock
│   ├── tools.py                    the typed tool registry + arg validation
│   ├── workflows.py                versioning + staged-rollout promotion
│   ├── guardrails.py               the per-step authorization decision
│   ├── orchestrator.py             the durable, idempotent execution loop
│   └── observability.py            run trace rendering + persistence
├── tests/test_platform.py         21 tests
└── INTERVIEW_SCRIPT.md
```

---

## Verified results

Everything below was produced by actually running `scripts/run_workflow_demo.py` and
`scripts/demo_guardrail_failure.py`.

```
Happy path (run_001, wf_ticket_triage v1):
  step 0  draft          APPLIED   $0.02
  step 1  refund (denied, no approval) -> PAUSED_FOR_APPROVAL
  [resume with approver]
  step 1  refund         APPLIED   $0.02 op-cost + real refund amount against the spend cap
  state = completed

Idempotency: issue_refund calls before retry = 1, after retry = 1  (no double-apply)

Durability: run "crashed" after step 0, resumed -> step 0 never re-ran, run completed

Negative controls (all correctly denied):
  wrong_role            - author cannot promote their own workflow
  cannot_skip_stage     - draft cannot jump straight to autonomous
  type_mismatch / missing_required_args - malformed tool args rejected before execution
  not_live              - a draft workflow's destructive step never fires
  spend_cap_exceeded    - a $500 refund against a $50 cap is refused, not clamped
  step_budget_exceeded  - a 30-step misconfigured workflow halts at its 5-step cap
  entity_locked         - a second run against an in-flight ticket is refused
```

**Tests** — 21, all passing, all deterministic (no LLM in this project at all).

### Read these numbers honestly

**This is one tenant, one scenario, run in-process.** The locks, idempotency-key store, and workflow
version store are all plain Python dicts — correct in shape, not backed by anything that survives a
process restart or is shared across workers. That gap is named directly in
`docs/04-system-design-coverage-map.md`'s scale section, not hidden.

---

## What this deliberately does *not* do

Named because an architect should know where the demo ends:

- **No real authoring surface.** There's no visual builder and no natural-language-to-spec
  compiler — `WorkflowSpec` objects are built directly in Python here, standing in for what either
  would emit.
- **The "agent runtime" is a fixed step list, not a real LLM choosing tools dynamically.** The loop
  shape (plan → select → call → observe → iterate, with a hard step cap) is real; the planner isn't.
- **No connector layer or secrets vault.** Tool calls are simulated; nothing here actually
  authenticates against Zendesk, Slack, or a billing system.
- **No PII redaction.** `enterprise_rag_platform`'s `redact_pii()` is directly reusable for this and
  isn't wired in yet.
- **Locks and idempotency keys are in-process only.** Correct logic, wrong storage for anything past
  a single process — see the scale section of `docs/04`.
