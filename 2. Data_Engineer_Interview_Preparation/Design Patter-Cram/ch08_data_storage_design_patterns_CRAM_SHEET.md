# Chapter 8: Data Storage — Interview Cram Sheet

> Quick-recall version. 9 patterns, 2–3 lines each. Full detail lives in the long-form doc.

---

## 1. Horizontal Partitioner

**Problem:** Filtering a growing dataset (e.g., "last 4 days") gets slower and slower as more data lands.
**Solution:** Physically isolate rows by a low-cardinality distribution key (usually event time, hour/day granularity).

> **📌 Note:** Sharding is a physical/hardware-layer special case of horizontal partitioning — not the same thing.

> **✅ Say this out loud:** "I partition by a low-cardinality, frequently-filtered attribute — usually event time rounded to the hour or day — so the engine can skip irrelevant partitions without exploding the metadata layer."

> 🎯 **FAANG pointer:** Classic follow-up — "what if you partitioned by user_id instead?" Tests whether you know the small-files/metadata-overload failure mode.

**Databricks:** Fully native — `PARTITIONED BY` at table creation, or `.partitionBy()` in Spark writes. Also exposed via `DESCRIBE TABLE EXTENDED` for partition metadata.

---

## 2. Vertical Partitioner

**Problem:** Mutable and immutable attributes are stored together, duplicating the immutable ones on every row.
**Solution:** Split the row into groups by mutability/access needs, joined back by a shared key (e.g., `visit_id`).

> **📌 Note:** This is the storage-focused version — Chapter 7 covers the same idea applied to security.

> **✅ Say this out loud:** "Vertical Partitioner trades read simplicity for storage savings and per-group policy flexibility — I reach for it when attribute groups have genuinely different retention or access needs."

> 🎯 **FAANG pointer:** Expect "how do you reconstruct the full row?" — answer is Dataset Materializer or a view, not a schema redesign.

**Databricks:** No dedicated feature — implemented manually via separate table writes (`.select()`/`.drop()` + `.persist()` to avoid double reads).

---

## 3. Bucket

**Problem:** A high-cardinality column (e.g., user_id) drives most query predicates but is too high-cardinality to partition on.
**Solution:** Hash-based colocation — `hash(key) % N buckets` — enables bucket pruning and shuffle-free joins.

> **📌 Note:** Popularized by Apache Hive; now in Spark and AWS Athena (Athena is logical-only — never writes data).

> **✅ Say this out loud:** "Bucketing is my answer when a high-cardinality column is central to filters and joins and partitioning would blow up the metadata layer — the cost is that the bucket count is essentially a one-way door."

> 🎯 **FAANG pointer:** They'll probe whether you know bucket count is near-immutable — resizing means a full backfill.

**Databricks:** `bucketBy()` is a Spark API and works on Databricks, but **not recommended with Delta Lake** — Delta's own file-skipping/Z-order generally supersedes it. Flag this trade-off if asked.

---

## 4. Sorter

**Problem:** Data is already organized (e.g., weekly tables) but queries still scan whole blocks.
**Solution:** Declare sort column(s) at table creation; use Z-order for multi-column "curved sort" skipping.

> **📌 Note:** Z-order gets called "clustering" but it's mechanically still a disk sort — the book classifies it under Sorter, not as its own pattern.

> **✅ Say this out loud:** "Lexicographical sort only helps if my query filters match the declared key order — if I need to skip blocks on any of several columns interchangeably, Z-order is the right call."

> 🎯 **FAANG pointer:** Book's own number to cite: lexicographical order read 9 data blocks vs. Z-order's 7 blocks on the same two-column predicate — concrete proof multi-dimensional skipping beats naive sort.

**Databricks:** Fully native — `OPTIMIZE ... ZORDER BY (...)` on Delta tables. One of the strongest, most commonly used Databricks-specific capabilities in this chapter.

---

## 5. Metadata Enhancer

**Problem:** Consumers load the full dataset before filtering, driving up latency and cloud cost.
**Solution:** Persist per-file/per-column statistics (Parquet footers, commit-log min/max/null counts) so the engine can skip files without opening them.

> **📌 Note:** Table formats (Delta, Iceberg, Hudi) layer extra commit-log stats on top of Parquet's own footer stats.

> **✅ Say this out loud:** "Predicate pushdown via file-level stats is close to free at read time — the real cost is keeping those stats fresh, which is a write-time and maintenance concern, not a query-time one."

> 🎯 **FAANG pointer:** Watch for "what if stats are stale?" — answer: threshold-based auto-refresh can lag; `ANALYZE TABLE` fixes it but adds temporary read overhead.

**Databricks:** Fully native and automatic — Delta Lake collects column stats (min/max/null count) in the transaction log on every write; no configuration needed for the default 32 columns.

---

## 6. Dataset Materializer

**Problem:** A view simplifying a costly multi-table query still feels slow — it re-runs the query on every access.
**Solution:** Precompute into a materialized view (some auto-refresh) or a table (manual refresh, but gains partitioning/bucketing/sorting).

> **📌 Note:** Incremental refresh (only new rows) is the standard mitigation for insert-only workloads — full refresh is the expensive default.

> **✅ Say this out loud:** "The materialized-view-vs-table choice comes down to who owns the refresh — automatic but less predictable, or manual but fully composable with other storage optimizations."

> 🎯 **FAANG pointer:** They may ask you to sketch the incremental-refresh SQL — it's just a `MERGE` filtered by `insertion_time > last_run`, combining Incremental Loader + Merger from earlier chapters.

**Databricks:** Native materialized views exist (Unity Catalog, DLT/Lakeflow pipelines) with automatic incremental refresh where possible — one of the chapter's strongest confirmed Databricks capabilities.

---

## 7. Manifest

**Problem:** Object-store file listing is the dominant latency cost once a Parquet dataset is exposed through a warehouse layer.
**Solution:** Record the file list once — either automatically (table format commit logs) or as an explicit manifest file — so readers skip the listing call entirely.

> **📌 Note:** Manifests also help writing — Redshift's `COPY ... MANIFEST` ties a load to a fixed file list, making replays idempotent.

> **✅ Say this out loud:** "A manifest turns an O(n) listing call into an O(1) metadata read — the only real cost is that the manifest itself can grow large with many small files or a continuous streaming writer."

> 🎯 **FAANG pointer:** Good war story to have ready: early Spark Structured Streaming manifests grew unbounded and could block job restarts (SPARK-27188) — shows you know a real historical failure mode, not just the theory.

**Databricks:** Fully native and automatic — Delta Lake's transaction log **is** the manifest; readers never list files directly. `generate('symlink_format_manifest')` exists for interop with non-Delta readers (e.g., Presto/Athena/BigQuery external tables).

---

## 8. Normalizer

**Problem:** Immutable reference attributes (device, OS) are duplicated on every event row, bloating storage and slowing updates.
**Solution:** Split into Normal Forms (1NF/2NF/3NF) or a snowflake schema (fact table + dimensions describing dimensions) — one fact represented once.

> **📌 Note:** The overarching goal is consistency over performance — an update lands once and is visible everywhere immediately.

> **✅ Say this out loud:** "I reach for Normalizer when reference data changes often and consistency matters more than read latency — the tax is paid in JOINs, which I can partially offset with colocation or broadcast joins."

> 🎯 **FAANG pointer:** They'll test if you know the archival angle — time-sensitive dimensions (e.g., changing prices) need SCD Type 2/4, not just a plain Normalizer.

**Databricks:** No single dedicated "Normalizer" feature — it's a modeling choice implemented with standard Delta tables + `MERGE`. Broadcast joins are tunable via `spark.sql.autoBroadcastJoinThreshold`.

---

## 9. Denormalizer

**Problem:** A fully relational model needs 8-table joins for 80% of queries — read latency collapses as volume grows.
**Solution:** Flatten into One Big Table (regular columns) or nested `STRUCT`s, or a star schema (fact + flat dimensions, no nested dimensions).

> **📌 Note:** Normalizer and Denormalizer aren't exclusive — build normalized for consistency, then a denormalized copy on top for reads, kept in sync via a Chapter 6 sequence pattern.

> **✅ Say this out loud:** "I'd reach for One Big Table or a star schema when read latency dominates and the source is close to append-only — the update cost is the real bill you're paying for that speed."

> 🎯 **FAANG pointer:** Classic trap question — "does denormalizing always help?" Answer: only if you can treat the table as an immutable snapshot; otherwise costly multi-row updates eat the gains.

**Databricks:** No dedicated feature — implemented as regular Delta table writes with `JOIN` + `write.mode('overwrite')`. `STRUCT`/nested columns are natively supported by Delta's Parquet-based storage.

---

## One-Page Recall Table

| # | Pattern | One-Line Problem | One-Line Fix | #1 Gotcha |
|---|---|---|---|---|
| 1 | Horizontal Partitioner | Growing dataset, slow filters | Physically isolate rows by low-cardinality key | High cardinality → metadata/small-files overload |
| 2 | Vertical Partitioner | Immutable attrs duplicated per row | Split row into groups by mutability | Full-row reconstruction needs a join/view |
| 3 | Bucket | High-cardinality key, can't partition | Hash % N colocation | Bucket count is a near one-way door |
| 4 | Sorter | Organized but still full-block scans | Declare sort cols; Z-order for multi-dim | Composite key order must match filter order |
| 5 | Metadata Enhancer | Full-dataset load before filtering | Persist file/column stats for pushdown | Stats go stale between refreshes |
| 6 | Dataset Materializer | View re-runs costly query every time | Precompute into view/table | Refresh cost + cross-table access policy |
| 7 | Manifest | Slow, repeated object-store listing | Record file list once (commit log/manifest) | Manifest can balloon with many small files |
| 8 | Normalizer | Duplicated reference data, update anomalies | Normal forms or snowflake schema | Distributed joins costly; needs SCD for archival |
| 9 | Denormalizer | Too many joins tank query time | One Big Table or star schema | Updates get expensive as duplication grows |

---

## The One Thread Tying This Chapter Together

Every pattern here trades **one resource for another** — never eliminates the cost, just moves it. Partitioning and bucketing trade write-time organization for read-time speed. Metadata Enhancer and Manifest trade a small write-time bookkeeping step for skipping expensive read-time work. Materializer trades storage for compute. Normalizer trades query simplicity for consistency; Denormalizer trades it right back. If an interviewer asks "does pattern X just make things faster for free?" — the correct answer is **"no — it's always faster reads paid for with slower writes, more storage, or harder updates; the skill is picking which side of that trade your workload can afford."**
