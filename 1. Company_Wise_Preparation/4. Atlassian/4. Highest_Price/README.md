# Highest Price

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Binary Search, Hash Tables · **Difficulty/Frequency:** Very Common (8/10)

---

## Problem Statement

Given a list of timestamps and commodity prices, find the highest commodity price at a given timestamp.

- Timestamps are not necessarily sorted.
- There can be multiple entries for the same timestamp.

### Follow-up (as posed with the problem)

After each `(timestamp, commodityPrice)` entry, we create a checkpoint.

Given a timestamp and a checkpoint, return the maximum commodity price up to that checkpoint.

---

## Study Tools

### Hint 1

Think about what data structure you'd reach for if the timestamps were already sorted, then figure out what changes when they aren't.

### Hint 2

For the follow-up, the checkpoint is just an index into the sequence of entries. You need a way to answer max-in-prefix queries without scanning.

### Hint 3

Sort entries by timestamp and maintain a running maximum. For checkpoints, build a prefix-max array once, then each query is an O(1) lookup.

---

### Answer

This is a sorting plus prefix-maximum problem. Sort the `(timestamp, price)` entries by timestamp, and for the base question, scan to find the max price among entries with that timestamp. For the follow-up, precompute a prefix-max array over the sorted entries so each checkpoint query is constant time.

#### Base Question

Sort the list by timestamp. Since multiple entries can share a timestamp, group them or just scan through the sorted list tracking the max for the target timestamp. The key insight: once sorted, all entries for a given timestamp are contiguous, so you can binary search to find the range or just do a linear scan tracking the max.

```python
from collections import defaultdict

def highest_price_at_timestamp(entries, target_ts):
    """
    entries: list of (timestamp, price) tuples
    target_ts: the timestamp to query
    Returns the highest price at target_ts, or None if no entry exists.
    """
    # Group by timestamp to handle duplicates cleanly
    price_map = defaultdict(list)
    for ts, price in entries:
        price_map[ts].append(price)

    if target_ts not in price_map:
        return None
    return max(price_map[target_ts])
```

**Time:** O(n) to build the map, O(1) to query — we touch each entry once. **Space:** O(n) — the map holds all entries.

If you want to avoid the map and just sort, the approach is:

```python
def highest_price_sorted(entries, target_ts):
    entries.sort(key=lambda x: x[0])
    best = None
    for ts, price in entries:
        if ts == target_ts:
            best = max(best, price) if best is not None else price
        elif ts > target_ts:
            break
    return best
```

**Time:** O(n log n) for sorting, O(n) worst-case scan. **Space:** O(1) extra if sorting in place.

#### Follow-up: Checkpoint Queries

A checkpoint is the state after the k-th entry in the original input order. The question asks: given a timestamp t and checkpoint k, what's the maximum price among all entries up to checkpoint k that have timestamp t?

The most standard interpretation is: among all entries with the given timestamp that appear at or before checkpoint k, return the max price.

```python
def max_price_at_checkpoint(entries, target_ts, checkpoint):
    """
    entries: list of (timestamp, price) tuples in original input order
    target_ts: the timestamp to query
    checkpoint: index (0-based) representing how many entries have been processed
    Returns max price for target_ts among entries[0..checkpoint], or None.
    """
    best = None
    for i in range(checkpoint + 1):
        ts, price = entries[i]
        if ts == target_ts:
            best = max(best, price) if best is not None else price
    return best
```

**Time:** O(k) per query — scans all entries up to the checkpoint. **Space:** O(1) — constant extra space.

A more efficient approach with preprocessing: group entries by timestamp, and for each timestamp maintain a running max as a list of `(checkpoint, max_so_far)` pairs. Then each query is a binary search within that timestamp's list.

```python
from collections import defaultdict
import bisect

class PriceTracker:
    def __init__(self, entries):
        self.checkpoints = defaultdict(list)  # ts -> list of (checkpoint_idx, running_max)
        running = {}
        for i, (ts, price) in enumerate(entries):
            if ts not in running:
                running[ts] = price
            else:
                running[ts] = max(running[ts], price)
            self.checkpoints[ts].append((i, running[ts]))

    def query(self, target_ts, checkpoint):
        if target_ts not in self.checkpoints:
            return None
        cps = self.checkpoints[target_ts]
        # Binary search for the rightmost checkpoint <= query checkpoint
        idx = bisect.bisect_right(cps, (checkpoint, float('inf'))) - 1
        if idx < 0:
            return None
        return cps[idx][1]
```

**Time:** O(n) preprocessing, O(log n) per query. **Space:** O(n) — stores one checkpoint entry per original entry.

**Correctness:** The running max invariant ensures that after processing entry i, `running[ts]` holds the maximum price for timestamp `ts` among entries 0..i. The binary search finds the latest checkpoint ≤ k for the target timestamp, which by the invariant gives the correct answer.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force: for each query, scan the entire list and track the max price for the target timestamp. That's O(n) per query, which is fine if queries are rare but wasteful if you're asked repeatedly.

**Step 1 — Sort to make timestamps contiguous.** If timestamps are sorted, all entries for a given timestamp sit next to each other. You can binary search to find the range and then take the max within that range. Sorting costs O(n log n) once, and each query becomes O(log n + m) where m is the number of entries at that timestamp. But you can do better for the base question — a hash map keyed by timestamp gives O(1) query time with O(n) preprocessing. The tradeoff is memory vs. query speed; in an interview, mention both and ask which matters more.

**Step 2 — Handle duplicates.** Multiple entries for the same timestamp mean you can't just store a single price per timestamp. You need to either store a list and take the max, or update the max as you build the map. The latter is cleaner: `price_map[ts] = max(price_map.get(ts, float('-inf')), price)`.

**Step 3 — The checkpoint twist.** A checkpoint is essentially a prefix of the input sequence. The naive approach is to re-scan from the start up to the checkpoint for each query — O(k) per query. The bottleneck is that you're repeating work across queries. The natural fix is to precompute something that lets you answer prefix queries quickly.

**Step 4 — Precompute running maxima per timestamp.** As you process entries in order, maintain a running max for each timestamp. Store a list of `(checkpoint_index, running_max)` pairs for each timestamp. Now a query `(ts, k)` is just a binary search in `ts`'s list for the rightmost checkpoint ≤ k. This drops query time to O(log n) with O(n) preprocessing. The key decision is recognizing that checkpoint queries are monotonic — the max only increases as the checkpoint increases — which is exactly what makes binary search work.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Clarify the query pattern before coding** — if you'll be asked many queries, preprocessing pays off; if it's a one-shot, a simple scan is fine. Interviewers want to see you think about tradeoffs.
- **Mention both the hash map and sorting approaches for the base question** — the hash map gives O(1) queries but uses O(n) space; sorting gives O(log n) queries with less overhead. Showing you can weigh these earns real points.
- **State the invariant explicitly for the checkpoint version** — "after processing entry i, `running[ts]` is the max price for `ts` among entries 0..i." A clear invariant makes your correctness argument trivial and shows you understand why the code works.
- **Handle the "timestamp not found" case explicitly** — return `None` or raise, but say which and why. Edge cases like this are where candidates silently lose points.
- **For the checkpoint follow-up, recognize the monotonicity** — the running max never decreases as the checkpoint increases. That's what enables binary search, and naming this property shows deeper understanding than just regurgitating code.
- **If the input can be huge, consider offline processing** — sort all queries by checkpoint and process entries once, streaming. This is a common extension interviewers probe for.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if entries arrive as a stream and you can't store them all?** — Think about maintaining a running max per timestamp and discarding old entries when you can prove they'll never be queried again.
- **What if you need to support updates (changing a price at a past timestamp)?** — This breaks the simple prefix-max approach; consider a segment tree or Fenwick tree keyed by checkpoint.
- **What if queries ask for the max price over a time range `[t1, t2]` rather than a single timestamp?** — Sort by timestamp and use a segment tree or sparse table over the sorted array.
- **What if the checkpoint is defined by wall-clock time rather than entry count?** — Entries would need timestamps for their own arrival, and you'd query by "all entries with arrival time ≤ T and commodity timestamp = t."
- **Can you answer checkpoint queries in O(1) with more preprocessing?** — Precompute a 2D structure or use a persistent segment tree over the checkpoint dimension.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
