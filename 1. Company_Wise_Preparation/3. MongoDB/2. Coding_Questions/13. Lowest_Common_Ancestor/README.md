# Lowest Common Ancestor

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Hash Tables, Trees · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Given two nodes of a binary tree `p` and `q`, return their **lowest common ancestor** (LCA).

Each node will have a reference to its **parent** node. The definition for `Node` is below:

```java
class Node {
    public int val;
    public Node left;
    public Node right;
    public Node parent;
}
```

---

## Study Tools

### Hint 1

You have parent pointers, so you can walk **upward** from either node. Think about where those two upward paths meet.

### Hint 2

Compute the **depth** of each node first. Then move the deeper node up until both nodes are at the same depth.

### Hint 3

Once both nodes are at the same depth, walk both pointers up one step at a time until they point to the same node. That node is the LCA.

---

### Answer

This is a lowest-common-ancestor problem where the parent pointers let you avoid a full tree traversal. The cleanest approach is to compute the depth of `p` and `q` by walking to the root, align the two nodes at the same depth, then move both pointers upward in lockstep until they meet. The meeting point is the LCA.

#### Solution

```java
class Solution {
    public Node lowestCommonAncestor(Node p, Node q) {
        int depthP = depth(p);
        int depthQ = depth(q);

        // Align the deeper node with the shallower one.
        while (depthP > depthQ) {
            p = p.parent;
            depthP--;
        }
        while (depthQ > depthP) {
            q = q.parent;
            depthQ--;
        }

        // Move both up until they point to the same node.
        while (p != q) {
            p = p.parent;
            q = q.parent;
        }

        return p;
    }

    private int depth(Node node) {
        int d = 0;
        while (node != null) {
            node = node.parent;
            d++;
        }
        return d;
    }
}
```

**Time:** O(h) — two depth walks plus one aligned climb, where h is the tree height.
**Space:** O(1) — only a few pointers and counters.

**Correctness** follows from the fact that both nodes share exactly one ancestor at each depth above the LCA. Once aligned at the same depth, the first common node encountered by simultaneous upward steps must be the lowest one, because any lower common ancestor would have been encountered earlier.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute-force idea: record the entire ancestor chain of `p` in a set, then walk up from `q` and return the first node already in that set. That's O(h) time and O(h) space, which is already reasonable, but you can do better on space.

The observation that unlocks the O(1)-space version is that both ancestor chains **end at the root**. If you knew how deep each node is, you could skip the extra nodes from the deeper chain and then just compare step by step. So the first decision is to write a helper that computes depth by following parent pointers until `null`. That costs O(h) time and no extra space.

With depths in hand, the second decision is to **align** the two nodes. Move the deeper one up until both have the same depth. Now the remaining upward paths have equal length, so the LCA is exactly the first node where the two pointers coincide. Walk both up one parent at a time until they're equal. No hash set, no recursion stack, just three simple loops.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State the tree-height complexity honestly** — you can say O(h) where h is the height, and note that in a balanced tree this is O(log n) while in a skewed tree it degrades to O(n). Interviewers listen for that distinction.
- **Contrast with the no-parent-pointer version** — mentioning that without parent pointers you'd do a recursive DFS with O(h) stack space shows you understand the trade-off the parent pointer buys you.
- **Handle the edge case where one node is the ancestor of the other** — the alignment loop naturally handles it, but call it out explicitly and trace it once so the interviewer sees you've thought about it.
- **Defend the O(1) space claim** — your depth helper uses only an integer counter, and the main method uses two pointers. No hidden recursion or collection allocations.
- **Consider the null-parent case implicitly** — every node is guaranteed to have a parent until the root, so walking past the root would return `null`, and your depth loop terminates.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the tree has no parent pointers?** — Think about a single recursive traversal that returns the first node whose left and right subtrees each contain one of the targets.
- **What if you need to answer LCA queries for many pairs on the same tree?** — Preprocess with binary lifting or an Euler tour plus RMQ to get O(log n) or O(1) per query.
- **What if the nodes are given by value instead of reference?** — You'd need to locate them first, which requires a traversal, and then apply the same parent-pointer logic.
- **How would this change for a general tree with an arbitrary number of children?** — The depth-and-align approach still works since the parent chain is still a linear path to the root.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Language note:** the official answer is written in Java. The accompanying notebook implements the same three algorithms in Python so every claim is executable and testable; the Java reference above is reproduced unchanged.
