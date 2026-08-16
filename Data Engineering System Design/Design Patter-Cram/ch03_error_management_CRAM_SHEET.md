# Chapter 3: Error Management — Interview Cram Sheet

> Quick-recall version. 7 patterns, 2-3 lines each. Full detail lives in the long-form doc.

---

## 1. Dead-Letter

**Problem:** Bad/unparseable records crash the whole pipeline instead of just failing on that one record.
**Solution:** Wrap risky logic in try-catch (or if-else for error-safe functions), route bad records to a separate dead-letter store + metadata, keep the main pipeline running.
**Gotcha:** Replaying dead-lettered records later can force a **snowball backfill** on downstream consumers; also **hides real failures** unless you alert on volume.

> 📌 **Note:** Transient errors self-heal (retry); nontransient errors (poison pills) need Dead-Letter.

> ✅ **Say this in interview:** "Dead-Letter trades pipeline uptime for hidden-error risk — I always pair it with volume-based alerting so a spike still pages someone."

> 🎯 **FAANG pointer:** Interviewers love asking "what if dead-letter records need reprocessing?" — answer: optional replay pipeline, but flag the snowball backfill risk to consumers first.

**Databricks:** Delta Lake supports this cleanly — write valid rows and invalid rows to two different Delta tables (as shown in the book's `CONCAT`/`is_valid` flag example). No dedicated "dead-letter" product feature; it's just a write pattern on Delta.

---

## 2. Windowed Deduplicator

**Problem:** At-least-once delivery + producer retries = duplicate records reaching your table.
**Solution:** Batch → `DISTINCT` or `ROW_NUMBER()` window over the whole dataset. Streaming → dedup key stored in a **state store** for a time-bound window.
**Gotcha:** Short window = may miss dupes but cheap; long window = catches more but costs more state. Dedup ≠ exactly-once **delivery** (retries can still write twice).

> 📌 **Note:** 3 state store types — Local (fast, no fault tolerance), Local+fault-tolerant (balanced), Remote (safe, slower).

> ✅ **Say this in interview:** "Deduplication solves exactly-once *processing*, not exactly-once *delivery* — for the latter I'd add an idempotency pattern from Chapter 4."

> 🎯 **FAANG pointer:** Classic follow-up — "how do you dedup an unbounded stream?" Answer: you can't fully; you bound it with a time window and accept the trade-off.

**Databricks:** Spark's native `dropDuplicates()` works as-is on Databricks (batch and Structured Streaming with `withWatermark`). Delta Lake also supports `MERGE INTO` for idempotent upserts as an alternative dedup strategy.

---

## 3. Late Data Detector

**Problem:** Users go offline, buffer events locally, then flush late — pipeline needs to know a record is "late" vs "on time."
**Solution:** Track event time per partition using **MAX** (never MIN — avoids getting stuck). `watermark = MAX(event time) − allowed lateness`. Records before the watermark = late.
**Gotcha:** MIN per-partition → stuck-in-the-past risk. MAX across skewed sources → can wrongly drop a genuinely slow-but-valid source's data.

> 📌 **Note:** Event time (when it happened) ≠ processing time (when you saw it). Processing time is never late.

> ✅ **Say this in interview:** "I always use MAX for per-partition watermarking to guarantee monotonic progress — MIN risks the pipeline getting permanently stuck waiting on one slow partition."

> 🎯 **FAANG pointer:** Whiteboard-friendly question — draw the watermark formula and walk through one "on time" and one "late" example. They're testing if you understand *why* MAX, not just the formula.

**Databricks:** Structured Streaming's `.withWatermark("event_time", "1 hour")` is native and works the same on Databricks. Capturing the dropped late records into a separate sink, though, is **not exposed out of the box** in Spark Structured Streaming (Flink is better at this) — not sure Databricks has closed that gap either.

---

## 4. Static Late Data Integrator

**Problem:** Late data has a known fixed delay (e.g., "up to 15 days late") but you don't want to run 15 separate backfill jobs.
**Solution:** Every daily run automatically **replays a fixed N-day lookback window** as part of the same pipeline.
**Gotcha:** Wastes resources when no late data exists; naive replay of multiple days **overlaps** — you only need to rerun the *latest* execution to cover the whole range.

> 📌 **Note:** Switching to processing-time partitions "solves" this too easily — it just hides the event-time problem instead of fixing it.

> ✅ **Say this in interview:** "Static Integrator is simple but wasteful — it always pays the backfill cost even when there's nothing to backfill."

> 🎯 **FAANG pointer:** They may probe "why not just rerun the whole pipeline for the last 15 days daily?" — answer: overlapping runs reprocess the same data redundantly; only rerun the latest execution.

**Databricks:** Airflow's Dynamic Task Mapping (`expand()`) is the book's example — this is orchestration-layer, so it works the same whether Databricks Jobs, Airflow, or another scheduler triggers the notebook/job. Not a Databricks-specific feature.

---

## 5. Dynamic Late Data Integrator

**Problem:** Static's fixed window isn't enough — business now wants *all* late data included, even beyond 15 days.
**Solution:** Maintain a **state table** (partition, last_processed_time, last_update_time). Query for partitions where `last_update_time > last_processed_time` and backfill only those.
**Gotcha:** Concurrent runs can double-trigger backfills unless you add an `Is processed` flag; very late data in **stateful** pipelines can still force a long re-execution chain.

> 📌 **Note:** If you can isolate exactly which entities changed, overwrite just those instead of full partitions — more efficient, more complex.

> ✅ **Say this in interview:** "Dynamic Integrator only backfills what actually changed, but that state table adds real scheduling complexity and a concurrency hazard I have to explicitly lock against."

> 🎯 **FAANG pointer:** Great "trade-off" question to bring up unprompted — Static (simple, wasteful) vs Dynamic (efficient, complex) is a textbook system-design trade-off answer.

**Databricks:** This maps naturally to **Delta Lake table history/versions** — the book's own example uses Delta table version numbers instead of timestamps for tracking `lastProcessedVersion` per partition (via `DESCRIBE HISTORY`-style version tracking). This is a genuine Databricks/Delta strength.

---

## 6. Filter Interceptor

**Problem:** Filtered-out data volume unexpectedly jumped (e.g., 15% → 90%) after a code change, but the query plan collapses multiple filter conditions into one — you can't tell which condition is the culprit.
**Solution:** Wrap **each filter condition with its own counter** (accumulator in code, or a CASE-based column in SQL) so you can see per-condition drop counts.
**Gotcha:** Small runtime overhead; much harder to implement cleanly in SQL than in a programmatic API; streaming version may force you into stateful processing.

> 📌 **Note:** "Stay pragmatic" — use SQL or the programmatic API, whichever the job actually calls for.

> ✅ **Say this in interview:** "When filter selectivity suddenly spikes, the query plan won't tell you which rule is responsible if the optimizer merged them — Filter Interceptor isolates that with per-condition counters."

> 🎯 **FAANG pointer:** Good pattern to mention when asked "how do you debug a silent data quality regression?" — it's a diagnostic pattern, not a prevention one.

**Databricks:** Spark accumulators work the same on Databricks — no special product feature here. You could also just check `df.filter(cond).count()` per condition manually for ad hoc debugging, though that re-scans the data each time.

---

## 7. Checkpointer

**Problem:** A long-running streaming job (e.g., counting visits in 10-min windows) would have to reprocess everything from scratch after a crash.
**Solution:** Persist **offset position + computed state** to durable storage on a regular cadence — either framework-managed (Spark/Flink) or manually (custom Kafka consumer commits).
**Gotcha:** More frequent checkpoints = slower job, less reprocessing on failure. Less frequent = faster job, more reprocessing. Also — it only gives an **"exactly-once feeling,"** not real exactly-once delivery.

> 📌 **Note — 3 delivery modes:** Exactly once (needs Ch.4 idempotency) · At-least-once (checkpoint after write → duplicates possible) · At-most-once (checkpoint before write → data loss possible).

> ✅ **Say this in interview:** "Checkpointing alone gives an exactly-once *feeling* — a task can fail mid-write after processing but before committing the checkpoint, causing a retry to reprocess. Real exactly-once needs an idempotency pattern on top."

> 🎯 **FAANG pointer:** This is the #1 "gotcha" question interviewers ask to test if you actually understand delivery semantics vs. just knowing the checkpoint config flag.

**Databricks:** Fully native — `checkpointLocation` option in Structured Streaming is a first-class, heavily-used Databricks feature (stored in DBFS/cloud object storage). This is one of the strongest, most battle-tested Databricks capabilities in this whole chapter.

---

## One-Page Recall Table

| # | Pattern | One-Line Problem | One-Line Fix | #1 Gotcha |
|---|---|---|---|---|
| 1 | Dead-Letter | Bad records crash the job | Catch + reroute to dead-letter store | Snowball backfill on replay |
| 2 | Windowed Deduplicator | Retries cause duplicates | Dedup within dataset/time window | Not real exactly-once delivery |
| 3 | Late Data Detector | Can't tell late vs on-time | MAX-based watermark per partition | MAX can drop skewed slow sources |
| 4 | Static Late Data Integrator | Fixed-window late data ignored | Always replay fixed lookback window | Wastes resources, snowball backfill |
| 5 | Dynamic Late Data Integrator | Late data beyond any fixed window | State table tracks real late arrivals | Concurrency hazard w/o locking |
| 6 | Filter Interceptor | Don't know which filter dropped data | Per-condition counters | Hard in SQL, small overhead |
| 7 | Checkpointer | Crash = reprocess from scratch | Persist offset + state periodically | Only "feels" exactly-once |

---

## The One Thread Tying This Chapter Together

Every pattern here **reduces** risk — none of them **eliminates** it. The chapter's own closing line: error management gives you the *feeling* of exactly-once delivery, but real exactly-once needs **Chapter 4's idempotency patterns** on top. If an interviewer asks "is your pipeline exactly-once now?" — the correct answer after describing any of these 7 patterns is **"not fully — I'd still need idempotent writes."**
