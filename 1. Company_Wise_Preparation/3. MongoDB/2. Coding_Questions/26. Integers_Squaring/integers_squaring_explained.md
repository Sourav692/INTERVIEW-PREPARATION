# Integers Squaring — Explained Simply

## The Problem

Given a **sorted** array of integers, return the squares — also sorted.

```
[-6, 1, 2, 3, 4]   →   [1, 4, 9, 16, 36]
```

The catch is right there in the example: **negative numbers**. The smallest input (`-6`) produces the **largest** square (`36`).

## Squaring Breaks the Sort — But Predictably

```
input:    -6    1    2    3    4      ← sorted
squares:  36    1    4    9   16      ← not sorted
```

You could just sort the squares. That's O(n log n), and it works.

But look at the shape of those squares: `36, 1, 4, 9, 16`. They go **down**, then **up**. That's not random — it's a **valley**:

```
36 ╲
    ╲
     1 ── 4 ── 9 ── 16
     ╱                ╲
   (bottom near zero)  (rises again)
```

Why? Because the input is sorted, its values decrease in magnitude as they approach zero, then increase again. Squaring preserves magnitude ordering exactly.

And a valley has one very useful property:

> **The largest value is always at one of the two ends. Never in the middle.**

That single fact is the whole algorithm.

## An Analogy First: Two Queues, Tallest at the Back

Two lines of people facing away from each other, back to back. In each line, people are ordered shortest (in the middle) to tallest (at the far ends).

You want everyone lined up tallest-first.

You don't need to survey the crowd. **Look at the two people at the far ends** — one of them is the tallest person present. Take them, and now look at the two *new* ends. Repeat.

The negatives are one queue (getting taller as they go more negative), the positives are the other (getting taller as they get bigger), and they meet near zero.

## Step-by-Step Example (Narrated)

`[-6, 1, 2, 3, 4]`. Two pointers at the ends, filling the result **from the back**.

```
result = [_, _, _, _, _]
left → -6                  4 ← right
```

---

**Fill position 4 (the last).** Compare magnitudes: `|-6| = 6` vs `|4| = 4`.

Left is bigger → place `36`, move `left` inward.

```
result = [_, _, _, _, 36]
       left → 1        4 ← right
```

---

**Fill position 3.** `|1| = 1` vs `|4| = 4`. Right is bigger → place `16`, move `right` inward.

```
result = [_, _, _, 16, 36]
       left → 1   3 ← right
```

---

**Fill position 2.** `1` vs `3` → place `9`, move `right`.

```
result = [_, _, 9, 16, 36]
       left → 1  2 ← right
```

---

**Fill position 1.** `1` vs `2` → place `4`, move `right`.

```
result = [_, 4, 9, 16, 36]
       left → 1 ← right     (both on the same element)
```

---

**Fill position 0.** `1` vs `1` → tie, take the right branch → place `1`.

```
result = [1, 4, 9, 16, 36]   ✅
```

Exactly `n` iterations, each advancing exactly one pointer. Every element consumed once.

## Two Details Worth Knowing

### Fill from the back, not the front

The algorithm naturally produces the **largest** value first. So write it to the last free slot and work backwards.

Filling forwards would mean producing the *smallest* first — which requires finding where the valley bottoms out (a search) and then merging outward from there. More code, no benefit.

> **Produce output in the order the algorithm can generate it.**

### Compare `abs()`, not the squares

```python
if abs(nums[left]) > abs(nums[right]):    # ✅
if nums[left]**2 > nums[right]**2:        # works, but
```

Same decision, and `abs` is cheaper. In a language with fixed-width integers it also matters: squaring a value near the type's maximum **overflows**, while comparing magnitudes never does.

## The Claim That Isn't True

The official answer says:

> *"If the input is mutable and we're allowed to overwrite it, we could do this **in-place with O(1) extra space**."*

**You can't** — not with this algorithm.

The reason is a general one worth internalising:

> **An algorithm can run in place only if its write pattern never outruns its read pattern.**

Here it does, immediately. The first step writes `36` to index 4 — **destroying the `4`** that the `right` pointer is about to need.

The notebook runs that version and shows what it actually produces:

```
[7958661109946400884391936, 2821109907456, 1679616, 1296, 36]
```

It squares already-squared values, repeatedly. Not subtly wrong — catastrophically wrong.

### What in-place actually costs

There *is* a genuine in-place route:

1. Square everything in place — O(n). This leaves a valley.
2. Sort — O(n log n).

So the honest options are:

| | Time | Extra space |
|---|---|---|
| Two pointers | **O(n)** | O(n) |
| Square then sort in place | O(n log n) | **O(1)** |

**A trade, not a free lunch.** Naming the trade is worth more than claiming both.

*(There's a third route — square, reverse the negative prefix, then merge the two sorted runs — but an in-place merge is either O(n) scratch space or an intricate rotation-based O(n log n). No escape.)*

## A Surprising Benchmark Result

The two-pointer version is O(n). Square-then-sort is O(n log n). So the first should win.

**In CPython, it doesn't:**

| n | Square then sort | Two pointers |
|---|---|---|
| 50,000 | 13.9 ms | 11.1 ms |
| 100,000 | 41.0 ms | 36.3 ms |
| 200,000 | 57.9 ms | 63.0 ms |
| 400,000 | 116.3 ms | 151.2 ms |

Why?

- `sorted()` is **C**. And Timsort additionally *detects the two existing runs* in the squared valley and merges them in O(n) comparisons.
- The two-pointer loop is **interpreted Python**, paying per-iteration overhead on every element.

So the real comparison isn't O(n) vs O(n log n) — it's **one interpreted pass vs one native pass**, and native wins by a constant that dwarfs the missing `log n`.

**This doesn't make the two-pointer answer wrong.** It's what the question is testing (did you notice the input was sorted?), it wins outright in a compiled language, and the asymptotics reassert themselves at large enough n.

But it's a genuine reminder: **asymptotic complexity predicts scaling, not speed.** A constant factor of 50 beats a `log n` of 20 every time.

## Common Mistakes

- **Sorting the squares.** Correct, but throws away the one piece of structure you were given.
- **Handling negatives with case analysis.** Comparing `abs()` handles them with no branches.
- **Filling the result forwards.** You'd need to find the valley's floor first.
- **Claiming O(1) space by writing into the input.** The write clobbers a value still needed.
- **Comparing squares instead of magnitudes.** Overflow risk in fixed-width languages.
- **Forgetting the all-negative case.** `[-3, -2, -1]` → `[1, 4, 9]`. The order **reverses**.
- **Mutating the caller's array without saying so.** If you square in place, that's a contract change.

## The Takeaway

> When a transformation breaks sortedness, ask **how** it breaks it. Squaring turns a sorted array into a **valley** — and in a valley, the extremes live at the ends. Two pointers walking inward produce the whole answer in order, in one pass.

And be precise about space claims: **"in place" is a statement about your write pattern**, not about ambition. If you'll need to read what you're about to overwrite, you can't.
