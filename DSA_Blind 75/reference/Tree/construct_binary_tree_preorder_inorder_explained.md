# Construct Binary Tree from Preorder and Inorder — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/construct_binary_tree_preorder_inorder.ipynb`  
> **LeetCode:** [105. Construct Binary Tree from Preorder and Inorder Traversal](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/)  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| Preorder role | First value is always the **root** of the current subtree |
| Inorder role | Values left of root → left subtree; right of root → right subtree |
| Naive approach | `inorder.index(root)` + list slicing — simple but `O(n²)` |
| Optimal approach | Hash map for index lookup + index bounds (no slicing) — `O(n)` |
| Signal words | "rebuild tree from traversals", "construct from preorder/inorder" |

**Canonical input** (from notebook assert):

```
preorder = [3, 9, 20, 15, 7]
inorder  = [9, 3, 15, 20, 7]
```

**Rebuilt tree:**

```
        3          ← root (preorder[0])
       / \
      9  20
        /  \
      15    7
```

Level-order: `[3, 9, 20, None, None, 15, 7]`

---

## `build_naive` — search + slice (worst case O(n²))

### What it does

Recursively picks the first preorder value as root, finds it in inorder to split left/right halves, and recurses on slices.

### Code

```python
def build_naive(preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
    if not preorder:
        return None
    root = TreeNode(preorder[0])           # first preorder value is always the root
    mid = inorder.index(preorder[0])       # find the root in inorder (splits left/right)
    # Everything left of the root in inorder is its left subtree, everything right its right.
    root.left = build_naive(preorder[1:mid+1], inorder[:mid])
    root.right = build_naive(preorder[mid+1:], inorder[mid+1:])
    return root
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `if not preorder: return None` | Empty preorder → no tree |
| `root = TreeNode(preorder[0])` | First preorder value is the subtree root |
| `mid = inorder.index(preorder[0])` | Scan inorder to find where root sits — everything left is left subtree, right is right subtree |
| `preorder[1:mid+1]` | Preorder segment for left subtree (skip root, take `mid` values) |
| `inorder[:mid]` | Inorder segment for left subtree (values before root) |
| `preorder[mid+1:]` | Preorder segment for right subtree |
| `inorder[mid+1:]` | Inorder segment for right subtree |
| `return root` | Fully built subtree |

### Step-by-step trace (first 3 recursive calls)

**Input:** `preorder = [3, 9, 20, 15, 7]`, `inorder = [9, 3, 15, 20, 7]`

```
inorder:  [9 | 3 | 15, 20, 7]
           ^left  ^root  ^right
preorder: [3 | 9 | 20, 15, 7]
           root left   right
```

| Call # | `preorder` | `inorder` | Root | `mid` | Left slices | Right slices |
|--------|-----------|-----------|------|-------|-------------|--------------|
| 1 | `[3,9,20,15,7]` | `[9,3,15,20,7]` | **3** | 1 | `pre=[9]`, `ino=[9]` | `pre=[20,15,7]`, `ino=[15,20,7]` |
| 2 | `[9]` | `[9]` | **9** | 0 | `pre=[]`, `ino=[]` → `None` | `pre=[]`, `ino=[]` → `None` |
| 3 | `[20,15,7]` | `[15,20,7]` | **20** | 1 | `pre=[15]`, `ino=[15]` | `pre=[7]`, `ino=[7]` |

**Resulting tree after call 1 unwinds:**

```
        3
       / \
      9  20
        /  \
      15    7
```

**Final output:** Rebuilt tree with `preorder(rebuilt) = [3,9,20,15,7]` and `inorder(rebuilt) = [9,3,15,20,7]` ✓

### Mental model

- Preorder tells you **who** the root is; inorder tells you **which values belong left vs right**.
- Each recursive call shrinks both arrays. The `mid` index is the bridge between the two orderings.

### Common confusions

- **Slice sizes must match** — left preorder slice has length `mid` (number of left-subtree nodes), left inorder slice is `inorder[:mid]`.
- **`inorder.index()` is O(n)** — called at every node → `O(n²)` total.
- **Slicing copies data** — extra `O(n²)` space on top of recursion.

### Complexity

- **Time:** `O(n²)` — `O(n)` index search at each of `n` nodes
- **Space:** `O(n²)` — slicing creates new lists; recursion stack `O(h)`

---

## `build_fast` — hash map + pointer (optimal O(n))

### What it does

Precomputes a value→index map for inorder, walks preorder with a single advancing pointer, and uses index bounds instead of slicing.

### Code

```python
def build_fast(preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
    idx = {v: i for i, v in enumerate(inorder)}   # value -> its position in inorder (O(1))
    self_pre = [0]                         # our current position in preorder (in a list so it persists)
    def helper(lo, hi):                    # build the subtree covering inorder[lo..hi]
        if lo > hi:
            return None
        val = preorder[self_pre[0]]        # next preorder value is this subtree's root
        self_pre[0] += 1                   # advance the preorder pointer
        node = TreeNode(val)
        m = idx[val]                       # where the root splits inorder (instant lookup)
        node.left = helper(lo, m - 1)      # build the left part first (preorder does left first)
        node.right = helper(m + 1, hi)     # then the right part
        return node
    return helper(0, len(inorder) - 1)
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `idx = {v: i for ...}` | Hash map: any value → its index in inorder (`O(1)` lookup) |
| `self_pre = [0]` | Mutable preorder pointer (list wrapper so inner function can mutate it) |
| `def helper(lo, hi):` | Build subtree from inorder range `[lo..hi]` |
| `if lo > hi: return None` | Empty range → no nodes in this subtree |
| `val = preorder[self_pre[0]]` | Next unread preorder value is this subtree's root |
| `self_pre[0] += 1` | Consume that preorder entry (shared across all calls) |
| `node = TreeNode(val)` | Create the root node |
| `m = idx[val]` | Instant lookup: root's position in inorder |
| `helper(lo, m - 1)` | Left subtree covers inorder indices `[lo .. m-1]` |
| `helper(m + 1, hi)` | Right subtree covers `[m+1 .. hi]` |
| `return helper(0, len(inorder) - 1)` | Build full tree over entire inorder array |

### Step-by-step trace (first 3 `helper` calls)

**Input:** `preorder = [3, 9, 20, 15, 7]`, `inorder = [9, 3, 15, 20, 7]`

**Initial:** `idx = {9:0, 3:1, 15:2, 20:3, 7:4}`, `self_pre = [0]`

| Call | `helper(lo, hi)` | `self_pre` before | `val` | `m` | Left call | Right call | Returns |
|------|------------------|-------------------|-------|-----|-----------|------------|---------|
| 1 | `(0, 4)` | `[0]` | **3** | 1 | `helper(0, 0)` | `helper(2, 4)` | node 3 |
| 2 | `(0, 0)` | `[1]` | **9** | 0 | `helper(0, -1)` → None | `helper(1, 0)` → None | node 9 |
| 3 | `(2, 4)` | `[2]` | **20** | 3 | `helper(2, 2)` | `helper(4, 4)` | node 20 |

**Calls 4–5 (complete the right subtree):**

| Call | `helper(lo, hi)` | `self_pre` before | `val` | Returns |
|------|------------------|-------------------|-------|---------|
| 4 | `(2, 2)` | `[3]` | **15** | node 15 (both children None) |
| 5 | `(4, 4)` | `[4]` | **7** | node 7 (both children None) |

**Preorder pointer progression:** 0→1→2→3→4 — reads `[3, 9, 20, 15, 7]` in exactly that order.

**Final output:** Same tree as naive approach; `preorder(rebuilt) = [3,9,20,15,7]` ✓

### Mental model

- One shared preorder pointer walks the preorder list left-to-right — because preorder visits root before children, this naturally assigns roots in the right order.
- Inorder bounds `[lo, hi]` replace slicing — they tell you which values belong in the current subtree without copying arrays.
- Build left before right because preorder lists left subtree roots before right subtree roots.

### Common confusions

- **Why `self_pre` in a list?** — Python integers are immutable; a list wrapper lets the nested function mutate the shared pointer.
- **Left call before right call** — must match preorder's left-before-right ordering, or the shared pointer reads values out of order.
- **`helper(0, -1)` returns None** — `lo > hi` is the empty-subtree base case (e.g., node 9 has no left children).

### Complexity

- **Time:** `O(n)` — each node created once, each hash map lookup `O(1)`
- **Space:** `O(n)` — hash map + recursion stack `O(h)`

---

## Quick reference

| Function | Technique | Time | Space |
|----------|-----------|------|-------|
| `build_naive` | `index()` + slicing | `O(n²)` | `O(n²)` |
| `build_fast` | Hash map + bounds + pointer | `O(n)` | `O(n)` |

## Patterns to remember

- **Two orders pin down the tree** — preorder gives root; inorder splits left/right.
- **Hash map kills repeated scans** — `list.index()` → `dict` turns `O(n²)` into `O(n)`.
- **Pass bounds, don't slice** — `[lo, hi]` indices are cheaper and less error-prone than array copies.
- **Related problems:** Construct from Inorder + Postorder, Serialize/Deserialize Binary Tree.
