# 269. Alien Dictionary — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/alien_dictionary.ipynb`
> **LeetCode:** https://leetcode.com/problems/alien-dictionary/ (Premium / Locked)
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Graph construction | Compare each pair of **adjacent** words; the first differing letter gives a directed edge `earlier letter -> later letter` |
| In-degree tracking | Count how many "must come before" rules point at each letter |
| Topological sort (Kahn's method) | Repeatedly output a letter with in-degree 0, then decrement its neighbors' in-degrees |
| Cycle / contradiction detection | If the output doesn't contain every letter, the graph had a cycle — no valid order exists |
| Prefix-violation edge case | A longer word appearing **before** its own prefix (e.g. `"abc"` before `"ab"`) is invalid on its own, with no differing letter needed |

**Canonical example** (from notebook):

```
["wrt", "wrf", "er", "ett", "rftt"]  →  "wertf"
```

Adjacent-pair comparisons produce these ordering clues:

| Pair | First difference | Edge (clue) |
| ---- | ----------------- | ----------- |
| `wrt` vs `wrf` | index 2: `t` vs `f` | `t -> f` |
| `wrf` vs `er` | index 0: `w` vs `e` | `w -> e` |
| `er` vs `ett` | index 1: `r` vs `t` | `r -> t` |
| `ett` vs `rftt` | index 0: `e` vs `r` | `e -> r` |

Expected outputs (from notebook asserts, checked via the `respects` helper):

| Input | Expected result | `alien_order` |
| ----- | ---------------- | ------------- |
| `["wrt","wrf","er","ett","rftt"]` | a valid order (`"wertf"`) | ✓ matches (verified via `respects`) |
| `["z","x"]` | a valid order (`"zx"`) | ✓ matches |
| `["z","x","z"]` | `""` (cycle: `z -> x -> z`) | ✓ matches |
| `["abc","ab"]` | `""` (prefix violation: `"abc"` can't come before `"ab"`) | ✓ matches |

---

## `alien_order` — Build Graph + Kahn's Topological Sort

### What it does

Builds a directed graph where an edge `a -> b` means "letter `a` must come before letter `b`" — derived from the **first differing letter** of every pair of adjacent words. Also tracks an in-degree count per letter. Detects the invalid "longer word is a prefix of, and sorts before, its own prefix" case immediately. Finally runs Kahn's BFS topological sort: start from letters with in-degree 0, peel them off, decrement neighbors' in-degrees, and enqueue any that reach 0. If the resulting order doesn't include every letter, a cycle existed, so return `""`.

### Code

```python
from collections import defaultdict, deque

def alien_order(words):
    graph = defaultdict(set)               # letter -> set of letters that must come AFTER it
    indeg = {c: 0 for w in words for c in w}   # every letter starts with 0 "must come before" rules
    for i in range(len(words) - 1):        # compare each adjacent pair of words
        a, b = words[i], words[i + 1]
        minlen = min(len(a), len(b))
        if len(a) > len(b) and a[:minlen] == b[:minlen]:
            return ""                      # e.g. "abc" before "ab" is impossible -> invalid
        for j in range(minlen):
            if a[j] != b[j]:               # first difference reveals the order clue
                if b[j] not in graph[a[j]]:
                    graph[a[j]].add(b[j]); indeg[b[j]] += 1   # a[j] comes before b[j]
                break                      # only the FIRST difference is a real clue
    q = deque([c for c in indeg if indeg[c] == 0])   # letters with no constraints
    order = []
    while q:
        c = q.popleft(); order.append(c)   # output a letter with nothing before it
        for nxt in graph[c]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    return "".join(order) if len(order) == len(indeg) else ""   # leftover letters -> a cycle
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `graph = defaultdict(set)` | Adjacency list: letter → set of letters that must come after it (a `set` avoids duplicate edges) |
| `indeg = {c: 0 for w in words for c in w}` | Every unique letter across all words seeded at in-degree 0 |
| `for i in range(len(words) - 1)` | Only adjacent word pairs give a valid clue (that's how the dictionary is sorted) |
| `minlen = min(len(a), len(b))` | Can only compare up to the shorter word's length |
| `if len(a) > len(b) and a[:minlen] == b[:minlen]: return ""` | Longer word is a strict prefix-superset of the shorter one but appears **first** — contradiction, no valid alphabet |
| `for j in range(minlen): if a[j] != b[j]:` | Scan left to right for the first differing character |
| `if b[j] not in graph[a[j]]: graph[a[j]].add(b[j]); indeg[b[j]] += 1` | Add the edge `a[j] -> b[j]` once (guards against double-counting in-degree if the same pair of letters recurs) |
| `break` | Stop scanning — only the first difference is a real ordering clue; later letters carry no information |
| `q = deque([c for c in indeg if indeg[c] == 0])` | Kahn's start set: letters with no unresolved "must come before" constraints |
| `c = q.popleft(); order.append(c)` | Emit a letter that is safe to place next |
| `for nxt in graph[c]: indeg[nxt] -= 1; ... append` | Removing `c` frees up any letter that only depended on `c`; once a letter's in-degree hits 0, it's ready |
| `return "".join(order) if len(order) == len(indeg) else ""` | If every letter got emitted, we have a full valid order; if some are still stuck (cycle), invalid |

### Step-by-step trace (canonical example `["wrt","wrf","er","ett","rftt"]`)

**Unique letters:** `w, r, t, f, e` → `indeg = {w:0, r:0, t:0, f:0, e:0}` initially, `graph = {}` (empty).

**Phase 1 — building edges from adjacent pairs:**

| Pair (`a`, `b`) | `minlen` | Prefix-violation check | First diff (`j`) | Edge added | `indeg` after |
| ---------------- | -------- | ----------------------- | ----------------- | ---------- | -------------- |
| `wrt`, `wrf` | 3 | equal length, skip | `j=2`: `t` vs `f` | `t -> f` | `f:1` |
| `wrf`, `er` | 2 | `len(a)=3 > len(b)=2` but `"wr" != "er"`, not a violation | `j=0`: `w` vs `e` | `w -> e` | `e:1` |
| `er`, `ett` | 2 | `len(a)=2` not `>` `len(b)=3`, skip | `j=1`: `r` vs `t` | `r -> t` | `t:1` |
| `ett`, `rftt` | 3 | `len(a)=3` not `>` `len(b)=4`, skip | `j=0`: `e` vs `r` | `e -> r` | `r:1` |

Final graph and in-degrees:

```
graph: t -> {f}
       w -> {e}
       r -> {t}
       e -> {r}

indeg: w=0, r=1, t=1, f=1, e=1
```

**Phase 2 — Kahn's BFS:**

| Step | Queue (front…back) | Popped | `order` after | In-degree updates |
| ---- | ------------------- | ------ | -------------- | ------------------ |
| init | — | — | `[]` | seed queue with in-degree-0 letters → `[w]` |
| 1 | `[w]` | `w` | `[w]` | neighbor `e`: `indeg[e] 1→0` → enqueue `e` |
| 2 | `[e]` | `e` | `[w, e]` | neighbor `r`: `indeg[r] 1→0` → enqueue `r` |
| 3 | `[r]` | `r` | `[w, e, r]` | neighbor `t`: `indeg[t] 1→0` → enqueue `t` |
| 4 | `[t]` | `t` | `[w, e, r, t]` | neighbor `f`: `indeg[f] 1→0` → enqueue `f` |
| 5 | `[f]` | `f` | `[w, e, r, t, f]` | no neighbors (`graph[f]` empty) |
| end | `[]` | — | `[w, e, r, t, f]` | queue empty, loop ends |

`len(order) == 5 == len(indeg)` → return `"wertf"`. ✓ matches expected.

### Edge case trace — cycle (`["z", "x", "z"]`)

| Pair | First diff | Edge added |
| ---- | ---------- | ---------- |
| `z`, `x` | `j=0`: `z` vs `x` | `z -> x`, `indeg[x]=1` |
| `x`, `z` | `j=0`: `x` vs `z` | `x -> z`, `indeg[z]=1` |

`indeg = {z:1, x:1}` — **no letter has in-degree 0**, so `q` starts empty. The `while q` loop never runs, `order = []`. `len(order)=0 != len(indeg)=2` → return `""`. This is the `z -> x -> z` cycle: neither letter can be safely placed first.

### Edge case trace — prefix violation (`["abc", "ab"]`)

`indeg` is seeded as `{a:0, b:0, c:0}`. On the very first (and only) pair: `a="abc"`, `b="ab"`, `minlen=2`. Check: `len(a)=3 > len(b)=2` **and** `a[:2]="ab" == b[:2]="ab"` → condition true → **immediately `return ""`**, without ever reaching the topological sort. This models the real-world impossibility: if `"ab"` sorts after `"abc"`, but `"ab"` is a strict prefix of `"abc"`, no alphabet ordering can make a shorter prefix come after its own extension.

### Mental model

- Think of it as **Course Schedule with letters as courses**: "letter `a` before letter `b`" is exactly like "course `a` is a prerequisite of course `b`".
- Only the **first differing character** between two adjacent words carries information — everything after it is irrelevant (and can't be, since sorting is decided by the first difference).
- In-degree 0 = "nothing constrains this letter to come after something else yet" = safe to place next.
- A letter left with `indeg > 0` at the end means it's stuck in a cycle (directly or indirectly) — no order satisfies it.
- The prefix check is a **separate, cheaper** contradiction than a graph cycle — catch it before even attempting to build an edge for that pair.

### Common confusions

- **Comparing every letter, not just the first difference:** words like `"wrt"` vs `"wrf"` only tell you `t` comes before `f` — comparing the third position again (nothing to compare, they're equal length) is not needed, but critically, don't build edges for the *matching* prefix letters (`w==w`, `r==r`) — they carry no ordering information.
- **Missing the prefix-violation check:** without it, `["abc", "ab"]` would silently produce no edges at all (no differing letter within `minlen`) and wrongly return every unique letter in in-degree-0 order — an invalid "valid" answer.
- **Double-counting in-degree:** the `if b[j] not in graph[a[j]]` guard prevents adding the same edge twice (e.g. if two different word pairs both imply `t -> f`), which would inflate `indeg[f]` and make the letter unreachable even though the graph has no real cycle.
- **`indeg` must include every letter, even ones with no edges:** built via `{c: 0 for w in words for c in w}` up front, so letters that never appear as the first difference (like `f` here, which only ever appears as a target) are still tracked and still get emitted once their in-degree drops to 0. Letters that appear in only one word and never trigger a comparison still start correctly at `indeg[c] = 0` and reach the initial queue.
- **Multiple valid orders can exist:** Kahn's algorithm returns *a* valid order, not necessarily the lexicographically smallest or a unique one — that's why the `respects` helper checks validity against the *rules*, not against one fixed expected string.

### Complexity

- **Time:** `O(C)` where `C` is the total number of characters across all words (building edges is one pass per adjacent pair, bounded by word lengths; Kahn's BFS is `O(V + E)` where `V`/`E` are bounded by the unique letters and edges, which is at most 26 letters and 26² edges for the English alphabet, but expressed generally as total input size)
- **Space:** `O(unique letters + edges)` — for the `graph`, `indeg` dict, and the BFS `queue`/`order` list

---

## `respects` — Correctness Checker (test helper, not the solution)

### What it does

Given the original `words` list and a candidate `order` string produced by `alien_order`, verifies the order is actually consistent with every adjacent-word clue. Returns `None` if `order` is `""` (nothing to check — the "invalid" case is a separate assertion path), `True` if every clue is respected, `False` if any clue is violated (including the prefix-violation rule). This is a testing utility, not part of the LeetCode solution itself — it exists in the notebook purely to validate `alien_order`'s output without hardcoding one "correct" string (since multiple valid topological orders can exist).

### Code

```python
def respects(words, order):
    if order == "":
        return None
    pos = {c: i for i, c in enumerate(order)}
    for a, b in zip(words, words[1:]):
        for x, y in zip(a, b):
            if x != y:
                if pos[x] > pos[y]:
                    return False
                break
        else:
            if len(a) > len(b):
                return False
    return True
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if order == "": return None` | No order to validate — caller should separately assert this was the *expected* invalid case |
| `pos = {c: i for i, c in enumerate(order)}` | Map each letter to its index in the candidate alphabet, for O(1) "which comes first" lookups |
| `for a, b in zip(words, words[1:])` | Walk each adjacent word pair, same as the solution does |
| `for x, y in zip(a, b): if x != y: ...` | Find the first differing character between the two words |
| `if pos[x] > pos[y]: return False` | If the earlier word's differing letter is positioned *after* the later word's letter in the candidate order, the order is wrong |
| `break` | Stop at the first difference, same rule as in `alien_order` |
| `else: if len(a) > len(b): return False` | The `for...else` fires only if the loop completed with **no** differing letter found (one word is a prefix of the other) — in that case the shorter one must come first, or it's invalid |
| `return True` | All adjacent pairs checked out |

### Step-by-step trace (canonical example, `order="wertf"`)

`pos = {w:0, e:1, r:2, t:3, f:4}`

| Pair | First diff | `pos[x]` vs `pos[y]` | Violation? |
| ---- | ---------- | ---------------------- | ---------- |
| `wrt`, `wrf` | `t` vs `f` | `pos[t]=3`, `pos[f]=4` → `3 > 4`? No | OK |
| `wrf`, `er` | `w` vs `e` | `pos[w]=0`, `pos[e]=1` → `0 > 1`? No | OK |
| `er`, `ett` | `r` vs `t` | `pos[r]=2`, `pos[t]=3` → `2 > 3`? No | OK |
| `ett`, `rftt` | `e` vs `r` | `pos[e]=1`, `pos[r]=2` → `1 > 2`? No | OK |

All pairs pass → returns `True`, confirming `"wertf"` is a valid alphabet for this input.

### Mental model

- It replays the exact same "first differing letter" logic as `alien_order`, but instead of building a graph, it just checks the candidate order agrees with each clue.
- A `for...else` on the inner loop is the Pythonic way to detect "the loop never broke", i.e. one word is entirely a prefix of the other.
- This decouples **testing** ("is this a legal alphabet?") from **generation** ("what's a legal alphabet?") — necessary because topological sort is not unique.

### Common confusions

- **`for...else` semantics:** the `else` block runs when the `for` loop completes without hitting `break` — easy to misread as "the loop didn't run at all". Here it correctly captures "no differing character was found within the compared range".
- **Not checking letters absent from any clue:** `respects` only validates letters that appear in some adjacent-pair comparison; a valid `order` could place unconstrained letters anywhere among themselves without affecting the result.
- **`None` vs `False`:** returning `None` for `order == ""` is a deliberate three-way result (not checked / valid / invalid) — the notebook's test loop treats `exp == "invalid"` and `respects(...)` separately rather than conflating "no order returned" with "order returned but wrong".

### Complexity

- **Time:** `O(C)` where `C` is total characters across all words — one pass over adjacent pairs, each pair scanned up to its shorter length
- **Space:** `O(k)` where `k` is the number of unique letters in `order` (the `pos` dict)

---

## Quick reference

| Function | Role | Technique | Result on `["wrt","wrf","er","ett","rftt"]` | Time | Space |
| -------- | ---- | --------- | --------------------------------------------- | ---- | ----- |
| `alien_order` | Solution | Build graph from first-difference clues + Kahn's topological sort | `"wertf"` | `O(C)` total chars | `O(letters + edges)` |
| `respects` | Test helper | Replays first-difference logic to validate a candidate order against every clue | `True` | `O(C)` total chars | `O(k)` unique letters |

## Patterns to remember

- **Comparisons → directed graph → topological sort:** whenever a problem gives you pairwise "this comes before that" facts (sorted words, task dependencies, build order), model it as a graph and run Kahn's algorithm or DFS-based topo sort.
- **Only the first difference matters:** in lexicographic comparisons, everything after the first differing character is noise — don't build edges from it.
- **In-degree 0 = free to place:** Kahn's queue always starts with, and stays fed by, nodes that currently have no unresolved dependency.
- **Leftover in-degree = cycle:** if `len(order) != len(all nodes)` after the BFS drains, some nodes never reached in-degree 0 — a contradiction/cycle exists.
- **Prefix contradiction is a distinct edge case** from a graph cycle — a longer word sorted before its own prefix is invalid *before* you even look at differing letters.
- **Multiple valid answers:** don't test topological-sort output against one fixed string; verify it against the *rules* instead (see `respects`).
- **Signal words:** "unknown alphabet", "derive an order from comparisons", "sorted dictionary", "build order", "prerequisite".
- **Related problems:** Course Schedule II, Sequence Reconstruction, Build Order (CTCI), Minimum Height Trees.
