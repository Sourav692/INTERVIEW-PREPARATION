# Hash Map

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Concurrency, Hash Tables, OOP & Design Patterns · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

Implement a hash map class with `put` and `get` methods. What's the time complexity? How to make the map thread safe?

---

## Study Tools

### Hint 1

The core idea is to map each key to an index in an underlying array using a deterministic function, then handle the case where two different keys produce the same index.

### Hint 2

For the collision resolution, think about storing a linked list of `(key, value)` pairs at each array slot so you can walk the chain when looking up a key.

### Hint 3

Use an array of buckets where each bucket is a linked list. Resize the array (typically doubling it) and rehash all existing entries whenever the **load factor** exceeds a threshold like 0.75.

---

### Answer

This is a classic **separate-chaining** hash map. You maintain an array of buckets, each bucket holding a linked list of key-value pairs. `put` hashes the key to find the bucket, updates the value if the key already exists, otherwise appends a new node. `get` hashes, walks the chain, and returns the value or -1 if absent. Average-case complexity is O(1) for both operations; worst case is O(n) when all keys collide into one bucket. Thread safety can be achieved by making `put` and `get` synchronized, or by using a concurrent structure like `ConcurrentHashMap` that does lock striping.

```python
class ListNode:
    def __init__(self, key, val, next_node=None):
        self.key = key
        self.val = val
        self.next = next_node


class MyHashMap:
    def __init__(self):
        self.capacity = 16
        self.size = 0
        self.load_factor = 0.75
        self.buckets = [None] * self.capacity

    def _hash(self, key):
        return hash(key) % self.capacity

    def put(self, key, value):
        idx = self._hash(key)
        head = self.buckets[idx]

        # Check if key already exists in the chain
        curr = head
        while curr:
            if curr.key == key:
                curr.val = value
                return
            curr = curr.next

        # Key not found, prepend new node
        new_node = ListNode(key, value, head)
        self.buckets[idx] = new_node
        self.size += 1

        # Resize if load factor exceeded
        if self.size / self.capacity > self.load_factor:
            self._resize()

    def get(self, key):
        idx = self._hash(key)
        curr = self.buckets[idx]
        while curr:
            if curr.key == key:
                return curr.val
            curr = curr.next
        return -1

    def _resize(self):
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        self.size = 0
        for head in old_buckets:
            curr = head
            while curr:
                self.put(curr.key, curr.val)
                curr = curr.next
```

**Time:** O(1) average for `put` and `get`; O(n) worst case when all keys collide into one chain — the hash function distributes keys uniformly, so chains stay short. **Space:** O(n) for storing n key-value pairs; each entry is a `ListNode` with key, value, and next pointer.

**Correctness:** The invariant is that every key-value pair is stored in the chain at `buckets[hash(key) % capacity]`. `put` preserves this by inserting at the correct bucket and updating in place if the key exists. `get` walks only the chain at the hashed index, so it finds the key iff it was inserted and not removed. Resizing rehashes every entry into the new array, preserving the invariant.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest possible version: a fixed-size array of `(key, value)` tuples, where `put` scans the whole array and `get` scans it too. That's O(n) per operation. The bottleneck is the linear scan — you need to jump straight to the right slot.

The first improvement is to use the key's hash to compute an index directly, giving O(1) access. But a fixed array means collisions are inevitable. You could use **open addressing** (probing for the next empty slot), but deletion gets messy and clustering hurts performance. **Chaining** with linked lists at each bucket is cleaner: collisions just append to a list, and `get` walks a short chain.

The next issue is that a fixed capacity means chains grow long as you insert more entries. Each chain's average length is `size / capacity` — the **load factor**. Once that exceeds 0.75, you double the capacity and rehash everything. Rehashing is O(n) but amortized over many inserts, so the average stays O(1). Prepend to the chain rather than append so insertion is O(1) without walking to the tail.

For thread safety, the straightforward answer is to synchronize `put` and `get` so only one thread mutates the buckets at a time. That's correct but serializes all operations. If you want better concurrency, mention `ConcurrentHashMap`'s approach: **lock striping** across bucket ranges, or a `ReadWriteLock` allowing concurrent reads while writes are exclusive. For an interview, the synchronized version plus a mention of the tradeoff is usually enough.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State the average vs. worst case complexity explicitly** — interviewers want to hear you distinguish O(1) expected from O(n) adversarial, and explain that the average assumes a good hash function. Saying just O(1) without the caveat is a red flag.
- **Explain why the load factor matters** — tying resize threshold to chain length shows you understand the performance degradation. A load factor of 0.75 keeps average chain length under 1, which is why it's the standard default.
- **Walk through a collision example on the whiteboard** — inserting keys that hash to the same index and showing how `get` traverses the chain demonstrates you actually understand the mechanics, rather than just memorized the code.
- **Mention the amortized cost of resizing** — doubling capacity and rehashing is O(n) for that one operation, but it happens rarely enough that the amortized cost per insert is still O(1). Saying this unprompted shows depth.
- **Distinguish thread safety approaches** — `synchronized` on every method is correct but kills concurrency. Mentioning `ConcurrentHashMap` or `ReadWriteLock` and the tradeoff between simplicity and throughput elevates the answer.
- **Handle the update case in `put`** — if the key already exists, you must replace the value without incrementing `size`. Forgetting this causes the load factor calculation to drift and the map to resize unnecessarily.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What changes if you use open addressing instead of chaining?** — think about how deletion works and why tombstones are needed, plus how clustering affects probe lengths.
- **How would you implement `remove(key)`?** — walk the chain at the hashed index, unlink the node, and decrement `size`; consider whether to shrink the array when the load factor drops too low.
- **What if keys are not hashable, or the hash function is malicious?** — discuss using a cryptographic hash or randomized seed to prevent collision attacks, and the worst-case O(n) degradation.
- **How does `ConcurrentHashMap` achieve better concurrency than a fully synchronized map?** — lock striping across bucket ranges, volatile reads, and CAS for lock-free updates in some cases.
- **How would you iterate over all key-value pairs efficiently?** — maintaining an auxiliary linked list of entries alongside the buckets gives O(n) iteration without scanning empty slots.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Two problems with the official answer

**1. `get` returns `-1` for "not found", which collides with a stored value of `-1`.**

```python
m.put("a", -1)
m.get("a")      # -> -1
m.get("nope")   # -> -1   ... indistinguishable
```

This is the same sentinel trap as [Deep Key Search](../7.%20Deep_Key_Search_Nested_JSON/README.md). The fix is a private sentinel object, a `(found, value)` pair, or a `KeyError`. The notebook uses a sentinel and asserts the difference.

**2. `_resize` calls `self.put`, which re-checks the load factor mid-resize.**

It happens not to recurse — after doubling, the load factor is at most ~0.375 — but it is fragile: change the growth factor from 2× to 1.5× and `0.75 / 1.5 = 0.5` is still under threshold, but the margin is now thin and entirely accidental. Rehashing should insert directly into the new bucket array rather than re-entering the public `put`, which also avoids re-running the duplicate-key scan on entries that are known to be unique.

**See also:** [`25. Hash_Table`](../25.%20Hash_Table/README.md) sounds like the same question but is a different one — it adds **TTL expiration** on top of a hash table. This problem is the table itself; that one is what happens when entries expire.
