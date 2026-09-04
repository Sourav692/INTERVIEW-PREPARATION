# K-Way Merge

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Heaps, Linked List · **Difficulty/Frequency:** Very Common (7/10)

---

## Problem Statement

Basically the same as **Merge k Sorted Lists** (LeetCode 23, Hard).

You are given an array of `k` linked-lists `lists`, each linked-list is sorted in ascending order.

Merge all the linked-lists into one sorted linked-list and return it.

**Example 1:**

```
Input: lists = [[1,4,5],[1,3,4],[2,6]]
Output: [1,1,2,3,4,4,5,6]
Explanation: The linked-lists are:
[
  1->4->5,
  1->3->4,
  2->6
]
merging them into one sorted linked list:
1->1->2->3->4->4->5->6
```

**Example 2:**

```
Input: lists = []
Output: []
```

**Example 3:**

```
Input: lists = [[]]
Output: []
```

**Constraints:**

- `k == lists.length`
- `0 <= k <= 10^4`
- `0 <= lists[i].length <= 500`
- `-10^4 <= lists[i][j] <= 10^4`
- `lists[i]` is sorted in ascending order.
- The sum of `lists[i].length` will not exceed `10^4`.

---

## Study Tools

### Hint 1

You have k sorted lists, and repeatedly scanning all k heads to find the smallest would be O(k) per element. Think about which data structure gives you the minimum of a changing set in sublinear time.

### Hint 2

Put the head node of each non-empty list into a min-heap keyed by node value. When you pop the smallest node, you advance that node's list and push its successor back into the heap.

### Hint 3

Initialize a dummy head node, then repeatedly pop the min from the heap, append it to your result, and push the popped node's `next` if it exists. Keep going until the heap is empty.

---

### Answer

This is a k-way merge problem, and the standard approach is a min-heap over the current heads of all k lists. You pop the smallest node, append it to the result, then push that node's successor back into the heap. That gives O(N log k) time and O(k) space, where N is the total number of nodes.

```python
import heapq


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def mergeKLists(lists):
    heap = []
    # Push the head of each non-empty list with a tie-breaker to avoid
    # comparing ListNode objects when values are equal.
    for i, node in enumerate(lists):
        if node:
            heapq.heappush(heap, (node.val, i, node))

    dummy = ListNode()
    tail = dummy

    while heap:
        val, i, node = heapq.heappop(heap)
        tail.next = node
        tail = tail.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))

    return dummy.next
```

**Time:** O(N log k) — every node is pushed and popped exactly once, and each heap operation costs O(log k).

**Space:** O(k) — the heap holds at most one node per list at any time.

**Correctness argument:** Maintain the invariant that the heap always contains the smallest unprocessed node from each non-empty list. At each step, the heap's minimum is the smallest remaining node across all lists, because every list is sorted in ascending order and the heap contains the current head of each list. Appending it to the result preserves sorted order. The loop terminates when all lists are exhausted, at which point every node has been appended exactly once.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force you could write in two minutes: collect all nodes into an array, sort by value, and relink them. That's O(N log N) time and O(N) space. It passes the constraints but doesn't use the fact that each list is already sorted.

Since each list is sorted, the smallest remaining element is always one of the k current heads. Scanning all k heads for each of the N elements gives O(N·k) time. With k up to 10^4 and N up to 10^4, that's potentially 10^8 operations — borderline, and it misses the point.

The bottleneck is finding the minimum among k candidates repeatedly. A min-heap turns that into O(log k) per operation. You seed the heap with the head of each non-empty list. Each pop gives you the next smallest node; you then push that node's successor. The heap never grows beyond k elements.

One implementation detail: when two nodes have the same value, Python's heap will try to compare the `ListNode` objects themselves, which raises a `TypeError`. The fix is to push tuples `(val, index, node)` so the index breaks ties before the node comparison is ever attempted. In Python 3, the comparison of the third tuple element only happens if the first two are equal, so a unique index per list guarantees no `ListNode` comparison.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Name the pattern early** — saying "k-way merge with a min-heap" in the first sentence signals you've seen the problem class and lets the interviewer calibrate the rest of the discussion.
- **State the complexity as O(N log k), and explain why it's better than O(N log N)** — N can be much larger than k, and the heap's size stays bounded by k, which is the whole insight.
- **Handle the tie-breaker explicitly** — in Python, pushing `(val, node)` crashes when two nodes share a value. Mentioning the `(val, index, node)` tuple shows you've actually run this code, not just sketched it.
- **Walk through the heap invariant before coding** — say "the heap contains the smallest unprocessed node from each list" and then show how each pop-and-push step maintains it. That's the correctness proof in one sentence.
- **Edge cases: empty lists, lists containing empty lists, and all lists exhausted** — the `if node:` guard at seeding time and the `while heap:` loop handle all three without special-casing.
- **If asked about alternatives, mention divide-and-conquer merging** — repeatedly merging pairs of lists is also O(N log k) and avoids heap overhead, but the heap version is cleaner to implement iteratively.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the input were k sorted arrays instead of linked lists?** — The heap approach works unchanged; you'd just track `(val, array_index, element_index)` and advance the index.
- **Can you do this in O(1) extra space?** — Yes: repeatedly merge pairs of lists using the standard two-list merge, which reuses existing nodes and only needs a few pointers.
- **What if the lists are streamed and you can't hold all k heads in memory at once?** — You'd need external merge techniques: merge in batches, spilling intermediate results to disk.
- **How would you parallelize this?** — Partition the k lists into groups, merge each group in a worker, then merge the resulting partial results. The final merge is still a k-way merge, but with far fewer inputs.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**See also:** [`2. Iterators`](../2.%20Iterators/README.md) is the streaming form of this same k-way merge — worth studying the two together.
