# Company Hierarchy

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Trees · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

**Lowest Common Manager in an M-ary Tree**

You are given the root of an M-ary tree representing a company hierarchy and a list of employee names. Return the lowest common manager for all employees in the list.

Each node represents:
- The company (root)
- A department or team (internal nodes)
- An employee (leaf node)

All node names are unique.

### Example 1

```
              Company
             /   |    \
          Sales Tech   HR
          /  \  / | \
      Alice Bob Carl Dan Eva
```

Input:

```python
root = "Company"
nodes = ["Alice", "Bob"]
```

Output:

```
"Sales"
```

### Example 2

Same tree.

Input:

```python
root = "Company"
nodes = ["Alice", "Dan"]
```

Output:

```
"Company"
```

---

## Study Tools

### Hint 1

Think about what information a node needs from each of its children to decide whether it's the answer: specifically, how many of the target employees live in each subtree.

### Hint 2

A post-order traversal works here. Each recursive call can return either a target node it found, the current LCA candidate, or `None`.

### Hint 3

If a node receives non-None results from two or more children, or is itself a target and gets a non-None from a child, it's the LCA. Otherwise propagate the single non-None result upward.

---

### Answer

This is a lowest common ancestor problem on an M-ary tree where the targets are a subset of nodes. You solve it with a single post-order DFS that returns a count of targets found in each subtree, and the first node where the count reaches the total number of targets is your answer.

```python
class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

def lowest_common_manager(root, target_names):
    targets = set(target_names)
    total_targets = len(targets)
    answer = None

    def dfs(node):
        nonlocal answer
        if node is None:
            return 0

        count = 1 if node.name in targets else 0

        for child in node.children:
            count += dfs(child)

        if count == total_targets and answer is None:
            answer = node

        return count

    dfs(root)
    return answer.name if answer else None
```

**Time:** O(n) — each node is visited exactly once, and set lookups are O(1) on average. **Space:** O(h) — recursion stack depth equals the tree height, which is O(n) in the worst case for a skewed tree.

**Correctness:** The DFS returns the number of target employees in the subtree rooted at each node. The first node (in post-order, so from the bottom up) where this count equals `total_targets` must be the lowest node whose subtree contains all targets, which is exactly the lowest common manager. The `answer is None` guard ensures we capture the lowest such node, not any ancestor above it.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force: for each target employee, trace the path from the root down to that employee, then find the deepest node common to all paths. Building each path takes O(h) time, and with k targets you'd spend O(k·h) time plus O(k·h) space to store the paths. That works, but you can do better.

The bottleneck is storing and comparing full paths. Instead, think about what you actually need from a subtree: just the count of target employees inside it. If you do a post-order traversal, each node can tally up the counts from all its children plus itself. The first node whose count hits k is the answer, because post-order visits children before parents, so you encounter the lowest qualifying node first.

A subtle detail: you need to stop the search once you find the answer, otherwise an ancestor will also have count k and overwrite it. The `answer is None` check handles that. Another edge case: if one target is an ancestor of another, the ancestor itself is the LCA, which this approach naturally handles since the ancestor's count will include itself and the descendant.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Define the node structure explicitly** — interviewers want to see you handle M-ary trees cleanly. A `Node` class with a `children` list keeps the traversal natural.
- **Use a set for target lookup** — converting the list to a set makes each membership check O(1), keeping the overall traversal O(n) instead of O(n·k).
- **Explain why post-order works** — the key insight is that you process children before parents, so the first node where the count reaches k is guaranteed to be the lowest one. State this before coding.
- **Guard against overwriting the answer** — the `answer is None` check is a small detail that prevents a bug. Mentioning it shows you've thought through the full recursion.
- **Discuss the space-time tradeoff** — the path-building approach uses O(k·h) space; the count-based DFS uses only O(h) for the stack. Being explicit about this comparison signals strong complexity analysis.
- **Handle the ancestor edge case** — if one target is the manager of another, the LCA is the ancestor itself. Your solution handles this naturally, but calling it out preempts a follow-up question.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the tree is extremely deep and you risk stack overflow?** — Consider an iterative post-order traversal or explicit stack to avoid recursion limits.
- **What if you need to answer multiple LCA queries on the same tree?** — Preprocess with binary lifting or Euler tour + RMQ to get O(log n) per query after O(n log n) preprocessing.
- **What if the tree changes over time (employees join or leave)?** — Look into dynamic LCA data structures or re-running the DFS when the tree is small enough.
- **How would you handle duplicate names if the uniqueness constraint were removed?** — You'd need to track node references or unique IDs instead of relying on name equality.
- **What if targets are given as node references instead of names?** — The solution simplifies since you can compare object identity directly, avoiding the set of strings.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page (including inside the ASCII tree diagram). These were stripped out and not acted on.
