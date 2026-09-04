# Iterators

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Heaps, Two Pointers · **Difficulty/Frequency:** Popular! (10/10)

---

## Problem Statement

Given two iterators with strict sorted order, implement `hasNext()` and `next()` with **constant space**.

### Follow-up (as posed with the problem)

How to handle `n` iterators?

---

## Study Tools

### Hint 1

The key is that you don't need to merge both iterators into a single sorted sequence upfront. You only need to track the current head of each iterator and decide which one to consume next.

### Hint 2

Keep two variables holding the current value from each iterator. When one runs out, mark it as exhausted so you can drain the other without further comparisons.

### Hint 3

On each `next()`, compare the two current heads, return the smaller one, and advance only that iterator. For `n` iterators, replace the two variables with a min-heap of `(value, iterator_index)` pairs.

---

### Answer

This is a k-way merge problem where k = 2, and it generalizes via a priority queue.

The core observation: both iterators yield values in strictly increasing order, so at any moment the next smallest value in the union must be one of the two current heads. You don't need to materialize the merged sequence, just track the head of each iterator and pick the smaller one on each `next()` call.

```python
class MergedIterator:
    def __init__(self, it1, it2):
        self.it1 = it1
        self.it2 = it2
        self.v1 = None
        self.v2 = None
        self.has1 = True
        self.has2 = True
        self._advance1()
        self._advance2()

    def _advance1(self):
        try:
            self.v1 = next(self.it1)
        except StopIteration:
            self.has1 = False
            self.v1 = None

    def _advance2(self):
        try:
            self.v2 = next(self.it2)
        except StopIteration:
            self.has2 = False
            self.v2 = None

    def hasNext(self):
        return self.has1 or self.has2

    def next(self):
        if not self.has1 and not self.has2:
            raise StopIteration

        if self.has1 and self.has2:
            if self.v1 <= self.v2:
                result = self.v1
                self._advance1()
            else:
                result = self.v2
                self._advance2()
        elif self.has1:
            result = self.v1
            self._advance1()
        else:
            result = self.v2
            self._advance2()

        return result
```

**Time:** O(1) per `next()` and `hasNext()` — each call does constant work: one comparison and one iterator advancement.

**Space:** O(1) — we store exactly two current values and two boolean flags, regardless of the total number of elements.

**Correctness:** At any point, `v1` and `v2` are the smallest unreturned values from their respective iterators. Since both iterators are sorted, the global minimum among all unreturned values must be one of these two. By returning the smaller and advancing only that iterator, we maintain the invariant that the merged output is sorted and that no value is skipped or duplicated.

#### Follow-up: `n` iterators

The same logic generalizes with a min-heap. Push the first element of each iterator into the heap along with its iterator index. On `next()`, pop the smallest `(value, idx)`, return the value, and push the next element from iterator `idx` if it exists. This gives O(log n) per `next()` and O(n) space for the heap.

```python
import heapq


class MergedIterators:
    def __init__(self, iterators):
        self.iterators = iterators
        self.heap = []
        for i, it in enumerate(iterators):
            try:
                val = next(it)
                heapq.heappush(self.heap, (val, i))
            except StopIteration:
                pass

    def hasNext(self):
        return len(self.heap) > 0

    def next(self):
        if not self.heap:
            raise StopIteration
        val, idx = heapq.heappop(self.heap)
        try:
            next_val = next(self.iterators[idx])
            heapq.heappush(self.heap, (next_val, idx))
        except StopIteration:
            pass
        return val
```

**Time:** O(log n) per `next()` — heap operations dominate.

**Space:** O(n) — the heap holds at most one element per iterator.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive approach: collect all elements from both iterators into a list, sort it, and iterate over that. That's O(m + n) space and O((m+n) log(m+n)) time for the sort, which violates the constant-space requirement.

The bottleneck is the sort. But you don't actually need to sort — both inputs are already sorted. The merged output is just the result of repeatedly taking the smaller of the two current heads. So the question becomes: how do you track the current head of each iterator without consuming ahead?

Python iterators are lazy, so you can't peek without advancing. The trick is to advance each iterator by one in the constructor and store the value. That's your "current head." When you return a value from `next()`, you advance only that iterator to get its new head. The other iterator's head stays put.

Now there's a subtle detail: what happens when one iterator runs out? You need a way to signal that. A boolean flag per iterator works cleanly. When both flags are false, `hasNext()` returns false. In `next()`, if only one iterator is alive, you drain it directly — no comparison needed.

For the n-iterator follow-up, the two-variable approach doesn't scale. You'd have to compare n heads on every `next()`, giving O(n) per call. A min-heap fixes that: it always keeps the smallest head at the top, and when you pop it, you push the next element from that same iterator. The heap never holds more than n elements, so space stays bounded by the number of iterators, not the total element count.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State the invariant explicitly** — the two stored values are always the smallest unreturned elements from their respective iterators. This makes the correctness argument trivial and shows you understand why the approach works.
- **Handle the exhausted-iterator case cleanly** — using boolean flags and draining the remaining iterator without comparisons keeps the logic simple and avoids off-by-one errors when one input is much shorter than the other.
- **Mention the lazy nature of Python iterators** — you can't peek without advancing, which is why the constructor eagerly pulls one element from each. Acknowledging this constraint demonstrates you understand the underlying abstraction.
- **Generalize to n iterators without being asked** — the heap-based solution is the natural extension, and bringing it up shows you see the pattern behind the problem. The complexity shift from O(1) to O(log n) per operation is the key insight.
- **Discuss the tradeoff between eager and lazy merging** — your solution is fully lazy: it does no work until `next()` is called, and each call does constant work. This matters if the iterators are infinite or very large.
- **Consider duplicate values** — since the iterators are strictly sorted, duplicates within one iterator are impossible, but duplicates across iterators are possible. Using `<=` in the comparison ensures stable behavior when both heads have the same value.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the iterators are sorted but not strictly (duplicates allowed within a single iterator)?** — The logic still works; the `<=` comparison already handles ties.
- **How would you handle k iterators where k is very large?** — The heap approach gives O(log k) per operation; consider whether k or the total element count dominates.
- **What if one iterator is infinite?** — Your solution still works lazily, but `hasNext()` will always return true and the finite iterator will eventually be exhausted.
- **Can you implement this as a generator function instead of a class?** — Yes, using `yield` and the same two-variable logic, but the class approach gives you explicit `hasNext()` control.
- **What if the iterators yield objects with a custom comparison key?** — Pass a key function to the constructor and use it in comparisons, or use `heapq` with `(key(value), value, idx)` tuples to handle ties.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.
