# DSA Study Guide for Atlassian Prep

This file is the **first thing to read** before working through `Atlassian_Prep/`. It distills the 12 [DSA_Deep_Dive](../DSA_Deep_Dive/README.md) tutorials actually used by these 13 problems down to *only* what's needed to solve them — verified section-by-section against the real solution code, not guessed.

**How to use this:**
1. Read **Part 1 (Primary)** below, topic by topic — that's the complete minimum you need.
2. Ignore **Part 2 (Secondary)** unless you have spare time or want to handle a "how does X work internally" follow-up question.
3. Each Primary entry links to the full tutorial if you want the complete explanation, diagrams, and cheat sheet for that topic.

---

# Part 1 — 🎯 PRIMARY (read this first)

## Hash Tables — [PRIMARY.md](../DSA_Deep_Dive/16_Hash_Tables/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/16_Hash_Tables/README.md)
*Used in: 1, 2, 3, 4, 6, 8, 9, 10, 11, 12*
**Read sections:**
- §5 — Hash Map vs Hash Set
- §6 — Python's `dict`/`set`
- §7 — Where hash tables shine
- §1 — worth a skim for context
- ~~§2–§4~~ — skip (hashing mechanics, collisions, load factor/resizing)

- **Map vs. Set:** reach for `dict` when you need a value attached to a key; reach for `set` when you only need "have I seen this?" membership.
- **Python's toolkit, not the internals:** `dict.get(key, default)`, `collections.defaultdict(int)` / `defaultdict(list)` (auto-creates missing keys), `collections.Counter` (frequency counting + `.most_common()`).
- **The four patterns that actually appear:**
  - **Complement lookup** — "have I seen `target - x` before?" (turns an O(n²) scan into O(n)).
  - **Frequency counting** — `Counter` for tallying occurrences.
  - **Grouping** — `defaultdict(list)` to bucket items by a derived key (e.g. group prices by timestamp, group files by collection).
  - **Memoization** — cache `key -> result` so repeated lookups are O(1) instead of recomputed.
- You never need to know *why* it's O(1) average to write any of these solutions — just that it is.

## Sorting Algorithms — [PRIMARY.md](../DSA_Deep_Dive/17_Sorting_Algorithms/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/17_Sorting_Algorithms/README.md)
*Used in: 1, 4, 6, 7, 10*
**Read sections:**
- §5 — Python's `sorted()`
- §6 — Stability in action (multi-key sorting)
- ~~§1–§4~~ — skip (the lower-bound theory and hand-written insertion/merge/quicksort)

- **Just use `sorted()` / `.sort()`** with a `key=` function and `reverse=True/False`. You never hand-roll a sort in any of these problems.
- **The one property that matters: stability.** Python's sort never reorders elements that compare equal.
- **The multi-key sort trick** (used in Jira CSV Exporter, Ballot Processing, Customer Satisfaction): to sort by several columns with **independent, possibly-mixed** directions, sort once per column — **least significant column first, most significant column last**. Stability carries each earlier pass's ordering through as the tiebreak under the final sort.
  ```python
  step1 = sorted(issues, key=lambda i: i["assignee"], reverse=True)   # least significant, first
  result = sorted(step1, key=lambda i: i["status"])                    # most significant, last
  ```

## Binary Search — [PRIMARY.md](../DSA_Deep_Dive/18_Binary_Search/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/18_Binary_Search/README.md)
*Used in: 4*
**Read sections:**
- §3 — `bisect_left` vs `bisect_right` (the only section you need)
- ~~§1, §2~~ — skip (the halving idea, manual implementation)
- ~~§4~~ — skip (binary search on the answer)

- You only need Python's **`bisect`** module — never the manual `lo`/`hi`/`mid` loop.
- **`bisect_right(a, x) - 1`** = the pattern for "find the latest entry `<= x`" in a sorted list — this is exactly the checkpoint-query trick in *Highest Price*.
  ```python
  idx = bisect.bisect_right(checkpoints, target) - 1
  ```

## Two Pointers & Sliding Window — [PRIMARY.md](../DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md)
*Used in: 7 (and the `max_overlap` sanity-check helper in 13)*
**Read sections:**
- §4 — Event/sweep-line (the only section you need)
- ~~§1~~ — skip (opposite-ends two pointers)
- ~~§2~~ — skip (sliding window)
- ~~§3~~ — skip (fast/slow pointers)

- Only the **event / sweep-line** variant is used — not opposite-ends two pointers, not sliding window, not fast/slow pointers.
- **The pattern:** turn each interval into a `(start, +1)` / `(end, -1)` event pair, sort all events by time, sweep through keeping a running "how many active right now" counter.
  ```python
  events = [(s, 1) for s, e in intervals] + [(e, -1) for s, e in intervals]
  events.sort(key=lambda ev: (ev[0], -ev[1]))   # tie-break controls whether touching counts as overlap
  ```
- The tie-break rule (`-ev[1]` vs `ev[1]`) is what decides whether touching endpoints count as overlapping — get this backwards and your answer for boundary cases flips.

## Greedy Algorithms & Amortized Analysis — [PRIMARY.md](../DSA_Deep_Dive/20_Greedy_Algorithms/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/20_Greedy_Algorithms/README.md)
*Used in: 3, 13*
**Read sections:**
- §1 — the exchange argument (read the concept, skip the coin-change worked example)
- §3 — Interval partitioning
- §4 — Amortized analysis
- ~~§2~~ — skip (interval scheduling — a different problem shape than Tennis Club's)

- **Interval partitioning** (Tennis Club): sort by **start time**, keep a **min-heap of resource-availability times**; reuse the earliest-freeing resource if it's already free, otherwise open a new one. Min resources needed = max simultaneous overlap.
- **The exchange argument**, in one sentence: a greedy choice is provably safe if you can always swap it into *any* optimal solution without making that solution worse. This is the actual justification behind "always reuse the earliest-freeing court."
- **Amortized analysis**, in one sentence: a single call can look expensive, but if the *total* cost across a whole sequence of calls is bounded, the average cost per call is small. This is exactly the justification for Content Popularity Tracker's `max_score` walk-down loop (each score value can only be vacated once, ever — so the walking work sums to O(N) across N calls, not O(N) *per* call).
- You do **not** need the coin-change-fails counterexample or the formal aggregate/accounting proof methods to solve either problem — those are there to deepen understanding, not required.

## Generic (M-ary) Trees — [PRIMARY.md](../DSA_Deep_Dive/01_Generic_Tree/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/01_Generic_Tree/README.md)
*Used in: 2, 8*
**Read sections:**
- §2 — vocabulary (quick skim)
- §3 — children-list representation only (skip the `{id, parent_id}` and first-child/next-sibling parts)
- §4 — DFS pre/post-order (skip BFS)
- §5 — the everyday operations / solve-subtree-then-combine pattern
- ~~§1, §6~~ — skip

- **Representation:** a node holds a value plus a `children` **list** (any number of children) — exactly the `Page`/`Node` classes in both problems.
- **The one traversal that matters here: post-order DFS.** Process every child before combining their results into the current node's own answer.
  ```python
  def solve(node):
      result = own_contribution(node)
      for child in node.children:
          result = combine(result, solve(child))
      return result
  ```
- This "solve each subtree, then combine" shape **is** the entire algorithm behind both `subtreeWordCount` (Confluence Word Count) and `lowest_common_manager` (Company Hierarchy) — everything else in those problems is bookkeeping around this one pattern.
- You do not need BFS on a generic tree, the `{id, parent_id}` flat-reconstruction technique, or the first-child/next-sibling representation for either problem.

## Graph Representation — [PRIMARY.md](../DSA_Deep_Dive/06_Graph_Representation/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/06_Graph_Representation/README.md)
*Used in: 9*
**Read sections:**
- §2 — The adjacency list
- §3 — Head-to-head comparison (just enough to justify "list over matrix")
- ~~§1~~ — skip (adjacency matrix)
- ~~§4~~ — skip (edge list)

- **Adjacency list only** — `dict[node] -> list[neighbors]`. The adjacency matrix and edge-list representations are never used.
- **The one design decision that matters:** Confluence Page Link Graph keeps **both** a forward map (`out_adj`) and a reverse map (`in_adj`) side by side, so `get_inbound` doesn't need an O(V+E) scan — this is a deliberate space-for-speed trade, worth being able to explain out loud.

## Graph Traversal (BFS & DFS) — [PRIMARY.md](../DSA_Deep_Dive/07_Graph_Traversal/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/07_Graph_Traversal/README.md)
*Used in: 9*
**Read sections:**
- §1 — The visited set
- §2 — BFS
- §3 — DFS (needed as the rejected-approach comparison)
- §4 — BFS vs DFS table
- ~~§5~~ — skip (the extended toolbox — components/cycle detection/topo sort/bipartite)

- **The visited set** (or a `parent` map that doubles as one) is what keeps traversal from looping forever on a cyclic graph — non-negotiable.
- **BFS with a parent map** finds a **shortest** path on an unweighted graph, and lets you reconstruct that path by walking `parent` backward from the target. This is `find_path`'s actual implementation.
- **Know the one-line reason BFS beats DFS here:** "BFS explores in order of distance, so the first time it reaches the target is guaranteed shortest; DFS just finds *a* path, with no length guarantee." (The problem's own naive DFS approach exists specifically to make this comparison concrete.)
- You don't need connected-components counting, cycle detection via DFS, topological sort, or bipartite checking for this problem — those are extensions the tutorial covers, not things this problem asks for.

## Heaps & Priority Queues — [PRIMARY.md](../DSA_Deep_Dive/12_Heaps_Priority_Queues/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md)
*Used in: 2, 3, 12, 13*
**Read sections:**
- §1 — brief motivation table (why a heap beats sorted/unsorted arrays)
- §6 — Python's `heapq`, incl. the max-heap negation trick
- §7 — Where heaps shine (just the top-K bounded-heap part)
- ~~§2–§5~~ — skip (heap property internals, manual sift-up/down, O(n) heapify)
- ~~two-heap-median/Dijkstra-Prim part of §7~~ — skip

- **You only ever use `heapq`** — never hand-roll `push`/`pop`/`heapify`. Know the two idioms:
  ```python
  heapq.heappush(h, x); heapq.heappop(h)          # min-heap, built in
  heapq.heappush(h, -x); largest = -heapq.heappop(h)   # max-heap trick: negate in, negate out
  ```
- **The size-bounded min-heap pattern for top-K:** push everything; pop whenever the heap exceeds size K. What survives is the K largest, in O(C log K) instead of sorting everything (O(C log C)). This is the whole algorithm in both Confluence Word Count's `topWords_heap` and File System's `top_collections`.
- **Why a heap does NOT fit Content Popularity Tracker:** `heapq` has no O(log n) way to update or remove an arbitrary entry's priority — a score that changes needs a rebuild or "lazy deletion" (push a new entry, discard the stale one when it surfaces). Knowing *why* a heap is the wrong tool here is as important as knowing when it's the right one.
- You don't need the from-scratch sift-up/sift-down mechanics, `O(n)` heapify, or the two-heap median trick for any of these four problems.

## Tries — [PRIMARY.md](../DSA_Deep_Dive/13_Tries/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/13_Tries/README.md)
*Used in: 5*
**Read sections:**
- §1 — the idea (letters/segments on edges)
- §2 — the node + insert/search/starts_with operations
- §3 — why a trie beats a hash set for prefixes
- ~~§4~~ — skip (radix-tree compression)
- ~~§5~~ — skip (use-case list)

- **The core idea:** a tree keyed by "the next unit of the key" (segments here, not characters) — shared prefixes share nodes, and a flag on a node marks "something terminates here."
- **Why a trie beats a flat dict for this problem:** a hash map (`RouterNaive`'s flat `dict`) gives O(1) exact lookup but has no way to represent "matches any single segment here" (a wildcard) — a trie's per-node branching is what makes that expressible at all. This is the exact reasoning behind Middleware Router's Approach 1 → Approach 2 progression.
- You don't need radix-tree compression or the autocomplete/IP-routing use-case list for this problem.

## Strongly Connected Components — [PRIMARY.md](../DSA_Deep_Dive/15_Strongly_Connected_Components/PRIMARY.md) · [full tutorial](../DSA_Deep_Dive/15_Strongly_Connected_Components/README.md)
*Used in: 9*
**Read sections:**
- §1 — What "strongly connected" means + condensation
- §3 — Tarjan's algorithm
- ~~§2~~ — skip (Kosaraju's algorithm)
- ~~§4~~ — skip (Kosaraju vs Tarjan comparison)

- **What an SCC is:** a maximal group of vertices where every one can reach every other one — that's the literal definition of what `find_cycles` returns (any SCC of size > 1 is a genuine multi-page cycle).
- **Tarjan's algorithm specifically** (not Kosaraju's) is what's implemented: one DFS pass, tracking `disc`/`low` per vertex and a stack of "currently open" vertices; `low[v] == disc[v]` marks the root of a finished SCC, popped off the stack.
- You don't need Kosaraju's two-pass alternative to solve this problem — it's a valid different way to get the same answer, not a prerequisite.

---

# Part 2 — 📚 SECONDARY (skip unless you want depth, or expect a "how does X work internally" follow-up)

### [Hash Tables](../DSA_Deep_Dive/16_Hash_Tables/README.md)
**Skip**
- §2 hash function → index mechanics
- §3 collision resolution (chaining / open addressing)
- §4 load factor & resizing

**Why it's safe to skip:** Python's `dict` does all of this invisibly — no problem asks you to implement or reason about it.

### [Sorting Algorithms](../DSA_Deep_Dive/17_Sorting_Algorithms/README.md)
**Skip**
- §1 comparison-sort lower bound theory
- §2 insertion sort
- §3 merge sort
- §4 quicksort (all hand-written implementations)

**Why it's safe to skip:** Every problem calls `sorted()` directly; nobody implements a sort algorithm from scratch.

### [Binary Search](../DSA_Deep_Dive/18_Binary_Search/README.md)
**Skip**
- §1 the halving idea (already intuitive)
- §2 manual `lo` / `hi` / `mid` implementation
- §4 binary search on the answer

**Why it's safe to skip:** `bisect` is used directly; none of these problems are "search on the answer" style.

### [Two Pointers & Sliding Window](../DSA_Deep_Dive/19_Two_Pointers_Sliding_Window/README.md)
**Skip**
- §1 opposite-ends two pointers
- §2 sliding window
- §3 fast/slow pointers

**Why it's safe to skip:** None of the 13 problems use these three variants — only sweep-line (§4) appears.

### [Greedy & Amortized Analysis](../DSA_Deep_Dive/20_Greedy_Algorithms/README.md)
**Skip**
- §1's coin-change counterexample specifics
- §2 interval scheduling (max non-overlapping — a different problem shape than Tennis Club's partitioning)
- formal aggregate / accounting proof methods

**Why it's safe to skip:** Useful context, not required to write or justify either solution.

### [Generic Trees](../DSA_Deep_Dive/01_Generic_Tree/README.md)
**Skip**
- §3's `{id, parent_id}` flat reconstruction
- first-child / next-sibling representation
- BFS on a generic tree
- §6 real-world examples

**Why it's safe to skip:** Both tree problems get objects directly (no flat-row reconstruction) and use DFS only, never BFS.

### [Tree Traversal](../DSA_Deep_Dive/04_Tree_Traversal/README.md) — skip the entire tutorial
**Skip**
- the entire tutorial (in-order traversal, pre+in-order reconstruction, Morris traversal)

**Why it's safe to skip:** This topic is binary-tree-specific. Both Atlassian tree problems use **generic M-ary trees** with no left/right distinction, so none of it applies. Use `01_Generic_Tree` §4–5 instead.

### [Graph Representation](../DSA_Deep_Dive/06_Graph_Representation/README.md)
**Skip**
- §1 adjacency matrix
- §4 edge list

**Why it's safe to skip:** Confluence Page Link Graph only ever uses an adjacency list.

### [Graph Traversal](../DSA_Deep_Dive/07_Graph_Traversal/README.md)
**Skip**
- §5 connected components
- §5 cycle detection
- §5 topological sort
- §5 bipartite check

**Why it's safe to skip:** None of these are asked for — only BFS shortest-path and the visited-set idea are used.

### [Heaps & Priority Queues](../DSA_Deep_Dive/12_Heaps_Priority_Queues/README.md)
**Skip**
- §3 manual sift-up
- §4 manual sift-down
- §5 O(n) heapify from an array
- two-heap median
- Dijkstra / Prim

**Why it's safe to skip:** Every problem uses `heapq` directly; nobody builds a heap by hand or needs the median / shortest-path use cases.

### [Tries](../DSA_Deep_Dive/13_Tries/README.md)
**Skip**
- §4 radix-tree compression
- §5 autocomplete / IP-routing / spell-check examples

**Why it's safe to skip:** Middleware Router needs the core insert/branch idea only, not compression or the broader use-case list.

### [Strongly Connected Components](../DSA_Deep_Dive/15_Strongly_Connected_Components/README.md)
**Skip**
- §2 Kosaraju's algorithm
- §4 Kosaraju-vs-Tarjan comparison

**Why it's safe to skip:** The problem implements Tarjan's; Kosaraju's is a valid alternative, not a prerequisite.
