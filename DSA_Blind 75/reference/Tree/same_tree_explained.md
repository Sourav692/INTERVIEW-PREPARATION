# 100. Same Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/same_tree.ipynb`
> **LeetCode:** https://leetcode.com/problems/same-tree/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Parallel DFS | Walk **both** trees in lockstep — compare roots, then left-with-left and right-with-right |
| Recursion | Same logic as the iterative version, but the call stack holds node pairs |
| Explicit stack | Push pairs `(a, b)` instead of recursing |

**Canonical examples** (from notebook asserts):

```
Tree A: [1, 2, 3]          Tree B: [1, 2, 3]     → True (identical)

    1                          1
   / \                        / \
  2   3                      2   3

Tree A: [1, 2]             Tree B: [1, None, 2]  → False (different shape)

    1                          1
   /                            \
  2                              2
```

Expected outputs (from notebook asserts):

| Tree `p` | Tree `q` | `same_rec` | `same_iter` |
| -------- | -------- | ---------- | ----------- |
| `[1, 2, 3]` | `[1, 2, 3]` | `True` | `True` |
| `[1, 2]` | `[1, None, 2]` | `False` | `False` |
| `[]` | `[]` | `True` | `True` |
| `[1, 2, 1]` | `[1, 1, 2]` | `False` | `False` |

---

## `same_rec` — Recursion

### What it does

Compares two nodes at a time. Both empty → match. One empty or values differ → not the same. Otherwise recurse on left-with-left and right-with-right.

### Code

```python
def same_rec(p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
    if not p and not q:
        return True
    if not p or not q or p.val != q.val:
        return False
    return same_rec(p.left, q.left) and same_rec(p.right, q.right)
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not p and not q:` | Both reached `None` at the same position → still matching |
| `if not p or not q or p.val != q.val:` | One side missing, or values differ → trees differ |
| `return False` | Early exit on any mismatch |
| `same_rec(p.left, q.left)` | Left subtrees must also match |
| `same_rec(p.right, q.right)` | Right subtrees must also match |
| `and` | **Both** subtrees must be identical |

### Step-by-step trace — matching trees `[1,2,3]` vs `[1,2,3]`

| Step | Call `(p, q)` | `p.val` / `q.val` | Result |
| ---- | ------------- | ----------------- | ------ |
| 1 | `(1, 1)` | 1 == 1 | recurse left & right |
| 2 | `(2, 2)` | 2 == 2 | recurse (both leaves) |
| 3 | `(None, None)` | both empty | `True` |
| 4 | `(None, None)` | both empty | `True` |
| 5 | back at step 2 | | `True and True` → `True` |
| 6 | `(3, 3)` | 3 == 3 | recurse (both leaves) |
| 7 | `(None, None)` | both empty | `True` |
| 8 | `(None, None)` | both empty | `True` |
| 9 | back at step 6 | | `True` |
| 10 | back at step 1 | | `True and True` → **`True`** |

**Final output:** `True` ✓

### Step-by-step trace — shape mismatch `[1,2]` vs `[1,None,2]`

| Step | Call `(p, q)` | Observation | Result |
| ---- | ------------- | ----------- | ------ |
| 1 | `(1, 1)` | values match | recurse |
| 2 | `(2, None)` | `p` exists, `q` is `None` | **`False`** |

**Final output:** `False` ✓ (left child of 1 exists in `p` but not in `q`)

### Mental model

- Two pointers walking the same path in two trees simultaneously.
- "Same tree" means **same shape AND same values** at every position.
- Think of it as a zip of two pre-order walks that can stop early on mismatch.

### Common confusions

- **Order of checks:** Test both-empty **before** comparing values — `None.val` would crash.
- **Left vs right mix-up:** Must compare `p.left` with `q.left`, not `p.left` with `q.right`.
- **Structural vs value-only:** `[1,2,1]` vs `[1,1,2]` have the same values but different shapes → `False`.

### Complexity

- **Time:** `O(n)` — visit each node at most once (n = nodes in the smaller tree)
- **Space:** `O(h)` — recursion stack depth

---

## `same_iter` — Explicit Stack

### What it does

Same logic as recursion, but stores pairs of nodes on an explicit stack. Pop a pair, compare, push child pairs.

### Code

```python
def same_iter(p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
    stack = [(p, q)]
    while stack:
        a, b = stack.pop()
        if not a and not b:
            continue
        if not a or not b or a.val != b.val:
            return False
        stack.append((a.left, b.left))
        stack.append((a.right, b.right))
    return True
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `stack = [(p, q)]` | Start with the two roots as a pair |
| `while stack:` | Process until no pairs remain |
| `a, b = stack.pop()` | Take the next pair (LIFO — depth-first) |
| `if not a and not b: continue` | Both empty at this position → OK, try other pairs |
| `if not a or not b or a.val != b.val:` | Mismatch → immediate `False` |
| `stack.append((a.left, b.left))` | Schedule left-subtree comparison |
| `stack.append((a.right, b.right))` | Schedule right-subtree comparison |
| `return True` | No mismatches found |

### Step-by-step trace — matching trees `[1,2,3]` vs `[1,2,3]`

Stack notation: `[bottom … top]`

| Step | Action | Stack after |
| ---- | ------ | ----------- |
| 0 | Init | `[(1,1)]` |
| 1 | Pop `(1,1)` — match; push `(2,2)`, `(3,3)` | `[(2,2), (3,3)]` |
| 2 | Pop `(3,3)` — match; push `(None,None)` × 2 | `[(2,2), (None,None), (None,None)]` |
| 3 | Pop `(None,None)` — continue | `[(2,2), (None,None)]` |
| 4 | Pop `(None,None)` — continue | `[(2,2)]` |
| 5 | Pop `(2,2)` — match; push `(None,None)` × 2 | `[(None,None), (None,None)]` |
| 6 | Pop `(None,None)` — continue | `[(None,None)]` |
| 7 | Pop `(None,None)` — continue | `[]` |

Stack empty → **`True`** ✓

### Step-by-step trace — shape mismatch `[1,2]` vs `[1,None,2]`

| Step | Action | Stack after |
| ---- | ------ | ----------- |
| 0 | Init | `[(1,1)]` |
| 1 | Pop `(1,1)` — match; push `(2,None)`, `(None,2)` | `[(2,None), (None,2)]` |
| 2 | Pop `(None,2)` — `a` is `None`, `b` is not → | **`False`** |

**Final output:** `False` ✓

### Mental model

- The stack is a to-do list of "positions to compare."
- `continue` on `(None, None)` means "this branch ended symmetrically — move on."
- Push order (left then right) means right pairs are checked first (LIFO), but the final answer is the same.

### Common confusions

- **`continue` vs `return True`:** `(None, None)` is not a global success — just skip that pair.
- **Stack vs queue:** A stack gives DFS order; a queue would give BFS — both work for correctness.
- **Early `False`:** Any single mismatch anywhere means the whole answer is `False`.

### Complexity

- **Time:** `O(n)`
- **Space:** `O(n)` — stack can hold up to all node pairs in a skewed tree

---

## Quick reference

| Function | Technique | `[1,2,3]` vs `[1,2,3]` | `[1,2]` vs `[1,None,2]` | Time | Space |
| -------- | --------- | ----------------------- | ------------------------ | ---- | ----- |
| `same_rec` | Parallel DFS recursion | `True` | `False` | `O(n)` | `O(h)` |
| `same_iter` | Explicit stack of pairs | `True` | `False` | `O(n)` | `O(n)` |

## Patterns to remember

- **Parallel traversal:** always move both pointers together — same side to same side.
- **Three-case template:** both empty → OK; one empty or values differ → fail; else recurse.
- **Signal words:** identical trees, same structure, mirror check (with different comparison).
- **Related problems:** Symmetric Tree, Subtree of Another Tree, Merge Two Binary Trees.
