# Design a Distributed Task Scheduler

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** System Design · **Tags:** Onsite Loop, Caching, Concurrency, Databases, Distributed Systems · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Design a distributed task scheduler that can execute tasks across a cluster of machines.

**Requirements:**

- Clients can submit tasks that need to be executed at a scheduled time or on a recurring schedule (e.g., cron-like expressions).
- The system should distribute task execution across multiple worker nodes for scalability and fault tolerance.
- If a worker node fails while executing a task, the task should be retried or reassigned to another worker.
- The system should guarantee **at-least-once** execution semantics for tasks.
- The system should be able to handle a high volume of tasks (e.g., millions of tasks per day).

**Functional Requirements:**

- API to create, update, delete, and list tasks.
- Support for one-time and recurring schedules.
- Task execution history and status tracking (e.g., pending, running, succeeded, failed).
- Configurable retry policies (e.g., max retries, backoff).

**Non-Functional Requirements:**

- High availability: the scheduler itself should not be a single point of failure.
- Scalability: adding more workers should linearly increase throughput.
- Low operational overhead: minimal manual intervention for node failures.

**Questions to consider:**

- How would you store tasks and their schedules?
- How would you ensure tasks are not lost if a node crashes?
- How would you avoid duplicate execution if a task is retried?
- How would you handle time zones and daylight saving time for recurring tasks?

---

## Study Tools

### Hint 1

The core challenge is splitting the scheduler's **brain** (deciding what should run when) from the workers' **brawn** (executing the tasks). Think about how a durable log or queue can act as the buffer that survives node crashes.

### Hint 2

For the scheduler itself, you need a reliable way to claim work without two scheduler nodes picking the same task. Consider a transactional `UPDATE ... WHERE claim_deadline < now()` pattern on a strongly consistent store.

### Hint 3

The simplest way to guarantee at-least-once execution is to have workers **heartbeat a lease** while running. If the lease expires, the task's state is reset to pending and its `attempt_count` is incremented, making it visible for reassignment.

---

### Answer

This is a classic distributed coordination problem solved by separating a durable, transactional scheduler from a stateless pool of workers that communicate via a message queue. The scheduler's job is to **atomically claim** tasks whose time has come, while workers execute them and hold **renewable leases** to prove they are still alive.

#### High-Level Architecture

Four main components:

- **API Gateway / Frontend:** Stateless service that validates client requests and writes to the database.
- **Scheduler Nodes:** A small cluster (e.g., 3-5 nodes) that runs a loop to find due tasks and push them to a message queue. They use database transactions to avoid duplicate claims. Leader election is not strictly required if the claim operation is atomic.
- **Message Queue:** A durable, partitioned queue (like Kafka or SQS) that buffers claimed tasks for workers.
- **Worker Pool:** A horizontally scalable set of machines that pull tasks from the queue, execute them, and update the task's status in the database. Workers also run a background thread to renew leases on long-running tasks.

#### Data Model

We use a relational database (e.g., PostgreSQL) for the task metadata because we need **strong consistency** for the claim and lease operations. The queue handles high-throughput delivery, but the DB is the source of truth.

```sql
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    payload JSONB NOT NULL,                -- arbitrary data for the worker
    schedule_type TEXT NOT NULL,           -- 'once' or 'recurring'
    cron_expr TEXT,                        -- for recurring tasks
    timezone TEXT NOT NULL DEFAULT 'UTC',
    next_run_at TIMESTAMPTZ NOT NULL,      -- when the task is due
    status TEXT NOT NULL DEFAULT 'pending',-- 'pending','running','succeeded','failed','paused'
    attempt_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    backoff_seconds INT NOT NULL DEFAULT 60,
    lease_owner UUID,                      -- worker ID that claimed the task
    lease_expires_at TIMESTAMPTZ,          -- when the lease expires
    last_run_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tasks_due ON tasks (next_run_at, status)
    WHERE status IN ('pending', 'failed');

CREATE TABLE task_executions (
    execution_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(task_id),
    worker_id UUID NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,                  -- 'running', 'succeeded', 'failed'
    attempt_number INT NOT NULL,
    error_message TEXT
);
```

The **partial index** `idx_tasks_due` is critical. It allows the scheduler to scan only tasks that are pending or failed and whose `next_run_at` has passed, which is a tiny fraction of the table if you archive old tasks.

#### API Surface

```
POST /v1/tasks
  body: { payload, schedule: { type: "once", run_at: "2024-01-01T00:00:00Z" } }
  or:   { payload, schedule: { type: "recurring", cron: "0 9 * * 1-5", timezone: "America/New_York" } }
  returns: { task_id }

GET /v1/tasks/{task_id}
  returns: { task_id, status, next_run_at, attempt_count, last_run_at, ... }

PUT /v1/tasks/{task_id}
  body: { payload?, schedule?, max_retries?, backoff_seconds? }

DELETE /v1/tasks/{task_id}
  soft-deletes the task (sets status to 'deleted')

GET /v1/tasks?user_id={user_id}&status={status}&limit=50&cursor={cursor}
  returns: { tasks: [...], next_cursor: "..." }

GET /v1/tasks/{task_id}/executions
  returns: { executions: [ { execution_id, status, started_at, completed_at, attempt_number } ] }
```

#### Scheduler Claim Loop

Every scheduler node runs this loop every second (or every 100ms for lower latency):

```sql
-- Claim a batch of due tasks atomically
UPDATE tasks
SET status = 'running',
    lease_owner = :worker_id,
    lease_expires_at = now() + interval '30 seconds',
    attempt_count = attempt_count + 1,
    updated_at = now()
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

The **`FOR UPDATE SKIP LOCKED`** clause is the key. It lets multiple scheduler nodes run this query concurrently without blocking each other. Each row is locked by exactly one transaction, so no task is claimed twice. The `RETURNING *` gives us the claimed tasks to push to the queue.

After the transaction commits, the scheduler publishes each claimed task to the message queue. The queue is partitioned by `task_id` so that retries of the same task go to the same partition, preserving order per task.

#### Worker Execution Flow

1. Worker pulls a message from the queue. The message contains `task_id`, `payload`, and `attempt_number`.
2. Worker executes the task. While executing, a background thread **renews the lease** every 10 seconds:
   ```sql
   UPDATE tasks SET lease_expires_at = now() + interval '30 seconds'
   WHERE task_id = :task_id AND lease_owner = :worker_id AND status = 'running';
   ```
3. On success, the worker marks the task succeeded:
   ```sql
   UPDATE tasks SET status = 'succeeded', last_run_at = now(),
                    lease_owner = NULL, lease_expires_at = NULL
   WHERE task_id = :task_id AND lease_owner = :worker_id;
   ```
4. On failure, the worker checks `attempt_count`:
   - If `attempt_count < max_retries`, set `status = 'failed'` and `next_run_at = now() + backoff_seconds * 2^(attempt_count - 1)`. The scheduler will pick it up again.
   - If `attempt_count >= max_retries`, set `status = 'failed'` permanently (or to a terminal dead state) and record `last_error`.
5. If the worker crashes mid-execution, the lease expires after 30 seconds. The scheduler's claim query sees `lease_expires_at < now()` and reassigns the task to another worker. **This is how we get at-least-once semantics:** the task might run twice, but it will never be lost.

#### Recurring Schedule Computation

When a recurring task succeeds, the worker (or the scheduler, on the next claim) computes the next `next_run_at` from the cron expression and the task's timezone. The cron library must handle DST correctly. The standard approach is to compute the next UTC timestamp after `last_run_at` by evaluating the cron expression in the task's **IANA timezone** (e.g., `America/New_York`). On a DST spring-forward day, a task scheduled for 2:30 AM simply runs at 3:00 AM (or is skipped, depending on the policy you choose — document it). On fall-back, it runs once, not twice.

#### Capacity Numbers

Let's sanity-check the scale. Millions of tasks per day means, say, 5 million tasks per day. That's about **58 tasks per second** on average (5,000,000 / 86,400). Peak might be 10x that, so **~580 TPS**. This is trivial for PostgreSQL with the partial index. The scheduler claim loop with `LIMIT 100` and running every 100ms can claim up to **1,000 tasks per second per scheduler node**. Three scheduler nodes give us 3,000 TPS of claim capacity, which is 5x headroom over peak.

**Workers are the real bottleneck.** If each task takes 100ms of CPU, one worker handles 10 tasks per second. To handle 580 TPS peak, we need about **60 workers**. Adding more workers scales linearly because the queue partitions work and the DB only sees a status update per task completion, not per task execution step.

**Storage:** each task row is maybe 500 bytes. 5 million tasks per day means **2.5 GB per day** if we keep them all. We should archive or delete completed tasks after 30 days to keep the hot table small. The `task_executions` table grows faster — one row per attempt, maybe 200 bytes each. At 5M tasks/day with an average of 1.2 attempts, that's **1.2 GB/day**. Again, archive after 30 days.

**Time:** The scheduler claim is O(batch_size) per transaction, and the worker update is O(1) per task. The claim query uses the partial index, so it touches only due tasks. Overall throughput is bounded by the queue and worker count, not the database.

**Space:** O(n) in the number of active tasks plus the number of execution history rows. With archiving, the active working set stays small.

#### Correctness Argument

The at-least-once guarantee rests on the **lease mechanism**. A task is only marked succeeded when a worker that holds a valid lease confirms it. If a worker dies, its lease expires, and the task becomes visible to the claim query again. The only way a task is lost is if the database itself loses data, which we mitigate with replication and backups. Duplicate execution is possible (a worker finishes just as its lease expires, and another worker picks it up), but that is the accepted trade-off for at-least-once semantics. **If the user needs exactly-once, they must make their task idempotent** — we can't guarantee it in a distributed system with crashes.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest thing that could work: a single machine with a cron daemon and a database. A loop runs every second, queries `SELECT * FROM tasks WHERE next_run_at <= now()`, and executes each task in-process. This handles maybe 10 tasks per second and dies completely if the machine reboots. The bottleneck is that the scheduler and the executor are the same process, so a slow task blocks the scheduler loop.

**First improvement:** split the scheduler from the workers. The scheduler's only job is to find due tasks and put them on a queue. Workers pull from the queue and execute. This lets you scale workers independently. The scheduler is still a single point of failure, but now the queue is durable, so tasks claimed before a crash are not lost — they sit in the queue until a worker picks them up.

**The next problem:** what if the scheduler crashes while claiming tasks? If it reads a task, then crashes before pushing it to the queue, the task is lost. The fix is to make the claim **atomic in the database**. Use `UPDATE ... RETURNING` to atomically mark tasks as running and get their contents in the same transaction. If the scheduler crashes after the commit but before publishing to the queue, the task is stuck in `running` with an expired lease. That's why the claim query includes `lease_expires_at < now()` — it recovers tasks that were claimed but never delivered.

Now think about what happens when a **worker dies mid-execution**. The task is marked `running` in the DB, but nobody is actually working on it. The **lease** solves this. The worker renews its lease every 10 seconds. If the lease expires, the claim query treats the task as available again. The `attempt_count` tracks how many times this has happened, so we can give up after `max_retries`.

For **recurring tasks**, the naive approach is to compute the next run time when the task is created and then just add the interval each time it runs. That breaks on DST boundaries and months with different lengths. The robust approach is to store the cron expression and timezone, and compute the next UTC timestamp from scratch each time using a library that understands IANA timezones. This is a well-solved problem — use a library, don't write your own cron parser.

The last thing to think about is the **claim query's performance**. A naive `SELECT ... WHERE next_run_at <= now() AND status = 'pending'` scans the entire table if you don't have the right index. The partial index on `(next_run_at, status)` where `status IN ('pending', 'failed')` means the query only touches rows that are actually due. Combined with `FOR UPDATE SKIP LOCKED`, multiple scheduler nodes can run the claim concurrently without blocking each other, which gives you high availability for the scheduler itself.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **The `FOR UPDATE SKIP LOCKED` claim pattern** — this is the heart of the design. If you can articulate why it prevents duplicate claims while allowing concurrent schedulers, you've solved the hardest part. Interviewers are listening for this specific mechanism.
- **The lease renewal loop on the worker** — many candidates forget that long-running tasks need heartbeats. Explain that the worker runs a background thread that updates `lease_expires_at` every 10 seconds, and that the claim query treats expired leases as available work.
- **At-least-once vs. exactly-once** — explicitly state that you are designing for at-least-once, and that the only way to get exactly-once is to make the task idempotent. This shows you understand the fundamental trade-off in distributed systems.
- **The partial index on `(next_run_at, status)`** — this is the difference between a design that works at 100 TPS and one that works at 10,000 TPS. Mention that without it, the claim query scans the full table every second.
- **DST handling for recurring tasks** — don't hand-wave this. Say you store the IANA timezone and compute the next UTC timestamp from the cron expression each time. A task at 2:30 AM on a spring-forward day runs at 3:00 AM, and you document that policy.
- **Capacity math done out loud** — 5M tasks/day is ~58 TPS average, ~580 TPS peak. Show that a single PostgreSQL instance with the partial index handles this easily, and that the real scaling lever is the number of workers, which is linear.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you support tasks that depend on other tasks completing first?** — Think about adding a `depends_on` field and a DAG scheduler that only claims tasks whose dependencies are all succeeded.
- **What if a task is scheduled to run exactly once at a time that has already passed when the scheduler picks it up?** — Consider a `missed_run_policy` field: `run_immediately`, `skip`, or `run_once_late`.
- **How would you prevent a single user from flooding the system with millions of tasks?** — Add per-user rate limits at the API gateway and per-user quotas in the database.
- **How would you implement task priorities so that high-priority tasks jump the queue?** — Use multiple queue topics (e.g., high, normal, low) and have the claim query order by priority first, then `next_run_at`.
- **How would you handle a task that takes 3 hours to run, but the lease renewal fails because the worker was network-partitioned?** — The task gets reassigned and runs twice. To mitigate, you can have the worker write a heartbeat to the `task_executions` table and check for a superseded flag before writing the final result.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Two corrections to the answer

Both are verified by runnable assertions in [`2. Distributed_Task_Scheduler.ipynb`](2.%20Distributed_Task_Scheduler.ipynb).

### 1. The claim query's recovery clause can never fire

The claim query filters on two predicates:

```sql
AND status IN ('pending', 'failed')
AND (lease_expires_at IS NULL OR lease_expires_at < now())
```

But the same `UPDATE` sets `status = 'running'`. So when a worker dies holding a lease, its task sits in `running` — and `running` is not in `('pending','failed')`. **The row is filtered out before the lease check is ever evaluated.** The expiry predicate is unreachable, and the crashed task is stranded permanently.

This directly contradicts two claims made elsewhere in the answer:

> *"That's why the claim query includes `lease_expires_at < now()` — it recovers tasks that were claimed but never delivered."* (Walkthrough)
>
> *"If a worker dies, its lease expires, and the task becomes visible to the claim query again."* (Correctness Argument)

Neither happens as the query is written. The status set has to admit expired-but-running rows:

```sql
AND (
      status IN ('pending', 'failed')
   OR (status = 'running' AND lease_expires_at < now())   -- the actual recovery path
)
```

The partial index needs widening to match, or it stops covering the query:

```sql
CREATE INDEX idx_tasks_due ON tasks (next_run_at, status, lease_expires_at)
    WHERE status IN ('pending', 'failed', 'running');
```

The lease *mechanism* in the answer is right. The query silently doesn't use it — which is worth spotting out loud, because "correct design, unreachable code path" is exactly the class of bug that survives review.

### 2. `attempt_count` counts claims, not executions

The claim query increments `attempt_count` **at claim time**, not at execution time. That is deliberate and correct — it is what makes a crashed worker's task eventually give up rather than retry forever — but it has a consequence the answer does not state:

**A task that is claimed and then never executed still burns a retry.** If the scheduler commits the claim and crashes before publishing to the queue, the task waits for its lease to expire, gets re-claimed, and `attempt_count` is now 2 — despite the task having never run once. With `max_retries = 3`, three scheduler crashes exhaust a task that was never attempted.

The fix is to distinguish **claim attempts** from **execution attempts**: keep `attempt_count` for the retry budget but increment it only when a worker actually starts executing (recorded in `task_executions`), and use a separate `claim_count` for observability. The notebook models both and shows the difference.

**See also:** [`18. Retry_Strategy`](../../2.%20Coding_Questions/18.%20Retry_Strategy/README.md) in the coding folder is the single-process version of this problem's backoff logic — the same exponential/jitter reasoning, at a smaller scale.
