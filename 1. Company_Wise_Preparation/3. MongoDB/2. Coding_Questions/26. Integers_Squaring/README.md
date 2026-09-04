# Integers Squaring

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Arrays, Two Pointers · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

Given a **sorted** list of integers, return the list with each integer squared.

- What if the original list is **immutable**? What if not?
- What to do if there are **negative integers**? For example, `[-6, 1, 2, 3, 4]` should return `[1, 4, 9, 16, 36]`.

---

## Study Tools

### Hint 1

The list is already sorted, so think about **where the largest squared values live**. You can avoid sorting the result if you exploit that property.

### Hint 2

With negatives present, the smallest original values (most negative) produce the **largest** squares. Use two pointers, one at each end of the list.

### Hint 3

Compare the absolute values at both ends, place the larger square at the **end** of the result array, and move the corresponding pointer inward.

---

### Answer

This is a two-pointer merge-from-the-ends problem. Since the input is sorted, the squares form a **valley** shape: values decrease as you move toward zero, then increase. The largest square is always at one of the two ends.

```python
from typing import List


def sorted_squares(nums: List[int]) -> List[int]:
    n = len(nums)
    result = [0] * n
    left, right = 0, n - 1

    for i in range(n - 1, -1, -1):
        if abs(nums[left]) > abs(nums[right]):
            result[i] = nums[left] ** 2
            left += 1
        else:
            result[i] = nums[right] ** 2
            right -= 1

    return result
```

**Time:** O(n) — each element is visited exactly once by one of the two pointers.

**Space:** O(n) for the output array. If the input is mutable and we're allowed to overwrite it, we could do this in-place with O(1) extra space, but that destroys the original list.

**Correctness:** The invariant is that after placing the square at index `i`, the elements remaining to be processed are exactly `nums[left..right]`, and the largest remaining square is at either `left` or `right`. Since the input is sorted, `abs(nums[left])` and `abs(nums[right])` are the two largest absolute values in the remaining range. We pick the larger one, place it at the current end of the result, and shrink the window. By induction, the result is filled from right to left in non-decreasing order.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force: square every element and sort the result. That's O(n log n) time and O(n) space. The bottleneck is the sort — we're throwing away the fact that the input is already sorted.

Think about what the squared array looks like. For a sorted input like `[-6, 1, 2, 3, 4]`, the squares are `[36, 1, 4, 9, 16]`. The values decrease from 36 down to 1, then increase to 16. So the squared array is a **valley**: it's decreasing then increasing. The maximum is at one end, the next maximum is at one of the two remaining ends, and so on.

That observation suggests a two-pointer approach. Keep `left` at index 0 and `right` at index `n-1`. The largest square among the remaining elements is either `nums[left] ** 2` or `nums[right] ** 2`. Compare their absolute values, place the larger square at the end of the result array, and advance the pointer that produced it. Repeat until the pointers cross.

This is a classic example of recognizing that the sorted structure of the input gives you more information than just "the values are in order" — it tells you exactly where the extremes of the squared values live.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Identify the valley property** — The squared values of a sorted array form a decreasing-then-increasing sequence, so the maximum is always at an end. Naming this property shows you see the structure, which is what turns an O(n log n) solution into O(n).
- **Use two pointers from the ends** — Walking inward from both ends and filling the result from the back is the clean way to exploit that property. You compare absolute values, which handles negatives without any case analysis.
- **Handle the mutable vs. immutable distinction explicitly** — If the input is immutable (like a tuple or a frozen list), you must allocate a new array. If it's mutable, you can overwrite in place, but state the tradeoff: you destroy the original data, which may or may not be acceptable.
- **State the time and space complexity precisely** — O(n) time and O(n) space for the immutable case, O(1) extra space for the in-place mutable case. Mentioning both variants shows you're thinking about real-world constraints, not just the textbook answer.
- **Walk through the example `[-6, 1, 2, 3, 4]` step by step** — Trace the pointers: compare `abs(-6)=6` vs `abs(4)=4`, place 36 at the end, move `left` to 1. Then `abs(1)=1` vs `abs(4)=4`, place 16, move `right` to 3. Continue until done. This catches off-by-one errors and demonstrates the invariant.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the input contains duplicates?** — The two-pointer approach handles them naturally; think about whether the comparison should be `>` or `>=` and what changes.
- **Can you do this in-place with O(1) extra space if the input is mutable?** — Consider swapping elements or using the fact that the squared values form a valley to rearrange without a second array.
- **What if the input is sorted but not fully sorted, e.g., a rotated sorted array?** — The valley property breaks down; think about how you'd adapt or whether you need a different approach.
- **What if the input is a linked list instead of an array?** — Two pointers still work, but you'd need to traverse from both ends, which requires either a doubly linked list or reversing one half.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One correction to the official answer

The space claim is wrong:

> *"If the input is mutable and we're allowed to overwrite it, we could do this **in-place with O(1) extra space**."*

You cannot. The two-pointer algorithm **writes to the end of the result while still reading from both ends of the input** — so writing into the input array would overwrite a value the algorithm has not consumed yet. With `[-6, 1, 2, 3, 4]`, the very first step writes 36 to index 4, destroying the `4` that the `right` pointer is about to need.

A genuine O(1)-extra-space in-place version exists, but it is a different algorithm: square everything in place (O(n)), which leaves a **valley**, then **reverse the negative prefix** and merge the two now-sorted runs in place — and an in-place merge of two runs is itself either O(n) extra space or an intricate O(n log n) rotation-based merge.

The honest answers are: **O(n) extra space** for the clean two-pointer version, or **in-place at O(n log n)** by squaring and re-sorting. The notebook implements and tests both, and asserts that the naive "write into the input" version actually produces wrong output.
