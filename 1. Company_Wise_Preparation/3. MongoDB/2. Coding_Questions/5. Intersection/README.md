# Intersection

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Arrays, Hash Tables · **Difficulty/Frequency:** Very Common (7/10)

---

## Problem Statement

Given two integer arrays `nums1` and `nums2`, return an array of their intersection. Each element in the result must be **unique** and you may return the result in any order.

**Example 1:**

```
Input:  nums1 = [1,2,2,1], nums2 = [2,2]
Output: [2]
```

**Example 2:**

```
Input:  nums1 = [4,9,5], nums2 = [9,4,9,8,4]
Output: [9,4]
Explanation: [4,9] is also accepted.
```

**Constraints:**

- `1 <= nums1.length, nums2.length <= 1000`
- `0 <= nums1[i], nums2[i] <= 1000`

---

## Study Tools

### Hint 1

You need to know which values appear in both arrays, and duplicates in the result are collapsed away. Think about which container gives you O(1) membership checks and automatic deduplication.

### Hint 2

Load the smaller array into a hash set first. Then scan the larger array once and collect values that hit the set into a second set, so each matched value is recorded exactly once.

### Hint 3

Convert the second set into a list and return it. The entire scan is O(n + m) expected time because every hash operation is average O(1).

---

### Answer

This is a set intersection problem. The clean approach is to dump one array into a hash set, then iterate the other array and collect any value that's already in the set. Using a second set for the result handles the uniqueness requirement for free.

```python
def intersection(nums1: list[int], nums2: list[int]) -> list[int]:
    set1 = set(nums1)
    result = set()
    for val in nums2:
        if val in set1:
            result.add(val)
    return list(result)
```

**Time:** O(n + m) — building `set1` from `nums1` is O(n) expected, scanning `nums2` is O(m), and each hash lookup/add is average O(1).

**Space:** O(n + min(n, m)) — `set1` holds up to n elements, and `result` holds at most `min(n, m)` elements (every matched value must exist in both arrays).

**Correctness** is straightforward: any value that ends up in `result` must have been in `set1` (so it's in `nums1`) and was encountered while scanning `nums2`, so it's in both arrays. Conversely, if a value is in both arrays, it's in `set1` and will be encountered during the `nums2` scan, so it gets added to `result`. Since `result` is a set, no duplicates appear in the output.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force everyone reaches for: for each element in `nums1`, scan all of `nums2` to see if it appears. That's O(n × m) time, which is fine for tiny arrays but falls apart fast — at the constraint limit of 1000 elements each, you're doing up to a million comparisons, and in a real interview they'll push for better.

The bottleneck is the repeated linear scan of `nums2`. The fix: preprocess one array so membership checks become cheap. Turn `nums1` into a hash set in O(n) time. Now, instead of scanning `nums2` for every element of `nums1`, you iterate `nums2` once and ask "is this value in the set?" — each check is average O(1). Total work drops to O(n + m).

You still need to handle uniqueness. If you just collect matches into a list, `[2, 2]` in both arrays would give you `[2, 2]` instead of `[2]`. The natural fix is to collect into a second hash set, which deduplicates for you. At the end, convert it to a list and return.

One optimization worth mentioning: if one array is significantly smaller, build the set from the smaller one and iterate the larger one. The time complexity stays O(n + m) either way, but it can reduce the constant factor and the size of the first set.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Name the approach before writing code** — saying "hash set for O(1) membership, second set for dedup" lets the interviewer follow your reasoning and course-correct if needed before you commit to syntax.
- **Handle uniqueness explicitly** — the result must contain each element once, and a set is the cleanest way to guarantee that. If you collect into a list and dedup afterward, you're doing extra work.
- **State expected vs. worst-case complexity** — hash operations are average O(1) but worst-case O(n) with collisions. Mentioning this shows you understand the data structure's behavior under adversarial inputs.
- **Consider the smaller-array optimization** — building the set from the smaller array and iterating the larger one reduces memory usage and can speed things up in practice, even though asymptotic complexity is unchanged.
- **Explain correctness in terms of the set invariant** — every value in `result` is provably in both arrays, and every value in both arrays provably lands in `result`. That two-way argument is what the interviewer is listening for.
- **Know the follow-up territory** — if the arrays are sorted, two pointers give O(n + m) time and O(1) extra space. If duplicates in the result must match the minimum count across both arrays, you need a hash map with counts instead of a set.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if both arrays are already sorted?** — Two-pointer approach gives O(n + m) time and O(1) extra space.
- **What if the result should include duplicates, matching the minimum occurrence count across both arrays?** — Use a hash map counting frequencies, then build the result from the smaller count.
- **What if one array is much larger than the other and you can't fit both in memory?** — Sort the smaller array, then binary search each element of the larger one, or use an external sort and merge.
- **What if the arrays are so large that even the set doesn't fit in memory?** — Talk about disk-based approaches: sort both, then a streaming merge intersection.
- **What if instead of exact matches you need values within some numeric distance?** — Sort one array and use binary search for the nearest value, or use a balanced BST for range queries.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.
