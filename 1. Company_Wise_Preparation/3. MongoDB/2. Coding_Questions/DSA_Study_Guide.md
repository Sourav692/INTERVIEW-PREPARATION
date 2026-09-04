# DSA Study Guide for MongoDB Prep

This file is the **first thing to read** before working through the 27 coding problems in this folder. It distils the [DSA_Deep_Dive](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/README.md) tutorials down to *only* what these problems actually use — checked against the real solution code, not guessed.

**How to use this:**

1. Read **Part 1 (Primary)** — that's the complete minimum.
2. Skip **Part 2 (Secondary)** unless you have spare time or want to handle a "how does X work internally" follow-up.
3. Read **Part 3** — it covers the things this bank tests that `DSA_Deep_Dive` doesn't cover at all, and it's nearly half the questions.

---

# Part 1 — 🎯 PRIMARY (read this first)

## Hash Tables — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md)

*Used in: 1, 3, 5, 7, 8, 9, 10, 11, 12, 19, 21, 23, 24, 25 — **more than half the bank***

**Read:** §5 (map vs. set), §6 (Python's `dict`/`set`), §7 (where hash tables shine). Skim §1. Skip §2–§4 unless doing problem 24, which asks you to *build* one.

- **The four patterns that actually appear:**
  - **Grouping** — `defaultdict(list)` / `defaultdict(set)` to bucket items by a derived key. This is problems 1, 8, 19, 21, 23.
  - **Membership** — "have I seen this?" in O(1). Problems 5, 23.
  - **Index** — `key -> position/node/offset`, so a second structure can be reached instantly. Problems 3, 10, 12, 25.
  - **Counting** — `Counter` for tallies. Problems 5, 23.
- **Average O(1), worst-case O(n).** Say both. Problem 24 measures the adversarial case directly.
- You never need to know *why* it's O(1) to solve any of these — except problem 24, where building it is the question.

## Heaps & Priority Queues — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md)

*Used in: 2, 6, 11, 19, 25*

**Read:** the `heapq` API section and the "top-K" pattern. Skip the sift-up/sift-down implementation details.

- **`heapq` is a min-heap over a plain list.** `heappush`, `heappop`, and `heap[0]` to peek.
- **Two patterns, and they cover every use here:**
  - **k-way merge** (2, 6) — seed with one element per source, pop the smallest, push that source's next.
  - **Top-K / find-the-extreme-of-a-changing-set** (19, 25) — a size-k min-heap for the k *largest*, because the item you need at hand is the **weakest survivor** you're about to evict.
- **Always put a tiebreaker in the tuple:** `(key, unique_int, payload)`. Without it, equal keys make Python compare the payloads, which raises `TypeError` for objects. This bites in problems 2, 6 and 25.
- **A heap cannot be updated in place.** When a priority changes, use **lazy deletion**: push the new entry, discard stale ones on pop. Problems 19, 21, 25.

## Binary Search — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/18_Binary_Search/README.md)

*Used in: 8, 20, 21, 25*

**Read:** §3 (`bisect_left` vs `bisect_right`) — genuinely the only section you need. Skip the manual `lo`/`hi`/`mid` loop unless problem 20 asks you to write it out.

- **You only ever need the *lower bound*.** Not "where is x?" but **"where would x go?"** — a question that always has an answer, even when x is absent.
- **`bisect_left(a, x)`** = the first index with `a[i] >= x`. That's it. Every one of these four problems is that call.
- **`bisect_right(a, x) - 1`** = "the last entry `<= x`", which is the *"what was true at time T?"* query in problems 21 and 25.
- **Use the half-open interval** `[left, right)` with `right = len(arr)` — it makes "nothing qualifies" fall out with no special case.

## Two Pointers & Sliding Window — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md)

*Used in: 2, 5, 26, 27*

**Read:** §1 (opposite ends) and §2 (sliding window). Skip §3 (fast/slow) and §4 (sweep-line) — neither appears.

- **Opposite ends** (5, 26) — walk inward from both ends of a sorted array. Problem 26's twist: squaring makes a **valley**, so the extremes are at the ends.
- **Sliding window** (27) — consecutive windows overlap, so *repair* the aggregate rather than rebuilding it.
- **The rule worth memorising:** an aggregate can slide only if its operation has an **inverse**. Sum ✅, product ⚠️ (division fails on zero), min/max ❌ (need a monotonic deque).

## Graphs: Representation, Traversal, Topological Sort

*Used in: 11, 23*

**Read:** [06 — Representation](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/06_Graph_Representation/README.md) (adjacency lists only), [10 — Topological Sort](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/10_Topological_Sort/README.md) (Kahn's algorithm). Skip Dijkstra, MST, and A\* — they do not appear anywhere in this bank.

- **Kahn's algorithm** (11): keep an **in-degree** count per node and a **reverse** adjacency map. Run whatever hits zero; decrement its dependents.
- **Cycle detection is free** with Kahn's — if `executed < total`, whatever is left is in a cycle. No second pass, no colouring.
- **Store both edge directions.** The forward direction expresses the constraint; the reverse is what you traverse when a task completes. That's the difference between O(V²) and O(V+E).
- **Two-hop traversal** (23): "mutual friend" = a path of length 2. Walk out from the node, don't scan the graph.

## Tree Traversal (DFS) — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/04_Tree_Traversal/README.md)

*Used in: 7, 13, 14*

**Read:** the pre-order DFS section. Skip in-order and post-order — neither appears here.

- **Pre-order** (check the node, *then* descend) is what gives you the **shallowest** match, which is what "find this key" almost always means.
- **JSON is a tree**: objects and lists are internal nodes, scalars are leaves. Problems 7 and 14 are both tree walks in disguise.
- **Keep the iterative version in your pocket** — Python's recursion limit is ~1000, and both problems have a "what if it's 10,000 deep?" follow-up. When you swap recursion for a stack, **push children reversed** or the visit order flips.

---

# Part 2 — 📎 SECONDARY (only if you have time)

## Sorting — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/17_Sorting_Algorithms/README.md)

*Used in: 5, 19, 26 — and in all three the point is that you can **avoid** it*

- Just use `sorted()` with a `key=`. You never hand-roll a sort here.
- **The one thing to know:** a **sort key expresses a tie-break once**. `(-count, name)` in problem 19 is descending-by-count then ascending-by-name — write the rule as a key, not as comparison logic in two places.
- Timsort **detects existing runs**, which is why problem 26's benchmark shows the O(n log n) sort beating the O(n) hand-written loop in CPython.

## Binary Trees — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/02_Binary_Tree/README.md)

*Used in: 13*

- Only problem 13, and its key insight isn't tree-shaped at all: **a parent pointer turns the ancestor chain into a linked list**, so LCA becomes "find where two linked lists intersect".

## Cycle Detection — [full tutorial](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/11_Cycle_Detection/README.md)

*Used in: 11*

- Worth a skim only for the DFS three-colour method, as the contrast with Kahn's. Kahn's is the better answer for problem 11 (iterative, free detection, exposes parallelism); DFS wins only when you need to *print* the cycle.

## Not needed at all

`03_Binary_Search_Tree`, `05_Graph_Fundamentals`, `08_Weighted_Shortest_Paths`, `09_Minimum_Spanning_Tree`, `13_Tries`, `14_AStar_Floyd_Warshall`, `15_Strongly_Connected_Components`, `20_Greedy_Algorithms`, `21_Backtracking` — **none of these appear in any of the 27 problems.** (Contrast with the Atlassian set, which does use tries, BFS, Tarjan's and greedy interval partitioning.)

---

# Part 3 — ⚙️ WHAT THE DEEP DIVE DOESN'T COVER

**Roughly half of this bank is systems design wearing algorithm clothing** — unsurprising for a database company. There is no tutorial for any of the following, so the notebooks themselves are the material.

## Concurrency — problems 4, 9, 16, 24, 25

The single recurring question: **how little can you hold the lock for?**

- **Lock vs. semaphore.** A lock answers *"who may touch this?"*; a semaphore answers *"how many may proceed?"*. Reaching for a mutex when the constraint is a *count* leads to hand-rolled bookkeeping and bugs. (Problem 4.)
- **Never hold a lock across slow or unknown work** — I/O, `sleep`, or a user callback. This one rule shapes problems 4, 9 and 16.
- **`while`, not `if`, around `Condition.wait()`.** Spurious wakeups are real. (Problem 16.)
- **Snapshot iteration.** Never walk a collection that the code inside the loop can mutate. In Python the failure is *silent* — it skips elements. (Problem 9.)
- **Fairness is a choice between starvation modes**, not a bug you can remove. (Problem 16.)
- **A `get` that mutates is a writer.** True of the LRU cache (10) and the TTL table (25) — so a readers-writer lock buys nothing there.

## Durability & log-structured storage — problems 3, 21

- **`write` ≠ durable.** Only `fsync` (Java: `force`) reaches the disk.
- **Length-prefix framing** makes a byte stream self-describing.
- **Append-only turns a byte offset into a permanent address** — which is what makes O(1) reads and a small in-memory index possible.
- **Deletion in an immutable store is an append** — a *tombstone* — plus periodic compaction.
- **Store deltas, not states.** One entry per change instead of a full copy: O(n) rather than O(n²). This is MVCC, and it's how PostgreSQL and WiredTiger let readers and writers avoid blocking each other.

## Index design — problems 1, 8

- An index is **a second copy of your data, ordered by what you query on**.
- **Sparse** = skip documents lacking the field (MongoDB's `sparse: true`).
- **Compound indexes obey the prefix rule**: `(a, b)` answers queries on `a`, and on `a`+`b`, but *not* on `b` alone.
- **O(log n + k)** is a promise with *no `n` term*: query cost tracks the size of the **answer**, not the index.

## Production API concerns — problems 15, 18, 22, 25

- **Validate at the boundary; raise at the mistake; catch where you can act.** A library that swallows its own exceptions turns loud bugs into silent wrong answers.
- **`TypeError` for the wrong kind, `ValueError` for the wrong value** — and remember `bool` subclasses `int`.
- **Never use an in-band value for "not found".** `-1`, `0` and `None` are all legitimate data. Use a sentinel object.
- **Inject the clock and the sleep function.** A one-hour TTL becomes a microsecond test, and flakiness disappears.
- **`time.monotonic()`, never `time.time()`, for durations.** Wall clocks jump.
- **Never bill in floating point.** Integer minor units or `Decimal`.
- **Retries assume the failed attempt had no effect** — otherwise you need an idempotency key on the *job*, not a cleverer backoff.

## Design patterns — problems 4, 18

- **Strategy** (18): separate the policy that varies from the loop that doesn't.
- **Object pool** (4): reuse anything whose creation dwarfs its use.
- **Prefer a pure function to remembered state.** Problem 18's Fibonacci backoff *looks* like it needs memory and doesn't — and dropping the state makes it reusable and thread-safe.

---

# The five ideas that recur most

If you internalise nothing else:

1. **Compose a hash map with a second ordering structure.** Map for identity, list/heap/array for order, **sharing the same objects**. Problems 8, 10, 12, 21, 25 are all this.
2. **Precompute once so reads are free.** Inverted index, prefix sums, sparse index, aggregation map. Problems 1, 8, 19, 22.
3. **Sortedness means the answer is at a known place.** The front (k-way merge), an end (squaring), or findable by binary search. Problems 2, 6, 8, 20, 26.
4. **Store the change, not the state.** Deltas, tombstones, running aggregates, in-degree counters. Problems 3, 11, 21, 27.
5. **Never overload a real value as a signal.** `-1`, `0`, `None` are data. Use a sentinel — it's a documented bug in two of the official answers.
