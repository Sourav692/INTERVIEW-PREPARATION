# 572. Subtree of Another Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/subtree_of_another_tree.ipynb`
> **LeetCode:** https://leetcode.com/problems/subtree-of-another-tree/
> **Generated for:** personal study reference

---

## Overview

| Topic                 | Key idea                                                                                  |
| --------------------- | ----------------------------------------------------------------------------------------- |
| Brute force           | At**every** node of `root`, run a "same tree?" check against `sub`              |
| Serialize + substring | Flatten both trees to strings with markers;`sub`'s string must appear inside `root`'s |
| Empty subtree         | An empty`sub` is a subtree of anything → `True`                                      |

**Canonical example** (from notebook):

```
root = [3, 4, 5, 1, 2]          sub = [4, 1, 2]  →  True

        3                              4
       / \                            / \
      4   5        contains  →       1   2
     / \
    1   2
```

Expected outputs (from notebook asserts):

| `root`                                       | `sub`       | `is_subtree_brute` | `is_subtree_serial` |
| ---------------------------------------------- | ------------- | -------------------- | --------------------- |
| `[3, 4, 5, 1, 2]`                            | `[4, 1, 2]` | `True`             | `True`              |
| `[3, 4, 5, 1, 2, None, None, None, None, 0]` | `[4, 1, 2]` | `False`            | `False`             |
| `[1, 1]`                                     | `[1]`       | `True`             | `True`              |

---

## `is_subtree_brute` — Same-Tree at Every Node

### What it does

If `sub` is empty → `True`. If `root` is empty but `sub` is not → `False`. If the tree hanging at `root` is identical to `sub` (`same_shape`) → `True`. Otherwise search in `root.left` or `root.right`.

### Code

```python
def is_subtree_brute(root: Optional[TreeNode], sub: Optional[TreeNode]) -> bool:
    if not sub:
        return True
    if not root:
        return False
    if same_shape(root, sub):
        return True
    return is_subtree_brute(root.left, sub) or is_subtree_brute(root.right, sub)
```

### Line by line

| Line / code                              | What it does                                        |
| ---------------------------------------- | --------------------------------------------------- |
| `if not sub: return True`              | Empty`sub` is trivially a subtree                 |
| `if not root: return False`            | Ran out of`root` without finding a match          |
| `if same_shape(root, sub):`            | Does the subtree at this node exactly match`sub`? |
| `return True`                          | Found a matching anchor node                        |
| `is_subtree_brute(root.left, sub)`     | Search left half                                    |
| `or is_subtree_brute(root.right, sub)` | Or search right half                                |

### Step-by-step trace — canonical match `root=[3,4,5,1,2]`, `sub=[4,1,2]`

| Step | Current`root` node | `same_shape(root, sub)?`                   | Next action        |
| ---- | -------------------- | -------------------------------------------- | ------------------ |
| 1    | `3`                | No (values/structure differ at root)         | search left        |
| 2    | `4`                | **Yes** — subtree at 4 is `[4,1,2]` | **`True`** |

**Final output:** `True` ✓

### Step-by-step trace — false case `root` has extra node `0`

`root = [3,4,5,1,2,None,None,None,None,0]` builds to:

```
        3
       / \
      4   5
     / \
    1   2
       /
      0
```

(`build_tree`'s level-order BFS attaches `0` as the **left child of node `2`**, which is `4`'s right child — not as a child of `1`.) `sub = [4,1,2]` is still the flat two-leaf tree `4(1, 2)`.

| Step | Current`root` node                                                    | `same_shape(root, sub)?` | Why                                                                                                                                  | Next action                        |
| ---- | ----------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| 1    | `3`                                                                   | No                         | `3 != 4` (sub's root value)                                                                                                        | search left                        |
| 2    | `4`                                                                   | **No**               | left`1`(leaf) matches sub's `1`(leaf) ✓, but right: root's `2` has a left child `0` while sub's `2` is a leaf → mismatch | search left                        |
| 3    | `1`                                                                   | No                         | `1 != 4`                                                                                                                           | search left & right (both`None`) |
| 4    | `2`                                                                   | No                         | `2 != 4`                                                                                                                           | search left & right                |
| 5    | `0`                                                                   | No                         | `0 != 4`                                                                                                                           | search left & right (both`None`) |
| 6    | `5`                                                                   | No                         | `5 != 4`                                                                                                                           | search left & right (both`None`) |
| —   | all branches exhausted, no`None` root passed the `same_shape` check | —                         | —                                                                                                                                   | **`False`**                |

**Final output:** `False` ✓ — `4` was the only node whose value matched `sub`'s root, and its right subtree (`2` with an extra child `0`) doesn't match `sub`'s right leaf `2`, so no anchor ever returns `True`.

### Mental model

- Slide `sub` over every possible anchor in `root` and ask "identical?"
- Reuses the Same Tree logic as a subroutine.
- `or` short-circuits — first match wins.

### Common confusions

- **Subtree vs substructure:** LeetCode requires an exact match of a **connected** subtree, not just matching values scattered in the tree.
- **Empty `sub`:** Always `True` — handle before checking `root`.
- **Performance:** Worst case `O(m · n)` when `sub` is never found and every node triggers a full comparison.

### Complexity

- **Time:** `O(m · n)` — up to `n` nodes in `root`, each `same_shape` costs `O(m)`
- **Space:** `O(h)` — recursion stack on `root`

---

## `is_subtree_serial` — Serialize + Substring

### What it does

Flattens each tree to a string with `^value` for nodes and `#` for empty children. Returns `True` if `ser(sub)` is a substring of `ser(root)`. Markers prevent false matches like `12` containing `2`.

### Code

```python
def is_subtree_serial(root: Optional[TreeNode], sub: Optional[TreeNode]) -> bool:
    def ser(node):
        if not node:
            return "#"
        return "^" + str(node.val) + " " + ser(node.left) + " " + ser(node.right)
    return ser(sub) in ser(root)
```

### Line by line

| Line / code                                  | What it does                                         |
| -------------------------------------------- | ---------------------------------------------------- |
| `def ser(node):`                           | Inner helper — preorder-like flattening             |
| `if not node: return "#"`                  | Empty child marker (captures shape)                  |
| `"^" + str(node.val)`                      | Value delimiter —`^4` cannot match inside `^12` |
| `+ ser(node.left) + " " + ser(node.right)` | Recurse left then right with spaces                  |
| `ser(sub) in ser(root)`                    | Python substring search                              |

### Step-by-step trace — canonical match

**Serialize `sub = [4, 1, 2]`:**

| Call       | Returns                                     |
| ---------- | ------------------------------------------- |
| `ser(1)` | `"#"`                                     |
| `ser(2)` | `"#"`                                     |
| `ser(4)` | `"^4 # #"` (left=1, right=2, both leaves) |

Full `ser(sub)` = `"^4 # # # #"` — more precisely built as:

```
ser(4) = "^4 " + ser(1) + " " + ser(2)
       = "^4 " + "^1 # #" + " " + "^2 # #"
       = "^4 ^1 # # ^2 # #"
```

**Serialize `root = [3, 4, 5, 1, 2]`:**

| Call                   | Contribution                     |
| ---------------------- | -------------------------------- |
| `ser(1)`, `ser(2)` | leaf strings                     |
| `ser(4)`             | `"^4 ^1 # # ^2 # #"`           |
| `ser(5)`             | `"^5 # #"`                     |
| `ser(3)`             | `"^3 ^4 ^1 # # ^2 # # ^5 # #"` |

**Substring check:** `"^4 ^1 # # ^2 # #"` is contained in `ser(root)` → **`True`** ✓

### Step-by-step trace — false case (extra `0` under node `2`)

In the false-case `root`, the subtree hanging at `4` looks like `4(1, 2(0, None))` — node `2` (not `1`) has the extra left child `0`:

```
ser(4_with_0) = "^4 " + ser(1) + " " + ser(2_with_0)
              = "^4 " + "^1 # #" + " " + "^2 ^0 # # #"
              = "^4 ^1 # # ^2 ^0 # # #"
```

`ser(sub)` = `"^4 ^1 # # ^2 # #"` — **not** a substring of `"^4 ^1 # # ^2 ^0 # # #"`, because right after `^2` the root string has `^0` where sub's string has `#`. The extra branch breaks the match.

**Final output:** `False` ✓

### Step-by-step trace — `[1,1]` contains `[1]`

| String        | Value               |
| ------------- | ------------------- |
| `ser(sub)`  | `"^1 # #"`        |
| `ser(root)` | `"^1 ^1 # # # #"` |

`"^1 # #"` appears inside `ser(root)` (at the right child position) → **`True`** ✓

### Mental model

- Turn trees into "DNA strings" that encode **both values and shape**.
- `^` before each value and `#` for empties prevent digit-merging false positives.
- Subtree problem becomes plain string containment.

### Common confusions

- **No markers → false positives:** Serializing `12` and `2` without delimiters can wrongly match.
- **Missing `#` for nulls:** `[1]` vs `[1, null, 1]` need different strings — null markers matter.
- **`in` is not always O(n):** Python's substring search is O(len(root_str) · len(sub_str)) worst case, but still O(m+n) tree building dominates conceptually.

### Complexity

- **Time:** `O(m + n)` to build both strings + substring search
- **Space:** `O(m + n)` for the two serialized strings

---

## Quick reference

| Function              | Technique               | `[3,4,5,1,2]` ⊃ `[4,1,2]` | Extra`0` case | Time        | Space      |
| --------------------- | ----------------------- | ------------------------------ | --------------- | ----------- | ---------- |
| `is_subtree_brute`  | Same-tree at every node | `True`                       | `False`       | `O(m·n)` | `O(h)`   |
| `is_subtree_serial` | Serialize + substring   | `True`                       | `False`       | `O(m+n)`  | `O(m+n)` |

## Patterns to remember

- **Reuse a sub-check:** "do X at every node" — brute force pattern for many tree problems.
- **Serialize to compare shape:** delimiters + null markers turn structure into strings.
- **Signal words:** subtree, contained in, matching sub-structure.
- **Related problems:** Same Tree, Serialize and Deserialize Binary Tree, Symmetric Tree.
