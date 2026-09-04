# Hash Map — Explained Simply

## The Problem

Build a hash map from scratch: `put(key, value)` and `get(key)`.

Then answer the two questions that come with it:
- **What's the time complexity?**
- **How do you make it thread-safe?**

## The One Idea

An **array** gives you instant access — but only *by index*:

```python
arr[7]      # instant
```

You want instant access **by key**:

```python
map["hello"]    # also instant?
```

So: **turn the key into an index.**

```python
index = hash("hello") % capacity
```

That's the entire concept. Everything else in a hash map implementation exists to repair the places where this breaks.

## An Analogy First: A Cloakroom with Numbered Pegs

A cloakroom with 16 numbered pegs.

Instead of searching every peg for your coat, the attendant uses a **rule**: take the first letter of your surname, convert it to a number, divide by 16, and use the remainder. Your coat always goes on that peg, and it's always found on that peg. **One look, no searching.**

But the rule has an obvious problem: **Smith and Sanders both start with S.** Same peg.

That's a **collision**, and it isn't an edge case — with 16 pegs and 200 guests it's a mathematical certainty. Two options:

- **Separate chaining** — hang multiple coats on the same peg and flick through the few that are there.
- **Open addressing** — if the peg is taken, walk to the next free one.

And one more thing: if 200 coats go on 16 pegs, each peg holds a dozen coats and you're back to searching. So **when the cloakroom gets more than about three-quarters full, you move to a bigger room** and re-hang everything.

That's the load factor and the resize.

## Collisions Are Guaranteed

Infinitely many possible keys. Finitely many array slots. By the pigeonhole principle, two keys **must** eventually land on the same index.

**Separate chaining** — the approach here — stores a **linked list** at each slot:

```
buckets[1] → ("b", 2) → ("a", 1) → None
buckets[3] → ("c", 3) → None
buckets[0] → None
```

`get("a")`: hash to bucket 1, walk the chain. `"b"`? No. `"a"`? Yes → `1`.

Two comparisons — not a scan of all the keys in the map.

### Prepend, don't append

New entries go at the **head** of the chain:

```python
buckets[idx] = Entry(key, value, buckets[idx])    # O(1)
```

Appending would mean walking to the tail first, making insertion cost the chain length. Prepending is one pointer assignment.

## The Load Factor Is the Average Chain Length

```
load factor = size / capacity
```

That's literally the average number of entries per bucket.

- **0.75** → the average chain is under one node. A lookup is "hash, then look at roughly one thing". **That's the O(1).**
- **10.0** → every lookup walks ten nodes. Ten times slower.

So once the load factor passes 0.75, you **double the capacity** and rehash everything.

### Why doubling, specifically?

Rehashing is genuinely O(n) work. Doesn't that ruin the O(1) claim?

No — because doubling makes resizes exponentially rare. Across n inserts, the total rehash work is:

```
n + n/2 + n/4 + n/8 + ... < 2n
```

That's **O(1) per insert, amortised**.

If you grew by a *constant* (say +16) instead, you'd resize every 16 inserts, and the total work would be O(n²). Same argument as why `list.append` is amortised O(1).

## Step-by-Step Example (Narrated)

Capacity 4, load factor 0.75.

---

**`put("a", 1)`** → `hash("a") % 4 = 1`. Bucket 1 is empty.

```
buckets[1] → ("a",1)
size = 1        1/4 = 0.25   no resize
```

---

**`put("b", 2)`** → also hashes to bucket 1. **Collision.**

Walk the chain first: is `"b"` already there? `"a"` — no. Chain ends. So prepend:

```
buckets[1] → ("b",2) → ("a",1)
size = 2        2/4 = 0.5    no resize
```

---

**`put("a", 99)`** → hashes to bucket 1. Walk the chain: `"b"`? no. `"a"`? **Yes.**

Overwrite the value **and return immediately** — no new node, and crucially **`size` does not change**:

```
buckets[1] → ("b",2) → ("a",99)
size = 2        ← still 2
```

> **This is the bug people write.** If you increment `size` on an update, it starts counting *insertions* rather than *entries*. The load factor drifts upward and the map resizes for no reason.

---

**`put("c", 3)`, `put("d", 4)`** → size reaches 4.

```
4/4 = 1.0  >  0.75    →  RESIZE
```

Capacity doubles to 8, every entry is rehashed into the new array. Note the indices genuinely change: `hash("a") % 8` is a different slot from `hash("a") % 4`.

> A detail worth noticing: with capacity 4 and size 3, `3/4 = 0.75` exactly — and the check is `> 0.75`, strictly. So **three entries don't trigger a resize; four do.** That boundary is worth a test.

---

**`get("a")`** → bucket 1 (in the new table), walk the chain, find `"a"` → `99`.

## "O(1)" Needs an Asterisk

| Case | Cost | When |
|---|---|---|
| **Average** | O(1) | a good hash spreading keys evenly |
| **Worst** | **O(n)** | every key lands in one bucket |

Saying just "O(1)" is the red flag. Interviewers want to hear the caveat.

**And the worst case is not hypothetical.** If an attacker can choose the keys — HTTP parameter names, JSON field names — they can craft keys that all collide, turning every lookup into a full scan and every request into a CPU burn.

That's **hash flooding**, and it took down real web frameworks in 2011. It's why Python randomises string hashing per process by default (since 3.3).

The benchmark makes it visible — same map, adversarial keys:

| Entries | Healthy hash | Adversarial keys |
|---|---|---|
| 250 | 1.2 ms | 45.8 ms |
| 500 | 1.6 ms | 110.6 ms |
| 1,000 | 3.4 ms | 589.2 ms |
| 2,000 | 3.5 ms | 1,114.8 ms |

The healthy map stays flat. The adversarial one **doubles every time** — it has degenerated into the very linked list the hash map was built to replace.

*(Java 8 defends against this by converting a bucket into a balanced tree once it exceeds 8 nodes, capping the worst case at O(log n).)*

## The Bug in the Official Answer: `-1` for "Not Found"

```python
def get(self, key):
    ...
    return -1     # not found
```

But `-1` is a **perfectly good value to store**:

```python
m.put("a", -1)
m.get("a")      # -> -1
m.get("nope")   # -> -1     ← indistinguishable
```

Same trap as [Deep Key Search](../7.%20Deep_Key_Search_Nested_JSON/README.md). Use a private sentinel object, return `(found, value)`, or raise `KeyError`.

> **Never use an in-band value to signal absence.** Whatever value you pick, someone will eventually store it.

## The Second Problem: Rehashing Through `put`

The official `_resize` calls `self.put()` for each entry.

It happens to work — after doubling, the load factor is ~0.375, so it doesn't recurse. But it's **accidentally** safe: change the growth factor from 2× to 1.5× and the margin quietly shrinks.

It's also wasteful. Every `put` during a resize re-checks the load factor and re-scans the chain for duplicate keys — but the entries came *from* a valid table, so there are no duplicates.

**Rehash directly into the new array.** You can even reuse the existing `Entry` objects rather than allocating new ones.

## Thread Safety: Three Answers

The question asks about it explicitly, and there are three genuinely different answers.

### 1. One global lock

```python
with self._lock:
    ...
```

Correct, trivially. And it serialises **everything** — including reads that could safely have run in parallel.

### 2. A readers–writer lock

Many concurrent readers, exclusive writers.

**This works here** — and it's worth saying why explicitly: a hash map's `get` is a **genuine read**, mutating nothing.

Contrast the [LRU cache](../10.%20LRU_Cache/README.md), where `get` relinks the recency list and is therefore a *writer*. That's precisely why an LRU cache can't use this optimisation and a hash map can.

### 3. Lock striping

Keep N independent locks; bucket `i` is guarded by lock `i % N`. Two threads touching different buckets **never contend**, so throughput scales with N. This is what Java's `ConcurrentHashMap` does.

**The cost, and it's the interesting part:** any operation that spans the whole structure — `size()`, `resize()`, iteration — must acquire **every** lock, in a fixed order to avoid deadlock.

That's why `ConcurrentHashMap.size()` is famously approximate, and why its iterator is "weakly consistent" (it never throws, but may or may not see concurrent changes). Deliberate trades, not bugs.

> **The general lesson:** finer locks buy concurrency and send the bill to whichever operation needs to see the whole structure at once.

## Common Mistakes

- **Incrementing `size` on an update.** The load factor drifts and the map resizes needlessly.
- **Not checking for the key before inserting.** You get duplicate nodes and a wrong `size`.
- **Appending to the chain instead of prepending.** Turns O(1) insertion into O(chain length).
- **Returning `-1` for "not found".** Collides with a stored `-1`.
- **Forgetting `% capacity` on a negative hash.** Python's `hash()` returns negatives; `%` fixes it, but `abs()` would bias the distribution.
- **Growing by a constant instead of doubling.** O(n²) total rehash work.
- **Saying "O(1)" with no caveat.** It's O(1) *average, with a good hash*.
- **Rehashing through the public `put`.** Redundant work and an accidental recursion hazard.

## The Takeaway

> A hash map is an **array plus a function from keys to indices**. Arrays are O(1) by index; the hash supplies the index. Everything else — chaining, load factors, resizing — exists to repair the places where that simple idea breaks.

And the two questions attached to it have real answers, not recited ones: **O(1) average, O(n) adversarial** (with hash flooding as the reason that matters), and **thread safety is a spectrum** — one lock, a readers–writer lock, or striping — where finer granularity buys concurrency and charges you at the whole-structure operations.
