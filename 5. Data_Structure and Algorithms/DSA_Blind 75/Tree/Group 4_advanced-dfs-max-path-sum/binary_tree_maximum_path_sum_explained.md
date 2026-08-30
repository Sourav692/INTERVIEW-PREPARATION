
# Binary Tree Maximum Path Sum — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/binary_tree_maximum_path_sum.ipynb`
> **LeetCode:** [124. Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/)
> **Generated for:** personal study reference

---

## Overview

| Topic             | Key idea                                                                                                |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| Path definition   | Any connected sequence of nodes; does**not** have to pass through the root                        |
| Bent path         | Best path*through* a node may use **left arm + node + right arm**                               |
| Return vs track   | DFS**returns** one best downward arm to parent; **updates** global best with full bent path |
| Negative branches | Clamp harmful branches to`0` (skip them)                                                              |

**Canonical tree from `[-10, 9, 20, None, None, 15, 7]`:**

```
        -10
        /   \
       9    20
           /  \
          15   7
```

Expected outputs (from notebook asserts):

| Input                                      | Expected                        |
| ------------------------------------------ | ------------------------------- |
| `[-10, 9, 20, None, None, 15, 7]`        | `42` (path `15 → 20 → 7`) |
| `[1, 2, 3]`                              | `6` (path `2 → 1 → 3`)    |
| `[-3]`                                   | `-3`                          |
| `[2, -1]`                                | `2`                           |
| `max_path_brute` vs `max_path_optimal` | Always equal                    |

---

## `max_path_brute` — recompute downward sums at every node

### What it does

Visits every node, and at each node recomputes the best downward path on left and right (via `down()`) to evaluate the best bent path through that node. Correct but repeats work → `O(n²)`.

### Code

```python
def max_path_brute(root: Optional[TreeNode]) -> int:
    def down(n):                           # best sum of a path going straight DOWN from n
        if not n:
            return 0
        return max(0, n.val + max(down(n.left), down(n.right)))  # 0 = skip a harmful branch
    best = [float("-inf")]                 # global best (in a list so inner functions can update it)
    def visit(n):
        if not n:
            return
        # Best path that BENDS through n = n + best downward-left + best downward-right.
        through = n.val + max(0, down(n.left)) + max(0, down(n.right))
        best[0] = max(best[0], through)
        visit(n.left); visit(n.right)      # (down() is recomputed at each node -> O(n^2))
    visit(root)
    return best[0]
```

### Line by line

| Line / code                                                    | What it does                                                                                          |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `def down(n)`                                                | Helper: best sum of a**single downward** path starting at `n` (may be 0 if all branches hurt) |
| `if not n: return 0`                                         | Empty subtree contributes nothing                                                                     |
| `max(0, n.val + max(down(left), down(right)))`               | Take the better child arm, add`n.val`, but never go below 0 (skip negative paths)                   |
| `best = [float("-inf")]`                                     | Mutable container so nested functions can update the global maximum                                   |
| `through = n.val + max(0, down(left)) + max(0, down(right))` | Best path that**bends** at `n` using both arms                                                |
| `best[0] = max(best[0], through)`                            | Record the best bent path seen anywhere                                                               |
| `visit(n.left); visit(n.right)`                              | DFS over all nodes;`down()` is called fresh each time → redundant work                             |

### Step-by-step trace — `max_path_brute` on `[-10, 9, 20, None, None, 15, 7]` → `42`

**Tree:**

```
        -10
        /   \
       9    20
           /  \
          15   7
```

**`visit` order (preorder-style DFS):** `-10` → `9` → `20` → `15` → `7`

| Visit # | Node`n`     | `down(left)`   | `down(right)`  | `through`        | `best[0]` after |
| ------- | ------------- | ---------------- | ---------------- | ------------------ | ----------------- |
| 1       | **9**   | `down(None)=0` | `down(None)=0` | `9+0+0=9`        | `9`             |
| 2       | **15**  | `0`            | `0`            | `15+0+0=15`      | `15`            |
| 3       | **7**   | `0`            | `0`            | `7+0+0=7`        | `15`            |
| 4       | **20**  | `down(15)=15`  | `down(7)=7`    | `20+15+7=**42**` | `**42**`        |
| 5       | **-10** | `down(9)=9`    | `down(20)=35`* | `-10+9+35=34`    | `42`            |

\* `down(20)` = `max(0, 20 + max(15, 7))` = `max(0, 35)` = `35` (best single arm down from 20)

**Final output:** `42` ✓

---

### Step-by-step trace — `[1, 2, 3]` → `6`

**Tree:**

```
    1
   / \
  2   3
```

| Visit # | Node        | `through`     | `best[0]` after |
| ------- | ----------- | --------------- | ----------------- |
| 1       | **2** | `2`           | `2`             |
| 2       | **3** | `3`           | `3`             |
| 3       | **1** | `1+2+3=**6**` | `**6**`         |

**Final output:** `6` ✓

---

### Step-by-step trace — `[-3]` → `-3`

| Visit # | Node         | `through`   | `best[0]` after |
| ------- | ------------ | ------------- | ----------------- |
| 1       | **-3** | `-3+0+0=-3` | `-3`            |

**Final output:** `-3` ✓ (all-negative tree: must accept the single node)

---

### Step-by-step trace — `[2, -1]` → `2`

**Tree:**

```
  2
 /
-1
```

| Visit # | Node         | `through`                                      | `best[0]` after |
| ------- | ------------ | ------------------------------------------------ | ----------------- |
| 1       | **-1** | `max(0,-1)=0` clamped → `through=-1+0+0=-1` | `-1`            |
| 2       | **2**  | `2+0+0=2` (left arm clamped to 0)              | `2`             |

**Final output:** `2` ✓

### Mental model

- Correct idea: at each node, evaluate the "arch" through that node.
- Inefficiency: `down()` re-walks subtrees every time `visit` calls it.

### Complexity

- **Time:** `O(n²)` — each of `n` nodes may trigger `down()` that walks its subtree
- **Space:** `O(h)` — recursion depth

---

## `max_path_optimal` — one-pass DFS (optimal)

### What it does

A single post-order DFS: `gain(n)` returns the best single downward arm from `n` (for the parent), while updating a global `best` with the full bent path through `n`.

### Code

```python
def max_path_optimal(root: Optional[TreeNode]) -> int:
    best = [float("-inf")]                 # global best answer found anywhere
    def gain(n):                           # returns the best single downward arm from n
        if not n:
            return 0
        left = max(0, gain(n.left))        # ignore a branch that would hurt the sum (clamp to 0)
        right = max(0, gain(n.right))
        best[0] = max(best[0], n.val + left + right)  # a path bending through n uses BOTH arms
        return n.val + max(left, right)    # but we can only hand our PARENT one arm
    gain(root)
    return best[0]
```

### Line by line

| Line / code                                      | What it does                                                              |
| ------------------------------------------------ | ------------------------------------------------------------------------- |
| `best = [float("-inf")]`                       | Tracks global maximum; starts at`-inf` so all-negative trees still work |
| `def gain(n)`                                  | Post-order helper: process children first, then node                      |
| `if not n: return 0`                           | Null child contributes 0 to any sum                                       |
| `left = max(0, gain(n.left))`                  | Best left arm, floored at 0 (skip if negative)                            |
| `right = max(0, gain(n.right))`                | Best right arm, floored at 0                                              |
| `best[0] = max(best[0], n.val + left + right)` | Update global best with bent path through`n`                            |
| `return n.val + max(left, right)`              | Return**one** arm upward to parent — a parent path cannot split    |
| `gain(root)`                                   | Kick off DFS from root                                                    |
| `return best[0]`                               | Answer is the best bent path seen anywhere                                |

### Step-by-step trace — `max_path_optimal` on `[-10, 9, 20, None, None, 15, 7]` → `42`

**Tree:**

```
        -10
        /   \
       9    20
           /  \
          15   7
```

**Post-order visit order:** `9` → `15` → `7` → `20` → `-10`

| Step | Call`gain(n)`     | `left` | `right` | `n.val + left + right` → `best[0]` | Return to parent    |
| ---- | ------------------- | -------- | --------- | --------------------------------------- | ------------------- |
| 1    | **gain(9)**   | `0`    | `0`     | `9 → best=9`                         | `9`               |
| 2    | **gain(15)**  | `0`    | `0`     | `15 → best=15`                       | `15`              |
| 3    | **gain(7)**   | `0`    | `0`     | `7 → best=15`                        | `7`               |
| 4    | **gain(20)**  | `15`   | `7`     | `20+15+7=**42** → best=**42**`       | `20+max(15,7)=35` |
| 5    | **gain(-10)** | `9`    | `35`    | `-10+9+35=34 → best=42`              | `-10+35=25`       |

**Final output:** `42` ✓ (path through nodes `15`, `20`, `7`)

---

### Step-by-step trace — `[1, 2, 3]` → `6`

| Step | Call              | `left` | `right` | update`best`  | return    |
| ---- | ----------------- | -------- | --------- | --------------- | --------- |
| 1    | **gain(2)** | `0`    | `0`     | `2`           | `2`     |
| 2    | **gain(3)** | `0`    | `0`     | `3`           | `3`     |
| 3    | **gain(1)** | `2`    | `3`     | `1+2+3=**6**` | `1+3=4` |

**Final output:** `6` ✓

---

### Step-by-step trace — `[-3]` → `-3`

| Step | Call               | `left` | `right` | update`best` | return |
| ---- | ------------------ | -------- | --------- | -------------- | ------ |
| 1    | **gain(-3)** | `0`    | `0`     | `-3`         | `-3` |

**Final output:** `-3` ✓

---

### Step-by-step trace — `[2, -1]` → `2`

| Step | Call               | `left` | `right` | update`best` | return                    |
| ---- | ------------------ | -------- | --------- | -------------- | ------------------------- |
| 1    | **gain(-1)** | `0`    | `0`     | `-1`         | `max(0,-1+0)=0` clamped |
| 2    | **gain(2)**  | `0`    | `0`     | `2+0+0=2`    | `2`                     |

**Final output:** `2` ✓ (brute and optimal both match notebook asserts)

### Mental model

- **Return one thing, track another:** parent only gets one arm; global best may use both.
- **Clamp to zero:** if a branch would drag the sum down, pretend it doesn't exist (`max(0, ...)`).
- The answer is **not** necessarily the return value of `gain(root)` — it's `best[0]`.

### Common confusions

- **Don't return the bent path to the parent:** `return n.val + max(left, right)` is a single arm; returning `n.val + left + right` would let the parent illegally "split" into two children.
- **All-negative tree:** seeding `best` with `-inf` ensures a lone negative node still becomes the answer.
- **Negative node values:** `max(0, gain(child))` means "skip this child entirely" — different from "include the child as 0."

### Complexity

- **Time:** `O(n)` — each node visited once
- **Space:** `O(h)` — recursion stack depth

---

## Quick reference

| Function             | Technique                     | `[-10,9,20,…,7]` | `[1,2,3]` | `[-3]` | `[2,-1]` |
| -------------------- | ----------------------------- | ------------------- | ----------- | -------- | ---------- |
| `max_path_brute`   | DFS + recompute`down()`     | `42`              | `6`       | `-3`   | `2`      |
| `max_path_optimal` | One-pass post-order`gain()` | `42`              | `6`       | `-3`   | `2`      |

## Patterns to remember

- **Return one arm, track bent path globally** — same pattern as diameter of binary tree.
- **Clamp negatives to zero** — skip branches that hurt the sum.
- **Signal phrases:** "maximum path sum", "path may bend at any node", "doesn't need to include root."
