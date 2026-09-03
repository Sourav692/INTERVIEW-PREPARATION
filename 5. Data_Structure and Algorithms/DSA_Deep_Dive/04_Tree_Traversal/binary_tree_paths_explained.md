# 257. Binary Tree Paths — Step-by-Step Reference

> **Source notebook:** `DSA_Deep_Dive/04_Tree_Traversal/1. bfs_dfs_pattern_playbook.ipynb` (Part 3.1 — the baseline)
> **LeetCode:** https://leetcode.com/problems/binary-tree-paths/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Backtracking along a path | Build up a shared list one child at a time (`CHOOSE`), recurse into it (`RECURSE`), then undo that choice (`UN-CHOOSE`) so sibling branches start clean |
| When to record | Only at a **leaf** — a node with no `left` and no `right` — is the current path a finished, real root-to-leaf path |
| Shared mutable `path` | One list threaded through every recursive call; append before going down, pop after coming back up |
| Closure / nested function | `backtrack` is defined *inside* `binary_tree_paths` so it can read and mutate `out` and `path` without passing them as arguments |

**Canonical example** (from notebook):

```
build_tree([1, 2, 3, None, 5])

        1
       / \
      2   3
       \
        5

-> ['1->2->5', '1->3']
```

Expected output (from notebook print):

| Input | Expected | `binary_tree_paths` |
| ----- | -------- | -------------------- |
| `build_tree([1, 2, 3, None, 5])` | `['1->2->5', '1->3']` | ✓ matches |

---

## `binary_tree_paths` — Backtrack Along Root-to-Leaf Paths

### What it does

Starts `path` with the root's value already in it. A nested helper, `backtrack`, walks the tree: at a leaf it joins the current `path` with `"->"` and saves it into `out`; at any other node it loops over whichever children exist, appending each child's value before recursing into it and popping that value back off once the recursion returns. Because `path` is popped after every child, one node's children never see leftovers from a sibling's exploration.

### Code

```python
def binary_tree_paths(root):
    if not root:
        return []
    out, path = [], [str(root.val)]
    def backtrack(node):
        if not node.left and not node.right:
            out.append("->".join(path))         # RECORD - reached a leaf
            return
        for nxt in (node.left, node.right):
            if nxt:
                path.append(str(nxt.val))         # CHOOSE
                backtrack(nxt)                      # RECURSE
                path.pop()                          # UN-CHOOSE
    backtrack(root)
    return out
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not root: return []` | Empty tree has no paths at all |
| `out, path = [], [str(root.val)]` | `out` collects finished paths; `path` starts already holding the root |
| `def backtrack(node):` | Nested closure — shares `out` and `path` with the outer function, no arguments needed for them |
| `if not node.left and not node.right:` | Leaf check — no children means this branch is finished |
| `out.append("->".join(path))` | RECORD — join the breadcrumb trail into `"1->2->5"`-style string |
| `return` | Leaf never loops over children — nothing left to choose |
| `for nxt in (node.left, node.right):` | Try left child, then right child |
| `if nxt:` | Skip a `None` child (missing branch) |
| `path.append(str(nxt.val))` | CHOOSE — step into `nxt`, path now reflects "root ... nxt" |
| `backtrack(nxt)` | RECURSE — explore everything below `nxt` |
| `path.pop()` | UN-CHOOSE — remove `nxt` so the *next* sibling starts from a clean path |
| `backtrack(root)` | Kick off the walk from the root |
| `return out` | All recorded root-to-leaf paths |

### Step-by-step trace (canonical example `build_tree([1, 2, 3, None, 5])`)

Initial state: `out = []`, `path = ["1"]`, call `backtrack(1)`.

| Step | Call / action | `path` after | `out` after |
| ---- | -------------- | ------------- | ------------ |
| 1 | `backtrack(1)` — has children `(2, 3)`, not a leaf, loop starts | `["1"]` | `[]` |
| 2 | CHOOSE `2` — `path.append("2")` | `["1", "2"]` | `[]` |
| 3 | `backtrack(2)` — has `right=5`, not a leaf, loop skips `None` left | `["1", "2"]` | `[]` |
| 4 | CHOOSE `5` — `path.append("5")` | `["1", "2", "5"]` | `[]` |
| 5 | `backtrack(5)` — leaf, RECORD `"1->2->5"` | `["1", "2", "5"]` | `["1->2->5"]` |
| 6 | UN-CHOOSE — `path.pop()` (back in `backtrack(2)`, loop ends) | `["1", "2"]` | `["1->2->5"]` |
| 7 | UN-CHOOSE — `path.pop()` (back in `backtrack(1)`, loop moves to `3`) | `["1"]` | `["1->2->5"]` |
| 8 | CHOOSE `3` — `path.append("3")` | `["1", "3"]` | `["1->2->5"]` |
| 9 | `backtrack(3)` — leaf, RECORD `"1->3"` | `["1", "3"]` | `["1->2->5", "1->3"]` |
| 10 | UN-CHOOSE — `path.pop()` (`backtrack(1)`'s loop ends, all done) | `["1"]` | `["1->2->5", "1->3"]` |

**Result:** `out = ["1->2->5", "1->3"]` ✓

### Mental model

- `path` is a **stack of breadcrumbs** — append before going down a branch, pop after coming back up, so it always mirrors the exact chain from root to wherever you currently are.
- Only a **leaf** triggers a RECORD; every other node's job is purely to CHOOSE a child, RECURSE, and UN-CHOOSE — it never records anything itself.
- The nested `backtrack` closure avoids passing `out`/`path` as parameters on every call — a common shape for backtracking problems.

### Common confusions

- **Forgetting `path.pop()`:** without the UN-CHOOSE step, `path` keeps growing across sibling branches and every later recorded path would wrongly include earlier siblings' values.
- **Recording at every node instead of only leaves:** the check `if not node.left and not node.right` is what limits RECORD to *finished* paths — recording at internal nodes would produce partial, incorrect paths.
- **Order of pop vs. recurse:** `path.pop()` must come **after** `backtrack(nxt)` returns, not before — the recursive call needs the child's value still in `path` while it explores that child's own subtree.

### Complexity

- **Time:** `O(n^2)` worst case — `n` nodes visited, and each of up to `n` leaf paths does an `O(n)` string join; `O(n)` if you only count node visits
- **Space:** `O(h)` for the recursion stack and shared `path` (`h` = tree height), plus `O(n)` for the output strings

---

## Quick reference

| Function | Technique | Result on `build_tree([1, 2, 3, None, 5])` | Time | Space |
| -------- | --------- | -------------------------------------------- | ---- | ----- |
| `binary_tree_paths` | Backtracking DFS (choose / recurse / un-choose) | `['1->2->5', '1->3']` | `O(n)` visits, `O(n^2)` incl. joins | `O(h)` + `O(n)` output |

## Patterns to remember

- **Choose / recurse / un-choose is the backtracking skeleton:** append state before recursing, always pop it after — this is the same shape used by `path_sum_ii`, `smallest_from_leaf`, and most "collect all X" tree/graph problems.
- **Record only at the terminal condition:** here that's a leaf; in other problems it might be "leaf AND remaining sum is 0" or "reached target depth" — the choose/recurse/un-choose loop itself doesn't change.
- **A closure sharing `out`/`path` is simpler than threading them as parameters** — common in Python backtracking solutions, though passing copies (`path[:]`) is required instead of `path.pop()` when the collected items must be independent lists rather than strings.
- **Signal words:** "all root-to-leaf paths", "every path", "enumerate all", "return all".
- **Common pitfalls:** (1) recording before reaching a leaf; (2) missing the `pop()` and corrupting sibling paths; (3) storing a reference to a mutable list (`path[:]` not `path`) when paths are lists instead of joined strings.
- **Related problems:** Path Sum II, Sum Root to Leaf Numbers, Smallest String Starting From Leaf, Path Sum.
