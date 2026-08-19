# Binary Tree Level Order Traversal — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/binary_tree_level_order_traversal.ipynb`  
> **LeetCode:** [102. Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/)  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| BFS with queue | Process one full level at a time — queue holds exactly the current frontier |
| Snapshot trick | `for _ in range(len(q))` freezes the level size before children are appended |
| DFS by depth | Recurse with a depth counter; append each value to `res[depth]` |
| Signal words | "level order", "by depth", "row by row", "zigzag level order" |

**Canonical tree used throughout** (from notebook assert `[3,9,20,None,None,15,7]`):

```
        3          ← root
       / \
      9  20
        /  \
      15    7
```

Expected output: `[[3], [9, 20], [15, 7]]`

---

## `level_order_bfs` — BFS with a queue (natural approach)

### What it does

Returns node values grouped by level, top to bottom, left to right, using a queue to expand one level at a time.

### Code

```python
def level_order_bfs(root: Optional[TreeNode]) -> List[List[int]]:
    res = []
    if not root:
        return res
    q = deque([root])
    while q:
        level = []                         # values collected for the current level
        for _ in range(len(q)):            # snapshot: current queue = exactly one level
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)   # push the next level's nodes
            if node.right: q.append(node.right)
        res.append(level)                  # store this finished level
    return res
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `res = []` | Accumulates one inner list per level |
| `if not root: return res` | Empty tree → return `[]` (not `[[]]`) |
| `q = deque([root])` | Seed the queue with the root — level 0 |
| `while q:` | Keep going until no nodes remain |
| `level = []` | Fresh list for the current level's values |
| `for _ in range(len(q)):` | **Snapshot** — only process nodes that were in the queue at the start of this iteration (one full level) |
| `node = q.popleft()` | Take the front node (FIFO) |
| `level.append(node.val)` | Record this node's value in the current level |
| `if node.left: q.append(node.left)` | Enqueue left child for the **next** level |
| `if node.right: q.append(node.right)` | Enqueue right child for the **next** level |
| `res.append(level)` | Store the finished level before starting the next |
| `return res` | All levels collected |

### Step-by-step trace

**Input tree:**

```
        3
       / \
      9  20
        /  \
      15    7
```

**Initial state:**

| Variable | Value |
|----------|-------|
| `q` | `[3]` (front ← → back) |
| `res` | `[]` |

| Iter (outer) | Inner step | Action | `q` after | `level` | `res` after |
|--------------|------------|--------|-----------|---------|-------------|
| 1 | start | `len(q)=1`, begin level 0 | `[3]` | `[]` | `[]` |
| 1 | 1 | popleft **3**, enqueue 9, 20 | `[9, 20]` | `[3]` | `[]` |
| 1 | end | append level | `[9, 20]` | — | `[[3]]` |
| 2 | start | `len(q)=2`, begin level 1 | `[9, 20]` | `[]` | `[[3]]` |
| 2 | 1 | popleft **9** (no children) | `[20]` | `[9]` | `[[3]]` |
| 2 | 2 | popleft **20**, enqueue 15, 7 | `[15, 7]` | `[9, 20]` | `[[3]]` |
| 2 | end | append level | `[15, 7]` | — | `[[3], [9, 20]]` |
| 3 | start | `len(q)=2`, begin level 2 | `[15, 7]` | `[]` | `[[3], [9, 20]]` |
| 3 | 1 | popleft **15** (no children) | `[7]` | `[15]` | `[[3], [9, 20]]` |
| 3 | 2 | popleft **7** (no children) | `[]` | `[15, 7]` | `[[3], [9, 20]]` |
| 3 | end | append level | `[]` | — | `[[3], [9, 20], [15, 7]]` |
| done | — | `q` empty, exit loop | `[]` | — | `[[3], [9, 20], [15, 7]]` |

**Final output:** `[[3], [9, 20], [15, 7]]` ✓ (matches notebook assert)

### Mental model

- The queue is a **sliding window** of the current frontier. Each outer `while` pass drains exactly one row and fills the queue with the next row's nodes.
- The `len(q)` snapshot is the key trick — without it, newly appended children would get processed in the same iteration, mixing levels.

### Common confusions

- **Reading `len(q)` inside the inner loop after appends** — the size grows as you enqueue children; capture it once with `range(len(q))` at the start.
- **Empty tree** — return `[]`, not `[[]]`.
- **Single-node tree `[1]`** — one outer iteration, one inner step → `[[1]]`.

### Complexity

- **Time:** `O(n)` — every node dequeued and enqueued once
- **Space:** `O(n)` — queue can hold up to one full level (worst case: last level of a complete tree ≈ n/2 nodes)

---

## `level_order_dfs` — DFS tagged by depth

### What it does

Recursively walks the tree, appending each node's value to `res[depth]`, producing the same level-grouped output without a queue.

### Code

```python
def level_order_dfs(root: Optional[TreeNode]) -> List[List[int]]:
    res = []
    def dfs(node, depth):
        if not node:
            return
        if depth == len(res):              # first time we reach this depth...
            res.append([])                 # ...create its (empty) list
        res[depth].append(node.val)        # add this node's value to its depth's list
        dfs(node.left, depth + 1)          # children live one level deeper
        dfs(node.right, depth + 1)
    dfs(root, 0)
    return res
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `res = []` | Outer list of per-level lists |
| `def dfs(node, depth):` | Inner recursive helper; `depth` = 0 at root |
| `if not node: return` | Base case — empty subtree |
| `if depth == len(res):` | First visit to this depth means no list exists yet |
| `res.append([])` | Create a new empty level list |
| `res[depth].append(node.val)` | Place this node's value at its depth (left-to-right order preserved because left is visited first) |
| `dfs(node.left, depth + 1)` | Recurse into left child one level deeper |
| `dfs(node.right, depth + 1)` | Then right child |
| `dfs(root, 0)` | Kick off from root at depth 0 |
| `return res` | All levels built |

### Step-by-step trace (every visit)

**Input tree:** same as above.

| Step | Call | Depth | Action | `res` after |
|------|------|-------|--------|-------------|
| 1 | `dfs(3, 0)` | 0 | create `res[0]`, append **3** | `[[3]]` |
| 2 | `dfs(9, 1)` | 1 | create `res[1]`, append **9** | `[[3], [9]]` |
| 3 | `dfs(None, 2)` | 2 | return (base case) | `[[3], [9]]` |
| 4 | `dfs(None, 2)` | 2 | return (base case) | `[[3], [9]]` |
| 5 | `dfs(20, 1)` | 1 | append **20** to existing `res[1]` | `[[3], [9, 20]]` |
| 6 | `dfs(15, 2)` | 2 | create `res[2]`, append **15** | `[[3], [9, 20], [15]]` |
| 7 | `dfs(None, 3)` | 3 | return | `[[3], [9, 20], [15]]` |
| 8 | `dfs(None, 3)` | 3 | return | `[[3], [9, 20], [15]]` |
| 9 | `dfs(7, 2)` | 2 | append **7** to existing `res[2]` | `[[3], [9, 20], [15, 7]]` |
| 10 | `dfs(None, 3)` | 3 | return | `[[3], [9, 20], [15, 7]]` |
| 11 | `dfs(None, 3)` | 3 | return | `[[3], [9, 20], [15, 7]]` |

**Final output:** `[[3], [9, 20], [15, 7]]` ✓ (matches notebook assert)

### Mental model

- Think of `res` as a **row of buckets** indexed by depth. The first time you arrive at a depth, you add a new bucket. Visiting left before right keeps values left-to-right within each bucket.
- This is DFS in **pre-order** visit order, but the output is organized by depth instead of a flat list.

### Common confusions

- **`depth == len(res)` vs `depth > len(res)`** — equality is correct; you create a new list exactly when you first reach a depth that doesn't exist yet.
- **Empty root** — `dfs(None, 0)` returns immediately; `res` stays `[]`.
- **BFS vs DFS space** — DFS uses `O(h)` call-stack space (height); BFS uses `O(w)` queue space (max width). For a balanced tree BFS queue is wider; for a skewed tree DFS stack is deeper.

### Complexity

- **Time:** `O(n)` — every node visited once
- **Space:** `O(h)` for recursion stack (+ `O(n)` for output, which both approaches need)

---

## Quick reference

| Function | Technique | Output on canonical tree |
|----------|-----------|--------------------------|
| `level_order_bfs` | Queue + level snapshot | `[[3], [9, 20], [15, 7]]` |
| `level_order_dfs` | Recursion + depth index | `[[3], [9, 20], [15, 7]]` |

## Patterns to remember

- **BFS = level-by-level** — whenever grouping or distance-by-levels matters, reach for a queue.
- **Snapshot `len(q)`** — cleanly separates one level from the next without mixing children into the current pass.
- **DFS depth tagging** — alternative when you want `O(h)` auxiliary space instead of `O(width)`.
- **Related problems:** Zigzag Level Order, Right Side View, Minimum Depth of Binary Tree.
