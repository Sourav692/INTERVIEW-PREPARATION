# Chapter 11 — Orchestration

> *(Printed as "Chapter Ten" in the book's own running heads — see the numbering note in
> Chapter 3. This guide follows the outer Table of Contents, so this is "Chapter 11" for citation
> purposes.)*

## The Simple Version, First

Imagine a busy restaurant kitchen. The head chef doesn't just hand out a printed schedule of
"soup at 6, salad at 6:05, entrée at 6:15" and walk away. The real job is what happens when the
delivery truck is late, the salad station catches fire, or two orders for table 12 both hit the
grill at once. **A schedule that only works when nothing goes wrong isn't a kitchen — it's a
poster on the wall.**

**Orchestration** is the part of a data platform that decides what runs, when, and in what order.
The whole chapter comes down to this: **orchestration is a contract, not a calendar.** Drawing
boxes and arrows and picking run times is the easy 20%. The real 80% is what happens when
something upstream is late, a job succeeds but produces wrong data, or two copies of the same job
accidentally try to write the same thing at once.

Everything below builds on that one idea.

---

## What You'll Be Able to Say by the End

*(These are the book's own scripted interview lines — say them close to word-for-word.)*

> "The dependency graph is the easy part. The hard part is sensor timeouts, SLA misses, and the
> job that looks healthy but isn't."
>
> "A DAG that can't be rerun is a liability. Idempotent operators aren't optional; they're the
> thing that makes the 2 AM rerun succeed."
>
> "Backfill windows are a design decision, not an operational afterthought. Partition-aware
> backfills are why a DAG recovers in 30 minutes instead of 8 hours."
>
> "Task concurrency limits are where most orchestrators get misconfigured, and where most data
> incidents have their root cause."
>
> "SLA tiers let me design different blast-radius budgets per DAG, instead of pretending every
> pipeline is equally critical."

---

## Why One Team Sleeps Through the Night and Another Doesn't

Two teams run about 200 scheduled pipelines each (called **DAGs** — short for "directed acyclic
graph," which is just a fancy way of saying "a map of which task has to finish before the next one
starts"). Both use the same tool. Both promise the business "99.9% on-time."

**Team A** gets paged three times a week. Incidents drag on for two to eight hours. The pattern is
almost always the same: something upstream didn't land on time, a downstream job timed out
waiting for it, that job failed, and by the time someone notices the morning dashboard is wrong,
hours have passed.

**Team B** gets paged twice a month. When it happens, it's resolved in under 30 minutes — because
the on-call person reruns just the one broken piece, instead of trying to figure out why the whole
thing fell over.

Same tools, similar team size, similar complexity. **The difference is that Team B treats
orchestration as a contract, and Team A treats it as scheduling.**

Scheduling — picking when things run and drawing the arrows between them — is the easy half.
The hard half is what happens when things *don't* go according to plan.

---

## Idea 1: A Task That Can't Be Safely Repeated Isn't Ready for Production

Every orchestration system eventually fails at something. A network hiccups, an external service
has a bad five minutes, a worker machine restarts mid-task. **This isn't a rare edge case — it's
the normal, expected state of any system running continuously over months.** So the question
isn't "will this task ever need to be retried?" It's "what happens when it is?"

Imagine a task that adds a row to a report every time it runs. If that task runs successfully once,
you get one row — correct. But if it partially fails and gets automatically retried, and the retry
*also* appends a row on top of whatever the first attempt already wrote, you now have a duplicate,
and nobody told you. **A task like this is a landmine: it works fine until the one day it gets
retried, and then it silently corrupts your data.**

An **idempotent task** is one where running it twice produces exactly the same result as running
it once. This is the single most important design property in the whole chapter, because
everything else — retries, backfills, recovering from a crash — depends on it being true.

Three ways of building this in practice, in order of how often they come up:

- **"Replace this day's data" instead of "add to it."** The task writes to one specific,
  clearly-defined slice of data (say, "everything for June 15th") and *replaces* whatever was
  there, rather than appending. Rerunning it just re-does that same replacement — same result,
  every time. This is the natural fit for data organized by date.
- **"Insert-or-update" with duplicate removal.** For data that has a stable, unique ID per row
  (rather than being organized by date), the task removes duplicates from its input first, then
  applies an insert-or-update operation keyed on that ID. Because the operation is keyed on a
  stable ID, running it again just harmlessly re-applies the same result.
- **Write somewhere temporary, then atomically swap it into place.** The task writes its output to
  a staging location first, and only *after* it's fully done does it swap that staging output into
  the "real" location in one instant, all-or-nothing step. A partial or failed run never leaves a
  half-finished result sitting where downstream consumers can accidentally read it.

> **❌ Anti-Pattern**
> "We'll just retry on failure" without making the task idempotent first. Retrying a
> non-idempotent task is a recipe for silently corrupting your data under load. Idempotency has to
> come *before* you turn retries on, not after.

```python
# src/code-examples/ch10/airflow_idempotent_dag.py
# Daily ETL DAG: idempotent writes, exponential retry backoff,
# an SLA callback that pages someone, and bounded concurrency.
default_args = {
    "owner": "data_platform",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "sla": timedelta(hours=4),
    "execution_timeout": timedelta(hours=3),  # kill long-running tasks
    "on_failure_callback": paging_callback,
}
with DAG(
    dag_id="daily_user_rollup",
    max_active_runs=1,  # critical for partition-sensitive DAGs — see Idea 3
    ...
)
```

---

## Idea 2: Retries Are Supposed to Happen — Design for Them on Purpose

Transient failures — a brief network blip, an external service having a rough moment, a worker
restarting — are the **normal state of the world**, not an exception. A pipeline that gives up and
pages a human the instant something fails once is treating "normal" as an emergency.

**The standard, sensible default: retry a task up to 3 times, waiting a bit longer each time**
(5 minutes, then 10, then 20 — this growing wait is called "exponential backoff"). This handles
roughly 80% of transient pain automatically, with zero human involvement. If a task is going to
succeed on retry, it usually succeeds quickly. If it's hitting a *real* problem — not just a
transient blip — it fails definitively after those three attempts instead of quietly flapping for
an hour.

**But remember Idea 1: retries only work safely if the task is idempotent.** A retry on a
non-idempotent task is exactly how you get a partial write followed by a second write stacked on
top of it.

---

## Idea 3: Two Copies of the Same Job Running at Once Is How Data Gets Silently Wrong

This is the most common real-world orchestration incident, and it's almost always caused by one
misconfigured setting.

Most orchestration tools let you cap how many copies of the *same* scheduled pipeline can be
running at the same time. Airflow's default cap is 16 — meaning up to 16 separate runs of the
exact same daily job could, in theory, be executing simultaneously. That default is fine for jobs
where it doesn't matter if multiple copies run in parallel. **It is very much not fine for a job
where each run writes to a specific day's data slice** — because now you can have two or more runs
racing to write the *same* slice, and whichever one happens to finish last silently overwrites the
other's work, with no error, no warning, nothing.

**When does this actually happen?** Classically: the scheduler goes down for a few hours (a
weekend outage, say), and when it comes back, it tries to "catch up" on every schedule it missed —
potentially launching many overlapping runs back to back, all racing for the same underlying data.

> **⚠️ War Story**
> A data platform team ran 200 scheduled pipelines. One core pipeline computed daily revenue from
> the main transactions table, and its "how many copies can run at once" setting had been left at
> the tool's default of 16. One morning, an upstream data format change caused a dependency check
> to time out on its first run. The system automatically retried — but meanwhile, the scheduler
> also launched the *next* day's scheduled run, and then the one after that, stacking up several
> missed schedule windows. Within three hours, eight overlapping copies of the same pipeline were
> all fighting over the same day's data slice. Each one technically used the safe "replace this
> day's data" pattern from Idea 1 — but each was working from a *different* snapshot of the
> upstream data, because the underlying data had kept changing between when each copy started. The
> final result in that day's slice was whichever copy happened to finish last. The next morning's
> dashboards showed revenue numbers that made no sense to anyone. The investigation took eight
> hours. The actual fix was one line: capping concurrent runs of that pipeline at 1. The real
> lesson wasn't that idempotency (replace-don't-append) was wrong — they already had that. It was
> that **idempotency plus a concurrency cap is the actual safety contract. Either one without the
> other doesn't protect you.**

> **✅ Pattern**
> For any pipeline where each run writes to a specific, shared slice of data, cap it to exactly
> one run at a time. Say this out loud unprompted in an interview — the too-permissive default is
> the single most common real-world misconfiguration at medium scale.

---

## Idea 4: Waiting on Something Upstream Needs Its Own Careful Design

A very common pattern: pipeline B shouldn't start until pipeline A has finished producing its
data. The mechanism that waits for this is usually called a **sensor** — it periodically checks
"is the thing I'm waiting for ready yet?"

**Here's the subtlety that trips people up:** a naive sensor holds onto a worker slot for its
*entire* waiting period, doing nothing but repeatedly checking. If you have 100 pipelines all
waiting on something upstream this way, that's 100 worker slots tied up purely on polling, doing
zero actual work. At a small scale this is invisible. At a medium scale, this alone is enough to
make the whole scheduling system start slowing down.

**The fix:** use a waiting mode that releases the worker slot in between checks, instead of
holding onto it the whole time. This trades a small amount of extra latency for a much healthier,
much more scalable system. Newer tools go a step further and let a completed pipeline directly
"announce" that its output is ready, so downstream pipelines don't need to poll for it at all —
they just get notified.

> **🚩 FAANG Signal**
> When you mention a sensor waiting on an upstream dependency, the interviewer wants to hear you
> immediately flag the polling-vs-release distinction. Naming it unprompted signals you've run
> this at a scale where it actually mattered, not just read about it.

---

## Idea 5: When Something Breaks, How Much Do You Have to Redo?

When a pipeline fails and needs to be fixed, there are two very different-sized responses:

- **Rebuild everything from scratch.** Rerun every date, every step, from the very beginning.
  Simple to reason about, but slow — and it touches data that was already correct.
- **Fix just the broken piece.** Rerun *only* the specific failed step, for the specific date that
  failed. Dramatically faster — but this only works safely if that task is idempotent (Idea 1),
  since you're deliberately re-doing something that may have partially run already.

Teams that haven't invested in making their tasks safely re-runnable end up defaulting to the
first option every time — rebuilding an entire multi-day pipeline because one day's data had a
problem. That's the difference between a 30-minute fix and an 8-hour one.

> **✅ Pattern**
> Every pipeline you ship should come with a rerun plan. The exact rerun command belongs in that
> pipeline's own documentation, gets tested somewhere safe before it's ever needed for real, and
> gets pasted directly into the on-call runbook. If detecting the problem, diagnosing it, rerunning
> the fix, and a safety buffer add up to more time than your promised recovery window allows, the
> pipeline is in the wrong priority tier.

---

## Idea 6: Not Every Pipeline Deserves the Same Level of Panic

Treating all 200 pipelines as equally critical is exactly how an on-call team burns out. The fix:
sort pipelines into tiers based on how bad it is if they're late, and give each tier a
correspondingly different response.

A workable three-tier split:

| Tier | How bad is "late"? | How many pipelines (example) | Response |
|---|---|---|---|
| **Highest priority** | Directly affects revenue within an hour | A small handful | Wakes someone up immediately, mandatory rerun runbook |
| **High priority** | Affects the business within about 4 hours | A larger group | Pages during business hours, email overnight |
| **Lower priority** | Fine to be wrong for up to a day | The majority | A chat notification, handled next business day |

**The real "time budget" for recovering from a failure adds up like this:**
```
time budget = time to detect + time to diagnose + time to rerun + safety buffer
```
For a 4-hour-tolerance pipeline, that might break down as roughly 30 minutes to detect + 30
minutes to diagnose + 60 minutes to rerun + 2 hours of buffer — which adds up to the full 4 hours.
Every one of those pieces is a named, budgeted number — not a hope.

---

## A Real Interview, Walked Through Simply

This is the classic orchestration prompt: a specific number of pipelines, a specific reliability
promise, a specific "how bad can it get" limit. Watch the candidate sort pipelines by how critical
they are, do the recovery-time math out loud, and reason through what breaks first at scale.

**Interviewer:** Design the orchestration for a 200-pipeline platform with a 99.9% reliability
promise and a 4-hour maximum "how bad can it get" limit.

**Candidate:** Three questions first. What does 99.9% mean across 200 pipelines — if each one is
independently 99.9% reliable, the platform as a whole is meaningfully less reliable than that.
Does the promise apply per-pipeline, or to the platform overall?

**Interviewer:** Per pipeline, measured daily. Each one has to hit its expected completion window
99.9% of the time.

**Candidate:** Good. Second: how critical are these 200 pipelines, relative to each other? All
equally important, or is there a small set that drives revenue directly and a much larger set
that's more exploratory?

**Interviewer:** Call it 10 revenue-critical, 50 business-critical, 140 purely analytical.

**Candidate:** That split is the first real design decision — different tiers get different
response budgets and different on-call treatment. Third: who owns each pipeline — a central
platform team, or is ownership spread across individual engineers?

**Interviewer:** Spread out. A central platform team owns the underlying scheduling
infrastructure; individual engineers own their own pipelines.

**Candidate:** Right — so the platform team's real job is making it *hard to ship a badly-behaved
pipeline* in the first place, not just running the infrastructure. Let me lay out the tiers.

Highest tier: 10 pipelines, 1-hour limit, pages someone immediately, requires idempotent tasks,
requires a concurrency cap of one, and requires a tested rerun runbook before it's even allowed to
ship. Middle tier: 50 pipelines, 4-hour limit, pages during business hours and emails overnight.
Lowest tier: 140 pipelines, 24-hour limit, just a chat notification.

I'd enforce these tier requirements automatically, at the point someone tries to ship a new
pipeline — a pipeline tagged as highest-tier that doesn't pass an automated idempotency check, or
doesn't have its concurrency capped at one, should simply fail that check and block from shipping.

**Interviewer:** What breaks first at 200 pipelines?

**Candidate:** The central scheduler itself. A single scheduler instance starts showing real
slowdown somewhere around several hundred simultaneously running tasks, and it hurts worst at
burst moments — like midnight UTC, if half the fleet is scheduled to start then. I'd run the
scheduler in a high-availability setup (multiple coordinating instances, only one active at a
time) with a worker pool that scales automatically based on how much work is queued up.

Second: the polling problem from Idea 4 — if 100 pipelines are all checking on an upstream
dependency every minute, that's a lot of unnecessary load on the scheduler. I'd make sure
everything uses the "release the worker slot between checks" mode, or migrate to the newer
notify-instead-of-poll approach where possible.

Third: tier inheritance across dependencies. If a business-critical pipeline depends on a purely
analytical one, it inherits that analytical pipeline's looser guarantees whether it wants to or
not — a downstream pipeline promising a 4-hour window is meaningless if something it depends on is
allowed to be a full day stale. I'd add an automated check that blocks a pipeline from claiming a
tighter guarantee than the loosest guarantee among everything it depends on.

**Interviewer:** What's the plan if the scheduler itself goes down?

**Candidate:** The high-availability setup handles most failure modes — if all instances go down,
runs simply pause; anything already running finishes; nothing new gets queued. No data corruption,
just stalled work.

*(pauses)*

Let me push on that a bit, though — "no corruption, just stalled work" is only true if the
catch-up *after* recovery is controlled. If the scheduler's been down for six hours and catch-up
kicks in with the default, overly permissive concurrency cap, we're right back in the war-story
failure mode from earlier — many overlapping runs racing through the backlog, competing for the
same output. So: high-availability scheduler, plus a concurrency cap of one on anything that
writes to a shared data slice, plus explicitly *not* auto-replaying every missed schedule blindly.
Drop any one of those three and a scheduler outage turns into a real data incident.

**Interviewer:** Cost?

**Candidate:** Mostly modest — a small handful of scheduler instances for high availability, an
autoscaling worker pool, and a metadata database. Roughly a few thousand dollars a month for the
orchestration layer itself. The real cost is the actual pipeline execution time in the compute
layer underneath, which this estimate doesn't include — the orchestrator itself is the cheapest
part of the whole stack.

---

## Common Mistakes People Make

1. **Treating the dependency diagram as the whole design.** It's actually the least interesting
   part. Concurrency limits, retry policy, and idempotency are where the real design work is.
2. **Leaving the "how many copies can run at once" setting at its default** for any pipeline that
   writes to a shared data slice. This is the classic real-world incident from Idea 3.
3. **Using a "wait and keep checking" sensor without releasing the worker slot in between
   checks.** Works fine with a handful of pipelines, falls over at scale.
4. **Turning on retries for a task that isn't idempotent yet.** Data corrupts silently on retry.
   Idempotency has to come first.
5. **Applying one single reliability promise across every pipeline.** Pretends every pipeline is
   equally critical, and is a direct path to on-call burnout. Tiered promises with different
   response budgets are the fix.

---

## The Big Ideas, One Line Each

1. **A task has to survive being run twice.** That's what makes retries, backfills, and crash
   recovery all safe to do.
2. **Retries should be expected, not treated as emergencies** — but only once the underlying task
   is idempotent.
3. **Cap how many copies of the same pipeline can run at once**, especially for anything writing to
   shared data. This one setting is behind most real orchestration incidents.
4. **Waiting on something upstream needs a design that doesn't quietly choke your whole system**
   at scale.
5. **Not every pipeline deserves the same level of urgency.** Tier them, and budget the recovery
   time for each tier explicitly.

---

## Cheat Sheet

**The one-sentence version**
Orchestration is a contract about failure behavior, not just a schedule. Scheduling is the easy
half.

**Four operational building blocks**
- **Idempotency** — replace-don't-append, insert-or-update with dedup, or atomic swap-into-place
- **Retries** — a few attempts, waiting longer each time, only after idempotency is in place
- **Concurrency limits** — cap same-pipeline runs to 1 for anything writing to shared data
- **Sensors** — release the worker slot between checks at scale; prefer "notify me" over "let me
  keep checking"

**Recovery time budget**
```
time budget = time to detect + time to diagnose + time to rerun + safety buffer
```

**Backfill options, fastest to slowest**
1. Rerun just the broken piece (needs idempotency)
2. Full rebuild from scratch (slow, simple, the fallback)
3. Manual fix (emergency only, loses your audit trail)

**Reliability tiers**
- **Highest** — ~1 hour tolerance, pages immediately, runbook mandatory
- **High** — ~4 hour tolerance, pages during hours, email overnight
- **Lower** — ~24 hour tolerance, chat notification only

**Three lines worth memorizing**
- "Orchestration is a contract, not scheduling."
- "Idempotency plus bounded concurrency. One without the other doesn't save you."
- "The rerun command lives in the runbook before the pipeline ships."

---

## Further Reading

- **Apache Airflow Documentation: Concepts.** airflow.apache.org. The canonical reference for
  sensors, resource pools, SLAs, and retry policies.
- **Data Pipelines Pocket Reference.** James Densmore. O'Reilly, 2021. A concise book on pipeline
  operational discipline, with concrete patterns for retries, idempotency, and observability.
- **Enterprise Integration Patterns.** Gregor Hohpe and Bobby Woolf. Addison-Wesley, 2003. The
  source for the "write-then-publish safely" and "pass a reference, not a large payload" patterns
  used across service boundaries — predates modern orchestrators but is still the clearest
  taxonomy of the patterns they keep rediscovering.

---

## A Couple of Extra Ideas (From the Older 2025 Edition)

- **"Fan-out, fan-in" coordination:** a common shape where one raw dataset branches into many
  downstream transformations (fan-out), which later need to be collected back together before
  moving on (fan-in). The tricky part isn't drawing this shape — it's that a fan-in step waiting
  on many upstream pieces means the *slowest* one controls your overall latency, and one badly
  formatted upstream file can block everything downstream of it. Breaking a large fan-in into
  layers, or checking that upstream data is genuinely complete before joining it, helps here.
- **Event-driven vs. schedule-driven orchestration:** a schedule ("run every day at midnight") is
  simple and predictable but can introduce unnecessary delay and wasted compute waiting for a
  fixed time. Event-driven triggering (start as soon as a file lands, or a signal arrives) reduces
  latency and cost but adds coordination complexity. Most mature platforms use both — schedules
  for deadline-bound work, events for anything where freshness really matters.
- **Retries can have real business consequences, not just technical ones:** in financial or
  healthcare contexts, blindly retrying a task that has an external side effect (like sending a
  payment instruction) can literally trigger that action twice. Careful retry policy sometimes
  means marking a step as "incomplete, needs manual review" rather than automatically retrying it.
