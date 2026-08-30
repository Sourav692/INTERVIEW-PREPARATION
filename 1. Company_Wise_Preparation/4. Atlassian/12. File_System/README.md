# File System

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Hash Tables, Sorting, Trees · **Difficulty/Frequency:** Common (5/10)

---

## Problem Statement

Imagine we have a system that stores files, and these files can be grouped into collections. We are interested in knowing where our resources are being taken up. For this system we would like to generate a report that lists:

- The total size of all files stored
- The top N collections (by file size), where N is user-defined

### Example input

```
file1.txt (size: 100)
file2.txt (size: 200) in collection "collection1"
file3.txt (size: 200) in collection "collection1"
file4.txt (size: 300) in collection "collection2"
file5.txt (size: 10)
```

Explanation: Collections behave like tags. Files can be tagged with one or multiple collections.

- "collection1" → 2 files → total size 400
- "collection2" → 1 file → total size 300
- Untagged files → total size 110
- Top 2 collections → `["collection1", "collection2"]`

### Follow-up 1: Every file can belong to multiple collections

```python
{file: "file1.txt", size: 100},
{file: "file2.txt", size: 200, collectionIds: ["collection1"]},
{file: "file3.txt", size: 200, collectionIds: ["collection1"]},
{file: "file4.txt", size: 300, collectionIds: ["collection2", "collection3"]},
{file: "file5.txt", size: 10}
```

### Follow-up 2: One collection can be the child of another collection

```python
{collection: "collection1"},
{collection: "collection2", parentCollectionId: "collection1"},
```

---

## Study Tools

### Hint 1

You need two maps: one to track each file's size and which collections tag it, and another to accumulate the total size per collection. A single pass over the input can build both.

### Hint 2

To get the top N collections without sorting everything, think about a heap. Push `(total_size, collection_name)` pairs and keep only the N largest as you go.

### Hint 3

For the multiple-collections follow-up, when a file has `collectionIds: [...]`, add the file's size to every collection in that list. For the hierarchy follow-up, propagate a child collection's total size up to all its ancestors before ranking.

---

### Answer

This is a map-and-heap problem. Build a `collections` map that accumulates total file size per collection, plus a separate counter for untagged files. Then use a min-heap of size N to extract the top N collections without a full sort.

```python
import heapq
from collections import defaultdict

def top_collections(files, n):
    """
    files: list of dicts like
      {'file': 'file1.txt', 'size': 100}
      {'file': 'file2.txt', 'size': 200, 'collectionIds': ['collection1']}
    n: number of top collections to return
    Returns list of collection names, sorted by total size descending.
    Untagged files are tracked separately and reported as 'untagged'.
    """
    collection_sizes = defaultdict(int)
    untagged_size = 0
    total_size = 0

    for f in files:
        total_size += f['size']
        colls = f.get('collectionIds', [])
        if not colls:
            untagged_size += f['size']
        for c in colls:
            collection_sizes[c] += f['size']

    # Min-heap of (size, name) to keep top N
    heap = []
    for name, size in collection_sizes.items():
        heapq.heappush(heap, (size, name))
        if len(heap) > n:
            heapq.heappop(heap)

    top = sorted(heap, key=lambda x: (-x[0], x[1]))
    return [name for size, name in top]
```

**Time:** O(F + C log N) where F is the number of files, C the number of distinct collections, and N the requested top count — each file touches each of its collections once, and each heap operation is O(log N).

**Space:** O(C + N) — the `collection_sizes` map holds up to C entries, and the heap holds at most N.

**Correctness:** The first loop accumulates the exact total size for every collection because each file contributes its size to every collection in its `collectionIds` list. The heap invariant ensures that after processing all collections, the heap contains the N largest `(size, name)` pairs: whenever a new pair is pushed, if the heap exceeds N, the smallest element (the heap root) is popped, so the N largest remain at the end. Sorting the final heap gives the correct descending order.

For the hierarchy follow-up, after computing `collection_sizes`, build a parent map from the collection definitions and propagate sizes upward:

```python
def propagate_to_ancestors(collection_sizes, parent_map):
    """Add each collection's size to all its ancestors."""
    result = defaultdict(int)
    for name, size in collection_sizes.items():
        curr = name
        while curr is not None:
            result[curr] += size
            curr = parent_map.get(curr)
    return result
```

The rest of the top-N extraction stays the same.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest version: each file has at most one collection. You could brute-force this by iterating over all files for each collection query — that's O(F·C) and clearly too slow for any real file system.

The first improvement is to build a dict mapping collection name to total size in one pass over the files. That's O(F) time and gives you exact totals. For untagged files, you can either track them under a special key like `'untagged'` or keep a separate variable — the problem statement lists them separately, so track them separately.

Now for the top N. A naive approach sorts all collections by size — O(C log C) — which works but does more work than needed when N is small. The bottleneck is sorting entries you'll throw away. A min-heap of size N fixes that: push every `(size, name)` pair, and whenever the heap grows past N, pop the smallest. After one pass, the heap holds exactly the N largest. This is O(C log N), which beats sorting when N << C.

The multiple-collections follow-up is a small change: instead of `f['collectionId']`, you have `f['collectionIds']`, a list. Loop over that list and add the file's size to each. The rest of the algorithm is unchanged.

The hierarchy follow-up is where it gets interesting. You can't just rank the direct collection sizes because a parent's total should include all descendants. Build a `parent_map` from the collection definitions, then for each collection, walk up the parent chain adding its size to every ancestor. This is O(C·H) where H is the max hierarchy depth — fine for tree-like structures. If the hierarchy can be a DAG with shared ancestors, you'd want memoization or a topological sort to avoid double-counting, but the tree case is the standard interpretation.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Mention the heap choice explicitly** — when N is small relative to the number of collections, a min-heap of size N reduces the top-N extraction from O(C log C) to O(C log N). Interviewers listen for this because it shows you understand the tradeoff between sorting and selection.
- **Track untagged files as a separate category** — the problem statement lists them as a distinct line item, and conflating them with a collection called `'untagged'` can cause bugs if a real collection has that name. A separate variable or a sentinel that can't collide with real names is cleaner.
- **Handle the multiple-collections case with a loop over `collectionIds`** — this is a one-line change from the single-collection version, and saying so out loud shows you recognize the problem is the same shape with a list instead of a scalar.
- **For the hierarchy, propagate sizes bottom-up** — walking each collection up to the root is O(C·H) and works for tree hierarchies. If the interviewer pushes on DAGs or deep hierarchies, mention memoization or topological ordering as the next step.
- **Be precise about tie-breaking** — when two collections have the same total size, the problem doesn't specify an order. Sorting the final heap by `(-size, name)` gives deterministic output, and mentioning that you've made a choice here prevents ambiguity.
- **State the total size as a byproduct** — you're already summing every file's size in the first loop, so reporting total storage is free. Pointing that out shows you see the whole problem, not just the top-N part.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the hierarchy is a DAG, not a tree — a collection can have multiple parents?** — Think about how to avoid double-counting when propagating sizes; memoization or a topological sort with dynamic programming.
- **What if files can be added, removed, or re-tagged at runtime?** — Consider maintaining the collection size map incrementally and how the heap would need to be updated on changes.
- **What if the number of files is huge and they don't fit in memory?** — Think about external sorting, streaming aggregation, or a map-reduce style approach where you aggregate per collection and then merge partial top-N results.
- **What if collection names are hierarchical strings like `"a/b/c"` instead of explicit parent pointers?** — Consider parsing the path and how that changes the propagation logic.
- **What if you need to report the top N collections at multiple points in time, like hourly snapshots?** — Think about pre-aggregating into time buckets and whether you can maintain rolling top-N structures.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
