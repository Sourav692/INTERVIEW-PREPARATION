# What the security gate should actually verify, and what "one engagement at a time" hides

**What this is:** the same gap-check already done for `enterprise_rag_platform` and `agent_platform`,
applied here. `docs/04-system-design-coverage-map.md` already checks this project thoroughly against
§5 (Problem Type C) and the §7 rollback/canary material — this doc covers where **§6 (Cross-Cutting
Concerns)** and **§7.4 (The Evaluation Stack)** apply *underneath* gates this project already proves
are structurally unskippable. The gates are real. What's genuinely open is **what counts as sufficient
evidence** to pass one of them — and that's exactly the kind of question a "walk me through a gate
that got signed off wrongly" follow-up would probe.

---

## 1. `security_review_passed` is a real gate with an unexamined evidence bar

`docs/04`'s own map is right that this gate is ✅ — `gates.py::sign_off()` genuinely refuses a
`security_reviewer`-only gate from anyone else, and `demo_gate_failure.py` proves the wrong-role
rejection live. That's the structural half. The half not yet examined: **`evidence: str` is a free-text
field.** Nothing in `gates.py` distinguishes *"pentest doc attached"* from a one-line "looks fine,"
because a `str` can't encode what kind of review actually happened.

§7.4's evaluation stack names five distinct layers, and only some of them are the kind of thing a
generic "security review" traditionally checks:

| Evaluation stack layer (§7.4) | Is this what `security_review_passed` usually means? |
| --- | --- |
| Unit — prompt produces schema-valid output | No — this is a code-quality check, not security |
| Component — retrieval/tool-selection/argument-extraction accuracy | No |
| End-to-end — task success rate on the golden set | No — this is `eval_baseline_met`'s job |
| **Adversarial — prompt injection attempts, permission-boundary probes, known-ambiguous queries** | **This is what a security review should mean, and nothing in this project's gate forces it** |
| Production — sampled human review + continuous scoring | No — this is ongoing, not a one-time gate |

**The concrete risk:** as built, a security reviewer could sign `security_review_passed` having only
checked "does this customer have a signed data-processing agreement," never having run a single
adversarial probe against the actual agent that's about to touch their data. The gate structurally
can't tell the difference, because `evidence` doesn't have a shape — it's a sentence, not a checklist.

**What closing this actually looks like** (concept, not built): `evidence` becomes a small structured
object — `{adversarial_probes_run: bool, permission_boundary_tested: bool, dpa_signed: bool, ...}` —
and `sign_off()` refuses the gate unless every required field is present, the same way
`pipeline.py::intake()` already refuses to start an engagement with an unmeasurable success metric.
The pattern already exists in this codebase; it just isn't applied to *what a signature actually
attests to* yet.

## 2. The engagement itself handles customer credentials — and nothing here models that

Days 3–4 ("data readiness: connect sources") means this framework's own tooling holds live credentials
to a real customer's Confluence, Zendesk, Salesforce, or CRM during the two-week window. `docs/04`'s
map correctly flags `agent_platform`'s missing secrets vault as a gap in *that* project — the same gap
exists here, one layer up: **the delivery framework that connects those sources for the FDA running
the engagement has no credential-handling story of its own.**

This matters specifically at Day 3–4 and again at Day 12–13 (limited production against the real
environment) — exactly the two points where this project's own pipeline (`pipeline.py`) is most
exposed, and exactly the two points its own coverage map doesn't mention credentials at all.

**What to say:** *"`data_access_granted` proves the gate — a human with the right role has to attest
access is live. What it doesn't prove is that the credentials enabling that access are ever handled
safely during the engagement — stored in a vault, scoped to only what this specific engagement needs,
rotated or revoked at handover. That's the same secrets-vault gap `agent_platform`'s coverage map
already names for the deployed agent; it applies just as much to the delivery tooling that connects
the sources in the first place, and it isn't modeled here either."*

## 3. Data residency and per-tenant encryption apply to what gets *deployed*, not just how it's tracked

§6.1's last point — per-tenant encryption keys and data residency for regulated customers — usually
gets read as a property of the *target system* (the RAG platform, the agent). It's equally a property
of **the engagement's own artifacts**: the golden set built with the customer's SMEs (Days 3–4) often
*contains real customer data* (real questions, real account details used as examples). If that golden
set is stored the same way for a regulated healthcare customer as for a low-sensitivity SaaS trial,
that's a residency/encryption gap in the delivery framework itself, independent of whatever the
deployed agent does. `accelerators.py::LIBRARY`'s `golden_set_harness` entry is currently a shared,
reusable *tool* — the golden set instances it produces per engagement are customer data, and nothing
in this project's model differentiates their handling by sensitivity tier.

## 4. Running many engagements — the portfolio gap, reframed as a tenancy decision

`docs/04`'s own "scale gap" section already names this honestly (single-`Engagement` model, no
portfolio view, no FDA capacity signal) and correctly calls it verbal-only pending real engagement
data. Worth sharpening one point when it comes up: this isn't only a scheduling problem, it's the same
§6.1 multi-tenancy decision every other project in this series has had to make, applied to the
delivery framework's *own* operational data.

- Are two customers' `Engagement` records, gate evidence, and golden sets **logically separated by a
  field** (this project's current shape) or **physically separated** (the RAG project's per-tenant
  Chroma collections)?
- If an FDA at another company account can query "show me all engagements," does that query
  structurally exclude a competitor's engagement data, or does it rely on remembering to filter?

Naming this as the *same* decision already made explicitly elsewhere in this series (rather than a
new, unrelated scaling problem) is the stronger answer — it shows the multi-tenancy principle
generalizes across every layer of DevRev's stack, not just the customer-facing RAG/agent layer.

---

## What to say if asked directly

*"The gates in my framework are structurally real — you can't sign off `security_review_passed`
without the right role, and `demo_gate_failure.py` proves the wrong role gets rejected. What I'd flag
as the honest gap is that `evidence` is currently free text, so the gate can't yet distinguish a real
adversarial security review — prompt injection attempts, permission-boundary probes, per §7.4's own
evaluation stack — from a one-line sign-off. Closing that is the same pattern already in this
codebase: make evidence a structured checklist gate-checks against, the same way intake already
refuses to start an engagement with an unmeasurable success metric. And the credentials this
framework's own tooling holds during the two-week engagement — to connect the customer's real data
sources — have no vault story yet either; that's the same secrets-handling gap `agent_platform`'s
coverage map names for the deployed agent, one layer earlier in the process."*
