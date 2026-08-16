# 133. Clone Graph — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/clone_graph.ipynb`
> **LeetCode:** https://leetcode.com/problems/clone-graph/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Visited/clone map | A `dict` mapping **original node → its copy**; the first time you see a node, create its copy and remember it |
| DFS | Recurse into neighbors, creating the copy for a node **before** recursing into its neighbors (so cycles terminate cleanly) |
| BFS | Copy the start node up front, then use a queue to visit every node once, wiring up copy-to-copy neighbor links as you go |
| Cycles | Undirected graphs here always contain cycles (edges go both ways); the map is what stops infinite recursion/looping |

**Canonical example** (from notebook `build_sample()` — a 4-node square/cycle graph):

```
Values:            Adjacency:
  1 --- 2           1: [2, 4]
  |     |           2: [1, 3]
  |     |           3: [2, 4]
  4 --- 3           4: [1, 3]
```

Built as:
```python
a, b, c, d = Node(1), Node(2), Node(3), Node(4)
a.neighbors = [b, d]; b.neighbors = [a, c]; c.neighbors = [b, d]; d.neighbors = [a, c]
```

Expected outputs (from notebook asserts — checked via `signature()`, which records each node's value and its sorted neighbor values):

| Input | Check | `clone_dfs` | `clone_bfs` |
| ----- | ----- | ----------- | ----------- |
| Square graph rooted at `a` (val `1`) | `cp is not orig` (new objects) | ✓ passes | ✓ passes |
| Square graph rooted at `a` (val `1`) | `signature(orig) == signature(cp)` (same structure) | ✓ passes | ✓ passes |

`signature()` for both the original and every clone resolves to:
```
[(1, (2, 4)), (2, (1, 3)), (3, (2, 4)), (4, (1, 3))]
```

---

## `clone_dfs` — DFS with a Clone Map

### What it does

Guards the empty-graph case. Uses a closure `dfs(n)` plus an outer `old_to_new` map. The **first** time a node is seen, its copy is created and stored in the map *before* recursing into its neighbors — this is what makes cycles safe (a later recursive call back to an already-visited node just returns the cached copy instead of recursing again). Each neighbor is copied (or fetched from the map) and appended to `copy.neighbors`.

### Code

```python
def clone_dfs(node):
    if not node:
        return None
    old_to_new = {}                        # original node -> its freshly-made copy
    def dfs(n):
        if n in old_to_new:                # already copied this node...
            return old_to_new[n]           # ...reuse the copy (this also stops cycles looping)
        copy = Node(n.val)                 # make the copy BEFORE recursing (so cycles work)
        old_to_new[n] = copy
        for nb in n.neighbors:             # copy each neighbor and link copy -> copy
            copy.neighbors.append(dfs(nb))
        return copy
    return dfs(node)
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not node: return None` | Empty graph edge case |
| `old_to_new = {}` | Map from original node object → its copy |
| `if n in old_to_new: return old_to_new[n]` | Membership check first — reuse an existing copy instead of recreating it (and prevents infinite recursion on cycles) |
| `copy = Node(n.val)` | Create the copy **before** visiting neighbors |
| `old_to_new[n] = copy` | Register the copy immediately so a cyclic reference back to `n` finds it already made |
| `for nb in n.neighbors: copy.neighbors.append(dfs(nb))` | Recursively copy (or fetch) each neighbor and wire copy → copy |
| `return copy` | Bubble the copy back up the call stack |
| `return dfs(node)` | Kick off the recursion from the given start node |

### Step-by-step trace (canonical square graph, starting at node `1`)

`old_to_new` shown as `{original_val: copy_id}` after each insertion; `dfs(1)` is the outer call.

| Step | Call | Already in map? | Action | `old_to_new` after |
| ---- | ---- | ---------------- | ------ | ------------------- |
| 1 | `dfs(1)` | no | create `copy1` | `{1: c1}` |
| 2 | `dfs(2)` (neighbor of 1) | no | create `copy2` | `{1: c1, 2: c2}` |
| 3 | `dfs(1)` (neighbor of 2) | **yes** | return cached `c1` — `c2.neighbors = [c1]` | `{1: c1, 2: c2}` |
| 4 | `dfs(3)` (neighbor of 2) | no | create `copy3` | `{1: c1, 2: c2, 3: c3}` |
| 5 | `dfs(2)` (neighbor of 3) | **yes** | return cached `c2` — `c3.neighbors = [c2]` | unchanged |
| 6 | `dfs(4)` (neighbor of 3) | no | create `copy4` | `{1: c1, 2: c2, 3: c3, 4: c4}` |
| 7 | `dfs(1)` (neighbor of 4) | **yes** | return cached `c1` — `c4.neighbors = [c1]` | unchanged |
| 8 | `dfs(3)` (neighbor of 4) | **yes** | return cached `c3` — `c4.neighbors = [c1, c3]`; `dfs(4)` returns `c4` | unchanged |
| 9 | back in `dfs(3)` | — | `c3.neighbors = [c2, c4]`; `dfs(3)` returns `c3` | unchanged |
| 10 | back in `dfs(2)` | — | `c2.neighbors = [c1, c3]`; `dfs(2)` returns `c2` | unchanged |
| 11 | `dfs(4)` (neighbor of 1) | **yes** | return cached `c4` — `c1.neighbors = [c2, c4]`; `dfs(1)` returns `c1` | unchanged |

**Final copy graph:** `c1.neighbors=[c2,c4]`, `c2.neighbors=[c1,c3]`, `c3.neighbors=[c2,c4]`, `c4.neighbors=[c1,c3]` — identical structure to the original, but every node is a new `Node` object. ✓

### Mental model

- Treat the map as "have I already made this node's copy?" — check it **first**, before doing any work.
- Creating and registering the copy *before* recursing is the trick that lets DFS survive cycles — without it, `dfs(1) → dfs(2) → dfs(1) → ...` would recurse forever.
- The recursion naturally wires `copy.neighbors` because each `dfs(nb)` call returns either a brand-new copy or a cached one — both are valid to append.

### Common confusions

- **Registering the copy after the neighbor loop (wrong):** if `old_to_new[n] = copy` happens *after* `for nb in n.neighbors: ...`, a cycle back to `n` would not find it in the map yet and would recurse infinitely.
- **Wiring copies to originals:** the whole point of the map is that `copy.neighbors` only ever holds objects pulled from `old_to_new`, never the original `Node` objects.
- **One map per call:** `old_to_new` is created fresh inside `clone_dfs` (not global), so repeated calls don't leak state between them.

### Complexity

- **Time:** `O(V + E)` — each node visited once (map lookup), each edge traversed once
- **Space:** `O(V)` — the map, plus `O(V)` recursion stack in the worst case (chain-shaped graph)

---

## `clone_bfs` — BFS with a Queue

### What it does

Guards the empty-graph case. Seeds `old_to_new` with a copy of the **start node** before the loop begins, then does a standard BFS: pop a node, for each of its neighbors make a copy if one doesn't exist yet (and enqueue it), then always link `copy(cur).neighbors` to `copy(neighbor)`.

### Code

```python
def clone_bfs(node):
    if not node:
        return None
    old_to_new = {node: Node(node.val)}    # copy the start node first
    q = deque([node])
    while q:
        cur = q.popleft()
        for nb in cur.neighbors:
            if nb not in old_to_new:       # first time we see this neighbor...
                old_to_new[nb] = Node(nb.val)  # ...make its copy and queue it
                q.append(nb)
            old_to_new[cur].neighbors.append(old_to_new[nb])  # link copy -> copy
    return old_to_new[node]
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not node: return None` | Empty graph edge case |
| `old_to_new = {node: Node(node.val)}` | Copy the start node immediately, before BFS begins |
| `q = deque([node])` | BFS queue seeded with the **original** start node |
| `cur = q.popleft()` | Dequeue the next original node to process |
| `if nb not in old_to_new: ... q.append(nb)` | First sighting of a neighbor: create its copy and enqueue the **original** neighbor for later processing |
| `old_to_new[cur].neighbors.append(old_to_new[nb])` | Always runs (whether `nb` was new or already copied) — links `copy(cur) → copy(nb)` |
| `return old_to_new[node]` | Return the copy of the original start node |

### Step-by-step trace (canonical square graph, starting at node `1`)

Queue holds **original** nodes. `old_to_new` shown as `{val: copy_id}`.

| Step | `old_to_new` before | Dequeue `cur` | Neighbors of `cur` | New copies made | Links added | Queue after |
| ---- | -------------------- | ------------- | ------------------- | ---------------- | ------------ | ------------- |
| 0 (seed) | `{}` | — | — | `1 → c1` | — | `[1]` |
| 1 | `{1:c1}` | `1` | `[2, 4]` | `2 → c2`, `4 → c4` | `c1.neighbors=[c2]`, then `[c2,c4]` | `[2, 4]` |
| 2 | `{1:c1,2:c2,4:c4}` | `2` | `[1, 3]` | `3 → c3` | `c2.neighbors=[c1]`, then `[c1,c3]` | `[4, 3]` |
| 3 | `{1:c1,2:c2,3:c3,4:c4}` | `4` | `[1, 3]` | (none — both already copied) | `c4.neighbors=[c1]`, then `[c1,c3]` | `[3]` |
| 4 | unchanged | `3` | `[2, 4]` | (none) | `c3.neighbors=[c2]`, then `[c2,c4]` | `[]` |

Loop ends (`q` empty). Return `old_to_new[1]` = `c1`.

**Final copy graph:** `c1.neighbors=[c2,c4]`, `c2.neighbors=[c1,c3]`, `c3.neighbors=[c2,c4]`, `c4.neighbors=[c1,c3]` — same structure as `clone_dfs` produced. ✓

### Mental model

- Seed the map with the start node's copy *before* the loop so the very first `old_to_new[cur]` lookup succeeds.
- Two separate concerns per neighbor: (1) does its copy exist yet? create + enqueue if not; (2) link `copy(cur)` to `copy(nb)` — this second step happens **unconditionally**, whether the neighbor was just created or already existed.
- The queue always holds **original** nodes; the map is the only place copies live until the very end.

### Common confusions

- **Only linking on first sighting (wrong):** the `old_to_new[cur].neighbors.append(...)` call must run every time a neighbor is processed, not just inside the `if nb not in old_to_new` block — otherwise edges discovered from the "non-first" visitor are lost (e.g. node `4`'s edge back to node `1` still needs to be appended even though `1` was copied at seed time).
- **Enqueueing copies instead of originals:** `q.append(nb)` appends the **original** node so its original `.neighbors` list can still be iterated later.
- **Forgetting to seed the start node:** unlike `clone_dfs` (which creates the copy lazily inside `dfs`), `clone_bfs` must pre-populate `old_to_new` with the start node before the `while` loop, or the first `old_to_new[cur]` lookup would `KeyError`.

### Complexity

- **Time:** `O(V + E)` — each node dequeued once, each edge inspected once
- **Space:** `O(V)` — the map plus a queue that can hold up to all nodes

---

## Quick reference

| Function | Technique | Clone of `[1,2,3,4]` square graph | Time | Space |
| -------- | --------- | ----------------------------------- | ---- | ----- |
| `clone_dfs` | DFS recursion + clone map (copy created before recursing into neighbors) | `1:[2,4], 2:[1,3], 3:[2,4], 4:[1,3]` | `O(V+E)` | `O(V)` |
| `clone_bfs` | BFS with a queue, start node pre-copied, copy map doubles as "seen" set | `1:[2,4], 2:[1,3], 3:[2,4], 4:[1,3]` | `O(V+E)` | `O(V)` |

## Patterns to remember

- **Visited/clone map:** any graph traversal that must avoid revisiting nodes (cycles!) or must remember created work (copies) uses a `dict` keyed by the original node object.
- **Create-before-recurse / seed-before-loop:** register a node's copy in the map *before* touching its neighbors — this is the difference between terminating on a cycle and infinite recursion/looping.
- **DFS and BFS are interchangeable here:** both are `O(V + E)` — the choice only affects traversal order and (for DFS) recursion-stack depth vs. (for BFS) queue width.
- **Signal words:** "deep copy a graph", "clone", "traverse with cycles", "connected undirected graph".
- **Related problems:** Number of Islands, Course Schedule, Copy List with Random Pointer.
- **Common pitfalls:** wiring copies to *original* nodes instead of other copies; omitting the visited/clone map and looping forever on a cycle.
