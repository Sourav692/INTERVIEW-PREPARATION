# 104. Maximum Depth of Binary Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/maximum_depth_of_binary_tree.ipynb`
> **LeetCode:** https://leetcode.com/problems/maximum-depth-of-binary-tree/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| DFS / recursion | Depth = 1 + the deeper of the two children's depths |
| BFS / queue | Peel the tree level by level; count how many levels exist |
| Base case | An empty tree (`None`) has depth **0** |

**Canonical tree** (from notebook example):

```
    3          ← root
   / \
  9  20
     / \
    15  7
```

Expected outputs (from notebook asserts):

| Input (`level-order`) | `max_depth_rec` | `max_depth_bfs` |
| --------------------- | --------------- | --------------- |
| `[3, 9, 20, None, None, 15, 7]` | `3` | `3` |
| `[1, 2]` | `2` | `2` |
| `[]` | `0` | `0` |
| `[1]` | `1` | `1` |

---

## `max_depth_rec` — Recursion / DFS

### What it does

Recursively asks each subtree "how tall are you?" and returns 1 plus the taller child's answer. An empty node contributes depth 0.

### Code

```python
def max_depth_rec(root: Optional[TreeNode]) -> int:
    if not root:
        return 0
    return 1 + max(max_depth_rec(root.left), max_depth_rec(root.right))
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not root:` | Base case — no node means zero height |
| `return 0` | Empty subtree contributes nothing to depth |
| `1 + max(...)` | This node adds one level on top of its taller child |
| `max_depth_rec(root.left)` | Recurse into the left subtree |
| `max_depth_rec(root.right)` | Recurse into the right subtree |
| `max(...)` | Take the deeper of the two children |

### Step-by-step trace (canonical tree)

Tree: `3` (left `9`, right `20` → `15`, `7`). Calls listed in evaluation order.

| Step | Call enters | Left child depth | Right child depth | Returns |
| ---- | ----------- | ---------------- | ----------------- | ------- |
| 1 | `max_depth_rec(9)` | 0 (no children) | 0 (no children) | `1` |
| 2 | `max_depth_rec(15)` | 0 | 0 | `1` |
| 3 | `max_depth_rec(7)` | 0 | 0 | `1` |
| 4 | `max_depth_rec(20)` | 1 (from step 2) | 1 (from step 3) | `1 + max(1,1) = 2` |
| 5 | `max_depth_rec(3)` | 1 (from step 1) | 2 (from step 4) | `1 + max(1,2) = 3` |

**Final output on canonical tree:** `3` ✓

### Mental model

- Ask every leaf "how deep?" → answer is 1.
- On the way back up, each parent adds 1 to whichever child reported a taller subtree.
- The root's final answer is the longest root-to-leaf path counted in **nodes**.

### Common confusions

- **Depth vs edges:** LeetCode counts **nodes** on the path (root = 1), not edges. A single-node tree has depth 1, not 0.
- **Forgetting the base case:** Without `if not root: return 0`, you recurse into `None` and crash.
- **`max` of children:** You need the **taller** subtree, not the sum of both.

### Complexity

- **Time:** `O(n)` — every node visited once
- **Space:** `O(h)` — recursion stack depth equals tree height (`h`)

---

## `max_depth_bfs` — BFS with a Queue

### What it does

Processes the tree one level at a time using a queue. Each time the queue is drained (after a snapshot of its size), increment the depth counter.

### Code

```python
def max_depth_bfs(root: Optional[TreeNode]) -> int:
    if not root:
        return 0
    q = deque([root])
    depth = 0
    while q:
        depth += 1
        for _ in range(len(q)):
            node = q.popleft()
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
    return depth
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not root: return 0` | Empty tree → depth 0 |
| `q = deque([root])` | Queue starts with the root on level 1 |
| `depth = 0` | Level counter |
| `while q:` | Keep going while nodes remain |
| `depth += 1` | About to process one full level |
| `for _ in range(len(q)):` | Snapshot current level size — only process nodes already in the queue |
| `node = q.popleft()` | Take the front node from the queue |
| `q.append(node.left/right)` | Enqueue children for the **next** level |

### Step-by-step trace (canonical tree)

Queue notation: `[front … back]`

| Iteration | `depth` (start) | Action | Queue after |
| --------- | --------------- | ------ | ----------- |
| — | 0 | Init | `[3]` |
| **Level 1** | | | |
| 1a | → 1 | `popleft` 3; enqueue 9, 20 | `[9, 20]` |
| **Level 2** | | | |
| 2a | → 2 | `popleft` 9; no children | `[20]` |
| 2b | | `popleft` 20; enqueue 15, 7 | `[15, 7]` |
| **Level 3** | | | |
| 3a | → 3 | `popleft` 15; no children | `[7]` |
| 3b | | `popleft` 7; no children | `[]` |

`while q` exits (queue empty). **Final output:** `depth = 3` ✓

### Mental model

- The queue always holds "the current frontier" of the tree.
- `len(q)` before each level's inner loop freezes how many nodes belong to **this** level.
- Each pass through the outer `while` = one more level discovered.

### Common confusions

- **Not snapshotting `len(q)`:** If you iterate `while q` without the inner `for _ in range(len(q))`, you mix levels and under-count depth.
- **Empty tree:** Must return 0 before creating the queue — `[None]` is not the same as `[]`.
- **BFS space:** Queue can hold up to one full level (`O(n)` in a wide tree), not `O(h)` like recursion.

### Complexity

- **Time:** `O(n)` — every node enqueued and dequeued once
- **Space:** `O(n)` — queue holds up to one complete level

---

## Quick reference

| Function | Technique | Output on `[3,9,20,None,None,15,7]` | Time | Space |
| -------- | --------- | ------------------------------------- | ---- | ----- |
| `max_depth_rec` | DFS recursion | `3` | `O(n)` | `O(h)` |
| `max_depth_bfs` | BFS level-order | `3` | `O(n)` | `O(n)` |

## Patterns to remember

- **Tree recursion template:** answer at a node = combine answers from children (`1 + max(left, right)`).
- **BFS level counting:** snapshot `len(queue)` per level; increment a counter each outer loop.
- **Signal words:** depth, height, levels, longest root-to-leaf path.
- **Related problems:** Minimum Depth, Balanced Binary Tree, Level Order Traversal.
