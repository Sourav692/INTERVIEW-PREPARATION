# Implement Trie (Prefix Tree) (208) — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/implement_trie_prefix_tree.ipynb`  
> **LeetCode:** https://leetcode.com/problems/implement-trie-prefix-tree/  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| Trie | Tree of characters — shared prefixes share the same path from root |
| End marker `$` | Distinguishes a **complete word** from a mere prefix node |
| `search` vs `startsWith` | `search` needs `$` at end; `startsWith` only needs the path to exist |
| Set naive | `word in set` is fast for exact match; `startswith` scans every word |

**Canonical sequence** (from notebook asserts):

```
1. insert("apple")
2. search("apple")   -> True
3. search("app")      -> False   (prefix exists but not a stored word)
4. startsWith("app")  -> True
5. insert("app")
6. search("app")      -> True
7. startsWith("apx")  -> False
```

Trie after `insert("apple")` only:

```
root
 └── a → p → p → l → e [$]     (apple)
```

Trie after also `insert("app")`:

```
root
 └── a → p → [$]              (app)
      └── l → e [$]           (apple)
```

---

## `TrieSetNaive` — set of words (naive prefix)

### What it does

Stores words in a Python `set`. Exact `search` is `O(1)` hash lookup, but `startsWith` must scan every word — `O(N·L)`.

### Code

```python
class TrieSetNaive:
    """A naive dictionary: exact search is fast, but prefix search scans every word."""
    def __init__(self):
        self.words = set()                 # just store all inserted words
    def insert(self, word: str) -> None:
        self.words.add(word)
    def search(self, word: str) -> bool:
        return word in self.words          # O(1) exact lookup
    def startsWith(self, prefix: str) -> bool:
        return any(w.startswith(prefix) for w in self.words)  # must scan EVERY word (slow)
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `self.words = set()` | Hash set of complete words |
| `insert` → `add` | Store the whole string |
| `search` → `in` | Membership test — no prefix logic |
| `startswith(prefix)` per word | Python string prefix check on each stored word |
| `any(...)` | True if at least one word begins with `prefix` |

### Step-by-step trace — notebook sequence on naive trie

After `insert("apple")`:

| Call | Action | Result |
|------|--------|--------|
| `search("apple")` | `"apple" in set` | **True** |
| `search("app")` | `"app" in set` | **False** |
| `startsWith("app")` | scan: `"apple".startswith("app")` | **True** |

After `insert("app")`:

| Call | Result |
|------|--------|
| `search("app")` | **True** |
| `startsWith("apx")` | no word starts with `apx` | **False** |

### Mental model

- Two different questions: “is this exact string stored?” vs “does any stored string **begin** this way?”
- A set answers the first instantly; the second requires reading (or comparing) every word.

### Complexity

- **Time:** `insert` / `search` `O(L)`; `startsWith` `O(N·L)`
- **Space:** `O(total letters)`

---

## `Trie` — prefix tree (optimal)

### What it does

Nested dicts form a trie. `insert` walks/creates the path; `_walk` follows a string; `search` requires `$` at the end node; `startsWith` only needs `_walk` to succeed.

### Code

```python
class Trie:
    """A prefix tree: words share their common starting path, letter by letter."""
    def __init__(self):
        self.root = {}                     # each node is a dict: {letter: child_node}
    def insert(self, word: str) -> None:
        node = self.root
        for c in word:
            node = node.setdefault(c, {})  # follow the letter path, creating nodes as needed
        node["$"] = True                   # mark that a complete word ends here
    def search(self, word: str) -> bool:
        node = self._walk(word)            # walk the exact letters
        return node is not None and "$" in node   # word exists only if it's marked as an end
    def startsWith(self, prefix: str) -> bool:
        return self._walk(prefix) is not None      # some word has this prefix if the path exists
    def _walk(self, s):                    # follow the path for string s; None if it breaks
        node = self.root
        for c in s:
            if c not in node:
                return None                # no such path -> not present
            node = node[c]
        return node
```

### Line by line — `insert`

| Line / code | What it does |
|-------------|--------------|
| `node = self.root` | Start at root dict |
| `for c in word` | One character per trie level |
| `setdefault(c, {})` | Create missing child; descend into it |
| `node["$"] = True` | Mark terminal node after last character |

### Line by line — `_walk`

| Line / code | What it does |
|-------------|--------------|
| `for c in s` | Follow each char of prefix or full word |
| `c not in node` | Broken path → return `None` |
| `node = node[c]` | Descend |
| `return node` | Return the node **after** walking all chars (may or may not be word-end) |

### Line by line — `search` vs `startsWith`

| Method | Condition | Meaning |
|--------|-----------|---------|
| `search` | `node is not None and "$" in node` | Path exists **and** a complete word ends here |
| `startsWith` | `node is not None` | Path exists — word may continue below |

### Step-by-step trace — `insert("apple")`

| Step | `c` | `node` after | Notes |
|------|-----|--------------|-------|
| start | — | `root` | `{}` |
| 1 | `a` | `root['a']` | created |
| 2 | `p` | `root['a']['p']` | created |
| 3 | `p` | `...['p']` | second `p` level |
| 4 | `l` | `...['l']` | |
| 5 | `e` | `...['e']` | |
| end | — | `node['$'] = True` | `apple` marked |

Trie shape: `root → a → p → p → l → e [$]`

### Step-by-step trace — `search("apple")` after insert

**`_walk("apple")`:**

| Step | `c` | `node` keys before step | Action |
|------|-----|-------------------------|--------|
| 1 | `a` | root: `a` | enter `a` |
| 2 | `p` | `p` | enter `p` |
| 3 | `p` | `p` | enter `p` |
| 4 | `l` | `l` | enter `l` |
| 5 | `e` | `e` | enter `e` |
| end | — | `$` | return node `{ '$': True }` |

`search`: `"$" in node` → **True** ✓

### Step-by-step trace — `search("app")` before second insert

**`_walk("app")`:**

| Step | `c` | Result node after walk |
|------|-----|------------------------|
| 1–3 | `a,p,p` | node at `root['a']['p']['p']` — keys: `l` only (continues to `apple`) |

Node is `{ 'l': {...} }` — **no `$`** → `search` returns **False** ✓

Path `app` exists as prefix, but no word ends at the `p` after `ap`.

### Step-by-step trace — `startsWith("app")` before second insert

Same `_walk("app")` → node is not `None` → **True** ✓

Prefix path exists even though `app` isn't a complete stored word yet.

### Step-by-step trace — `insert("app")` after `apple`

Walk `a → p → p`. At `root['a']['p']['p']` node currently `{ 'l': ... }`:

| Step | Action | Node at `a/p/p` after |
|------|--------|-------------------------|
| walk `a,p,p` | arrive at shared prefix node | `{ 'l': ..., '$': True }` |

Now both `app` (ends here) and `apple` (continues via `l`) share the `app` prefix.

| Call | Result |
|------|--------|
| `search("app")` | `"$" in node` → **True** ✓ |
| `startsWith("apx")` | `_walk`: at `p`, next char `x` missing → **False** ✓ |

### Mental model

- **Trie node = dict of outgoing letters** plus optional `$`.
- **`_walk` = “can I spell this string along existing edges?”** — doesn't care if it's a full word.
- **`search` = `_walk` + “am I standing on a word terminal?”**

### Common confusions

- **Without `$`:** `search("app")` would wrongly return True inside `apple` after walking three letters.
- **Set vs trie for prefixes:** `any(w.startswith(p))` scales with number of words; trie `startsWith` scales with prefix length only.
- **Shared prefixes:** inserting shorter word after longer one adds `$` on an existing node — doesn't duplicate the path.

### Complexity

- **Time:** `insert`, `search`, `startsWith` all `O(L)` where `L` = word or prefix length
- **Space:** `O(total letters)` across all inserted words

---

## Quick reference

| Method | Naive (`TrieSetNaive`) | Trie (`Trie`) |
|--------|------------------------|---------------|
| `insert` | `O(L)` hash store | `O(L)` |
| `search` (exact) | `O(L)` average | `O(L)` |
| `startsWith` | `O(N·L)` scan all words | `O(L)` |

| Question | Check |
|----------|-------|
| Is `word` stored? | `_walk(word)` and `"$" in node` |
| Any word begins with `prefix`? | `_walk(prefix) is not None` |

Notebook assert outcomes:

| Step | Call | Result |
|------|------|--------|
| after `apple` | `search("apple")` | True |
| after `apple` | `search("app")` | False |
| after `apple` | `startsWith("app")` | True |
| after `app` too | `search("app")` | True |
| after `app` too | `startsWith("apx")` | False |

## Patterns to remember

- **Trie for prefix work:** autocomplete, `startsWith`, shared-prefix problems → `O(L)` per query.
- **Signal:** “prefix”, “starts with”, “dictionary of words”, “autocomplete.”
- **Related:** Add and Search Word (211), Word Search II (212), Replace Words.
- **Pitfall:** omitting `$` (prefix mistaken for word); using a set when prefix queries matter.
