# Integers Window

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Arrays, Sliding Window · **Difficulty/Frequency:** Rare (2/10)

---

## Problem Statement

Write a class where the constructor takes an array of integers of length N. Also, there is a function in this class called `next`. Given `n <= N`, whenever `next` is called, it will return the **sum of all integers in a window of length `n`**, and the window moves right by one position.

For example, `arr = [1, 2, 3, 4, 5]`, `n = 2`. `next` is called the first time, return `1 + 2 = 3` (the window is `1, 2`). `next` is called again, return `2 + 3 = 5` (the window moved right by one position).

**Followup 1:** What about if it's not the sum but the **product**?

**Followup 2:** What about returning the **average**?

---

## Study Tools

### Hint 1

You don't need to recompute the sum from scratch on every `next` call. Think about how the window changes between two consecutive `next` calls.

### Hint 2

Keep a **running sum**. When the window slides right by one, one element **leaves** the window and one element **enters** it.

### Hint 3

Store the previous window sum as an instance variable. On each `next` call, subtract the element that just left and add the new element that just entered, then advance the window indices.

---

### Answer

This is a sliding window problem. The key idea is to maintain the sum of the current window as state, updating it in O(1) per `next` call instead of recomputing from scratch, which would be O(n) per call.

#### Approach

Keep three pieces of state:

- `arr`: the input array
- `n`: the window length
- `start`: the index of the leftmost element in the current window (initialized to 0)
- `current_sum`: the sum of elements in the current window (initialized to `sum(arr[0:n])`)

On each call to `next`:

1. Return `current_sum`
2. Slide the window right by one: subtract `arr[start]`, add `arr[start + n]`, increment `start`

Edge cases: when `start + n == len(arr)`, the window has reached the end. You can either stop sliding or handle it based on the problem constraints (typically, you assume `next` is called at most `N - n + 1` times).

```python
class IntegersWindow:
    def __init__(self, arr, n):
        self.arr = arr
        self.n = n
        self.start = 0
        self.current_sum = sum(arr[0:n])

    def next(self):
        result = self.current_sum
        # Slide the window right by one, if possible
        if self.start + self.n < len(self.arr):
            self.current_sum -= self.arr[self.start]
            self.current_sum += self.arr[self.start + self.n]
            self.start += 1
        return result
```

**Time:** O(1) per `next` call, O(n) for the initial sum in the constructor — each call does constant work: one subtraction, one addition, one index increment. **Space:** O(1) extra space — only a few scalar variables regardless of N.

#### Correctness

**Invariant:** before each call to `next`, `current_sum` equals the sum of `arr[start : start + n]`. Initially this holds by construction. Each call returns `current_sum`, then updates `start` to `start + 1` and adjusts `current_sum` by removing `arr[old_start]` and adding `arr[old_start + n]`, which is exactly the new window. By induction, the invariant holds after every call.

#### Followups

**Product:** Replace `current_sum` with `current_product`. To slide, divide by the element leaving and multiply by the element entering. **Caveat:** if the leaving element is 0, division breaks — you'd need to handle zeros specially, e.g., by tracking the count of zeros in the window or recomputing when a zero leaves. Time per call remains O(1) (amortized if you recompute on zero).

**Average:** Return `current_sum / n` instead of `current_sum`. Still O(1) per call.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

The naive approach: on every `next` call, loop over the current window of length `n` and sum it up. That's O(n) per call, and if `next` is called O(N) times, total is O(N × n). The bottleneck is the repeated recomputation.

Think about what changes between two consecutive calls. The window moves right by one position. **Only two elements differ**: the leftmost element of the old window drops out, and the element immediately to the right of the old window enters. So instead of summing all `n` elements every time, keep the previous sum and just adjust it.

This is the classic sliding window pattern. The constructor computes the first window sum in O(n), and every subsequent call is O(1). The tradeoff is that you're storing a small amount of state (the current sum and the window start index) in the class. That's a good tradeoff here because `next` is called repeatedly.

If the interviewer asks about product, the same pattern applies with multiplication and division, but you need to flag the zero-division issue. If they ask about average, you just divide the running sum by `n` before returning — the sliding mechanism itself doesn't change.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State the complexity contrast up front** — saying "naive is O(n) per call, sliding window is O(1) per call" immediately signals you understand the tradeoff.
- **Maintain the invariant explicitly** — before writing code, say "I'll keep `current_sum` equal to the sum of `arr[start : start + n]` at all times." This makes your correctness argument trivial.
- **Handle the end-of-array boundary** — the window can only slide `N - n + 1` times total. Decide what `next` does when it can't slide anymore (return the last sum again, raise an error, or assume it won't be called that many times) and state your choice.
- **For the product followup, call out the zero case immediately** — dividing by zero when a 0 leaves the window is a real bug. Mention tracking zero counts or recomputing the product from scratch when a zero leaves, and note the amortized complexity.
- **For the average followup, consider integer vs. float division** — in Python 3, `/` gives a float, which is usually what you want for an average, but if the interviewer expects a truncated integer, use `//` and say why.
- **Think about overflow in languages like Java or C++** — a running sum of large integers can overflow. Mention using `long` or arbitrary-precision integers if the values can grow large.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the array is a stream and you don't have random access to earlier elements?** — You'd need a queue (deque) to hold the current window, pushing new elements and popping old ones.
- **What if `n` can change between `next` calls?** — You'd need to rebuild the window sum when `n` changes, or maintain a more flexible data structure like a prefix sum array.
- **What if you need to support both sum and product queries on the same window?** — Maintain both running aggregates and update them together on each slide.
- **What if the window length is fixed but the array is huge and you only have O(n) memory?** — Sliding window still works; you only ever need the current window in memory if the array is a stream.
- **Can you do this with a circular buffer to avoid shifting elements?** — Yes, a circular buffer gives O(1) push and pop at both ends, which maps naturally to the sliding window.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One thing left unspecified

The official `next` silently **returns the last window's sum forever** once the window reaches the end:

```python
w = IntegersWindow([1, 2, 3], n=2)
w.next()   # 3
w.next()   # 5
w.next()   # 5   <- the window cannot slide, so it repeats
w.next()   # 5   <- ...indefinitely
```

That is a defensible choice, but it is made by *omission* rather than decision — the guard `if self.start + self.n < len(self.arr)` prevents the index error and happens to leave the sum unchanged. A caller looping `while True` gets an infinite stream of a stale value with no signal that the data ran out.

The notebook makes the policy explicit and offers all three: repeat the last value, raise `StopIteration` (which also makes the class a real Python iterator, usable in a `for` loop), or return a sentinel. Naming the choice is the point.

**Floating-point note on the product follow-up:** the divide-out trick is exact for integers but **accumulates error for floats**, and the error never washes out because each result feeds the next. For float inputs, a running product should be recomputed periodically — or you should use the deque approach instead.
