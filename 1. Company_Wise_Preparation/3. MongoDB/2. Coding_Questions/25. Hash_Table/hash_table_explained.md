# Hash Table with Expiration — Explained Simply

## The Problem

A hash table where every entry has a **time to live**. After its TTL passes, the key must behave as though it were never there.

```python
t.set("a", 1, ttl=10)     # lives for 10 seconds
t.set("b", 2, ttl=5)

t.get("b")   # -> 2       (at t=0)
# ... 6 seconds later ...
t.get("b")   # -> missing (expired)
t.get("a")   # -> 1       (still alive)
```

Expiry by **timeout**, not by least-recently-used.

## Why "Just Check on Read" Isn't Enough

The obvious approach: store `(value, expiry)` and check the deadline inside `get`.

```python
if expiry <= now:
    del data[key]
    return None
```

That makes reads **correct**. But nothing ever reclaims a key that nobody asks for again.

A cache holding a million short-lived keys leaks all million, because expiring them requires *noticing* they expired — and nothing is looking.

So you need a second capability: **find the expired entries without scanning everything.**

## An Analogy First: The Fridge

A fridge full of food, each item with a use-by date.

**Checking on read** is: you reach for the milk, notice it's off, and throw it out. Fine for the milk. But the yoghurt at the back that nobody reaches for stays there forever, quietly taking up space.

**Scanning** is: once a day, take *everything* out and check every date. Correct, and exhausting — you handle 200 items to throw away three.

**The smart way** is to keep a **list of items sorted by use-by date** pinned to the fridge door. To clear out what's expired, read from the top: the first item, the second... and **stop at the first date that hasn't passed yet**. Everything below it expires later, so there's nothing more to do.

You handled exactly the three items that were actually off.

That sorted list is the **min-heap**, and stopping at the first fresh item is what makes cleanup cheap.

## Two Questions, Two Structures

| Question | Structure | Cost |
|---|---|---|
| "What's the value for key K?" | **hash map** | O(1) |
| "What expires soonest?" | **min-heap** on expiry | O(1) to peek |

Same composition pattern as the [LRU cache](../10.%20LRU_Cache/README.md) — a map for lookup plus a second structure for ordering. Only the ordering criterion differs: recency there, deadline here.

## The Problem With Heaps: You Can't Reach Into Them

Here's where it gets interesting.

Suppose you `set("k", "v", ttl=5)`, then three seconds later `set("k", "v2", ttl=10)`.

The heap now contains **two** entries for `"k"` — the old deadline and the new one. You'd like to remove the stale one. **You can't.** A heap has no "find this entry and delete it" operation; only the minimum is accessible.

### The answer: lazy deletion

**Leave the garbage in.** Deal with it when it surfaces.

When `(expiry, key)` reaches the top of the heap, cross-check it against the map:

| Situation | How you know | What to do |
|---|---|---|
| The key was deleted | not in the map | pop, touch nothing |
| The key was overwritten | in the map, **different version** | pop, touch nothing |
| Genuinely expired | in the map, version matches, `expiry <= now` | pop **and** delete |
| Not expired yet | `expiry > now` | **stop** — everything after expires later |

> **The map is the source of truth. The heap is only a hint about when to look.**

## The Bug: Identifying Entries by Timestamp

The official answer detects "this heap entry is stale" by comparing expiry times:

```python
if entry is None or entry[1] != expiry:    # stale?
```

The idea is right, but it identifies an entry by its **deadline** — and two entries can share one.

```python
t.set("k", "old", ttl=5)
# ...5 seconds pass, get() expires it and removes it from the map...
t.set("k", "new", ttl=5)      # same clock reading, same TTL → SAME expiry
```

Now the stale heap entry and the live map entry have **identical** expiry times. The mismatch check passes, and `clean_expired` deletes a **live** entry.

Vanishingly unlikely with float timestamps — but it's an **identity** bug, not a timing one. The fix costs one integer:

```python
self._versions = itertools.count()      # never repeats
```

Every `set` takes the next version number. A heap entry is live only if the map holds that **exact** version. A monotonically increasing counter cannot collide.

*(Bonus: the version also gives the heap a deterministic tie-break, so it never has to compare the keys themselves — which would fail outright for keys of mixed or non-comparable types.)*

## The Other Bug: Reading the Wrong Clock

```python
expiry = time.time() + ttl        # ❌
expiry = time.monotonic() + ttl   # ✅
```

`time.time()` is **wall-clock** time, and wall-clock time moves for reasons that have nothing to do with elapsed time:

- an NTP correction
- daylight saving
- someone changing the system clock

Move it **backwards** and every TTL silently extends. Move it **forwards** and the whole table expires at once.

`time.monotonic()` only ever increases. **This is correctness, not polish** — the official answer's own talking points raise it, and its code doesn't do it.

### And inject the clock

```python
def __init__(self, clock=time.monotonic):
    self._clock = clock
```

Now tests advance a **fake clock** instead of sleeping. A one-hour TTL is testable in microseconds, and there's no flakiness.

Same dependency-injection move as passing `sleep` into the [Retry Strategy](../18.%20Retry_Strategy/README.md) scheduler.

## Step-by-Step Example (Narrated)

`set("a", 1, ttl=10)` and `set("b", 2, ttl=5)`, both at t=0.

```
map:  {a: (1, exp 10, v0),  b: (2, exp 5, v1)}
heap: [(5, v1, "b"), (10, v0, "a")]     ← ordered by deadline
```

---

**Advance to t = 6. Call `clean_expired()`.**

**Look at the heap top: `(5, v1, "b")`.**

- Is `"b"` in the map? Yes.
- Does the version match? `v1` vs `v1` — yes.
- Is `5 <= 6`? **Yes → genuinely expired.**

Pop it, delete `"b"` from the map.

---

**Look at the new top: `(10, v0, "a")`.**

- In the map, version matches.
- Is `10 <= 6`? **No.**

**Stop.** Because the heap is ordered, everything behind this expires *later* than it does. There is nothing more to reclaim.

---

**Total work: one pop and one comparison.** Not a scan of the table.

## Why It's Fast

The benchmark: a table where only ~20 entries are actually due, while the table itself grows.

| Entries | Scan every entry | Min-heap |
|---|---|---|
| 2,000 | 20.5 ms | 0.10 ms |
| 4,000 | 37.9 ms | 0.16 ms |
| 8,000 | 210.4 ms | 0.12 ms |
| 16,000 | 370.7 ms | 0.12 ms |

The scan grows with the table. The heap **doesn't move** — it costs what it *reclaims*, not what it *stores*.

At 16,000 entries that's **3,000× faster**.

## Bounding the Garbage

Lazy deletion trades promptness for speed — but without a limit, that trade becomes a leak.

Overwrite one hot key 2,000 times and the heap holds 2,000 entries for a map with **one**. So:

```python
if len(self._heap) > 2 * len(self._data) + 32:
    self._compact()      # rebuild from the live map
```

`heapify` is O(n) — cheaper than n individual pushes.

## The Follow-Up: A Background Reaper

*"How would you reclaim entries proactively?"*

Two pieces, and the interaction is the interesting part:

**1. Sleep until the next deadline, don't poll.**

`next_expiry()` says exactly how long to wait, so an idle table burns **no CPU at all**. Polling every 100 ms wakes up thousands of times an hour to find nothing.

**2. But `set` must wake the reaper.**

If a one-second TTL is created while the reaper sleeps for an hour, it would survive the hour. So `set` fires an `Event` to say "a sooner deadline now exists".

### And a surprise about locking

A hash map's `get` is normally a pure read, so a readers–writer lock would let reads run in parallel.

**Not here.** This `get` **deletes on expiry** — it's a *writer*. So the reader-writer split buys nothing.

Exactly the same counter-intuitive property as an [LRU cache](../10.%20LRU_Cache/README.md)'s `get`, for the same reason: the read has a side effect.

### How Redis does it

Both, and the reason is instructive:

- **Lazy** (on read) is free but never reclaims untouched keys.
- **Active** sampling reclaims them but costs CPU.

Redis samples a **random subset** of keys periodically rather than scanning — precisely to avoid the O(n) walk this whole design exists to eliminate.

## Common Mistakes

- **Only checking expiry on read.** Untouched keys leak forever.
- **Scanning the table to find expired entries.** O(n) per cleanup, to reclaim a handful.
- **Identifying heap entries by timestamp.** Two entries can share one; use a version counter.
- **Using `time.time()`.** Wall-clock jumps break TTLs in both directions.
- **Not injecting the clock.** Your tests now need to `sleep`, and they'll be flaky.
- **Continuing past the first live entry in cleanup.** The heap is ordered — stop there.
- **Never compacting.** Lazy deletion without a bound is an unbounded leak on a hot key.
- **Assuming `get` is a reader.** It expires, so it mutates.

## The Takeaway

> **Two questions need two structures**, sharing one set of entries: a hash map for "what is this key worth?", a min-heap for "what dies next?".

And because a heap can't be edited in place, use **lazy deletion**: leave the obsolete entry, detect it when it surfaces, and compact when the garbage outgrows the live set.

The two details that turn a plausible implementation into a correct one are both about **identity and time**: identify an entry by a version that can never repeat, and measure time with a clock that can never go backwards.
