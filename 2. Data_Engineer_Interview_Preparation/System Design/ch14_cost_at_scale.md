# Chapter 14 — Cost at Scale

> *(Printed as "Chapter Thirteen" in the book's own running heads — see the numbering note in
> Chapter 3. This guide follows the outer Table of Contents, so this is "Chapter 14" for citation
> purposes.)*

## The Simple Version, First

Imagine two roommates who both want to cut their household bills by the same amount. One calls
the electric company and negotiates a slightly better rate. The other actually walks through the
house and notices the water heater's been running at full blast 24/7 for no reason, half the
lights are left on in empty rooms, and one appliance is quietly using ten times the power it
should.

**Negotiating a better rate helps a little. Actually finding out where the waste is helps a
lot.** That's the entire chapter. Cutting a data platform's bill by 30–40% is almost never about
getting a better deal from a vendor — it's about figuring out **which specific queries are
scanning way more data than they need to, and moving the right data to a cheaper shelf.**

---

## What You'll Be Able to Say by the End

*(These are the book's own scripted interview lines — say them close to word-for-word.)*

> "Storage cost grows linearly; compute cost grows with the square of optimization neglect. A
> query that scans a partition isn't the same as a query that scans the table."
>
> "Cold tiering pays for itself the first time someone needs 90-day retention on a dataset that's
> hot-queried for two days after ingestion."
>
> "Reserved vs. on-demand is a bet about workload predictability. I can state the forecast error
> I'm willing to accept."
>
> "Cost per query is a user-level metric, not an aggregate. Five percent of users cause eighty
> percent of the bill, and you can't fix that by tuning the warehouse."
>
> "The best compute cost is the compute I didn't spend. Every dollar saved on a recurring query is
> saved every time it runs."

---

## Why Two Teams With the Same Starting Bill Ended Up Nowhere Near Each Other

Two data platforms at similarly-sized companies run the exact same tech stack (a cloud warehouse
plus cloud storage plus a transformation tool), both paying $1.2 million a month at the start of
the quarter.

**Team A's** finance lead negotiated a 15% discount on their warehouse contract at renewal. That
saved $180k a month, and everyone celebrated.

**Team B** identified their top 20 most expensive queries — about 1% of total query volume, but
60% of their compute cost. They rewrote the worst five using pre-computed result tables that
refresh on a schedule, so dashboards read a stored answer instead of recalculating it every time.
They moved 70% of their rarely-touched old data to a cheap archive storage tier, at roughly a
twentieth the price of their standard tier. And they switched 60% of their compute to a
discounted, pre-committed capacity plan. **They saved $480k a month, and never once talked to a
vendor.**

Same stack, same starting bill. **The difference is that Team B treated cost as a design problem,
and Team A treated it as a billing problem.**

> **❌ Anti-Pattern**
> Treating cost optimization as vendor negotiation. A vendor discount is capped at whatever margin
> the vendor is willing to give up — usually 10–20%. The architectural headroom underneath that is
> much larger (often 2x to 5x) and entirely within your own control. Every hour spent negotiating
> is an hour not spent finding the 5% of queries driving 60% of the bill. Negotiation is a closing
> move, not an opening one.

---

## Idea 1: Where the Money Actually Goes

Before optimizing anything, it helps to know roughly how a typical data platform bill breaks
down, in order of size for most organizations:

- **Compute** (usually 50–70% of the bill) — warehouse compute, batch/streaming processing
  clusters, and query-serving compute. This is the biggest lever, and the most variable: a bursty
  week can nearly double it.
- **Storage** (usually 20–30%) — warehouse storage, object storage, backups, and operational
  databases. Grows steadily and predictably with how much data you keep and for how long — low
  drama, but a big steady baseline.
- **Data movement between systems** (usually 5–15%) — moving data between cloud regions, between
  cloud and on-premises systems, or to third-party services. Easy to forget about until it's
  suddenly a large number — cross-region data copying alone can eat a meaningful chunk of a
  budget.
- **Third-party tools and managed services** (usually 5–15%, and often growing the fastest) —
  observability platforms, ingestion tools, data-catalog tools, and BI platforms.

**The reason this breakdown matters: optimization effort should follow the line items.** A team
that spends 20% of its quarter negotiating vendor deals while 5% of its users are running wasteful
queries is optimizing the wrong line item entirely.

---

## Idea 2: Storage Cost Is Simple. Compute Cost Is Not.

**Storage is linear** — twice the data, roughly twice the cost, in a straightforward and
predictable way. **Compute is not linear**, and it's not linear in two separate ways worth
understanding on their own.

### First: cost scales with how much data gets scanned, not with how complicated the question is

A query that reads 10 terabytes costs roughly 10 times as much as a query that reads 1 terabyte —
**regardless of whether that 10-terabyte scan involves one simple filter or a complicated join
across five tables.** This is the same "scan less data" lesson from query tuning, just now
measured directly in dollars instead of milliseconds. A query that only touches one day's worth of
a table is a routine, cheap cost. The same query accidentally scanning the *entire* table is a
budget event.

### Second: cost compounds with how often a query runs

A query that costs $1 to run, run once an hour, costs about $730 a month. A query that costs $50
to run, run hourly, costs about $36,000 a month. **The exact same dollar-for-dollar optimization —
say, shaving a query from $1 down to $0.10 — saves ten times more money on the expensive, frequent
query than on a one-off, ad-hoc query someone runs once.** This is why the right way to prioritize
optimization work is by *(cost per run) × (how often it runs)* — not by cost per run alone.

```sql
-- src/code-examples/ch13/cost_attribution.sql
-- Rank users by 30-day compute cost. The cumulative percentage
-- column shows how fast the top spenders consume the total bill.
-- Typical shape: top 10 users = 60% of the bill, top 20 = 80%.
WITH user_query_stats AS (
    SELECT
        user_email,
        COUNT(*) AS query_count,
        SUM(bytes_scanned) AS total_bytes_scanned,
        ROUND(SUM(bytes_scanned) / POWER(2, 40) * 5.00, 2) AS est_cost_usd
    FROM warehouse.query_history
    WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY user_email
)
SELECT
    user_email,
    query_count,
    ROUND(total_bytes_scanned / POWER(2, 40), 2) AS tb_scanned,
    est_cost_usd,
    RANK() OVER (ORDER BY est_cost_usd DESC) AS cost_rank,
    ROUND(100.0 * est_cost_usd / NULLIF(SUM(est_cost_usd) OVER (), 0), 2)
        AS pct_of_bill,
    ROUND(100.0 * SUM(est_cost_usd) OVER (ORDER BY est_cost_usd DESC)
        / NULLIF(SUM(est_cost_usd) OVER (), 0), 2) AS cumulative_pct
FROM user_query_stats
ORDER BY cost_rank
LIMIT 20;
```

**Once you know who your top spenders actually are, three fixes account for most of the savings:**

- **Pre-compute the dominant repeated queries.** If the same query runs every hour against the
  same underlying table, calculate the result once, save it, and refresh it on a schedule. Future
  queries just read the saved answer instead of recalculating it — a 10x to 100x cost reduction
  on that specific query.
- **Rewrite the classic anti-patterns from Chapter 10 (Query Engines).** A function wrapped
  around the column used for partition filtering silently disables the engine's ability to skip
  irrelevant data. Asking for every column when only a handful are needed reads far more than
  necessary. Each of these typically costs a factor of 5 to 50 in extra bytes scanned, and each is
  usually a one-line fix.
- **Route dashboards to pre-summarized tables instead of raw data.** A dashboard that refreshes
  every 15 minutes against a huge raw table can single-handedly drive 80% of a warehouse bill.
  Pointing it at an hourly or daily summary table instead cuts that dashboard's cost by 10x to
  100x — at the cost of slightly staler data, which most dashboards don't actually need as badly
  as people assume.

> **⚠️ War Story**
> A data platform team at a consumer SaaS company was paying $900k a month in warehouse costs. A
> single day spent building a cost-attribution report revealed that 62% of the bill came from just
> 14 users. Of those 14, nine were running BI dashboards directly against raw, unsummarized
> tables. Three were running ad-hoc queries that asked for every column against tables organized
> for a completely different filter pattern than what they were actually using. Two were doing
> legitimate machine-learning data preparation work. The fix: pre-computed summary tables for the
> dashboard queries (one week to build), an automatic alert that emailed a user the moment any
> single query cost more than $50 (two days to ship), and an office-hours session with the three
> ad-hoc users (one afternoon). Nobody talked to a vendor. Six weeks later, the monthly bill was
> $420k — a 53% reduction. The lesson wasn't that the users were doing anything malicious. It was
> that nobody had ever given them a tool that told them what their own queries actually cost.
> Making the cost visible was most of the fix.

---

## Idea 3: Storage Tiering — The Cheapest, Easiest Win

Cloud storage providers publish multiple pricing tiers with roughly a tenfold difference between
the cheapest and most expensive:

| Tier | Speed when accessed | Rough cost | Right for |
|---|---|---|---|
| **Hot** (Standard) | Instant, sub-100ms | ~$23/TB/month | Data queried regularly |
| **Warm** (Infrequent-Access) | Same speed, but a retrieval fee applies | ~$12/TB/month | Data accessed roughly monthly or less |
| **Cold** (Archive-Instant) | Milliseconds, higher retrieval fee | ~$4/TB/month | Data queried less than once a quarter |
| **Deep Archive** | Minutes to hours to retrieve | ~$1/TB/month | True long-term retention, rarely if ever read |

**This is usually the fastest win available, because it's low-risk and applies broadly** — most
platforms have a large fraction of data that's genuinely gone cold (untouched for 30+ days) sitting
uselessly on the most expensive tier, simply because nobody scheduled the (usually short) job to
set up an automatic tiering policy.

> **✅ Say this out loud**
> "Cold tiering pays for itself the first time someone needs 90-day retention on a dataset that's
> hot-queried for two days after ingestion."

---

## Idea 4: Reserved vs. On-Demand — A Bet on Predictability

Most cloud and warehouse vendors offer a discount (often 20–40%) if you commit upfront to a
baseline level of usage for a year or more, instead of paying full price for everything as you go.

**The size of that commitment should be driven by one specific number: how good is your
forecast?** Specifically, how far off has your actual usage tended to be from your predicted
usage, historically?

- **High predictability** (your forecast is typically within about 10% of actual usage): commit
  aggressively — 80–90% of your baseline usage. You capture the maximum discount, and any burst
  above the commitment just costs the normal on-demand rate on top.
- **Medium predictability** (forecast typically off by 10–30%): commit to a smaller, safer floor —
  maybe 50–70% of average usage. This balances discount capture against the risk of over-committing.
- **Low predictability** (forecast regularly off by more than 30%): minimal or no commitment. The
  penalty for over-committing — paying for reserved capacity you never actually use — usually
  outweighs whatever discount you'd have captured.

**The number that actually matters is your measured forecast error, not a gut feeling.** A team
that says "let's commit to 90%" without ever having measured how accurate their forecasts actually
are is betting on a future that might land at 70% usage instead — in which case the commitment
ends up costing *more* than paying full price would have. A team that has actually measured their
90-day forecast error at 8% can commit to 90% with real confidence, because they know the number
behind the decision.

> **✅ Say this out loud**
> "Reserved vs. on-demand is a bet about workload predictability. I can state the forecast error
> I'm willing to accept."

---

## Idea 5: Knowing Who's Actually Spending the Money

A single aggregate bill hides where the money goes. It breaks down into categories (compute,
storage, data movement) — but not into *people*. Who spent it? Which team, which user, which
dashboard, which pipeline?

**Per-user, per-query cost attribution is the single most useful report a team can build for cost
work.** Once there's a table showing cost per user over the last 30 days, the conversation shifts
from a vague complaint — "the warehouse is expensive" — into a concrete, actionable one: "this
specific pipeline costs $80 a month and the owner can cut it by 60% with a one-week refactor."

A genuinely useful attribution system needs three things:

1. **Per-query cost.** Every major warehouse already tracks bytes scanned or compute used, per
   query, through a built-in system log — this data usually already exists and is already
   retained; the actual work is just turning it into dollar figures and making it visible.
2. **Per-user rollups.** Aggregate that per-query data up by whoever (or whatever service account)
   actually ran each query.
3. **Monthly budget alerts.** Give each team or user an explicit monthly budget, with alerts at
   50%, 80%, and 100%. Hitting 100% shouldn't automatically block anyone (that causes its own
   business problems) — it should trigger a conversation with their team lead instead.

Without these three things, cost work becomes a quarterly finance exercise that produces
spreadsheets and no actual behavior change. With them, cost becomes an ongoing operational
feedback loop.

> **✅ Pattern**
> Ship per-user cost dashboards *before* any cost-reduction effort begins. Attribution is the
> precondition; optimization follows from it. A team that tries to cut costs without attribution
> ends up optimizing whatever's visible while the genuinely expensive stuff stays untouched. The
> cheapest way to save $100k a month is often simply showing the top five spenders their own
> numbers.

---

## A Real Interview, Walked Through Simply

The classic cost prompt: a specific savings target, no loss of capability, no vendor migration.
Watch the candidate build attribution first, sequence the work by speed of payoff, and — notably —
catch and revise their own reservation math mid-answer when they realize it doesn't fully account
for growth.

**Interviewer:** Cut the monthly data bill by 40% without reducing capabilities or migrating
vendors. Current bill is $1.2M/month: warehouse $800k, object storage $200k, ingestion tooling
$100k, other $100k.

**Candidate:** Three questions first. What's the bill's trend — growing, flat, or shrinking?

**Interviewer:** Growing about 8% a quarter.

**Candidate:** So this isn't just a cost cut, it's cost *growth control* too. Second: what does
cost attribution look like today — do we know who's spending what?

**Interviewer:** Rough team-level attribution only. No per-user, no per-query.

**Candidate:** That's the first workstream — without per-query attribution, every optimization
target is a guess. Third: is there existing storage tiering, or is everything sitting on the
default hot tier?

**Interviewer:** Everything's on the standard tier. No tiering policy at all.

**Candidate:** Good — storage will be the fastest win. Let me lay out the workstreams, sequenced
by how quickly each pays off.

**Workstream 1 — attribution (weeks 1–2).** Build the per-user, per-query cost dashboard and ship
it to users by end of week two. This is the precondition for everything else; without it we're
optimizing blind.

**Workstream 2 — storage tiering (weeks 2–4).** With most of our data untouched after 30 days, I'd
move it to an automatic tiering policy at day 30, and a colder archive tier at day 180. That
should cut the $200k storage bill by roughly 60%, saving about $120k/month — around 10% of the
total bill. Low risk, since the warm tier is identical latency when it *is* accessed.

**Workstream 3 — query optimization (weeks 4–10).** Based on the attribution dashboard, identify
the top 20 most expensive queries. I'd expect the same pattern as the earlier war story: dashboards
against raw tables, functions wrapped around partition columns, asking for every column
unnecessarily. Materialize the recurring ones, rewrite the rest. Target: 25% reduction in
warehouse spend, saving roughly $200k/month — about 17% of the total bill.

**Workstream 4 — reservation tuning (weeks 8–12).** After query optimization lands, measure the
new baseline's forecast error. If it's under 15%, commit 70% of that baseline to a one-year
reserved capacity plan.

*(pauses)*

Let me actually sanity-check that reservation number rather than just asserting it. If we commit
70% of baseline at a one-year discount of roughly 30%, the savings on that reserved portion is
70% × 30%, about 21% of the reserved compute. On a post-optimization $600k/month bill, 70%
reserved is $420k, and 30% off that is roughly $126k saved. That roughly matches my earlier
estimate. But — the 8%-per-quarter growth rate could push us past the reservation within the
committed year; if we grow 32% over the commitment year, the on-demand overage on that excess
usage eats into a chunk of the discount.

**Candidate:** Actually, let me revise that number down as a hedge. I'd commit 60% instead of 70%,
accepting roughly $100k/month in savings instead of $126k. That's $26k/month less saved, but it
protects us if growth accelerates faster than expected.

Cumulative savings so far: roughly $440k/month — about 36%, close to but not quite the 40% target.
I'd add a fifth workstream to close the gap:

**Workstream 5 — dashboard refresh renegotiation (weeks 10–14).** Most dashboards refresh every 15
minutes by default, which means they re-scan raw data up to 96 times a day. I'd audit the top 10
most expensive dashboards and confirm with stakeholders which ones actually need sub-hour
freshness. For the ones that don't, move them to hourly or daily refresh — this typically cuts
dashboard compute by roughly 80%. Estimated savings: $80k/month. Total: around 43%.

**Interviewer:** What are the risks?

**Candidate:** Three. First, reservation timing — if we commit before the query optimization has
actually landed, we lock in excess capacity based on the old, wasteful baseline. I'd sequence the
reservation *after* the optimization work, not before. Second, dashboard refresh pushback — the
users who want 15-minute freshness tend to be the most vocal about it, even when they don't
actually need it; this needs executive backing to hold the line. Third, attribution gaming — once
users can see their own costs clearly, some will route queries through shared service accounts to
avoid visibility. I'd need a service-account tagging policy in place before attribution ships,
specifically to prevent that.

**Interviewer:** What if the savings don't stick?

**Candidate:** A monthly cost review cadence. Each team lead reviews their own team's spend
monthly; anything growing more than 10% month-over-month triggers a conversation. Without that
cadence, savings typically erode within two to three quarters as new workloads ship and old
optimizations get quietly forgotten. The review itself is cheap — maybe 30 minutes per team per
month — and it's what keeps the bill from drifting back up.

---

## Common Mistakes People Make

1. **Starting with vendor negotiation.** A vendor's discount ceiling is their margin, usually
   10–20%. The architecture's ceiling is 2x to 5x that. Negotiate *after* you've optimized, not
   instead of it.
2. **Optimizing without attribution first.** You end up cutting something visible instead of
   something expensive. The genuinely expensive stuff stays untouched, and net savings are close
   to nothing.
3. **Committing to reserved capacity without measuring forecast error.** You commit to capacity
   the workload won't actually use, and the penalty cancels out the discount.
4. **Deferring storage tiering.** The easiest win available, left on the table simply because
   nobody scheduled the (typically short) job to set up the policy.
5. **Treating cost as a one-time quarterly project instead of an ongoing habit.** Savings quietly
   regress without a monthly review — cost work is operational, not a one-off initiative.

---

## The Big Ideas, One Line Each

1. **Attribution comes before optimization.** Without knowing per-user, per-query cost, every
   optimization target is a guess.
2. **Compute cost scales with bytes scanned and how often a query runs — not with how complex the
   query looks.** A cheap query run constantly can cost more than an expensive one run rarely.
3. **Storage tiering is usually the fastest, lowest-risk win available.** Most platforms have a
   large chunk of genuinely cold data still sitting on the most expensive tier.
4. **Reserved capacity is a bet you should size using your actual measured forecast error** — not
   a gut-feel percentage.
5. **Architecture has far more savings headroom than vendor negotiation ever will.** Negotiate
   last, not first.

---

## Cheat Sheet

**Where the money typically goes**
Compute 50–70% (the biggest lever) · Storage 20–30% (the easiest lever) · Data movement 5–15%
(the forgotten lever) · Third-party tools 5–15% (often growing fastest)

**Storage tiers, roughly 10x apart end to end**
Hot ~$23/TB/mo · Warm ~$12 · Cold ~$4 · Deep Archive ~$1
Reasonable defaults: hot for 30 days, warm to 180 days, cold/archive after that.

**Compute cost, two dimensions**
- Cost scales with bytes scanned, not query complexity — a partition scan isn't a table scan.
- Cost compounds with frequency — prioritize by (cost per run) × (runs per period), not cost per
  run alone.

**Reservation sizing by forecast error**
- Under 10% error → commit 80–90% of baseline
- 10–30% error → commit 50–70% of baseline
- Over 30% error → minimal or no commitment

**Cost optimization priority order**
1. Build per-user, per-query attribution (roughly a two-week build)
2. Materialize the top 5–10 recurring expensive queries
3. Rewrite function-on-partition-column and select-everything anti-patterns
4. Route dashboards to pre-summarized tables
5. Tune reservations — only after the above has landed and re-baselined

**Three lines worth memorizing**
- "Attribution before optimization. Without it, everything else is guessing."
- "Architecture before vendor negotiation. Negotiation is a closing move."
- "The best compute cost is the compute you didn't spend."

---

## Further Reading

- **Site Reliability Engineering (the "SRE Book"), on error budgets and capacity planning.**
  Google, 2016. The forecasting and capacity-commitment thinking in this chapter borrows directly
  from SRE's approach to capacity planning under uncertainty.
- **Cloud provider pricing documentation (AWS, GCP, Azure) for storage tiers and reserved
  capacity.** The specific numbers shift over time; the tiering *shape* (roughly 10x between
  hottest and coldest) has stayed consistent across providers for years.
- **Your own warehouse's query history system view** (e.g., Snowflake's `QUERY_HISTORY`,
  BigQuery's `INFORMATION_SCHEMA.JOBS`, Redshift's `STL_QUERY`). Not an external resource, but the
  single most useful "reading" for this chapter — the attribution data most platforms need already
  exists and is already retained; the real work is just turning it into dollars and surfacing it.

---

## A Couple of Extra Ideas (From the Older 2025 Edition)

- **Spot/interruptible compute as a deliberate cost lever, not just an operational side effect.**
  Fault-tolerant, non-urgent workloads — backfills, large ETL rewrites, ML training, compaction —
  can often run 70–100% on cheaper, interruptible compute instead of full-price on-demand
  capacity, typically at 60–90% lower cost for that portion of the workload. Latency-sensitive or
  stateful workloads (real-time scoring, streaming joins, schedulers) should stay on guaranteed
  capacity. Most mature platforms land on a blend: a guaranteed baseline sized to the minimum
  needed for reliability, with interruptible capacity absorbing the burst above that.
- **Serverless vs. dedicated clusters is its own cost trade-off, separate from storage/compute
  tiering.** Serverless compute is genuinely cost-effective for bursty, unpredictable, short-lived
  work — you only pay for what you use, with no idle cost. But it can get quietly expensive at
  high, sustained volume, since serverless pricing is usually per-execution and doesn't benefit
  from the caching or locality that a long-running cluster builds up over time. Long-running,
  stateful, or consistently heavy workloads (large joins, stateful streaming, ML training loops)
  tend to be cheaper on dedicated clusters instead. Most real platforms end up running both:
  serverless for ingestion, orchestration, and ad-hoc queries; clusters for the continuously
  running heavy lifting.
