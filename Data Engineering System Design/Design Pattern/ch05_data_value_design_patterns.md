# Chapter 5 — Data Value Design Patterns

> **Source:** *Data Engineering Design Patterns* by Bartosz Konieczny (O'Reilly, 2025)
> **Case study:** Blog analytics platform — Bronze/Silver/Gold Medallion architecture

## Chapter Framing

Raw ingested data is not a real asset on its own — most of the time it's poor and full of quality
issues right after ingestion. The book's running example is the visit-events stream: a browser
producer can tell you the browser version, language, or OS of a visitor, but each visit event
lands as a distinct, disconnected item. Correlating "what do visitors using a specific browser
have in common?" is impossible without extra effort.

That's the job of **data value design patterns**: augment a dataset to make it more useful for
end users. The chapter covers four sub-families, each answering a different flavor of "how do I
add value":

- **Data Enrichment** (Static Joiner, Dynamic Joiner) — combine two datasets.
- **Data Decoration** (Wrapper, Metadata Decorator) — compute and attach extra attributes to a
  record without a second dataset.
- **Data Aggregation** (Distributed Aggregator, Local Aggregator) — summarize volume into an
  overview.
- **Sessionization** (Incremental Sessionizer, Stateful Sessionizer) — a special case of
  aggregation that groups events into user sessions.
- **Data Ordering** (Bin Pack Orderer, FIFO Orderer) — guarantee delivery order downstream.

This chapter sits right after Idempotency (Chapter 4) and right before Data Flow (Chapter 6):
once you can safely ingest and retry, you generate business value — then the next chapter covers
how that value flows to the rest of the organization.

---

## Data Enrichment

### Pattern: Static Joiner

#### Problem

A team's datasets are extensively used by business stakeholders. A new project asks for a dataset
that simplifies understanding the dependency between a user's registration date and their
day-to-day activity. The raw activity dataset doesn't include user context — that only lives in a
static user reference dataset. The team needs to bring the reference data to the user's activity
data.

#### Solution

The at-rest character of the joined (reference) dataset is the perfect condition for the **Static
Joiner** pattern — and surprisingly, it also works for streaming pipelines, not just batch.

- Implementation requires a **list of attributes from both datasets** used to combine them (e.g.
  `user_id` shared between `visits` and `users`).
- The combination may also need **time constraints**, especially when the enrichment dataset
  implements a form of **slowly changing dimensions (SCD)**.
- Code implementation is most often a plain SQL `JOIN`, universal across modern processing
  frameworks and classical warehouses.
- Enrichment can also come from a **programmatic API** call instead of a table join. If
  idempotency matters, materialize the API-exposed dataset as a table first and use one of the SCD
  forms — that guarantees replays always see the same enrichment data.

> **📌 Note — Slowly Changing Dimensions (SCD)**
> A time-sensitive enrichment dataset should implement **SCD type 2 or type 4** to track an
> entity's evolution over time.
> - **SCD type 2** manages tracking with validity dates (`start_date` / `end_date`); the current
>   value has an empty/far-future `end_date`.
> - **SCD type 4** relies on two tables — one for the current value per entity, one for full
>   history including the current value.
> The only difference between the two is the technical implementation.

#### Consequences

- **Late data and consistency** — In an ideal world, the `users` reference stream evolves at the
  same pace as `visits` events. In reality, this rarely happens (see Chapter 3 and "Late Data").
  Mitigation: for streaming, use the **Dynamic Joiner** pattern instead; for batch, rely on the
  orchestrator to wait for the enrichment dataset (e.g., via the **Readiness Marker** pattern from
  Chapter 2).
- **Idempotency** — If you backfill a batch pipeline, ask whether the outcome must be idempotent
  for the enrichment side. If the data provider doesn't support time-based queries, you may need
  to bring the enrichment dataset into your own data layer to control time semantics before
  joining. This is trickier for datasets hidden behind an API — SCD is again the recommended fix.

> **🧩 Case Study**
> The `visits` / `users` join is the book's running example throughout this pattern: joining
> streaming visit events with a static (or slowly changing) `users` reference dataset to answer
> "how does registration date relate to daily activity?"

> **✅ Say this out loud**
> "I chose the Static Joiner because the enrichment dataset is at-rest — but since I need
> idempotent backfills, I implemented it as SCD type 2 so replaying a pipeline run always sees the
> same historical state of the reference data."

#### Examples

SCD type 2 tables and join (PostgreSQL-flavored SQL):

```sql
-- Two tables demonstrating SCD type 2
CREATE TABLE dedp.users (
  id TEXT NOT NULL,
  login VARCHAR(45) NOT NULL,
  start_date TIMESTAMP NOT NULL DEFAULT NOW(),
  end_date TIMESTAMP NOT NULL DEFAULT '9999-12-31'::timestamp,
  PRIMARY KEY(id, start_date)
);

CREATE TABLE dedp.visits (
  visit_id CHAR(36) NOT NULL,
  event_time TIMESTAMP NOT NULL,
  PRIMARY KEY(visit_id, event_time)
);
```

```sql
-- Example of SCD type 2 join
SELECT v.visit_id, v.event_time, v.page, u.id, u.login, u.email
FROM dedp.visits v JOIN dedp.users u ON u.id = v.user_id
AND NOW() BETWEEN start_date AND end_date;
```

> SCD type 4 is omitted here since it reuses the same query — the only difference is that type 4
> stores the current value in a separate table, while type 2 keeps current and past rows in the
> same dataset.

Stream-to-batch join in PySpark:

```python
# Stream-to-batch join in PySpark
devices: DataFrame = spark.read.format('delta').load(...)
visits: DataFrame = (spark.readStream.format('kafka').load()...)

(visits.join(devices_table, [visits.device_type == devices.type,
    visits.device_version == devices.version], 'left_outer'))
```

> **⚠️ Warning**
> This left join has no temporal condition because `devices` is insert-only, so missing matches
> are acceptable. But the static dataset and the streaming job have separate lifecycles — the
> streaming job does not wait for the static dataset to update. If the static dataset used a raw
> file format like JSON or CSV instead of a table format with atomicity guarantees, this could
> lead to joining against an empty reference table during a full rewrite.

Enrichment from an external API (buffered, bulk lookup):

```python
# PySpark writer with data enrichment
class KafkaWriterWithEnricher:
    BUFFER_THRESHOLD = 100
    # ...
    def process(self, row):
        if len(self.buffered_to_enrich) == self.BUFFER_THRESHOLD:
            self._enrich_ips()
            self._flush_records()
        else:
            self.buffered_to_enrich.append(row)

    def _enrich_ips(self):
        ips = (','.join(set(visit.ip for visit in self.buffered_to_enrich
            if visit.ip not in self.enriched_ips)))
        fetched_ips = requests.get(f'http://localhost:8080/geolocation/fetch?ips={ips}',
            headers={'Content-Type': 'application/json', 'Charset': 'UTF-8'})
        if fetched_ips.status_code == 200:
            mapped_ips = json.loads(fetched_ips.content)['mapped']
            self.enriched_ips.update(mapped_ips)
```

---

### Pattern: Dynamic Joiner

#### Problem

The Static Joiner is already implemented for the users-to-visits use case, but the outcome is
unsatisfying: with thousands of new users coming online each week, profile changes have
increased, and the enriched dataset becomes stale and problematic for downstream consumers. Each
user change is registered to a streaming broker via **Change Data Capture**, so a better way to
combine both moving datasets is needed.

#### Solution

Because both datasets are in motion, Static Joiner won't work — its alternative, the **Dynamic
Joiner**, is built for this.

- Shares the Static Joiner's key-identification and join-method logic, but adds one extra
  requirement: **time boundaries**. Without a time-management strategy, many joins will come back
  empty because the two streams may have different latencies.
- Time conditions imply a **time-bounded buffer** on both streams — the faster source buffers
  records, waiting for the slower source to catch up.
- This buffer introduces the **garbage collection (GC) watermark**: the mechanism that expires
  buffered records that are too old, so the buffer doesn't grow forever. You inevitably lose the
  join for records that arrive really late — that's the trade-off for a manageable buffer size.
- Most modern processing frameworks (Apache Spark Structured Streaming, Flink) implement this
  buffering natively — you don't hand-roll it.

#### Consequences

- **Space versus exactness trade-off** — The GC watermark and time boundaries mean you may not
  capture every possible join. More buffer space improves match rate but costs more hardware;
  less space saves storage but risks missed matches if latency differences are large. There's no
  one-size-fits-all formula — it depends on business requirements and typical latency skew.
- **Late data** — Streaming's low-latency semantics have weak tolerance for late data. If the
  `users` stream has connectivity issues causing delayed delivery, the GC watermark will move on
  and the buffered state will be invalidated, silently dropping the late events. To overcome this,
  you need to track and integrate late data as covered in Chapter 3.

> **⚠️ Warning**
> Neither data enrichment pattern in this chapter gives a 100% guarantee of join completeness
> without extra effort, due to late data arrival.

> **✅ Say this out loud**
> "For streaming-to-streaming enrichment I use Dynamic Joiner with watermarked buffers on both
> sides — the watermark size is a direct trade-off between join completeness and hardware cost,
> tuned to the observed latency skew between the two streams."

#### Examples

Time-based join condition in Apache Spark Structured Streaming:

```python
# Time-based condition for Apache Spark Structured Streaming
visits_from_kafka: DataFrame = (visits_data_stream # ...
    .withWatermark('event_time', '10 minutes'))
ads_from_kafka: DataFrame = (ads_data_stream # ...
    .withWatermark('display_time', '10 minutes'))

visits_with_ads = visits_from_kafka.join(ads_from_kafka, F.expr('''
    page = visit_page AND
    display_time BETWEEN event_time AND event_time + INTERVAL 2 minutes
'''), 'left_outer')
```

> The join condition has both business meaning (an ad can display at most two minutes after a page
> visit) and technical meaning (room is left for late data).

---

## Data Decoration

Data decoration adds extra value by computing individual attributes from within the record
itself — no second dataset required. Two flavors: **wrap** the record (Wrapper) or hide the extra
attributes in the **metadata layer** (Metadata Decorator).

### Pattern: Wrapper

#### Problem

A streaming layer processes visits from different data providers, resulting in different output
schemas. A job is needed to extract fields into a single place so downstream consumers get an
easy, uniform structure — while still clearly separating computed values from the original ones,
and keeping the original structure available for debugging.

#### Solution

Because the original record must stay untouched, you can't just parse and re-emit a new structure
— you'd lose the initial values. The **Wrapper** pattern adds an extra abstraction at the record
level: an envelope that wraps the original values and references computed attributes (which may
come from the input data itself or the execution context, e.g. processing time or job version).

For structured/table formats, there are **four wrapping implementations**:

| # | Implementation | Description |
|---|---|---|
| 1 | Raw flat, computed nested | Original row flat; all computed columns nested as one struct |
| 2 | Computed flat, raw nested | Opposite of #1 — computed columns flat, raw data nested |
| 3 | Fully flat | All columns (raw + computed) at the same level |
| 4 | Two separate tables | Joined later by a unique key |

Implementations 1–2 use denormalization (faster reads); #3 is normalized (slower reads, but better
logical isolation, or useful when you can't change the original structure); #4 fully separates the
datasets. All approaches need schema management (see Chapter 9's Schema Consistency patterns).

> **📌 Note**
> Even in structured/tabular formats, the wrapper envelope is still conceptually present — it's
> simply a row of a table. There's no need to break from columnar format to simulate nested
> attributes.

#### Consequences

- **Domain split** — Splitting attributes into `raw` and `computed` structures means a given
  entity's (e.g., a user's) fields live in two different high-level structures. This makes a clean
  distinction between transformed and non-transformed values, but complicates data retrieval —
  consumers must know both locations exist. Mitigation: treat the wrapped form as belonging to an
  early layer (e.g., **Silver**), not the final data exposed to end users.
- **Size** — Decorated values are an intrinsic part of the processed record and therefore impact
  overall size and network traffic (unlike the Metadata Decorator, covered next). Mitigation: use
  a storage format that supports **column/data source projection** — common in columnar
  warehouses like AWS Redshift or GCP BigQuery.

#### Examples

Wrapping metadata with PySpark:

```python
# Wrapping metadata with PySpark
visits_w_processing_context = (visits.withColumn('processing_context', F.struct(
    F.lit(job_version).alias('job_version'), F.lit(batch_number).alias('batch_version')
)))
visits_to_save = (visits_w_processing_context.withColumn('value', F.to_json(
    F.struct(F.col('value').cast('string').alias('raw_data'),
    F.col('processing_context')))))
```

Wrapping with an extra struct in SQL:

```sql
SELECT *, NAMED_STRUCT(
  'is_connected',
  CASE WHEN context.user.connected_since IS NULL
  THEN false ELSE true END,
  'page_referral_key', CONCAT_WS('-', page, context.referral)
) AS decorated FROM input_visits
```

Promoting computed values to first-class columns, raw as a nested struct:

```sql
SELECT
  CASE WHEN context.user.connected_since IS NULL
  THEN false ELSE true END AS is_connected,
  CONCAT_WS('-', page, context.referral) AS page_referral_key,
  STRUCT(visit_id, event_time, user_id, page, context) AS raw
FROM input_visits
```

---

### Pattern: Metadata Decorator

#### Problem

Streaming jobs evolve often — a new version releases almost weekly. Despite a smooth deployment
process, there's little visibility into how each release affects the generated data. Technical
context (like job version) needs to be attached to each record — but must **not** be visible to
end users.

#### Solution

Including technical context via the Wrapper pattern isn't appropriate here — consumers don't care
about internal processing details. Instead, use the storage layer's **metadata layer** directly.

- If the data store supports metadata natively (e.g., **Apache Kafka** record headers), the
  implementation is straightforward.
- For object stores, metadata can be applied as **file-level tags** when it applies uniformly to
  all rows in a file.
- If neither is available (relational/NoSQL databases), simulate decoration with a dedicated
  column or table that end users are blocked from — either via a view that excludes the column, or
  via **permissions** (see "Fine-Grained Accessor for Tables," Chapter 7).

> **📌 Note — Wrapper vs. Metadata semantics**
> This looks similar to the Wrapper pattern's structural approach, but the semantics differ:
> metadata is *not* meant to be exposed to business users (it's data about data), while the
> Wrapper is explicitly meant to decorate business attributes alongside technical ones.

> **⚠️ Warning**
> Avoid writing business-related attributes (e.g., shipment addresses, invoice amounts) into the
> metadata layer — they'll remain effectively hidden since most consumers never think to query
> metadata.

#### Consequences

- **Implementation** — Storage support for metadata is the biggest limitation. Some streaming
  brokers lack native metadata support entirely — e.g., **Amazon Kinesis Data Streams doesn't
  support headers**. For table datasets, you'll typically need an extra column or table, which
  takes more effort than data stores with native metadata support.

#### Examples

Adding a Kafka header in PySpark:

```python
# Adding a metadata header for Apache Kafka in PySpark
visits_with_metadata = (visits_to_save.withColumn('headers', F.array(
    F.struct(F.lit('job_version').alias('key'), F.lit(job_version).alias('value')),
    F.struct(F.lit('batch_version').alias('key'),
        F.lit(str(batch_number).encode('UTF-8')).alias('value'))
)))
(visits_with_metadata.write.format('kafka')
    .option('kafka.bootstrap.servers', 'localhost:9094')
    .option('includeHeaders', True).option('topic', 'visits-decorated')
    .save())
```

External metadata table (normalized approach):

```sql
-- Metadata table initialization
CREATE TABLE dedp.visits_context (
  execution_date_time TIMESTAMPTZ NOT NULL,
  loading_time TIMESTAMPTZ NOT NULL,
  code_version VARCHAR(15) NOT NULL,
  loading_attempt SMALLINT NOT NULL,
  PRIMARY KEY (execution_date_time)
)
```

---

## Trade-off Table — Data Enrichment & Decoration

| Pattern | When to Use | Trade-off |
|---|---|---|
| **Static Joiner** | Enrichment dataset is at-rest / slowly changing; also works with a streaming main dataset | Late-data consistency risk; idempotent backfills need SCD |
| **Dynamic Joiner** | Both datasets are streams (e.g., CDC-fed reference data) | Space-vs-exactness trade-off from watermark buffers; late data still causes missed joins |
| **Wrapper** | Extra attributes should stay visible and queryable alongside raw data | Domain split across raw/computed structures; adds to payload size |
| **Metadata Decorator** | Extra attributes are purely technical/debugging context, not for end users | Limited by the data store's native metadata support; not for business data |

---

## Data Aggregation

### Pattern: Distributed Aggregator

#### Problem

*(Implied by the pattern's Consequences and general framing: combining datasets and grouping
records that live across different physical nodes or stores, such as a streaming job aggregating
records by key across a partitioned or multi-store dataset, where records sharing a key are not
guaranteed to be colocated.)*

#### Solution

The classic **MapReduce**-style aggregation: a grouping function brings related rows together,
then a reduce function operates on them. Under the hood, this requires a **shuffle** — an
exchange of records, initially loaded on different machines, across the network — so the reduce
function can operate on all necessary collocated rows.

- Not all record exchanges need to be raw: any aggregation supporting **partial generation** can
  perform a partial aggregation locally before the shuffle, shrinking what's exchanged (e.g., a
  partial `COUNT` per node, then a final sum of just the counts).
- Works across physically isolated data stores too — Apache Spark can join a PostgreSQL table with
  local JSON files, or BigQuery can query external tables on GCS alongside native tables.

> **📌 Note**
> This pattern is a textbook instance of the **MapReduce** programming model, which simplified
> distributed processing starting in 2004 — from disk-based Hadoop MapReduce to memory-first
> Apache Spark.

#### Consequences

- **Additional network exchange** — Two exchanges happen: bringing input data to each node (hard
  to avoid since storage/compute colocation isn't common), and the shuffle itself to gather
  related data on the same server.
- **Data skew** — Unbalanced datasets where one key has disproportionately many occurrences make
  that key's network move and single-node processing the most expensive part of the job.
  Mitigation: **salting** — add a random "salt" value to the grouping key, aggregate on the salted
  key first, then re-aggregate on the original key. Frameworks may also offer native skew
  mitigation, e.g. Apache Spark's Adaptive Query Execution.
- **Scaling** — A node that's finished its reduce work may still be held by the hardware layer for
  fault-tolerance reasons and won't be reclaimed while the job runs. A **shuffle service** (e.g.,
  Spark's External Shuffle Service, GCP Dataflow's Shuffle) decouples shuffle-data storage from
  compute nodes so nodes can be freed even mid-job.

> **✅ Say this out loud**
> "When I see data skew in a distributed aggregation, my first lever is salting the grouping key
> and re-aggregating in two passes — it trades a bit of extra shuffle for avoiding a single
> overloaded reducer."

#### Examples

Combining two physically isolated data stores in PySpark:

```python
# Aggregation of two physically isolated data stores in PySpark
visits: DataFrame = spark_session.read.json(f'{base_dir}/input-visits')
devices: DataFrame = spark_session.read.jdbc(url='jdbc:postgresql:dedp',
    table='dedp.devices', properties={'user': 'dedp_test',
    'password': 'dedp_test', 'driver': 'org.postgresql.Driver'})

visits_with_devices = visits.join(devices,
    [devices.type == visits.context.technical.dev_type,
     devices.version == visits.context.technical.dev_version],
    'inner')
```

Checking for shuffle via the execution plan (look for `Exchange hashpartitioning`):

```text
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- SortMergeJoin [ctx#8.technical.dev_type, ctx#8.technical.dev_version],..
   :- Sort [ctx#8.technical.dev_type ASC NULLS FIRST, ...
   :  +- Exchange hashpartitioning(ctx#8.technical.dev_type, ...
   +- Sort [type#20 ASC NULLS FIRST, version#22 ASC NULLS FIRST], false, 0
      +- Exchange hashpartitioning(type#20, version#22, 200), ENSURE_REQUIREMENTS,..
```

Salting a skewed key:

```python
# Salting example in PySpark for skewed column column_a
dataset.withColumn('salt', (rand()*3).cast("int"))
    .groupBy('group_key', 'salt').agg(...)
    .groupBy('group_key').agg(...)
```

---

### Pattern: Local Aggregator

#### Problem

A streaming job generates windows for incoming visits stored in a **partitioned streaming
broker**. Data volume is static and the partition count never changes. The goal is to optimize the
job by removing the grouping shuffle step the processing framework adds automatically.

#### Solution

When you have a costly shuffle, **static data-source partitioning**, and related attributes
already stored together, the **Local Aggregator** is the alternative to the Distributed
Aggregator.

- Still performs aggregation, but only with the single network exchange of *reading* the input —
  no shuffle. Works because the fixed partitioning schema guarantees all records for a given
  grouping key already live in the same input partition.
- Bonus: tasks are **fully isolated** — they don't wait on other tasks' data, which is especially
  useful in streaming where slower processing units can otherwise delay the whole execution.
- Implementation effort shifts to the **producer side**: it must guarantee a record with a given
  grouping key always lands in the same physical partition (static per-record partitioning key +
  immutable partition count).
- Consumer-side support varies: Kafka Streams' `groupByKey` recognizes pre-partitioned data
  natively. Apache Spark has no explicit hint, but `mapPartitions`/`foreachPartition` let you
  perform local aggregation manually, and Spark avoids shuffle for datasets **bucketed** with the
  same key and bucket count.

#### Consequences

- **Scaling** — Depends on static partitioning; the pattern breaks if partition assignment for a
  key ever changes. Reorganizing storage is costly (requires reprocessing the whole dataset) and
  even trickier in streaming (a stop-the-world event is needed before producers can write to newly
  organized partitions).
- **Grouping keys** — Expects **one grouping-key logic shared by all consumers** of the
  partitioned data. If different consumers need different grouping keys (e.g., one groups by
  change type, another by user ID), at least one of them must fall back to the Distributed
  Aggregator.

> **✅ Say this out loud**
> "Local Aggregator only pays off when the producer guarantees stable partitioning by the grouping
> key — the moment two consumers need different grouping keys, or the partition count changes,
> you're back to paying for a shuffle."

#### Examples

Local aggregation via Kafka Streams' `groupByKey`:

```java
// Local aggregation in Kafka Streams
KStream<String, String> visitsSource = streamsBuilder.stream("visits");
KGroupedStream<String, String> groupedVisits = visitsSource.groupByKey();
KStream<String, AggregatedVisits> aggregatedVisits = groupedVisits
    .aggregate(AggregatedVisits::new, new AggregatedVisitsAggregator(),
        Materialized.with(Serdes.String(), new JsonSerializer<>())).toStream();
aggregatedVisits.to("visits-aggregated", Produced.with(new Serdes.StringSerde(),
    new JsonSerializer<>()));
```

Local aggregation in PySpark via partition-local sort + manual buffering:

```python
# Local Aggregator for visits in PySpark
sorted_visits: DataFrame = (visits_to_save
    .sortWithinPartitions(['visit_id', 'event_time']))

def write_records_from_spark_partition_to_kafka_topic(visits):
    kafka_writer = KafkaWriter(...)
    for visit in visits:
        kafka_writer.process(visit)
    kafka_writer.close()

sorted_visits.foreachPartition(write_records_from_spark_partition_to_kafka_topic)
```

```python
# Local Aggregator for visits in PySpark: partition-based writer
class KafkaWriter:
    def __init__(self, bootstrap_server: str, output_topic: str):
        self.in_flight_visit = {'visit_id': None}

    def process(self, row):
        if row.visit_id != self.in_flight_visit['visit_id']:
            send_visit_to_kafka(self.in_flight_visit)
            self.in_flight_visit = {'visit_id': row.visit_id, 'pages': [], ...}
        self.in_flight_visit['pages'].append(row.page)
        # ...
```

---

## Trade-off Table — Data Aggregation

| Pattern | When to Use | Trade-off |
|---|---|---|
| **Distributed Aggregator** | Data isn't guaranteed to be colocated by key; general-purpose aggregation | Network exchange (shuffle) cost; data skew; scaling/reclaiming compute mid-job |
| **Local Aggregator** | Input is statically and correctly partitioned by the grouping key already | Frozen/costly to rescale; all consumers must share one grouping key |

---

## Sessionization

Sessionization is data aggregation's specialized cousin: summarizing a user's experience into
sessions, adapted either to incremental batch workloads or real-time streaming.

### Pattern: Incremental Sessionizer

#### Problem

The data ingestion team stores visit events in an **hourly partitioned** location. Sessions should
start at a user's first visit and end after **two hours of inactivity**. Typical session duration
ranges from several minutes to three hours, so one session can span up to **three partitions**.
Analysts struggle because sessionizing correctly requires reprocessing many consecutive partitions
per user.

#### Solution

Since one session's records may spread across multiple consecutive partitions, this is an
incremental-processing problem — solved with the **Incremental Sessionizer**, building on the
**Incremental Loader** pattern (Chapter 2).

Three storage spaces are required:

| Storage | Purpose |
|---|---|
| **Input dataset storage** | Raw hourly-partitioned events to correlate |
| **Completed sessions storage** | Finished sessions, publicly exposed |
| **Pending sessions storage** | Sessions still spanning partitions; private, may carry internal/technical fields (e.g. execution ID for idempotency) |

Workflow: combine the input dataset with pending sessions from the previous run, per session
entity (user, product, visit, ...). Each combination yields one of:

- A **new session** (no pending session existed).
- A **restored session** with new incoming data.
- A **restored session with no new data** — likely near expiration.

Sessionization logic then applies three states:

1. **Initialization** — session starts (e.g., on a home-page visit).
2. **Accumulation** — session is live; new data is folded in (e.g., pages visited, in order).
3. **Finalization** — session ends, either on a specific event type or an inactivity period.

#### Consequences

- **Inactivity period** — Longer periods capture more late data but cost more compute/storage to
  hold open sessions. The right balance is business-specific. A long inactivity threshold also
  keeps sessions hidden longer — if users can tolerate partial views, you can emit them early, but
  there's a consistency risk: consumers must be told a session `is_completed: false` may still
  change (the book's example: a fraud-detection partial session flagged "not at risk" that later
  flips to "risky").
- **Data freshness** — Being a batch pattern, insight lags real time. Partial-session emission is
  the main mitigation while staying on batch infrastructure.
- **Late data, event time partitions, and backfilling** — Sessions are **forward dependent**: a
  session for the 09:00 partition affects the 10:00 one, which affects 11:00, and so on.
  Backfilling one partition means backfilling all subsequent ones — replaying everything is simple
  but costly; a smart detection-and-selective-rerun approach is cheaper but adds complexity. There
  is no silver bullet.

> **🧩 Case Study**
> The blog platform's two-hour inactivity window, spanning up to three hourly partitions per
> session, is the concrete numeric example the book uses throughout this pattern.

#### Examples

Session generation logic (Airflow-templated SQL, combining pending + new data):

```sql
-- Session generation: the logic
CREATE TEMPORARY TABLE sessions_to_classify AS
SELECT
  COALESCE(p.session_id, n.session_id) AS session_id,
  -- ...
  LEAST(p.start_time, n.start_time) AS start_time,
  GREATEST(p.last_visit_time, n.start_time) AS last_visit_time,
  ARRAY_CAT(p.pages, n.pages) AS pages,
  CASE
    WHEN n.user_id IS NULL THEN p.expiration_batch_id
    ELSE '{{ macros.ds_add(ds, 2) }}'
  END AS expiration_batch_id
FROM (SELECT ... FROM visits_{{ ds_nodash }}
  WINDOW visits_window AS (PARTITION BY visit_id, user_id ORDER BY event_time)
) AS n
FULL OUTER JOIN (
  SELECT ... FROM dedp.pending_sessions WHERE execution_time_id = '{{ prev_ds }}')
  AS p ON n.session_id = p.session_id;
```

Writing pending vs. finished sessions:

```sql
-- Session generation: the writing component
INSERT INTO dedp.pending_sessions (...)
SELECT ... FROM sessions_to_classify WHERE expiration_batch_id != '{{ ds }}';

INSERT INTO dedp.sessions (...)
SELECT ... FROM sessions_to_classify WHERE expiration_batch_id = '{{ ds }}';
```

---

### Pattern: Stateful Sessionizer

#### Problem

Stakeholders are satisfied with session availability but now want **lower latency** — impossible
with the Incremental Sessionizer, since its best latency is bounded by hourly partitions. Visits
are also available on the streaming broker within seconds. The team wants to rewrite the batch
pipeline to generate sessions in near real time.

#### Solution

Default stateless streaming pipelines don't help either — sessionization inherently needs state.
The **Stateful Sessionizer** uses a **state store**: an in-memory store for fast access, regularly
checkpointed to fault-tolerant storage to survive failures/restarts.

Two implementation abstractions:

- **Session windows** — A window per session key, with a fixed **gap duration** (max allowed
  inactivity between two events with the same key). A gap exceeding the duration starts a new
  session window.
- **Arbitrary stateful processing** — More implementation effort, more flexibility: the gap
  duration can be static or dynamic, possibly different per session key. Supported natively by
  Apache Spark Structured Streaming, Apache Flink, and GCP Dataflow.

#### Consequences

- **At-least-once processing** — Checkpointing happens irregularly, not on every state update, so
  a restart resumes from the last successful checkpoint — i.e., at-least-once semantics. Avoid
  building session-key logic on values that change between runs (e.g., wall-clock real time),
  since that would break idempotency on restart.
- **Scaling** — Changing compute capacity in a stateful job triggers **state rebalancing**: the
  job can't process data until state keys are reassigned to new workers. Not impossible, just
  costlier than for stateless jobs.
- **Inactivity period length** — Same balance as the Incremental Sessionizer: longer periods mean
  more hardware pressure but better completeness.
- **Inactivity period time** — Expiration can use **event time** (reliable, preferred) or
  **processing time** (riskier — unexpected latency, e.g. from write retries, can expire sessions
  too early). Reasoning in event time is safer for stateful pipelines.

> **✅ Say this out loud**
> "I picked event-time-based expiration over processing-time for the session state — processing
> time ties correctness to wall-clock latency, and any retry-induced delay would expire sessions
> prematurely."

#### Examples

Stateful mapping in PySpark with arbitrary stateful processing:

```python
# Stateful mapping in PySpark
grouped_visits = (visits_from_kafka.withWatermark('event_time', '1 minute')
    .groupBy(F.col('visit_id')))

visited_pages_type = ArrayType(StructType([StructField("page", StringType()),
    StructField("event_time_as_ms", LongType())]))

sessions = grouped_visits.applyInPandasWithState(
    func=map_visits_to_session,
    outputStructType=StructType([
        StructField("visit_id", StringType()), StructField("user_id", StringType()),
        StructField("start_time", TimestampType()),
        StructField("end_time", TimestampType()),
        StructField("visited_pages", visited_pages_type),
        StructField("duration_in_milliseconds", LongType())]),
    stateStructType=StructType([StructField("visits", visited_pages_type),
        StructField("user_id", StringType())]),
    outputMode="update", timeoutConf="EventTimeTimeout"
)
```

---

## Trade-off Table — Sessionization

| Pattern | When to Use | Trade-off |
|---|---|---|
| **Incremental Sessionizer** | Batch pipelines, hourly (or similar) partitioned input | Latency bounded by partition size; forward-dependent backfills are expensive |
| **Stateful Sessionizer** | Near-real-time session availability is required | At-least-once checkpointing semantics; state rebalancing complicates scaling |

---

## Data Ordering

The last data-value family: guaranteeing **chronological delivery order** downstream — easy to
say (`ORDER BY`), hard to guarantee at scale, especially against data stores with **partial commit
semantics**.

> **📌 Note — Partial commits**
> Unlike classical commits (success/failure only), some data stores can partially succeed a bulk
> write — ingesting only a subset of records. E.g., of three records timestamped 10:00, 10:10,
> 10:20, the store might write only 10:20. Retrying 10:00 and 10:10 afterward leaves the dataset
> out of order. This is most visible on streaming systems, but at-rest stores can also trigger
> downstream processing on a temporarily partial dataset. Seen in AWS Kinesis's `PutRecords`,
> DynamoDB's `BatchWriteItem`, and Elasticsearch's bulk operation.

### Pattern: Bin Pack Orderer

#### Problem

A blogging platform allows external sites to embed its pages; visit events from embeds arrive and
must be exposed via an external API for partner analytics. The synchronization job must be common
across all partners, build a **10-minute processing window with per-minute aggregates**, and flush
individually **per minute and per provider, in event-time order** — but the destination streaming
broker has **partial commit semantics**.

#### Solution

Individual per-record delivery avoids ordering issues but costs network overhead. The **Bin Pack
Orderer** uses bulk operations while still guaranteeing order under partial commits, via two steps:

1. **Sort** all related events by grouping key and event time.
2. **Pack** the sorted rows into delivery **bins**, such that each bin contains only **one**
   grouping key. Bins can be simple arrays/lists.
3. **Emit bins sequentially** — a retry within a bin stays local to that group (only one key per
   bin), and the next bin isn't sent until the current one is fully written.

> **📌 Note — In-flight requests**
> Using in-flight requests (issuing the next bulk request without waiting for the previous
> response) boosts throughput but can break ordering — if only the second of two in-flight
> requests succeeds and the first is retried, their relative order breaks.

#### Consequences

- **Retries** — Ordering is guaranteed *within a single execution*. If the whole pipeline fails and
  retries, already-emitted results are involved again, and overall ordering across runs can break.
- **Complexity** — Bin packing needs custom sort-and-bin logic; a classical sort call alone is not
  enough.

> **✅ Say this out loud**
> "Bin Pack Orderer gets me ordering under partial-commit semantics by making each bulk request
> single-key — but I still tell stakeholders that ordering is only guaranteed within one execution,
> not across pipeline-level retries."

#### Examples

Local sort preparation (no network shuffle — partitioned locally per task):

```python
# Bin packer preparation step
(events.sortWithinPartitions([F.col('visit_id'), F.col('event_time')])
    .foreachPartition(lambda rows: write_records_to_kinesis(...)))
```

Packing sorted rows into single-key bins:

```python
# Bin Pack Orderer for Amazon Kinesis Data Streams
def write_records_to_kinesis(output_stream, visits_rows):
    producer = boto3.client('kinesis')
    delivery_groups = []
    groups_index = 0
    last_visit_id: Optional[str] = None
    for visit in visits_rows:
        if visit.visit_id != last_visit_id:
            last_visit_id = visit.visit_id
            groups_index = 0
        if len(delivery_groups) <= groups_index:
            delivery_groups.append([])
        delivery_groups[groups_index].append(visit)
        groups_index += 1
    # ... bins are then delivered group by group to the Kinesis output stream
```

---

### Pattern: FIFO Orderer

#### Problem

A streaming job on the `visits` dataset needs to detect specific events and forward them, **in
processing order**, to a different stream — delivered **as soon as possible**, so buffering to
optimize network traffic is not an option.

#### Solution

For relaxed delivery constraints (no low latency or huge volume requirement), the simpler **FIFO
Orderer** applies: detect records and issue delivery requests, waiting for each record's
acknowledgment before sending the next.

- Can use a **single-record API** (AWS Kinesis `PutRecord`, or Kafka's `send(...)` followed by a
  synchronous `flush(...)`).
- Can also use a **bulk API**, but only for stores with **full commit semantics**, and only by
  limiting concurrent bulk requests (Kafka: `max.in.flight.requests.per.connection=1`, or the
  **idempotent producer** feature, which allows up to 5 concurrent requests while still
  guaranteeing order).

#### Consequences

- **I/O overhead and latency** — The core drawback: one network request per record instead of
  batched requests, increasing latency and visible pressure on delivery-rate monitoring.
  Mitigation: multithreading with per-entity process scoping — allocate all records for one entity
  (user, product) to the same process so ordering stays intact per entity, even though processes
  are otherwise isolated.
- **FIFO is not exactly-once** — FIFO only guarantees oldest-first delivery, not exactly-once. A
  naive send-then-ack loop can silently redeliver already-sent records if the ack step fails after
  a successful send. Mitigation: use one of the **idempotency patterns from Chapter 4**.

> **⚠️ Warning**
> A `producer.send(message)` immediately followed by `consumer.ack(message)` is *not* safe for
> exactly-once — if `ack()` fails after a successful `send()`, a restart will resend already
> delivered records.

> **✅ Say this out loud**
> "FIFO Orderer gives me delivery order, not delivery guarantees — for exactly-once I still need
> to layer one of the idempotency patterns from Chapter 4 on top."

#### Examples

Simplest implementation — one record, one flush:

```python
# FIFO Orderer with individual records delivery
producer.produce(...)
producer.flush()
```

Bulk requests with bounded concurrency:

```python
# FIFO Orderer with bulk requests
producer = Producer({
    'max.in.flight.requests.per.connection': 1,
    'queue.buffering.max.ms': 1000
})
producer.produce(...)
```

Idempotent producer for higher throughput while preserving order:

```python
# FIFO Orderer with idempotent producer
producer = Producer({
    'max.in.flight.requests.per.connection': 5,
    'enable.idempotence': True,
    'queue.buffering.max.ms': 2000
})
producer.produce(...)
```

---

## Trade-off Table — Data Ordering

| Pattern | When to Use | Trade-off |
|---|---|---|
| **Bin Pack Orderer** | Destination has partial-commit semantics; bulk throughput matters | Order only guaranteed within one execution; nontrivial bin-packing logic |
| **FIFO Orderer** | Low volume, latency-sensitive, order matters more than throughput | Per-record I/O overhead and latency; not exactly-once on its own |

---

## Gotchas — By Pattern

- **Static Joiner** — Late data breaks consistency between the enrichment and enriched datasets;
  idempotent backfills may require SCD if the data provider can't do time-based queries.
- **Dynamic Joiner** — Space-vs-exactness trade-off from the GC watermark buffer size; late data
  can still be silently dropped once the watermark advances past it.
- **Wrapper** — Domain split (entity attributes live in two structures: raw and computed); payload
  size grows since decorated values are part of the record itself.
- **Metadata Decorator** — Fully dependent on the storage layer's native metadata support (e.g.,
  Kinesis has no headers); scope must stay metadata-only, never business data.
- **Distributed Aggregator** — Network exchange (shuffle) cost; data skew on hot keys; reclaiming
  compute capacity after the reduce phase completes.
- **Local Aggregator** — Frozen/costly scaling tied to static partitioning; requires one shared
  grouping key across all consumers of the partitioned data.
- **Incremental Sessionizer** — Inactivity period trades resource cost against completeness;
  forward-dependent sessions make backfilling expensive; data freshness is bounded by batch cadence.
- **Stateful Sessionizer** — At-least-once processing from irregular checkpointing; state
  rebalancing complicates scaling; event-time vs. processing-time expiration choice matters.
- **Bin Pack Orderer** — Ordering guarantee only holds within a single execution, not across
  pipeline-level retries; bin-packing logic adds real implementation complexity.
- **FIFO Orderer** — Per-record I/O overhead/latency; FIFO delivery order is not the same thing as
  exactly-once delivery.

---

## Cheat Sheet

| Pattern | Problem (one line) | Solution (one line) | Biggest Gotcha |
|---|---|---|---|
| **Static Joiner** | Enrich data with a static/slowly-changing reference dataset | Key-based `JOIN`, optionally SCD type 2/4 for time-sensitivity | Late data breaks consistency; backfills need SCD for idempotency |
| **Dynamic Joiner** | Enrich a stream with another fast-moving stream | Watermarked, time-bounded buffers on both sides + GC watermark | Space-vs-exactness trade-off; late data still gets dropped |
| **Wrapper** | Separate computed attributes from raw record, but keep both visible | Envelope struct wrapping raw + computed fields | Domain split across two structures; larger payload |
| **Metadata Decorator** | Attach technical context without exposing it to end users | Native metadata layer (Kafka headers, object tags) or a hidden column/table | Storage-dependent; some stores (e.g. Kinesis) lack native metadata |
| **Distributed Aggregator** | Aggregate records not guaranteed to be colocated by key | Shuffle: exchange + group + reduce (MapReduce model) | Shuffle network cost; data skew on hot keys |
| **Local Aggregator** | Aggregate without a shuffle | Rely on static, correct producer-side partitioning by key | Frozen scaling; one grouping key must serve all consumers |
| **Incremental Sessionizer** | Build sessions on data spread across hourly (or similar) batch partitions | Input + completed-sessions + pending-sessions storage, combined each run | Forward-dependent backfills; freshness bounded by batch cadence |
| **Stateful Sessionizer** | Build near-real-time sessions on a stream | State store (session windows or arbitrary stateful processing) with checkpointing | At-least-once semantics; state rebalancing on scale changes |
| **Bin Pack Orderer** | Guarantee order on a destination with partial-commit semantics | Sort by key+time, pack into single-key bins, emit bins sequentially | Order guaranteed per-execution only; complex bin logic |
| **FIFO Orderer** | Deliver individual records in strict arrival order, low latency | Single-record or bounded-concurrency bulk delivery with per-record ack | I/O overhead; not exactly-once by itself |

---

## Further Reading

- Chapter 2, *Data Ingestion Design Patterns* — Readiness Marker and Incremental Loader patterns
  referenced for mitigating Static Joiner and Incremental Sessionizer consequences.
- Chapter 3, *Error Management Design Patterns* — Late Data Detector and late-data tracking
  referenced from both Data Enrichment patterns.
- Chapter 4, *Idempotency Design Patterns* — Idempotency techniques referenced as the fix for
  FIFO Orderer's "not exactly-once" gotcha.
- Chapter 7, *Data Security Design Patterns* — "Fine-Grained Accessor for Tables" referenced as a
  way to hide Metadata Decorator columns from end users.
- Chapter 9, *Data Quality Design Patterns* — Schema Consistency patterns referenced for managing
  Wrapper's multiple structural implementations.

### Special/Tool Notes

- **Amazon Kinesis Data Streams** does not support record headers — ruling out the native
  metadata-layer approach for the Metadata Decorator pattern on that platform.
- **Apache Spark** has no explicit "avoid shuffle" hint, but `mapPartitions`/`foreachPartition`
  plus matching bucket configuration let you approximate the Local Aggregator pattern manually.
- **Apache Kafka's idempotent producer** (`enable.idempotence=True`) allows up to 5 concurrent
  in-flight requests while preserving order — useful for FIFO Orderer throughput tuning.
- **`spark.sql.autoBroadcastJoinThreshold`** controls broadcasting behavior for large reference
  tables in join-heavy enrichment pipelines.
