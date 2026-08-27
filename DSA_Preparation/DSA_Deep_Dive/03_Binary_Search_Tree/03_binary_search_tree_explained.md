# Binary Search Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Deep_Dive/notebooks/03_binary_search_tree.ipynb`  
> **Companion tutorial:** `DSA_Deep_Dive/tutorials/03_Binary_Search_Tree.md`  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| BST invariant | **left < node < right** at every node, recursively |
| Search / insert | Follow comparisons — discard half each step → `O(h)` |
| In-order | **Always sorted** on a valid BST |
| Delete | 0 child / 1 child / 2 children (use in-order successor) |
| Validate | Carry `(low, high)` range — not just child checks |
| Balance | Skewed BST → `O(n)`; balanced → `O(log n)` |

**BST built from inserts `[8, 3, 10, 1, 6, 14, 4, 7, 13]`:**

```
        8
       / \
      3   10
     / \   \
    1   6   14
       / \  /
      4  7 13
```

Expected outputs (from notebook asserts):

| Function | Output |
|----------|--------|
| `search(7)` | `True` |
| `search(5)` | `False` |
| `inorder` | `[1, 3, 4, 6, 7, 8, 10, 13, 14]` (sorted) |
| `find_min` | `1` |
| `find_max` | `14` |
| After `delete(3)` | `[1, 4, 6, 7, 8, 10, 13, 14]` — still sorted |
| `is_valid_bst(good)` | `True` |
| `is_valid_bst(bad)` | `False` |
| `search_steps(skewed, 15)` | `15` (O(n)) |
| `search_steps(balanced, 15)` | `4` (O(log n)) |

---

## `insert` — add a value keeping BST order

### Code

```python
def insert(root, val):
    if root is None:
        return TreeNode(val)
    if val < root.val:
        root.left = insert(root.left, val)
    elif val > root.val:
        root.right = insert(root.right, val)
    return root
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `root is None` | Found empty slot — new node goes here |
| `val < root.val` | Go left (smaller values) |
| `val > root.val` | Go right (larger values) |
| equal | Ignore duplicate (no insert) |

### Trace — insert `7` into built tree

| Step | At node | Compare | Action |
|------|---------|---------|--------|
| 1 | 8 | 7 < 8 | go left |
| 2 | 3 | 7 > 3 | go right |
| 3 | 6 | 7 > 6 | go right |
| 4 | None | — | create node 7 as right child of 6 |

### Trace — full build order

| Insert | Where it lands |
|--------|----------------|
| 8 | root |
| 3 | left of 8 |
| 10 | right of 8 |
| 1 | left of 3 |
| 6 | right of 3 |
| 14 | right of 10 |
| 4 | left of 6 |
| 7 | right of 6 |
| 13 | left of 14 |

### Complexity

- **Time:** `O(h)` per insert · **Space:** `O(h)` recursion

---

## `search` — find a value

### Code

```python
def search(root, target):
    node = root
    while node:
        if target == node.val:
            return True
        node = node.left if target < node.val else node.right
    return False
```

### Trace — `search(root, 7)`

| Step | At node | Compare | Next |
|------|---------|---------|------|
| 1 | 8 | 7 < 8 | left → 3 |
| 2 | 3 | 7 > 3 | right → 6 |
| 3 | 6 | 7 > 6 | right → 7 |
| 4 | 7 | 7 == 7 | **return True** |

### Trace — `search(root, 5)`

| Step | At node | Compare | Next |
|------|---------|---------|------|
| 1 | 8 | 5 < 8 | left → 3 |
| 2 | 3 | 5 > 3 | right → 6 |
| 3 | 6 | 5 < 6 | left → 4 |
| 4 | 4 | 5 > 4 | right → None |
| 5 | None | — | **return False** |

### Complexity

- **Time:** `O(h)` · **Space:** `O(1)` iterative

---

## `inorder` — sorted output (the killer feature)

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
| 1 | **1** | `[1]` |
| 2 | **3** | `[1, 3]` |
| 3 | **4** | `[1, 3, 4]` |
| 4 | **6** | `[1, 3, 4, 6]` |
| 5 | **7** | `[1, 3, 4, 6, 7]` |
| 6 | **8** | `[1, 3, 4, 6, 7, 8]` |
| 7 | **10** | `[1, 3, 4, 6, 7, 8, 10]` |
| 8 | **13** | `[1, 3, 4, 6, 7, 8, 10, 13]` |
| 9 | **14** | `[1, 3, 4, 6, 7, 8, 10, 13, 14]` |

**Final output:** sorted ascending ✓ — `assert vals == sorted(vals)`

### Why it's sorted on a BST

- In-order visits left subtree (all smaller) → node → right subtree (all larger).
- BST guarantees that ordering at every node.

---

## `find_min` / `find_max`

### Code

```python
def find_min(node):
    while node.left:
        node = node.left
    return node.val

def find_max(node):
    while node.right:
        node = node.right
    return node.val
```

### Trace — `find_min` from root 8

| Step | `node` |
|------|--------|
| 1 | 8 → has left |
| 2 | 3 → has left |
| 3 | 1 → no left → **return 1** |

### Trace — `find_max` from root 8

| Step | `node` |
|------|--------|
| 1 | 8 → has right |
| 2 | 10 → has right |
| 3 | 14 → no right → **return 14** |

---

## `delete` — remove a value (three cases)

### Code

```python
def delete(root, val):
    if root is None:
        return None
    if val < root.val:
        root.left = delete(root.left, val)
    elif val > root.val:
        root.right = delete(root.right, val)
    else:
        if root.left is None:
            return root.right
        if root.right is None:
            return root.left
        succ = root.right
        while succ.left:
            succ = succ.left
        root.val = succ.val
        root.right = delete(root.right, succ.val)
    return root
```

### Three cases at the found node

| Case | Children | Action |
|------|----------|--------|
| 0 | none | return `None` |
| 1 | one child | return that child (splice out) |
| 2 | both | copy **in-order successor** (smallest in right subtree), then delete successor |

### Trace — `delete(root, 3)` (2 children)

Node 3 has left=1, right=6.

| Step | Action |
|------|--------|
| 1 | Find node 3 (val < 8 → left) |
| 2 | Two children → find successor |
| 3 | `succ = root.right` = 6, go left to **4** (smallest in right subtree) |
| 4 | `root.val = 4` (copy successor value up) |
| 5 | `delete(root.right, 4)` removes the old node 4 |

**Tree after delete:**

```
        8
       / \
      4   10
     / \   \
    1   6   14
       / \  /
      -  7 13
```

**In-order after:** `[1, 4, 6, 7, 8, 10, 13, 14]` ✓ — still sorted, 3 gone

### Mental model

- 0/1 child: easy splice.
- 2 children: replace with successor (next larger value), then delete the duplicate from right subtree.

---

## `is_valid_bst` — validate with a range

### Code

```python
def is_valid_bst(node, low=float("-inf"), high=float("inf")):
    if node is None:
        return True
    if not (low < node.val < high):
        return False
    return (is_valid_bst(node.left,  low, node.val) and
            is_valid_bst(node.right, node.val, high))
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `low < node.val < high` | Node must fit its **allowed window** |
| `is_valid_bst(left, low, node.val)` | Going left **tightens upper bound** |
| `is_valid_bst(right, node.val, high)` | Going right **tightens lower bound** |

### Good tree — `insert(10), insert(5), insert(15)`

```
    10
   /  \
  5   15
```

| Node | Range | Valid? |
|------|-------|--------|
| 10 | (-∞, +∞) | ✓ |
| 5 | (-∞, 10) | ✓ |
| 15 | (10, +∞) | ✓ |

**Result:** `True` ✓

### Bad tree — why child check alone fails

```
    10
   /  \
  5   15
     /
    6        ← 6 is left child of 15, but 6 < 10 (violates BST)
```

| Node | Range | Valid? |
|------|-------|--------|
| 6 | (10, 15) | **6 < 10 → False** |

Checking only `6 < 15` (parent) would wrongly pass. Range check catches it.

**Result:** `False` ✓

---

## `search_steps` — count comparisons (skew vs balanced)

### Code

```python
def search_steps(root, target):
    node, steps = root, 0
    while node:
        steps += 1
        if target == node.val:
            break
        node = node.left if target < node.val else node.right
    return steps
```

### Skewed tree — insert `1..15` in order

Becomes a linked list: `1→2→3→...→15`

**Search for 15:**

| Step | Node | Steps |
|------|------|-------|
| 1–15 | Walk 1→2→...→15 | **15 steps** |

### Balanced tree — insert `[8,4,12,2,6,10,14,...]`

**Search for 15:**

| Step | Node | Steps |
|------|------|-------|
| 1 | 8 | 1 |
| 2 | 12 | 2 |
| 3 | 14 | 3 |
| 4 | 15 | **4 steps** |

`15 > 3 × 4` ✓ — skewed is much worse.

### Mental model

- Skewed BST height = `n-1` → search `O(n)`.
- Balanced BST height ≈ `log n` → search `O(log n)`.
- Real systems use AVL / Red-Black trees to stay balanced.

---

## Quick reference

| Function | Technique | Key result |
|----------|-----------|------------|
| `insert` | Smaller left, larger right | Builds valid BST |
| `search` | Follow comparisons | 7=True, 5=False |
| `inorder` | L → Node → R | Sorted list |
| `find_min` / `find_max` | Walk leftmost / rightmost | 1 / 14 |
| `delete` | 0/1/2 child cases | Removes 3, stays valid |
| `is_valid_bst` | `(low, high)` range | Catches hidden violations |
| `search_steps` | Count path length | Skew=15, Balanced=4 |

## Patterns to remember

- **Invariant:** left `<` node `<` right, recursively.
- **In-order = sorted** — only on a valid BST.
- **Delete with 2 children:** in-order successor (smallest in right subtree).
- **Validate:** range `(low, high)`, not just parent comparison.
- **Skew = linked list = O(n)** — why self-balancing trees exist.
