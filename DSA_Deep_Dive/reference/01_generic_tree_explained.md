# Generic (N-ary) Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Deep_Dive/notebooks/01_generic_tree.ipynb`  
> **Companion tutorial:** `DSA_Deep_Dive/tutorials/01_Generic_Tree.md`  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| N-ary tree | Each node has a **list** of children (any count) |
| DFS | Pre-order (node first) or post-order (node last) |
| BFS | Queue — visit level by level |
| Subtree pattern | Solve each child subtree, then combine |
| Flat rebuild | Hash map `id → node`, one pass to link parents |

**Canonical tree used throughout:**

```
            A          ← root
         /  |  \
        B   C   D
       / \       \
      E   F        G
```

Expected outputs (from notebook asserts):

| Function | Output |
|----------|--------|
| `dfs_preorder` | `["A", "B", "E", "F", "C", "D", "G"]` |
| `dfs_postorder` | `["E", "F", "B", "C", "G", "D", "A"]` |
| `bfs` | `["A", "B", "C", "D", "E", "F", "G"]` |
| `size` | `7` |
| `height` | `2` |
| `count_leaves` | `4` |

---

## `Node` and `add_child` — building the tree

### Code

```python
class Node:
  def __init__(self, val):
    self.val = val
    self.children = []

def add_child(parent, child_val):
    child = Node(child_val)
    parent.children.append(child)
    return child
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `self.children = []` | Empty list — can hold any number of child nodes |
| `parent.children.append(child)` | Attach new child under parent (order preserved) |
| `return child` | Return the new node so you can attach grandchildren |

### Build sequence

| Step | Call | Result |
|------|------|--------|
| 1 | `A = Node("A")` | Root with no children |
| 2 | `add_child(A, "B")` | A.children = [B] |
| 3 | `add_child(A, "C")` | A.children = [B, C] |
| 4 | `add_child(A, "D")` | A.children = [B, C, D] |
| 5 | `add_child(B, "E")` | B.children = [E] |
| 6 | `add_child(B, "F")` | B.children = [E, F] |
| 7 | `add_child(D, "G")` | D.children = [G] |

---

## `dfs_preorder` — node before children

### What it does

Visits the current node, then each child left-to-right. Top-down DFS on an N-ary tree.

### Code

```python
def dfs_preorder(node, out=None):
    if out is None:
        out = []
    if node is None:
        return out
    out.append(node.val)
    for child in node.children:
        dfs_preorder(child, out)
    return out
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `out.append(node.val)` | Visit **before** recursing into children |
| `for child in node.children` | Process every child in list order (left to right) |

### Step-by-step trace (every visit)

| Step | Enters | Visit now? | `out` after |
|------|--------|------------|-------------|
| 1 | A | **A** | `["A"]` |
| 2 | B | **B** | `["A", "B"]` |
| 3 | E | **E** | `["A", "B", "E"]` |
| 4 | F | **F** | `["A", "B", "E", "F"]` |
| 5 | C | **C** | `["A", "B", "E", "F", "C"]` |
| 6 | D | **D** | `["A", "B", "E", "F", "C", "D"]` |
| 7 | G | **G** | `["A", "B", "E", "F", "C", "D", "G"]` |

**Final output:** `["A", "B", "E", "F", "C", "D", "G"]` ✓

### Complexity

- **Time:** `O(n)` · **Space:** `O(h)`

---

## `dfs_postorder` — node after children

### What it does

Fully finishes every child subtree first, then visits the node. Bottom-up DFS.

### Code

```python
def dfs_postorder(node, out=None):
    if out is None:
        out = []
    if node is None:
        return out
    for child in node.children:
        dfs_postorder(child, out)
    out.append(node.val)
    return out
```

### Step-by-step trace (every visit)

| Step | Subtree done | Visit now? | `out` after |
|------|--------------|------------|-------------|
| 1 | E (leaf) | **E** | `["E"]` |
| 2 | F (leaf) | **F** | `["E", "F"]` |
| 3 | B's children done | **B** | `["E", "F", "B"]` |
| 4 | C (leaf) | **C** | `["E", "F", "B", "C"]` |
| 5 | G (leaf) | **G** | `["E", "F", "B", "C", "G"]` |
| 6 | D's children done | **D** | `["E", "F", "B", "C", "G", "D"]` |
| 7 | A's children done | **A** | `["E", "F", "B", "C", "G", "D", "A"]` |

**Final output:** `["E", "F", "B", "C", "G", "D", "A"]` ✓

### Mental model

- Children before parent — same idea as binary post-order, but loop over `children` instead of `left`/`right`.

---

## `bfs` — level-order with a queue

### What it does

Visits nodes row by row using a FIFO queue.

### Code

```python
from collections import deque

def bfs(root):
    order = []
    if root is None:
        return order
    q = deque([root])
    while q:
        node = q.popleft()
        order.append(node.val)
        for child in node.children:
            q.append(child)
    return order
```

### Step-by-step trace

Queue: `[front ... back]` — `popleft` from front.

| Iter | Pop & visit | Enqueue children | `q` after | `order` after |
|------|-------------|------------------|-----------|---------------|
| 1 | **A** | B, C, D | `[B, C, D]` | `["A"]` |
| 2 | **B** | E, F | `[C, D, E, F]` | `["A", "B"]` |
| 3 | **C** | — | `[D, E, F]` | `["A", "B", "C"]` |
| 4 | **D** | G | `[E, F, G]` | `["A", "B", "C", "D"]` |
| 5 | **E** | — | `[F, G]` | `["A", "B", "C", "D", "E"]` |
| 6 | **F** | — | `[G]` | `["A", "B", "C", "D", "E", "F"]` |
| 7 | **G** | — | `[]` | `["A", "B", "C", "D", "E", "F", "G"]` |

**Final output:** `["A", "B", "C", "D", "E", "F", "G"]` ✓

### Complexity

- **Time:** `O(n)` · **Space:** `O(w)` — max width (here 4 at level 1)

---

## `size` — count all nodes

### Code

```python
def size(node):
    if node is None:
        return 0
    return 1 + sum(size(c) for c in node.children)
```

### Trace on node A

| Node | Child sizes | Returns |
|------|-------------|---------|
| E | (leaf) | `1` |
| F | (leaf) | `1` |
| B | E=1, F=1 | `1 + 1 + 1 = 3` |
| C | (leaf) | `1` |
| G | (leaf) | `1` |
| D | G=1 | `1 + 1 = 2` |
| A | B=3, C=1, D=2 | `1 + 3 + 1 + 2 = 7` |

**Final output:** `7` ✓

### Mental model

- `1 + sum(subtree sizes)` — classic "solve subtrees, combine."

---

## `height` — longest path down in edges

### Code

```python
def height(node):
    if node is None:
        return -1
    if not node.children:
        return 0
    return 1 + max(height(c) for c in node.children)
```

### Trace

| Node | Reasoning | Returns |
|------|-----------|---------|
| E, F, C, G | Leaves | `0` |
| B | max(0, 0) + 1 | `1` |
| D | max(0) + 1 | `1` |
| A | max(1, 0, 1) + 1 | `2` |

**Final output:** `2` ✓ (path like A→B→E)

### Common confusions

- Empty tree = `-1` so a single leaf = `0` edges (not `1`).

---

## `count_leaves` — nodes with no children

### Code

```python
def count_leaves(node):
    if node is None:
        return 0
    if not node.children:
        return 1
    return sum(count_leaves(c) for c in node.children)
```

**Leaves:** E, F, C, G → **4** ✓

---

## `find` — search for a value

### Code

```python
def find(node, target):
    if node is None:
        return False
    if node.val == target:
        return True
    return any(find(c, target) for c in node.children)
```

### Trace — `find(A, "G")`

| Step | Node checked | Result |
|------|--------------|--------|
| 1 | A | not G → check children |
| 2 | B subtree | not found |
| 3 | C | not G |
| 4 | D → G | **found** → `True` |

`find(A, "Z")` → `False` ✓

---

## `build_from_rows` — flat list → tree in O(n)

### What it does

Rebuilds a tree from database-style `{id, parent_id}` rows using a hash map.

### Code

```python
def build_from_rows(rows):
    nodes = {r["id"]: Node(r["id"]) for r in rows}
    roots = []
    for r in rows:
        pid = r["parent_id"]
        if pid is None:
            roots.append(nodes[r["id"]])
        else:
            nodes[pid].children.append(nodes[r["id"]])
    return roots
```

### Input (note: C before B — order doesn't matter)

```python
rows = [
    {"id": "A", "parent_id": None},
    {"id": "C", "parent_id": "A"},
    {"id": "B", "parent_id": "A"},
    {"id": "E", "parent_id": "B"},
]
```

### Step-by-step trace

**Phase 1 — build `nodes` map:**

```python
nodes = {"A": Node(A), "C": Node(C), "B": Node(B), "E": Node(E)}
```

| Iter | `r` | `pid` | Action | `roots` |
|------|-----|-------|--------|---------|
| 1 | A | None | append A to roots | `[A]` |
| 2 | C | A | `nodes[A].children.append(C)` | `[A]` |
| 3 | B | A | `nodes[A].children.append(B)` | `[A]` |
| 4 | E | B | `nodes[B].children.append(E)` | `[A]` |

**Result tree:**

```
    A
   / \
  C   B
     /
    E
```

`size(roots[0]) == 4` ✓

### Mental model

- Phase 1: create every node in a dict (O(1) lookup by id).
- Phase 2: one pass — link each node under its parent or mark as root.

### Complexity

- **Time:** `O(n)` · **Space:** `O(n)`

---

## Quick reference

| Function | Technique | Output on canonical tree |
|----------|-----------|--------------------------|
| `dfs_preorder` | Node → children (L→R) | `A,B,E,F,C,D,G` |
| `dfs_postorder` | Children → node | `E,F,B,C,G,D,A` |
| `bfs` | Queue, FIFO | `A,B,C,D,E,F,G` |
| `size` | 1 + sum(children) | `7` |
| `height` | 1 + max(child heights) | `2` |
| `count_leaves` | Leaf = 1, else sum | `4` |
| `find` | Check node, then any child | G=True, Z=False |
| `build_from_rows` | Hash map + one pass | 4-node tree |

## Patterns to remember

- N-ary tree: `children` is a **list**, not `left`/`right`.
- DFS = recursion/stack (deep); BFS = queue (wide).
- Most tree ops: **solve each subtree, combine** (sum, max, any).
- Flat rebuild: index by id first, link in one pass.
