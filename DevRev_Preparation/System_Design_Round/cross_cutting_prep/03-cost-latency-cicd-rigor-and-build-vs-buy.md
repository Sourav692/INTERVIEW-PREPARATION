# Caching, streaming, CI/CD rigor, and build vs. buy

Cross-cutting topics for any AI platform system design round. None of this needs a codebase — it's
architecture to describe on a whiteboard.

---

## 1. Semantic caching

A simple cache keyed on the exact question (plus whatever filters apply) is **exact-match**: two
questions that mean the same thing but are worded differently are two different cache keys, and the
second one recomputes everything from scratch even though the first one already answered it.

The next step is **semantic caching**: embed the incoming question, check it against previously
answered questions' embeddings, and treat a hit above a similarity threshold as a cache hit — serving
the prior answer instead of recomputing.

**Why this is a genuinely different problem, not just a bigger cache:**
- **A similarity threshold introduces a correctness risk exact-match never has.** Two questions can be
  close in meaning but expect different answers ("refund policy for EU customers" vs. "refund policy
  for US customers") — a naive similarity cache risks serving a *wrong* answer confidently, not just a
  *stale* one. The threshold has to be tuned conservatively, and the safest version never matches
  across different permission scopes or tenants, even if the wording is close.
- **Invalidation is harder.** An exact-match cache clears cleanly when the underlying content it
  answered from changes. A semantic cache has to decide when a stored answer's whole *neighborhood* of
  similar questions is no longer trustworthy — for example, after any relevant document changes, not
  only the one that produced the original cached answer.

## 2. Token streaming

Returning a complete answer in one shot is the simplest design. The next step, named explicitly in
most system design guides: **stream tokens to the user so perceived latency drops, even though total
latency doesn't change.**

**The point worth being precise about:** streaming is a *perceived*-latency fix, not a *total*-latency
fix — generation still takes exactly as long. What changes is when the user sees the *first* token
versus the *last* one. This matters most for interactive chat (where sub-second first response is the
whole point) and matters much less for an async reply that has minutes to spare. Streaming is
therefore a **channel-layer decision** — the underlying retrieve-and-answer pipeline doesn't change;
only whether the final step streams token-by-token depends on which channel is asking.

**Why a refusal decision has to happen before streaming starts, not during it:** if a system needs to
decide "do I even have enough information to answer" before generating, that decision has to be made
*before* the first token streams — a partially-streamed answer that then gets retracted mid-flight is a
worse experience than a clean up-front refusal. Streaming only ever applies to the final answer step,
after the "should I answer at all" decision is already settled.

## 3. Nightly regression runs — a different trigger than your own changes

A quality gate that only runs when *you* change a prompt misses a real risk: **the model provider can
silently change what a model version points to, without any change on your side at all.** Your
accuracy or safety metrics can quietly drift with zero commits to explain why.

**The fix:** run the same evaluation suite on a schedule (nightly), independent of any code change,
comparing against the last known-good baseline. This is a scheduling change around infrastructure that
already exists for any project with a real eval suite — worth naming precisely as that: the eval
suite itself doesn't need to be rebuilt, it needs a second trigger — a schedule, not only a
code-change hook — because the thing that can regress isn't only your own work.

## 4. Statistical rigor in A/B testing

LLM outputs vary from run to run even with an identical prompt and identical inputs. A naive A/B test
comparing two prompt or model variants on a small sample can easily be looking at noise, not a real
difference — and this matters *more* for LLM outputs than for a typical product metric, because the
natural variance is higher to begin with.

**The practical answer:** decide up front what size of improvement you actually care about detecting,
size the sample to reliably detect an effect that large (ordinary statistics, nothing LLM-specific),
and don't declare a winner before reaching that sample size — easy to state, easy to skip under
deadline pressure, which is exactly why it's worth having as a rehearsed answer rather than winging it
live.

## 5. Unit-level testing for prompts

A full evaluation suite (does the answer sound right, is it grounded, is it safe) is expensive and
slow to run on every single change. A cheaper, faster layer sits in front of it: **does this prompt, in
isolation, even produce output that parses correctly** — the right structure, every required field
present, nothing malformed — for a small set of known test inputs.

This is the equivalent of a type check running before the full test suite: fast, cheap, and it catches
a whole class of failure (a broken template, a missing variable) that the expensive full evaluation
would also eventually catch, just far more slowly. It runs on every prompt change, before the real
evaluation suite even starts — a cheap first gate, not a replacement for the real one.

## 6. Build vs. buy — a decision worth arguing explicitly

The general principle: **buy the undifferentiated layers, build the customer-specific logic.**
Applied across a typical AI platform stack:

| Layer | Default | Build only when |
| --- | --- | --- |
| Identity / login | Use the customer's own identity provider | Never — this is always a solved problem someone else already owns |
| Secrets storage | A managed vault product | Almost never — security infrastructure is a place where "we built our own" is a red flag, not a differentiator |
| Search / vector index | A managed search product | Self-hosted only at very large scale, or when data can't legally leave a specific environment |
| Monitoring | An existing, standards-compatible monitoring platform | A thin custom layer only for the domain-specific fields the platform doesn't yet support — layered on top, not instead of |
| **The permission rules, the retrieval tuning, the prompt design, the actual business workflows for this customer** | — | **Always build.** This is the differentiated value — nothing off the shelf can encode what's specific to this customer's data, policy, and process |

**The one-line version:** the line isn't "build everything to prove capability" or "buy everything to
move fast" — it's whether a component encodes something specific to this customer's business. Identity,
secrets, and search infrastructure are solved problems available from a vendor. The permission logic,
the retrieval tuning, and the actual workflow behavior are the parts that only exist because of who
the customer is — that's where engineering time belongs.

---

## What to say if asked directly

*"Exact-match caching is the safer starting point over semantic caching, since a similarity-threshold
cache risks confidently serving a wrong answer for two questions that are close in wording but expect
different answers. Streaming is a channel decision, not a core pipeline decision — and it only ever
applies after a 'do I have enough information to answer at all' check has already run, never before,
since retracting a partially-streamed answer is worse than a clean up-front refusal. And on
regression: a quality gate that only fires on my own changes misses the case where the model provider
silently changes something underneath a model version — that needs a scheduled run, independent of
any change I make."*
