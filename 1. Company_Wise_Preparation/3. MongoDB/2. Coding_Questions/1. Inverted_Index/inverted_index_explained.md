# Inverted Index — Explained Simply

## The Problem

Store a pile of text documents so you can instantly answer "which documents contain the word *coffee*?" — and also handle deletes and multi-word AND/OR queries.

```
insert("Coffee is good")
insert("I am at a coffee shop")
search("coffee")   -> both documents
delete("Coffee is good")
search("coffee")   -> ["I am at a coffee shop"]
```

## Why the Obvious Way Is Slow

The obvious approach: keep the documents in a list, and on every search, read all of them.

```
def search(query):
    return [d for d in docs if query.lower() in d.lower().split()]
```

Correct, but it re-reads **every document, every time**. With 1,000,000 documents and 100 searches, you read a million documents a hundred times over — and the documents never changed between searches.

## The Simple Trick: Flip the Direction of the Map

A document naturally maps *forward*: document → the words in it. But a search hands you a **word** and wants **documents**. You are asking the map to run backwards.

So build the backwards map once, while inserting:

```
"coffee" -> {doc 0, doc 1}
"shop"   -> {doc 1}
"good"   -> {doc 0}
```

That is the whole idea, and it is why it's called an **inverted** index. Now a search is one dictionary lookup — no documents are read at all.

## An Analogy First: The Index at the Back of a Textbook

Suppose you want every page that mentions "photosynthesis".

The naive approach is to open the book at page 1 and read all 900 pages, noting where the word appears. Do that again tomorrow for "mitochondria" and you re-read all 900 pages.

The index at the back of the book is the smart approach. Someone read the book **once** and wrote down, for each term, the pages it appears on:

```
photosynthesis .... 112, 340, 341
mitochondria ...... 88, 401
```

Now any lookup is: flip to the index, read one line, done. You never read the book again. Building the index cost one full pass; every query afterwards is free.

Our `index` dictionary *is* that back-of-book index. Our `docs` dictionary is the book itself — we keep it so we can hand back the actual text once we know which "page numbers" (document ids) matched.

## Step-by-Step Example (Narrated)

Start with two empty dictionaries and a counter:

```
index = {}      # word -> set of doc ids
docs  = {}      # doc id -> original text
next_id = 0
```

---

**`insert("Coffee is good")`** — this document gets id `0`. Store the original text so we can return it later: `docs = {0: "Coffee is good"}`.

Now lowercase and split it into words: `["coffee", "is", "good"]`. Add id `0` to each word's set:

```
index = {"coffee": {0}, "is": {0}, "good": {0}}
```

---

**`insert("I am at a coffee shop")`** — this one gets id `1`. `docs = {0: "Coffee is good", 1: "I am at a coffee shop"}`.

Words: `["i", "am", "at", "a", "coffee", "shop"]`. Add id `1` to each. Note `"coffee"` already exists, so `1` joins the set that already holds `0`:

```
index = {"coffee": {0, 1}, "is": {0}, "good": {0},
         "i": {1}, "am": {1}, "at": {1}, "a": {1}, "shop": {1}}
```

---

**`search("coffee")`** — lowercase the query, look up one key:

`index["coffee"]` → `{0, 1}` → sort → `[0, 1]` → look up the text → **`["Coffee is good", "I am at a coffee shop"]`** ✅

We sort the ids because ids were handed out in increasing order, so sorting them gives insertion order back for free — and makes the output deterministic instead of depending on set iteration order.

---

**`delete("Coffee is good")`** — first find the id whose stored text matches: that's `0`.

Now tokenize the *deleted* document (`["coffee", "is", "good"]`) so we know exactly which posting lists mention it, and remove `0` from each:

- `index["coffee"]`: `{0, 1}` → `{1}` — still has doc 1, keep it
- `index["is"]`: `{0}` → `{}` — now empty → **delete the key entirely**
- `index["good"]`: `{0}` → `{}` — now empty → **delete the key entirely**

Then drop the text: `docs = {1: "I am at a coffee shop"}`.

```
index = {"coffee": {1}, "i": {1}, "am": {1}, "at": {1}, "a": {1}, "shop": {1}}
```

> **Why bother deleting empty keys?** If you leave `"is": {}` behind, the index grows forever with dead words, and code that checks `if token in index` gets a misleading "yes". Cleaning up keeps one simple promise true: *a key exists in the index if and only if some live document contains that word.*

---

**`search("coffee")` again** — `index["coffee"]` → `{1}` → **`["I am at a coffee shop"]`** ✅

## AND and OR Are Just Set Math

Once every word points at a *set* of ids, multi-word queries stop being a search problem and become arithmetic on sets.

With both documents indexed again:

```
index["coffee"] = {0, 1}
index["shop"]   = {1}
```

**AND** — documents containing *all* the words — is set **intersection**:

```
{0, 1} & {1}  =  {1}   ->  ["I am at a coffee shop"]
```

**OR** — documents containing *any* of the words — is set **union**:

```
{0, 1} | {1}  =  {0, 1}  ->  ["Coffee is good", "I am at a coffee shop"]
```

### The one clever bit: intersect the smallest set first

Imagine `"the"` appears in 10,000 documents and `"mongodb"` in 3.

- Start with `"the"`: you begin with a 10,000-element set and then whittle it down.
- Start with `"mongodb"`: you begin with 3 elements, and the answer can never be bigger than 3.

Intersection can only ever **shrink** a result, so starting from the smallest posting list means every step afterwards works on a tiny set. One line of code:

```
tokens.sort(key=lambda t: len(index.get(t, ())))
```

Add the early exit too — the moment the running result becomes empty, nothing can bring documents back, so stop.

## Why It's Fast

| Operation | Naive scan | Inverted index |
|---|---|---|
| `insert` | O(1) | O(L) — L = words in the doc |
| `search` | **O(N × L)** every call | **O(1)** lookup + output |
| `delete` | O(N) | O(N) to find the id, then O(L) |
| `advancedSearch` | O(N × L) | O(sum of posting list sizes) |

The trade is the usual one: do work **once** at write time so read time is nearly free. Search engines make this trade because documents are written once and searched millions of times.

## Common Mistakes

- **Forgetting to lowercase at query time.** You lowercased when indexing, so `search("Coffee")` must lowercase too — otherwise the key isn't found and you return `[]`.
- **Putting document *strings* in the posting lists.** It works for `search`, but intersecting long strings is slow and duplicates the text. Store small integer ids and keep one copy of the text in a side table.
- **Leaving empty posting lists after a delete.** The index leaks memory and `token in index` starts lying to you.
- **Returning a set directly.** Set iteration order is arbitrary, so your output order changes between runs and tests fail intermittently. Sort by id.
- **Not handling an unknown token.** `index["zzz"]` on a `defaultdict` silently *creates* an empty entry — use `.get(token, set())`, or check membership first.

## The Takeaway

> When queries ask "which things contain X?", don't search for X — **precompute the map from X to the things**, and let a dictionary lookup replace the scan. Then boolean queries are just intersection and union on the sets you already built.

This is the same idea behind a database secondary index, a reverse adjacency list in a graph, and the back of every textbook you have ever used.
