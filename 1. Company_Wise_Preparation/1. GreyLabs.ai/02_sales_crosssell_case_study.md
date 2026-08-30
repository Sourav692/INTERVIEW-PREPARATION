# Interview Script — Case Study 2: Outbound Sales / Cross-Sell Voice Agent

**Role context:** Director, Forward Deployed Engineering — GreyLabs AI
**Scenario:** Outbound cross-sell calling with real-time intent detection and human handoff

---

## Opening Prompt (What the Interviewer Says)

> "Design the system for a Voice AI agent that makes outbound calls to a bank's existing customers to cross-sell a credit card, handles objections in real-time, and hands off to a human agent when the customer shows strong buying intent — for a bank running 200,000 outbound calls/week."

---

## Step 1 — Clarify Requirements

**Script:**

> "A few things I'd confirm before designing.
>
> First — this is outbound, which means the system controls when calls happen, not just how they're handled. That brings in Do Not Call registry compliance and calling-time-window regulations as gating logic *before* a call is even dialed, not just during the conversation.
>
> Second, on handoff: what does 'strong buying intent' mean operationally — is there an existing definition from the sales team, like specific questions about rate or limit, or do I need to define that scoring criteria myself as part of this design? I'll assume I need to propose it.
>
> Third, volume — 200K calls/week is roughly 28K/day. I'd want to know the outbound dialer's concurrency limits, since that's often the actual bottleneck in outbound systems, not the AI processing itself."

---

## Step 2 — High-Level Architecture

**Script:**

> "I'd break this into four pieces.
>
> **Pre-call gating layer:** before any call is dialed, check DNC registry status, consent records, and permitted calling windows. This is a hard block, not a soft check — a violation here is a direct regulatory issue.
>
> **Live conversation layer:** streaming STT feeds the voice agent's response logic, same pattern as before. But here the interesting part is objection handling — the agent needs a structured decision tree or retrieval-augmented response system to handle pushback on rate, tenure, or trust concerns, not just answer a fixed script.
>
> **Real-time intent scoring:** running alongside the conversation, a lightweight model tracks buying signals — positive sentiment shifts, specific product questions, requests for next steps. When a threshold is crossed, that triggers the handoff.
>
> **Handoff and state transfer:** when transferring to a human closer, the full conversation context — what's been said, objections raised, specific interest signals — needs to transfer instantly. This is a session-state design problem: I'd want a shared session object, keyed by call ID, that the human agent's screen pulls immediately on handoff, not a summary generated after the fact that adds latency."

---

## Step 3 — Defend Key Design Decisions

| Decision | What to Say |
|---|---|
| Pre-call DNC/consent check | "This has to be a hard gate, synchronous, before dialing — not something that can fail open. A single DNC violation is a real compliance and reputational risk." |
| Intent scoring threshold | "I'd start conservative — bias toward handing off too early rather than too late, since a missed high-intent customer is a lost sale, and I'd tune the threshold against actual sales team conversion data rather than guess a number upfront." |
| Session-state handoff | "The human agent should never have to ask the customer to repeat themselves — that kills trust instantly. I'd design the handoff as a live state object, not a post-call summary." |
| Objection handling design | "I'd lean toward a retrieval-augmented approach over a rigid decision tree, so the agent can pull from a bank of approved response patterns rather than being brittle on unexpected objections — but that needs to be paired with strict guardrails on what claims the agent is allowed to make about rates or terms." |

---

## Step 4 — Where to Lean on Real Experience

**Script:**

> "The objection-handling and retrieval piece maps directly to agentic AI work I've done — building multi-agent systems with LangGraph, where an agent needs to reason over a knowledge base rather than follow a fixed script. That's a pattern I've implemented, not just read about. And the compliance-gating logic follows the same governance discipline I've applied with Unity Catalog-style access control — hard gates before action, not soft warnings after."

---

## Step 5 — Honest Gap Acknowledgment

**Script:**

> "If asked exactly what the intent-scoring threshold should be, I wouldn't invent a number. I'd say: this needs to be calibrated against the sales team's actual historical conversion data — what conversation patterns preceded a real sale versus a false positive — and I'd treat the first few weeks post-launch as a tuning period with close sales-team collaboration, not a set-and-forget threshold."

---

## Anticipated Follow-Ups

1. **"What happens if the AI oversells or makes an inaccurate claim about the product?"**
   → This is a guardrails question. Script: "The agent's claims need to be constrained to an approved, versioned knowledge base — not free-generated. Any response touching rates, fees, or eligibility should be retrieval-based from an approved source, with a hard rule that anything outside that scope triggers human handoff rather than the AI improvising."

2. **"How do you measure success for this system beyond just call volume?"**
   → Script: "Conversion rate is the obvious one, but I'd also track handoff precision — are the calls we're escalating actually converting at a higher rate than random calls — and false-handoff rate, since escalating too aggressively burns human agent time and defeats the automation's purpose."

3. **"How would this differ if it were inbound instead of outbound?"**
   → Script: "The pre-call gating layer disappears since the customer initiated contact, but intent scoring and handoff logic stay largely the same. Inbound also usually has higher urgency and lower tolerance for AI missteps, since the customer chose to call — I'd probably set a lower handoff threshold for inbound."

---

## Closing Line

> "The core tension in this design is speed versus safety — the agent needs to move a sales conversation forward in real time, but every claim it makes needs to be traceable back to an approved source. That balance is exactly the kind of judgment call an FDE has to make repeatedly at each customer deployment, not just design once."
