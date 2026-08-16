# Chapter 9: Data Quality Design Patterns — Interview Cram Sheet

> Quick-recall version. 6 patterns, 2-3 lines each. Full detail lives in the long-form doc.

---

## One-Page Recall Table

| # | Pattern | One-line problem | One-line fix | #1 Gotcha |
|---|---|---|---|---|
| 1 | Audit-Write-Audit-Publish | Bad data silently reaches consumers | Audit gate before + after transform | Not every audit failure is a real issue |
| 2 | Constraints Enforcer | Pipeline code shouldn't own validation | Push type/null/value/integrity rules to DB/storage | All-or-nothing rejection, first-error-only |
| 3 | Schema Compatibility Enforcer | Producer breaks schema without warning | Backward/forward/full compatibility mode | Simple renames become add-new + deprecate-old |
| 4 | Schema Migrator | Need a breaking change (rename/retype/remove) safely | New field + old field in parallel + grace period | Needs non-transitive compatibility; costs storage |
| 5 | Offline Observer | Monitoring can't touch production resources | Separate job, independent schedule | Time-accuracy lag — consumers see bad data first |
| 6 | Online Observer | Weekly checks = consumers find issues first | Embed observation into the pipeline itself | Adds latency, or risks partial-data reads |

---

## 1. Audit-Write-Audit-Publish (AWAP)

**Problem:** Unique visitors "dropped 50%" — marketing paused a campaign over it — but the real bug was a broken aggregation, not a real traffic drop.
**Solution:** Two audit gates: cheap input-side checks (format/size/schema) before transform, real business-rule checks (row + dataset level) after — like unit tests running on live data.
**Gotcha:** Compute cost scales with validation depth; rules can go stale; an audit failure isn't automatically a real issue (e.g., a legit viral traffic spike).

> 📌 **Note:** AWAP evolves Michelle Ufford's **Write-Audit-Publish (WAP)** — the "audit" prefix is the added *input*-side gate WAP didn't have.

> ✅ **Say this out loud:** "AWAP extends unit tests onto real production data — tests are static, but datasets evolve, so AWAP validates against the dataset's current shape, not what it looked like when the tests were written."

> 🎯 **FAANG pointer:** Interviewers probe whether you'll treat *every* audit failure as a hard stop. The right answer: failures can also be **dispatched** (valid rows promoted, invalid parked separately) or **nonblocking** (published with an annotated quality flag) — not just fail/pass.

**Databricks:** Confirmed pattern — staging-based AWAP maps directly onto two chained Structured Streaming jobs writing to a Delta staging table, then auditing before promoting (`checkpointLocation` + `foreachBatch`, both native Databricks/Delta features from the book's own examples).

---

## 2. Constraints Enforcer

**Problem:** Random NULLs appearing in required fields; team wants the *load itself* to fail on bad data, without adding validation code to an already-complex pipeline.
**Solution:** Delegate to the database/storage format declaratively — four constraint types: type, nullability, value, integrity.
**Gotcha:** All-or-nothing rejection (one bad row kills the whole batch); DBs usually stop at the first error, meaning multiple round trips to find every issue.

> 📌 **Note:** Constraints are **producer-oriented** — a field nullable in the DB may still be *required* for a specific consumer, who then needs their own extra check on top.

> ✅ **Say this out loud:** "Constraints Enforcer trades flexibility for simplicity — it's declarative and needs no pipeline code, but it can't do partial dispatch like AWAP can, so I use it for hard business rules and AWAP for anything needing nuanced handling of failures."

> 🎯 **FAANG pointer:** A classic trap question — "why not just use Constraints Enforcer for everything?" Answer: coverage gaps (e.g., integrity constraints aren't supported by every table format) and all-or-nothing semantics make AWAP the more flexible complement, not a replacement.

**Databricks:** Fully native — Delta Lake's `CHECK` constraint (`ALTER TABLE ... ADD CONSTRAINT`) enforces value rules and raises `DELTA_VIOLATE_CONSTRAINT_WITH_VALUES` / `DELTA_NOT_NULL_CONSTRAINT_VIOLATED` on violation, straight from the book's own example.

---

## 3. Schema Compatibility Enforcer

**Problem:** Upstream team dropped fields they assumed were "obsolete"; a sessionization job broke repeatedly for a month as a result.
**Solution:** Enforce **backward** (new schema reads old data), **forward** (old schema reads new data), or **full** compatibility — via external registry (Kafka Schema Registry), implicit table/DB constraints, or DDL event triggers (Postgres/SQL Server).
**Gotcha:** Registry checks add a round trip per write; rigid compatibility can turn a simple rename into "add new field + deprecate old."

> 📌 **Note — Transitive vs. non-transitive:** Transitive compatibility must hold across *every* version, not just adjacent ones. Classic trap: `v0→v1` and `v1→v2` both look fine individually, but `v0→v2` can still break transitively (e.g., a field goes optional-with-default in v1, then required in v2 — a v2 reader can't safely parse v0 data).

> ✅ **Say this out loud:** "I pick backward compatibility when consumers upgrade independently of producers, forward when producers must be free to ship changes ahead of consumers, and full when I need both — but full is the most restrictive on what changes are even allowed."

> 🎯 **FAANG pointer:** Be ready to work through the transitive-vs-nontransitive Order-schema example live — it's the book's own worked proof that "compatible at each step" doesn't imply "compatible end-to-end."

**Databricks:** Partially confirmed — Delta Lake enforces schema implicitly on write (rejects unrecognized columns with a schema-mismatch `AnalysisException`, per the book's own example), which covers the "implicit with inserts" mode. Not sure about a first-class, explicit backward/forward/full compatibility *mode* configuration on Delta tables the way Kafka Schema Registry offers — flag this if asked and pivot to what's confirmed.

---

## 4. Schema Migrator

**Problem:** A visit-event schema has grown to ~60 loosely organized fields; consumers want related attributes grouped (e.g., `login`/`email`/`age` → one `user` struct) without a hard break.
**Solution:** Add the new field alongside the old, agree a transition/grace period where both are populated, then retire the old field once the deadline passes. Covers rename, type change, and removal.
**Gotcha:** Requires **non-transitive** compatibility (transitive rules block removal/rename by definition); running old + new fields together costs storage/network/I/O — some formats (Protobuf) explicitly warn against high field counts.

> ⚠️ **Warning:** This pattern only works if Schema Compatibility Enforcer is *not* set to transitive — that's a prerequisite, not an implementation detail to skip.

> ✅ **Say this out loud:** "Schema Compatibility Enforcer stops bad changes from happening; Schema Migrator is how you make a *good* breaking change happen safely — dual-write during a grace period, then cut over."

> 🎯 **FAANG pointer:** Good pattern to mention when asked "how do you rename a column in production without breaking anyone" — the two-field-plus-deadline answer is exactly what this pattern formalizes.

**Databricks:** Not sure about a dedicated Databricks/Delta feature for the dual-field grace-period mechanic itself — the book doesn't call one out. The Fine-Grained Tracker pattern (Ch. 10, often implemented via Unity Catalog lineage) is what the book points to for confirming a field is actually unused before removing it.

---

## 5. Offline Observer

**Problem:** A new pipeline is currently clean, but experience says the upstream dataset will drift. Need to monitor value distributions / null rates **without** blocking or slowing the main pipeline.
**Solution:** A fully separate observability job, on its own schedule (e.g., nightly, decoupled from hourly generation) — nonblocking by design.
**Gotcha:** Time-accuracy lag (issues may surface only after consumers already processed bad data); infrequent runs process bigger backlogs, which can cost *more* compute per run than frequent small ones.

> 📌 **Note — Observability ≠ Auditing:** Audit = **blocking** (can halt the pipeline). Observability = **nonblocking** (surfaces issues, pipeline keeps moving). This distinction is asked about directly.

> ✅ **Say this out loud:** "Offline Observer decouples monitoring from production resources entirely — the cost is time accuracy, since insight can lag behind what consumers already saw."

> 🎯 **FAANG pointer:** Expect "why not just always audit in-line?" — answer with the resource-isolation trade-off, and pivot to Online Observer as the fix when time accuracy matters more than isolation.

**Databricks:** Confirmed — the book's Spark Structured Streaming example uses `ydata-profiling`'s `ProfileReport` for HTML data profiles, plus a lag-detection function comparing checkpointed vs. latest offsets; both patterns run natively on Databricks compute against Delta/Kafka sources.

---

## 6. Online Observer

**Problem:** A `zip_code` format regression was caught by the Offline Observer — but only a week later, after consumers had already found it themselves.
**Solution:** Embed the same observation logic *into* the generation pipeline. Batch: **Parallel Split** (run alongside loading) or **Local Sequencer** (run right after). Streaming: must be embedded in-job, since it can't run as a separate pipeline.
**Gotcha:** Local Sequencer adds latency to the critical path; Parallel Split risks reading a partially-loaded/partially-valid dataset mid-write.

> 📌 **Note:** Observability isn't data-only — it also covers technical metadata (CPU/memory/disk), which naturally fits the Online Observer's near-real-time nature.

> ✅ **Say this out loud:** "Offline vs. Online Observer is a straight trade of time for accuracy — Online closes the detection gap but either slows the pipeline down or risks observing data mid-flight."

> 🎯 **FAANG pointer:** If asked to pick one, the correct move is contextual, not absolute: "It depends on whether false-negative risk (Offline's lag) or pipeline-latency risk (Online's overhead) is worse for this specific dataset's SLA."

**Databricks:** Not sure about a distinct Databricks-native "Online Observer" code path beyond general Structured Streaming `foreachBatch` composition — the book doesn't show streaming-specific Online Observer code beyond the architecture description (Parallel Split / in-job embedding), so don't overstate a dedicated feature here.

---

## The One Thread Tying This Chapter Together

Enforcement (AWAP, Constraints Enforcer) stops bad data from shipping *today*.
Schema Consistency (Compatibility Enforcer, Migrator) stops the *shape* of tomorrow's
data from silently breaking you. Observation (Offline, Online Observer) is the
feedback loop that tells you when today's enforcement rules have gone stale — because
**datasets are dynamic, and the rules you wrote last quarter won't cover what changed
since.** If an interviewer asks "how do you know your data quality rules are still
correct?" — the answer isn't "I wrote good rules once," it's **"I have an observation
pattern watching for drift the rules themselves can't see."**
