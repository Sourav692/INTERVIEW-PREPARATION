# Validate Binary Search Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/validate_binary_search_tree.ipynb`  
> **LeetCode:** [98. Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/)  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| BST rule | Every node must be **strictly** greater than all left descendants and **strictly** less than all right descendants |
| Range bounds | Pass `(low, high)` down recursion — going left tightens `high`, going right tightens `low` |
| In-order shortcut | BST in-order traversal yields **strictly increasing** values |
| Signal words | "valid BST", "is this ordered correctly" |

**Trees used in this doc:**

Valid BST `[2,1,3]`:

```
      2          ← root
     / \
    1   3
```

Invalid BST `[5,1,4,None,None,3,6]`:

```
      5          ← root
     / \
    1   4        ← 4 is in RIGHT subtree of 5 but 4 < 5 → invalid
       / \
      3   6
```

---

## `is_valid_bounds` — range bounds recursion

### What it does

Checks every node fits within a valid `(low, high)` window inherited from ancestors, not just its direct parent.

### Code

```python
def is_valid_bounds(root: Optional[TreeNode]) -> bool:
    def valid(node, low, high):            # node's value must stay strictly inside (low, high)
        if not node:
            return True                    # empty subtree is fine
        if not (low < node.val < high):    # out of its allowed range -> not a BST
            return False
        # Going left tightens the upper bound; going right tightens the lower bound.
        return valid(node.left, low, node.val) and valid(node.right, node.val, high)
    return valid(root, float("-inf"), float("inf"))
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `def valid(node, low, high):` | Inner helper — node must satisfy `low < val < high` |
| `if not node: return True` | Empty subtree is valid |
| `if not (low < node.val < high):` | Strict inequality — duplicates not allowed |
| `return False` | This node violates the ancestor-imposed range |
| `valid(node.left, low, node.val)` | Left child must be **less than** current node → tighten upper bound to `node.val` |
| `valid(node.right, node.val, high)` | Right child must be **greater than** current node → tighten lower bound to `node.val` |
| `return valid(root, -inf, inf)` | Root has no ancestor constraints — unbounded range |

### Step-by-step trace — valid tree `[2,1,3]`

```
      2
     / \
    1   3
```

| Step | Call | `low` | `high` | `node.val` | Check | Result |
|------|------|-------|--------|------------|-------|--------|
| 1 | `valid(2, -∞, +∞)` | -∞ | +∞ | 2 | -∞ < 2 < +∞ ✓ | continue |
| 2 | `valid(1, -∞, 2)` | -∞ | 2 | 1 | -∞ < 1 < 2 ✓ | continue |
| 3 | `valid(None, ...)` | — | — | — | empty | `True` |
| 4 | `valid(None, ...)` | — | — | — | empty | `True` |
| 5 | → step 2 returns | | | | | `True` |
| 6 | `valid(3, 2, +∞)` | 2 | +∞ | 3 | 2 < 3 < +∞ ✓ | continue |
| 7 | `valid(None, ...)` | — | — | — | empty | `True` |
| 8 | `valid(None, ...)` | — | — | — | empty | `True` |
| 9 | → step 6 returns | | | | | `True` |
| 10 | → step 1 returns | | | | | `True` |

**Final output:** `True` ✓

### Step-by-step trace — invalid tree `[5,1,4,None,None,3,6]`

```
      5
     / \
    1   4
       / \
      3   6
```

| Step | Call | `low` | `high` | `node.val` | Check | Result |
|------|------|-------|--------|------------|-------|--------|
| 1 | `valid(5, -∞, +∞)` | -∞ | +∞ | 5 | ✓ | continue |
| 2 | `valid(1, -∞, 5)` | -∞ | 5 | 1 | ✓ | `True` (leaf) |
| 3 | `valid(4, 5, +∞)` | **5** | +∞ | **4** | 5 < 4? **✗** | **`False`** |

**Final output:** `False` ✓ — node 4 is in the right subtree of 5 but `4 < 5`

### Mental model

- A BST constraint is **global within each subtree**, not local to the parent. Node 4 can satisfy `1 < 4` (parent check) but still fail `4 > 5` (ancestor range).
- Think of narrowing corridors: each step down the tree shrinks the allowed interval.

### Common confusions

- **Only comparing to direct parent** — `[5, 1, 4, ...]` passes parent checks (1 < 5, 4 > 1) but fails because 4 is in 5's right subtree.
- **`<=` vs `<`** — LeetCode requires **strict** ordering; `<=` would incorrectly allow duplicates.
- **Using `node.val` as bound when value is `±inf` edge** — with `float("-inf")` / `float("inf")`, strict inequalities still work for any finite node value.

### Complexity

- **Time:** `O(n)` — every node visited once
- **Space:** `O(h)` — recursion stack depth = tree height

---

## `is_valid_inorder` — in-order must be sorted

### What it does

Iteratively performs in-order traversal and checks each value is strictly greater than the previous — a BST iff in-order is strictly increasing.

### Code

```python
def is_valid_inorder(root: Optional[TreeNode]) -> bool:
    stack, prev, node = [], float("-inf"), root   # prev = last value visited in order
    while stack or node:
        while node:                        # go as far left as possible first
            stack.append(node); node = node.left
        node = stack.pop()                 # visit the smallest unvisited node
        if node.val <= prev:               # values must strictly increase in a BST
            return False
        prev = node.val                    # remember this value for the next comparison
        node = node.right                  # then explore the right subtree
    return True
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `stack, prev, node = [], -inf, root` | `prev` starts below any possible value; `node` begins at root |
| `while stack or node:` | Continue until all nodes visited |
| `while node: stack.append(node); node = node.left` | Push path to leftmost unvisited node |
| `node = stack.pop()` | **Visit** — smallest unvisited value |
| `if node.val <= prev: return False` | Not strictly increasing → not a BST |
| `prev = node.val` | Update the "last seen" value |
| `node = node.right` | Move to right subtree (next in-order values are larger) |
| `return True` | Every value was strictly increasing |

### Step-by-step trace — valid tree `[2,1,3]`

In-order visit order: 1 → 2 → 3

| Iter | Action | `stack` (bottom→top) | `node` | `prev` | Check |
|------|--------|----------------------|--------|--------|-------|
| 1 | dive left from 2: push 2,1 | `[2, 1]` | `None` | -∞ | — |
| 2 | pop **1**, visit | `[2]` | `None` | -∞ | 1 > -∞ ✓, `prev=1` |
| 3 | pop **2**, visit | `[]` | `3` | 1 | 2 > 1 ✓, `prev=2` |
| 4 | dive left from 3: push 3 | `[3]` | `None` | 2 | — |
| 5 | pop **3**, visit | `[]` | `None` | 2 | 3 > 2 ✓, `prev=3` |
| done | stack and node empty | `[]` | `None` | 3 | return `True` |

**Final output:** `True` ✓

### Step-by-step trace — invalid tree `[5,1,4,None,None,3,6]`

In-order visit order: 1 → 5 → 3 → 4 → 6

| Iter | Action | `stack` | `node` | `prev` | Check |
|------|--------|---------|--------|--------|-------|
| 1 | dive left: push 5,1 | `[5, 1]` | `None` | -∞ | — |
| 2 | pop **1**, visit | `[5]` | `None` | -∞ | 1 > -∞ ✓, `prev=1` |
| 3 | pop **5**, visit | `[]` | `4` | 1 | 5 > 1 ✓, `prev=5` |
| 4 | dive left from 4: push 4,3 | `[4, 3]` | `None` | 5 | — |
| 5 | pop **3**, visit | `[4]` | `None` | 5 | **3 ≤ 5 ✗** | **`False`** |

**Final output:** `False` ✓ — in-order is `[1, 5, 3, 4, 6]`, not strictly increasing

### Mental model

- In-order on a BST = sorted order. If the walk ever steps backward (or repeats), the tree isn't a BST.
- `prev` is a one-element memory of "what was the last value I output?" — O(1) extra state.

### Common confusions

- **In-order is sorted only on a BST** — on a generic binary tree, in-order is not sorted; this trick is BST-specific.
- **`prev` initialization** — use `-inf` (or `None` with a flag) so the first node always passes.
- **Iterative vs recursive in-order** — both work; iterative avoids recursion depth issues on skewed trees.

### Complexity

- **Time:** `O(n)` — every node pushed/popped once
- **Space:** `O(h)` — stack holds at most height nodes

---

## Quick reference

| Function | Technique | `[2,1,3]` | `[5,1,4,None,None,3,6]` |
|----------|-----------|-----------|-------------------------|
| `is_valid_bounds` | Range recursion | `True` | `False` |
| `is_valid_inorder` | In-order monotonicity | `True` | `False` |

## Patterns to remember

- **Pass constraints down** — a node's validity depends on all ancestors, not just its parent.
- **In-order = sorted for BST** — powerful shortcut reused in Kth Smallest, BST Iterator, Recover BST.
- **Strict inequalities** — duplicates break BST validity on LeetCode.
- **Related problems:** Kth Smallest Element in a BST, Recover BST, Range Sum of BST.
