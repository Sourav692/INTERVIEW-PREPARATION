# Distributed Task Scheduler — Explained Simply

## The Problem

Millions of tasks a day, each with a time it should run. Spread them across a fleet of machines. When a machine dies mid-task, notice and run it somewhere else. Never lose a task.

## An Analogy First: The Library and the Due-Back Slip

Picture a library where books are jobs to be done.

**The naive version:** one librarian both decides which books are due and reads them. A 600-page book blocks every other due date behind it.

**The split version:** the librarian only *checks out* books. Readers do the reading.

Now the interesting part. When you borrow a book, you don't get it forever — you get it **until Tuesday**. If Tuesday passes and you haven't renewed, the library assumes something happened to you and puts the book back on the shelf for someone else.

Nobody has to phone in and report that they got hit by a bus. **Not renewing is the report.**

That's a **lease**, and it's the whole trick. A crashed machine can't tell you it crashed — but it also can't renew.

## The Split That Makes Everything Else Possible

| | **Scheduler (the brain)** | **Workers (the brawn)** |
|---|---|---|
| Job | decide *what* runs now | actually run it |
| Work per item | bounded, milliseconds | arbitrary — could be 3 hours |
| How many | 3 | ~60, and growing |
| Failure impact | another scheduler claims instead | the lease expires, someone re-runs it |

A cron daemon does both, which is why one slow job delays everything behind it. Separating them means the scheduler's loop stays fast no matter what the tasks do.

## The Query That Is the Design

Everything hinges on one SQL statement:

```sql
UPDATE tasks
SET status = 'running',
    lease_expires_at = now() + interval '30 seconds',
    attempt_count = attempt_count + 1
WHERE task_id IN (
    SELECT task_id FROM tasks
    WHERE next_run_at <= now()
      AND status IN ('pending', 'failed')
      AND (lease_expires_at IS NULL OR lease_expires_at < now())
    ORDER BY next_run_at
    LIMIT 100
    FOR UPDATE SKIP LOCKED
)
RETURNING *;
```

Four clauses, four separate jobs:

| Clause | What breaks without it |
|---|---|
| `FOR UPDATE SKIP LOCKED` | schedulers queue behind each other; only one makes progress |
| `lease_expires_at < now()` | a crashed worker's task stays `running` forever |
| `RETURNING *` | you need a second read, and a crash between them loses the claim |
| the partial index | full table scan, every 100 ms, forever |

### `SKIP LOCKED` in one sentence

Ordinary `SELECT ... FOR UPDATE` makes the second scheduler **wait** for the first. `SKIP LOCKED` tells it: *anything already locked, pretend it isn't there* — so it skips past and grabs the next 100 rows instead.

Three schedulers, 250 due tasks, no coordination protocol at all:

```
scheduler-0  claimed 100
scheduler-1  claimed 100
scheduler-2  claimed  50
             ─────────
             250, zero duplicates
```

**The database's row locks *are* the distributed lock.** This is why there's no ZooKeeper, no leader election, no consensus. Consensus protocols exist to decide *who may act*; here the database decides that per-row, for free. Adding a leader would be strictly worse — a leader is a bottleneck, where `SKIP LOCKED` is a parallelism *enabler*.

## The Bug: A Recovery Path That Never Runs

Read those two predicates together:

```sql
AND status IN ('pending', 'failed')
AND (lease_expires_at IS NULL OR lease_expires_at < now())
```

The `UPDATE` sets `status = 'running'`. So a task whose worker died is in `running`. And `running` isn't in `('pending','failed')`.

**The row is thrown out before the lease check is ever reached.** The expiry clause is dead code.

The notebook asserts exactly this. Same task, same instant, lease long expired:

```
As printed:  NOT re-claimed. Task stranded forever.
Corrected:   re-claimed, attempt=2.
```

The fix admits expired-but-running rows:

```sql
AND (
      status IN ('pending', 'failed')
   OR (status = 'running' AND lease_expires_at < now())
)
```

What makes this worth studying isn't the SQL. It's that the *design* was correct — leases, renewal, expiry, all right — and the query silently didn't use it. **A mechanism that looks correct and never executes is the bug that survives review.** Trace one concrete failure through the actual predicate, not through your mental model of it.

## The Second Bug: Counting the Wrong Thing

`attempt_count` goes up on **claim**. That's what stops a task retrying forever — but it means a task that is claimed and never executed still burns a retry.

The scheduler commits the claim, then crashes before publishing to the queue. Lease expires, task is re-claimed, `attempt_count` is now 2 — for a task that has never run.

Three such crashes, `max_retries = 3`:

```
Naive (claims count):      GAVE UP (never ran!)             executions=0
Fixed (executions count):  SUCCEEDED                        executions=1
Real failures still stop:  GAVE UP (after real failures)    executions=3
```

The third line matters as much as the second: the fix must not disable retries for tasks that genuinely fail. Tie the retry budget to **executions actually started**, and count claims separately for observability.

## Step-by-Step: A Task Whose Worker Loses Power

A task due at 09:00. Lease TTL 30 seconds, renewed every 10.

---

**09:00:00 — The scheduler claims it.** `status=running`, `lease_expires=09:00:30`, `attempt=1`. Committed.

---

**09:00:00 — Published to the queue.** The scheduler's job is done; it moves on.

---

**09:00:01 — A worker picks it up** and starts a five-minute job.

---

**09:00:10 — Renew.** `lease_expires=09:00:40`.
**09:00:20 — Renew.** `lease_expires=09:00:50`.

---

**09:00:25 — The machine loses power.** No error, no message, no shutdown hook. Nothing.

---

**09:00:50 — The lease expires.** Nobody renewed it.

---

**09:00:51 — The scheduler's claim query sees it and re-claims.** `attempt=2`, a different worker starts over.

The dead worker never reported anything. **It didn't have to.** That inversion — silence as the signal — is the single most transferable idea here.

## The Guarantee, Stated Honestly

> **At-least-once.** A task will never be lost. It may run twice.

Duplicates happen in one specific, unavoidable window: the worker finishes the real work, and its lease expires *before* it writes the result. Someone else picks it up and does it again.

You cannot close that window. The work and the acknowledgement are two separate operations, and any crash between them looks identical to a crash before them.

So the contract is:

> **The system guarantees delivery. The task owner guarantees idempotency.**

Saying that out loud *is* the answer. Candidates who promise exactly-once are describing something that doesn't exist.

## Where the Bottleneck Actually Is

The arithmetic, from "5 million tasks/day":

```
5,000,000 / 86,400  =  58 tasks/sec average
           × 10     = 580 tasks/sec at peak

Scheduler capacity:  100 per batch × 10 batches/sec × 3 nodes = 3,000/sec
                     → 5x headroom over peak

Worker capacity:     1 worker × (1000ms / 100ms) = 10 tasks/sec
                     → 580 / 10 = 58 workers needed
```

> **The database has 5× headroom. The workers don't.**

Everyone worries about the database. It isn't the constraint. And because workers hold no state, the scaling story is "add more workers", and it's **linear** — which was a stated requirement, now demonstrated rather than asserted.

## Why the Partial Index Is Load-Bearing

```
Rows in the table after a year:      1,820,000,000
Rows the claim query actually needs:         34,720
Ratio:                                     52,560 : 1
```

A full index would carry 1.8 billion entries to find 35,000 relevant ones. The partial index — `WHERE status IN ('pending','failed')` — contains only claimable rows, so it stays tiny no matter how much history accumulates.

This reframes archiving. It isn't cost control; **it's what keeps the claim query fast.** Storage is only 3.7 GB/day, which is nothing. The reason to delete old rows is the index.

## Time Zones: The Part Everyone Hand-Waves

Store the interval and add it each run, and you break on the two days a year that don't have 24 hours.

Store the **cron expression** and the **IANA zone name**, and recompute from scratch after each run.

**The classic bug is storing an offset.** `UTC-5` is correct for exactly half the year:

```
Noon in New York, January:  UTC-05:00  (EST)
Noon in New York, July:     UTC-04:00  (EDT)
```

Store `-5` and every summer task runs an hour late. Store `America/New_York` and the library works it out.

Two days a year force a policy decision — make it explicitly rather than discovering it in production:

| Event | A daily 02:30 task | Policy |
|---|---|---|
| **Spring forward** — 02:00 jumps to 03:00 | 02:30 doesn't exist | run at 03:00, **or** skip |
| **Fall back** — 01:00–02:00 happens twice | 01:30 exists twice | run **once**, on the first |

The notebook demonstrates the fall-back case: the same wall-clock time, one hour apart in UTC. Dedupe on the computed UTC instant, or the task fires twice.

## Where This Design Gets Hard: The 3-Hour Task

A worker is 2 hours into a 3-hour job and gets network-partitioned. It can't renew. The lease expires, the task is reassigned — and now **it's running twice, concurrently**, with both workers believing they hold it.

This is the genuinely nasty case. Mitigations, weakest to strongest:

1. **Longer leases for long tasks.** Narrows the window. Doesn't close it. Also slows down real crash detection.
2. **Re-verify ownership before writing.** `UPDATE ... WHERE lease_owner = :me` — the partitioned worker's write is rejected when it comes back. Good, but the *side effects* already happened.
3. **Make the task idempotent.** The only actual fix.

This is a **fencing token** problem, and it's the same one behind distributed locks generally: a lock you can lose without noticing isn't a lock.

## Common Mistakes

- **Reaching for ZooKeeper.** The claim is already atomic. A leader adds a bottleneck where the database gave you parallelism.
- **Plain `FOR UPDATE` without `SKIP LOCKED`.** Correct, but serialised — the schedulers queue behind each other and you've built a single-threaded system with extra machines.
- **Claiming and reading in two statements.** A crash between them loses a claim you already made. `RETURNING *` exists for this.
- **Promising exactly-once.** It's at-least-once; say so and put idempotency on the task owner.
- **Forgetting the lease renewal loop.** Without heartbeats, every task longer than the TTL gets re-run while it's still running.
- **Storing a UTC offset instead of a zone name.** Right half the year.
- **No partial index.** Works at 100 TPS, dies at 10,000 as history accumulates.
- **Never archiving.** The index grows forever even though the number of claimable rows doesn't.
- **Strict priority ordering.** Low-priority tasks starve under sustained high-priority load. Weighted consumption (7:2:1) bounds it.

## The Takeaway

> A crashed process can't report its own death — but it also can't renew a lease. **Expiry is the detection mechanism.**

Three ideas carry the design: **split deciding from doing** (so slow work can't block scheduling), **let the database be the distributed lock** (`SKIP LOCKED` gives N schedulers disjoint work with no protocol), and **at-least-once is what's on offer** (delivery is the system's job, idempotency is the task's).

And the transferable habit is the one that found both bugs: **trace a single concrete failure through the actual code**, not through your description of it. The lease design was right, and the query it was implemented in never reached it.
