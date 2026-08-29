# Heaps & Priority Queues — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problems that use heaps (2 — Confluence Word Count, 3 — Content Popularity Tracker, 12 — File System, 13 — Tennis Club).

**Corresponds to README.md sections:**
- §1 — brief motivation table (why a heap beats sorted/unsorted arrays)
- §6 — Python's `heapq`, incl. the max-heap negation trick
- §7 — Where heaps shine (just the top-K bounded-heap part)
- ~~§2–§5~~ — heap property internals, manual sift-up/down, O(n) heapify — not needed here
- ~~the two-heap-median/Dijkstra-Prim part of §7~~ — not needed here — see the full tutorial if you want them

---

- **You only ever use `heapq`** — never hand-roll `push`/`pop`/`heapify`. Know the two idioms:
  ```python
  heapq.heappush(h, x); heapq.heappop(h)          # min-heap, built in
  heapq.heappush(h, -x); largest = -heapq.heappop(h)   # max-heap trick: negate in, negate out
  ```
- **The size-bounded min-heap pattern for top-K:** push everything; pop whenever the heap exceeds size K. What survives is the K largest, in O(C log K) instead of sorting everything (O(C log C)). This is the whole algorithm in both Confluence Word Count's `topWords_heap` and File System's `top_collections`.
- **Why a heap does NOT fit Content Popularity Tracker:** `heapq` has no O(log n) way to update or remove an arbitrary entry's priority — a score that changes needs a rebuild or "lazy deletion" (push a new entry, discard the stale one when it surfaces). Knowing *why* a heap is the wrong tool here is as important as knowing when it's the right one.
- You don't need the from-scratch sift-up/sift-down mechanics, `O(n)` heapify, or the two-heap median trick for any of these four problems.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for heap internals, `O(n)` heapify, and the two-heap median trick.
