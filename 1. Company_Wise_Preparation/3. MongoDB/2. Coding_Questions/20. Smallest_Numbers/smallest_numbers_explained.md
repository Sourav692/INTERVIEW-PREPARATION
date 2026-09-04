# Smallest Numbers — Explained Simply

## The Problem

You have a **sorted** array and a target number. Find the smallest numbers that are `>= target`, and return their **indices**.

```
arr = [1, 3, 5, 7, 9],  target = 4
→ the answer starts at index 2 (value 5)
```

## First — This Question Is Ambiguous, and You Should Say So

> *"find all **the smallest numbers** >= the integer"*

Read that carefully. It has **two** defensible meanings:

| Reading | `[1, 3, 3, 5, 7]`, target = 2 | Result |
|---|---|---|
| **A** — every number `>= target` | 3, 3, 5, 7 → indices `[1, 2, 3, 4]` | the whole tail |
| **B** — the *smallest* qualifying value, and all its copies | 3, 3 → indices `[1, 2]` | just that run |

The official answer implements **A**. But notice: under reading A, the word **"smallest"** does nothing at all — you'd get the same answer from "find all numbers >= the integer". That's a strong hint that **B** was intended.

**In an interview, ask.** One sentence costs you nothing; guessing wrong costs you the whole question.

*(The notebook implements both.)*

## The Core Technique: Finding a Boundary

Whichever reading, the engine is the same.

Because the array is sorted, it splits cleanly into two zones:

```
[1, 3, 5, 7, 9]     target = 4
 └──┬──┘  └──┬──┘
  < 4       >= 4
       ↑
   the boundary
```

You don't need to examine every element. You need to find **one number**: where the boundary sits. Everything from there onward qualifies.

## Ordinary Binary Search Isn't Quite Right

The binary search most people know asks *"where is x?"* — and returns "not found" when x isn't there.

That's useless here. `target = 4` isn't in `[1, 3, 5, 7, 9]` at all, but the question still has a perfectly good answer.

So you ask a **different** question, one that always has an answer:

> **"Where would `4` go, if I inserted it and kept the array sorted?"**

Equivalently: *the first index whose value is `>= 4`*. That's called the **lower bound**, and it's what `bisect_left` computes.

## An Analogy First: Finding Your Seat in a Cinema

Rows numbered in order. Your ticket says row 14, but row 14 doesn't exist in this screen — the rows jump from 12 to 16.

You don't walk from the front counting rows. You go to the middle:

- *"Row 20 — too far back."* → the answer is in front of me.
- *"Row 10 — too far forward."* → the answer is behind me.
- …and so on, halving the remaining rows each time.

You end up standing at the **first row numbered 14 or higher** — row 16. You didn't "find row 14", because there isn't one. You found **where it would be**, which is what you actually wanted.

## Step-by-Step Example (Narrated)

`arr = [1, 3, 5, 7, 9]`, `target = 4`.

Set up a search window. Note `right` starts at **5** (the length), not 4 — this matters, and I'll explain why in a moment.

```
left = 0,  right = 5     (the window is [left, right) — right is one PAST the end)
```

---

**Step 1.** `mid = (0 + 5) // 2 = 2`. `arr[2] = 5`.

Is `5 < 4`? **No** — 5 qualifies.

So the boundary is at index 2 **or somewhere to its left**. Index 2 might be the answer, so we **keep it in the window**:

```
right = 2        window is now [0, 2)
```

---

**Step 2.** `mid = (0 + 2) // 2 = 1`. `arr[1] = 3`.

Is `3 < 4`? **Yes** — 3 doesn't qualify.

So index 1 is definitively **not** the answer, and neither is anything before it. Skip **past** it:

```
left = 2         window is now [2, 2)
```

---

**Step 3.** `left == right == 2`. The window is empty. **Stop.**

**Answer: index 2.** ✅ (`arr[2] = 5`, the first value `>= 4`.)

Three steps for five elements. For a million elements it's twenty.

## Three Details That Make It Work

### 1. `right = len(arr)`, not `len(arr) - 1`

The window is **half-open**: `[left, right)` — `right` means "one past the last candidate".

Why it matters: if **nothing** in the array qualifies (`target = 99`), the loop ends with `left == len(arr)`. The slice `arr[5:]` is empty, which is exactly right.

Use `len(arr) - 1` and you need a special case for that. The half-open convention makes it disappear.

### 2. The two updates are asymmetric — deliberately

```python
if arr[mid] < target:
    left = mid + 1      # mid is ruled OUT — skip past it
else:
    right = mid         # mid might BE the answer — keep it
```

This asymmetry is the crux. When `arr[mid] < target`, `mid` definitively fails, so exclude it. When `arr[mid] >= target`, `mid` is a **candidate** — writing `right = mid - 1` here would silently throw away the correct answer.

### 3. Don't "return early" on an exact match

The classic optimisation — `if arr[mid] == target: return mid` — is **wrong** for a boundary search.

With duplicates `[1, 3, 3, 5]` and target 3, you'd return whichever 3 you happened to land on. The lower bound must return the **first** one, and it does precisely because it keeps narrowing instead of stopping.

## The Invariant — Say This Before You Write Code

> **Everything strictly left of `left` is `< target`. Everything from `right` onward is `>= target`.**

- Both are trivially true at the start (both regions are empty).
- Every step preserves them, by the asymmetric updates above.
- When `left == right`, the unknown middle is empty — so **`left` is the boundary**.

That's a complete correctness proof in three lines, and stating it up front turns "I think this works" into "here's why it works". Interviewers listen for exactly this.

## Reading B: Two Boundaries Instead of One

If the question means *"the smallest qualifying value and all its duplicates"*, you need **both** ends of a run:

```
[1, 3, 3, 5, 7],  target = 2

lower_bound(2) = 1      → the first qualifying element is arr[1] = 3
lower_bound(3) = 1      → where the 3s start
upper_bound(3) = 3      → one past where the 3s end

answer: indices 1, 2
```

Since the array is sorted, **duplicates are always contiguous** — so those two boundaries delimit exactly the run.

And here's the neat part: `upper_bound` is the *same function* with **one character changed**:

```python
if arr[mid] < target:      # lower_bound  → first index >= target
if arr[mid] <= target:     # upper_bound  → first index >  target
```

A useful consequence: `upper_bound(v) - lower_bound(v)` gives you **how many times `v` appears**, in O(log n), without ever looking at the elements between them.

## In Real Code: Just Use `bisect`

```python
import bisect
bisect.bisect_left(arr, target)      # the lower bound, in C
bisect.bisect_right(arr, target)     # the upper bound
```

Knowing that `bisect_left` **is** the lower bound is the practical half of this question.

In an interview: **write the loop** to show you understand the mechanics, then say you'd ship `bisect`. That order shows both capability and judgement.

*(One gotcha: `bisect` accepts `lo` and `hi` arguments so you can search a sub-range. Use those rather than slicing — a slice costs O(n) and quietly destroys the O(log n) you came for.)*

## Why It's Fast

2,000 queries against an array that doubles in size:

| Array size | Linear scan | Binary search | `bisect` (C) |
|---|---|---|---|
| 2,000 | 153 ms | 2.8 ms | 0.81 ms |
| 4,000 | 304 ms (2.0×) | 2.9 ms (1.1×) | 0.83 ms (1.0×) |
| 8,000 | 612 ms (2.0×) | 3.0 ms (1.0×) | 0.86 ms (1.0×) |
| 16,000 | 1,244 ms (2.0×) | 3.1 ms (1.0×) | 0.87 ms (1.0×) |

The scan **doubles** every time. Binary search is **flat** — going from 2,000 to 16,000 elements adds three extra halving steps, and that's it.

At 16,000 elements it's **402× faster**.

> **A caveat worth stating:** this benchmark uses targets near the *end* of the array, so the result set stays tiny. If the target were near the start, both would be O(n) — because producing O(n) *indices* is O(n) no matter how you found them. That's why the honest complexity is **O(log n + k)**, with the `k` there for a reason.

## The Overflow Bug That Lived in Java for Nine Years

```python
mid = (left + right) // 2
```

Fine in Python — integers are arbitrary-precision.

In C or Java with a large array, `left + right` can **overflow** to a negative number, producing a negative index. This exact bug sat in the JDK's own `binarySearch` from 1997 to 2006.

The fix:

```python
mid = left + (right - left) // 2
```

Mentioning it signals you've written binary search in a language without bignums.

## Common Mistakes

- **Using `right = len(arr) - 1`.** Now "nothing qualifies" needs a special case.
- **`right = mid - 1` in the else branch.** Discards the correct answer.
- **Returning early on `arr[mid] == target`.** Gives *an* occurrence, not the *first*.
- **Mixing conventions** (half-open window, closed-interval updates). Almost every binary-search off-by-one traces back to this.
- **Slicing to search a sub-range.** O(n), which defeats the whole purpose. Use `lo`/`hi`.
- **Not asking about the ambiguity.** Two readings, two different answers.
- **Saying O(log n) and stopping.** Building the output is O(k).

## The Takeaway

> Binary search isn't only for *"where is x?"* — it's for **"where's the boundary?"**. Whenever a yes/no test reads `False, False, …, True, True` across a sorted array, you can find that flip point in `log n` steps.

Two habits make it reliable every time: use the **half-open window** `[left, right)`, and **state the invariant before you write the loop**. Get those right and the off-by-ones stop happening.
