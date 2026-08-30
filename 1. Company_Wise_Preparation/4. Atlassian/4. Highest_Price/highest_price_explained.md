# Highest Price — Explained Simply

## The Problem

Given a list of `(timestamp, price)` entries — unsorted, with possible repeats at the same timestamp — answer: "what's the highest price recorded at timestamp T?"

```
entries = [(1, 100), (2, 150), (1, 120), (3, 90), (2, 200)]
highest_price_at_timestamp(entries, 1)   # -> 120 (max of 100 and 120)
highest_price_at_timestamp(entries, 2)   # -> 200 (max of 150 and 200)
```

## Why the Obvious Way Is Slow

The obvious approach: for every query, scan the whole list and track the max among entries matching the target timestamp.

```
def highest_price_naive(entries, target):
    best = None
    for ts, price in entries:
        if ts == target:
            best = max(best, price) if best is not None else price
    return best
```

This works, but it's O(n) **per query** — if you're asked about the same data 1,000 times, you redo the full O(n) scan 1,000 times, even though the underlying data never changed.

## The Simple Trick: Do the Work Once, Answer Instantly Forever After

Since the data doesn't change between queries, precompute a lookup table once: `timestamp -> highest price seen at that timestamp`. Building it costs one pass; every query after that is a single dictionary lookup.

## An Analogy First: A Filing Cabinet vs. a Pile of Papers

The naive approach is like keeping every receipt in one giant unsorted pile — every time your accountant asks "what's the biggest expense from March?" you have to flip through the entire pile again.

The smart approach is to spend five minutes *once*, sorting every receipt into a labeled folder by month, keeping only the biggest amount seen so far in each folder as you file. After that, "what's March's biggest expense?" is just: open the March folder, read the number. No more flipping through the whole pile, ever again.

## Step-by-Step Example (Narrated)

`entries = [(1, 100), (2, 150), (1, 120), (3, 90), (2, 200)]`

We build the index by walking the entries **once**, left to right, keeping a running max per timestamp.

---

**See `(1, 100)`** — timestamp 1 hasn't been seen. Create its entry directly: `index = {1: 100}`.

---

**See `(2, 150)`** — timestamp 2 hasn't been seen. Create it: `index = {1: 100, 2: 150}`.

---

**See `(1, 120)`** — timestamp 1 already has 100 on file. Is 120 bigger than 100? Yes → update it.
`index = {1: 120, 2: 150}`.

---

**See `(3, 90)`** — timestamp 3 hasn't been seen. Create it: `index = {1: 120, 2: 150, 3: 90}`.

---

**See `(2, 200)`** — timestamp 2 already has 150 on file. Is 200 bigger than 150? Yes → update it.
`index = {1: 120, 2: 150 → 200, 3: 90}` → final: `{1: 120, 2: 200, 3: 90}`.

---

Now every query is instant:
`highest_price_at_timestamp(index, 1)` → look up key `1` → **120** ✅
`highest_price_at_timestamp(index, 2)` → look up key `2` → **200** ✅
`highest_price_at_timestamp(index, 99)` → key `99` isn't there → **None** ✅

### The one detail that's easy to miss: `None` and "missing key" both mean "no data"

A timestamp that was never recorded should return the same thing as a timestamp query that found nothing — use `index.get(target)`, which returns `None` automatically when the key is absent, instead of writing a separate "does this key exist?" check.

## Plain-English Walkthrough

1. Walk through every `(timestamp, price)` entry exactly once.
2. For each timestamp, keep the running maximum price seen so far — either it's the first time you've seen that timestamp (store the price directly) or it's the current max compared against the new price.
3. To answer a query, just look up the timestamp in this table.

## Simple Python Code

```python
def build_price_index(entries):
    index = {}
    for ts, price in entries:
        index[ts] = price if ts not in index else max(index[ts], price)
    return index

def highest_price_at_timestamp(index, target):
    return index.get(target)

entries = [(1, 100), (2, 150), (1, 120), (3, 90), (2, 200)]
index = build_price_index(entries)
print(highest_price_at_timestamp(index, 1))   # 120
print(highest_price_at_timestamp(index, 2))   # 200
print(highest_price_at_timestamp(index, 99))  # None
```

## Why Not Just Sort Instead?

Sorting also works — sort by timestamp so same-timestamp entries sit next to each other, then binary-search or scan for the target's boundaries. It costs O(n log n) once and O(log n + matches) per query. The hash-map index is simpler and gives O(1) per query, at the cost of O(n) extra memory to hold the table — usually the better trade-off unless memory is unusually tight.

## Complexity

- **Time:** O(n) to build the index once; O(1) per query afterward.
- **Space:** O(n) — the index holds one entry per distinct timestamp.

## The Reusable Pattern

This is the **"precompute once, query many times"** pattern — the single most common trick for turning repeated O(n) work into O(1) or O(log n):
- Grouping/indexing by any key before answering many lookups
- Prefix sums (precompute running totals so range-sum queries are O(1))
- Memoization (cache a function's results so repeated calls are instant)

Core idea: if the underlying data won't change between queries, do the expensive work exactly **once**, and let every future question be a cheap lookup against what you already built.
