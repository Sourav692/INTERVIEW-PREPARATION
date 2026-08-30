# Interview Script — Case Study 1: Collections Voice AI Pipeline

**Role context:** Director, Forward Deployed Engineering — GreyLabs AI
**Scenario:** Real-time compliance-monitored collections calling at scale

---

## Opening Prompt (What the Interviewer Says)

> "Design the data pipeline for a Voice AI collections agent — from a live call happening with a bank customer, through transcription, real-time compliance monitoring, post-call analytics, and CRM/collections-system updates — for a large NBFC handling ~500,000 calls/month."

---

## Step 1 — Clarify Requirements (say this out loud first)

**Script:**

> "Before I sketch the architecture, let me confirm a few things — these change the design meaningfully.
>
> First, on real-time needs: does compliance monitoring need to interrupt or nudge the call *while it's happening*, or is post-call flagging sufficient? I'll assume live intervention is required, since that's usually the actual business need in collections.
>
> Second, on volume: 500K calls/month is roughly 17K/day. Assuming a business-hours concentration, that's likely 2,000–3,000 concurrent call-streams at peak. I'll design around that.
>
> Third — this is now a regulated data system, not just an analytics pipeline. Voice recordings plus PII plus financial data means DPDP Act and RBI-adjacent compliance are first-class constraints, not an afterthought.
>
> Fourth, downstream consumers: I'll assume the collections CRM, a compliance audit system, and an agent QA/coaching team all need to consume this data, each with different latency needs."

*(Pause here — a real interviewer will often confirm or adjust one of these assumptions. Let them.)*

---

## Step 2 — High-Level Architecture (three tiers)

**Script:**

> "I'd split this into three tiers, by latency requirement, because trying to serve all of them from one pipeline is where these designs usually break.
>
> **Tier A, the live call path**, needs sub-second to low-second latency. Voice stream goes through a streaming speech-to-text engine, and a lightweight NLU/rules layer scans the live transcript for compliance triggers — missing disclosures, prohibited language, threatening tone. If something crosses a threshold, it nudges the live agent or escalates to a supervisor. This tier has to be isolated from heavier batch systems — I'd put a pub-sub layer, something like Kafka, in front of it so ingestion and processing are decoupled.
>
> **Tier B, near-real-time post-call**, runs in seconds to minutes. Once the call ends, the full transcript gets sentiment and outcome tagging — promise-to-pay, dispute, refusal, escalation — and that event feeds three places: the CRM, an immutable compliance audit log, and an agent performance dashboard.
>
> **Tier C, batch and analytical**, is where I'd apply a medallion-style Lakehouse pattern — raw call logs, then cleaned and enriched transcripts, then business-level aggregates. This feeds collections-effectiveness reporting, model retraining datasets, and regulatory reporting exports."

---

## Step 3 — Defend Key Design Decisions

**Script — walk through this table verbally if asked "why":**

| Decision | What to Say |
|---|---|
| Streaming vs. batch for compliance | "Live-call flagging has to be streaming — a compliance breach caught after the fact is already a legal exposure, not something a nightly batch job can fix in time." |
| PII handling | "Raw audio sits in a separate, tightly access-controlled, encrypted store with short retention. Before anything reaches analytics or dashboards, PII gets tokenized or redacted — account numbers become something like `[ACCT_REDACTED]`. Access is role-based and logged." |
| Data retention | "Retention is tiered — raw audio shortest, transcripts longer, aggregates indefinite — driven by both storage cost at this volume and regulatory retention windows, which differ by data type." |
| Idempotency | "Telephony systems retry and can duplicate call events, so every event carries an ID and gets deduplicated on ingestion. Otherwise you risk double-counting a payment promise or double-firing a compliance alert." |
| Immutable audit trail | "The compliance log is append-only and separate from mutable operational tables — BFSI auditors need a tamper-evident trail, that's non-negotiable." |

---

## Step 4 — Where to Lean on Real Experience

**Script:**

> "This maps closely to patterns I've built in production. At Databricks, I've worked with medallion architecture — raw to enriched to aggregate — on real client data, not just in theory. I've also worked directly with Unity Catalog-style governance, which is the same pattern I'd apply here for PII access control — role-based, logged, auditable. And Delta Lake's ACID guarantees are directly relevant to how I'd guarantee the CRM doesn't get a duplicate or lost update from this pipeline."

---

## Step 5 — Honest Gap Acknowledgment (say this if pushed on latency numbers)

**Script:**

> "If you're asking for an exact latency budget on the compliance nudge — say, does it need to land in 1 second or 3 seconds — I don't want to guess a number I haven't validated. My instinct is somewhere in the 2–3 second range based on how live-agent-assist tools typically work, but I'd want to benchmark against the actual STT vendor's P95 latency and validate the number against agent UX research before committing to a spec. That's the honest answer rather than a made-up one."

---

## Anticipated Follow-Ups (from earlier prep — quick reference)

1. **"How would you scale this to 5M calls/month?"**
   → Identify Tier A (live compliance) as the bottleneck, not Tier C. Shard by region/client. Decouple ingestion from processing so bursts don't get dropped. Name cost-per-call as a real business conversation at 10x scale.

2. **"How do you handle a downstream CRM outage?"**
   → Live call must never depend on CRM uptime. Queue with retry + idempotent replay. Compliance-critical paths get their own dead-letter queue and immediate alerting, separate from routine CRM sync.

3. **"How do you know your compliance model isn't producing false positives/negatives at scale?"**
   → Continuous human-in-the-loop sampling. Track precision/recall, not just accuracy — bias toward catching more (false negatives are costlier than false positives here). Retraining tied to both schedule and regulatory-change triggers.

---

## Closing Line (optional, use if the round is wrapping up)

> "The thread running through all of this is: decouple the critical live-call path from everything else, and validate assumptions with real data rather than guessing numbers I don't have. That's the same discipline I'd bring to building this out as an actual FDE deployment, not just a whiteboard design."
