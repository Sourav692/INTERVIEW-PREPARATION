# Serialize and Deserialize Binary Tree — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Tree/serialize_and_deserialize_binary_tree.ipynb`  
> **LeetCode:** [297. Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/)  
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
|-------|----------|
| Goal | Convert a tree to a string and rebuild it **exactly** |
| Encoding | Preorder DFS: write each value, write `#` for every empty child |
| Decoding | Read tokens in the **same order**; `#` → `None`, else create node and fill left then right |
| Why markers | Without null markers, shape is ambiguous (can't tell missing children from "not yet written") |

**Canonical tree from `[1, 2, 3, None, None, 4, 5]`:**

```
    1
   / \
  2   3
     / \
    4   5
```

Expected outputs (from notebook asserts):

| Input | Serialized | Round-trip |
|-------|------------|------------|
| `[1, 2, 3, None, None, 4, 5]` | `"1,2,#,#,3,4,#,#,5,#,#"` | `same_shape == True` |
| `[1]` | `"1,#,#"` | `True` |
| `[]` | `"#"` | `True` |
| `[5, 4, 7, 3, None, 2, None, -1, None, 9]` | `"5,4,3,-1,#,#,#,#,7,2,9,#,#,#,#"` | `True` |

---

## `serialize` — preorder with null markers

### What it does

Walks the tree in preorder (node → left → right), appending each value and `#` for every `None` child, then joins with commas.

### Code

```python
def serialize(root: Optional[TreeNode]) -> str:
    out = []
    def dfs(n):                            # preorder walk, writing '#' for empty children
        if not n:
            out.append("#")               # marker records where a child is missing
            return
        out.append(str(n.val))            # record this node's value
        dfs(n.left); dfs(n.right)         # then its left subtree, then its right
    dfs(root)
    return ",".join(out)                  # e.g. "1,2,#,#,3,#,#"
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `out = []` | Collects tokens in visit order |
| `def dfs(n)` | Inner preorder DFS |
| `if not n: out.append("#"); return` | Empty spot → write marker so shape is recoverable |
| `out.append(str(n.val))` | Write this node's value |
| `dfs(n.left); dfs(n.right)` | Preorder: left subtree fully, then right subtree fully |
| `dfs(root)` | Start from root (if `root` is `None`, first call writes `#`) |
| `return ",".join(out)` | Single comma-separated string |

### Step-by-step trace — `serialize(root)` on `[1, 2, 3, None, None, 4, 5]`

**Tree:**

```
    1
   / \
  2   3
     / \
    4   5
```

**Initial state:**

| Variable | Value |
|----------|-------|
| `out` | `[]` |

| Step | Call / visit | Action | `out` after |
|------|--------------|--------|-------------|
| 1 | `dfs(1)` | append `"1"` | `["1"]` |
| 2 | `dfs(2)` | append `"2"` | `["1","2"]` |
| 3 | `dfs(None)` left of 2 | append `"#"` | `["1","2","#"]` |
| 4 | `dfs(None)` right of 2 | append `"#"` | `["1","2","#","#"]` |
| 5 | `dfs(3)` | append `"3"` | `["1","2","#","#","3"]` |
| 6 | `dfs(4)` | append `"4"` | `["1","2","#","#","3","4"]` |
| 7 | `dfs(None)` left of 4 | append `"#"` | `[...,"#"]` |
| 8 | `dfs(None)` right of 4 | append `"#"` | `[...,"#","#"]` |
| 9 | `dfs(5)` | append `"5"` | `[...,"5"]` |
| 10 | `dfs(None)` left of 5 | append `"#"` | `[...,"#"]` |
| 11 | `dfs(None)` right of 5 | append `"#"` | `[...,"#","#"]` |

**Join:** `"1,2,#,#,3,4,#,#,5,#,#"`

**Final output:** `"1,2,#,#,3,4,#,#,5,#,#"` ✓ (matches notebook assert)

---

### Step-by-step trace — `[1]` → `"1,#,#"`

| Step | Visit | `out` after |
|------|-------|-------------|
| 1 | node `1` | `["1"]` |
| 2 | left `None` | `["1","#"]` |
| 3 | right `None` | `["1","#","#"]` |

**Final output:** `"1,#,#"` ✓

---

### Step-by-step trace — `[]` (empty tree) → `"#"`

| Step | Visit | `out` after |
|------|-------|-------------|
| 1 | `dfs(None)` on empty root | `["#"]` |

**Final output:** `"#"` ✓

### Mental model

- Preorder uniquely identifies structure **if** you record where children are missing.
- Every `None` child gets its own `#` — two per leaf node.

### Common confusions

- **Omitting `#` markers:** `"1,2,3"` is ambiguous — can't tell if `2` and `3` are left/right children or something else.
- **Empty tree:** `serialize(None)` correctly produces `"#"` (one marker for the missing root).

### Complexity

- **Time:** `O(n)` — visit every node and every null child slot once
- **Space:** `O(n)` — output list size is `2n+1` tokens in worst case (full tree)

---

## `deserialize` — rebuild by reading tokens in write order

### What it does

Splits the string into tokens, reads them with an iterator in preorder order: `#` → `None`, otherwise create a `TreeNode` and recursively attach left then right children.

### Code

```python
def deserialize(data: str) -> Optional[TreeNode]:
    vals = iter(data.split(","))          # read tokens in the SAME order serialize wrote them
    def build():
        v = next(vals)
        if v == "#":                      # a '#' means "no node here"
            return None
        node = TreeNode(int(v))
        node.left = build()               # rebuild left subtree first (matches preorder)
        node.right = build()              # then the right subtree
        return node
    return build()
```

### Line by line

| Line / code | What it does |
|-------------|--------------|
| `vals = iter(data.split(","))` | Token stream in left-to-right order (same as serialize wrote) |
| `def build()` | Recursive preorder builder — one call = one tree position |
| `v = next(vals)` | Consume the next token |
| `if v == "#": return None` | Marker → no node at this position |
| `node = TreeNode(int(v))` | Real value → create node |
| `node.left = build()` | Left subtree is encoded immediately after this node in preorder |
| `node.right = build()` | Right subtree follows left subtree's encoding |
| `return node` | Fully wired subtree rooted here |
| `return build()` | Build from the first token (root position) |

### Step-by-step trace — `deserialize("1,2,#,#,3,4,#,#,5,#,#")`

**Token queue (front → back):**

```
[1, 2, #, #, 3, 4, #, #, 5, #, #]
 ↑ front (next)
```

| Step | `build()` call | `next(vals)` | Action | Tree built so far (conceptual) |
|------|----------------|--------------|--------|--------------------------------|
| 1 | root `build()` | **1** | create node `1` | `1` |
| 2 | left of `1` | **2** | create node `2` | `1` / `2` |
| 3 | left of `2` | **#** | `None` | `2` has no left |
| 4 | right of `2` | **#** | `None` | `2` is a leaf |
| 5 | right of `1` | **3** | create node `3` | `1` / `2`, `3` |
| 6 | left of `3` | **4** | create node `4` | `3` / `4` |
| 7 | left of `4` | **#** | `None` | |
| 8 | right of `4` | **#** | `None` | `4` is a leaf |
| 9 | right of `3` | **5** | create node `5` | `3` / `4`, `5` |
| 10 | left of `5` | **#** | `None` | |
| 11 | right of `5` | **#** | `None` | `5` is a leaf; tokens exhausted |

**Rebuilt tree:**

```
    1
   / \
  2   3
     / \
    4   5
```

**Final output:** tree identical to input ✓ (`same_shape(root, back) == True`)

---

### Step-by-step trace — `deserialize("1,#,#")` → single node

| Step | Token | Action |
|------|-------|--------|
| 1 | **1** | create node `1` |
| 2 | **#** | `1.left = None` |
| 3 | **#** | `1.right = None` |

**Final output:** lone node `1` ✓

---

### Step-by-step trace — `deserialize("#")` → empty tree

| Step | Token | Action |
|------|-------|--------|
| 1 | **#** | return `None` |

**Final output:** `None` ✓ (matches `build_tree([])`)

---

### Step-by-step trace — round-trip on `[5, 4, 7, 3, None, 2, None, -1, None, 9]`

**Serialized:** `"5,4,3,-1,#,#,#,#,7,2,9,#,#,#,#"`

**Tree shape:**

```
      5
     / \
    4   7
   /   /
  3   2
 /     \
-1      9
```

**First 8 `build()` token reads:**

| Step | Token | Creates / returns |
|------|-------|-------------------|
| 1 | `5` | node `5` |
| 2 | `4` | node `4` (left of 5) |
| 3 | `3` | node `3` (left of 4) |
| 4 | `-1` | node `-1` (left of 3) |
| 5 | `#` | `None` (left of -1) |
| 6 | `#` | `None` (right of -1) |
| 7 | `#` | `None` (right of 3) |
| 8 | `#` | `None` (right of 4) |

Remaining tokens `7, 2, 9, #, #, #, #` wire the right subtree of `5` the same way.

**Final output:** `same_shape(root, back) == True` ✓ (notebook assert)

### Mental model

- **Mirror serialize exactly:** every `build()` call consumes one token — same as one `dfs()` visit.
- **Iterator is the queue:** `next(vals)` always reads the next preorder position; no index juggling needed.
- **Left before right is mandatory:** preorder encodes left subtree before right subtree.

### Common confusions

- **Reading in wrong order:** level-order deserialize won't match preorder serialize.
- **Forgetting null markers on serialize:** deserialize will read wrong tokens and build a malformed tree.
- **Empty string:** `"".split(",")` → `[""]` — not the same as `"#"`; the notebook uses `serialize(None)` → `"#"`.

### Complexity

- **Time:** `O(n)` — one token per tree position
- **Space:** `O(n)` — token list + recursion stack `O(h)`

---

## Round-trip helper (from notebook tests)

```python
def roundtrip(root):
    return deserialize(serialize(root))
```

| Input | Serialized | `same_shape` |
|-------|------------|--------------|
| `[1,2,3,None,None,4,5]` | `1,2,#,#,3,4,#,#,5,#,#` | `True` |
| `[1]` | `1,#,#` | `True` |
| `[]` | `#` | `True` |
| `[5,4,7,3,None,2,None,-1,None,9]` | `5,4,3,-1,#,#,#,#,7,2,9,#,#,#,#` | `True` |

---

## Quick reference

| Function | Order | Output on canonical tree |
|----------|-------|--------------------------|
| `serialize` | Preorder + `#` for nulls | `"1,2,#,#,3,4,#,#,5,#,#"` |
| `deserialize` | Same preorder read order | Rebuilds original tree |
| `roundtrip` | serialize → deserialize | `same_shape == True` |

## Patterns to remember

- **Preorder + null markers = lossless snapshot** — shape and values fully captured.
- **Write order = read order** — deserialize mirrors serialize call-for-call.
- **Signal phrases:** "serialize/deserialize", "encode tree to string", "restore exact structure."
