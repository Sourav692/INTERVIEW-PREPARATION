# SnapID — Explained Simply

## The Problem

Build a key-value store that never forgets. Every `insert` and `delete` returns a **snapshot id**, and you can later ask:

> *"What did key `k` look like **at snapshot 3**?"*

```
insert(k1, v1)   -> snap1
insert(k2, v2)   -> snap2
delete(k1)       -> snap3
insert(k1, v3)   -> snap4

hasKey(k1, snap1) -> True      getVal(k1, snap1) -> v1
hasKey(k1, snap2) -> True
hasKey(k1, snap3) -> False
hasKey(k1, snap4) -> True      getVal(k1, snap4) -> v3
```

A normal dictionary answers *"what is it now?"*. This one answers *"what was it then?"* — so nothing can ever be overwritten.

## An Analogy First: A Ledger, Not a Whiteboard

A **whiteboard** is an ordinary dictionary. Write a new value, wipe the old one. Only the present exists.

A **ledger** is this problem. You never erase a line — you write a new one underneath:

```
line 1:  k1 = v1
line 2:  k2 = v2
line 3:  k1 DELETED
line 4:  k1 = v3
```

To answer *"what was k1 at line 2?"* you don't need a photocopy of the ledger as it stood at line 2. You just **read down the k1 entries and stop at the last one on or before line 2** — that's line 1, so `k1 = v1`.

Two things follow from the ledger view, and they're the whole solution:

1. **A deletion has to be written down.** You can't un-write line 1, so "deleted" is itself a line. That's a **tombstone**.
2. **The lines are already in order**, because line numbers only go up. So finding "the last one on or before N" is a binary search.

## Why the Obvious Way Explodes

The literal reading of "snapshot" is: **copy the whole map** after every operation.

```
snapshots[1] = {k1: v1}
snapshots[2] = {k1: v1, k2: v2}
snapshots[3] = {k2: v2}
snapshots[4] = {k1: v3, k2: v2}
```

Lookups become trivial. But look at the cost: with 1,000 keys and 1,000 operations, you store **a million entries** — to record a thousand changes.

That's O(n) work *per write* and O(n²) memory. The notebook measures it: after 2,000 operations the copying version holds **596,493** entries; the delta version holds **2,000**. That's **298× more memory** for identical information.

## The Fix: Store What Changed

Every operation touches exactly **one key**. So record exactly one thing:

```python
history = {
    "k1": [(1, "v1"), (3, TOMBSTONE), (4, "v3")],
    "k2": [(2, "v2")],
}
```

- **Writing** is now O(1) — append one entry.
- **Reading** means: find the latest entry in that key's list at or before the query snapID.

And because snapIDs only ever increase and entries are only ever appended, **each list is automatically sorted**. That's what makes the read a binary search: **O(log m)**.

> **Store the deltas, not the states.** Same idea as git commits, event sourcing, and a database's write-ahead log.

## Tombstones: Deletion as a Record

In an append-only history you can't remove anything. So a delete gets written down like everything else:

```
history["k1"] = [(1, "v1"), (3, ✝), (4, "v3")]
                              ↑
                    "k1 was deleted at snap 3"
```

The payoff is that **delete-then-reinsert needs no special case**. The timeline is just `value, tombstone, value`, and the binary search picks whichever is current at the moment you ask.

Without tombstones you'd need extra bookkeeping to distinguish "deleted at snap 3" from "never existed", and re-insertion would get genuinely fiddly.

## Step-by-Step Example (Narrated)

### Building the history

**`insert(k1, v1)`** → gets snapID **1**.
```
history = {k1: [(1, v1)]}
```

**`insert(k2, v2)`** → snapID **2**. A *different* key, so `k1`'s list doesn't change.
```
history = {k1: [(1, v1)], k2: [(2, v2)]}
```

**`delete(k1)`** → snapID **3**. Append a tombstone.
```
history = {k1: [(1, v1), (3, ✝)], k2: [(2, v2)]}
```

**`insert(k1, v3)`** → snapID **4**.
```
history = {k1: [(1, v1), (3, ✝), (4, v3)], k2: [(2, v2)]}
```

### Answering the queries

Each one: *find the latest entry at or before this snapID*.

**`hasKey(k1, 1)`** → entries `≤ 1` are `[(1, v1)]` → last is a **value** → **True** ✅

**`hasKey(k1, 2)`** → entries `≤ 2` are *still* `[(1, v1)]` → **True** ✅

> This is the interesting one. Snapshot 2 was created by an operation on `k2` — nothing happened to `k1` at all. But snapIDs are **global logical time**, not per-key indices, so "k1 at time 2" is a perfectly meaningful question. And the answer is: still `v1`, because nothing had changed it yet.

**`hasKey(k1, 3)`** → entries `≤ 3` end at the tombstone → **False** ✅

**`hasKey(k1, 4)`** → entries `≤ 4` end at `(4, v3)` → **True**, value `v3` ✅

## Three Different Kinds of "Not There"

This is what interviewers probe, and it's easy to conflate them:

| Situation | What you find | Answer |
|---|---|---|
| Key never inserted at all | no history entry | `False` |
| Query **before** the key's first insert | history exists, but nothing `≤ s` | `False` |
| Latest entry `≤ s` is a **tombstone** | entry found, it's a ✝ | `False` |
| Latest entry `≤ s` is a value | entry found | `True` |

All three "no" cases need handling, and they arrive by different routes: a missing dict key, a binary search returning -1, and a tombstone check.

### And a fourth trap: a stored `None`

If someone does `insert("k", None)`, then `getVal("k", s)` returns `None` — the same thing it returns for "absent".

This is exactly why the API has **both** `hasKey` and `getVal`. `hasKey` answers presence unambiguously; `getVal` answers value. Alternatively, take a `default` parameter so the caller can pick a sentinel they know can't collide.

## Why the Binary Search Is Legal

Worth saying out loud, because "just binary search it" skips the actual argument:

> Each key's history is sorted by snapID **because** `next_id` strictly increases and entries are only ever appended.

Sortedness isn't something you arranged — it's a consequence of how snapIDs are issued. That's what licenses the search.

The idiom itself:

```python
idx = bisect.bisect_right(entries, (snap_id, HIGH)) - 1
```

The `HIGH` sentinel makes an **exact** snapID match sort *after* the entry rather than before it, so a query at the precise moment of a write sees that write. Get it backwards and you have a silent off-by-one that only shows up on exact-match queries.

## Why It's Fast

| Operations | Copy the whole map | Append one delta |
|---|---|---|
| 500 | 1.0 ms | 0.33 ms |
| 1,000 | 6.5 ms (6.3×) | 0.49 ms (1.5×) |
| 2,000 | 33.9 ms (5.2×) | 1.09 ms (2.2×) |
| 4,000 | 155.5 ms (4.6×) | 1.94 ms (1.8×) |

The copying version **quadruples** as the workload doubles — quadratic, exactly as predicted, because each write copies a map that is itself growing. The delta version **doubles** — linear.

And the memory difference is 298×.

## Pruning: Bounded Memory Has a Price

History grows forever. Real systems discard versions no reader can still see.

Two things follow, and both matter:

**1. Keep the last entry at or before the cutoff.**

Not just "everything after the cutoff". A query *at* the cutoff still needs that entry. Dropping it silently corrupts the boundary.

**2. Below the cutoff, the past is genuinely gone.**

After pruning at snapshot 2, a query at snapshot 1 returns "absent" — not because the key was absent, but because **the information no longer exists**.

That's not a bug. It's the price of bounded memory, and every real system has it:

- MongoDB: *"resume token is no longer in the oplog"*
- Kafka: `OFFSET_OUT_OF_RANGE`

What separates a good implementation is that it **detects and reports** the stale snapID, rather than quietly answering from whatever happened to survive.

(PostgreSQL sidesteps it by tracking the oldest *live reader* and never pruning past it.)

## This Is MVCC

Worth naming in an interview, because it connects the exercise to real systems.

**Multi-version concurrency control** is exactly this design: keep multiple versions of each row, tagged with a transaction id, and let each reader see the snapshot that was current when it started.

- **PostgreSQL** stores row versions with transaction ids.
- **MongoDB's WiredTiger** does the same.

The payoff: **readers never block writers, and writers never block readers** — because nothing is ever overwritten in place. A report that takes ten minutes to run sees a consistent snapshot from ten minutes ago, while writes continue undisturbed.

## Common Mistakes

- **Copying the whole map per operation.** O(n²) time and memory, for O(n) worth of information.
- **Treating deletion as removing the entry.** In an append-only history you can't; you need a tombstone.
- **Not justifying why binary search applies.** The sortedness is a consequence of monotonic snapIDs — say so.
- **Getting the `bisect` boundary backwards.** A query at the exact snapID of a write must see that write.
- **Conflating the "not there" cases.** Never inserted, not yet inserted, and deleted are three different routes to `False`.
- **Returning `None` for both "absent" and "stored None".** That's what `hasKey` is for.
- **Pruning everything strictly older than the cutoff.** You must keep the boundary entry.
- **Using a linked list for the history.** Binary search needs random access; a linked list forces an O(m) scan.

## The Takeaway

> When you need history, **record the changes, not the states**. One entry per operation instead of one full copy, and "what was true at time T?" becomes a **lower-bound binary search** over an automatically-sorted list.

And in an append-only world, **absence must be written down**. A tombstone is what lets deletion be just another event — which is what makes delete-then-reinsert fall out with no special cases at all.
