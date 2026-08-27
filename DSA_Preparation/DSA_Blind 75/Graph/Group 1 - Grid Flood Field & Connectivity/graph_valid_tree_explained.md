# 261. Graph Valid Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/graph_valid_tree.ipynb`
> **LeetCode:** https://leetcode.com/problems/graph-valid-tree/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Tree definition | A graph on `n` nodes is a tree iff it has exactly `n-1` edges, is fully **connected**, and has **no cycle** |
| Union-Find | Merge each edge's endpoints; if both ends are already in the same group, that edge closes a cycle |
| Connectivity traversal | Once the edge count is right, DFS/BFS from node 0 and check every node was reached |

**Canonical example** (from notebook):

```
n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]

        0
      / | \
     1  2  3
     |
     4

-> valid tree (4 edges = n-1, connected, acyclic) -> True
```

**Cycle counter-example** (from notebook):

```
n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]

5 edges but n-1 = 4  ->  fails the edge-count check immediately -> False
(the edge (1,3) also closes a cycle 1-2-3-1, which is the deeper reason)
```

Expected outputs (from notebook asserts):

| `n` | `edges` | Expected | `valid_tree_uf` | `valid_tree_dfs` |
| --- | ------- | -------- | ---------------- | ----------------- |
| `5` | `[[0,1],[0,2],[0,3],[1,4]]` | `True` | ✓ matches | ✓ matches |
| `5` | `[[0,1],[1,2],[2,3],[1,3],[1,4]]` | `False` | ✓ matches | ✓ matches |
| `4` | `[[0,1],[2,3]]` | `False` (edge count 2 ≠ 3) | ✓ matches | ✓ matches |
| `1` | `[]` | `True` (single node, no edges needed) | ✓ matches | ✓ matches |

---

## `valid_tree_uf` — Union-Find

### What it does

First rejects any input that doesn't have exactly `n-1` edges (a tree's defining edge count). Then walks each edge, using `find` (with path compression) to locate each endpoint's group leader. If both endpoints already share a leader, the edge would create a cycle, so it returns `False` immediately. Otherwise it merges the two groups. If every edge merges cleanly, the graph is connected and acyclic — a valid tree.

### Code

```python
def valid_tree_uf(n, edges):
    if len(edges) != n - 1:                # a tree on n nodes has EXACTLY n-1 edges
        return False
    parent = list(range(n))                # each node starts as its own group leader
    def find(x):                           # find x's group leader (with path compression)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:                       # both ends already connected -> this edge makes a cycle
            return False
        parent[ra] = rb                    # otherwise merge the two groups
    return True                            # n-1 edges + no cycle => connected tree
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if len(edges) != n - 1: return False` | Cheap early filter — wrong edge count can never be a tree |
| `parent = list(range(n))` | Union-Find init: every node is its own leader |
| `while parent[x] != x: ...` | Climb toward the group's root, halving the path each step (path compression) |
| `parent[x] = parent[parent[x]]` | Point `x` at its grandparent, flattening the tree as we climb |
| `return x` (in `find`) | `x` has reached a node that is its own parent — the group leader |
| `ra, rb = find(a), find(b)` | Resolve both edge endpoints to their group leaders |
| `if ra == rb: return False` | Same group already → this edge would close a cycle |
| `parent[ra] = rb` | Merge: `a`'s whole group now points at `b`'s leader |
| `return True` | All edges merged without a collision → connected + acyclic → tree |

### Step-by-step trace (canonical example `n=5, edges=[[0,1],[0,2],[0,3],[1,4]]`)

Edge-count check: `len(edges)=4`, `n-1=4` → passes.

`parent` starts as `[0, 1, 2, 3, 4]` (index = node, value = current parent).

| Step | Edge `(a,b)` | `find(a)` | `find(b)` | Cycle? | `parent` after merge |
| ---- | ------------ | --------- | --------- | ------ | --------------------- |
| 1 | `(0, 1)` | `0` | `1` | no | `[1, 1, 2, 3, 4]` (`parent[0]=1`) |
| 2 | `(0, 2)` | `0`→compress→`1` (returns `1`) | `2` | no | `[1, 2, 2, 3, 4]` (`parent[1]=2`) |
| 3 | `(0, 3)` | `0`→compress→`2` (returns `2`) | `3` | no | `[1, 2, 3, 3, 4]` (`parent[2]=3`) |
| 4 | `(1, 4)` | `1`→compress→`3` (returns `3`) | `4` | no | `[1, 2, 3, 4, 4]` (`parent[3]=4`) |

All 4 edges merged without any `ra == rb` collision → **returns `True`**.

*(On the cycle example `n=5, edges=[[0,1],[1,2],[2,3],[1,3],[1,4]]`, `len(edges)=5` but `n-1=4`, so the function returns `False` on the very first line — the edge-count filter catches it before Union-Find even starts.)*

### Mental model

- Think of `parent` as a forest of upside-down trees; `find` walks up to the root/leader of a node's tree.
- Merging two different groups is always safe — it can only *grow* connectivity.
- Merging two nodes that are **already** in the same group means there was already a path between them — adding this edge would create a second path, i.e. a cycle.
- Path compression (`parent[x] = parent[parent[x]]`) is what keeps `find` close to `O(1)` amortized instead of degrading to `O(n)` on a long chain.

### Common confusions

- **Checking edge count only:** `n-1` edges is necessary but not sufficient by itself — you still need the cycle check, since `n-1` edges could form a cycle plus a disconnected node (e.g. `n=4, edges=[[0,1],[1,2],[0,2]]` has 3 edges but node 3 is isolated and 0-1-2 is a triangle). The function's loop still verifies this because a triangle would trigger `ra == rb` on the closing edge.
- **`parent[ra] = rb` direction:** the merge direction (which leader adopts which) doesn't affect correctness here — either `parent[ra]=rb` or `parent[rb]=ra` works, it just changes the resulting tree shape.
- **Forgetting path compression:** `find` still works without `parent[x] = parent[parent[x]]`, just slower — correctness doesn't depend on it, performance does.

### Complexity

- **Time:** `O(n · α(n)) ≈ O(n)` — `α` is the inverse-Ackermann function, effectively constant
- **Space:** `O(n)` — the `parent` array

---

## `valid_tree_dfs` — Connectivity Traversal

### What it does

Same edge-count early filter as the Union-Find version. Then builds an undirected adjacency list from the edges, and runs an iterative DFS (explicit stack) starting at node `0`, marking nodes as `seen`. If the traversal reaches every node (`len(seen) == n`), the graph is fully connected; combined with the `n-1` edge count already verified, that guarantees it's also acyclic (a connected graph with exactly `n-1` edges cannot contain a cycle).

### Code

```python
from collections import defaultdict

def valid_tree_dfs(n, edges):
    if len(edges) != n - 1:                # wrong edge count can't be a tree
        return False
    graph = defaultdict(list)              # build an undirected adjacency list
    for a, b in edges:
        graph[a].append(b); graph[b].append(a)
    seen = set(); stack = [0]              # explore from node 0
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for nb in graph[node]:
            if nb not in seen:
                stack.append(nb)
    return len(seen) == n                  # reached every node -> fully connected
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if len(edges) != n - 1: return False` | Same cheap early filter as the Union-Find version |
| `graph = defaultdict(list)` | Adjacency list, auto-creates an empty list for unseen keys |
| `graph[a].append(b); graph[b].append(a)` | Undirected edge → add both directions |
| `seen = set(); stack = [0]` | DFS state: visited set + explicit stack seeded with node `0` |
| `node = stack.pop()` | Pop the most recently pushed node (LIFO = depth-first) |
| `if node in seen: continue` | Skip nodes pushed more than once (duplicate stack entries) |
| `seen.add(node)` | Mark this node visited |
| `for nb in graph[node]: ...` | Look at every neighbor |
| `if nb not in seen: stack.append(nb)` | Only push neighbors not yet visited |
| `return len(seen) == n` | Every node reachable from `0` → the graph is one connected piece |

### Step-by-step trace (canonical example `n=5, edges=[[0,1],[0,2],[0,3],[1,4]]`)

Edge-count check: `len(edges)=4`, `n-1=4` → passes.

Adjacency list built (undirected, both directions added):

```
graph[0] = [1, 2, 3]
graph[1] = [0, 4]
graph[2] = [0]
graph[3] = [0]
graph[4] = [1]
```

DFS trace — `stack` shown left(bottom)→right(top of stack, popped next):

| Step | Pop | In `seen`? | Action | `seen` after | `stack` after |
| ---- | --- | ---------- | ------ | ------------- | -------------- |
| 0 | — | — | init | `{}` | `[0]` |
| 1 | `0` | no | mark visited, push unseen neighbors `1,2,3` | `{0}` | `[1, 2, 3]` |
| 2 | `3` | no | mark visited, neighbor `0` already seen | `{0, 3}` | `[1, 2]` |
| 3 | `2` | no | mark visited, neighbor `0` already seen | `{0, 3, 2}` | `[1]` |
| 4 | `1` | no | mark visited, push unseen neighbor `4` (`0` already seen) | `{0, 3, 2, 1}` | `[4]` |
| 5 | `4` | no | mark visited, neighbor `1` already seen | `{0, 3, 2, 1, 4}` | `[]` |

`len(seen) = 5 == n = 5` → **returns `True`**.

*(On the cycle example, the `n-1` edge check fails first (`5` edges vs `n-1=4`), so `valid_tree_dfs` also short-circuits to `False` before the traversal runs.)*

### Mental model

- The edge-count check does the "no cycle *and* no extra disconnected structure" heavy lifting cheaply; the traversal only needs to prove "no missing piece."
- Iterative DFS with an explicit stack avoids Python recursion-depth limits on long chains (e.g. a path graph of thousands of nodes).
- `if node in seen: continue` guards against processing a node twice when it was pushed onto the stack from two different neighbors before being popped.

### Common confusions

- **DFS alone doesn't prove "no cycle":** without the `n-1` edge-count pre-check, a fully connected graph with cycles (e.g. a graph plus one extra edge) would still visit all `n` nodes and wrongly look like a tree. The two checks (edge count + connectivity) are both required.
- **BFS vs DFS:** either traversal works identically here — only reachability matters, not order.
- **`defaultdict` for isolated nodes:** a node with zero edges still gets an implicit empty list (`graph[node]` returns `[]`) so it just never gets pushed as a neighbor — but it still needs to be reached *from* somewhere, or `len(seen) != n`.

### Complexity

- **Time:** `O(n)` (equivalently `O(V + E)`, and `E = n-1` here) — every node and edge visited once
- **Space:** `O(n)` — adjacency list + `seen` set + stack

---

## Quick reference

| Function | Technique | Canonical result (`n=5`, star+branch edges) | Time | Space |
| -------- | --------- | --------------------------------------------- | ---- | ----- |
| `valid_tree_uf` | Union-Find, merge-and-detect-cycle | `True` | `O(n · α(n)) ≈ O(n)` | `O(n)` |
| `valid_tree_dfs` | Adjacency list + iterative DFS | `True` | `O(n)` | `O(n)` |

## Patterns to remember

- **Tree = connected + acyclic + exactly n-1 edges:** check the edge count first — it's an O(1)-ish filter that rules out most non-trees immediately.
- **Union-Find for cycle detection:** merging an edge whose two endpoints already share a root reveals a cycle in an undirected graph.
- **Connectivity traversal:** once the edge count is confirmed, a single DFS/BFS from any node that reaches all `n` nodes proves the graph is one connected component.
- **Signal words:** "is this a tree", "connected and acyclic", "exactly one path between any two nodes".
- **Related problems:** Number of Connected Components in an Undirected Graph, Redundant Connection, Number of Islands.
