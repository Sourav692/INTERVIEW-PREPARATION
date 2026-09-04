# Inverted Index

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Hash Tables, Strings · **Difficulty/Frequency:** Popular! (10/10)

---

## Problem Statement

Implement an `InvertedIndex` data structure with the following methods:

```
insert("Coffee is good")
insert("I am at a coffee shop")
search("coffee")  -> "I am at a coffee shop", "Coffee is good"
delete("Coffee is good")
search("coffee")  -> "I am at a coffee shop"
advancedSearch(["coffee", "shop"...], "AND") -> "I am at a coffee shop"
advancedSearch(["coffee", "shop"...], "OR")  -> "I am at a coffee shop", "Coffee is good"
```

---

## Study Tools

### Hint 1

The core idea is a map from each token to the set of documents that contain it. Think about what you need to store per document so you can support `delete` without rescanning everything.

### Hint 2

For `advancedSearch`, the key is to intersect or union sets of document IDs. If you store documents as integer IDs and keep a mapping from ID to the original string, set operations become the whole problem.

### Hint 3

Normalize tokens to lowercase before indexing and searching. For AND, start with the smallest posting list and intersect with the rest; for OR, union all posting lists, then map the resulting IDs back to their document strings.

---

### Answer

This is a classic inverted index problem. The core data structure is a hash map from token to a set of document IDs, plus a map from document ID back to the original string for retrieval. For `advancedSearch`, you do set intersection for AND and set union for OR on the posting lists, then convert the surviving IDs back to strings.

```python
from collections import defaultdict


class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(set)   # token -> set of doc_ids
        self.docs = {}                  # doc_id -> original string
        self.next_id = 0

    def _tokenize(self, text):
        return text.lower().split()

    def insert(self, doc):
        doc_id = self.next_id
        self.next_id += 1
        self.docs[doc_id] = doc
        for token in self._tokenize(doc):
            self.index[token].add(doc_id)
        return doc_id

    def delete(self, doc):
        # Find the doc_id by matching the original string
        doc_id = None
        for did, text in self.docs.items():
            if text == doc:
                doc_id = did
                break
        if doc_id is None:
            return
        # Remove doc_id from every token's posting list
        for token in self._tokenize(doc):
            if doc_id in self.index[token]:
                self.index[token].discard(doc_id)
            # Clean up empty posting lists
            if not self.index[token]:
                del self.index[token]
        del self.docs[doc_id]

    def search(self, query):
        token = query.lower().strip()
        if token not in self.index:
            return []
        return [self.docs[did] for did in sorted(self.index[token])]

    def advancedSearch(self, tokens, operator):
        tokens = [t.lower() for t in tokens]
        if not tokens:
            return []
        if operator == "AND":
            # Start with the smallest posting list
            tokens.sort(key=lambda t: len(self.index.get(t, set())))
            result = set(self.index.get(tokens[0], set()))
            for token in tokens[1:]:
                result &= self.index.get(token, set())
                if not result:
                    break
        elif operator == "OR":
            result = set()
            for token in tokens:
                result |= self.index.get(token, set())
        else:
            raise ValueError(f"Unsupported operator: {operator}")
        return [self.docs[did] for did in sorted(result)]
```

**Time:** O(L) for `insert` where L is the number of tokens in the document; O(1) average for `search` (hash lookup plus output size); O(L) for `delete`; O(S × min_len) for AND where S is the number of search tokens and min_len is the smallest posting list size; O(S × max_len) for OR.

**Space:** O(N × L_avg) where N is the number of documents and L_avg is the average tokens per document, since each token occurrence is stored once in the index.

**Correctness argument:** The invariant is that after every operation, `index[token]` contains exactly the set of `doc_id`s for documents currently containing `token`. `insert` adds the new `doc_id` to each token's set, maintaining the invariant. `delete` removes the `doc_id` from each token's set and cleans up empty sets, restoring the invariant. `search` relies on the invariant to return exactly the matching documents. For `advancedSearch` with AND, the intersection of posting lists contains exactly the `doc_id`s that appear in all token sets, which by the invariant are exactly the documents containing all tokens. Starting with the smallest list is a performance optimization that doesn't change the result. For OR, the union contains exactly the `doc_id`s appearing in at least one token set.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive approach: store documents in a list and on each search, scan every document and check if it contains the query token. That's O(N × L) per search, which is fine for a handful of docs but collapses as N grows. The bottleneck is the linear scan.

Flip it around. Instead of scanning documents to find a token, precompute the mapping from token to documents. That's the inverted index. When you insert a doc, you tokenize it and add the doc's ID to the set for each token. Now `search` is a hash lookup plus returning the stored docs, O(1) plus output size.

For `delete`, you need to know which doc ID to remove. The example deletes by string, so you scan `self.docs` to find the matching ID — O(N) in the worst case. You could optimize by keeping a reverse map from string to ID, but for an interview, the linear scan is acceptable unless the interviewer pushes. Once you have the ID, you remove it from every token's posting list and drop the doc from `self.docs`.

For `advancedSearch`, recognize that AND is set intersection and OR is set union on posting lists. For AND, a key optimization is to process tokens in order of increasing posting list size — intersecting the smallest sets first minimizes the number of comparisons. For OR, just union everything. Finally, map the surviving doc IDs back to strings and return them sorted by ID for deterministic order.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Lowercase normalization in `_tokenize`** — you handle "Coffee" and "coffee" as the same token, which the example demonstrates. Mention that real systems also strip punctuation and handle stemming.
- **Storing doc IDs, not strings, in the index** — this makes set operations cheap and lets you return the original string via a separate `self.docs` map. If you store strings directly in posting lists, you lose the ability to do efficient intersections.
- **Cleaning up empty posting lists on delete** — if you don't remove empty sets from `self.index`, your index accumulates garbage and `search` on a deleted token returns a non-empty result.
- **Sorting the output by doc ID** — the example expects a deterministic order. Returning a set's arbitrary iteration order will fail tests. Sorting by ID gives you insertion order for free.
- **Starting AND with the smallest posting list** — this is the classic IR optimization. If one token appears in only 2 docs and another in 10,000, intersecting the small set first saves thousands of comparisons. Interviewers look for this.
- **Handling the empty `tokens` list in `advancedSearch`** — an empty AND is vacuously true (all docs) and an empty OR is false (no docs), but most interviewers accept returning an empty list. Say what you're doing and why.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if documents can be inserted with duplicate text? How would you handle duplicate inserts?**
- **How would you support phrase search, like searching for "coffee shop" as an exact phrase?** — think about storing token positions per document.
- **How would you rank search results by relevance, like TF-IDF or BM25?** — you'd need term frequencies per document.
- **How would you make this thread-safe for concurrent inserts and deletes?** — think about locking granularity on individual posting lists.
- **How would you support prefix search, like searching for `"coff*"`?** — consider a trie over tokens pointing into the index.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.
