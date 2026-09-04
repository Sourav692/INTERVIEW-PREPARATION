# Sparse Field Index

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Binary Search, Trees · **Difficulty/Frequency:** Common (6/10)

---

## Problem Statement

Implement a `SparseIndex` that indexes **only** documents where a specific field is present, and supports point lookups and range scans.

```
SparseIndex(fieldName: string)
indexDocument(docId: string, doc: object) -> void   // no-op if field absent
removeDocument(docId: string, doc: object) -> void
lookup(value) -> List<string>                       // exact match, returns docIds
rangeScan(low, high, inclusive: bool) -> List<string>  // returns docIds sorted
```

**Example:**

```python
idx = SparseIndex("age")
idx.indexDocument("u1", {"name": "Alice", "age": 30})
idx.indexDocument("u2", {"name": "Bob"})              # no-op, no "age" field
idx.indexDocument("u3", {"name": "Carol", "age": 25})
idx.indexDocument("u4", {"name": "Dave", "age": 30})

idx.lookup(30)                            # -> ["u1", "u4"]
idx.rangeScan(25, 29, inclusive=True)     # -> ["u3"]
idx.removeDocument("u1", {"name": "Alice", "age": 30})
idx.lookup(30)                            # -> ["u4"]
```

**Constraints:**

- Field values are comparable (integers or strings).
- Up to 10^6 documents.
- `rangeScan` must run in **O(log n + k)** where k is the number of results.

### Follow-up (as posed with the problem)

How would you extend this to a **compound** sparse index on two fields, where a document is indexed only if **both** fields are present?

---

## Study Tools

### Hint 1

You need a data structure that keeps values sorted so range scans can start at the lower bound and walk forward, but you also need to handle multiple docIds per value and support O(1)-ish removal when a document disappears.

### Hint 2

A balanced BST keyed by field value works, where each node holds a secondary structure of docIds. The tricky part is removal: you need to find the right value node and delete only that docId from it.

### Hint 3

Use a `TreeMap` (or sorted map) from value to a `LinkedHashSet` of docIds. Removal requires looking up the value in the document you're removing, then deleting that docId from the set; if the set becomes empty, drop the value key entirely.

---

### Answer

This is a sparse index backed by a balanced binary search tree. Since field values are comparable and we need O(log n + k) range scans, a sorted map from value to a set of docIds gives us everything: `lookup` is a direct map access, `rangeScan` uses the map's sorted iteration, and `removeDocument` needs the document's field value to locate and clean up the entry.

```python
from sortedcontainers import SortedDict


class SparseIndex:
    def __init__(self, fieldName: str):
        self.field = fieldName
        self.index = SortedDict()          # value -> set of docIds

    def indexDocument(self, docId: str, doc: dict) -> None:
        if self.field not in doc:
            return
        value = doc[self.field]
        if value not in self.index:
            self.index[value] = set()
        self.index[value].add(docId)

    def removeDocument(self, docId: str, doc: dict) -> None:
        if self.field not in doc:
            return
        value = doc[self.field]
        if value not in self.index:
            return
        self.index[value].discard(docId)
        if not self.index[value]:
            del self.index[value]

    def lookup(self, value) -> list:
        if value in self.index:
            return sorted(self.index[value])
        return []

    def rangeScan(self, low, high, inclusive: bool) -> list:
        result = []
        if inclusive:
            for value in self.index.irange(low, high):
                result.extend(sorted(self.index[value]))
        else:
            for value in self.index.irange(low, high, inclusive=(False, False)):
                result.extend(sorted(self.index[value]))
        return result
```

**Time:** O(log n + k) for `rangeScan` where k is the number of results — the `irange` iterator finds the lower bound in O(log n) and then walks forward, and sorting each bucket's docIds adds O(k log k) in the worst case if we sort each bucket; if we maintain sorted sets (e.g., `SortedSet`), this becomes O(log n + k). `lookup` is O(log n + m) where m is the number of matches. `indexDocument` and `removeDocument` are O(log n).

**Space:** O(n) — we store each indexed document's docId exactly once, plus the map overhead for distinct values.

**Correctness:** The sparse property is enforced by checking `self.field not in doc` in both `indexDocument` and `removeDocument`. The map keyed by value guarantees that all docIds for a given value are in one bucket, so `lookup` returns exactly the right set. `rangeScan` relies on the sorted order of `SortedDict` to enumerate values in ascending order, and we extend results in that order, so the returned docIds are sorted by value (and within each value, by docId if we sort the bucket). Removal cleans up empty buckets, so the map never contains stale keys.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive approach: a list of `(value, docId)` pairs. `indexDocument` appends in O(1), but `lookup` and `rangeScan` require scanning the entire list in O(n), which is way too slow for 10^6 documents.

The bottleneck is finding the relevant entries without scanning everything. Since values are comparable, we want a sorted structure. A sorted list lets us binary search the lower bound in O(log n), but inserting into the middle is O(n) because we have to shift elements. That's also too slow for repeated indexing.

The decision point: we need O(log n) insertion and O(log n) lower-bound search. That points to a balanced BST. A `SortedDict` (or `TreeMap` in Java, `std::map` in C++) gives us exactly this. Keys are field values, and each key maps to a collection of docIds that share that value.

Now handle the multi-docId-per-value case. A simple list of docIds per value works for `lookup` and `rangeScan`, but `removeDocument` would need to find and remove a docId from the list, which is O(m) where m is the bucket size. Using a set gives O(1) removal. The trade-off: sets don't preserve insertion order, so `lookup` and `rangeScan` need to sort the results if deterministic ordering matters. For the given example, sorting each bucket is fine since k is typically small relative to n.

The `removeDocument` method is where most implementations fail. The document passed to `removeDocument` contains the field value, so we can look it up directly in the map. If we didn't have the document, we'd need a reverse index from docId to value, which is a separate concern. Here, the API gives us the document, so we can find the value, access the bucket, discard the docId, and clean up empty buckets.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **The sparse check in both `indexDocument` and `removeDocument`** — you must check `self.field not in doc` in both methods, otherwise removal of a document that was never indexed will corrupt the index.
- **The choice of secondary structure for docIds** — you should discuss using a set for O(1) removal versus a sorted structure for ordered output, and state the trade-off clearly.
- **The cleanup of empty buckets** — you need to `del self.index[value]` when the set becomes empty, otherwise `rangeScan` will return empty buckets and the index grows unboundedly.
- **The `inclusive` flag handling** — you should show how `irange` with `inclusive=(False, False)` handles exclusive bounds, and explain that the lower bound is found in O(log n).
- **The complexity analysis** — you should derive O(log n + k) by separating the cost of finding the lower bound from the cost of walking through results, and mention that sorting buckets adds a factor if you use unsorted sets.
- **The API design tension** — you should point out that `removeDocument` requires the document's field value, which is why the API passes the full document rather than just the docId; this is a deliberate design choice worth acknowledging.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you handle duplicate `indexDocument` calls for the same `(docId, value)` pair?** — Your set-based approach naturally deduplicates, but you should discuss whether that's the desired semantics.
- **What if `removeDocument` is called with a document that has the field but a different value than what was indexed?** — You'd need to store the original value or maintain a reverse map from docId to value.
- **How would you extend this to a compound sparse index on two fields, where a document is indexed only if both fields are present?** — Use a composite key `(field1_value, field2_value)` as the map key, and check that both fields are present before indexing.
- **How would you support concurrent reads and writes to this index?** — Consider a read-write lock or copy-on-write for the map, and discuss the trade-offs.
- **What if values can be null or missing?** — Decide whether null is a valid indexable value or treated as absent, and document the semantics.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Dependency note:** the official answer imports `sortedcontainers.SortedDict`, a third-party package. The accompanying notebook builds an equivalent sorted map on top of the **standard library's `bisect`**, so it runs with no installation — and documents exactly where the two differ in complexity.
