# Chapter 5: Data Value Design Patterns — Interview Cram Sheet

> Quick-recall version. 9 patterns, 2-3 lines each. Full detail lives in the long-form doc.

---

## One-Page Recall Table

| # | Pattern | One-line problem | One-line fix |
|---|---|---|---|
| 1 | Static Joiner | Enrich with an at-rest reference dataset | Key JOIN, optionally SCD type 2/4 |
| 2 | Dynamic Joiner | Enrich a stream with another moving stream | Watermarked buffers + GC watermark |
| 3 | Wrapper | Keep raw + computed values, both visible | Envelope struct around raw data |
| 4 | Metadata Decorator | Attach technical context, hidden from users | Native metadata layer (headers/tags) |
| 5 | Distributed Aggregator | Aggregate data not colocated by key | Shuffle: group + reduce (MapReduce) |
| 6 | Local Aggregator | Aggregate without paying for a shuffle | Rely on static producer-side partitioning |
| 7 | Incremental Sessionizer | Sessions span multiple batch partitions | Input + completed + pending session storage |
| 8 | Stateful Sessionizer | Need near-real-time sessions | State store, event-time expiration |
| 9 | Bin Pack Orderer | Order guarantee under partial commits | Sort → single-key bins → sequential emit |
| — | FIFO Orderer | Simple strict-order, low-volume delivery | One record in, ack, then next |

---

## 1. Static Joiner

**Problem:** Need to enrich a raw dataset with reference data (e.g. `users`) that lives at rest.
**Solution:** Key-based `JOIN`; use **SCD type 2/4** if the reference data changes over time and idempotent backfills matter.
**Gotcha:** Late data desyncs the two datasets; idempotent replays need SCD, not just a plain join.

> 📌 **Note:** Static Joiner works even when the *main* dataset is streaming — only the enrichment side needs to be at-rest.

> ✅ **Say this out loud:** "I use Static Joiner when the enrichment side is at-rest — if I also need idempotent backfills, I back it with SCD type 2 so a replay always sees the same historical state."

> 🎯 **FAANG pointer:** Expect a follow-up — "what if the reference dataset also starts streaming?" That's your bridge straight into Dynamic Joiner.

> 🧱 **Databricks angle:** Delta Lake table joins support SCD type 2 natively via `MERGE INTO` with `start_date`/`end_date` columns — a very common Databricks reference-table pattern.

---

## 2. Dynamic Joiner

**Problem:** Both sides of the join are streams (e.g. CDC-fed reference data) with different latencies — plain joins return mostly empty matches.
**Solution:** Time-bounded buffers on both sides + a **GC watermark** that expires stale buffered keys.
**Gotcha:** Space-vs-exactness trade-off — bigger buffer = more matches but more hardware; late data past the watermark is silently dropped.

> 📌 **Note:** The GC watermark is the same watermark concept from the Late Data Detector (Chapter 3) — reused here to bound buffer size, not just to flag lateness.

> ✅ **Say this out loud:** "Dynamic Joiner's watermark size is a direct dial between join completeness and hardware cost — I tune it to the observed latency skew between the two streams, not a fixed default."

> 🎯 **FAANG pointer:** They'll probe whether you know Dynamic Joiner ≠ 100% join coverage — always mention the watermark trade-off unprompted.

> 🧱 **Databricks angle:** Spark Structured Streaming's `withWatermark()` + stream-stream join with a time-range condition is exactly this pattern, natively supported on Databricks.

---

## 3. Wrapper

**Problem:** Multiple providers send visits with different schemas; need computed fields separated from raw ones, but both visible.
**Solution:** Wrap the record in an envelope — `{raw: {...}, computed: {...}}` — 4 layout variants (flat-raw/nested-computed, flat-computed/nested-raw, fully flat, two tables).
**Gotcha:** Domain split — one entity's fields live in two places, complicating retrieval; payload size grows since computed values are part of the record.

> 📌 **Note:** Even in a plain table, the "envelope" is just a row — no need to break columnar format to simulate nesting.

> ✅ **Say this out loud:** "Wrapper keeps raw and computed values visible and queryable — I treat the wrapped shape as a Silver-layer concern, not what I expose to end users, to avoid confusing them with the domain split."

> 🎯 **FAANG pointer:** Common trap question — "why not just add computed columns directly?" Answer: schema clarity and debuggability, at the cost of size and domain split.

> 🧱 **Databricks angle:** `withColumn(F.struct(...))` in PySpark on Databricks implements this directly; Delta Lake's schema evolution handles the nested-struct schema changes over time.

---

## 4. Metadata Decorator

**Problem:** Need to attach technical context (job version, batch ID) to records — but it must stay invisible to business users.
**Solution:** Use the storage layer's **native metadata** (Kafka headers, object-store tags) or a hidden column/table behind a view/permissions.
**Gotcha:** Fully dependent on storage support — **Amazon Kinesis has no headers at all**; scope must stay metadata-only, never business data.

> 📌 **Note:** This differs from Wrapper only in *semantics* — metadata is never meant for business users, while Wrapper explicitly decorates business attributes too.

> ✅ **Say this out loud:** "Metadata Decorator vs. Wrapper is a visibility decision, not a technical one — same structural idea, but metadata never leaks to the business-facing schema."

> 🎯 **FAANG pointer:** Know the Kinesis gotcha cold — it's a specific, quotable fact interviewers like to check ("does Kinesis support headers?" → no).

> 🧱 **Databricks angle:** Kafka source/sink on Databricks fully supports `includeHeaders` for native metadata; for Delta tables, a hidden metadata column + a view excluding it is the standard workaround.

---

## 5. Distributed Aggregator

**Problem:** Aggregate records that aren't guaranteed to be colocated by key across nodes/stores.
**Solution:** Classic MapReduce — group, **shuffle** (network exchange), then reduce. Partial pre-aggregation before the shuffle shrinks what's exchanged.
**Gotcha:** Shuffle network cost; **data skew** on hot keys; reclaiming compute capacity after the reduce phase completes.

> 📌 **Note:** Salting (add a random suffix to the key, aggregate twice) is the standard skew fix — first pass on `key+salt`, second pass re-aggregates on `key`.

> ✅ **Say this out loud:** "When I see data skew in a distributed aggregation, my first lever is salting the grouping key and re-aggregating in two passes — trades extra shuffle for avoiding one overloaded reducer."

> 🎯 **FAANG pointer:** Be ready to explain *why* a shuffle happens (data for a key must be physically colocated to reduce) — this is a classic distributed-systems fundamentals question.

> 🧱 **Databricks angle:** Adaptive Query Execution (AQE) on Databricks Runtime handles skew mitigation automatically in many cases — mention it, but also know manual salting as the fallback.

---

## 6. Local Aggregator

**Problem:** Same aggregation need as above, but the shuffle itself is the thing you want to eliminate.
**Solution:** Only works if the **producer guarantees** a key always lands in the same partition — then aggregate locally with `mapPartitions`/`foreachPartition`, no network exchange.
**Gotcha:** Frozen/costly to rescale (breaks if partitioning ever changes); requires **one shared grouping key** across all consumers of that partitioned data.

> 📌 **Note:** Kafka Streams' `groupByKey()` recognizes pre-partitioned data natively; Spark has no explicit hint but matches bucketed datasets with the same key + bucket count.

> ✅ **Say this out loud:** "Local Aggregator only pays off when the producer guarantees stable partitioning by the grouping key — the moment two consumers need different keys, or partition count changes, you're back to paying for a shuffle."

> 🎯 **FAANG pointer:** This is the "avoid a shuffle" answer they're fishing for in performance-tuning questions — pair it with the constraint (static partitioning) or it sounds like a free lunch.

> 🧱 **Databricks angle:** Bucketing (`bucketBy`) on Delta/managed tables is the closest Databricks-native mechanism to guarantee colocation and avoid shuffle on repeated joins/aggregations.

---

## 7. Incremental Sessionizer

**Problem:** Visit events are hourly-partitioned; a session (up to 2hrs inactivity) can span up to 3 partitions — reprocessing many partitions per user is painful.
**Solution:** Three storage spaces — **input**, **completed sessions**, **pending sessions** — combined each run; sessions carry Init → Accumulation → Finalization states.
**Gotcha:** Sessions are **forward dependent** (09:00 affects 10:00 affects 11:00) — backfilling one partition means backfilling all subsequent ones; batch-bound freshness.

> 📌 **Note:** Emitting partial (not-yet-finalized) sessions early improves freshness but risks consumers treating an interim state as final — always flag with `is_completed: false`.

> ✅ **Say this out loud:** "Incremental Sessionizer's real cost isn't the sessionization logic — it's that sessions are forward dependent, so a late-arriving event forces a cascading backfill of every downstream partition."

> 🎯 **FAANG pointer:** They'll test whether you understand forward-dependency cost — don't just describe the happy path, volunteer the backfill-cascade gotcha.

> 🧱 **Databricks angle:** Delta Lake's `MERGE INTO` for the pending-sessions table + Delta table version history for idempotent reprocessing is a natural fit; Databricks Workflows/Jobs can orchestrate the multi-partition combine step.

---

## 8. Stateful Sessionizer

**Problem:** Stakeholders want near-real-time sessions — impossible with hourly batch partitions.
**Solution:** **State store** (in-memory, checkpointed) with either session windows (fixed gap duration) or arbitrary stateful processing (dynamic gap logic).
**Gotcha:** **At-least-once** processing from irregular checkpointing; **state rebalancing** makes scaling costlier than stateless jobs; event-time vs. processing-time expiration choice matters.

> 📌 **Note:** Always expire on **event time**, not processing time — processing-time expiration ties correctness to wall-clock latency and can expire sessions early after a retry delay.

> ✅ **Say this out loud:** "I picked event-time expiration over processing-time for the session state — processing time ties correctness to wall-clock latency, and any retry-induced delay would expire sessions prematurely."

> 🎯 **FAANG pointer:** Classic stateful-streaming question — "what happens to state on a restart?" Answer: resumes from last checkpoint → at-least-once, so avoid non-idempotent session-key logic.

> 🧱 **Databricks angle:** `applyInPandasWithState` / `mapGroupsWithState` on Spark Structured Streaming (Databricks) is the direct implementation; state is checkpointed to DBFS/cloud storage via `checkpointLocation`.

---

## 9. Bin Pack Orderer

**Problem:** Destination has **partial commit semantics** (Kinesis, DynamoDB batch writes) — bulk writes can succeed for only some records, breaking order.
**Solution:** Sort by key + event_time → pack into bins with **one key per bin** → emit bins sequentially (next bin waits for current one).
**Gotcha:** Order guaranteed only **within one execution** — a full pipeline retry can still replay already-emitted bins out of order; bin-packing logic is genuinely more complex than a plain sort.

> 📌 **Note:** In-flight (concurrent, unacknowledged) requests boost throughput but can break ordering if an earlier request fails while a later one succeeds — the same trade-off shows up in FIFO Orderer's idempotent-producer setting.

> ✅ **Say this out loud:** "Bin Pack Orderer gets me ordering under partial-commit semantics by making each bulk request single-key — but ordering is only guaranteed within one execution, not across pipeline-level retries."

> 🎯 **FAANG pointer:** Know the "partial commit" definition cold — three possible outcomes (full success / partial success / full failure), and *why* partial success is the dangerous one for ordering.

> 🧱 **Databricks angle:** Not a typical Databricks-native concern — this pattern targets downstream stores like Kinesis/DynamoDB, not Delta Lake writes (which are already atomic/transactional). **Not sure** Databricks offers a dedicated bin-packing primitive; you'd implement this in application code (PySpark `foreachPartition`) same as the book's example.

---

## Bonus: FIFO Orderer

**Problem:** Low-volume, latency-sensitive delivery where strict arrival order matters more than throughput.
**Solution:** Single-record delivery with ack-before-next, or bounded-concurrency bulk (Kafka idempotent producer, up to 5 in-flight).
**Gotcha:** Per-record I/O overhead and latency; **FIFO ≠ exactly-once** — a failed ack after a successful send can cause silent redelivery.

> ✅ **Say this out loud:** "FIFO Orderer gives me delivery order, not delivery guarantees — for exactly-once I still layer one of the idempotency patterns from Chapter 4 on top."

> 🧱 **Databricks angle:** Kafka's `enable.idempotence=True` producer setting is directly usable from Databricks streaming jobs writing to Kafka; no Databricks-specific enhancement beyond that.

---

## Before You Close the Laptop Tonight

Every enrichment/aggregation/ordering pattern here trades **completeness or throughput** for a
constraint — static data, stable partitioning, bounded buffers, single-key bins. If you can say
out loud *what each pattern gives up* — not just what it does — you're ready.

The two threads that tie the whole chapter together:
- **Enrichment & Sessionization** both fight the same enemy: **late data** — Static/Dynamic Joiner
  and Incremental/Stateful Sessionizer all have a late-data gotcha for a reason.
- **Ordering & Aggregation** both fight the same enemy: **network exchange** — Bin Pack/FIFO
  Orderer pay for individual acks the same way Distributed Aggregator pays for a shuffle.
