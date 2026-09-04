# Hash Table (with expiration)

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Caching, Hash Tables · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

Design/Implement a Hash table with an **expiration duration** setting (expires when it times out, **not** LRU).

---

## Study Tools

### Hint 1

Expiration is fundamentally about **ordering entries by their expiry time**. Think about which container gives you constant-time access by key and which gives you constant-time access to the soonest-expiring entry.

### Hint 2

Keep a hash map from key to `(value, expiry)`, and a separate **min-heap** keyed by expiry time. **Lazy deletion** handles stale entries: when you pop the heap, check whether that entry still exists with the same expiry.

### Hint 3

On every `get`, check if the entry's expiry has passed and remove it if so. On `set`, push `(expiry, key)` onto the heap and overwrite the map. On `clean_expired`, pop the heap while the top entry is stale.

---

### Answer

This is a hash table with TTL-based expiration. The core idea: a hash map gives O(1) keyed access, and a min-heap ordered by expiry time lets you find the soonest-expiring key in O(1) without scanning the whole table. Expired entries are removed **lazily** — they sit in the heap until they surface, at which point you verify against the map and discard if stale.

#### Implementation

```python
import heapq
import time


class ExpiringHashTable:
    def __init__(self):
        self._data = {}     # key -> (value, expiry_timestamp)
        self._heap = []     # (expiry_timestamp, key)

    def set(self, key, value, ttl_seconds):
        expiry = time.time() + ttl_seconds
        self._data[key] = (value, expiry)
        heapq.heappush(self._heap, (expiry, key))

    def get(self, key):
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if expiry <= time.time():
            del self._data[key]
            return None
        return value

    def delete(self, key):
        if key in self._data:
            del self._data[key]

    def clean_expired(self):
        now = time.time()
        while self._heap:
            expiry, key = self._heap[0]
            entry = self._data.get(key)
            if entry is None or entry[1] != expiry:
                heapq.heappop(self._heap)
                continue
            if expiry <= now:
                heapq.heappop(self._heap)
                del self._data[key]
            else:
                break

    def size(self):
        self.clean_expired()
        return len(self._data)
```

**Time:** O(1) average for `set`, `get`, `delete`; O(k log n) for `clean_expired` where k is the number of stale heap entries removed — amortized O(log n) per entry over its lifetime.

**Space:** O(n) where n is the number of live entries plus stale heap entries not yet cleaned.

#### Correctness

**Invariant:** the heap top is always the minimum expiry among all entries ever inserted. When `clean_expired` pops it, one of three cases holds: the key is gone from the map (already deleted or overwritten), the heap entry's expiry doesn't match the map's current expiry (overwritten by a later `set`), or the entry is genuinely expired. In the first two cases the heap entry is stale and discarded; in the third the map entry is removed. The loop terminates when the heap top has a future expiry, meaning no remaining entry is expired. `get` enforces the same check on a single key, so a key past its TTL is never returned.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive approach: a plain dict where `get` checks `expiry <= now` and deletes on the spot. That handles correctness for `get`, but there's no way to find **all** expired keys without iterating every entry — O(n) per cleanup.

The bottleneck is the scan. You need a structure that orders entries by expiry. A sorted list gives you the minimum in O(1) but inserting is O(n). A balanced tree gives O(log n) for both, but Python doesn't ship one, and you'd be reimplementing a heap anyway.

A **min-heap** fits: `heappush` and `heappop` are both O(log n), and `heap[0]` is the minimum expiry in O(1). The catch is that heap entries can go **stale** — a key gets overwritten with a new TTL, or deleted, and the old `(expiry, key)` tuple is still in the heap. You handle that lazily: when an entry surfaces at the top of the heap, cross-check it against the map. If the map has no entry for that key, or the expiry in the map differs from the heap's expiry, the heap entry is obsolete and you pop it without touching the map. Only when both match do you actually delete.

That's the whole design. **The map is the source of truth; the heap is an index over expiry times that you clean opportunistically.**

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Lazy deletion** — you don't need to remove expired entries the instant their TTL passes. Let them accumulate in the heap and clean them when they surface or when `clean_expired` is called. This keeps `set` and `get` at O(1).
- **Stale heap entry detection** — storing `(expiry, key)` and comparing the heap's expiry against the map's current expiry handles overwrites correctly. A key set twice with different TTLs leaves one stale heap entry, and the mismatch check catches it.
- **`get` must also expire** — a key past its TTL should return `None` even if `clean_expired` hasn't run. Checking expiry inside `get` and deleting on the spot keeps the table's observable behavior correct.
- **Amortized analysis** — each `set` pushes one heap entry, and each heap entry is popped at most once. So `clean_expired` costs O(k log n) where k is the number of stale entries, which amortizes to O(log n) per `set` over the table's lifetime.
- **Thread safety** — if multiple threads call `set` and `get`, the map and heap need a lock or you need to swap in thread-safe structures. The interviewer may push on this; mention that a single lock around all operations is the simple answer, and finer-grained locking is premature unless you have a measured contention problem.
- **Monotonic clock** — using `time.time()` is fine for an interview, but wall-clock time can jump backward. Mentioning `time.monotonic()` for TTLs shows you've thought about clock skew in real systems.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Add a background reaper thread** — how would you periodically call `clean_expired` without blocking `set`/`get`? Think about lock granularity and whether the reaper needs the same lock.
- **Persist to disk** — how do you serialize the table and the heap so expirations survive a restart? Consider writing a WAL of `set`/`delete` operations and replaying on boot.
- **Cap total memory** — what if the table grows unbounded? Add a max-size eviction policy on top of TTL expiration and discuss which entry to evict first.
- **Support `ttl_seconds = 0` or negative** — should that expire immediately, or is it an error? Define the semantics and adjust `set` accordingly.
- **Batch `get_many`** — how would you implement `get` for a list of keys efficiently, cleaning expired entries for all of them in one pass?

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Two issues with the official answer

**1. The staleness check compares floating-point timestamps.**

```python
if entry is None or entry[1] != expiry:      # stale?
```

This is *usually* right, but it identifies a heap entry by its **expiry time**, and two entries can share one. Set a key, let `get` expire it, then set it again within the same clock tick with the same TTL — the new entry's expiry equals the old heap entry's, the mismatch check passes, and `clean_expired` deletes a **live** entry.

Vanishingly unlikely with float timestamps, but it is an identity bug, not a timing one: the fix is a monotonically increasing **version counter** per `set`, which cannot collide. The notebook uses one.

**2. `time.time()` is the wrong clock.**

Wall-clock time can jump — NTP corrections, daylight saving, a manual clock change. Jump it backwards and every TTL silently extends; forwards and everything expires at once. `time.monotonic()` never goes backwards and is what TTLs should use. The answer's own talking points raise this, and the code does not do it.

The notebook uses `time.monotonic()` and injects the clock so expiry can be tested deterministically rather than with `sleep`.

**See also:** [`24. Hash_Map`](../24.%20Hash_Map/README.md) — the hash table itself, without expiration.
