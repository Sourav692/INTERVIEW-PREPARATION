# 128. Longest Consecutive Sequence — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/longest_consecutive_sequence.ipynb`
> **LeetCode:** https://leetcode.com/problems/longest-consecutive-sequence/
> **Generated for:** personal study reference

---

## Overview

> **Note on placement:** this problem lives in the `Graph` folder, but the notebook implements it purely as an array / hash-set problem — there is no explicit graph traversal here. The "graph" framing is implicit: consecutive integers form chains (`x → x+1 → x+2 → ...`), and a hash set lets you walk each chain in O(1) steps per hop, the same way you'd walk edges in an unweighted graph. The reference below stays faithful to the actual code.

| Topic               | Key idea                                                                                                                               |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Hash set membership | `set` gives O(1) average "is `x` present?" checks, replacing the need to sort or scan                                              |
| Run-start detection | Only begin counting a run at a number`x` whose predecessor `x-1` is **absent** — this is what keeps the set approach linear |
| Sort-and-scan       | Simpler baseline: dedupe + sort, then walk once counting consecutive runs                                                              |

**Canonical example** (from notebook):

```
[100, 4, 200, 1, 3, 2] -> 4     (the run 1, 2, 3, 4)
```

Expected outputs (from notebook asserts):

| Input                              | Expected | `longest_consec_sort` | `longest_consec_set` |
| ---------------------------------- | -------- | ----------------------- | ---------------------- |
| `[100, 4, 200, 1, 3, 2]`         | `4`    | ✓ matches              | ✓ matches             |
| `[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]` | `9`    | ✓ matches              | ✓ matches             |
| `[]`                             | `0`    | ✓ matches              | ✓ matches             |
| `[5, 5, 5]`                      | `1`    | ✓ matches              | ✓ matches             |

---

## `longest_consec_sort` — Sort, Then Scan (worst)

### What it does

Deduplicates and sorts the input. Walks the sorted unique values once, extending a running streak `cur` whenever the current value is exactly one more than the previous value, and resetting `cur` to `1` whenever there's a gap. Tracks `best` as the maximum streak seen.

### Code

```python
def longest_consec_sort(nums):
    if not nums:
        return 0
    s = sorted(set(nums))                  # unique values in order
    best = cur = 1
    for i in range(1, len(s)):
        if s[i] == s[i-1] + 1:             # continues the current run
            cur += 1; best = max(best, cur)
        else:
            cur = 1                        # gap -> start a new run
    return best
```

### Line by line

| Line / code                         | What it does                                                               |
| ----------------------------------- | -------------------------------------------------------------------------- |
| `if not nums: return 0`           | Empty input has no run                                                     |
| `s = sorted(set(nums))`           | Dedupe (so repeats like`5,5,5` don't inflate a run), then sort ascending |
| `best = cur = 1`                  | A single value is always a run of length ≥ 1                              |
| `for i in range(1, len(s))`       | Walk every adjacent pair in sorted order                                   |
| `if s[i] == s[i-1] + 1`           | Consecutive values — streak continues                                     |
| `cur += 1; best = max(best, cur)` | Extend the streak and update the best-seen length                          |
| `else: cur = 1`                   | Gap found — the streak resets, starting fresh at length 1                 |
| `return best`                     | Longest streak found across the whole scan                                 |

### Step-by-step trace (canonical example `[100, 4, 200, 1, 3, 2]`)

`s = sorted(set([100, 4, 200, 1, 3, 2])) = [1, 2, 3, 4, 100, 200]`

| Step | `i` | `s[i]` | `s[i-1]` | Consecutive?    | `cur` | `best` |
| ---- | ----- | -------- | ---------- | --------------- | ------- | -------- |
| init | —    | —       | —         | —              | `1`   | `1`    |
| 1    | 1     | `2`    | `1`      | yes (`1+1=2`) | `2`   | `2`    |
| 2    | 2     | `3`    | `2`      | yes (`2+1=3`) | `3`   | `3`    |
| 3    | 3     | `4`    | `3`      | yes (`3+1=4`) | `4`   | `4`    |
| 4    | 4     | `100`  | `4`      | no (gap)        | `1`   | `4`    |
| 5    | 5     | `200`  | `100`    | no (gap)        | `1`   | `4`    |

**Result:** `best = 4` ✓ (the run `1, 2, 3, 4`)

### Mental model

- Sorting turns "find consecutive runs anywhere" into "find consecutive runs in a line" — a single linear pass suffices after the `O(n log n)` sort.
- `cur` is a streak counter that only ever grows by exactly 1 or resets to 1 — it never needs to "look back" further than the immediately previous element.
- Deduplication via `set(nums)` before sorting is what makes `[5, 5, 5]` correctly return `1` instead of `3`.

### Common confusions

- **Forgetting to dedupe:** without `set(nums)`, repeated values (`5, 5, 5`) would be adjacent in the sorted list but are not a "consecutive" run — they'd need an explicit equal-value check instead of relying on dedup.
- **Off-by-one on `best` initialization:** `best = cur = 1` (not `0`) because a non-empty array always has a run of at least length 1.
- **Confusing "sorted order" with "index order":** the streak check compares *values* (`s[i] == s[i-1] + 1`), not array positions in the original unsorted input.

### Complexity

- **Time:** `O(n log n)` — dominated by the sort
- **Space:** `O(n)` — the deduped/sorted list

---

## `longest_consec_set` — Hash Set, Grow From Starts (optimal)

### What it does

Puts every number into a set for O(1) membership tests. For each number `x`, only starts counting a run if `x - 1` is **not** in the set (meaning `x` is the true start of its run). From a true start, walks forward (`x+1`, `x+2`, ...) while each next number exists in the set, tracking the run's length. Keeps the max length seen across all starts.

### Code

```python
def longest_consec_set(nums):
    numset = set(nums)                     # O(1) membership tests
    best = 0
    for x in numset:
        if x - 1 not in numset:            # x is the START of a run (nothing comes before it)
            length = 1
            while x + length in numset:    # walk forward while the next number exists
                length += 1
            best = max(best, length)
    return best                            # each number is visited at most once overall
```

### Line by line

| Line / code                                 | What it does                                                          |
| ------------------------------------------- | --------------------------------------------------------------------- |
| `numset = set(nums)`                      | Build the hash set once — dedupes and gives O(1) lookups             |
| `best = 0`                                | No run found yet (handles the empty-input case naturally)             |
| `for x in numset`                         | Consider every distinct value as a potential run start                |
| `if x - 1 not in numset`                  | Skip`x` unless it's a true run start — its predecessor is missing  |
| `length = 1`                              | The run starting at`x` includes at least `x` itself               |
| `while x + length in numset: length += 1` | Extend the run forward one step at a time while the next value exists |
| `best = max(best, length)`                | Record the longest run found so far                                   |
| `return best`                             | Longest consecutive run length across the whole array                 |

### Step-by-step trace (canonical example `[100, 4, 200, 1, 3, 2]`)

`numset = {100, 4, 200, 1, 3, 2}`

Iterating `x` over the set (order doesn't matter — the "is it a start" filter makes the result order-independent):

| `x`   | `x - 1 in numset`? | Is a start? | Walk (`x + length in numset`)              | Final`length` | `best` after |
| ------- | -------------------- | ----------- | -------------------------------------------- | --------------- | -------------- |
| `100` | `99` absent        | yes         | `101` absent → stop                       | `1`           | `1`          |
| `4`   | `3` present        | no          | — (skipped)                                 | —              | `1`          |
| `200` | `199` absent       | yes         | `201` absent → stop                       | `1`           | `1`          |
| `1`   | `0` absent         | yes         | `2`✓ `3`✓ `4`✓ `5` absent → stop | `4`           | `4`          |
| `3`   | `2` present        | no          | — (skipped)                                 | —              | `4`          |
| `2`   | `1` present        | no          | — (skipped)                                 | —              | `4`          |

Only `x = 1` is a true run start (its predecessor `0` is missing), and walking forward from it finds `1, 2, 3, 4` — a streak of length `4`, which becomes the answer. Every other candidate either isn't a start (skipped immediately) or produces a run of length `1`.

**Result:** `best = 4` ✓

### Mental model

- Think of the set as chains of consecutive numbers; the `x - 1 not in numset` check finds each chain's "head" so it's only walked once, from the front.
- Because every number is examined by at most one walk (as the start of its own chain, or skipped as an interior/non-start element), the total work across *all* walks combined is `O(n)`, not `O(n)` per element.
- No sorting needed — membership testing replaces the need for order.

### Common confusions

- **Starting a walk from every element (not just true starts):** this is the classic bug that silently degrades to `O(n²)` — e.g. walking from `2`, `3`, and `4` in addition to `1` would re-scan the same run three extra times.
- **Why check `x - 1` and not `x + 1`:** checking the predecessor identifies the *start* of a chain; checking the successor would not prevent redundant walks from the middle of a chain.
- **Duplicates:** `set(nums)` already collapses duplicates like `[5, 5, 5]` into `{5}`, so the walk correctly yields `1`, not `3`.
- **Iteration order:** iterating a Python `set` has no guaranteed order, but the algorithm's correctness doesn't depend on order — every true start is found and every non-start is skipped regardless of visit order.

### Complexity

- **Time:** `O(n)` — each number is visited a constant number of times overall (once as a candidate, and at most once as part of exactly one run's forward walk)
- **Space:** `O(n)` — the hash set

---

## Quick reference

| Function                | Technique                               | Result on`[100,4,200,1,3,2]` | Time           | Space    |
| ----------------------- | --------------------------------------- | ------------------------------ | -------------- | -------- |
| `longest_consec_sort` | Dedupe + sort, scan for streaks         | `4`                          | `O(n log n)` | `O(n)` |
| `longest_consec_set`  | Hash set, walk forward from true starts | `4`                          | `O(n)`       | `O(n)` |

## Patterns to remember

- **Set membership to avoid sorting:** testing "is the neighbor present?" in O(1) lets you find runs in linear time instead of paying for a sort.
- **Only start at true starts:** the `x - 1 not in numset` check is what keeps the hash-set approach O(n) — without it, every element re-walks its whole chain and the algorithm degrades toward O(n²).
- **Signal words:** "longest consecutive", "run of numbers", "O(n) without sorting", "unsorted array of integers".
- **Related problems:** Longest Increasing Subsequence (different — that's about relative order, not exact `+1` chains), Union-Find groupings (an alternative way to merge chains), Number of Islands (same "expand from a seed, mark visited" flavor).
- **Common pitfalls:** (1) counting a run starting from every element instead of only true starts (→ O(n²)); (2) not de-duplicating before sorting/scanning.
