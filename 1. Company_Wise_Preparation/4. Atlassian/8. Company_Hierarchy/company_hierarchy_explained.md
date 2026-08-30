# Company Hierarchy — Explained Simply

## The Problem

Given a company org chart (a tree: Company → Departments → Employees) and a list of employee names, find the **lowest common manager** — the deepest node whose subtree contains every one of those employees.

```
Company
├── Sales -> [Alice, Bob]
├── Tech  -> [Carl, Dan]
└── HR    -> [Eva]

nodes = ["Alice", "Bob"]   -> "Sales"    (both directly under Sales)
nodes = ["Alice", "Dan"]   -> "Company"  (only Company contains both)
```

## Why the Obvious Way Is Slow

The obvious approach: for each target employee, walk from the root down to find them, recording the full path. Then compare all the paths to find where they last agree.

```
paths = [path_from_root_to("Alice"), path_from_root_to("Dan")]
# walk all paths together from the root; the last node where they still agree is the answer
```

This works, but building each path means searching the *entire tree* from the root for every single target — in the worst case, a search for one target has to fully explore unrelated branches before stumbling onto the right one. With k targets, that's k separate full-tree searches, each potentially touching every node.

## The Simple Trick: Ask Each Subtree "How Many Targets Are You Hiding?"

Instead of tracing paths down to each target individually, do **one single pass** over the whole tree. Every node reports back a single number: "how many of the target employees exist somewhere inside me?" The first node — found while working from the leaves upward — whose count reaches the *full* number of targets is, by definition, the lowest node containing all of them.

## An Analogy First: A Lost-and-Found Search Party

Imagine a search party looking for 2 specific missing hikers, spread out across a mountain that branches into trails, then sub-trails, then paths. Instead of one person tracing hiker #1's exact path and a separate person tracing hiker #2's exact path and then comparing notes, you send searchers to fan out and each one reports upward: "I found 0 hikers in my area," "I found 1 hiker," etc.

Each junction on the mountain adds up what its own branches reported, plus checks if it *is* one of the hikers itself. The very first junction — checking from the smallest branches outward — that can say "both hikers are somewhere under me" is exactly the lowest point on the mountain that's a common ancestor of both hikers' locations. Any junction higher up the mountain would *also* be able to say that, but it wouldn't be the lowest one, so you stop at the first junction that reaches 2.

## Step-by-Step Example (Narrated)

Tree: `Company -> {Sales -> [Alice, Bob], Tech -> [Carl, Dan], HR -> [Eva]}`. Targets: `["Alice", "Dan"]` (2 targets total).

We visit nodes in **post-order** — process every child completely before combining into the parent.

---

**Visit `Alice` (a leaf)**
Is "Alice" one of our targets? Yes → count = 1. No children to add. Return 1.
Does 1 equal our target total (2)? No — keep going.

---

**Visit `Bob` (a leaf)**
Is "Bob" a target? No → count = 0. Return 0.

---

**Visit `Sales` (now that both children, Alice and Bob, are done)**
Is "Sales" itself a target? No → start at 0.
Add Alice's count (1) → running total 1.
Add Bob's count (0) → running total 1.
Return 1. Does 1 equal 2? No — Sales alone doesn't contain both targets. Nothing recorded yet.

---

**Visit `Carl` (a leaf)** — not a target → return 0.

**Visit `Dan` (a leaf)** — **is** a target → return 1.

**Visit `Tech`** — not a target itself. Add Carl (0) + Dan (1) → return 1. Does 1 equal 2? No.

---

**Visit `Eva` (a leaf)** — not a target → return 0.

**Visit `HR`** — not a target itself. Add Eva (0) → return 0.

---

**Visit `Company` (now that Sales, Tech, and HR are all done)**
Is "Company" itself a target? No → start at 0.
Add Sales's count (1) → running total 1.
Add Tech's count (1) → running total 2.
Add HR's count (0) → running total 2.
**Does 2 equal our target total (2)? Yes!** — and no node below has claimed the answer yet (`answer is None`) → **record `Company` as the answer.**

---

Final answer: **`"Company"`** — matches the expected output exactly.

### The one detail that's easy to miss: stop recording after the first match

Once `Company` claims the answer, any node *above* `Company` (if there were one) would *also* see a count of 2 and could try to overwrite the answer. The `if count == total and answer is None` guard prevents that — post-order guarantees the first node to reach the full count, scanning from the bottom up, is the **lowest** one, so we lock in that answer and never overwrite it.

## Plain-English Walkthrough

1. Put all target names in a set (so checking "is this a target?" is instant).
2. Visit the tree with a function that, for each node, first fully processes all of its children.
3. That function returns a count: 1 if this node itself is a target, plus the sum of what every child returned.
4. The moment a node's count equals the total number of targets, and no answer has been recorded yet, that node **is** the lowest common manager.

## Simple Python Code

```python
class Node:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

def lowest_common_manager(root, target_names):
    targets = set(target_names)
    total = len(targets)
    answer = [None]   # use a list so the nested function can update it

    def dfs(node):
        count = 1 if node.name in targets else 0
        for child in node.children:
            count += dfs(child)
        if count == total and answer[0] is None:
            answer[0] = node
        return count

    dfs(root)
    return answer[0].name if answer[0] else None

company = Node("Company", [
    Node("Sales", [Node("Alice"), Node("Bob")]),
    Node("Tech", [Node("Carl"), Node("Dan")]),
    Node("HR", [Node("Eva")]),
])
print(lowest_common_manager(company, ["Alice", "Dan"]))   # Company
print(lowest_common_manager(company, ["Alice", "Bob"]))   # Sales
```

## Why Does This Work for *Any* Number of Targets, Not Just 2?

Classic "lowest common ancestor" problems are often taught for exactly 2 nodes, with special-cased logic. This counting approach doesn't care how many targets there are — `total` could be 1, 2, or 50. A single target is even handled for free: with `total = 1`, the very first node that *is* the target already has count 1, so it becomes its own answer, correctly.

## Complexity

- **Time:** O(n) — every node is visited exactly once, and checking "is this a target?" against a set is O(1).
- **Space:** O(h) for the recursion stack, where h is the tree's height (worst case O(n) for a very skewed tree).

## The Reusable Pattern

This is the **"post-order count, first-to-reach-the-target wins"** pattern — a generalization of Lowest Common Ancestor:
- LCA of two nodes in a binary tree (the k=2 special case)
- "Deepest node containing all of a set of markers/tags"
- Any "smallest subtree satisfying a property" question

Core idea: instead of comparing paths, have every subtree report a single summary number, and let the traversal's natural bottom-up order guarantee you find the *lowest* qualifying node first.
