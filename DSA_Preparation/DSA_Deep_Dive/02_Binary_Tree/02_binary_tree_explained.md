# Binary Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Deep_Dive/notebooks/02_binary_tree.ipynb`  
> **Companion tutorial:** `DSA_Deep_Dive/tutorials/02_Binary_Tree.md`  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| Binary tree | At most **two** ordered children: `left`, `right` |
| Recursion | Solve left, solve right, combine |
| Invert | Swap left/right everywhere — reverses in-order |
| Diameter | Return height up, track best path in a side variable |
| Array packing | Complete trees: `left=2i+1`, `right=2i+2` |

**Canonical tree used throughout:**

```
          1          ← root
         / \
        2   3
       / \   \
      4   5    6
```

Expected outputs (from notebook asserts):

| Function | Output |
|----------|--------|
| `size` | `6` |
| `height` | `2` |
| `inorder` (before invert) | `[4, 2, 5, 1, 3, 6]` |
| `inorder` (after invert) | `[6, 3, 1, 5, 2, 4]` (reversed) |
| `diameter` | `4` edges (path 4→2→1→3→6) |
| `from_array([1..7])` inorder | `[4, 2, 5, 1, 6, 3, 7]` |

---

## `TreeNode` — the node class

### Code

```python
class TreeNode:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

| Field | Meaning |
|-------|---------|
| `left` | Left child (or `None`) |
| `right` | Right child (or `None`) |

---

## `size` — count nodes

### Code

```python
def size(node):
    if not node:
        return 0
    return 1 + size(node.left) + size(node.right)
```

### Trace

| Node | Left size | Right size | Returns |
|------|-----------|------------|---------|
| 4, 5, 6 | 0 | 0 | `1` each |
| 2 | 1 | 1 | `1+1+1=3` |
| 3 | 0 | 1 | `1+0+1=2` |
| 1 | 3 | 2 | `1+3+2=6` |

**Final output:** `6` ✓

### Complexity

- **Time:** `O(n)` · **Space:** `O(h)`

---

## `height` — longest path in edges

### Code

```python
def height(node):
    if not node:
        return -1
    return 1 + max(height(node.left), height(node.right))
```

### Trace

| Node | Left h | Right h | Returns |
|------|--------|---------|---------|
| 4, 5, 6 | -1 | -1 | `0` (leaves) |
| 2 | 0 | 0 | `1` |
| 3 | -1 | 0 | `1` |
| 1 | 1 | 1 | `2` |

**Final output:** `2` ✓ (e.g. path 4→2→1 in edges: 2 edges)

---

## `inorder` — Left → Node → Right

### Code

```python
def inorder(node, out=None):
    out = [] if out is None else out
    if node:
        inorder(node.left, out)
        out.append(node.val)
        inorder(node.right, out)
    return out
```

### Step-by-step trace

| Step | Visit | `out` after |
|------|-------|-------------|
| 1 | **4** | `[4]` |
| 2 | **2** | `[4, 2]` |
| 3 | **5** | `[4, 2, 5]` |
| 4 | **1** | `[4, 2, 5, 1]` |
| 5 | **3** | `[4, 2, 5, 1, 3]` |
| 6 | **6** | `[4, 2, 5, 1, 3, 6]` |

**Final output:** `[4, 2, 5, 1, 3, 6]` ✓

---

## `invert` — mirror the tree

### What it does

Swaps left and right at every node. LeetCode 226.

### Code

```python
def invert(node):
    if not node:
        return None
    node.left, node.right = invert(node.right), invert(node.left)
    return node
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `invert(node.right)` | Recursively mirror right subtree first |
| `invert(node.left)` | Recursively mirror left subtree |
| `node.left, node.right = ...` | Swap them at this node |

### Trace (structural changes)

| Node visited | Before | After swap |
|--------------|--------|------------|
| 4, 5, 6 | leaves | no change |
| 2 | left=4, right=5 | unchanged (both leaves) |
| 3 | left=None, right=6 | left=6, right=None |
| 1 | left=2, right=3 | left=3, right=2 |

**In-order after invert:** `[6, 3, 1, 5, 2, 4]` = original reversed ✓

### Mental model

- Mirror = swap at every node, recursively.
- In-order of mirrored tree = reverse of original in-order.

---

## `diameter` — longest path between any two nodes

### What it does

Finds the longest path in **edges** between any two nodes. Path may not pass through root.

### Code

```python
def diameter(root):
    best = 0
    def depth(node):
        nonlocal best
        if not node:
            return 0
        L = depth(node.left)
        R = depth(node.right)
        best = max(best, L + R)
        return 1 + max(L, R)
    depth(root)
    return best
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `L = depth(node.left)` | Height of left subtree (in edges) |
| `R = depth(node.right)` | Height of right subtree |
| `best = max(best, L + R)` | Path **through** this node uses L+R edges |
| `return 1 + max(L, R)` | Report height **up** to parent (not diameter) |

### Trace (bottom-up)

| Node | L | R | `L+R` candidate | `best` so far | Returns height |
|------|---|---|-----------------|---------------|----------------|
| 4 | 0 | 0 | 0 | 0 | 1 |
| 5 | 0 | 0 | 0 | 0 | 1 |
| 2 | 1 | 1 | **2** | 2 | 2 |
| 6 | 0 | 0 | 0 | 2 | 1 |
| 3 | 0 | 1 | 1 | 2 | 2 |
| 1 | 2 | 2 | **4** | **4** | 3 |

**Final output:** `4` ✓ — path **4 → 2 → 1 → 3 → 6** (4 edges)

### Mental model

- **Return** one thing (height) to parent.
- **Track** another (best diameter) in a side variable.
- Pattern used in max-path-sum, balance checks, etc.

---

## `from_array` — build tree from level-order array

### What it does

Converts a level-order array into a linked tree using index arithmetic.

### Code

```python
def from_array(arr):
    if not arr:
        return None
    nodes = [TreeNode(v) if v is not None else None for v in arr]
    for i, node in enumerate(nodes):
        if node is None:
            continue
        li, ri = 2*i + 1, 2*i + 2
        if li < len(arr): node.left  = nodes[li]
        if ri < len(arr): node.right = nodes[ri]
    return nodes[0]
```

### Trace — `arr = [1, 2, 3, 4, 5, 6, 7]`

Built tree (perfect):

```
          1
         / \
        2   3
       / \ / \
      4  5 6  7
```

| Index `i` | Node | `left=2i+1` | `right=2i+2` |
|-----------|------|-------------|--------------|
| 0 | 1 | → 2 | → 3 |
| 1 | 2 | → 4 | → 5 |
| 2 | 3 | → 6 | → 7 |
| 3–6 | 4–7 | leaves | leaves |

**In-order of rebuilt tree:** `[4, 2, 5, 1, 6, 3, 7]` ✓

### Index formulas

| Link | Formula |
|------|---------|
| Left child of `i` | `2*i + 1` |
| Right child of `i` | `2*i + 2` |
| Parent of `i` | `(i - 1) // 2` |

---

## `to_array` — pack tree back into array

### Code

```python
def to_array(root, n):
    arr = [None] * n
    def fill(node, i):
        if node is None or i >= n:
            return
        arr[i] = node.val
        fill(node.left,  2*i + 1)
        fill(node.right, 2*i + 2)
    fill(root, 0)
    return arr
```

### Trace — fill from perfect tree

| Call | `i` | `arr[i]` |
|------|-----|----------|
| fill(1, 0) | 0 | 1 |
| fill(2, 1) | 1 | 2 |
| fill(4, 3) | 3 | 4 |
| fill(5, 4) | 4 | 5 |
| fill(3, 2) | 2 | 3 |
| fill(6, 5) | 5 | 6 |
| fill(7, 6) | 6 | 7 |

**Final output:** `[1, 2, 3, 4, 5, 6, 7]` ✓

### Complexity

- **Time:** `O(n)` for both `from_array` and `to_array`

---

## Quick reference

| Function | Technique | Key result |
|----------|-----------|------------|
| `size` | 1 + left + right | `6` |
| `height` | 1 + max(left, right) | `2` |
| `inorder` | L → Node → R | `[4,2,5,1,3,6]` |
| `invert` | Swap children recursively | Reverses in-order |
| `diameter` | Return height, track L+R | `4` edges |
| `from_array` | `2i+1`, `2i+2` links | Perfect tree from array |
| `to_array` | DFS fill by index | Round-trip packing |

## Patterns to remember

- Binary tree recursion: **solve left, solve right, combine**.
- Diameter pattern: **return height, track answer separately**.
- Complete trees pack into arrays — basis of **heaps**.
- Invert swaps at every node; in-order becomes reversed.
