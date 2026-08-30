# 424. Longest Repeating Character Replacement — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 1_sliding-window/longest_repeating_character_replacement.ipynb`
> **LeetCode:** https://leetcode.com/problems/longest-repeating-character-replacement/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Sliding window | Grow the window on the right; shrink from the left when it becomes invalid |
| "Changes needed" formula | `window length - count of most frequent letter` = characters you'd have to replace to make the window all one letter |
| Max-frequency count | Track `maxf`, the count of the most common letter currently in the window, to test validity in O(1) |
| Brute force baseline | Try every start, extending while `length - maxf <= k` — `O(n^2)` |

**Canonical example** (from notebook asserts):

```
s = "ABAB", k = 2  -> 4   (change both A->B or both B->A)
```

Other notebook asserts: `("AABABBA", 1) -> 4`, `("AAAA", 0) -> 4`, `("ABCDE", 1) -> 2`.

---

## `char_replace_brute` — Check Every Start (worst)

### What it does

For each starting index `i`, extends the window right while it can still be turned into one repeated letter using at most `k` replacements (`window length - most-frequent-letter count <= k`). The moment that condition fails it stops (it can only get worse from there) and moves to the next start.

### Code

```python
def char_replace_brute(s: str, k: int) -> int:
    best = 0
    n = len(s)
    for i in range(n):                     # try every starting index
        count = {}                         # letter counts inside the current window
        maxf = 0                           # count of the most common letter in the window
        for j in range(i, n):              # extend the window to the right
            count[s[j]] = count.get(s[j], 0) + 1
            maxf = max(maxf, count[s[j]])  # update the most-frequent letter's count
            # letters we'd have to change = window size - most common letter's count
            if (j - i + 1) - maxf > k:     # needs more than k changes...
                break                      # ...and it only gets worse, so stop this start
            best = max(best, j - i + 1)    # window is fixable within k -> record its length
    return best
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `for i in range(n):` | Outer loop — try every starting index |
| `count = {}; maxf = 0` | Reset per-start letter counts and the running max frequency |
| `for j in range(i, n):` | Inner loop — extend the window right from `i` |
| `count[s[j]] = count.get(s[j], 0) + 1` | Tally the incoming letter |
| `maxf = max(maxf, count[s[j]])` | Track the highest single-letter count seen in this window so far |
| `if (j - i + 1) - maxf > k: break` | `changes needed = size - maxf`; if it exceeds `k`, this start can't extend further |
| `best = max(best, j - i + 1)` | Window is still fixable within `k` -> record its length |

### Step-by-step trace (canonical example `s = "ABAB"`, `k = 2`)

Indices: `0:A 1:B 2:A 3:B`

| `i` | Inner iterations (`j`, char, `count`, `maxf`, changes-needed, action) | `best` after this `i` |
| --- | --------------------------------------------------------------------------- | ------------------------ |
| 0 | j=0 'A' count={A:1} maxf=1 needed=1-1=0<=2 best=1; j=1 'B' count={A:1,B:1} maxf=1 needed=2-1=1<=2 best=2; j=2 'A' count={A:2,B:1} maxf=2 needed=3-2=1<=2 best=3; j=3 'B' count={A:2,B:2} maxf=2 needed=4-2=2<=2 best=4 | 4 |
| 1 | j=1 'B' count={B:1} maxf=1 needed=0 best=1; j=2 'A' count={B:1,A:1} maxf=1 needed=1<=2 best=2; j=3 'B' count={B:2,A:1} maxf=2 needed=1<=2 best=3 | 4 |
| 2 | j=2 'A' count={A:1} maxf=1 needed=0 best=1; j=3 'B' count={A:1,B:1} maxf=1 needed=1<=2 best=2 | 4 |
| 3 | j=3 'B' count={B:1} maxf=1 needed=0 best=1 | 4 |

**Final output on `("ABAB", 2)`:** `4` (matches the assert)

### Mental model

- "Changes needed" is a single formula, not a rescan — recomputed cheaply from `maxf` each step.
- Because `maxf` only ever grows within one start's inner loop, once `size - maxf > k` fails there's no point continuing that start: adding more characters can only keep `size` growing while `maxf` growing is capped by the remaining unique-letter counts, so the gap can't shrink back below `k`.
- This is the naive baseline; the windowed version reuses `count`/`maxf` across starts instead of resetting them.

### Common confusions

- **`maxf` is never decremented within a start:** it's a running max across the growing window, which is exactly why the "stop, it only gets worse" reasoning for `break` holds.
- **The formula counts *changes*, not matches:** `size - maxf` is how many non-majority letters exist in the window, i.e. how many would need to change.
- **`k = 0` still works:** it just means "no changes allowed", so the window must already be one repeated letter.

### Complexity

- **Time:** `O(n^2)` — up to `n` starts, each re-scanning up to `n` characters
- **Space:** `O(1)` — `count` holds at most 26 letters regardless of `n`

---

## `char_replace_window` — Sliding Window (optimal)

### What it does

Maintains one window `[left, right]` across the whole string with a persistent `count` map and running `maxf`. Grows `right` every step, updating `maxf`; whenever the window needs more than `k` changes (`size - maxf > k`), shrinks from the left until it's valid again. The best valid window length seen is the answer.

### Code

```python
def char_replace_window(s: str, k: int) -> int:
    count = {}                             # letter counts inside the window
    left = best = maxf = 0                 # window left edge; best length; top letter count
    for right in range(len(s)):            # right edge sweeps across
        count[s[right]] = count.get(s[right], 0) + 1
        maxf = max(maxf, count[s[right]])  # most frequent letter in the window
        # If the window needs more than k replacements, shrink it from the left.
        while (right - left + 1) - maxf > k:
            count[s[left]] -= 1            # remove the leftmost letter
            left += 1                      # move the left edge right
        best = max(best, right - left + 1) # window is now valid -> update best length
    return best
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `count = {}` | Persistent letter counts for `[left, right]` |
| `left = best = maxf = 0` | Window left edge, running best, and running max-frequency |
| `for right in range(len(s)):` | Right edge sweeps once across the string |
| `count[s[right]] += 1` | Tally the incoming letter |
| `maxf = max(maxf, count[s[right]])` | Update the most-frequent letter's count (never decremented, see below) |
| `while (right - left + 1) - maxf > k:` | Window is invalid; keep shrinking until it's fixable within `k` |
| `count[s[left]] -= 1; left += 1` | Remove the leftmost letter and advance `left` |
| `best = max(best, right - left + 1)` | Record the window length if it's a new best |

### Step-by-step trace (canonical example `s = "ABAB"`, `k = 2`)

| `right` | char | `count` after tally | `maxf` | window size | needed (`size - maxf`) | shrink? | `left` after | `best` after |
| ------- | ---- | ---------------------- | ------ | ----------- | ------------------------- | ------- | -------------- | ------------- |
| 0 | 'A' | `{A:1}` | 1 | 1 | 0 | no (0<=2) | 0 | 1 |
| 1 | 'B' | `{A:1,B:1}` | 1 | 2 | 1 | no (1<=2) | 0 | 2 |
| 2 | 'A' | `{A:2,B:1}` | 2 | 3 | 1 | no (1<=2) | 0 | 3 |
| 3 | 'B' | `{A:2,B:2}` | 2 | 4 | 2 | no (2<=2) | 0 | 4 |

**Final output on `("ABAB", 2)`:** `4` (matches the assert)

### Mental model

- `maxf` is a **watermark**, not a live max — it's allowed to stay stale (referencing a count from a letter that has since partially left the window) because a stale `maxf` can only make the shrink condition *stricter* than necessary, never *looser*; it never causes an invalid window to be accepted as valid, only possibly delays finding the true best by a step it will later catch up to.
- The window never shrinks below the largest valid window already found, because `best` tracks the max window size ever reached and the window's size only decreases when it's already invalid.
- Grow-check-maybe-shrink is the same two-pointer shape as the "no repeating characters" problem, just with a different validity test.

### Common confusions

- **Not decrementing `maxf` when shrinking:** this looks like a bug but is intentional — the answer only cares about the *largest* valid window seen, and a stale `maxf` never lets the algorithm accept an invalid window (it only makes the shrink trigger slightly earlier-than-strictly-needed in later steps, which self-corrects as `right` keeps advancing).
- **`while` vs `if` for shrinking:** using `while` (not `if`) matters in general, though because `maxf` never decreases, in practice at most one shrink step is needed per `right` step here.
- **Off-by-one in the formula:** window size is `right - left + 1`, not `right - left`.

### Complexity

- **Time:** `O(n)` — amortized; `left` and `right` each traverse the string at most once
- **Space:** `O(1)` — `count` holds at most 26 letters regardless of `n`

---

## Quick reference

| Function | Technique | Output on `("ABAB", 2)` | Time | Space |
| -------- | --------- | -------------------------- | ---- | ----- |
| `char_replace_brute` | Try every start, `size - maxf <= k` check | `4` | `O(n^2)` | `O(1)` |
| `char_replace_window` | Sliding window with running `maxf` watermark | `4` | `O(n)` | `O(1)` |

## Patterns to remember

- **Window validity via a cheap summary:** track just the most-frequent count; the "changes needed" formula (`size - maxf`) tells you when to shrink without rescanning the window.
- **Stale watermark trick:** letting `maxf` go stale during shrinks is safe because the goal is the largest window ever seen, not the currently-most-precise one.
- **Signal words:** "longest substring after changing at most k", "at most k edits / flips".
- **Related problems:** Longest Substring Without Repeating Characters, Max Consecutive Ones III, Minimum Window Substring.
- **Common pitfalls:** (1) recomputing max frequency from scratch every step (unnecessary and slow); (2) using `if` instead of a `while`/size-check for shrinking; (3) forgetting the `-maxf` term and just comparing window size to `k` directly.
