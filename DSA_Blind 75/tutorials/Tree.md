# 🌳 Tree — Concept Tutorial

> A plain-language guide to the ideas behind the Blind 75 **Tree** problems, with diagrams.
> Pair this with `visualizations/Tree/` and `notebooks/Tree/`.

---

## 1. What is a Binary Tree?

A **binary tree** is nodes in a branching shape. Each node holds a value and up to **two children** — a **left** and a **right**. The top node is the **root**; nodes with no children are **leaves**.

```mermaid
graph TD
    A["3 (root)"] --> B["9"]
    A --> C["20"]
    C --> D["15 (leaf)"]
    C --> E["7 (leaf)"]
```

- **Height** = the longest path from root to a leaf.
- Most tree problems are solved by **recursion**: *"solve a node by combining the answers of its children."*

---

## 2. The Two Ways to Walk a Tree

### 🌊 DFS (Depth-First Search) — go deep first

Dive down one branch as far as possible, then back up. Written with recursion.

```mermaid
graph TD
    A["1"] --> B["2"]
    A --> C["3"]
    B --> D["4"]
    B --> E["5"]
    A:::o
    B:::o
    D:::o
    E:::o
    C:::o
    classDef o fill:#e5edff,stroke:#3563e9;
```
*Visit order (preorder): 1 → 2 → 4 → 5 → 3.*

### 🪣 BFS (Breadth-First Search) — go level by level

Use a **queue**: take a node, add its children to the back, repeat. Perfect for "by level" problems.

```mermaid
flowchart LR
    Q["Queue"] --> L0["level 0: [3]"] --> L1["level 1: [9, 20]"] --> L2["level 2: [15, 7]"]
```

**Rule of thumb:** *"level / depth / shortest steps"* → **BFS**. Everything else → **DFS**.

---

## 3. Traversal Orders (and why they matter)

```mermaid
graph TD
    A["1"] --> B["2"]
    A --> C["3"]
```

| Order | Rule | On the tree above |
|---|---|---|
| **Preorder** | node, left, right | 1, 2, 3 |
| **Inorder** | left, node, right | 2, 1, 3 |
| **Postorder** | left, right, node | 2, 3, 1 |

Two facts to memorize:
- **Preorder's first value is always the root** → used to rebuild trees.
- **Inorder of a BST comes out sorted** → used to validate and rank.

**Problems:** Construct Binary Tree from Preorder & Inorder, Serialize/Deserialize.

---

## 4. Binary Search Tree (BST) — the ordered tree

In a BST, for **every** node: everything on the **left is smaller**, everything on the **right is larger**.

```mermaid
graph TD
    A["6"] --> B["2"]
    A --> C["8"]
    B --> D["0"]
    B --> E["4"]
    C --> F["7"]
    C --> G["9"]
```

Two superpowers:
1. **In-order walk = sorted values** (0,2,4,6,7,8,9) → validate a BST, find the k-th smallest.
2. **Navigate by comparison** — to find where two values split, go left if both are smaller, right if both are larger. This is `O(height)`, not `O(n)`.

```mermaid
flowchart TD
    S["at a node"] --> Q{"targets vs node"}
    Q -->|both smaller| GL["go left"]
    Q -->|both larger| GR["go right"]
    Q -->|they split| A["this is the answer ✅"]
```

**Problems:** Validate BST, Kth Smallest in BST, Lowest Common Ancestor of a BST.

---

## 5. The "Return One Thing, Track Another" Trick

For problems where the best answer can appear **anywhere** (not just at the root), a single DFS both **returns** a value to its parent and **updates a global best**.

```mermaid
flowchart TD
    N["at node n"] --> L["best downward arm on the left"]
    N --> R["best downward arm on the right"]
    L --> G["update GLOBAL best = n + left + right<br/>(a path that BENDS through n)"]
    R --> G
    G --> Ret["RETURN to parent: n + max(left, right)<br/>(only one arm — a parent's path can't split)"]
```

**Problems:** Binary Tree Maximum Path Sum (and Diameter of a Tree).

---

## 6. Trie (Prefix Tree) — a tree of letters

A **trie** stores words letter by letter, so words sharing a start share a path. A marker (`$`) flags where a word ends.

```mermaid
graph TD
    R["•(root)"] --> A["a"]
    A --> P1["p"]
    P1 --> P2["p ($ = 'app')"]
    P2 --> L["l"]
    L --> E["e ($ = 'apple')"]
    P1 --> T["t ($ = 'apt')"]
```

- Insert / search / prefix-check a word of length L is **O(L)** — no matter how many words are stored.
- Add a small DFS at a `.` wildcard to branch into all children.

**Problems:** Implement Trie, Add and Search Word, Word Search II (trie + grid backtracking).

---

## 7. Which Pattern for Which Problem?

```mermaid
mindmap
  root((Tree))
    DFS recursion
      Maximum Depth
      Same Tree
      Invert Tree
    BFS queue
      Level Order Traversal
    BST order
      Validate BST
      Kth Smallest
      Lowest Common Ancestor
    Traversal orders
      Construct from Pre+Inorder
      Serialize / Deserialize
    Return + global best
      Max Path Sum
    Trie
      Implement Trie
      Add and Search Word
      Word Search II
```

---

## 8. Complexity Cheat Sheet

| Task | Time | Space |
|---|---|---|
| Full traversal (DFS/BFS) | `O(n)` | `O(height)` / `O(width)` |
| BST navigation | `O(height)` | `O(1)`–`O(height)` |
| Trie op (word length L) | `O(L)` | `O(total letters)` |

---

## 9. Interview Playbook

1. **Reach for recursion:** "solve each node by combining its children," and say the **base case** (empty node) out loud.
2. **Spot the tell:** levels → *BFS*; it's a BST → *in-order is sorted* / *navigate by comparison*; rebuild/save → *traversal orders + null markers*; answer anywhere → *return one arm, track a global best*; prefixes/many words → *trie*.
3. **Mind the edges:** empty tree, single node, and very deep (skewed) trees where recursion could get tall.

> ▶ **Next:** open `visualizations/Tree/index.html` to watch these traversals and tricks animate.
