# Integers Window — Explained Simply

## The Problem

A class holding an array and a window length `n`. Each call to `next()` returns the **sum of the current window**, then slides the window one position right.

```python
w = IntegersWindow([1, 2, 3, 4, 5], n=2)
w.next()   # 3   ← window [1, 2]
w.next()   # 5   ← window [2, 3]
w.next()   # 7   ← window [3, 4]
w.next()   # 9   ← window [4, 5]
```

**Follow-ups:** what about the **product**? What about the **average**?

## The One Observation

Look at two consecutive windows:

```
[1, 2, 3, 4, 5]
 └──┘              window 1 = [1, 2]
    └──┘           window 2 = [2, 3]
```

They **overlap almost entirely**. Going from one to the next:

- `1` **leaves** (from the left)
- `3` **enters** (on the right)
- **`2` doesn't move.**

With a window of 100, 99 elements are unchanged. Re-adding all 100 every time is throwing away 99% of the work.

So don't recompute — **repair**:

```python
sum -= arr[start]        # the element leaving
sum += arr[start + n]    # the element entering
```

O(n) once in the constructor. **O(1) forever after.**

## An Analogy First: A Moving Train

You're weighing a 100-carriage train, one 10-carriage section at a time.

**The slow way:** weigh all 10 carriages, write it down, shuffle forward one carriage, weigh all 10 again. You weigh 10 carriages to learn about a section that differs from the last by only two.

**The fast way:** weigh the first 10 once. Then for each step forward: **subtract** the carriage that dropped off the back, **add** the one that joined the front. Two weighings instead of ten, no matter how long the section.

That's it. And note what makes it work: you can *subtract* a weight. Which brings us to the interesting part.

## Which Aggregates Can Slide?

This is the part worth understanding rather than memorising.

| Aggregate | Slides? | Why |
|---|---|---|
| **Sum** | ✅ | subtraction exactly undoes addition |
| **Average** | ✅ | it's just the sum, divided at the end |
| **Product** | ⚠️ | division undoes multiplication — **except by zero** |
| **Min / Max** | ❌ | there is no "un-minimum" |

The rule:

> **An aggregate can slide when its operation has an inverse.**

- Addition has subtraction. ✅
- Multiplication has division — *unless the departing element is 0*. ⚠️
- `min` has **nothing**. Remove the current minimum and the next-smallest is simply unknowable from the aggregate alone. ❌

That last row is why the classic "sliding window maximum" problem needs a **monotonic deque** rather than a running value. Being able to explain *why* min is different — not just knowing the deque trick — is what this problem is really testing.

## Step-by-Step Example (Narrated)

`arr = [1, 2, 3, 4, 5]`, `n = 2`.

---

**Constructor.** Sum the first window once: `1 + 2 = 3`.

```
window: [1, 2]      sum = 3      start = 0
```

*This is the only O(n) work that ever happens.*

---

**`next()` → returns 3.**

Now slide. `arr[0] = 1` leaves, `arr[0+2] = 3` enters:

```
sum = 3 - 1 + 3 = 5        start = 1
window: [2, 3]
```

---

**`next()` → returns 5.**

Slide: `arr[1] = 2` leaves, `arr[3] = 4` enters.

```
sum = 5 - 2 + 4 = 7        start = 2
window: [3, 4]
```

---

**`next()` → returns 7.** Slide: `3` out, `5` in → `9`.

**`next()` → returns 9.** The window is at the end.

---

Four windows. After the first, each cost **two arithmetic operations** instead of `n` additions.

## The Invariant

Before writing any code, say this:

> **`current_sum` always equals the sum of `arr[start : start + n]`.**

It holds at the start (the constructor computes exactly that), and each slide subtracts precisely what left and adds precisely what arrived. Correctness proof: two sentences.

Stating it first is also what stops the off-by-ones. `arr[start + n]` is the element **just past** the window's right edge — the one entering. Get that index wrong and you're adding a value that's already inside.

## The Question the Official Answer Doesn't Answer

What happens when the window reaches the end?

The official code has this guard:

```python
if self.start + self.n < len(self.arr):
    ...slide...
return result
```

It stops the index running off the end — and, as a side effect, `next()` **returns the last sum forever**:

```python
w = IntegersWindow([1, 2, 3], n=2)
w.next()   # 3
w.next()   # 5
w.next()   # 5   ← can't slide
w.next()   # 5   ← ...forever
```

That's a defensible policy. But it was made by **omission**, not decision — and a caller looping `while True` gets an endless stream of a stale value with no signal that the data ran out.

Make it a choice:

- **`"repeat"`** — the official behaviour, now deliberate.
- **`"raise"`** — `StopIteration`, which also makes the class a real Python iterator (`for s in window:` just works).
- **`"none"`** — a sentinel the caller can test.

> **Decide the boundary; don't let a guard decide it for you.**

## Follow-Up 1: The Product, and the Zero That Breaks It

Same slide, with `*` and `/`:

```python
product = product / leaving * entering
```

Works fine — until the departing element is **zero**, and you divide by it.

And you can't just skip it. Consider `[2, 0, 3, 4]` with `n = 2`:

- `[2, 0]` → product 0
- `[0, 3]` → product 0
- `[3, 4]` → product **12**

When the `0` finally leaves, you need to *recover* the real product — but you multiplied it away three windows ago.

### The fix: split the aggregate

```python
zero_count       = how many zeros are in the window
nonzero_product  = product of the NON-ZERO elements
```

The answer is `0 if zero_count else nonzero_product`.

Every slide updates whichever of the two the departing and arriving elements belong to. Still O(1), no recomputation, and **no special case at the call site** — the zero is handled structurally, not with a check everywhere it's used.

> **A floating-point caveat:** the divide-out trick is exact for integers. For floats it accumulates error, and the error **never washes out** because each result feeds the next. For float inputs, recompute periodically — or use the deque approach below, which never divides at all.

## Follow-Up 2: The Average

Return `current_sum / n`. The sliding mechanism doesn't change at all.

Worth mentioning: in Python 3, `/` gives a float, which is usually what you want for an average. If the interviewer expects a truncated integer, use `//` — and say why.

## Follow-Up 3: A Stream, With No Random Access

The running sum needs `arr[start]` — the element **leaving**. A stream can't give you that; it's already gone past.

So keep the window itself in a **deque**:

```python
self.window.append(value)
self.total += value
if len(self.window) > self.n:
    self.total -= self.window.popleft()    # the pop RETURNS the departing value
```

The `popleft()` hands back exactly what random access would have supplied. `deque` does both ends in O(1); a list would pay O(n) on `pop(0)`.

Memory is O(n) — the **window**, not the stream. That's why this pattern is how you compute a moving average over a metrics feed, or a rolling rate limit, without storing history.

## And the Min/Max Case

`max` can't slide as a running value. But a deque of **candidates** can:

- Keep indices with **decreasing** values, front to back.
- When a new element arrives, discard every candidate it's larger than — they can never be the max again while it's in the window.
- Drop the front if it has slid out of the window.
- **The front is always the window maximum.**

Amortised O(1), because each index is pushed and popped at most once.

## Why It's Fast

A full pass over an array, with the window sized proportionally:

| Array size | Re-sum each window | Running sum |
|---|---|---|
| 500 | 0.40 ms | 0.13 ms |
| 1,000 | 0.99 ms (2.5×) | 0.27 ms (2.0×) |
| 2,000 | 3.05 ms (3.1×) | 0.54 ms (2.0×) |
| 4,000 | 10.44 ms (3.4×) | 1.06 ms (2.0×) |

The naive version grows **faster than linearly** — there are O(N) windows and each costs O(n), and here `n` grows with N. The running sum is cleanly linear.

## Running Aggregate vs. Prefix Sum

Worth knowing which tool fits:

| | Best for |
|---|---|
| **Running aggregate** (this problem) | a **fixed** window, walked in order |
| **Prefix sums** ([Billing System](../22.%20Billing_System/README.md)) | **arbitrary** ranges, queried out of order |

If `n` can change between calls, the running sum has to be rebuilt — and a prefix array becomes the better structure, answering *any* range in O(1) with no state at all.

## Common Mistakes

- **Recomputing the whole window each call.** The entire point is that you don't have to.
- **Getting the entering index wrong.** It's `arr[start + n]`, the element just past the right edge.
- **Dividing by a departing zero in the product version.** Count zeros separately.
- **Letting a guard define the end-of-array behaviour.** Make the policy explicit.
- **Using a list as a queue in the streaming version.** `pop(0)` is O(n).
- **Assuming min/max slide like sum does.** They have no inverse.
- **Ignoring overflow** in Java or C++ — a running sum of large values overflows, and a running *product* does so spectacularly fast.

## The Takeaway

> Consecutive windows overlap almost completely. **Repair the aggregate instead of rebuilding it** — subtract what left, add what arrived — and O(n) per call becomes O(1).

And the transferable insight: an aggregate can be maintained incrementally exactly when its operation has an **inverse**. Sum has subtraction; product has division except by zero; min and max have nothing at all. That test tells you instantly whether a running value will work, or whether you need something cleverer.
