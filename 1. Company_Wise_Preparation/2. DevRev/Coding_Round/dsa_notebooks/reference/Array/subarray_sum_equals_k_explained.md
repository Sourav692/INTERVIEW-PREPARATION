# Subarray Sum Equals K — Explained Simply

## The Problem

You're given an array of numbers and a target number `k`. You need to find **how many contiguous subarrays** (chunks of the array that sit next to each other, in order) add up exactly to `k`.

Example:

```
nums = [1, 2, 3]
k = 3
```

Subarrays that sum to 3:
- `[1, 2]` → 1 + 2 = 3 ✅
- `[3]` → 3 = 3 ✅

Answer: **2**

## Why the Obvious Way Is Slow

The obvious way: try every possible subarray, add it up, check if it equals `k`.

```
for every starting point i:
    for every ending point j (>= i):
        sum the numbers from i to j
        if sum == k: count += 1
```

For an array of size `n`, this checks roughly `n²` subarrays, and summing each one takes more time too. For a large array (say 100,000 numbers), this is far too slow.

## The Simple Trick: Running Total + "Have I Seen This Before?"

Think of walking through the array left to right, keeping a **running total** (a "prefix sum") of everything you've added so far.

Here's the key insight:

> If the running total right now is `X`, and at some earlier point the running total was `X - k`, then the numbers **in between** those two points must add up to exactly `k`.

Why? Because:
```
(sum up to now) - (sum up to that earlier point) = sum of the numbers in between
X - (X - k) = k
```

So instead of re-summing subarrays over and over, we just keep a **dictionary (hash map)** that remembers: *"I've seen running total X this many times before."*

At each step, we ask: *"Have I seen a running total of `(current total - k)` before?"* If yes, that many subarrays ending here sum to `k`. We add that count to our answer.

## Step-by-Step Example

```
nums = [1, 2, 3]
k = 3
```

We keep:
- `running_sum` = the total so far
- `seen` = a dictionary mapping {running_sum → how many times we've seen it}
- We start `seen = {0: 1}` — meaning "a running sum of 0 has occurred once" (this represents "before we started anything", which lets subarrays starting from index 0 be counted correctly)

| Step | Number | running_sum | Looking for (running_sum - k) | Found in seen? | count added | seen (updated) |
|------|--------|-------------|-------------------------------|-----------------|-------------|-----------------|
| 1 | 1 | 1 | 1 - 3 = -2 | No | 0 | {0:1, 1:1} |
| 2 | 2 | 3 | 3 - 3 = 0 | Yes (seen 1 time) | +1 | {0:1, 1:1, 3:1} |
| 3 | 3 | 6 | 6 - 3 = 3 | Yes (seen 1 time) | +1 | {0:1, 1:1, 3:1, 6:1} |

Total count = **2** ✅ (matches `[1,2]` and `[3]` from before)

## Plain-English Walkthrough

1. Walk through the array once, keeping a running total.
2. At every point, ask: "If I subtract `k` from my running total, have I seen that exact total before?"
3. If yes, that means there's some earlier point in the array where, if you take everything *after* that point up to now, it sums to `k`. Every time you've seen that earlier total, that's one more valid subarray.
4. Record how many times each running total has occurred, so future steps can look it up instantly.

This way, you only walk through the array **once** (checking a hash map is essentially instant), instead of checking every possible pair of start/end points.

## Simple Python Code

```python
def subarray_sum(nums, k):
    count = 0
    running_sum = 0
    seen = {0: 1}  # running_sum : how many times it occurred

    for num in nums:
        running_sum += num
        # Have we seen a running_sum that, if removed, leaves exactly k?
        if (running_sum - k) in seen:
            count += seen[running_sum - k]
        # record this running_sum as seen
        seen[running_sum] = seen.get(running_sum, 0) + 1

    return count

print(subarray_sum([1, 2, 3], 3))  # 2
```

## Why `seen = {0: 1}` at the Start?

Say `nums = [3]` and `k = 3`.

- running_sum after first number = 3
- We look for `3 - 3 = 0` in `seen`
- If we hadn't pre-loaded `{0: 1}`, we'd miss this — but `[3]` by itself IS a valid subarray summing to 3!

So `{0: 1}` handles the case where a subarray **starting from the very beginning** of the array sums to `k`.

## Complexity

- **Time:** O(n) — one pass through the array, hash map lookups are O(1) on average.
- **Space:** O(n) — in the worst case, we store a running sum for every prefix.

## The Reusable Pattern

This is the **"prefix sum + hash map"** pattern. Use it whenever you need to answer questions like:
- "How many subarrays sum to X?"
- "Does a subarray summing to X exist?"
- "What's the longest subarray summing to X?"

The core idea is always the same: keep a running total, and use a hash map to instantly check "have I seen the total I need before?" instead of re-scanning the array.
