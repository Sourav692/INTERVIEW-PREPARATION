# Lowest Common Ancestor of a Binary Tree — Explained Simply

## The Problem

Given a tree and two nodes `p` and `q` somewhere in it, find their **lowest common ancestor (LCA)** — the deepest node that is an ancestor of *both* `p` and `q` (a node can count as its own ancestor).

Example:

```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
      / \
     7   4

LCA(5, 1) = 3   (5 and 1 only meet at the root)
LCA(5, 4) = 5   (5 is itself an ancestor of 4)
```

Unlike a Binary Search Tree, a general binary tree has **no ordering** — you can't compare values to decide which way to go. You have to actually search.

## Why You Can't Just "Navigate" Like a BST

In a BST, you can compare `p` and `q` against the current node's value and know instantly whether to go left or right. In a *general* binary tree, values aren't sorted — 5 could be anywhere relative to 1. So there's no shortcut; you must explore the tree and see where `p` and `q` actually live.

## The Simple Trick: Ask Each Subtree "Do You Contain One of the Targets?"

Do a search (DFS) that, at every node, asks its left and right subtrees: *"Did you find `p` or `q` down there?"*

- If **both** the left and right subtree report "yes, I found one," then **this node** is the meeting point — it's the LCA, because `p` is on one side and `q` is on the other.
- If only one side reports "yes," pass that answer up — the LCA must be further down on that side (or it's this node itself, if this node IS `p` or `q`).
- If a node itself equals `p` or `q`, report itself immediately — no need to look further down that branch.

## Step-by-Step Example

```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
      / \
     7   4

Find LCA(5, 4)
```

Walk through the DFS:

| Node visited | What happens |
|---------------|----------------|
| 3 | Not p or q. Recurse left (5) and right (1). |
| 5 | 5 == p! Return node 5 immediately (no need to search its subtree for q). |
| 1 | Not p or q. Recurse left (0) and right (8) — neither finds anything. Return None. |
| Back at 3 | left = node 5, right = None → only one side found something → bubble up node 5. |

Result: **LCA(5, 4) = 5** ✅ (because 5 is itself an ancestor of 4 — the search short-circuits as soon as it hits node 5)

Now try `LCA(5, 1)`:

| Node visited | What happens |
|---------------|----------------|
| 3 | Recurse left (finds 5) and right (finds 1). |
| 5 | 5 == p → return node 5 |
| 1 | 1 == q → return node 1 |
| Back at 3 | left = node 5, right = node 1 → BOTH sides found something → node 3 is the LCA! |

Result: **LCA(5, 1) = 3** ✅

## Plain-English Walkthrough

1. If the current node is empty, or it equals `p` or `q`, return it immediately (or `None` if empty).
2. Otherwise, recursively search the left subtree and the right subtree.
3. If **both sides** come back with something found, the current node is the split point — it's the LCA.
4. If only **one side** found something, that's the answer so far — pass it up unchanged.
5. If **neither side** found anything, pass up `None`.

## Simple Python Code

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def lca(root, p, q):
    if root is None:
        return None
    if root.val == p or root.val == q:
        return root                      # found one of the targets — report it up

    left = lca(root.left, p, q)
    right = lca(root.right, p, q)

    if left and right:
        return root                      # p on one side, q on the other -> this IS the LCA
    return left or right                 # otherwise, pass up whichever side found something (or None)
```

## Why "If Both Sides Found Something, This Node Is the Answer"

Think about it physically: if `p` lives somewhere in the left subtree and `q` lives somewhere in the right subtree, the **only** node that "sees" both of them below it is the one sitting right above the split — the current node. Any node further down would only see one of the two targets, not both.

## Complexity

- **Time:** O(n) — in the worst case, you visit every node once.
- **Space:** O(height) — the recursion stack goes as deep as the tree is tall.

## The Reusable Pattern

This is the **"return-something-up DFS"** pattern: each subtree reports a signal back to its parent, and the parent combines the signals from its children to make a decision. It shows up in:
- Lowest Common Ancestor (this problem)
- Diameter of a Binary Tree
- Maximum Path Sum in a Binary Tree

Signal to recognize this pattern: "find the deepest point where two things meet" or "combine info from both children" in a tree with no ordering to exploit.
