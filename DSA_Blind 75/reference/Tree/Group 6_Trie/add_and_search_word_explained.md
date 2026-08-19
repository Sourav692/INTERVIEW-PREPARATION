# Add and Search Word (211) — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/add_and_search_word.ipynb`  
> **LeetCode:** https://leetcode.com/problems/design-add-and-search-words-data-structure/  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| Trie (prefix tree) | Words stored letter-by-letter; shared prefixes share paths |
| Wildcard `.` | Matches any single letter — branch to **all** children at that trie node |
| DFS on trie | Recursive `dfs(node, index)` walks the pattern; dots trigger multi-branch search |
| Naive fallback | List of words + character-by-character compare — simple but `O(N·L)` per search |

**Canonical data used in this doc** (from notebook asserts):

```
Words inserted: "bad", "dad", "mad"
```

Trie after all three inserts (each node is a dict `{letter: child}`; `$` marks word-end):

```
root
 ├── b → a → d [$]     (bad)
 ├── d → a → d [$]     (dad)
 └── m → a → d [$]     (mad)
```

Expected search results:

| Query | Result | Why |
|-------|--------|-----|
| `search("bad")` | `True` | Exact path exists |
| `search("pad")` | `False` | No `p` child at root |
| `search(".ad")` | `True` | `.` matches `b`, `d`, or `m` → all end in `ad` |
| `search("b..")` | `True` | `b` → `.` matches `a` → `.` matches `d` → word end |
| `search("b.x")` | `False` | After `b`, no letter child gives `x` at position 2 |

---

## `WordDictNaive` — list + pattern match (naive)

### What it does

Stores every word in a Python list. On `search`, scans all words of equal length and checks each character, treating `.` as “matches anything.” Correct but slow when many words exist.

### Code

```python
class WordDictNaive:
    """Naive: keep all words in a list and match each on search (slow for many words)."""
    def __init__(self):
        self.words = []
    def addWord(self, word: str) -> None:
        self.words.append(word)
    def search(self, word: str) -> bool:
        for w in self.words:               # compare against every stored word of equal length
            if len(w) == len(word) and all(a == "." or a == b for a, b in zip(word, w)):
                return True                # '.' matches any single character
        return False
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `self.words = []` | Empty list holds every inserted word |
| `addWord` → `append` | No structure — just push the string |
| `for w in self.words` | Every search walks the full list |
| `len(w) == len(word)` | Wildcards don't change length — skip mismatched lengths early |
| `zip(word, w)` | Pair query char with stored char at same index |
| `a == "." or a == b` | Dot always matches; otherwise chars must be equal |
| `all(...)` | Every position must match for this candidate word |
| `return False` | No stored word matched |

### Step-by-step trace — `search(".ad")`

**Words in list:** `["bad", "dad", "mad"]`  
**Query:** `.ad` (length 3)

| Iter | Candidate `w` | Length check | Char pairs `(query, w)` | `all(...)` | Return? |
|------|-----------------|--------------|-------------------------|------------|---------|
| 1 | `bad` | 3 == 3 ✓ | `(. , b)` ` (a,a)` `(d,d)` | `.` matches `b` ✓ | **True** |

Search stops at first match. (Would also match `dad` and `mad` if we continued.)

### Step-by-step trace — `search("b.x")`

| Iter | Candidate `w` | Char pairs | Result |
|------|-----------------|------------|--------|
| 1 | `bad` | `(b,b)` `(.,a)` `(x,d)` | `x != d` → fail |
| 2 | `dad` | `(b,d)` | `b != d` → fail |
| 3 | `mad` | `(b,m)` | `b != m` → fail |

**Final output:** `False` ✓

### Mental model

- Think “filter the list”: length filter first, then a zip-and-compare loop.
- Dots are local — they only affect one position in the comparison, not branching.

### Complexity

- **Time:** `addWord` `O(1)` amortized append; `search` `O(N·L)` — `N` words, `L` = query length
- **Space:** `O(total letters)` — all words stored verbatim

---

## `WordDictionary` — trie + wildcard DFS (optimal)

### What it does

Stores words in a trie. Plain letters follow one child; a `.` triggers DFS into every letter-child (skipping the `$` end marker). Exact searches are `O(L)`; dots add branching only where they appear.

### Code

```python
class WordDictionary:
    """Trie-based: exact letters follow one path; a '.' branches into all children."""
    def __init__(self):
        self.root = {}                     # {letter: child_node}
    def addWord(self, word: str) -> None:
        node = self.root
        for c in word:
            node = node.setdefault(c, {})  # build the letter path
        node["$"] = True                   # mark the end of a word
    def search(self, word: str) -> bool:
        def dfs(node, i):
            if i == len(word):
                return "$" in node         # consumed the word -> is it a complete word here?
            c = word[i]
            if c == ".":                   # wildcard: any child could match this position
                return any(dfs(child, i + 1) for k, child in node.items() if k != "$")
            if c not in node:
                return False               # this exact letter isn't present
            return dfs(node[c], i + 1)     # follow the matching letter
        return dfs(self.root, 0)
```

### Line by line — `addWord`

| Line / code | What it does |
|-------------|--------------|
| `node = self.root` | Start at the trie root (empty dict) |
| `for c in word` | Walk one character at a time |
| `node.setdefault(c, {})` | If letter child missing, create `{}`; move into that child |
| `node["$"] = True` | After last letter, mark this node as a complete word |

### Line by line — `search` / `dfs`

| Line / code | What it does |
|-------------|--------------|
| `dfs(node, i)` | `node` = current trie position; `i` = index in query string |
| `i == len(word)` | All query chars consumed — success only if we're at a word-end |
| `"$" in node` | End marker present → a full word ends here |
| `c == "."` | Wildcard: try every **letter** child (not `$`) |
| `k != "$"` | Skip the end marker — it's not a letter branch |
| `any(dfs(child, i+1) ...)` | If **any** child path completes the rest, return True |
| `c not in node` | Exact letter missing → dead end |
| `dfs(node[c], i+1)` | Follow the single matching child |

### Step-by-step trace — `addWord("bad")`

| Step | `c` | Action | Trie path (conceptual) |
|------|-----|--------|------------------------|
| start | — | `node = root` | `root` |
| 1 | `b` | create/follow `b` | `root['b']` |
| 2 | `a` | create/follow `a` | `root['b']['a']` |
| 3 | `d` | create/follow `d` | `root['b']['a']['d']` |
| end | — | `node['$'] = True` | word `bad` marked |

After all three `addWord` calls, trie matches the overview diagram.

### Step-by-step trace — `search("bad")` (exact, no dots)

| Step | `i` | `c` | `node` (keys) | Action | Result |
|------|-----|-----|---------------|--------|--------|
| 1 | 0 | `b` | root: `b,d,m` | follow `b` | recurse |
| 2 | 1 | `a` | `b`: `a` | follow `a` | recurse |
| 3 | 2 | `d` | `a`: `d` | follow `d` | recurse |
| 4 | 3 | — | `d`: `$` | `i == len` → `"$" in node` | **True** |

**Final output:** `True` ✓

### Step-by-step trace — `search(".ad")` (wildcard at start)

At `i=0`, `c='.'`, `node=root` with children `b`, `d`, `m`:

| Branch | Child | `dfs(child, 1)` — query suffix `ad` |
|--------|-------|-------------------------------------|
| 1 | `b` → `a` → `d` | `i=1` `a` ✓ → `i=2` `d` ✓ → `i=3` `$` ✓ | **True** |
| 2 | `d` → `a` → `d` | same pattern for `dad` | **True** |
| 3 | `m` → `a` → `d` | same pattern for `mad` | **True** |

`any(...)` → **True** on first successful branch (`bad`).

**Final output:** `True` ✓

### Step-by-step trace — `search("b..")` (two wildcards)

| Step | `i` | `c` | Current node | Action |
|------|-----|-----|--------------|--------|
| 1 | 0 | `b` | root | follow `b` only |
| 2 | 1 | `.` | `b` → child `a` | wildcard: only child `a` |
| 3 | 2 | `.` | `a` → child `d` | wildcard: only child `d` |
| 4 | 3 | — | `d` has `$` | `i == len(3)` → `"$" in node` |

**Final output:** `True` ✓ (matches `bad`)

Note: at each `.`, we skip `$` and only recurse into letter keys. The second `.` at index 2 enters child `d`, then index 3 checks word-end.

### Step-by-step trace — `search("b.x")` (fails)

| Step | `i` | `c` | Action |
|------|-----|-----|--------|
| 1 | 0 | `b` | follow `b` |
| 2 | 1 | `.` | wildcard → try child `a` only |
| 3 | 2 | `x` | `x not in node` (`a` only has `d`) | **False** |

**Final output:** `False` ✓

### Mental model

- **Letters = single lane:** one child, one recursive call — same as normal trie lookup.
- **Dot = fork:** “every letter child might be right” — small DFS only at dot positions.
- **Base case = index + end marker:** consumed all query chars? Must be standing on a `$` node, not just a prefix.

### Common confusions

- **Iterating `$` at a dot:** `if k != "$"` prevents treating the end marker as a letter branch (would consume a dot without advancing a real character).
- **`b..` vs word length:** three characters in the query means `i` runs `0,1,2`; success check happens at `i == 3` (past last char).
- **Prefix vs full word:** `"$" in node` at the end ensures `search("ba")` on trie with only `bad` returns False.

### Complexity

- **Time:** `addWord` `O(L)`; `search` `O(L)` with no dots; with dots `O(L · branching)` worst case up to `O(26^L)` if every level branches
- **Space:** `O(total letters)` for trie nodes + `O(L)` recursion stack

---

## Quick reference

| Class / method | Technique | `search("bad")` | `search(".ad")` | `search("b.x")` |
|----------------|-----------|-----------------|-----------------|-----------------|
| `WordDictNaive.search` | List scan + zip | `True` | `True` | `False` |
| `WordDictionary.search` | Trie + DFS at `.` | `True` | `True` | `False` |

| Operation | Naive | Trie |
|-----------|-------|------|
| `addWord` | `O(1)` | `O(L)` |
| `search` (exact) | `O(N·L)` | `O(L)` |
| `search` (with `.`) | `O(N·L)` | `O(L · branches)` |

## Patterns to remember

- **Trie + DFS for wildcards:** dot = branch all letter-children; exact char = single path.
- **Signal:** dictionary with `.` wildcard, “match pattern in word list.”
- **Related:** Implement Trie (208), Word Search II (212), Regular Expression Matching.
- **Pitfall:** forgetting `k != "$"` in the wildcard loop; forgetting end-marker check when query is fully consumed.
