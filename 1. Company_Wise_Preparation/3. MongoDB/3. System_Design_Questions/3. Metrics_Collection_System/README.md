# Design a Metrics Collection and Analysis System for a Client Database

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** System Design · **Tags:** Onsite Loop, Caching, Concurrency, Data Engineering, Databases, Distributed Systems · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Design a metrics collection and analysis system for a client database. The system should periodically collect operational and performance metrics from a client database, store them, and support analysis.

**Requirements:**

- Describe the overall architecture and components.
- Explain how metrics are collected from the client database (e.g., push vs. pull, agents, collectors).
- Define a storage model for time-series metrics and metadata.
- Discuss how the system supports querying and analysis of collected metrics (e.g., aggregations, alerting, dashboards).
- Address scalability, reliability, and retention considerations.

You do not need to write code, but be specific about components, data flow, and trade-offs.

---

## Study Tools

### Hint 1

Think of this as a pipeline with three distinct stages: acquisition, storage, and query. The hardest constraint is that you're collecting data from systems you don't fully control, so the collection layer needs to be as dumb and resilient as possible.

### Hint 2

For the storage model, a single wide metrics table will melt under analytical load. Consider separating the write path (recent, high-volume, append-only) from the read path (pre-aggregated, downsampled, indexed for range scans).

### Hint 3

Pull-based collection with a central coordinator gives you a single config surface, but you'll need a push gateway or sidecar for short-lived or NAT'd clients. For retention, use tiered storage: raw data for a few days, rolled-up aggregates for months, and a metadata catalog that never expires.

---

### Answer

This is a time-series telemetry pipeline with a pull-based collection model, a tiered storage engine, and a separate metadata catalog. The core architectural idea is to keep the write path cheap and append-only, push aggregation work to background jobs, and serve dashboards and alerts from pre-computed rollups rather than raw scans.

#### Architecture

Three main tiers, plus a control plane:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client DBs    │     │ Collection Tier  │     │  Storage Tier   │
│ (instrumented)  │────▶│  (pull agents)   │────▶│  (TSDB + object │
│                 │     │                  │     │  store + meta)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌──────────────────┐   ┌──────────▼─────────┐
                        │    Alerting      │◀──│  Query / Analysis  │
                        │ (rules engine)   │   │ (API + dashboards) │
                        └──────────────────┘   └────────────────────┘
```

The control plane holds collector configs, scrape targets, retention policies, and alert rules. It's the single source of truth for what gets collected and how long it lives.

#### Collection Model

**Pull-based, with a push fallback.** A central collector (or fleet of collectors behind a load balancer) scrapes each client database's metrics endpoint on a fixed interval — 15s or 30s for operational metrics, 60s for capacity metrics. Each client runs a lightweight agent that exposes `GET /metrics` in Prometheus text format or a compact binary protocol.

**Why pull:** the collector controls the rate, a dead client simply stops responding (no backpressure), and you can re-scrape on demand for debugging. The downside is that clients behind NAT or with ephemeral lifetimes can't be reached. For those, a **push gateway** accepts `POST /metrics` from client agents, and the collector scrapes the gateway instead.

What gets collected falls into three buckets:

- **Host-level:** CPU, memory, disk I/O, network throughput, file descriptor counts.
- **Database-level:** connections active/idle, queries per second, slow query count, replication lag, cache hit ratio, lock waits, WAL/gc metrics.
- **Business-level:** rows per collection/table, index sizes, top-N query shapes (hashed or anonymized).

Each metric is tagged with `client_id`, `db_instance_id`, `host_id`, `shard_id`, and `dc` (datacenter). Tags are the dimensions you'll group by later.

#### Storage Model

Three stores, each optimized for a different access pattern:

```sql
-- Metadata catalog: relational, small, long-lived
CREATE TABLE clients (
    client_id       UUID PRIMARY KEY,
    org_name        TEXT NOT NULL,
    plan_tier       TEXT NOT NULL,              -- 'free', 'pro', 'enterprise'
    retention_days  INT NOT NULL DEFAULT 30,
    created_at      TIMESTAMPTZ NOT NULL
);

CREATE TABLE db_instances (
    db_instance_id  UUID PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id),
    db_version      TEXT NOT NULL,
    topology        TEXT NOT NULL,              -- 'standalone', 'replica_set', 'sharded'
    shard_count     INT NOT NULL DEFAULT 1,
    region          TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL
);

CREATE TABLE metric_definitions (
    metric_id       SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,       -- 'db.connections.active'
    unit            TEXT NOT NULL,              -- 'count', 'bytes', 'seconds'
    metric_type     TEXT NOT NULL,              -- 'gauge', 'counter', 'histogram'
    description     TEXT
);
```

```sql
-- Hot tier: recent raw samples, fast append, fast range scans
CREATE TABLE metrics_recent (
    db_instance_id  UUID NOT NULL,
    metric_id       INT NOT NULL,
    ts              TIMESTAMPTZ NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    labels          JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (db_instance_id, metric_id, ts)
) PARTITION BY RANGE (ts);

-- One partition per day, dropped after the raw retention window
CREATE TABLE metrics_recent_2025_01_15 PARTITION OF metrics_recent
    FOR VALUES FROM ('2025-01-15') TO ('2025-01-16');
```

```sql
-- Cold tier: pre-aggregated rollups, compact, long-lived
CREATE TABLE metrics_rollup_1h (
    db_instance_id  UUID NOT NULL,
    metric_id       INT NOT NULL,
    ts_bucket       TIMESTAMPTZ NOT NULL,       -- start of the 1-hour bucket
    labels          JSONB NOT NULL DEFAULT '{}',
    count           BIGINT NOT NULL,
    sum             DOUBLE PRECISION NOT NULL,
    min             DOUBLE PRECISION NOT NULL,
    max             DOUBLE PRECISION NOT NULL,
    avg             DOUBLE PRECISION NOT NULL,
    p50             DOUBLE PRECISION,
    p95             DOUBLE PRECISION,
    p99             DOUBLE PRECISION,
    PRIMARY KEY (db_instance_id, metric_id, ts_bucket, labels)
);
```

The hot tier holds raw samples for **2–7 days** depending on plan tier. A background rollup job (run every hour, or continuously with a lag) aggregates raw samples into `metrics_rollup_1h` and `metrics_rollup_1d` buckets. The 1-hour rollups live for **90 days**; 1-day rollups for **13 months**. Raw data past the retention window is dropped by **dropping the partition**, which is O(1) and doesn't fragment the table.

**Why not a single table with a long retention:** a month of 15-second samples for 10,000 instances at 200 metrics each is 10,000 × 200 × (30 × 24 × 60 × 4) ≈ **345.6 billion rows**. Range scans over that are brutal. Rollups cut the query surface by 360× for hourly data and 8,640× for daily data.

#### Query and Analysis

A query API sits in front of the storage tier:

```
GET  /api/v1/query?metric=db.connections.active&instance=<id>&start=<ts>&end=<ts>&step=60s
GET  /api/v1/query_range?metric=db.queries.per_sec&instance=<id>&start=<ts>&end=<ts>&step=5m
GET  /api/v1/aggregate?metric=db.slow_queries&group_by=client_id,dc&start=<ts>&end=<ts>&agg=sum
POST /api/v1/alert_rules
POST /api/v1/dashboards
```

The query engine picks the storage tier automatically: if the requested time range is within the raw window and the step is fine-grained, it hits `metrics_recent`; otherwise it hits the rollup tables. Dashboards poll the query API; alert rules are evaluated by a separate rules engine that runs every 30–60 seconds and pushes to webhooks, email, or PagerDuty.

#### Scalability and Reliability

**Collector scaling:** shard the scrape targets by `client_id` hash across N collector nodes. Each collector is stateless — target config comes from the control plane. If a collector dies, another picks up its shard. Target count per collector is bounded by scrape interval × scrape throughput; a single collector can handle ~10,000 targets at 30s intervals comfortably.

**Storage scaling:** the hot tier partitions by time, so inserts are append-only per partition. If write throughput exceeds a single node, shard by `db_instance_id` hash across multiple TSDB nodes. Rollup jobs read from the hot tier and write to the cold tier in batches, so they're naturally parallelizable per `db_instance_id`.

**Reliability:** the collection tier is allowed to **drop samples under overload** (metrics are lossy by design). The storage tier uses replication (3× for hot tier, erasure coding for cold tier object storage). The metadata catalog is small enough to fit in a single PostgreSQL with a hot standby.

**Retention enforcement:** daily partition drops for raw data, a scheduled `DELETE` with `LIMIT` batches for rollups past their window, and a nightly job that flags clients whose retention policy changed.

#### Capacity Numbers (worked out)

Assume **5,000 client DB instances, each emitting 200 metrics every 15 seconds.**

- **Ingest rate:** 5,000 × 200 / 15s ≈ **66,700 samples/second**. With tags and overhead, ~100 KB/s per instance, or ~500 MB/s total. This fits in a handful of collector nodes.
- **Raw storage per day:** 66,700 samples/s × 86,400 s/day × (8 bytes value + ~50 bytes tags + ~12 bytes ts) ≈ 66,700 × 86,400 × 70 bytes ≈ **403 GB/day**. A 7-day raw window is ~2.8 TB — fits on a single TSDB node with replication.
- **Rollup storage per day (1h):** 5,000 × 200 × 24 buckets × ~100 bytes ≈ **2.4 GB/day**. 90 days is ~216 GB.
- **Rollup storage per day (1d):** 5,000 × 200 × 1 bucket × ~100 bytes ≈ **100 MB/day**. 13 months is ~39 GB.
- **Query load:** dashboards with 5s refresh for 100 concurrent users hitting 1-hour rollups at 10 queries per refresh = **200 QPS**. Each query scans a few thousand rows in a partition; total query time under 50 ms if indexed properly.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive version: a single collector that scrapes every client DB every 15 seconds and writes raw samples into one big `metrics` table with `(db_instance_id, metric_name, ts, value, tags)` columns. That works for 50 clients. The problem is it falls apart in three places at once: the collector becomes a single point of failure and a throughput bottleneck, the table grows unboundedly, and every dashboard query triggers a full scan over billions of rows.

The first decision is **collection topology**. Push means each client agent sends metrics to a central endpoint. That's simpler for clients (no inbound firewall rules), but it means a misbehaving client can flood the collector, and you have no way to re-request data if a batch is lost. Pull inverts that: the collector initiates the request, controls the rate, and can retry. The trade-off is reachability — clients behind NAT or with short lifetimes can't be pulled. So the standard answer is **pull with a push gateway as an escape hatch**. State this trade-off explicitly; it shows you've thought about the operational reality.

The second decision is **storage**. A single table with a long retention window is the obvious first attempt, and the numbers kill it: with 5,000 instances and 200 metrics at 15s intervals, you're ingesting ~66,700 samples per second. Over 30 days that's ~172 billion rows. No index makes range scans over that fast. The fix is tiering: keep raw data for a short window (2–7 days) in a partitioned table where dropping old data is a partition drop, and run background rollup jobs that aggregate raw samples into hourly and daily buckets with pre-computed min, max, avg, p50, p95, p99. Dashboards and alerts almost always query rollups; raw data is only needed for forensic debugging. The rollup job is the workhorse — it's a map-reduce over time buckets, parallelizable per `db_instance_id`.

The third decision is the **metadata catalog**. Metric names, client info, instance topology, and retention policies should live in a small relational database, not in the TSDB. This keeps the TSDB lean and gives you a single place to enforce per-client retention and plan-tier limits. When a client upgrades from free to pro, you update one row in the catalog and the retention job picks it up on the next pass.

Finally, think about **failure modes**. If the collector fleet is stateless and targets are sharded by hash, a dead collector is just a re-shard event. If the TSDB write path saturates, you drop samples rather than backpressure the clients — a client database's availability is more important than your metrics completeness. If the rollup job falls behind, dashboards show stale data but the system keeps ingesting. These are the trade-offs to verbalize.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Separate the metadata catalog from the time-series data** — metric definitions and client info change slowly and need transactional consistency; samples are append-only and high-volume. Mixing them forces the TSDB to do relational work it's bad at.
- **Work out the ingest and storage numbers during the interview** — 5,000 instances × 200 metrics / 15s = ~66,700 samples/s, and ~403 GB/day of raw data. Doing the arithmetic on the whiteboard shows you can size a system, and it justifies the tiered storage design immediately.
- **State the pull vs. push trade-off explicitly** — pull gives you rate control and retry, push handles NAT and ephemeral clients. The hybrid (pull with a push gateway) is the production answer, and you should be able to say why each piece exists.
- **Design retention as partition drops, not deletes** — `DELETE` on billions of rows is a disaster; dropping a daily partition is O(1). Mention this specifically when describing retention enforcement.
- **Give the rollup job a real schema** — pre-computed count, sum, min, max, avg, and percentiles in the rollup tables. This is what makes dashboards fast and alerts cheap, and it's the difference between a design that looks good on a whiteboard and one that actually works.
- **Explain what happens when things fail** — collectors are stateless and re-shardable, the write path drops samples under overload, the rollup job can lag without affecting ingestion. Reliability in a metrics system is about graceful degradation, not perfect delivery.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you handle a client database that emits 10× more metrics than expected (cardinality explosion)?** — Think about per-client metric budgets, sampling, and label cardinality limits.
- **How do you alert on a metric that has gaps because collection failed?** — Think about staleness detection: alerting on *absence* of data, not just threshold breaches.
- **What changes if you need to support multi-tenancy with strict data isolation between clients?** — Think about storage sharding by `client_id`, per-tenant encryption, and query-time tenant scoping.
- **How would you support custom user-defined metrics from client applications, not just database internals?** — Think about a registration API, dynamic metric definitions, and validation to prevent high-cardinality label abuse.
- **How do you backfill data if a collector was down for 6 hours?** — Think about replay from client-side buffers, or reconstructing from rollups with reduced fidelity.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Two arithmetic errors in the answer

Both are verified by runnable assertions in [`3. Metrics_Collection_System.ipynb`](3.%20Metrics_Collection_System.ipynb).

### 1. The bandwidth figure is 100× too large — and contradicts the storage figure

> *"With tags and overhead, ~100 KB/s per instance, or ~500 MB/s total."*

Use the answer's own per-sample size of 70 bytes:

| | Stated | Actual |
|---|---|---|
| Per instance | 100 KB/s | 200 metrics ÷ 15s × 70 B = **933 B/s** |
| Fleet total | 500 MB/s | 66,667 × 70 B = **4.67 MB/s** |

The answer contradicts itself two bullets later. 403 GB/day ÷ 86,400 s = **4.67 MB/s** — the correct figure. If ingest really were 500 MB/s, raw storage would be **43 TB/day**, not 403 GB/day.

This matters because the two numbers point at completely different systems. At 4.67 MB/s a single collector's NIC is 99.5% idle and bandwidth never enters the design. At 500 MB/s you need a dedicated ingest fleet and probably compression on the wire. Quoting the wrong one sends the whole conversation somewhere it doesn't need to go.

### 2. The rollup reduction factors assume a 10-second interval, not 15

> *"Rollups cut the query surface by 360× for hourly data and 8,640× for daily data."*

At the stated 15-second scrape interval:

| Rollup | Samples collapsed | Stated |
|---|---|---|
| 1 hour | 3,600 ÷ 15 = **240×** | 360× |
| 1 day | 86,400 ÷ 15 = **5,760×** | 8,640× |

360 and 8,640 are exactly the factors for a **10-second** interval (3,600÷10 and 86,400÷10). Someone changed the scrape interval and didn't recompute.

The design conclusion is unaffected — 240× is still a decisive reduction — but the reduction factor *is* the justification for the rollup tier, so it should follow from the interval you actually named. The notebook derives it from the interval instead of hardcoding it, and shows how it moves as the interval changes.

**See also:** [`21. SnapID`](../../2.%20Coding_Questions/21.%20SnapID/README.md) in the coding folder covers the MVCC/tombstone side of time-ordered data, and [`2. Distributed_Task_Scheduler`](../2.%20Distributed_Task_Scheduler/README.md) covers the partition-drop-vs-delete argument from the scheduler's side.
