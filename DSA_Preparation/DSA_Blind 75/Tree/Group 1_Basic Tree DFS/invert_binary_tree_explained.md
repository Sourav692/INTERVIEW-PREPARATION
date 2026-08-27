# 226. Invert Binary Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/invert_binary_tree.ipynb`
> **LeetCode:** https://leetcode.com/problems/invert-binary-tree/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Visit-and-modify | At **every** node, swap its left and right children |
| DFS recursion | Recursively invert subtrees, then swap (or swap via simultaneous assignment) |
| BFS | Visit each node in level order and swap children in place |

**Canonical example** (from notebook):

```
Before:                    After (mirror):
   4                          4
  / \                        / \
 2   7          →           7   2
/ \ / \                    / \ / \
1 3 6 9                    9 6 3 1
```

Expected outputs (from notebook asserts — checked via `preorder`):

| Input | Expected preorder after invert | `invert_rec` | `invert_bfs` |
| ----- | ------------------------------ | ------------ | ------------ |
| `[4, 2, 7, 1, 3, 6, 9]` | `[4, 7, 2, 9, 6, 3, 1]` | ✓ matches | ✓ matches |
| `[2, 1, 3]` | `[2, 3, 1]` | ✓ matches | ✓ matches |
| `[]` | `[]` (empty) | ✓ matches | ✓ matches |

---

## `invert_rec` — Recursion

### What it does

Base case: empty node returns `None`. Otherwise recursively inverts both subtrees, then assigns them swapped to `root.left` and `root.right`. Returns the (mutated) root.

### Code

```python
def invert_rec(root: Optional[TreeNode]) -> Optional[TreeNode]:
    if not root:
        return None
    root.left, root.right = invert_rec(root.right), invert_rec(root.left)
    return root
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not root: return None` | Nothing to invert at an empty node |
| `invert_rec(root.right)` | Fully invert the right subtree first (evaluated before assignment) |
| `invert_rec(root.left)` | Fully invert the left subtree |
| `root.left, root.right = ...` | **Swap** — old right becomes new left, old left becomes new right |
| `return root` | Return the root of the now-inverted tree |

### Step-by-step trace (canonical tree `[4,2,7,1,3,6,9]`)

Post-order style evaluation — children inverted before parent swaps.

| Step | Call on node | After recursive children | Swap at this node | `left` / `right` after |
| ---- | ------------ | ------------------------ | ----------------- | ---------------------- |
| 1 | `1` (leaf) | — | no children | `None` / `None` |
| 2 | `3` (leaf) | — | no children | `None` / `None` |
| 3 | `2` | children 1, 3 done | swap | `3` / `1` |
| 4 | `6` (leaf) | — | no children | `None` / `None` |
| 5 | `9` (leaf) | — | no children | `None` / `None` |
| 6 | `7` | children 6, 9 done | swap | `9` / `6` |
| 7 | `4` | subtrees 2, 7 done | swap | `7` / `2` |

**Preorder of inverted tree:** `[4, 7, 2, 9, 6, 3, 1]` ✓

### Mental model

- Every node is a hinge — flip its two branches, then the whole tree mirrors.
- The simultaneous assignment `left, right = invert(right), invert(left)` avoids swapping before recursing into already-swapped children.
- Same tree object is mutated in place; the root pointer stays the same node `4`.

### Common confusions

- **Swap then recurse (wrong):** If you swap first and then call `invert_rec(root.left)`, you are actually inverting the old right subtree twice.
- **Forgetting `return root`:** LeetCode expects the root pointer back.
- **Copy vs mutate:** This approach mutates in place — no new nodes created.

### Complexity

- **Time:** `O(n)` — every node visited once
- **Space:** `O(h)` — recursion stack

---

## `invert_bfs` — BFS with a Queue

### What it does

Enqueue the root, then repeatedly dequeue a node, swap its children, and enqueue any non-empty children. Returns the root after all nodes are processed.

### Code

```python
def invert_bfs(root: Optional[TreeNode]) -> Optional[TreeNode]:
    if not root:
        return None
    q = deque([root])
    while q:
        node = q.popleft()
        node.left, node.right = node.right, node.left
        if node.left:
            q.append(node.left)
        if node.right:
            q.append(node.right)
    return root
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not root: return None` | Empty tree edge case |
| `q = deque([root])` | BFS starts at root |
| `node = q.popleft()` | Process front of queue |
| `node.left, node.right = node.right, node.left` | Swap this node's children in place |
| `if node.left: q.append(node.left)` | Enqueue new left (was old right) |
| `if node.right: q.append(node.right)` | Enqueue new right (was old left) |
| `return root` | Root unchanged as a pointer; tree is mirrored |

### Step-by-step trace (canonical tree)

Queue: `[front … back]`. Swap happens **before** enqueuing children.

| Step | Dequeue | Swap children | Queue after enqueue |
| ---- | ------- | ------------- | ----------------- |
| 0 | — | — | `[4]` |
| 1 | `4` | `2↔7` | `[7, 2]` |
| 2 | `7` | `6↔9` | `[2, 9, 6]` |
| 3 | `2` | `1↔3` | `[9, 6, 3, 1]` |
| 4 | `9` | (leaves) | `[6, 3, 1]` |
| 5 | `6` | (leaves) | `[3, 1]` |
| 6 | `3` | (leaves) | `[1]` |
| 7 | `1` | (leaves) | `[]` |

**Preorder of inverted tree:** `[4, 7, 2, 9, 6, 3, 1]` ✓

### Mental model

- Level-by-level mirror: swap at each node as you meet it.
- After swapping at node `4`, enqueue `7` then `2` — they will be swapped themselves when visited.
- Order of traversal does not matter for correctness — every node is swapped exactly once.

### Common confusions

- **Enqueue before vs after swap:** Here we swap first, then enqueue the **new** children (old right becomes left, etc.) — both orders work if you are consistent.
- **BFS does not create a new tree:** Like recursion, it mutates nodes in place.
- **Empty tree:** Must return `None`, not an empty deque.

### Complexity

- **Time:** `O(n)`
- **Space:** `O(n)` — queue holds up to one level

---

## Quick reference

| Function | Technique | Preorder after `[4,2,7,1,3,6,9]` | Time | Space |
| -------- | --------- | ----------------------------------- | ---- | ----- |
| `invert_rec` | DFS post-order swap | `[4, 7, 2, 9, 6, 3, 1]` | `O(n)` | `O(h)` |
| `invert_bfs` | BFS level-order swap | `[4, 7, 2, 9, 6, 3, 1]` | `O(n)` | `O(n)` |

## Patterns to remember

- **Visit-and-modify:** any full traversal works when the local operation is "swap children."
- **Tuple swap:** `a, b = b, a` avoids a temporary variable.
- **Signal words:** mirror, flip, invert, symmetric.
- **Related problems:** Symmetric Tree, Same Tree, Binary Tree Level Order Traversal.
