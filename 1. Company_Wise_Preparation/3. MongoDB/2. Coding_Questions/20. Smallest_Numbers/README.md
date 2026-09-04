# Smallest Numbers

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Arrays, Binary Search · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Given a sorted array and an integer, find all the smallest numbers `>=` the integer and return their indices.

---

## Study Tools

### Hint 1

The array is sorted, so you don't need to scan from the start. Think about which index you can find in O(log n) time that immediately gives you the answer.

### Hint 2

Use binary search to find the **first** index `i` where `arr[i] >= target`. Once you have that index, the answer is just the slice `arr[i:]`.

### Hint 3

Implement a **lower-bound** binary search. If `arr[mid] < target`, search right; otherwise, search left. The `left` pointer at the end is your starting index.

---

### Answer

This is a binary search for the **lower bound** — the first index where the value is at least the target. Since the array is sorted, every element from that index onward satisfies the condition, so you return the slice starting there.

```python
def smallest_numbers(arr, target):
    left, right = 0, len(arr)
    while left < right:
        mid = (left + right) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return list(range(left, len(arr)))
```

**Time:** O(log n + k) — O(log n) for binary search plus O(k) to build the index list, where k is the number of returned indices. **Space:** O(k) — the output list of indices.

**Correctness:** The invariant is that `arr[left-1] < target` (or `left == 0`) and `arr[right] >= target` (or `right == len(arr)`). When the loop exits, `left == right`, which is exactly the first index where `arr[left] >= target`. Since the array is sorted, all elements from `left` to the end satisfy the condition.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force: scan the array from the beginning, and collect indices where `arr[i] >= target`. That's O(n) time, which works but misses the point of having a sorted array.

The sorted order is the key. You don't need to check every element — you just need to find the **boundary** between elements smaller than target and elements at least target. Once you know that boundary index, everything from there to the end is your answer.

So the problem reduces to finding the first index `i` such that `arr[i] >= target`. That's a classic lower-bound binary search. Initialize `left = 0` and `right = len(arr)`. At each step, look at `mid = (left + right) // 2`. If `arr[mid] < target`, the boundary must be to the right, so set `left = mid + 1`. Otherwise, `arr[mid] >= target`, so the boundary is at `mid` or to the left — set `right = mid`. When `left == right`, that's your answer.

One edge case: if all elements are smaller than target, the loop exits with `left == len(arr)`, and you return an empty list, which is correct.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Naming the lower bound explicitly** — saying "this is a lower-bound binary search" shows you recognize the pattern and have a precise vocabulary for it, which lets you reason about edge cases cleanly.
- **Handling the all-smaller case** — when every element is below target, your binary search should return `len(arr)`, producing an empty result. Walking through this edge case before coding shows you've thought about termination.
- **Using `right = len(arr)` instead of `len(arr) - 1`** — this off-by-one choice is what makes the all-smaller case fall out naturally without a special-case check.
- **Stating the complexity as O(log n + k)** — the output size k matters here. If you just say O(log n), you're ignoring the cost of building the index list, and the interviewer may probe that.
- **Mentioning `bisect_left` if Python's stdlib is allowed** — saying you could use `bisect.bisect_left(arr, target)` shows practical fluency, then implement it manually to demonstrate the mechanics.
- **Defining the invariant before coding** — stating "`arr[left-1] < target` and `arr[right] >= target`" up front makes your correctness argument a formality rather than a hand-wave.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Return the actual values instead of indices** — how does the code change, and does complexity stay the same?
- **What if the array contains duplicates of target?** Does your binary search return the first, last, or some middle occurrence?
- **Implement the upper bound:** the first index where `arr[i] > target` — how does the comparison flip?
- **The array is sorted but you need to support k queries against the same array** — can you precompute anything to answer each query faster than O(log n)?
- **What if the array is sorted but rotated at an unknown pivot?** How do you adapt the binary search?

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ The problem statement is ambiguous — ask before coding

> *"find all **the smallest numbers** >= the integer"*

That phrase supports two genuinely different readings, and they give different answers:

| Reading | `arr = [1, 3, 3, 5, 7]`, `target = 2` | Returns |
|---|---|---|
| **A — the whole suffix**: every number `>= target` | indices 1, 2, 3, 4 (values 3, 3, 5, 7) | O(n) results |
| **B — the smallest such value, and all its duplicates** | indices 1, 2 (both value 3) | usually a handful |

The official answer implements **A**. But "the *smallest* numbers" (plural) reads much more naturally as **B** — *the smallest qualifying value, and every index holding it*. Under reading A the word "smallest" does no work at all, which is a strong hint it was meant to.

Reading B is also the more interesting problem: it needs **two** binary searches (`bisect_left` for where the value starts, `bisect_right` for where it ends), and it returns O(k) results where k is the duplicate count rather than the whole tail.

**In an interview, ask.** The notebook implements both, names them explicitly, and tests them side by side — because the cost of guessing wrong here is solving a different problem from the one asked.
