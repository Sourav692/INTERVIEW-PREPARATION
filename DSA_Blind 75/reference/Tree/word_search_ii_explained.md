# Word Search II (212) — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/word_search_ii.ipynb`  
> **LeetCode:** https://leetcode.com/problems/word-search-ii/  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| Grid DFS + backtracking | Mark cell used (`#`), explore 4 neighbors, restore cell |
| Trie of all words | One board sweep finds every word; trie prunes dead paths instantly |
| Brute per-word search | Run full grid DFS for each word — re-walks board `W` times |
| Store word at `$` | At word-end node, store the full string; `pop` avoids duplicate reports |

**Canonical input** (from notebook asserts):

```
Board (4×4):
  col: 0   1   2   3
row 0:  o   a   a   n
row 1:  e   t   a   e
row 2:  i   h   k   r
row 3:  i   f   l   v

Words: ["oath", "pea", "eat", "rain"]
Expected output: ["eat", "oath"]  (sorted)
```

Words **found** on board:

| Word | Path (row, col) | Letters |
|------|-----------------|---------|
| `oath` | (0,0)→(0,1)→(1,1)→(2,1) | o → a → t → h |
| `eat` | (1,0)→(1,1)→(1,2) | e → t → a |

Words **not** found:

| Word | Why |
|------|-----|
| `pea` | `p` not on board |
| `rain` | `r` exists but no connected `r-a-i-n` path |

Trie built from all four words:

```
root
 ├── o → a → t → h [$="oath"]
 ├── p → e → a [$="pea"]
 ├── e → a → t [$="eat"]
 └── r → a → i → n [$="rain"]
```

---

## `find_words_brute` — per-word grid DFS (worst)

### What it does

For each word in the list, runs a separate grid DFS from every cell. Correct but repeats board exploration for every word.

### Code

```python
def find_words_brute(board: List[List[str]], words: List[str]) -> List[str]:
    rows, cols = len(board), len(board[0])
    def exists(word):                      # can we spell this one word somewhere on the board?
        def dfs(r, c, i):
            if i == len(word):
                return True                # matched every letter -> found it
            if r < 0 or c < 0 or r >= rows or c >= cols or board[r][c] != word[i]:
                return False               # off the board, or letter doesn't match
            tmp = board[r][c]; board[r][c] = "#"   # mark this cell as used
            found = (dfs(r+1,c,i+1) or dfs(r-1,c,i+1) or
                     dfs(r,c+1,i+1) or dfs(r,c-1,i+1))  # try all 4 neighbors for the next letter
            board[r][c] = tmp              # restore the cell (backtrack)
            return found
        return any(dfs(r, c, 0) for r in range(rows) for c in range(cols))  # try every start
    return [w for w in words if exists(w)]  # re-scans the whole board once per word (slow)
```

### Line by line — inner `dfs(r, c, i)`

| Line / code | What it does |
|-------------|--------------|
| `i == len(word)` | All letters matched — success |
| bounds / `board[r][c] != word[i]` | Reject out-of-grid or wrong letter |
| `tmp = board[r][c]; board[r][c] = "#"` | Mark current cell visited |
| four `dfs` with `i+1` | Try next letter in all 4 directions |
| `board[r][c] = tmp` | **Backtrack** — undo mark so other paths can use cell |
| `any(dfs(r,c,0) ...)` | Try every cell as start for letter 0 |

### Step-by-step trace — `exists("eat")`

**Word:** `eat` — successful path (1,0)→(1,1)→(1,2)

| Step | `(r,c)` | `i` | `word[i]` | Board char | Action |
|------|---------|-----|-----------|------------|--------|
| 1 | (1,0) | 0 | `e` | `e` ✓ | mark `#`, explore neighbors for `t` |
| 2 | (1,1) | 1 | `t` | `t` ✓ | mark, explore for `a` |
| 3 | (1,2) | 2 | `a` | `a` ✓ | mark, explore for end |
| 4 | — | 3 | — | — | `i == len` → **True** |

Backtrack restores cells along the return path.

### Step-by-step trace — `exists("pea")` (fails quickly)

Every start cell: first letter must be `p`. No `p` on board → all 16 starts fail at `i=0`.

**Final:** `pea` not in result list.

### Mental model

- Outer loop: “does **this** word exist?” Inner DFS: standard Word Search I pattern.
- Board is reset (via backtracking) between attempts from different starts; each word search is independent.

### Complexity

- **Time:** `O(W · m · n · 4^L)` — `W` words, board `m×n`, word length `L`
- **Space:** `O(L)` recursion depth

---

## `find_words_trie` — trie + one board sweep (optimal)

### What it does

Builds a trie of all target words. DFS from every cell follows trie edges; dead letters prune immediately. When `$` is found, append the stored word and `pop` it to avoid duplicates.

### Code

```python
def find_words_trie(board: List[List[str]], words: List[str]) -> List[str]:
    root = {}                              # build a trie of all the words
    for w in words:
        node = root
        for c in w:
            node = node.setdefault(c, {})  # walk/create the letter path
        node["$"] = w                      # store the whole word at its end node
    rows, cols = len(board), len(board[0])
    res = []
    def dfs(r, c, node):                   # walk the board, guided by the trie
        if r < 0 or c < 0 or r >= rows or c >= cols:
            return
        ch = board[r][c]
        if ch == "#" or ch not in node:    # used cell, or no word continues with this letter
            return                         # -> dead end, prune immediately
        nxt = node[ch]
        if "$" in nxt:                     # a word ends here
            res.append(nxt.pop("$"))       # collect it (pop so we don't report duplicates)
        board[r][c] = "#"                  # mark used
        dfs(r+1,c,nxt); dfs(r-1,c,nxt); dfs(r,c+1,nxt); dfs(r,c-1,nxt)  # explore neighbors
        board[r][c] = ch                   # restore (backtrack)
    for r in range(rows):                  # one sweep of the board finds ALL words at once
        for c in range(cols):
            dfs(r, c, root)
    return res
```

### Line by line — trie build

| Line / code | What it does |
|-------------|--------------|
| `node["$"] = w` | At word end, store **full word string** (not just `True`) |
| `setdefault(c, {})` | Standard trie insert along letters |

### Line by line — grid `dfs(r, c, node)`

| Line / code | What it does |
|-------------|--------------|
| bounds check | Off board → return |
| `ch == "#"` | Cell already used on current path |
| `ch not in node` | Trie says no target word continues with this letter → **prune** |
| `nxt = node[ch]` | Descend trie one letter |
| `"$" in nxt` | A word ends at this trie node |
| `nxt.pop("$")` | Collect word once; remove marker |
| mark `#` / restore `ch` | Standard backtracking |
| four neighbor `dfs` | Continue with trie node `nxt` |
| outer `for r, for c` | Start DFS from every cell with `node=root` |

### Step-by-step trace — finding `oath` (key steps)

Start: `dfs(0, 0, root)`, board `(0,0)='o'`, `root` has child `o`.

| Step | `(r,c)` | `ch` | Trie `node` keys | Action |
|------|---------|------|------------------|--------|
| 1 | (0,0) | `o` | root: `o,e,p,r` | `nxt = root['o']`, no `$` yet, mark (0,0) |
| 2 | (0,1) | `a` | `o`: `a` | `nxt = o/a`, mark (0,1) |
| 3 | (1,1) | `t` | `a`: `t` | `nxt = o/a/t`, mark (1,1) |
| 4 | (2,1) | `h` | `t`: `h` | `nxt = o/a/t/h`, `"$" in nxt` |
| 5 | — | — | — | `res.append("oath")`, `pop("$")` |
| 6+ | neighbors | — | — | continue/backtrack with restored cells |

**`res` contains `oath`** after step 5.

### Step-by-step trace — finding `eat` (key steps)

From `dfs(1, 0, root)`: `(1,0)='e'` matches trie child `e`.

| Step | `(r,c)` | `ch` | Trie path | Action |
|------|---------|------|-----------|--------|
| 1 | (1,0) | `e` | `root→e` | mark, descend |
| 2 | (1,1) | `t` | `e→t`? wait: `e` child is `a` for eat | need `e` then `a` then `t` |

Correct path for `eat`: (1,0) `e` → (1,1) `t` is wrong letter order.

Trie for `eat`: `e → a → t`. Board path:

| Step | `(r,c)` | `ch` | Trie node after step |
|------|---------|------|----------------------|
| 1 | (1,0) | `e` | at `root['e']` |
| 2 | (1,1) | `t` | `e` has only `a` — **prune** if we go to `t` |

So from (1,0) we must go to a neighbor with `a` for letter 2. Neighbors of (1,0): (2,0)`i`, (0,0)`o`, (1,1)`t`. None is `a` at trie step 2.

Try start (1,2) `a`? Word starts with `e`, not `a`.

Correct path: (1,0)`e` → must reach `a` then `t`. (1,0) neighbors: (1,1) is `t` — that's letter 2 of `eat`, not letter 1.

Re-read eat: e-a-t. (1,0)e → (1,1)t is e-t — wrong.

(1,0)e → (0,1)a? (0,1) adjacent to (1,0)? No — diagonal not allowed.

(1,0)e → (2,0)i — no.

Actually: (1,0)e → (1,1)t → (1,2)a gives e-t-a not e-a-t.

Wait the notebook says eat is found. Path (1,0)→(1,1)→(1,2): letters e, t, a = "eta" not "eat".

Let me check board again:
row 1: e t a e
(1,0)=e, (1,1)=t, (1,2)=a

For "eat" we need e then a then t. 
(1,0)e → (1,2)a? (1,0) and (1,2) are not adjacent (need same row adjacent cols).

(1,0)e → (0,0)o, (2,0)i, (1,1)t only.

Maybe (2,2) or other? 
(0,2)a adjacent to (1,2)a?
(1,2)a adjacent to (1,1)t and (1,3)e and (2,2)k.

Path: (1,2)a → (1,1)t → (1,0)e gives a-t-e.

(0,1)a → (1,1)t → (1,0)e? a-t-e.

(1,3)e → (1,2)a → (1,1)t gives e-a-t = eat! Yes!

Start at (1,3) not (1,0).

| Step | `(r,c)` | `ch` | Trie |
|------|---------|------|------|
| 1 | (1,3) | `e` | root→e |
| 2 | (1,2) | `a` | e→a |
| 3 | (1,1) | `t` | a→t, `$` = eat |
| 4 | — | — | append `eat`, pop `$` |

### Step-by-step trace — pruning `pea` and `rain`

**`pea`:** From any cell, first trie step from `root` needs `p`. No `p` on board → every `dfs(r,c,root)` hits `ch not in node` immediately (or wrong first letter).

**`rain`:** From (2,3)`r`: `ch='r'` matches trie. Next letter `a`: neighbors of (2,3) are (2,2)`k`, (3,3)`v`, (1,3)`e`, (2,2). (1,2)`a` is not adjacent to (2,3). (0,3)`n` — no `a` neighbor. Path dies — trie never reaches `rain`'s `$`.

### Step-by-step trace — backtracking on one cell

At (1,1) during `oath` search:

| Phase | `board[1][1]` | Meaning |
|-------|---------------|---------|
| enter | `t` | original |
| mark | `#` | cell locked for this path |
| explore 4 neighbors | `#` | DFS continues |
| restore | `t` | other paths from other starts can use (1,1) again |

Without restore, a second word path through (1,1) would see `#` and fail.

### Mental model

- **Trie steers DFS:** only move to a neighbor if that letter is a trie child — instant prune.
- **One sweep:** outer loop starts from every cell once; trie encodes **all** words simultaneously.
- **`pop("$")`:** if `app` and `apple` both end along same path, collect each once.

### Common confusions

- **Not restoring cells:** breaks other words that need the same cell on a different path/order.
- **Duplicate results:** use `pop("$")` or a `found` set; otherwise same word reported from multiple starts.
- **`$` as word vs True:** storing the full word string avoids walking back up to reconstruct it.

### Complexity

- **Time:** `O(m · n · 4^L)` one board sweep; trie pruning cuts branches in practice; plus `O(total letters)` to build trie
- **Space:** `O(total letters)` trie + `O(L)` recursion stack

---

## Quick reference

| Function | Strategy | Board passes | Pruning |
|----------|----------|--------------|---------|
| `find_words_brute` | DFS per word | `W` full scans | only letter mismatch |
| `find_words_trie` | Trie + one DFS sweep | 1 (all starts) | trie child missing |

Canonical output:

| Input words | On canonical board | Result |
|-------------|-------------------|--------|
| oath, pea, eat, rain | 4×4 grid above | `["eat", "oath"]` |

Grid DFS template:

```
1. Check bounds / visited / match
2. Mark cell
3. Recurse 4 directions (or trie-guided)
4. Unmark cell (backtrack)
```

Trie-on-grid template:

```
1. Build trie with word at `$`
2. dfs(r, c, trie_node):
   - if out of bounds or visited or char not in node → return
   - descend node = node[char]
   - if `$` in node → collect word, pop `$`
   - mark, dfs 4 neighbors with node, unmark
3. dfs from every (r,c) with root
```

## Patterns to remember

- **Trie + grid DFS:** many words on one board — trie guides and prunes a single sweep.
- **Backtracking:** mark → explore → restore — required for “no cell reuse within one path.”
- **Signal:** “find all words in grid”, “board + word list”, Boggle-style problems.
- **Related:** Word Search I (212), Implement Trie (208), Number of Islands (grid DFS).
- **Pitfalls:** skip restore; duplicate reporting; searching each word separately on large `W`.
