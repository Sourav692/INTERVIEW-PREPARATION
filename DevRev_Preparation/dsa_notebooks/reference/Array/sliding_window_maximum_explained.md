# Sliding Window Maximum — Explained Simply

## The Problem

You have an array of numbers and a window size `k`. Slide a window of size `k` across the array, one step at a time, and report the **maximum value inside the window** at every position.

Example:

```
nums = [1, 3, -1, -3, 5, 3, 6, 7]
k = 3
```

```
[1  3 -1]-3  5  3  6  7   -> max = 3
 1 [3 -1 -3] 5  3  6  7   -> max = 3
 1  3[-1 -3  5]3  6  7    -> max = 5
 1  3 -1[-3  5  3]6  7    -> max = 5
 1  3 -1 -3 [5  3  6]7    -> max = 6
 1  3 -1 -3  5 [3  6  7]  -> max = 7
```

Answer: `[3, 3, 5, 5, 6, 7]`

## Why the Obvious Way Is Slow

The obvious way: for every window position, look at all `k` numbers inside it and find the max.

```
for every window start:
    scan the k numbers in that window
    record the max
```

For `n` numbers and window size `k`, this is `O(n * k)`. If `k` is large (close to `n/2`), this becomes roughly `O(n²)` — too slow for big arrays.

## The Simple Trick: Only Keep Numbers That *Could Still* Be the Max

Think about it this way: if you see a `5` and there's a `3` sitting earlier in the window, the `3` is **useless from now on**. Why? Because the `5` is bigger AND it will stay in the window at least as long as the `3` does. The `3` can never become the answer again — throw it away.

So we keep a special list (a **deque** — a list you can add/remove from both ends quickly) of "candidates that could still be the max," always sorted from **biggest to smallest**.

Rules:
1. **Before adding a new number**, kick out any smaller numbers from the back of the list — they're dominated by the new number and can never win again.
2. **Add the new number** to the back.
3. **Check the front** — if the front number has fallen out of the current window (too old), remove it.
4. **The front of the list is always the current window's maximum.**

## An Analogy First: The Elimination Line

Imagine people walking into a room one at a time, each holding a number. They line up **left to right**. But there's a rule bouncer at the door:

> "If the person walking in is bigger than the person(s) already at the **back** of the line, those smaller people get kicked out immediately — they're never going to matter again, because you (the bigger, newer person) will outlast them."

So the line always ends up sorted **biggest to smallest**, front to back. The person at the **very front** of the line is always the biggest person currently in the room.

That's the entire trick. Now let's walk through it one number at a time, super slowly.

## Step-by-Step Example (Narrated)

```
nums = [1, 3, -1, -3, 5, 3, 6, 7],  k = 3
```

We keep a **line of candidates** (just think of it as a list of numbers, biggest at the front). At each step we say out loud what happens.

---

**Step 1 — see `1` (position 0)**
Line is empty, so `1` just joins.
Line: `[1]`
(Window not full yet — we need 3 numbers before we can report a max.)

---

**Step 2 — see `3` (position 1)**
Look at the back of the line: it's `1`. Is `1` smaller than `3`? Yes → kick `1` out, it can never win again.
Line is now empty, so `3` joins.
Line: `[3]`
(Still not full — only 2 numbers seen so far.)

---

**Step 3 — see `-1` (position 2)**
Look at the back of the line: it's `3`. Is `3` smaller than `-1`? No (3 is bigger) → don't kick anyone out.
`-1` just joins at the back.
Line: `[3, -1]`
We've now seen 3 numbers (window is full!) → **report the front of the line as the max: `3`** ✅

---

**Step 4 — see `-3` (position 3)**
Back of the line is `-1`. Is `-1` smaller than `-3`? No → don't kick anyone out.
`-3` joins at the back.
Line: `[3, -1, -3]`
Check the front: is `3` (the front) still inside our window of the last 3 numbers (positions 1,2,3)? Yes, position 1 is still in range.
**Report the max: `3`** ✅

---

**Step 5 — see `5` (position 4)**
Back of the line is `-3`. Is `-3` smaller than `5`? Yes → kick it out.
New back is `-1`. Is `-1` smaller than `5`? Yes → kick it out too.
New back is `3`. Is `3` smaller than `5`? Yes → kick it out too.
Line is now empty, so `5` joins.
Line: `[5]`
**Report the max: `5`** ✅ (everyone weaker got wiped out — `5` dominates the whole window)

---

**Step 6 — see `3` (position 5)**
Back of the line is `5`. Is `5` smaller than `3`? No → don't kick anyone out.
`3` joins at the back.
Line: `[5, 3]`
Check the front (`5`, from position 4) — still inside the window of the last 3 positions (3,4,5)? Yes.
**Report the max: `5`** ✅

---

**Step 7 — see `6` (position 6)**
Back of the line is `3`. Is `3` smaller than `6`? Yes → kick it out.
New back is `5`. Is `5` smaller than `6`? Yes → kick it out too.
Line is now empty, so `6` joins.
Line: `[6]`
**Report the max: `6`** ✅

---

**Step 8 — see `7` (position 7)**
Back of the line is `6`. Is `6` smaller than `7`? Yes → kick it out.
Line is now empty, so `7` joins.
Line: `[7]`
**Report the max: `7`** ✅

---

Final answer, collecting every "report" line above: `[3, 3, 5, 5, 6, 7]` ✅ — matches what we expected!

### The one detail the analogy hides: "too old, not too small"

Sometimes a number gets removed from the **front** of the line not because it lost to anyone, but because it's simply **too far back in the array now** — it fell outside the window. For example, if the current biggest number entered 5 steps ago and our window is only size 3, it no longer counts even though nothing ever "beat" it. That's why in the code below we also check the position (index) of the front, not just its value.

## Plain-English Walkthrough

1. Walk through the array once.
2. Before adding a new number to your "candidates" list, throw away any candidates at the back that are smaller — they've been beaten and can never be the max again.
3. Add the new number.
4. If the candidate at the front is now outside the window (too far back), remove it.
5. Once you've seen at least `k` numbers, the front of your candidates list is the max for the current window.

Each number is added and removed from the list **at most once**, so the whole thing takes only `O(n)` time — one pass.

## Simple Python Code

```python
from collections import deque

def max_sliding_window(nums, k):
    dq = deque()   # stores INDICES, values strictly decreasing front -> back
    result = []

    for i, num in enumerate(nums):
        # Remove smaller values from the back — they can't win anymore
        while dq and nums[dq[-1]] <= num:
            dq.pop()
        dq.append(i)

        # Remove the front if it has slid out of the window
        if dq[0] <= i - k:
            dq.popleft()

        # Once the window is full, record the max (front of dq)
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result

print(max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3))  # [3, 3, 5, 5, 6, 7]
```

## Why Store Indices, Not Values?

We need to know **when** a candidate falls out of the window. If we only stored values, we couldn't tell whether that `5` came from 10 steps ago (too old) or 1 step ago (still valid). Storing the index lets us check `dq[0] <= i - k` to know if it's expired.

## Complexity

- **Time:** O(n) — even though there's a `while` loop inside the `for` loop, each element is pushed and popped **at most once** across the whole run, so total work is linear.
- **Space:** O(k) — the deque holds at most `k` candidates at a time.

## The Reusable Pattern

This is the **"monotonic deque"** pattern — used any time you need a **rolling max or min** over a sliding window efficiently:
- Sliding Window Maximum / Minimum
- Rolling peak load or latency on a live dashboard
- Largest Rectangle in Histogram
- Daily Temperatures (a related "monotonic stack" idea)

Core idea: keep only the candidates that could still win, in sorted order, and evict anyone who's been beaten or aged out.
