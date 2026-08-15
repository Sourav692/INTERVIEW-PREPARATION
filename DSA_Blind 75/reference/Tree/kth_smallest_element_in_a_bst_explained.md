# Kth Smallest Element in a BST — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/kth_smallest_element_in_a_bst.ipynb`
> **LeetCode:** [230. Kth Smallest Element in a BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/)
> **Generated for:** personal study reference

---

## Overview

| Topic          | Key idea                                                              |
| -------------- | --------------------------------------------------------------------- |
| BST + in-order | In-order traversal visits values in**sorted ascending** order   |
| Full collect   | Gather all values, index`k-1` — simple `O(n)` time and space     |
| Early stop     | Count during in-order walk; return when`count == k` — `O(h + k)` |
| Indexing       | `k` is **1-indexed** (1st smallest, 2nd smallest, …)         |
| Signal words   | "k-th smallest/largest", "order statistic in BST"                     |

**Trees used in this doc:**

Example 1 — `[3,1,4,None,2]`, k=1:

```
      3
     / \
    1   4
     \
      2
```

In-order: `[1, 2, 3, 4]` → k=1 → answer **1**

Example 2 (main trace) — `[5,3,6,2,4,None,None,1]`, k=3:

```
        5
       / \
      3   6
     / \
    2   4
   /
  1
```

In-order: `[1, 2, 3, 4, 5, 6]` → k=3 → answer **3**

---

## `kth_full` — full in-order list (O(n))

### What it does

Collects every value in sorted order via recursive in-order traversal, then returns the element at index `k - 1`.

### Code

```python
def kth_full(root: Optional[TreeNode], k: int) -> int:
    vals = []
    def ino(n):                            # inorder walk lists values smallest-first
        if not n: 
          return
        ino(n.left); 
      	vals.append(n.val); 
      	ino(n.right)
    ino(root)
    return vals[k - 1]                     # the k-th smallest (k is 1-indexed)
```

### Line by line

| Line / code            | What it does                                     |
| ---------------------- | ------------------------------------------------ |
| `vals = []`          | Accumulates values in sorted order               |
| `def ino(n):`        | Recursive in-order helper                        |
| `if not n: return`   | Base case — empty node                          |
| `ino(n.left)`        | Visit entire left subtree first (smaller values) |
| `vals.append(n.val)` | **Visit** — record current node           |
| `ino(n.right)`       | Then right subtree (larger values)               |
| `ino(root)`          | Start from root                                  |
| `return vals[k - 1]` | 1-indexed k → 0-indexed array position          |

### Step-by-step trace — `[5,3,6,2,4,None,None,1]`, k=3

**In-order visit order:**

| Step | Visit       | `vals` after         |
| ---- | ----------- | ---------------------- |
| 1    | **1** | `[1]`                |
| 2    | **2** | `[1, 2]`             |
| 3    | **3** | `[1, 2, 3]`          |
| 4    | **4** | `[1, 2, 3, 4]`       |
| 5    | **5** | `[1, 2, 3, 4, 5]`    |
| 6    | **6** | `[1, 2, 3, 4, 5, 6]` |

`vals[3 - 1]` = `vals[2]` = **3**

**Final output:** `3` ✓ (matches notebook assert)

### Mental model

- In-order on a BST is a sorted array laid out in the tree. The k-th smallest is simply the k-th element of that implicit sorted list.
- Straightforward but always visits every node even when k is small.

### Common confusions

- **`k - 1` not `k`** — k is 1-indexed per problem statement; Python lists are 0-indexed.
- **Works only on BST** — in-order on a non-BST does not produce sorted order.

### Complexity

- **Time:** `O(n)` — full tree traversal
- **Space:** `O(n)` — stores all values (+ `O(h)` recursion stack)

---

## `kth_early` — early-stop in-order (O(h + k))

### What it does

Iteratively performs in-order traversal with a stack, incrementing a counter at each visit, and returns immediately when the count reaches k.

### Code

```python
def kth_early(root: Optional[TreeNode], k: int) -> int:
    stack, node, count = [], root, 0
    while stack or node:
        while node:                        # dive to the smallest unvisited node
            stack.append(node); node = node.left
        node = stack.pop()
        count += 1                         # we've now visited one more value (in sorted order)
        if count == k:                     # reached the k-th smallest...
            return node.val                # ...return it immediately (no need to continue)
        node = node.right
    return -1
```

### Line by line

| Line / code                                          | What it does                                                         |
| ---------------------------------------------------- | -------------------------------------------------------------------- |
| `stack, node, count = [], root, 0`                 | Stack for iterative in-order; counter tracks how many values visited |
| `while stack or node:`                             | Continue while unprocessed nodes remain                              |
| `while node: stack.append(node); node = node.left` | Push path to leftmost node (standard in-order setup)                 |
| `node = stack.pop()`                               | **Visit** the next smallest unvisited value                    |
| `count += 1`                                       | One more value seen in sorted order                                  |
| `if count == k: return node.val`                   | Early exit — no need to traverse the rest                           |
| `node = node.right`                                | Move to right subtree for next in-order values                       |
| `return -1`                                        | Fallback if k exceeds tree size (not needed for valid inputs)        |

### Step-by-step trace — `[5,3,6,2,4,None,None,1]`, k=3

```
        5
       / \
      3   6
     / \
    2   4
   /
  1
```

| Iter | Action                                            | `stack` (bottom→top) | `node` | `count`   | Result                             |
| ---- | ------------------------------------------------- | ----------------------- | -------- | ----------- | ---------------------------------- |
| 1    | dive left from 5: push 5,3,2,1                    | `[5, 3, 2, 1]`        | `None` | 0           | —                                 |
| 2    | pop**1**, visit; `node = 1.right` → None | `[5, 3, 2]`           | `None` | 1           | count ≠ 3                         |
| 3    | pop**2**, visit; `node = 2.right` → None | `[5, 3]`              | `None` | 2           | count ≠ 3                         |
| 4    | pop**3**, visit; `node = 3.right` → 4    | `[5]`                 | `4`    | **3** | count == k →**return 3** ✓ |

**Final output:** `3` ✓ (matches notebook assert) — stops early without visiting 4, 5, or 6

### Mental model

- Same in-order walk as validation/iterator problems — push left chain, pop to visit, go right.
- The counter turns "sorted enumeration" into "find the k-th" — stop as soon as you've seen enough.
- For small k in a large tree, this is much faster than collecting all values.

### Common confusions

- **1-indexed k** — first smallest is k=1, not k=0; compare `count == k`, index with `k - 1` only in the full-list approach.
- **When to use early stop** — best when k is small relative to n; worst case k=n still visits all nodes → `O(n)`.
- **Iterative vs recursive early stop** — iterative is easier to break out of cleanly; recursive needs a flag or nonlocal.

### Complexity

- **Time:** `O(h + k)` — descend to smallest (`O(h)`), then k visits along in-order path
- **Space:** `O(h)` — stack holds at most height nodes

---

## Quick reference

| Function      | Technique                     | `[3,1,4,None,2]`, k=1 | `[5,3,6,2,4,None,None,1]`, k=3 |
| ------------- | ----------------------------- | ----------------------- | -------------------------------- |
| `kth_full`  | Full in-order →`vals[k-1]` | `1`                   | `3`                            |
| `kth_early` | Iterative in-order + counter  | `1`                   | `3`                            |

## Patterns to remember

- **In-order for order statistics** — k-th smallest/largest in a BST falls out of an in-order walk.
- **Stop early** — return as soon as `count == k`; no need to collect the whole tree.
- **Reusable in-order stack pattern** — same skeleton as Validate BST (`is_valid_inorder`) and BST Iterator.
- **Related problems:** Validate BST, BST Iterator, Kth Largest Element in a Stream.
