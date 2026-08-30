# File System — Explained Simply

## The Problem

Files can be tagged with collections. Report the **top N** collections by total file size.

```
files:
  file1.txt (100)              -- untagged
  file2.txt (200) in "collection1"
  file3.txt (200) in "collection1"
  file4.txt (300) in "collection2"

collection1 -> 400, collection2 -> 300
top 2 -> ["collection1", "collection2"]
```

## Why the Obvious Way Is Slow

The obvious approach: tally every collection's total size (unavoidable — you need to touch every file at least once), then **sort every single collection** by size and take the first N.

```
sizes = tally_by_collection(files)
top_n = sorted(sizes.items(), key=lambda x: -x[1])[:n]   # sorts ALL collections
```

If there are thousands of collections but you only want the top 5, you're doing a full O(C log C) sort just to throw away almost all of the result — sorting is more work than the question actually requires.

## The Simple Trick: Keep Only N Candidates at a Time, Not All of Them

You don't need every collection ranked — you only need to know the **top N**. A min-heap capped at size N does exactly that: push every candidate in, and the instant the heap grows past size N, kick out the smallest one. By the end, whatever's left in the heap is guaranteed to be the N largest — without ever fully sorting the whole set.

## An Analogy First: A Talent Show With Only 3 Finalist Slots

Imagine judging a talent show where only the top 3 acts advance to the finals, but acts perform one at a time and you must decide on the spot. You keep a shortlist of 3 "current finalists." When a new act performs, you compare it only to the **weakest** current finalist. If the new act beats them, the weakest finalist is bumped out and the new act takes their spot. If not, the new act is dismissed immediately.

By the end of the show, your shortlist of 3 is guaranteed to be the actual top 3 — even though you never ranked every single act against every other act. You only ever compared newcomers against the *current weakest* finalist.

## Step-by-Step Example (Narrated)

Collection sizes: `collection1: 400, collection2: 300, collection3: 150` (imagine a 3rd collection for a fuller example). We want the top **2**.

We use a **min-heap** (smallest on top) capped at size 2 — think of it as "the weakest of my current shortlist is always right at the front, easy to check."

---

**See `collection1` (400).** Heap is empty → push it. Heap: `[400]`. Size (1) is not over the cap (2) — nothing to evict.

---

**See `collection2` (300).** Push it. Heap: `[300, 400]` (min-heap keeps 300 on top, since it's smaller). Size (2) is not over the cap — nothing to evict yet. Both are still "in the running."

---

**See `collection3` (150).** Push it. Heap now has 3 items: `{150, 300, 400}`. Size (3) **is** over the cap (2) → pop the smallest, which is `150`. Heap: `[300, 400]`.

`collection3` (150) got evicted immediately — it never had a chance once the shortlist was full and it was the weakest.

---

No more collections to process. Sort just the 2 survivors descending: **`["collection1" (400), "collection2" (300)]`** — matches the expected top-2.

### The one detail that's easy to miss: you compare against the *heap's current minimum*, not against every existing entry

When `collection3` (150) arrived, we didn't compare it to `collection1` and `collection2` individually — we just pushed it in and let the heap's own structure surface the new minimum (150) to the top, then popped whatever that minimum turned out to be. The heap does the "who's currently weakest?" bookkeeping for you in O(log N) instead of a manual scan.

## Plain-English Walkthrough

1. Tally every file's size into its collection(s) — one pass, unavoidable.
2. Maintain a min-heap that's never allowed to hold more than N entries.
3. For each collection's total, push it onto the heap.
4. If the heap now has more than N entries, pop the smallest one — it can never end up in the final top-N no matter what shows up later, because at least N other entries are already proven to be at least as large.
5. Whatever remains in the heap at the end, sorted descending, is your answer.

## Simple Python Code

```python
import heapq
from collections import defaultdict

def top_collections(files, n):
    sizes = defaultdict(int)
    for f in files:
        for c in f.get("collectionIds", []):
            sizes[c] += f["size"]

    heap = []
    for name, size in sizes.items():
        heapq.heappush(heap, (size, name))
        if len(heap) > n:
            heapq.heappop(heap)          # evict the current weakest

    top = sorted(heap, reverse=True)
    return [name for size, name in top]

files = [
    {"size": 100},
    {"size": 200, "collectionIds": ["collection1"]},
    {"size": 200, "collectionIds": ["collection1"]},
    {"size": 300, "collectionIds": ["collection2"]},
]
print(top_collections(files, 2))   # ['collection1', 'collection2']
```

## Why Is This Faster Than Sorting Everything, If We Still Sort at the End?

We only sort **N** items at the very end (a cheap, fixed-size operation), not all **C** collections. The heap maintenance during the main loop costs O(log N) per push — and crucially, that N is usually much smaller than C. Compare: sorting everything is O(C log C); this approach is O(C log N) for the loop plus O(N log N) for the tiny final sort. When N is small and C is large, that's a real, measurable win.

## Complexity

- **Time:** O(F) to tally file sizes (F = number of files), O(C log N) to maintain the bounded heap (C = number of distinct collections), O(N log N) for the final sort.
- **Space:** O(C) for the tally map (you must compute every collection's exact size), O(N) for the heap.

## The Reusable Pattern

This is the **"size-bounded heap for top-K"** pattern — reach for it any time a problem asks for the top/bottom K out of a much larger set:
- Top K Frequent Elements
- Kth Largest Element in a Stream (the same heap, just maintained incrementally as new elements arrive)
- "Top N trending topics" type dashboards

Core idea: you never need to know the *exact rank* of anything outside the top K — a heap capped at size K throws away non-contenders as soon as they're proven not to matter, so you never pay to sort what you'd immediately discard anyway.
