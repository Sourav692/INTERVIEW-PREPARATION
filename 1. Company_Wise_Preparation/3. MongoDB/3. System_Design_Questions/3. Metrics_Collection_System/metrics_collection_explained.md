# Metrics Collection System — Explained Simply

## The Problem

5,000 customer databases. Each one reports 200 numbers about itself, every 15 seconds, forever. Store all of it. Make dashboards fast. Don't slow down the customers' databases.

## An Analogy First: The Weather Station Archive

Picture a national weather service with 5,000 stations.

Every station records temperature every 15 seconds. Keep every reading forever and you have an archive nobody can search — to draw "average temperature in July 1987" you'd read 180,000 readings per station.

So the archive does something obvious: **at the end of each hour, it writes one summary card** — highest, lowest, average, count. At the end of each day, one card for the day.

Now "average temperature in July 1987" is **31 cards**, not 5 million readings.

The raw tapes? Kept for a week, then thrown out. Nobody ever asks what the temperature was at 3:47:15pm on a Tuesday two years ago — and if they genuinely might, that's a separate, expensive request.

That's the entire design: **raw for days, summaries for years.**

And one more detail that turns out to matter more than it sounds. The tapes are filed **one box per day**. Throwing out old data means throwing out a box — not going through every tape deciding which to keep.

## The Number That Decides Everything

Do this arithmetic *before* drawing any boxes:

```
5,000 instances × 200 metrics ÷ 15 seconds  =  66,700 samples/second

66,700/s × 86,400 s/day × 70 bytes          =  403 GB/day
                                               5.76 billion rows/day
                                               172 billion rows/month
```

> **172 billion rows a month.** No index makes a range scan over that fast.

That single number kills the obvious design — one big `metrics` table — and forces all three of the real decisions: tiering, rollups, and partition drops. Say it out loud and the architecture defends itself.

## Pull vs. Push

| | **Push** (client sends) | **Pull** (you fetch) |
|---|---|---|
| Firewall | easy — outbound only | needs to reach the client |
| Rate control | the client decides | **you** decide |
| A misbehaving client | floods you | can't — you set the pace |
| Lost batch | gone | re-scrape it |
| A dead client | silence, indistinguishable from idle | **connection fails — a real signal** |
| NAT / short-lived instances | works | **can't be reached** |

Pull wins on everything except the last row — and the last row is real. So:

> **Pull by default, with a push gateway as an escape hatch.**

Clients that can't be reached push to the gateway; the collector scrapes the gateway like any other target. One collection path, one config surface, one exception handled explicitly.

## The Three Stores, and Why They're Three

| Store | Holds | Access pattern | Size |
|---|---|---|---|
| **Metadata catalog** | clients, instances, metric definitions | relational, transactional, tiny | MBs |
| **Hot tier** (`metrics_recent`) | raw samples, 2–7 days | append-only, partitioned by day | 2.8 TB |
| **Cold tier** (rollups) | hourly + daily summaries | range scans, long-lived | 256 GB |

The instinct is to put everything in the time-series database. Don't. **Metric definitions and client info change slowly and need transactions; samples are append-only and enormous.** Mixing them forces the TSDB to do relational work it's bad at, and the catalog is what lets you change one row when a client upgrades their plan and have retention follow.

### The bargain the rollups strike

```
13 months of rollups (1h for 90d + 1d for 13mo):   256 GB
ONE day of raw samples:                            403 GB
```

> **Over a year of queryable history costs less than a day of raw data.**

That's the whole justification for the cold tier in one comparison.

## What a Rollup Actually Buys

One "last 30 days" chart, one series:

| Read from | Rows |
|---|---|
| raw | **172,800** |
| 1h rollup | 720 |
| 1d rollup | **30** |

And 30 rows is all a 30-point chart can draw anyway. You were never going to render 172,800 points on a 900-pixel-wide panel — you were going to average them **at query time, on every refresh, for every user.** The rollup does that averaging once, in the background, and everyone reads the result.

**That's the reframe:** a rollup isn't a compression trick, it's *moving work from read time to write time*. Same idea as fan-out on write in the chat problem — pay once, make every read cheap.

## Retention: Why the Table Is Partitioned

This is the detail that separates a whiteboard design from one that survives.

The obvious way to enforce a 7-day window:

```sql
DELETE FROM metrics_recent WHERE ts < now() - interval '7 days';
```

On 5.76 billion rows a day, that's a production incident. It rewrites every row it touches, bloats the index instead of shrinking it, needs a vacuum afterwards, and holds a long transaction open on a table taking 66,700 inserts a second.

The alternative:

```sql
DROP TABLE metrics_recent_2025_01_08;
```

One unlink. **O(1) instead of O(5,760,000,000).**

> The table is `PARTITION BY RANGE (ts)` **so that deletion is a file operation.** Partitioning here isn't a performance tweak — it's the delete strategy.

The rollup tables *do* still need batched `DELETE`s — but at 24 million rows/day instead of 5.76 billion, 240× smaller. Which is exactly what makes a `DELETE` tolerable there and intolerable in the hot tier.

## Two Numbers in the Answer Are Wrong

### The bandwidth figure is 100× too big — and contradicts the next bullet

> *"~100 KB/s per instance, or ~500 MB/s total."*

Using the answer's own 70 bytes per sample:

| | Stated | Actual |
|---|---|---|
| Per instance | 100 KB/s | 200 ÷ 15 × 70 = **933 B/s** |
| Fleet | 500 MB/s | 66,667 × 70 = **4.67 MB/s** |

And the answer refutes itself two bullets later: **403 GB/day ÷ 86,400 = 4.67 MB/s.** If ingest were really 500 MB/s, storage would be 43 TB/day, not 403 GB.

Why care about a number that doesn't change the boxes on the diagram? Because it changes what you *talk about*:

- At **4.67 MB/s**, a 1 Gb NIC sits 96% idle. Bandwidth never comes up.
- At **500 MB/s**, you need a dedicated ingest fleet, wire compression, and a conversation about network topology.

Quote the wrong one and you spend ten minutes of the interview solving a problem you don't have.

### The rollup reduction factors are computed at the wrong interval

> *"Rollups cut the query surface by 360× hourly and 8,640× daily."*

At the stated 15-second interval:

| | Actual | Stated |
|---|---|---|
| 1 hour | 3,600 ÷ 15 = **240×** | 360× |
| 1 day | 86,400 ÷ 15 = **5,760×** | 8,640× |

360 and 8,640 are precisely the factors for a **10-second** interval. Someone changed the scrape interval and didn't recompute downstream.

The conclusion survives — 240× still justifies the rollup tier. But the reduction factor **is** the justification, so it has to follow from the interval you just named. **Derive it, don't quote it.**

## Capacity Isn't Always What Sizes a Fleet

```
5,000 targets ÷ 10,000 targets per collector  =  0.5 collectors
```

One collector covers the entire fleet twice over. You run **three** anyway.

Not for throughput — for **availability**. Collectors are stateless with targets sharded by `client_id` hash, so a dead collector is just a re-shard event rather than an outage.

Being explicit about *which constraint you're sizing against* is worth saying out loud. "Three collectors" sounds like a capacity answer; it isn't.

## The Rule That Makes This a Metrics Problem

> **If the write path saturates, drop samples. Never apply backpressure to the client's database.**

The customer's database availability outranks your telemetry's completeness. Metrics are **lossy by design** — a gap in a chart is a bad afternoon; a monitoring system that slows down the thing it monitors is an outage you caused.

Almost nothing else in systems design gets to say that. Saying it is what marks this as a metrics problem rather than a generic ingest problem.

The same principle runs through every failure mode:

| What fails | What happens | Why it's acceptable |
|---|---|---|
| A collector | re-shard; another picks up its targets | stateless |
| The write path | samples dropped | client DB stays healthy |
| The rollup job | dashboards go stale | ingestion continues |
| The catalog | no new registrations | existing collection unaffected |

**Reliability in a metrics system is graceful degradation, not perfect delivery.**

## The Follow-Up Worth Preparing: Cardinality Explosion

A label with 100 distinct values doesn't add 1 series. It **multiplies** — `http_requests{status="200"}` and `{status="404"}` are separate series.

One customer, one 100-value label:

```
Normal:                200 series
After the label:    20,000 series
Extra storage:       7.98 GB/day  =  2% of the ENTIRE fleet
```

**Ten such customers cost 20% of your total storage.** And note who pulled the trigger: three of the four inputs to your capacity model — instance count, metrics per instance, scrape frequency — are set by *clients*, not by you.

Defences, best first:

1. **Cardinality limits at registration.** Reject the metric definition. The client finds out immediately, in their own deploy, not in your on-call page.
2. **Per-client series budgets at ingest.** Drop *new* series past the cap; keep existing ones working.
3. **Sampling.** Last resort — it makes the data lie in ways users can't see.

Enforce at write time. Discovering cardinality at query time means discovering it as a timeout.

## The Other Follow-Up: Alerting on Gaps

A rule like `cpu > 90%` can only fire on data that arrived. If collection breaks, the rule is **silently true of nothing** — the most dangerous failure a monitoring system has, because the dashboard is green and the alert is quiet.

You need **staleness detection** as a first-class rule type — `absent(metric) for 5m` — and it should be the *default* for every registered instance, not something each user remembers to add.

> Alert on absence, not just on thresholds.

## Common Mistakes

- **Designing before sizing.** Every decision here falls out of "172 billion rows/month". Draw boxes first and you can't justify any of them.
- **One big table with long retention.** The design the numbers exist to kill.
- **`DELETE` for retention.** Partition drops, and it's why the table is partitioned at all.
- **Putting metric definitions in the TSDB.** Slow-changing relational data belongs in a relational store.
- **Push-only collection.** No rate control, and a bad client can flood you.
- **Pull-only collection.** NAT'd and short-lived clients are unreachable.
- **Backpressuring the client database.** Never. Drop samples.
- **Threshold alerts with no staleness rule.** Silent when it matters most.
- **Unbounded user-defined labels.** How cardinality explosions get in.
- **Quoting numbers you didn't derive.** Both errors in the source answer are figures that stopped tracking their assumptions.

## The Takeaway

> Keep raw data for days, summaries for years, and make deleting a file operation.

Three ideas carry it: **size it before you design it** (the row count forces every structural choice), **move work from read time to write time** (rollups pre-compute what every dashboard would otherwise recompute per refresh), and **metrics are lossy by design** (drop samples before you ever slow down the system you're watching).

And the habit worth stealing: **cross-check your own derived numbers against each other.** 500 MB/s and 403 GB/day can't both be true. Nothing but that check would have caught it.
