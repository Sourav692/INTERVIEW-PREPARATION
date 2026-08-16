# Chapter 6 Cram Sheet — Data Flow Design Patterns

> **The connecting thread:** This chapter is about pipeline *topology*, not pipeline
> *logic*. Sequence patterns decide whether steps live in one job or many. Fan-in patterns
> decide how branches merge back together (all-or-nothing vs. partial). Fan-out patterns
> decide how one task spawns others (all branches vs. one branch). Orchestration patterns
> decide how many whole-pipeline *instances* can run at once. Get the topology right and
> readability, backfill cost, and correctness all fall out of it.

## One-Page Recall Table

| # | Pattern | Problem | Fix | #1 Gotcha |
|---|---|---|---|---|
| 1 | Local Sequencer | One bloated job, hard to debug/maintain | Ordered, dependency-driven steps (orchestration or processing layer) | No universal split boundary — judge per pipeline |
| 2 | Isolated Sequencer | Two teams/pipelines must hand off data without merging ownership | Connect physically separate pipelines via data- or trigger-based dependency | Scheduling & communication overhead across the boundary |
| 3 | Aligned Fan-In | Need one daily result from 24 hourly partitions | Branch per hour, merge via UNION/JOIN once ALL succeed | Slowest parent gates everything (scheduling skew) |
| 4 | Unaligned Fan-In | Aligned Fan-In blocks entirely on one failed hour | `trigger_rule=ALL_DONE`; publish partial + completeness % | Must actively signal incompleteness or consumers assume 100% |
| 5 | Parallel Split | Need to write the same data to two destinations (e.g. migration) | Materialize input once (`.persist()`), fan out to independent writers | Slowest branch blocks all subsequent time-dependent runs |
| 6 | Exclusive Choice | Only one of several job variants should run per condition | Router/branch task before splitting; one path executes | Over-branching → unreadable "complexity factory" |
| 7 | Single Runner | Incremental logic breaks if two instances run at once | Cap concurrency at 1 (`max_active_runs=1`) | Backfilling is slow — it's a correctness rule, not a preference |
| 8 | Concurrent Runner | Independent datasets needlessly serialized, adding latency | Raise concurrency above 1 | Resource starvation / shared-state bugs without workload management |

---

## 1. Local Sequencer

**Problem:** A monolithic job (hundreds of lines, tripled transformation count) fails often and every retry restarts from scratch.

**Solution:** Decompose into smaller steps run in strict data-dependency order — either as separate orchestration tasks or as one processing-layer unit, chosen by naming clarity, backfill cost, and whether it forfeits built-in orchestrator abstractions.

**Gotcha:** No fixed rule for where the split boundary goes — over-splitting hurts readability just as under-splitting hurts maintainability.

> **📌 Note:** CRON is still a valid choice for a genuinely isolated task with zero dependencies — the Local Sequencer only earns its keep once real ordering exists.

> **✅ Say this in interview:** "I split this at the orchestration layer instead of using one processing job because backfilling a paid-API readiness check inside a monolith would re-trigger billed calls on every retry."

> **🎯 FAANG pointer:** Expect "how would you decide whether to split this into two tasks or keep it as one job?" — the correct answer names the three book criteria (separation of concerns / maintainability / implementation effort), not just "it depends."

> **Databricks:** No dedicated feature — this is an orchestration-layer choice (Databricks Workflows task dependencies, or chaining `dbutils.notebook.run` / multi-task jobs) rather than a Delta Lake capability.

---

## 2. Isolated Sequencer

**Problem:** Your team's cleansed dataset feeds a separate team's dashboard pipeline; the two pipelines must stay owned and run independently.

**Solution:** Connect two physically separate pipelines via either implicit data-dependency sensors or explicit trigger-based dependency (`ExternalTaskMarker` upstream + `ExternalTaskSensor` downstream, which also auto-propagates backfills).

**Gotcha:** Scheduling and communication overhead — cross-boundary coordination replaces the implicit signals you'd get inside a single DAG. `[verify against source page]`

> **📌 Note:** Draw the boundary either by team/consumer-provider ownership, or — when you're both provider and consumer of your own output — by pipeline complexity.

> **✅ Say this in interview:** "I'd use ExternalTaskMarker/ExternalTaskSensor so a backfill on the upstream DAG automatically propagates downstream, instead of relying on manual coordination between teams."

> **🎯 FAANG pointer:** A common follow-up is "how do you avoid two teams' pipelines drifting out of sync?" — answer with the marker/sensor auto-backfill-propagation mechanism, not just "we'd talk to each other."

> **Databricks:** No dedicated product feature for cross-pipeline triggering — this stays an orchestrator concern (Airflow `ExternalTaskSensor`, or Databricks Workflows job-to-job triggers via the Jobs API).

---

## 3. Aligned Fan-In

**Problem:** Compute one daily aggregate from 24 hourly partitions without reprocessing the whole day at once.

**Solution:** Branch per hour; merge into a common task via `UNION` (vertical, more rows) or `JOIN` (horizontal, more columns) — but only once **all** 24 branches succeed.

**Gotcha:** The merge task is gated by the *slowest* parent — scheduling skew — plus infrastructure spikes from 24 simultaneous jobs and general DAG complexity.

> **📌 Note:** `UNION` in SQL is position-based by default and will silently misalign mismatched column order — Spark's `unionByName()` avoids this.

> **✅ Say this in interview:** "I chose Aligned Fan-In here because a true daily total requires every hour to be present — a partial merge would just be wrong, not just incomplete."

> **🎯 FAANG pointer:** Interviewers often probe "what happens if hour 14 fails?" — correct answer: the whole merge blocks (that's the trade-off vs. Unaligned Fan-In), and recovery only requires replaying the failed hour, not all 24.

> **Databricks:** No dedicated feature; implement via Databricks Workflows task dependencies (all-upstream-success) feeding a downstream `MERGE`/`UNION` notebook task.

---

## 4. Unaligned Fan-In

**Problem:** Aligned Fan-In blocks the whole daily output when just one hour fails; the team wants a partial dataset released instead.

**Solution:** Relax the trigger condition (Airflow's `trigger_rule=ALL_DONE`) so the merge runs even with some parent failures; publish a completeness signal (companion table, metadata tag, or notification) alongside the partial result.

**Gotcha:** Consumers will wrongly assume 100% completeness unless you explicitly publish a completeness metric — this is the single most important detail to get right.

> **📌 Note:** The trigger-rule relaxation is invisible in the DAG graph — it lives only in code, so document it clearly.

> **✅ Say this in interview:** "I'd default to Aligned Fan-In unless a partial-but-timely result genuinely beats a complete-but-delayed one — and if I relax it, I always publish a completeness percentage so consumers never silently assume 100%."

> **🎯 FAANG pointer:** "How do downstream consumers know the data is incomplete?" is the expected follow-up — naming a concrete completeness-tracking mechanism (not just "we'd document it") is what separates a strong answer.

> **Databricks:** No dedicated feature; a completeness flag column or a companion Delta table tracking per-partition status is the practical implementation — not a first-class Delta/Databricks primitive.

---

## 5. Parallel Split

**Problem:** Migrating a legacy framework requires writing the same processed dataset to two destinations simultaneously during the transition.

**Solution:** One parent feeds multiple parallel child tasks; materialize the shared intermediary dataset once (`.persist()` in Spark, or a SQL temp table) so it's not re-read per branch.

**Gotcha:** On time-dependent pipelines, execution blocks on the *slowest* branch — a failure blocks all subsequent runs entirely.

> **📌 Note:** Branches with mismatched hardware needs (CPU-heavy vs. memory-heavy) can't both get ideal resources from one job — split the intermediary-generation step out first if this matters.

> **✅ Say this in interview:** "I read the shared input once with `.persist()` so both branches don't trigger duplicate reads, and I use Delta's `txnVersion`/`txnAppId` to make the writes idempotent on retry."

> **🎯 FAANG pointer:** Expect "how do you avoid processing the same data twice?" — the answer is `.persist()`/temp-table materialization, plus retry-safe writes, not just "run them in parallel."

> **Databricks:** Confirmed capability — Delta Lake's `txnVersion`/`txnAppId` write options give idempotent, retry-safe appends, directly solving this pattern's duplicate-write risk.

---

## 6. Exclusive Choice

**Problem:** A new job version should run only from a cutover date forward; backfills for prior dates must still use the old version, without creating a new pipeline.

**Solution:** Add a router/condition-evaluator task before branching (Airflow `BranchPythonOperator`, ADF if-condition activity) so only one of the declared branches executes.

**Gotcha:** Over-branching becomes a "complexity factory" — the book's own heuristic is rubber-duck debugging: if you can't explain the branching concisely to a new teammate, it's too complex.

> **📌 Note:** Prefer metadata-based routing conditions over data-based ones — evaluating the actual dataset to decide a route adds real runtime cost ("heavy conditions").

> **✅ Say this in interview:** "I evaluate the route using execution-date metadata rather than reading the dataset, so the branching decision itself doesn't add processing time."

> **🎯 FAANG pointer:** A likely trap question is "why not just put an if/else inside the job?" — answer: hidden processing-layer branching is easy to forget over time; surfacing it at the orchestration layer keeps it visible in the DAG.

> **Databricks:** No dedicated feature; implemented via Databricks Workflows conditional task execution (`Run if` dependency conditions) or plain `if`/`else` inside a notebook/job task.

---

## 7. Single Runner

**Problem:** An incremental sessionization pipeline gives wrong results if two instances execute concurrently.

**Solution:** Cap concurrency at exactly 1 (Airflow/ADF `max_active_runs=1` or equivalent); without native support, use a Readiness Marker to wait on the prior run.

**Gotcha:** Backfilling is inherently slow and can't be parallelized — this is a **correctness** constraint, not a tunable performance trade-off.

> **📌 Note:** Straggler runs (a normally-30-min job creeping to 1.5h) compound delay for every downstream consumer even outside of backfill scenarios.

> **✅ Say this in interview:** "Single concurrency here isn't a performance choice — it's a correctness requirement, because the pipeline's incremental logic depends on the prior run's output."

> **🎯 FAANG pointer:** "How would you speed up backfilling under Single Runner?" — the honest answer is you mostly can't relax concurrency; the only lever is checking whether the full pipeline (vs. just part of it) truly needs to re-run.

> **Databricks:** No dedicated feature; enforced via Databricks Workflows job concurrency settings (max concurrent runs = 1) or Airflow's `max_active_runs` when Airflow orchestrates Databricks jobs.

---

## 8. Concurrent Runner

**Problem:** Independent, unrelated dataset ingestions are needlessly serialized under Single Runner, compounding delivery latency.

**Solution:** Raise the concurrency ceiling above 1 so the orchestrator can start the next run without waiting on the current one — balanced against overall infrastructure capacity.

**Gotcha:** In multitenant orchestrators, several high-concurrency pipelines backfilling at once can starve other teams' scheduling capacity.

> **📌 Note:** Shared mutable state under concurrent execution is a distinct risk from resource starvation — e.g. the Dynamic Late Data Integrator (Ch. 4) could double-trigger or skip backfilling under uncontrolled concurrency.

> **✅ Say this in interview:** "I'd only relax to Concurrent Runner once I've confirmed the datasets are truly independent — and I'd pair it with workload management so one team's concurrency setting can't starve another's."

> **🎯 FAANG pointer:** "What could go wrong if you just set concurrency to a high number?" — expect this; the strong answer names both resource starvation *and* shared-state nondeterminism, not just infrastructure cost.

> **Databricks:** No dedicated feature; workload isolation is achieved via Databricks Workflows concurrency limits per job plus cluster policies / pools for compute isolation across concurrent tenants.

---

## Before You Close the Laptop

Sequence → Fan-In → Fan-Out → Orchestration is the chapter's own build order: local ordering, then merging branches, then splitting them, then controlling how many whole pipelines run at once. If you remember only one thing per family: **Aligned/Single Runner favor correctness over speed; Unaligned/Concurrent Runner favor speed but require you to explicitly manage the honesty gap that creates** (completeness metadata, workload isolation). That trade-off — correctness vs. timeliness, and what you owe consumers when you pick timeliness — is the thread an interviewer is really testing.
