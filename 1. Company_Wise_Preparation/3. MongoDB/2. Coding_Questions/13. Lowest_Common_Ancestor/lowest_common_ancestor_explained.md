# Lowest Common Ancestor — Explained Simply

## The Problem

Given two nodes in a binary tree, find the **deepest node that is an ancestor of both**.

The twist: every node has a **parent pointer**, so you can walk *upward*.

```
        3
      /   \
     5     1
    / \   / \
   6   2 0   8
      / \
     7   4

LCA(7, 1) = 3       LCA(6, 4) = 5       LCA(7, 4) = 2
```

## The Reframe That Solves It

Here's the whole insight:

> With parent pointers, **the chain of ancestors from any node up to the root is a linked list.**

Node 7's chain: `7 → 2 → 5 → 3`
Node 1's chain: `1 → 3`

Both chains end at the **same node** — the root. Two linked lists that end at the same node form a **Y shape**:

```
7 → 2 → 5 ↘
             3
        1 ↗
```

**The LCA is the point where they merge.**

So this isn't really a tree problem at all. It's "find where two linked lists intersect" wearing a tree costume — and recognising that is most of the answer.

## An Analogy First: Two Rivers Meeting the Sea

Two streams start at different points in the mountains. Both eventually flow into the same river, and that river reaches the sea.

You want to find the **confluence** — the exact spot where the two streams first become one body of water.

Walking downstream from each source, once you pass the confluence you're on the same water. The question is where that starts.

The obvious problem: one stream might be much longer than the other. If you walk one step at a time from each source, you'll be at different distances from the sea, comparing places that have nothing to do with each other.

**The fix:** measure how far each source is from the sea. Walk the *longer* stream forward by the difference first. Now both walkers are the same distance from the sea — and from that moment on, they arrive at the confluence **at the same time**.

That's the entire algorithm.

## Why "Align First" Is Necessary

Say you naively step both pointers up together:

```
p = 7 (depth 4)          q = 1 (depth 2)

step 1:  7 → 2           1 → 3
step 2:  2 → 5           3 → None
```

You're comparing node 2 against node 3 — nodes at completely different depths. That comparison is meaningless, and `q` runs off the top before `p` gets anywhere.

After aligning, both pointers are always at **the same depth**. So any common ancestor sits at some depth `d`, and both pointers reach depth `d` at the same moment. That means the **first** time they coincide is at the **greatest** depth — which is exactly the definition of *lowest*.

## Step-by-Step Example (Narrated)

`LCA(7, 1)` in the tree above.

---

**Step 1 — measure both depths.**

Walk up from each, counting:

```
7 → 2 → 5 → 3 → None      depth(7) = 4
1 → 3 → None              depth(1) = 2
```

---

**Step 2 — align.** `p` is 2 levels deeper, so climb it exactly twice:

```
p: 7 → 2        (depth 3)
p: 2 → 5        (depth 2)
```

Now `p = 5`, `q = 1`. **Both at depth 2.**

---

**Step 3 — walk together.**

Is `5` the same node as `1`? No. Climb both:

```
p: 5 → 3
q: 1 → 3
```

Is `3` the same node as `3`? **Yes.**

**LCA = 3** ✅

---

Total work: two walks up to measure, one aligning climb, one lockstep walk. All O(h), and the only memory used was **three integers and two pointers**.

## The Edge Case That Handles Itself

*What if one node is an ancestor of the other?* For instance `LCA(5, 4)` — node 5 is 4's grandparent.

```
depth(5) = 2,  depth(4) = 4
```

Align: climb `q` twice: `4 → 2 → 5`.

Now `q = 5` and `p = 5`. The lockstep loop checks `p is q` → **immediately true** → returns 5. ✅

**No special case needed.** The alignment step lands `q` directly on `p`. Worth tracing out loud in an interview, because it's the first thing you'll be asked about.

(This relies on the standard convention that a node counts as its own ancestor. If your interviewer wants a *strict* ancestor, say so and adjust.)

## The Approach You'll Think of First (and It's Fine)

Before the depth trick, most people reach for a **hash set**:

```python
seen = set()
node = p
while node:                 # record p's entire chain
    seen.add(id(node))
    node = node.parent

node = q
while node:                 # first of q's ancestors we've already seen
    if id(node) in seen:
        return node
    node = node.parent
```

This is genuinely good — O(h) time, simple, hard to get wrong. And since you're walking **up** from `q`, the first hit is automatically the *lowest*.

Its only cost is **O(h) memory** for the set.

The depth-alignment version does the same job with **O(1)** memory, because *depth already encodes position* — you don't need to remember which nodes you saw, just how far up you are.

> **The general lesson:** before reaching for a hash set, ask whether there's a **computable invariant** that gives you the same information for free.

## Comparing by Identity, Not by Value

Notice the code uses `is` and `id()`, never `==` or `node.val`.

The problem says "given two **nodes**" — two specific objects. If the tree has duplicate values (employee records with the same name, say), comparing `node.val` would happily return the wrong ancestor.

```python
while p is not q:      # ✅ identity
while p.val != q.val:  # ❌ breaks on duplicate values
```

## What If There Are No Parent Pointers?

Then you can't walk up at all, and the problem changes shape completely. You have to search **downward** from the root:

```python
def lca(root, p, q):
    if root is None or root is p or root is q:
        return root                     # found one - report it upward
    left  = lca(root.left,  p, q)
    right = lca(root.right, p, q)
    if left and right:
        return root                     # p and q are on opposite sides -> this is it
    return left or right                # only one side found something - pass it up
```

The idea: each node reports upward "did I find `p` or `q` below me?". **The first node that hears from *both* children is the LCA** — because any lower common ancestor would have had both nodes in a single subtree.

Note the trade:

| | With parent pointers | Without |
|---|---|---|
| Time | **O(h)** — just two root-paths | O(n) — may visit every node |
| Space | **O(1)** | O(h) recursion stack |

That's what the parent pointer buys you, and saying so explicitly is a strong talking point.

## Why It's Fast

The notebook benchmark uses a deliberately degenerate tree — one long chain, so `h = n`:

| Height | Nested walk | Hash set | Align + walk |
|---|---|---|---|
| 100 | 9.7 ms | 2.0 ms | 1.0 ms |
| 200 | 39.3 ms (4.0×) | 4.0 ms (2.0×) | 2.0 ms (2.0×) |
| 400 | 157 ms (4.0×) | 8.6 ms (2.2×) | 4.5 ms (2.2×) |
| 800 | 658 ms (4.2×) | 15.9 ms (1.9×) | 9.7 ms (2.2×) |

The naive nested walk **quadruples** — textbook quadratic, because it re-walks `q`'s whole chain once per ancestor of `p`. The two linear approaches **double**, and the alignment version is consistently about twice as fast as the hash set while using no memory at all.

## A Note on Complexity: O(h), Not O(n)

State it as **O(h)** — the height — and then add what that means:

- **Balanced tree:** h ≈ log n. Finding the LCA in a million-node balanced tree touches about 20 nodes.
- **Degenerate tree** (every node has one child): h = n, and you're back to linear.

Making that distinction unprompted is exactly what interviewers listen for.

## Common Mistakes

- **Walking both pointers up without aligning first.** You compare nodes at different depths, which is meaningless, and the shallower pointer runs off the top.
- **Comparing values instead of identities.** Breaks silently on duplicate values.
- **Special-casing "p is an ancestor of q".** It's already handled — adding a branch just gives you something else to get wrong.
- **Saying O(n) when you mean O(h).** They're the same only in the worst case.
- **Forgetting the disjoint-trees case.** If the nodes are in different trees, both pointers hit `None` at the same time and the loop ends with `p is q is None` — which is the right answer, but only because the loop was written to allow it.
- **Using recursion when you have parent pointers.** The whole point of the parent pointer is that you *don't* need a stack.

## The Takeaway

> A parent pointer turns a tree into a **linked list**, and two ancestor chains that meet at the root form a **Y**. Measure both lengths, skip the difference, then walk in lockstep — the first place they touch is the answer.

The "align, then walk together" technique shows up whenever you compare two sequences of unequal length: linked-list intersection, diffing, merge joins. And replacing a hash set with arithmetic — because *depth already tells you where you are* — is a move worth looking for every time you're about to allocate memory to remember something.
