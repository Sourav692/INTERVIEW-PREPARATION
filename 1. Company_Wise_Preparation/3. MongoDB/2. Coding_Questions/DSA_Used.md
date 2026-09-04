# Data Structures & Algorithms Used

A quick-reference index of which data structures and algorithms each MongoDB coding problem exercises, linked to the matching [DSA_Deep_Dive](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/README.md) tutorial for a from-scratch refresher.

> 🎯 **Short on time?** Read [`DSA_Study_Guide.md`](DSA_Study_Guide.md) first — it distils the tutorials linked below down to only what these 27 problems actually need.

> **Note on paths:** the Deep Dive lives at `5. Data_Structure and Algorithms/DSA_Deep_Dive/`, so links from here go up three levels. (The equivalent file in `4. Atlassian/` uses `../DSA_Deep_Dive/`, which resolves to a folder that does not exist — those links are broken.)

| # | Problem | Data Structures | Algorithms / Techniques |
|---|---|---|---|
| 1 | [Inverted Index](<1. Inverted_Index/README.md>) | [Hash map / hash set](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) (posting lists) | Index inversion, set intersection/union, smallest-first AND ordering |
| 2 | [Iterators](<2. Iterators/README.md>) | [Min-heap](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md), one-element buffer | k-way merge, [two pointers](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md), lazy evaluation |
| 3 | [Persistent Append-Only Log](<3. Persistent_Append_Only_Log/README.md>) | On-disk array, [hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) (offset index) | Length-prefix framing, `fsync` durability, log compaction, tombstones |
| 4 | [Connection Pool](<4. Connection_Pool/README.md>) | Stack (LIFO), semaphore | Lock granularity, object pooling, permit accounting |
| 5 | [Intersection](<5. Intersection/README.md>) | [Hash set](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md), `Counter` | Set intersection, [two pointers](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md) on sorted input |
| 6 | [K-Way Merge](<6. K_Way_Merge/README.md>) | [Min-heap](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md), linked list | k-way merge, divide & conquer, dummy-head splicing |
| 7 | [Deep Key Search in Nested JSON](<7. Deep_Key_Search_Nested_JSON/README.md>) | Tree (JSON), explicit stack | [Pre-order DFS](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/04_Tree_Traversal/README.md), sentinel values, early exit |
| 8 | [Sparse Field Index](<8. Sparse_Field_Index/README.md>) | Sorted array + [hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) buckets | [Binary search](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/18_Binary_Search/README.md) lower/upper bound, range scan, compound keys |
| 9 | [Broadcast Message Bus](<9. Broadcast_Message_Bus/README.md>) | [Hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) of tuples, ring buffer (`deque`) | Copy-on-write snapshot iteration, lazy cursors, durable replay |
| 10 | [LRU Cache](<10. LRU_Cache/README.md>) | [Hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) + doubly linked list | O(1) relinking, sentinel nodes, eviction policy |
| 11 | [Task Scheduler](<11. Task_Scheduler/README.md>) | [Directed graph](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/06_Graph_Representation/README.md) (forward + reverse), `deque`, heap | [Topological sort (Kahn's)](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/10_Topological_Sort/README.md), [cycle detection](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/11_Cycle_Detection/README.md), parallel waves |
| 12 | [Linked Hash Map](<12. Linked_Hash_Map/README.md>) | [Hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) + doubly linked list | Insertion vs. access ordering, sentinel nodes |
| 13 | [Lowest Common Ancestor](<13. Lowest_Common_Ancestor/README.md>) | [Binary tree](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/02_Binary_Tree/README.md) with parent pointers | Align-then-walk, [DFS](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/04_Tree_Traversal/README.md) (no-parent variant), linked-list intersection |
| 14 | [Path Resolving](<14. Path_Resolving/README.md>) | Tree (JSON), explicit stack | Fan-out recursion, wildcard matching |
| 15 | [Random Dice Roll](<15. Random_Dice_Roll/README.md>) | `deque` (bounded history) | Input validation, structural parsing, keep-highest selection |
| 16 | [Read/Write Lock](<16. Read_Write_Lock/README.md>) | Counters, condition variables | Readers-writer exclusion, fairness policy, starvation analysis |
| 17 | [Regex Checking](<17. Regex_Checking/README.md>) | Memo table / rolling DP array | Recursive backtracking, **memoisation**, bottom-up DP |
| 18 | [Retry Strategy](<18. Retry_Strategy/README.md>) | — (pure functions) | Strategy pattern, exponential/Fibonacci backoff, jitter |
| 19 | [Scores Finding](<19. Scores_Finding/README.md>) | [Hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md), size-k [min-heap](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md) | Group-by-max aggregation, top-K without a full sort, lazy deletion |
| 20 | [Smallest Numbers](<20. Smallest_Numbers/README.md>) | Sorted array | [Binary search](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/18_Binary_Search/README.md) — `bisect_left` / `bisect_right` |
| 21 | [SnapID](<21. SnapID/README.md>) | [Hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) of per-key histories | Delta storage (MVCC), tombstones, [binary search](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/18_Binary_Search/README.md) over time |
| 22 | [Billing System](<22. Billing_System/README.md>) | Prefix-sum array, Fenwick tree | Prefix sums, range clamping, piecewise-linear cost |
| 23 | [Friends Recommendation](<23. Friends_Recommendation/README.md>) | [Graph](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/06_Graph_Representation/README.md) (adjacency list), [hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) | Two-hop [traversal](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/07_Graph_Traversal/README.md), mutual-friend counting, Adamic–Adar weighting |
| 24 | [Hash Map](<24. Hash_Map/README.md>) | [Hash table](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) with separate chaining | Load factor, amortised doubling, lock striping |
| 25 | [Hash Table (TTL)](<25. Hash_Table/README.md>) | [Hash map](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) + [min-heap](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md) | Lazy deletion, version counters, monotonic clocks |
| 26 | [Integers Squaring](<26. Integers_Squaring/README.md>) | Sorted array | [Two pointers](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md) from the ends, valley property |
| 27 | [Integers Window](<27. Integers_Window/README.md>) | `deque` (monotonic), running aggregate | [Sliding window](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md), invertible aggregates |

## Cross-cutting patterns

- **Hash maps** appear in 15 of the 27 problems (1, 3, 5, 7, 8, 9, 10, 11, 12, 19, 21, 23, 24, 25, plus incidentally elsewhere) — almost always for O(1) grouping or lookup. If you study one topic, study this.
- **Heaps** appear 5 times (2, 6, 19, 25, and the priority variant of 11) — three as k-way merge, two as "find the extreme of a changing set".
- **Map + a second ordering structure** is the single most repeated *composition* in the bank: LRU cache (10), linked hash map (12), sparse field index (8), TTL table (25), SnapID (21). Learn it once and five problems collapse.
- **Concurrency** appears 5 times (4, 9, 16, 24, 25) and always turns on the same question: *how little can you hold the lock for?*
- **Binary search** appears 4 times (8, 20, 21, and inside 25) — but only ever as a **lower bound** (`bisect_left`), never as an exact-match search.
- **Lazy deletion** appears 3 times (19, 21, 25) — always because a heap cannot be edited in place.
- **Sentinel values** (a private object for "not found") matter in 4 problems (7, 21, 24, 25) and are a documented bug in two of the official answers.

## By data structure

| Data structure | Deep Dive tutorial | Used in problems |
|---|---|---|
| Hash map / hash set | [16 — Hash Tables](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/16_Hash_Tables/README.md) | 1, 3, 5, 7, 8, 9, 10, 11, 12, 19, 21, 23, 24, 25 |
| Heap (priority queue) | [12 — Heaps & Priority Queues](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md) | 2, 6, 11, 19, 25 |
| Doubly linked list | [02 — Binary Tree](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/02_Binary_Tree/README.md) *(pointer mechanics; no dedicated linked-list tutorial)* | 6, 10, 12 |
| `deque` / ring buffer | [19 — Two Pointers & Sliding Window](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md) | 9, 11, 15, 27 |
| Tree (JSON / binary) | [02 — Binary Tree](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/02_Binary_Tree/README.md) · [04 — Tree Traversal](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/04_Tree_Traversal/README.md) | 7, 13, 14 |
| Graph (adjacency list) | [06 — Graph Representation](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/06_Graph_Representation/README.md) | 11, 23 |
| Sorted array | [17 — Sorting](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/17_Sorting_Algorithms/README.md) · [18 — Binary Search](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/18_Binary_Search/README.md) | 5, 8, 20, 26 |
| Prefix-sum array / Fenwick tree | *(not covered in DSA_Deep_Dive)* | 22 |
| Locks, semaphores, conditions | *(not covered in DSA_Deep_Dive — OS/concurrency territory)* | 4, 9, 16, 24, 25 |

## By technique

| Technique | Deep Dive tutorial | Used in problems |
|---|---|---|
| Binary search (lower bound) | [18 — Binary Search](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/18_Binary_Search/README.md) | 8, 20, 21, 25 |
| Two pointers / sliding window | [19 — Two Pointers & Sliding Window](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md) | 2, 5, 26, 27 |
| DFS (tree / JSON) | [04 — Tree Traversal](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/04_Tree_Traversal/README.md) | 7, 13, 14 |
| Graph traversal (2-hop, BFS-like) | [07 — Graph Traversal](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/07_Graph_Traversal/README.md) | 23 |
| Topological sort + cycle detection | [10 — Topological Sort](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/10_Topological_Sort/README.md) · [11 — Cycle Detection](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/11_Cycle_Detection/README.md) | 11 |
| k-way merge | [12 — Heaps & Priority Queues](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md) | 2, 6 |
| Top-K without a full sort | [12 — Heaps & Priority Queues](../../../5.%20Data_Structure%20and%20Algorithms/DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md) | 19 |
| Memoisation / dynamic programming | *(no dedicated DP track in DSA_Deep_Dive)* | 17 |
| Prefix sums | *(not covered)* | 22 |
| Concurrency (locks, semaphores, CoW) | *(not covered)* | 4, 9, 16, 24, 25 |
| Durability & log-structured storage | *(not covered)* | 3, 21 |
| Design patterns (strategy, object pool) | *(not covered)* | 4, 18 |

## What this bank tests that a pure DSA track does not

Nearly half these problems are **systems** questions wearing algorithm clothing — which fits MongoDB as a database company. `DSA_Deep_Dive` will not prepare you for:

- **Durability semantics** (3) — `write` versus `fsync`, and what survives a crash.
- **Concurrency design** (4, 9, 16, 24, 25) — lock granularity, fairness, snapshot iteration.
- **MVCC / versioned storage** (21) — deltas, tombstones, pruning.
- **Index design** (1, 8) — sparse indexes, compound keys, the prefix rule.
- **Production API concerns** (15, 18, 22) — validation, retry policy, idempotency, money in floats.

These are covered in the problem notebooks themselves rather than by any tutorial linked above.
