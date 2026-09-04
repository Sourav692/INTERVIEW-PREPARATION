# K-Way Merge — Explained Simply

## The Problem

You have `k` linked lists. Each one is **already sorted**. Combine them into a single sorted list.

```
1 -> 4 -> 5
1 -> 3 -> 4
2 -> 6

result:  1 -> 1 -> 2 -> 3 -> 4 -> 4 -> 5 -> 6
```

## Why the Obvious Way Wastes the Gift

The obvious approach: walk every list, collect all the values into one big array, sort it, rebuild.

```
values = [1,4,5, 1,3,4, 2,6]
values.sort()
```

It works. But look at what you just did: you took data that was **already sorted** and sorted it again from scratch.

Sorting costs `N log N`. The merge should cost `N log k` — and `k` (the number of lists, maybe 3) is usually much smaller than `N` (the total number of values, maybe 10,000). `log 3` versus `log 10000` is a factor of eight, thrown away for nothing.

## The Key Insight: The Answer Is Always at a Head

Here's the observation that unlocks everything:

> Every list is sorted, so the **smallest value you haven't used yet** must be at the **front** of one of the lists.

It cannot be buried in the middle of a list, because everything behind a list's front is larger than the front.

So you never search. You only ever ask one question, over and over:

> **"Which of the `k` fronts is the smallest?"**

Take that one, move that list's front forward one step, and ask again.

## An Analogy First: The Supermarket Checkout

Picture `k` checkout queues. In each queue, people are already lined up **shortest to tallest** — that's the sortedness you were given.

You need to let everyone out through one door, shortest first overall.

You don't need to survey the entire shop. You only look at the **person at the front of each queue** and wave out the shortest of those. Then the next person in *that* queue steps forward, and you look again.

- With **3 queues**, comparing 3 faces each time is trivial.
- With **10,000 queues**, comparing 10,000 faces for every single person is a nightmare — and you're re-doing almost all of that comparison work every round, since only one queue changed.

The fix is to keep the front-of-queue people organised in a way that always knows who's shortest without re-checking everyone. That's a **min-heap**.

## What Is a Min-Heap?

A min-heap is a container built on one rule:

> **Every parent is smaller than or equal to its children.**

That single rule guarantees the smallest item is at the very top — readable instantly. Adding an item or removing the top costs about `log k` steps (the item bubbles up or down a tree of depth `log k`), not `k`.

The crucial thing is that a heap **remembers**. When one queue changes, the heap only needs to reposition that one item. The linear scan throws away everything it learned and starts over each round.

In Python it's just a list with `heapq` functions:

```
heapq.heappush(heap, item)     # add
smallest = heapq.heappop(heap) # remove and return the smallest
```

## Step-by-Step Example (Narrated)

`lists = [1→4→5, 1→3→4, 2→6]`

**Seed the heap** with the front of each list. Each entry records the value, which list it came from, and the node itself:

```
heap = [ (1, list0), (1, list1), (2, list2) ]
```

The heap holds **3 entries** — one per list. It will never hold more.

---

**Pop the smallest: `(1, list0)`.** Attach that node to the result. Then look at what came after it in list 0 — that's `4` — and push it back:

```
result: 1
heap:   [ (1, list1), (2, list2), (4, list0) ]
```

*Only list 0 was touched. Lists 1 and 2 kept their places in the heap for free.*

---

**Pop `(1, list1)`.** Attach it. Push its successor, `3`:

```
result: 1 -> 1
heap:   [ (2, list2), (3, list1), (4, list0) ]
```

---

**Pop `(2, list2)`.** Attach. Push `6`:

```
result: 1 -> 1 -> 2
heap:   [ (3, list1), (4, list0), (6, list2) ]
```

---

**Pop `(3, list1)`.** Attach. Push `4`:

```
result: 1 -> 1 -> 2 -> 3
heap:   [ (4, list0), (4, list1), (6, list2) ]
```

---

Continue: pop `4`, pop `4`, pop `5` (list 0 is now empty, so nothing gets pushed back), pop `6`.

```
result: 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> 5 -> 6   ✅
heap:   empty  ->  done
```

**Why the heap never exceeds `k`:** you only push a replacement **after** you pop. One out, one in. That's what bounds memory at `k` (the number of lists) rather than `N` (the total values).

## The Python Trap That Will Break Your Code

This is the detail that separates "I've written this" from "I've sketched this".

The natural thing to push is `(value, node)`:

```
heapq.heappush(heap, (node.val, node))
```

It works... until two nodes have the **same value**. Then Python compares the tuples: the first elements tie, so it moves on to compare the second elements — `node < node` — and linked-list nodes have no `<` operator.

```
TypeError: '<' not supported between instances of 'ListNode' and 'ListNode'
```

In our example, list 0 and list 1 **both start with 1**. This crashes on the very first pop.

**The fix** is to slip a unique integer in between:

```
heapq.heappush(heap, (node.val, i, node))
                              ^-- the list's index
```

Now when values tie, Python compares the indexes — which are always distinct integers — and **never reaches the node at all**.

> **General rule:** if you put objects in a heap, always include a unique tiebreaker before them in the tuple.

## The Dummy Head Trick

When building a linked list, the first node is always awkward:

```
if result is None:
    result = node
    tail = node
else:
    tail.next = node
    tail = node
```

That branch appears every single time. Instead, start with a **throwaway node**:

```
dummy = ListNode()
tail = dummy

# now this always works, no branch:
tail.next = node
tail = node

return dummy.next        # the real answer starts after the dummy
```

One line of setup removes a branch from your hot loop and a whole class of null-pointer bugs.

## One More Trap: Cut the Tail Loose

When you splice the final node onto your result, that node **still points at whatever followed it in its original list**.

If you don't clear it, you either append a stale leftover chunk, or — in the divide-and-conquer variant — create a **cycle**, and anything walking the result loops forever.

```
tail.next = None       # one line, do not skip it
```

## The Other Good Answer: Divide and Conquer

There's a second approach worth knowing, because it answers a follow-up the heap can't.

Merging **two** sorted lists is easy — it's just two pointers, no heap needed. So run a tournament:

```
round 1:  [A, B, C, D, E, F, G, H]
           \_/   \_/   \_/   \_/
round 2:  [ AB,   CD,   EF,   GH ]
             \___/       \___/
round 3:  [   ABCD,       EFGH   ]
                \_________/
round 4:  [      ABCDEFGH        ]
```

**Why it's also `N log k`:** there are `log k` rounds, and each round touches every value at most once — so each round is `N`.

**Why you might prefer it:** no heap, no tuples, no tiebreaker trap, and it uses **O(1) extra space** — it just relinks the nodes you already have. That's the answer to *"can you do this without extra memory?"*, because the heap version always costs `O(k)`.

**Why you might not:** the pairing loop is fiddlier to get right under time pressure.

> In an interview: lead with the heap (it's the expected answer, and it generalises to streaming). Then offer divide-and-conquer as the O(1)-space alternative. Naming both is what makes it a strong pass.

## Why It's Fast

The notebook benchmark holds the **total values fixed at 20,000** and doubles the **number of lists**:

| k (lists) | Scan all heads | Min-heap |
|---|---|---|
| 16 | 24 ms | 12 ms |
| 32 | 34 ms | 13 ms |
| 64 | 66 ms | 13 ms |
| 128 | 119 ms | 14 ms |
| 256 | 241 ms | 14 ms |

The scan **doubles** every time k doubles. The heap is **flat** — going from 16 lists to 256 barely moves it, because `log 256` is only twice `log 16`.

## Common Mistakes

- **Collecting everything and sorting.** Correct, but it discards the sortedness you were handed and costs `N log N` instead of `N log k`.
- **Pushing `(value, node)` without a tiebreaker.** `TypeError` on the first duplicate value.
- **Pushing before popping.** The heap grows past `k` and you lose the space guarantee.
- **Forgetting `tail.next = None`.** Stale suffix, or an infinite cycle.
- **Not handling `k = 0` or lists that are empty.** Guard with `if node is not None` when seeding, and let `while heap:` handle the rest — no special cases needed.
- **Copying values into new nodes instead of relinking.** Wastes `O(N)` memory, and loses object identity if the nodes carry anything besides a number.
- **Mixing up N and k.** The whole complexity story is "`O(N log k)`, which beats `O(N log N)` whenever `k` is much smaller than `N`". You can't say that sentence if the two names have blurred.

## The Takeaway

> When every input is already sorted, the next answer is always at one of the fronts. The only work left is *"which front is smallest?"* — and a **min-heap** answers that repeated question in `log k` instead of `k`, by remembering what it already figured out.

This is the merge phase of merge sort, of an external sort spilling to disk, of a database merge-join, and of an LSM-tree compacting its sorted levels.
