# Tree Traversal — Step-by-Step Reference

> **Source notebook:** `DSA_Deep_Dive/notebooks/04_tree_traversal.ipynb`
> **Companion tutorial:** `DSA_Deep_Dive/tutorials/04_Tree_Traversal.md`
> **Generated for:** personal study reference

---

## Overview

| Topic                 | Key idea                                                   |
| --------------------- | ---------------------------------------------------------- |
| DFS (pre / in / post) | Same walk — only**when you visit** the node changes |
| Iterative DFS         | Explicit**stack** replaces the call stack            |
| BFS (level-order)     | **Queue** — visit row by row                        |
| Rebuild tree          | **Pre-order + in-order** uniquely determine the tree |

**Canonical tree used throughout** (generic binary tree — **not** a BST):

```
          1          ← root
         / \
        2   3
       / \ / \
      4  5 6  7
```

Expected outputs (from notebook asserts):

| Function        | Output                          |
| --------------- | ------------------------------- |
| `preorder`    | `[1, 2, 4, 5, 3, 6, 7]`       |
| `inorder`     | `[4, 2, 5, 1, 6, 3, 7]`       |
| `postorder`   | `[4, 5, 2, 6, 7, 3, 1]`       |
| `level_order` | `[[1], [2, 3], [4, 5, 6, 7]]` |

---

## `TreeNode` — the node class

### What it does

Stores a value plus optional left and right child pointers — the building block for every function in this notebook.

### Code

```python
class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val; self.left = left; self.right = right
```

### Line by line

| Line / code    | What it does                        |
| -------------- | ----------------------------------- |
| `val`        | The data stored at this node        |
| `left=None`  | Pointer to left child (or`None`)  |
| `right=None` | Pointer to right child (or`None`) |

---

## `preorder` — Node → Left → Right (recursive)

### What it does

Visits the current node **before** its subtrees. Use for copying/serializing a tree top-down.

### Code

```python
def preorder(n, out=None):
    """Node, Left, Right."""
    out = [] if out is None else out
    if n:
        out.append(n.val); 
      	preorder(n.left, out); 
      	preorder(n.right, out)
    return out
```

### Line by line

| Line / code                          | What it does                                              |
| ------------------------------------ | --------------------------------------------------------- |
| `out = [] if out is None else out` | Create a fresh result list on the first (outer) call only |
| `if n:`                            | Base case: empty node → do nothing                       |
| `out.append(n.val)`                | **Visit** — record this node now (before children) |
| `preorder(n.left, out)`            | Recurse into entire left subtree                          |
| `preorder(n.right, out)`           | Then entire right subtree                                 |

### Step-by-step trace (every visit)

| Step | Call enters     | Visit now?  | `out` after             |
| ---- | --------------- | ----------- | ------------------------- |
| 1    | `preorder(1)` | **1** | `[1]`                   |
| 2    | `preorder(2)` | **2** | `[1, 2]`                |
| 3    | `preorder(4)` | **4** | `[1, 2, 4]`             |
| 4    | `preorder(5)` | **5** | `[1, 2, 4, 5]`          |
| 5    | `preorder(3)` | **3** | `[1, 2, 4, 5, 3]`       |
| 6    | `preorder(6)` | **6** | `[1, 2, 4, 5, 3, 6]`    |
| 7    | `preorder(7)` | **7** | `[1, 2, 4, 5, 3, 6, 7]` |

**Final output:** `[1, 2, 4, 5, 3, 6, 7]` ✓

### Mental model

- Stamp each node the **first time you arrive** at it, then dive left, then right.
- Root always appears **first** in the output.

### Complexity

- **Time:** `O(n)` — every node visited once
- **Space:** `O(h)` — recursion stack depth = tree height

---

## `inorder` — Left → Node → Right (recursive)

### What it does

Visits the node **between** its left and right subtrees. On a **BST** this gives sorted order; on this generic tree it does not.

### Code

```python
def inorder(n, out=None):
    """Left, Node, Right."""
    out = [] if out is None else out
    if n:
        inorder(n.left, out); out.append(n.val); inorder(n.right, out)
    return out
```

### Line by line

| Line / code               | What it does                                         |
| ------------------------- | ---------------------------------------------------- |
| `inorder(n.left, out)`  | Fully finish the left subtree first                  |
| `out.append(n.val)`     | **Visit** — node goes in the **middle** |
| `inorder(n.right, out)` | Then finish the right subtree                        |

### Step-by-step trace (every visit)

| Step | Action                                        | `out` after             |
| ---- | --------------------------------------------- | ------------------------- |
| 1    | Finish left of 1 → go to 4, visit**4** | `[4]`                   |
| 2    | Back at 2, visit**2**                   | `[4, 2]`                |
| 3    | Right of 2 → visit**5**                | `[4, 2, 5]`             |
| 4    | Back at 1, visit**1**                   | `[4, 2, 5, 1]`          |
| 5    | Left of 3 → visit**6**                 | `[4, 2, 5, 1, 6]`       |
| 6    | Visit**3**                              | `[4, 2, 5, 1, 6, 3]`    |
| 7    | Right of 3 → visit**7**                | `[4, 2, 5, 1, 6, 3, 7]` |

**Final output:** `[4, 2, 5, 1, 6, 3, 7]` ✓ (not sorted — this tree is not a BST)

### Common confusions

- In-order is sorted **only on a BST**. Here root is `1` but children are `2` and `3` — both greater than `1`, so BST property is violated.
- Root `1` lands in the **middle** of the output: whole left subtree before it, whole right subtree after.

### Complexity

- **Time:** `O(n)` · **Space:** `O(h)`

---

## `postorder` — Left → Right → Node (recursive)

### What it does

Visits the node **after** both subtrees. Use for bottom-up work (height, size, delete).

### Code

```python
def postorder(n, out=None):
    """Left, Right, Node."""
    out = [] if out is None else out
    if n:
        postorder(n.left, out); postorder(n.right, out); out.append(n.val)
    return out
```

### Line by line

| Line / code                 | What it does                               |
| --------------------------- | ------------------------------------------ |
| `postorder(n.left, out)`  | Finish left subtree completely             |
| `postorder(n.right, out)` | Finish right subtree completely            |
| `out.append(n.val)`       | **Visit last** — on the way back up |

### Step-by-step trace (every visit)

| Step | Subtree finished | Visit now?  | `out` after             |
| ---- | ---------------- | ----------- | ------------------------- |
| 1    | Left of 2 done   | **4** | `[4]`                   |
| 2    | Right of 2 done  | **5** | `[4, 5]`                |
| 3    | Node 2 done      | **2** | `[4, 5, 2]`             |
| 4    | Left of 3 done   | **6** | `[4, 5, 2, 6]`          |
| 5    | Right of 3 done  | **7** | `[4, 5, 2, 6, 7]`       |
| 6    | Node 3 done      | **3** | `[4, 5, 2, 6, 7, 3]`    |
| 7    | Root done        | **1** | `[4, 5, 2, 6, 7, 3, 1]` |

**Final output:** `[4, 5, 2, 6, 7, 3, 1]` ✓ — root **last**

### Mental model

- Children before parent — natural for "solve subtrees, then combine."

### Complexity

- **Time:** `O(n)` · **Space:** `O(h)`

---

## `preorder_iter` — iterative pre-order

### What it does

Same order as recursive pre-order, using an explicit stack. Safer on very deep trees (no recursion limit).

### Code

```python
def preorder_iter(root):
    """Push RIGHT before LEFT, so LEFT pops first (Node, Left, Right)."""
    if not root:
        return []
    out, stack = [], [root]
    while stack:
        node = stack.pop()            # LIFO -> depth-first
        out.append(node.val)
        if node.right: stack.append(node.right)
        if node.left:  stack.append(node.left)
    return out
```

### Line by line

| Line / code                  | What it does                                                      |
| ---------------------------- | ----------------------------------------------------------------- |
| `stack = [root]`           | Seed the stack with the root                                      |
| `node = stack.pop()`       | Take the top node — this is who we visit now                     |
| `out.append(node.val)`     | Record the visit                                                  |
| `stack.append(node.right)` | Push right**first**                                         |
| `stack.append(node.left)`  | Push left**second** → left ends up on **top** (LIFO) |

### Step-by-step trace

Stack notation: `[bottom ... top]` — **top** is popped next.

**Before loop:** `stack = [1]`, `out = []`

| Iter | Pop & visit | Push (right → left) | `stack` after | `out` after             |
| ---- | ----------- | -------------------- | --------------- | ------------------------- |
| 1    | **1** | 3, 2                 | `[3, 2]`      | `[1]`                   |
| 2    | **2** | 5, 4                 | `[3, 5, 4]`   | `[1, 2]`                |
| 3    | **4** | —                   | `[3, 5]`      | `[1, 2, 4]`             |
| 4    | **5** | —                   | `[3]`         | `[1, 2, 4, 5]`          |
| 5    | **3** | 7, 6                 | `[7, 6]`      | `[1, 2, 4, 5, 3]`       |
| 6    | **6** | —                   | `[7]`         | `[1, 2, 4, 5, 3, 6]`    |
| 7    | **7** | —                   | `[]`          | `[1, 2, 4, 5, 3, 6, 7]` |

**Final output:** `[1, 2, 4, 5, 3, 6, 7]` ✓

### Common confusions

- Pushing right first does **not** mean visiting right first. Stack is LIFO — left (pushed last) pops first.
- **Memory hook:** push right, then left → left pops first → Root → Left → Right.

### Complexity

- **Time:** `O(n)` · **Space:** `O(h)` for the stack

---

## `inorder_iter` — iterative in-order

### What it does

Same order as recursive in-order. Cannot visit on pop immediately like pre-order — must go all the way left first.

### Code

```python
def inorder_iter(root):
    """Walk left pushing nodes; pop to visit; then go right."""
    out, stack, node = [], [], root
    while stack or node:
        while node:                   # dive as far LEFT as possible
            stack.append(node)
            node = node.left
        node = stack.pop()            # deepest unvisited node
        out.append(node.val)
        node = node.right             # now handle its right subtree
    return out
```

### Line by line

| Line / code                | What it does                                                    |
| -------------------------- | --------------------------------------------------------------- |
| `while node:` inner loop | Push every node on the path going left — remember the way back |
| `node = stack.pop()`     | Leftmost unvisited node — time to visit                        |
| `out.append(node.val)`   | Record visit                                                    |
| `node = node.right`      | Pivot into the right subtree and repeat                         |

### Step-by-step trace

Stack: `[bottom ... top]`

| Iter | Phase   | Action                               | `stack` after | `node` after | `out` after             |
| ---- | ------- | ------------------------------------ | --------------- | -------------- | ------------------------- |
| 1    | go left | push 1→2→4                         | `[1, 2, 4]`   | `None`       | `[]`                    |
| 2    | visit   | pop**4**, visit                | `[1, 2]`      | `None`       | `[4]`                   |
| 3    | visit   | pop**2**, visit, go right to 5 | `[1]`         | `5`          | `[4, 2]`                |
| 4    | go left | push 5 (no left)                     | `[1, 5]`      | `None`       | `[4, 2]`                |
| 5    | visit   | pop**5**, visit                | `[1]`         | `None`       | `[4, 2, 5]`             |
| 6    | visit   | pop**1**, visit, go right to 3 | `[]`          | `3`          | `[4, 2, 5, 1]`          |
| 7    | go left | push 3→6                            | `[3, 6]`      | `None`       | `[4, 2, 5, 1]`          |
| 8    | visit   | pop**6**, visit                | `[3]`         | `None`       | `[4, 2, 5, 1, 6]`       |
| 9    | visit   | pop**3**, visit, go right to 7 | `[]`          | `7`          | `[4, 2, 5, 1, 6, 3]`    |
| 10   | go left | push 7                               | `[7]`         | `None`       | `[4, 2, 5, 1, 6, 3]`    |
| 11   | visit   | pop**7**, visit                | `[]`          | `None`       | `[4, 2, 5, 1, 6, 3, 7]` |

**Final output:** `[4, 2, 5, 1, 6, 3, 7]` ✓

### Mental model

- Push the whole left spine, pop one (visit), step right, repeat.
- Unlike pre-order, push and pop are **not** one-to-one per node.

### Complexity

- **Time:** `O(n)` · **Space:** `O(h)`

---

## `level_order` — BFS grouped by level

### What it does

Visits the tree row by row. Returns a list of levels (each level is a list of values).

### Code

```python
from collections import deque

def level_order(root):
    """BFS grouped by level: each output entry is one full row."""
    if not root:
        return []
    out, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):       # freeze this level's size ...
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        out.append(level)             # ... so each entry is one level
    return out
```

### Line by line

| Line / code                | What it does                                    |
| -------------------------- | ----------------------------------------------- |
| `deque([root])`          | Queue — FIFO (first in, first out)             |
| `for _ in range(len(q))` | Snapshot current level size before processing   |
| `node = q.popleft()`     | Take the oldest waiting node                    |
| `q.append(child)`        | Children wait at the**back** of the queue |
| `out.append(level)`      | One full row saved per outer loop               |

### Step-by-step trace

Queue: `[front ... back]` — `popleft` from front, `append` to back.

| Outer iter | Level built      | `q` after processing level | `out` after                   |
| ---------- | ---------------- | ---------------------------- | ------------------------------- |
| 1          | `[1]`          | `[2, 3]`                   | `[[1]]`                       |
| 2          | `[2, 3]`       | `[4, 5, 6, 7]`             | `[[1], [2, 3]]`               |
| 3          | `[4, 5, 6, 7]` | `[]`                       | `[[1], [2, 3], [4, 5, 6, 7]]` |

**Detail — outer iter 2 (level 1):**

| Inner step | `popleft` | enqueue children | `level` so far | `q` after      |
| ---------- | ----------- | ---------------- | ---------------- | ---------------- |
| 1          | **2** | 4, 5             | `[2]`          | `[3, 4, 5]`    |
| 2          | **3** | 6, 7             | `[2, 3]`       | `[4, 5, 6, 7]` |

**Final output:** `[[1], [2, 3], [4, 5, 6, 7]]` ✓

### Mental model

- BFS = **queue** (spread wide). DFS = **stack** (dive deep).
- `len(q)` snapshot ensures you process exactly one row per outer loop.

### Complexity

- **Time:** `O(n)` · **Space:** `O(w)` where `w` = max width (here 4)

---

## `build` — rebuild tree from pre-order + in-order

### What it does

Recovers the unique binary tree when given both a pre-order and in-order traversal list.

### Code

```python
def build(preorder, inorder):
    """Rebuild the unique tree from pre-order + in-order lists."""
    if not preorder:
        return None
    root_val = preorder[0]            # pre-order's first element is the root
    root = TreeNode(root_val)
    mid = inorder.index(root_val)     # its position splits in-order into left | right
    root.left  = build(preorder[1:mid + 1], inorder[:mid])
    root.right = build(preorder[mid + 1:],  inorder[mid + 1:])
    return root
```

### Line by line

| Line / code                       | What it does                                                 |
| --------------------------------- | ------------------------------------------------------------ |
| `root_val = preorder[0]`        | Pre-order always starts with the root                        |
| `mid = inorder.index(root_val)` | Root's index in in-order splits left subtree\| right subtree |
| `preorder[1:mid+1]`             | Pre-order slice for left subtree (size =`mid`)             |
| `preorder[mid+1:]`              | Pre-order slice for right subtree                            |
| `inorder[:mid]`                 | In-order values in left subtree                              |
| `inorder[mid+1:]`               | In-order values in right subtree                             |

### Input

```
preorder = [1, 2, 4, 5, 3, 6, 7]
inorder  = [4, 2, 5, 1, 6, 3, 7]
```

### Step-by-step trace (first 3 recursive calls)

**Call 1 — `build([1,2,4,5,3,6,7], [4,2,5,1,6,3,7])`**

| Step         | Value                             |
| ------------ | --------------------------------- |
| `root_val` | `1`                             |
| `mid`      | `3` (index of `1` in inorder) |
| left slice   | `pre=[2,4,5]`, `in=[4,2,5]`   |
| right slice  | `pre=[3,6,7]`, `in=[6,3,7]`   |

```
inorder:  [4, 2, 5, | 1 | 6, 3, 7]
                    root
          left subtree | right subtree
```

**Call 2 — `build([2,4,5], [4,2,5])` (left child of 1)**

| Step         | Value                   |
| ------------ | ----------------------- |
| `root_val` | `2`                   |
| `mid`      | `1`                   |
| left slice   | `pre=[4]`, `in=[4]` |
| right slice  | `pre=[5]`, `in=[5]` |

**Call 3 — `build([4], [4])` (left child of 2)**

| Step         | Value                   |
| ------------ | ----------------------- |
| `root_val` | `4`                   |
| `mid`      | `0`                   |
| left / right | both empty → leaf node |

Remaining calls build node `5`, then root `3` with children `6` and `7`, reconstructing the original tree.

**Verification:** `level_order(rebuilt) == [[1], [2, 3], [4, 5, 6, 7]]` ✓

### Mental model

- Pre-order tells you **who** the root is.
- In-order tells you **which nodes are left vs right** of that root.
- Recurse on both halves.

### Complexity

- **Time:** `O(n²)` with `.index()` on a list each call (can be `O(n)` with a hash map)
- **Space:** `O(n)` for slices / recursion

---

## Quick reference

| Function          | Order / technique                 | Output on canonical tree        |
| ----------------- | --------------------------------- | ------------------------------- |
| `preorder`      | Node → Left → Right (recursive) | `[1, 2, 4, 5, 3, 6, 7]`       |
| `inorder`       | Left → Node → Right (recursive) | `[4, 2, 5, 1, 6, 3, 7]`       |
| `postorder`     | Left → Right → Node (recursive) | `[4, 5, 2, 6, 7, 3, 1]`       |
| `preorder_iter` | Pre-order with explicit stack     | `[1, 2, 4, 5, 3, 6, 7]`       |
| `inorder_iter`  | In-order with explicit stack      | `[4, 2, 5, 1, 6, 3, 7]`       |
| `level_order`   | BFS with queue, grouped by level  | `[[1], [2, 3], [4, 5, 6, 7]]` |
| `build`         | Pre + in → unique tree           | recovers tree above             |

## Patterns to remember

- **Pre-order** → root first; serialize / copy top-down.
- **In-order** → root in the middle; **sorted only on a BST**.
- **Post-order** → root last; bottom-up (height, delete).
- **Level-order** → BFS with a queue; shortest path on unweighted trees.
- **Iterative pre-order** → push **right then left** so left pops first (LIFO).
- **Rebuild** → pre-order gives root; in-order splits left | right; recurse.
- **DFS = stack/recursion** · **BFS = queue**.
