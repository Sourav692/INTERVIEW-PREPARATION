# Interview Script — Case Study 3: Multi-Language Voice Servicing

**Role context:** Director, Forward Deployed Engineering — GreyLabs AI
**Scenario:** Regional-language servicing agent with confidence-based human escalation

---

## Opening Prompt (What the Interviewer Says)

> "Design the pipeline for a Voice AI servicing agent that handles customer queries in Hindi, Tamil, Bengali, and English — for an insurer with call volume split roughly 60% regional language, 40% English — and must route to human agents when confidence is low."

---

## Step 1 — Clarify Requirements

**Script:**

> "A few clarifying questions first.
>
> Is the customer's language known ahead of time — say, from account records or IVR selection — or does the system need to detect it live from the first few seconds of speech? I'll assume live detection is needed as the general case, since account records won't always be reliable.
>
> Second, on 'low confidence' — is that about the AI not understanding the customer, or about the AI understanding the question but being unsure of the correct policy answer? These are different failure modes and I'd want to design for both.
>
> Third — insurance servicing likely means the agent is answering questions with real financial and coverage implications. I'd treat wrong answers here as a compliance risk, not just a customer-experience one."

---

## Step 2 — High-Level Architecture

**Script:**

> "I'd structure this in three layers.
>
> **Language detection and routing, upfront:** within the first few seconds of the call, detect the spoken language — either from an IVR pre-selection or a lightweight language-ID model on the initial audio — and route to the matching STT and NLU model set. I'd avoid trying to run a single multilingual model across all four languages if language-specific models perform meaningfully better, which is usually the case for Indian regional languages today.
>
> **Confidence-scored response generation:** every AI response carries two confidence signals — transcription confidence, meaning did we understand what the customer said, and answer confidence, meaning are we sure this is the correct policy information. Either one falling below a threshold triggers escalation.
>
> **Escalation and fallback routing:** below-threshold calls route to a human agent, ideally one matched to the same language, with the partial transcript and confidence reasoning passed along so the human isn't starting cold."

---

## Step 3 — Defend Key Design Decisions

| Decision | What to Say |
|---|---|
| Language-specific models vs. one multilingual model | "I'd default to language-specific STT/NLU pipelines, because regional language model quality in India today is genuinely uneven — treating all four as equally capable would be the wrong assumption to build on." |
| Dual confidence scoring (transcription + answer) | "These are different risk types. Bad transcription is a technical failure; a wrong policy answer is a compliance and trust failure. Conflating them into one confidence score would hide which problem you're actually solving." |
| Escalation threshold varies by language | "I'd expect — and design for — higher escalation rates in regional languages initially, since those models are typically less mature. I wouldn't set one universal threshold across all languages and assume it's fair." |
| Human agent language-matching on escalation | "Handing a Tamil-speaking customer to an English-only human agent after an AI failure compounds the bad experience. I'd route by matched language wherever staffing allows." |

---

## Step 4 — Where to Lean on Real Experience

**Script:**

> "This routing-and-confidence pattern is close to how I've designed multi-agent systems that need to choose between specialized sub-agents based on a task classification step — same underlying principle of 'route to the right specialist, don't force one model to do everything.' And the idea of treating model quality as uneven across segments, rather than assuming uniform performance, is something I've had to be disciplined about in enterprise AI CoE work, where client expectations often assume AI performs consistently across all inputs when it genuinely doesn't."

---

## Step 5 — Honest Gap Acknowledgment

**Script:**

> "If asked for the exact confidence threshold per language, I wouldn't invent numbers — regional language STT accuracy varies by vendor and keeps improving, so I'd want to benchmark the actual model against a labeled sample of real customer calls per language before setting thresholds, and expect Tamil or Bengali thresholds to need to be more conservative than Hindi or English initially, based on typical model maturity gaps."

---

## Anticipated Follow-Ups

1. **"How would you measure whether the system is actually working well per language?"**
   → Script: "I'd track escalation rate, resolution accuracy on escalated calls, and customer satisfaction, all segmented by language — not blended into one number, because a blended metric would hide a badly-performing regional language behind a strong English number."

2. **"What if a customer code-switches — mixes Hindi and English mid-sentence, which is common in India?"**
   → Script: "This is a real failure mode for naive language-ID systems. I'd want the STT layer itself to handle code-switching, which some modern multilingual ASR models do reasonably well, rather than relying purely on an upfront single-language routing decision — and I'd flag this as something to explicitly test for during vendor evaluation, not assume away."

3. **"How do you improve regional language accuracy over time?"**
   → Script: "Every escalated or corrected call becomes labeled training data, fed back into a retraining loop — segmented by language so you're specifically closing the gap on the weaker languages, not just improving the aggregate."

---

## Closing Line

> "The core discipline here is refusing to treat all four languages as equally AI-ready just because the architecture looks the same on paper. Segmenting metrics and thresholds by language is what actually protects the customer experience — and it's the kind of nuance that matters a lot more in an India-BFSI context than it would in a single-language market."
