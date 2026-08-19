# 3. Longest Substring Without Repeating Characters — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 1_sliding-window/longest_substring_without_repeating.ipynb`
> **LeetCode:** https://leetcode.com/problems/longest-substring-without-repeating-characters/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Sliding window | Grow the window on the right; shrink from the left whenever a repeat appears |
| Hash set | `seen` tracks which characters currently sit inside the window |
| Hash map (last-seen) | Remembering *where* each character last appeared lets `left` jump instead of crawl |
| Brute force baseline | Try every start index, re-scanning with a fresh `set` each time — `O(n^2)` |

**Canonical example** (from notebook asserts):

```
"abcabcbb" -> 3   ("abc")
```

Other notebook asserts: `"bbbbb" -> 1`, `"pwwkew" -> 3`, `"" -> 0`, `"dvdf" -> 3`, `"abba" -> 2`.

---

## `length_brute` — Check Every Start (worst)

### What it does

For every possible starting index `i`, extends a fresh window to the right using a local `seen` set. The moment a repeated character would enter, it stops that start entirely (no early exits beyond a single break) and moves on to the next `i`. Tracks the best window length found across all starts.

### Code

```python
def length_brute(s: str) -> int:
    best = 0
    for i in range(len(s)):                # try every possible starting index
        seen = set()                       # characters used in the current window
        for j in range(i, len(s)):         # extend the window to the right
            if s[j] in seen:               # a repeat means this window can't grow further
                break                      # stop; move on to the next start i
            seen.add(s[j])                 # record the new character
            best = max(best, j - i + 1)    # window length = j - i + 1
    return best
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `for i in range(len(s)):` | Outer loop — try every starting index |
| `seen = set()` | Reset the "characters used so far" tracker for this start |
| `for j in range(i, len(s)):` | Inner loop — extend the window right from `i` |
| `if s[j] in seen: break` | A repeat means this start can't extend further; abandon it |
| `seen.add(s[j])` | Record the new, still-unique character |
| `best = max(best, j - i + 1)` | Window length is `j - i + 1`; keep the best seen |

### Step-by-step trace (canonical example `"abcabcbb"`)

Indices: `0:a 1:b 2:c 3:a 4:b 5:c 6:b 7:b`

| `i` | Inner iterations (`j`, char, action) | Window found | `best` after this `i` |
| --- | --------------------------------------- | ------------- | ---------------------- |
| 0 | j=0 'a' add; j=1 'b' add; j=2 'c' add; j=3 'a' repeat -> break | `"abc"` (len 3) | 3 |
| 1 | j=1 'b' add; j=2 'c' add; j=3 'a' add; j=4 'b' repeat -> break | `"bca"` (len 3) | 3 |
| 2 | j=2 'c' add; j=3 'a' add; j=4 'b' add; j=5 'c' repeat -> break | `"cab"` (len 3) | 3 |
| 3 | j=3 'a' add; j=4 'b' add; j=5 'c' add; j=6 'b' repeat -> break | `"abc"` (len 3) | 3 |
| 4 | j=4 'b' add; j=5 'c' add; j=6 'b' repeat -> break | `"bc"` (len 2) | 3 |
| 5 | j=5 'c' add; j=6 'b' add; j=7 'b' repeat -> break | `"cb"` (len 2) | 3 |
| 6 | j=6 'b' add; j=7 'b' repeat -> break | `"b"` (len 1) | 3 |
| 7 | j=7 'b' add (inner loop ends naturally, no repeat left to hit) | `"b"` (len 1) | 3 |

**Final output on `"abcabcbb"`:** `3` (matches the assert)

### Mental model

- Every start index gets its own clean slate — no information is carried between starts.
- A repeat always means "stop growing right now, restart from a later `i`", so the inner loop never overshoots.
- This is the naive baseline that the sliding-window versions optimize away by reusing work across starts.

### Common confusions

- **`break` vs `continue`:** on a repeat you abandon the *rest of this start*, not just this character — hence `break`, not skipping just `j`.
- **Fresh `seen` per `i`:** forgetting to reset `seen` inside the outer loop would corrupt every subsequent start.
- **Quadratic, not linear:** each `i` can re-examine characters already seen by previous starts — that redundant work is exactly what `O(n)` approaches eliminate.

### Complexity

- **Time:** `O(n^2)` — up to `n` starts, each re-scanning up to `n` characters
- **Space:** `O(n)` — the `seen` set can hold up to the window's length

---

## `length_window_set` — Sliding Window with a Set

### What it does

Maintains one window `[left, right]` across the whole string using a single `seen` set that persists between iterations. When the incoming character `s[right]` is already inside the window, characters are removed from the left one at a time until the duplicate is gone, then the new character is added.

### Code

```python
def length_window_set(s: str) -> int:
    seen = set()                           # characters currently inside the window
    left = best = 0                        # left edge of the window; best length so far
    for right in range(len(s)):            # right edge sweeps across the string
        while s[right] in seen:            # new char already inside -> shrink from the left
            seen.remove(s[left])           # drop the leftmost char
            left += 1                      # move the left edge right
        seen.add(s[right])                 # now safe to add the new character
        best = max(best, right - left + 1) # update the best window length
    return best
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `seen = set()` | Characters currently inside `[left, right]` |
| `left = best = 0` | Window's left edge and running best length |
| `for right in range(len(s)):` | Right edge sweeps once across the string |
| `while s[right] in seen:` | Keep shrinking as long as the incoming char is a duplicate |
| `seen.remove(s[left]); left += 1` | Drop the leftmost character and advance `left` |
| `seen.add(s[right])` | The window is now duplicate-free; admit the new character |
| `best = max(best, right - left + 1)` | Record the window length if it's a new best |

### Step-by-step trace (canonical example `"abcabcbb"`)

| `right` | char | shrink steps (`while`) | `seen` after | `left` | `best` after |
| ------- | ---- | ----------------------- | -------------- | ------ | ------------- |
| 0 | 'a' | none | `{a}` | 0 | 1 |
| 1 | 'b' | none | `{a,b}` | 0 | 2 |
| 2 | 'c' | none | `{a,b,c}` | 0 | 3 |
| 3 | 'a' | remove 'a' (left 0->1) | `{b,c,a}` | 1 | 3 |
| 4 | 'b' | remove 'b' (left 1->2) | `{c,a,b}` | 2 | 3 |
| 5 | 'c' | remove 'c' (left 2->3) | `{a,b,c}` | 3 | 3 |
| 6 | 'b' | remove 'a' (left 3->4), remove 'b' (left 4->5) | `{c,b}` | 5 | 3 |
| 7 | 'b' | remove 'c' (left 5->6), remove 'b' (left 6->7) | `{b}` | 7 | 3 |

**Final output on `"abcabcbb"`:** `3` (matches the assert)

### Mental model

- `seen` always mirrors exactly what's between `left` and `right` — no stale entries survive.
- The `while` (not `if`) handles the case where multiple stale characters must leave before the duplicate is actually gone.
- Every character is added once and removed at most once — that's what makes the total work `O(n)` even though there's a nested loop.

### Common confusions

- **`while` vs `if` for shrinking:** a single `if` would be wrong if more than one character needs to leave before the window is valid again.
- **Order of operations:** shrink *before* adding the new character, not after — otherwise the set briefly contains a duplicate.
- **Amortized, not literally linear-looking:** the inner `while` can run multiple times per outer step, but `left` never moves backward, so total shrink-steps across the whole run are bounded by `n`.

### Complexity

- **Time:** `O(n)` — amortized; `left` and `right` each traverse the string at most once
- **Space:** `O(n)` — the `seen` set can hold up to `min(n, alphabet size)` characters

---

## `length_window_map` — Sliding Window with Last-Seen Map

### What it does

Instead of shrinking one character at a time, remembers the **last index** each character was seen at. When `s[right]` repeats *inside* the current window, `left` jumps directly to one past that last position — no incremental removal needed.

### Code

```python
def length_window_map(s: str) -> int:
    last = {}                              # character -> the last index we saw it at
    left = best = 0                        # window's left edge; best length so far
    for right, c in enumerate(s):          # right edge sweeps across the string
        # If c was seen and its last position is inside the window, jump left past it.
        if c in last and last[c] >= left:
            left = last[c] + 1             # skip straight past the previous copy
        last[c] = right                    # remember where we saw c this time
        best = max(best, right - left + 1) # update the best window length
    return best
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `last = {}` | Maps each character to the most recent index it appeared at |
| `left = best = 0` | Window's left edge and running best length |
| `for right, c in enumerate(s):` | Right edge sweeps once across the string, `c` is `s[right]` |
| `if c in last and last[c] >= left:` | Only jump if the previous copy of `c` is still inside the window (stale positions outside `[left, right]` are ignored) |
| `left = last[c] + 1` | Jump `left` straight past the previous occurrence |
| `last[c] = right` | Update `c`'s last-seen position to the current index |
| `best = max(best, right - left + 1)` | Record the window length if it's a new best |

### Step-by-step trace (canonical example `"abcabcbb"`)

| `right` | `c` | `c in last`? | `last[c] >= left`? | `left` after | `last` after | `best` after |
| ------- | --- | ------------ | -------------------- | -------------- | -------------- | ------------- |
| 0 | 'a' | no | — | 0 | `{a:0}` | 1 |
| 1 | 'b' | no | — | 0 | `{a:0,b:1}` | 2 |
| 2 | 'c' | no | — | 0 | `{a:0,b:1,c:2}` | 3 |
| 3 | 'a' | yes (0) | 0>=0 yes | 1 | `{a:3,b:1,c:2}` | 3 |
| 4 | 'b' | yes (1) | 1>=1 yes | 2 | `{a:3,b:4,c:2}` | 3 |
| 5 | 'c' | yes (2) | 2>=2 yes | 3 | `{a:3,b:4,c:5}` | 3 |
| 6 | 'b' | yes (4) | 4>=3 yes | 5 | `{a:3,b:6,c:5}` | 3 |
| 7 | 'b' | yes (6) | 6>=5 yes | 7 | `{a:3,b:7,c:5}` | 3 |

**Final output on `"abcabcbb"`:** `3` (matches the assert)

### Mental model

- `last` is a memory of "where did I last see this character", not "is it in the window right now" — the `last[c] >= left` guard is what converts that memory into a window-aware check.
- Jumping `left` directly to `last[c] + 1` replaces potentially many one-step removals with a single O(1) update.
- `left` only ever moves forward, same invariant as the set-based version, just reached differently.

### Common confusions

- **Forgetting `last[c] >= left`:** without this guard, a character seen long ago (now outside the window) would incorrectly yank `left` forward past where it already is, or even backward — always check the stale-position condition.
- **`left` moving backward:** if you compute `left = last[c] + 1` unconditionally, `left` could move *left* on a stale hit; the `>= left` guard prevents that.
- **Updating `last[c]` unconditionally:** this must happen every time regardless of the jump, so future lookups see the freshest position.

### Complexity

- **Time:** `O(n)` — single pass, O(1) work per character
- **Space:** `O(n)` — `last` can hold up to `min(n, alphabet size)` entries

---

## Quick reference

| Function | Technique | Output on `"abcabcbb"` | Time | Space |
| -------- | --------- | ------------------------ | ---- | ----- |
| `length_brute` | Try every start, fresh set | `3` | `O(n^2)` | `O(n)` |
| `length_window_set` | Sliding window, shrink one char at a time | `3` | `O(n)` | `O(n)` |
| `length_window_map` | Sliding window, jump left via last-seen map | `3` | `O(n)` | `O(n)` |

## Patterns to remember

- **Sliding window for "longest/shortest stretch that satisfies a rule":** grow on the right, shrink on the left, keep a running summary — `O(n)`.
- **Last-seen map to jump:** remembering positions lets the left edge leap instead of crawl, collapsing a `while`-loop shrink into an O(1) jump.
- **Signal words:** "longest/shortest substring with (no repeats / at most k / containing ...)".
- **Related problems:** Longest Repeating Character Replacement, Minimum Window Substring, Find All Anagrams.
- **Common pitfalls:** (1) not checking `last[c] >= left` (acting on stale positions); (2) forgetting to update the best length every step, not just when the window grows; (3) using `if` instead of `while` when shrinking one character at a time (multiple stale characters may need to leave).
