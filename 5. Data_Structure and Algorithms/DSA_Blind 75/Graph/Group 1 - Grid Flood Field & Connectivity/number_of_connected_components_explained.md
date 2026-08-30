# 323. Number of Connected Components in an Undirected Graph — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/number_of_connected_components.ipynb`
> **LeetCode:** https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/ (Premium)
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Connected component | A maximal blob of nodes joined (directly or indirectly) by edges |
| Union-Find (Disjoint Set) | Start with `n` groups; each edge that joins two *different* groups merges them and reduces the group count by one |
| Traversal, count starts | DFS/BFS from every unvisited node; each fresh start marks the discovery of one new component |
| Adjacency list | `dict`/`defaultdict` mapping each node to the list of nodes it directly connects to |
| Path compression | `find(x)` flattens the chain toward the root as it walks, keeping future `find` calls near `O(1)` |

**Canonical example** (from notebook):

```
n = 5, edges = [[0,1],[1,2],[3,4]]

Component A: 0 - 1 - 2      Component B: 3 - 4

    0
     \
      1 - 2        3 - 4

-> 2 connected components
```

Expected outputs (from notebook asserts):

| Input | Expected | `count_components_uf` | `count_components_dfs` |
| ----- | -------- | ---------------------- | ------------------------ |
| `n=5, edges=[[0,1],[1,2],[3,4]]` | `2` | ✓ matches | ✓ matches |
| `n=5, edges=[[0,1],[1,2],[2,3],[3,4]]` | `1` | ✓ matches | ✓ matches |
| `n=4, edges=[]` | `4` | ✓ matches | ✓ matches |

---

## `count_components_uf` — Union-Find

### What it does

Starts every node as its own group (`parent[i] = i`) with a running `count = n`. For each edge `(a, b)`, finds the group leader (root) of `a` and of `b` using path-halving compression. If the roots differ, the edge joins two previously separate groups — the roots are merged (`parent[ra] = rb`) and `count` is decremented by one. Edges that connect nodes already in the same group are ignored (they don't reduce the component count). Returns the final `count`.

### Code

```python
def count_components_uf(n, edges):
    parent = list(range(n))                # each node starts alone
    count = n                              # start with n separate groups
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:                       # this edge joins two different groups
            parent[ra] = rb                # merge them...
            count -= 1                      # ...so one fewer group remains
    return count
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `parent = list(range(n))` | Every node is its own leader initially — `n` singleton groups |
| `count = n` | Group counter starts at `n` (worst case: no edges at all) |
| `def find(x): ...` | Walks up the parent chain to the root; `parent[x] = parent[parent[x]]` is **path halving** — each step skips a level, flattening the tree over time |
| `for a, b in edges:` | Process every edge once |
| `ra, rb = find(a), find(b)` | Get the current group leader of each endpoint |
| `if ra != rb:` | Only act if the edge actually connects two *different* groups |
| `parent[ra] = rb` | Merge — attach `a`'s group under `b`'s group |
| `count -= 1` | One fewer distinct group remains |
| `return count` | Final number of connected components |

### Step-by-step trace (canonical example `n=5, edges=[[0,1],[1,2],[3,4]]`)

Initial state: `parent = [0, 1, 2, 3, 4]`, `count = 5`

| Step | Edge | `find(a)` | `find(b)` | Roots differ? | Merge applied | `parent` after | `count` after |
| ---- | ---- | --------- | --------- | -------------- | -------------- | ---------------- | -------------- |
| 1 | `(0, 1)` | `ra = 0` | `rb = 1` | yes | `parent[0] = 1` | `[1, 1, 2, 3, 4]` | `4` |
| 2 | `(1, 2)` | `ra = 1` | `rb = 2` | yes | `parent[1] = 2` | `[1, 2, 2, 3, 4]` | `3` |
| 3 | `(3, 4)` | `ra = 3` | `rb = 4` | yes | `parent[3] = 4` | `[1, 2, 2, 4, 4]` | `2` |

Note: `find(0)` on step 1 needed no compression because `parent[0] == 0` before any merge (it hits the base case of the `while` loop immediately). No further edges touch node `0` or `1` again in this example, so path halving never actually triggers here — with a longer chain (e.g. a 4th edge `(0, 2)`), `find(0)` would walk `0 -> 1 -> 2`, and the compression step would rewrite `parent[0]` to point at `parent[parent[0]] = parent[1] = 2` directly, shortening future lookups.

**Result:** `count = 2` ✓

### Mental model

- Think of `count` as "how many separate friend groups are left" — it only ever goes down, one group at a time, on each edge that actually *merges* two groups.
- `find(x)` answers "who is the leader of x's group right now?" — two nodes are in the same component exactly when they share a root.
- Path halving is a cheap trick that keeps future `find` calls fast without a full recursive "point everyone at the true root" pass.

### Common confusions

- **Decrementing `count` for every edge:** wrong — only decrement when `ra != rb`. An edge between two nodes already in the same component is redundant and must not shrink `count` again.
- **Isolated nodes:** a node that never appears in `edges` stays as its own untouched group of one — this is exactly why `count` starts at `n`, not `0`.
- **Union direction doesn't matter for the count:** `parent[ra] = rb` vs `parent[rb] = ra` both merge the two groups; only the tree shape (and thus future `find` speed) differs, not the final `count`.

### Complexity

- **Time:** `O((n + E) · α(n)) ≈ O(n + E)` — near-constant amortized `find`/`union` thanks to path compression
- **Space:** `O(n)` — the `parent` array

---

## `count_components_dfs` — Traversal, Count Starts

### What it does

Builds an undirected adjacency list from the edge list (each edge added both ways). Then iterates every node `0..n-1`; whenever a node hasn't been `seen` yet, that means a brand-new component has been found, so `count` is bumped and an iterative DFS (explicit stack) explores and marks every node reachable from it. By the time the loop finishes, `count` equals the number of times a fresh, previously-unseen node was used to kick off a traversal — i.e., the number of components.

### Code

```python
from collections import defaultdict

def count_components_dfs(n, edges):
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b); graph[b].append(a)
    seen = set(); count = 0
    for i in range(n):
        if i not in seen:                  # a node we haven't reached -> a NEW component
            count += 1
            stack = [i]                    # explore this whole component
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                for nb in graph[node]:
                    if nb not in seen:
                        stack.append(nb)
    return count
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `graph = defaultdict(list)` | Adjacency list; missing keys default to an empty list (handles isolated nodes automatically) |
| `graph[a].append(b); graph[b].append(a)` | Undirected edge — record the connection in both directions |
| `seen = set(); count = 0` | Global visited set and component counter |
| `for i in range(n):` | Try every node as a possible new component start |
| `if i not in seen:` | Unvisited node found — it must belong to a component not yet counted |
| `count += 1` | Register the new component |
| `stack = [i]` | Seed an iterative DFS from this node |
| `while stack: node = stack.pop()` | Standard stack-based DFS |
| `if node in seen: continue` | Skip nodes pushed more than once (defensive re-check) |
| `seen.add(node)` | Mark this node as explored |
| `for nb in graph[node]: if nb not in seen: stack.append(nb)` | Push all unvisited neighbors to keep exploring the component |
| `return count` | Total number of components found |

### Step-by-step trace (canonical example `n=5, edges=[[0,1],[1,2],[3,4]]`)

**Adjacency list built first:**

```
graph = {
  0: [1],
  1: [0, 2],
  2: [1],
  3: [4],
  4: [3]
}
```

`seen = {}`, `count = 0`

| Step | Outer `i` | Action | Stack (top = last) | `seen` after | `count` after |
| ---- | --------- | ------ | ------------------- | ------------- | -------------- |
| 1 | `i=0` | `0 not in seen` -> new component | `stack=[0]` | `{}` | `1` |
| 2 | — | pop `0`, mark seen, push neighbor `1` | `stack=[1]` | `{0}` | `1` |
| 3 | — | pop `1`, mark seen, neighbors `[0,2]` — `0` seen (skip), push `2` | `stack=[2]` | `{0,1}` | `1` |
| 4 | — | pop `2`, mark seen, neighbor `[1]` — `1` seen (skip) | `stack=[]` | `{0,1,2}` | `1` |
| 5 | `i=1` | `1 in seen` -> skip | `stack=[]` | `{0,1,2}` | `1` |
| 6 | `i=2` | `2 in seen` -> skip | `stack=[]` | `{0,1,2}` | `1` |
| 7 | `i=3` | `3 not in seen` -> new component | `stack=[3]` | `{0,1,2}` | `2` |
| 8 | — | pop `3`, mark seen, push neighbor `4` | `stack=[4]` | `{0,1,2,3}` | `2` |
| 9 | — | pop `4`, mark seen, neighbor `[3]` — `3` seen (skip) | `stack=[]` | `{0,1,2,3,4}` | `2` |
| 10 | `i=4` | `4 in seen` -> skip | `stack=[]` | `{0,1,2,3,4}` | `2` |

**Result:** `count = 2` ✓

### Mental model

- Every entry into the outer `for i` loop that finds an unvisited node is, by definition, a node in a component nobody has explored yet — that's the whole counting trick.
- The inner `while stack` loop is just "flood fill" — mark a node, then queue its unmarked neighbors, until the whole blob is painted.
- Isolated nodes (no edges) still get counted: `graph[i]` defaults to `[]`, so the DFS marks just that one node and moves on — exactly the `n=4, edges=[]` -> `4` test case.

### Common confusions

- **Using `graph[node]` on a node with no edges:** works fine because `defaultdict(list)` returns `[]` instead of raising `KeyError` — don't assume you need to pre-seed every node into the dict.
- **Checking `seen` only when pushing vs. also when popping:** the code does both (`if nb not in seen` before pushing, and `if node in seen: continue` after popping) — belt-and-suspenders against pushing the same node twice from different branches.
- **Recursion vs. explicit stack:** this uses an explicit stack (`list` as LIFO) to avoid Python recursion-depth limits on long chains; a recursive DFS would behave identically but risk `RecursionError` on large graphs.

### Complexity

- **Time:** `O(n + E)` — build the adjacency list in `O(E)`, then visit each node and edge at most once across all DFS calls
- **Space:** `O(n + E)` — adjacency list plus the `seen` set and stack

---

## Quick reference

| Function | Technique | Result on `n=5, edges=[[0,1],[1,2],[3,4]]` | Time | Space |
| -------- | --------- | -------------------------------------------- | ---- | ----- |
| `count_components_uf` | Union-Find with path halving | `2` | `O((n+E)·α(n)) ≈ O(n+E)` | `O(n)` |
| `count_components_dfs` | Iterative DFS, count fresh starts | `2` | `O(n + E)` | `O(n + E)` |

## Patterns to remember

- **Union-Find counts groups:** start at `n`, subtract one every time an edge merges two *different* groups; edges within an already-merged group are free no-ops.
- **Traversal counts starts:** loop over every node; each time you hit an unvisited one, that's a brand-new component — DFS/BFS from it just paints the rest of that component.
- **Isolated nodes still count:** don't forget nodes with zero edges — both approaches handle them naturally (Union-Find via the initial `count = n`; traversal via `defaultdict` returning `[]`).
- **Signal words:** "connected components", "groups", "friend circles", "provinces", "islands of nodes".
- **Common pitfalls:** (1) decrementing the Union-Find count for an edge that joins nodes already in the same group; (2) forgetting to iterate over *all* `n` nodes in the traversal approach and missing isolated ones.
- **Related problems:** Graph Valid Tree, Number of Islands, Redundant Connection, Accounts Merge.
