# Lowest Common Ancestor of a BST — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/lowest_common_ancestor_of_a_bst.ipynb`  
> **LeetCode:** [235. Lowest Common Ancestor of a Binary Search Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/)  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| BST ordering | Left subtree values are smaller; right subtree values are larger |
| LCA definition | Deepest node that has **both** `p` and `q` in its subtrees |
| Walk strategy | If both targets are smaller → go left; both larger → go right; else you're at the split |
| Complexity | `O(h)` time where `h` is height; iterative uses `O(1)` extra space |

**Canonical BST from level-order `[6, 2, 8, 0, 4, 7, 9]`:**

```
        6
       / \
      2   8
     / \ / \
    0  4 7  9
```

Expected outputs (from notebook asserts):

| Call | Expected |
|------|----------|
| `lca_iter(root, 2, 8)` | `6` |
| `lca_iter(root, 2, 4)` | `2` |
| `lca_iter(root, 7, 9)` | `8` |
| `lca_iter(root, 0, 4)` | `2` |
| `lca_rec(...)` | Same values for all four cases |

---

## `lca_iter` — iterative walk using BST ordering

### What it does

Walks down from the root using BST comparisons until the two targets would diverge (one on each side) or one target equals the current node — that node is the lowest common ancestor.

### Code

```python
def lca_iter(root: Optional[TreeNode], p: int, q: int) -> int:
    node = root
    while node:
        if p < node.val and q < node.val:  # both targets are smaller -> go left
            node = node.left
        elif p > node.val and q > node.val:# both targets are larger -> go right
            node = node.right
        else:                              # they split here (one each side, or equal)
            return node.val                # this is the lowest common ancestor
    return -1
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `node = root` | Start at the root; we'll walk down without recursion |
| `while node:` | Keep going while we haven't fallen off the tree |
| `p < node.val and q < node.val` | Both targets are strictly smaller → LCA must be in the left subtree |
| `node = node.left` | Move left and repeat the check |
| `p > node.val and q > node.val` | Both targets are strictly larger → LCA must be in the right subtree |
| `node = node.right` | Move right and repeat |
| `else: return node.val` | Targets split here (one left, one right) **or** one equals `node.val` — this is the answer |
| `return -1` | Safety fallback if the tree is empty (not hit in normal LeetCode inputs) |

### Step-by-step trace — `lca_iter(root, 2, 8)` → `6`

**Input / tree:**

```
        6  ← start
       / \
      2   8
     / \ / \
    0  4 7  9
```

**Initial state:**

| Variable | Value |
|----------|-------|
| `node` | `6` |
| `p`, `q` | `2`, `8` |

| Iter | Action | `node` | Condition | Result |
|------|--------|--------|-----------|--------|
| start | Begin at root | **6** | — | continue |
| 1 | `2 < 6` but `8 > 6` → neither "both smaller" nor "both larger" | **6** | split / equal case | **return 6** |

**Final output:** `6` ✓ (matches notebook assert for `p=2, q=8`)

---

### Step-by-step trace — `lca_iter(root, 2, 4)` → `2`

| Iter | Action | `node` | Condition | Result |
|------|--------|--------|-----------|--------|
| start | Begin at root | **6** | `2<6` and `4<6` → both smaller | go left |
| 1 | Move left | **2** | `2==2` (not both smaller, not both larger) | **return 2** |

**Final output:** `2` ✓ (matches notebook assert for `p=2, q=4`)

---

### Step-by-step trace — `lca_iter(root, 7, 9)` → `8`

| Iter | Action | `node` | Condition | Result |
|------|--------|--------|-----------|--------|
| start | Begin at root | **6** | `7>6` and `9>6` → both larger | go right |
| 1 | Move right | **8** | `7<8` but `9>8` → split | **return 8** |

**Final output:** `8` ✓ (matches notebook assert for `p=7, q=9`)

---

### Step-by-step trace — `lca_iter(root, 0, 4)` → `2`

| Iter | Action | `node` | Condition | Result |
|------|--------|--------|-----------|--------|
| start | Begin at root | **6** | `0<6` and `4<6` → both smaller | go left |
| 1 | Move left | **2** | `0<2` and `4>2` → split | **return 2** |

**Final output:** `2` ✓ (matches notebook assert for `p=0, q=4`)

### Mental model

- The LCA is the **first node where the two targets stop agreeing on direction** — one wants left, one wants right, or one *is* the current node.
- BST ordering lets you ignore entire subtrees; you never backtrack.

### Common confusions

- **One target equals the current node:** e.g. `p=2, q=4` at node `2` — the `else` branch fires because `2` is not strictly less than `2`, so you correctly return `2` (a node is an ancestor of itself).
- **BST LCA vs general tree LCA:** this problem is much simpler because you never need to search both subtrees; the general binary-tree version requires a different algorithm.

### Complexity

- **Time:** `O(h)` — one downward walk, height `h`
- **Space:** `O(1)` — only a pointer, no recursion stack

---

## `lca_rec` — same rule, expressed recursively

### What it does

Recursively descends into the left or right subtree when both targets lie on the same side; otherwise returns the current node's value as the LCA.

### Code

```python
def lca_rec(root: Optional[TreeNode], p: int, q: int) -> int:
    if p < root.val and q < root.val:      # both smaller -> answer is in the left subtree
        return lca_rec(root.left, p, q)
    if p > root.val and q > root.val:      # both larger -> answer is in the right subtree
        return lca_rec(root.right, p, q)
    return root.val                        # the split point is the lowest common ancestor
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `p < root.val and q < root.val` | Both targets are in the left subtree |
| `return lca_rec(root.left, p, q)` | Delegate to the left child; the answer bubbles up unchanged |
| `p > root.val and q > root.val` | Both targets are in the right subtree |
| `return lca_rec(root.right, p, q)` | Delegate to the right child |
| `return root.val` | Neither branch taken → split point (or target equals root) → return here |

### Step-by-step trace — `lca_rec(root, 2, 8)` → `6`

**Call stack (enter top → bottom, return bottom → top):**

| Step | Call | Condition | Action |
|------|------|-----------|--------|
| 1 | `lca_rec(6, 2, 8)` | not both < 6, not both > 6 | **return 6** |

**Final output:** `6` ✓

---

### Step-by-step trace — `lca_rec(root, 2, 4)` → `2`

| Step | Call | Condition | Action |
|------|------|-----------|--------|
| 1 | `lca_rec(6, 2, 4)` | both < 6 | recurse left |
| 2 | `lca_rec(2, 2, 4)` | split (2 not < 2) | **return 2** |
| 3 | unwind step 1 | receives `2` | **return 2** |

**Final output:** `2` ✓

---

### Step-by-step trace — `lca_rec(root, 7, 9)` → `8`

| Step | Call | Condition | Action |
|------|------|-----------|--------|
| 1 | `lca_rec(6, 7, 9)` | both > 6 | recurse right |
| 2 | `lca_rec(8, 7, 9)` | split | **return 8** |
| 3 | unwind step 1 | receives `8` | **return 8** |

**Final output:** `8` ✓

---

### Step-by-step trace — `lca_rec(root, 0, 4)` → `2`

| Step | Call | Condition | Action |
|------|------|-----------|--------|
| 1 | `lca_rec(6, 0, 4)` | both < 6 | recurse left |
| 2 | `lca_rec(2, 0, 4)` | split (`0<2`, `4>2`) | **return 2** |
| 3 | unwind step 1 | receives `2` | **return 2** |

**Final output:** `2` ✓ (all four notebook tests: `iter == rec == expected`)

### Mental model

- Identical logic to the iterative version — recursion is just "call myself on the child I'd walk to."
- The base case is implicit: when you stop recursing, you return `root.val`.

### Common confusions

- **Assumes non-empty tree:** `root` is never `None` in valid LeetCode inputs (both `p` and `q` exist in the tree).
- **Return value propagates unchanged:** inner calls return the final LCA value; outer calls just pass it up.

### Complexity

- **Time:** `O(h)` — one path from root to answer
- **Space:** `O(h)` — recursion call stack depth equals tree height

---

## Quick reference

| Function | Technique | `LCA(2,8)` | `LCA(2,4)` | `LCA(7,9)` | `LCA(0,4)` |
|----------|-----------|------------|------------|------------|------------|
| `lca_iter` | Iterative BST walk | `6` | `2` | `8` | `2` |
| `lca_rec` | Recursive BST walk | `6` | `2` | `8` | `2` |

## Patterns to remember

- **Exploit BST ordering to prune:** never explore a branch that can't contain both targets.
- **LCA = the split point:** first node where targets diverge (or one equals the node).
- **Signal phrases:** "lowest common ancestor in a BST", "where do two paths meet".
