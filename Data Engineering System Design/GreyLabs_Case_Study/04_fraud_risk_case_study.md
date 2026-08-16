# Interview Script — Case Study 4: Real-Time Fraud/Risk Signal During a Servicing Call

**Role context:** Director, Forward Deployed Engineering — GreyLabs AI
**Scenario:** Live fraud-risk detection during a credit-limit-increase servicing call

---

## Opening Prompt (What the Interviewer Says)

> "A customer calls in claiming to be a cardholder wanting to increase their credit limit. Design how the Voice AI system detects potential fraud signals in real-time during the call and decides whether to proceed, escalate, or block."

---

## Step 1 — Clarify Requirements

**Script:**

> "A few things I'd want to pin down first.
>
> Is voice biometric enrollment already in place for this customer base — meaning, can the system compare the caller's voice against a known voiceprint — or should I assume that's not available and design around other signals? I'll assume it may or may not be available and design for both cases.
>
> Second, what existing risk data can this system access in real time — recent account activity, past fraud flags, device or number reputation? I'll assume there's a backend risk system I can query, since building fraud detection from scratch inside this call flow wouldn't be realistic.
>
> Third — what's the acceptable false-block rate? Blocking a legitimate customer's request is also a cost, not just a security win, so I'd want to know how the business weighs that trade-off before setting thresholds."

---

## Step 2 — High-Level Architecture

**Script:**

> "I'd design this as a layered, real-time risk-scoring system running alongside the conversation.
>
> **Multi-source real-time lookup:** as the call starts, the system pulls recent account activity, historical fraud flags, and — if enrolled — a voice-biometric match score, from backend systems. This means several sub-second calls to different services during a live call, not just one lookup.
>
> **Tiered risk scoring, not binary:** I wouldn't design this as a simple pass/fail. Low risk — proceed automatically. Medium risk — trigger step-up verification, like an OTP or security questions, live during the call. High risk — escalate to a human fraud specialist immediately, without completing the request.
>
> **Latency-aware signal splitting:** some checks are fast enough to run synchronously before responding to the customer — account activity lookup, voice match if available. Others, like deeper behavioral pattern analysis, might be too slow to block on live and would run asynchronously, flagged for post-call review rather than blocking the conversation.
>
> **Immutable decision logging:** every proceed, escalate, or block decision gets logged with the exact signals that triggered it — this becomes evidence in any real fraud investigation, so it needs to be tamper-evident and complete, not a best-effort log."

---

## Step 3 — Defend Key Design Decisions

| Decision | What to Say |
|---|---|
| Tiered scoring vs. binary block/allow | "A binary system either blocks too many legitimate customers or misses real fraud — a tiered response with step-up verification captures the middle ground, which is most of real-world traffic." |
| Sync vs. async signal checks | "This is a real latency-versus-completeness trade-off, and I wouldn't pretend it isn't. I'd want the business to weigh in on which signals are worth the latency cost of running synchronously." |
| Immutable audit logging | "In a fraud case, the log of *why* a decision was made is often more important after the fact than the decision itself — auditors and dispute teams need to reconstruct exactly what the system saw." |
| Voice biometric as one signal, not the only one | "I wouldn't design this to depend entirely on voice match, since not every customer will be enrolled, and voice biometrics can have their own failure modes — it should be one weighted signal among several, not a single point of failure." |

---

## Step 4 — Where to Lean on Real Experience

**Script:**

> "The multi-source real-time lookup pattern is close to designing an agentic system that needs to call multiple tools or APIs mid-conversation and synthesize the results before responding — that's a pattern I've built directly with tool-use and MCP-based architectures. And the idea of tiered, weighted risk scoring rather than a single hard rule reflects the kind of enterprise architecture judgment I've applied in BFSI client work, where a single wrong binary decision has outsized cost."

---

## Step 5 — Honest Gap Acknowledgment

**Script:**

> "I don't have hands-on experience building a fraud-scoring model itself — that's usually a specialized risk/fraud data science function, not something an FDE builds from scratch. What I'd bring is the systems design around it: how the scoring signal gets integrated into the live call flow, how the tiered response is orchestrated, and how the audit trail is built — and I'd expect to partner closely with GreyLabs' or the client's existing fraud/risk team on the actual scoring model rather than claim that as something I'd own solo."

---

## Anticipated Follow-Ups

1. **"What if the voice-biometric check and the account-activity check disagree — one says high risk, one says low risk?"**
   → Script: "I'd design the overall score as a weighted combination rather than requiring unanimous agreement, with clear precedence rules — for example, a strong negative signal like a recent fraud flag on the account should be able to override a positive biometric match, since biometric spoofing is a known attack vector."

2. **"How do you avoid this system becoming a bad customer experience for legitimate customers who get flagged?"**
   → Script: "This is exactly why I'd push back on binary blocking — step-up verification for medium risk keeps the legitimate customer moving forward with minor friction, rather than a hard stop. I'd also track false-escalation rate as a real metric, not just fraud-catch rate, since over-flagging erodes trust in the whole system."

3. **"How would you test this system before it goes live with real customers?"**
   → Script: "I'd want a shadow-mode period — the fraud-scoring logic runs against live calls but doesn't yet act on its decisions, just logs what it *would* have done — compared against actual outcomes and the existing fraud team's judgment, before letting it make live escalation decisions."

---

## Closing Line

> "The theme across this design is that fraud detection here isn't a single model decision — it's an orchestration problem across multiple real-time signals, with a tiered response and a defensible audit trail. That orchestration is the FDE's job; the underlying scoring model is a partnership with a specialized risk team, and I'd be clear about that boundary in how I scope the work."
