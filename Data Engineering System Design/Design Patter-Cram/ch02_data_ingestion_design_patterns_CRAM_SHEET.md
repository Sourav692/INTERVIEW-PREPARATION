# Chapter 2 — Data Ingestion Design Patterns (Cram Sheet)

> **The connecting thread** — Ingestion is where you stop controlling the data. Every pattern here
> exists because a producer you don't own — a legacy DB, a third-party API, an irregular
> event stream — hands you data on its own terms, and you have to adapt without breaking
> downstream consumers. The chapter moves from *how much* to load (Full → Incremental → CDC), to
> *how* to copy it safely (Replication), to the operational plumbing that makes ingestion
> trustworthy: knowing when data is ready, keeping storage from clogging with small files, and
> reacting to data that shows up on no fixed schedule at all.

## One-Page Recall Table

| # | Pattern | Problem | Fix | #1 Gotcha |
|---|---|---|---|---|
| 1 | **Full Loader** | No delta signal to detect changed rows | Reload the whole dataset each run (EL/ETL) | Data consistency during overwrite (partial reads, lost rollback) |
| 2 | **Incremental Loader** | Growing dataset, only need what's new since last run | Delta column or time-partition based read | Hard deletes invisible; backfill can silently become a full load |
| 3 | **Change Data Capture** | Need sub-minute latency + hard-delete capture | Stream changes off the DB commit log | High setup complexity; output is data-in-motion, not data-at-rest |
| 4 | **Passthrough Replicator** | Non-idempotent source needs identical copies across environments | EL job or infra replication policy, zero transformation | Unusable the moment the dataset contains PII |
| 5 | **Transformation Replicator** | Same as above, but source has PII/PHI/IP | EL job + mapping/SQL layer that strips or alters sensitive fields | Schema-based transforms can silently corrupt data |
| 6 | **Compactor** | Small files slow batch jobs to a crawl | Merge small files into bigger ones (`OPTIMIZE`, rewrite action) | Needs its own cleanup (`VACUUM`) or old files linger |
| 7 | **Readiness Marker** | Consumers read incomplete datasets | Flag file or partition convention signaling "done" | Convention is unenforced; late data breaks it |
| 8 | **External Trigger** | Data arrives unpredictably; polling wastes resources | Push-based event subscription triggers ingestion | Missing execution context or dropped events with no dead-letter path |

---

## 1. Full Loader

**Problem:** A device reference dataset has no last-updated column, so you can't detect which rows changed since the last run.

**Solution:** Reload the entire dataset every run via a two-step extract-and-load (EL) job, or ETL if source/destination are heterogeneous.

**Gotcha:** A naive drop-and-insert overwrite can expose consumers to partial data mid-run and destroys rollback capability unless you use a view-swap abstraction or a time-travel format.

> **📌 Note:** EL jobs are also called "passthrough jobs" — data just passes through, unmodified.

> **✅ Say this in interview:** "We chose Full Loader because the provider gives us no delta signal — but we protect consumers from partial reads with a view-swap so ingestion never half-exposes the dataset."

> **🎯 FAANG pointer:** Expect a follow-up on "what happens to readers while you're overwriting?" — the correct shape of answer is transactions or a single exposition abstraction (view/table-swap), not "just overwrite it."

**Databricks:** Delta Lake's built-in time travel (table version history) gives you the rollback safety net this pattern needs without hand-building a view-swap mechanism yourself.

---

## 2. Incremental Loader

**Problem:** Legacy visit events land in a transactional DB; ingestion should only pull rows added since the last execution as volume keeps growing.

**Solution:** Use a delta column (e.g., `ingestion_time`) to filter new rows, or target a whole new time-partition each run.

**Gotcha:** Hard deletes are invisible to a delta-column read (the row just vanishes), and backfilling without a bounded window turns the job into a full load.

> **📌 Note:** Partition-based implementations don't need to remember state — the partition to process is implicit from the execution time.

> **✅ Say this in interview:** "We bound the ingestion window explicitly during backfills — `delta_column BETWEEN ingestion_time AND ingestion_time + INTERVAL '1 HOUR'` — so a replay never silently becomes a full load."

> **🎯 FAANG pointer:** They'll probe on deletes — know that soft deletes (`UPDATE` marking removed) or insert-only/append-only tables are the two standard answers, since physical deletes leave no delta-column trace.

**Databricks:** Delta Lake's `MERGE INTO` combined with a `insertion_time`-filtered source query is the standard incremental-upsert pattern shown in the book's Dataset Materializer example — same idea applied to ingestion.

---

## 3. Change Data Capture (CDC)

**Problem:** Incremental Loader is too slow — you need every database change captured within 30 seconds and published to a streaming topic.

**Solution:** Stream changes directly off the database's append-only commit log (e.g., via Debezium + Kafka Connect, or Delta Lake's native change data feed).

**Gotcha:** CDC output is data-in-motion, not data-at-rest — a `JOIN` against two CDC streams returning nothing might just mean the data hasn't arrived yet, not that there's no match.

> **📌 Note:** CDC captures every operation type, including hard deletes — producers no longer need to implement soft deletes for you.

> **✅ Say this in interview:** "CDC gets us the low latency and native delete support Incremental Loader can't, but it costs more in setup complexity — it usually needs operations-team involvement to enable the commit log."

> **🎯 FAANG pointer:** A classic trap question is "why not just poll more often?" — the answer is that polling still has query/scheduling overhead that can't reliably hit sub-minute latency; CDC reads the commit log directly instead.

**Databricks:** Delta Lake's Change Data Feed (`TBLPROPERTIES (delta.enableChangeDataFeed = true)`, `readChangeFeed` option) is a confirmed, much lighter-weight CDC path than standing up Debezium against a source database.

---

## 4. Passthrough Replicator

**Problem:** A non-idempotent third-party API feeds a reference dataset; dev/staging need the *exact same* data as production, not a re-run of the load.

**Solution:** A simple EL job (or infra-level replication policy) that copies data as-is, with zero transformation.

**Gotcha:** The moment the dataset contains PII, this pattern is off the table entirely — you must switch to Transformation Replicator.

> **📌 Note:** Prefer push (source pushes to targets) over pull, to avoid destabilizing the production environment.

> **✅ Say this in interview:** "Passthrough Replicator only works because there's nothing sensitive to strip — the instant PII enters the picture, this pattern is disqualified by design, not by policy."

> **🎯 FAANG pointer:** They may ask "why not just re-run the ingestion pipeline in staging?" — the answer is non-idempotency: a non-idempotent source (like a third-party API) can return different data on each call, so replaying the *pipeline* doesn't reproduce the *dataset*.

**Databricks:** No dedicated product feature here beyond standard cloud-storage replication (e.g., S3 replication via Terraform) or a plain Spark EL job — it's an infra/job-design pattern, not a Databricks-specific capability.

---

## 5. Transformation Replicator

**Problem:** You need to replicate production data into staging for realistic testing, but the dataset contains PII that can't leave production.

**Solution:** Same EL shape as Passthrough Replicator, plus a transformation layer (mapping function or SQL `SELECT`) that removes or replaces sensitive fields.

**Gotcha:** Schema-based transformations can silently corrupt data — e.g., a datetime format mismatch can drop timestamp columns and break the staging job.

> **📌 Note:** PII definitions drift over time — new attributes get reclassified as sensitive — so tie the transformation to a governed data catalog/contract, not a hardcoded column list.

> **✅ Say this in interview:** "We route PII removal through governance-tagged fields rather than a hardcoded column list, so a newly-classified PII attribute doesn't silently leak into staging."

> **🎯 FAANG pointer:** Expect "how do you know your anonymization stays correct as the schema evolves?" — the strong answer references a data catalog/contract driving the transformation, not a manually maintained list.

**Databricks:** Unity Catalog's column-level tagging and access controls are the natural governed-field-list mechanism this pattern implies, though the book's own examples (`SELECT * EXCEPT`, `.drop()`) are framework-level, not Unity-Catalog-specific.

---

## 6. Compactor

**Problem:** A passthrough streaming-to-object-store job accumulates so many small files that batch jobs spend 70% of runtime just listing files.

**Solution:** Merge many small files into fewer large ones — `OPTIMIZE` (Delta Lake), rewrite data file action (Iceberg), row/columnar merge (Hudi), or key-based log compaction (Kafka).

**Gotcha:** Compaction alone can leave the original small files in place — you need a separate cleanup job (`VACUUM`) or the small-files problem persists.

> **📌 Note:** There's no universally correct compaction frequency — it's a deliberate cost-vs-performance trade-off, not a solved problem.

> **✅ Say this in interview:** "We treat compaction and cleanup as two separate jobs — compaction alone doesn't remove the pre-compaction files, so we always pair `OPTIMIZE` with a scheduled `VACUUM`."

> **🎯 FAANG pointer:** They'll likely ask "how often do you compact?" — the strong answer names the trade-off explicitly (rare compaction saves compute but denies uncompacted jobs the benefit) rather than giving a single "correct" cadence.

**Databricks:** `OPTIMIZE` and `VACUUM` on Delta tables are directly confirmed by the book as the compaction and cleanup mechanism — this is one of the most concretely Databricks-native patterns in the chapter.

---

## 7. Readiness Marker

**Problem:** An hourly Silver-layer job feeds other teams' ML models and dashboards, who keep complaining about consuming incomplete datasets.

**Solution:** Signal completeness with a flag file (e.g., Spark's `_SUCCESS`) created as the last pipeline step, or rely on a time-partition convention (partition N+1 appearing implies N is done).

**Gotcha:** Neither implementation is enforced — a consumer can start reading mid-write regardless of convention, and late data breaks the "next partition means previous is closed" assumption.

> **📌 Note:** The readiness marker must always be generated as the *last* step in a pipeline, after the final transformation — not before.

> **✅ Say this in interview:** "Readiness Marker is pull-based and convention-only — it doesn't enforce anything, so we either treat partitions as immutable once closed or explicitly share and communicate the mutability rules with consumers."

> **🎯 FAANG pointer:** A natural follow-up is "what if late data lands in an already-closed partition?" — the correct answer distinguishes immutable-partition design from explicit mutability contracts with consumers, not silently overwriting a "closed" partition.

**Databricks:** Delta Lake's own commit log effectively acts as a built-in readiness signal — a reader querying a Delta table only ever sees committed, complete writes, which is a stronger guarantee than a bare `_SUCCESS` file convention on raw formats.

---

## 8. External Trigger

**Problem:** Feature releases happen irregularly (at most weekly); a daily refresh job wastes compute reloading data that hasn't changed.

**Solution:** Subscribe to a notification channel, react to events, and push-trigger the ingestion pipeline only when something actually changed.

**Gotcha:** A trigger that's just a bare "ping" with no execution context (trigger version, event time, processing time) becomes very hard to debug when something fails.

> **📌 Note:** Push-based triggers (source notifies you) beat pull-based polling (you continuously check) — polling wastes resources finding nothing new most of the time.

> **✅ Say this in interview:** "We always enrich the trigger payload with metadata — trigger version, notification envelope, processing and event time — because a bare ping-to-orchestrator becomes undebuggable the first time it misfires."

> **🎯 FAANG pointer:** They may ask "what happens if the trigger event itself gets lost?" — the strong answer routes back to Dead-Letter handling (Chapter 3), since the pipeline's only entry point is the event stream.

**Databricks:** No dedicated Databricks trigger primitive is confirmed in the book's own examples (it uses AWS Lambda + Airflow's REST API) — Databricks Workflows' file-arrival/table triggers are a plausible real-world fit, but that's outside what this chapter's source material confirms, so treat it as `[verify against source page]` rather than asserted fact.

---

## One-Page Recall Table (repeated)

| # | Pattern | Problem | Fix | #1 Gotcha |
|---|---|---|---|---|
| 1 | **Full Loader** | No delta signal to detect changed rows | Reload the whole dataset each run (EL/ETL) | Data consistency during overwrite (partial reads, lost rollback) |
| 2 | **Incremental Loader** | Growing dataset, only need what's new since last run | Delta column or time-partition based read | Hard deletes invisible; backfill can silently become a full load |
| 3 | **Change Data Capture** | Need sub-minute latency + hard-delete capture | Stream changes off the DB commit log | High setup complexity; output is data-in-motion, not data-at-rest |
| 4 | **Passthrough Replicator** | Non-idempotent source needs identical copies across environments | EL job or infra replication policy, zero transformation | Unusable the moment the dataset contains PII |
| 5 | **Transformation Replicator** | Same as above, but source has PII/PHI/IP | EL job + mapping/SQL layer that strips or alters sensitive fields | Schema-based transforms can silently corrupt data |
| 6 | **Compactor** | Small files slow batch jobs to a crawl | Merge small files into bigger ones (`OPTIMIZE`, rewrite action) | Needs its own cleanup (`VACUUM`) or old files linger |
| 7 | **Readiness Marker** | Consumers read incomplete datasets | Flag file or partition convention signaling "done" | Convention is unenforced; late data breaks it |
| 8 | **External Trigger** | Data arrives unpredictably; polling wastes resources | Push-based event subscription triggers ingestion | Missing execution context or dropped events with no dead-letter path |

## Before You Close the Laptop

Every pattern in this chapter is really answering one of two questions: **"how much data do I
pull?"** (Full → Incremental → CDC, in order of decreasing latency and increasing setup cost) and
**"how do I know it's safe to act?"** (Readiness Marker for scheduled data, External Trigger for
unscheduled data). If you get stuck on a follow-up question, ground your answer in *who controls
the timing* — the consumer (pull/Readiness Marker) or the producer (push/External Trigger/CDC) —
that's the axis the book keeps coming back to.
