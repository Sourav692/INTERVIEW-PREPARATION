# Sparse Field Index — Explained Simply

## The Problem

Build the thing a database calls an **index**: given a field name like `"age"`, let people ask

- "which documents have `age == 30`?" (a **point lookup**), and
- "which documents have `age` between 25 and 29?" (a **range scan**)

...fast. And **only index documents that actually have that field** — that's the "sparse" part.

```python
idx = SparseIndex("age")
idx.index_document("u1", {"name": "Alice", "age": 30})
idx.index_document("u2", {"name": "Bob"})              # no age -> ignored entirely
idx.index_document("u3", {"name": "Carol", "age": 25})
idx.index_document("u4", {"name": "Dave", "age": 30})

idx.lookup(30)                          # -> ["u1", "u4"]
idx.range_scan(25, 29, inclusive=True)  # -> ["u3"]
```

The hard requirement: `range_scan` must run in **O(log n + k)** — where `k` is how many results you get back.

## What "Sparse" Means, and Why It Exists

Bob has no `age` field. A **sparse** index simply leaves him out — he isn't in the index at all, not even as a null entry.

Why does this matter? In a document database, most documents don't have most fields. A collection of a million users might have `age` on only ten thousand of them. A **dense** index would store a million entries, 990,000 of which say "no value here" — wasting space to record absences that nobody can ever query.

MongoDB has this exact option: `createIndex({age: 1}, {sparse: true})`.

## Why the Obvious Way Is Slow

The obvious approach: keep a list of `(value, docId)` pairs and scan it.

```
entries = [(30,"u1"), (25,"u3"), (30,"u4")]

range_scan(25, 29):  look at every pair, keep the ones in range
```

Correct. But with a million documents, answering "who is aged 25 to 29?" means **reading a million entries to return maybe three**.

That's O(n) per query. The requirement says O(log n + k). Those are very different promises.

## Reading the Requirement: O(log n + k)

This is worth unpacking, because it's really **two separate costs**:

| Part | What it is |
|---|---|
| `log n` | **Finding where the range starts** — a binary search |
| `k` | **Reading out the k answers** — you have to at least touch each one |

And notice what's **missing**: there's no plain `n`. The cost doesn't depend on how big your index is. Whether you have a thousand documents or a billion, a query returning three results does roughly the same amount of work.

> **The promise: query cost tracks the size of the *answer*, not the size of the *index*.**

## An Analogy First: A Phone Book vs. a Shoebox

Imagine you need everyone whose surname starts with "Mc".

**The shoebox** (the naive list): a thousand loose slips of paper in no order. To find the "Mc" ones, you must look at **every single slip**. Even to find three of them.

**The phone book** (the sorted index): names in alphabetical order. You:

1. **Flip to roughly the right place** — a few flips, halving the remaining pages each time. That's the `log n`.
2. **Read forward** through the "Mc" entries. That's the `k`.
3. **Stop the moment you hit "Me"** — because it's sorted, the first non-match means there are no more. Ever.

That last point is the one people miss. **Sortedness is what lets you stop early.** In the shoebox you can never stop, because the next slip might be a "Mc".

## The Design: Two Structures, Working Together

The solution keeps **two things** in step:

```
buckets = { 25: {"u3"},  30: {"u1", "u4"} }     # a plain dict -> instant exact lookup
keys    = [ 25, 30 ]                            # the same keys, kept SORTED -> ranges
```

Why both?

- A **hash map** answers *"is it exactly 30?"* instantly — but it has no idea what comes after 30.
- A **sorted array** answers *"what's between 25 and 29?"* — but finding an exact value in it takes a binary search rather than one hop.

The two questions need two structures. That's not redundancy; it's the API asking for both.

### Why buckets and not single values?

Two people are aged 30. So a value maps to a **set** of document ids, not one id. Databases call this a *posting list*.

Using a **set** (not a list) buys two things: removing a docId is instant, and re-indexing the same document twice can't create a duplicate.

## Step-by-Step Example (Narrated)

Start empty: `buckets = {}`, `keys = []`.

---

**`index_document("u1", {"name": "Alice", "age": 30})`**

Does the document have `age`? **Yes**, it's 30.

Bucket 30 doesn't exist yet, so create it — and because a new value appeared, insert it into the sorted key array.

```
buckets = {30: {"u1"}}
keys    = [30]
```

---

**`index_document("u2", {"name": "Bob"})`**

Does Bob have `age`? **No.**

**Return immediately.** Nothing is stored. Bob doesn't exist as far as this index is concerned. *This is the entire sparse rule, and it's one line.*

```
buckets = {30: {"u1"}}        (unchanged)
keys    = [30]
```

---

**`index_document("u3", {"name": "Carol", "age": 25})`**

New value 25. Create the bucket, and insert 25 into `keys` **in sorted position** — before 30, not appended at the end.

```
buckets = {25: {"u3"}, 30: {"u1"}}
keys    = [25, 30]
```

---

**`index_document("u4", {"name": "Dave", "age": 30})`**

Value 30 **already has a bucket**. Just add Dave to it. `keys` doesn't change — 30 is already there.

```
buckets = {25: {"u3"}, 30: {"u1", "u4"}}
keys    = [25, 30]
```

---

**`lookup(30)`** → one dict hop → `{"u1", "u4"}` → sorted → **`["u1", "u4"]`** ✅

---

**`range_scan(25, 29, inclusive=True)`**

1. **Binary search** `keys` for where 25 begins → position 0.
2. Read `keys[0]` = 25. Is `25 > 29`? No → in range. Add its bucket: `["u3"]`.
3. Read `keys[1]` = 30. Is `30 > 29`? **Yes → stop.**

**Result: `["u3"]`** ✅

We looked at **two** keys. Not a thousand. And we stopped confidently, because sorted order guarantees everything after 30 is bigger still.

---

**`remove_document("u1", {"name": "Alice", "age": 30})`**

Find bucket 30, discard `"u1"`:

```
buckets = {25: {"u3"}, 30: {"u4"}}
```

Bucket 30 still has Dave, so it stays. `lookup(30)` → **`["u4"]`** ✅

## The Bug Everyone Writes: Leaving Empty Buckets

Now remove Dave too. Bucket 30 becomes **empty**.

If you stop there, you're left with:

```
buckets = {25: {"u3"}, 30: set()}       # <-- a dead key
keys    = [25, 30]                      # <-- and it's still in the sorted array
```

Three things now go wrong:

1. **The index grows forever.** Delete a million documents and you keep a million empty buckets.
2. **`range_scan` walks over dead keys**, doing work for nothing.
3. **`30 in buckets` starts lying** — the key "exists" but no document has that value.

**The fix** is two lines: when a bucket empties, delete the key from *both* structures.

> **The invariant to state out loud:** *a value appears as a key **if and only if** at least one live document has that value.*

Say that sentence in an interview and then check each method against it. That's what a correctness argument looks like, and it's exactly what catches this bug.

## The Subtle Bug: `remove_document` Trusts You Too Much

Look at the API again:

```
remove_document(doc_id, doc)
```

It takes the **document** because it needs to read `doc["age"]` to know which bucket to clean. Fine — until the document has been **updated**:

```
index_document("x1", {"age": 30})       # stored in bucket 30
# ...someone changes the user's age to 31...
remove_document("x1", {"age": 31})      # looks in bucket 31. Finds nothing. Silently does nothing.
```

Now `x1` is stuck in bucket 30 **forever**, and `lookup(30)` keeps returning a document that no longer matches. No error, no warning.

**The fix** is to make the index remember what it actually stored:

```
indexed_value = { "x1": 30 }        # doc_id -> the value WE recorded
```

Now removal consults its own record instead of trusting the caller. It costs one extra dict entry per document — and it also lets you remove by id alone, and implement a proper `update_document`.

> **The general lesson:** if correctness depends on the caller handing back exactly what they gave you earlier, **keep your own copy**. That's a whole class of silent corruption, avoided for O(n) space.

## The Follow-Up: Compound Indexes

*"Index on two fields, only if both are present."*

The change is small: make the key a **tuple**.

```
buckets = { (30, "NY"): {"p2"},  (30, "SF"): {"p1"} }
keys    = [ (25,"SF"), (30,"NY"), (30,"SF") ]
```

Two things fall out for free:

**Tuples sort lexicographically** — `(30,"NY") < (30,"SF") < (31,"AK")` — so all the binary search code works unchanged, no custom comparator needed.

**The prefix rule.** A compound index on `(age, city)` can answer:

- ✅ queries on `age` alone (all the `(30, ...)` entries sit together)
- ✅ queries on `age` **and** `city`
- ❌ queries on `city` alone — entries with `city == "SF"` are scattered all through the ordering

This is the real prefix rule in MongoDB and every SQL database, and it's why the **order of fields** in a compound index is a design decision, not an arbitrary one.

And sparseness gets stricter: missing **either** field means the document isn't indexed at all.

## Why It's Fast

The notebook benchmark runs 2,000 narrow range scans against an index that doubles in size:

| Documents | Full scan | Binary search + walk |
|---|---|---|
| 1,000 | 87 ms | 4.4 ms |
| 2,000 | 172 ms | 3.8 ms |
| 4,000 | 334 ms | 4.4 ms |
| 8,000 | 675 ms | 5.4 ms |

The scan **doubles** every time. The index **barely moves** — because `log n` only grew from 10 to 13 across that entire range, and `k` never changed.

By 8,000 documents it's already **125× faster**, and the gap keeps widening.

## A Note on What Real Databases Do

The sorted array here is honest about one weakness: **inserting into the middle of an array shifts everything after it** — that's O(n), even though *finding* the spot was O(log n).

Real databases use a **B-tree** instead. Two reasons:

1. It gets O(log n) inserts as well as O(log n) searches.
2. More importantly, a B-tree node holds **hundreds** of keys, so one node fits in one disk page. That turns `log₂ n` disk reads into `log₂₅₆ n` — and when data lives on disk, the number of *page fetches* is the only cost that matters.

That's the whole reason database indexes are B-trees rather than binary trees.

## Common Mistakes

- **Forgetting the sparse check in `remove_document`.** It's needed in *both* methods. Without it, removing a document that has no field raises `KeyError`.
- **Leaving empty buckets behind.** Memory leak, wasted scanning, and a membership test that lies.
- **Using a list instead of a set for the bucket.** Removal becomes a linear scan, and double-indexing creates duplicates.
- **Testing `inclusive` inside the loop.** Handle the boundary once, when picking `bisect_left` vs `bisect_right` — not per element.
- **Not stopping early.** If you walk past the end of the range "just to be safe", you've thrown away the whole point of sorting.
- **Appending to `keys` instead of inserting in sorted position.** The array must stay sorted or the binary search silently returns wrong answers.
- **Letting `None` into a mixed-type key array.** In Python 3, `None < 5` raises `TypeError` and your `bisect` blows up. Decide your null policy and enforce it at the door.

## The Takeaway

> An index is a **second, differently-ordered copy** of your data — stored by the thing you query on rather than by id. **Sorted order** is what makes ranges cheap: binary-search to the start, walk forward, and stop at the first miss. And "sparse" just means *don't bother recording the absences*.

The same shape appears everywhere: the [Inverted Index](../1.%20Inverted_Index/README.md) next door does it for words, a database B-tree does it for columns, and the index at the back of a book has been doing it for centuries.
