# 76. Minimum Window Substring — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 1_sliding-window/minimum_window_substring.ipynb`
> **LeetCode:** https://leetcode.com/problems/minimum-window-substring/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Sliding window | Grow the window on the right until it covers all of `t`; then shrink from the left as much as possible while it still covers |
| `Counter` of needed letters | `need[c]` starts as how many of `c` are still required; can go negative for extra copies collected |
| `missing` tally | Single running counter of "how many characters (with multiplicity) are still uncovered" — avoids rescanning counts every step |
| Brute force baseline | Try every start, check full coverage with `all(...)` each extension — `O(n^2 * m)` |

**Canonical example** (from notebook asserts):

```
s = "ADOBECODEBANC", t = "ABC" -> "BANC"
```

Other notebook asserts: `("a","a") -> "a"`, `("a","aa") -> ""`, `("aa","aa") -> "aa"`.

---

## `min_window_brute` — Check Every Start (worst)

### What it does

For each start `i`, extends the window right, tallying characters into a local `count` dict. After every extension it checks — via `all(count.get(c,0) >= need[c] for c in need)` — whether the window now contains at least as many of each needed character as `t` requires. The first time it does, that's the shortest possible window for this start, so it records it (if better than the current best) and stops extending.

### Code

```python
from collections import Counter

def min_window_brute(s: str, t: str) -> str:
    if not t or not s:
        return ""
    need = Counter(t)                      # how many of each character we must cover
    n = len(s)
    best = ""
    for i in range(n):                     # try every starting index
        count = {}                         # characters collected in the current window
        for j in range(i, n):              # extend the window to the right
            count[s[j]] = count.get(s[j], 0) + 1
            # Does the window now contain enough of every needed character?
            if all(count.get(c, 0) >= need[c] for c in need):
                if best == "" or (j - i + 1) < len(best):
                    best = s[i:j+1]        # keep the shortest covering window
                break                      # can't get shorter for this start -> next i
    return best
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not t or not s: return ""` | Edge case — nothing to search or nothing to find |
| `need = Counter(t)` | Required count of each character, taken from `t` |
| `for i in range(n):` | Outer loop — try every starting index |
| `count = {}` | Reset per-start character tally |
| `for j in range(i, n):` | Inner loop — extend the window right from `i` |
| `count[s[j]] = count.get(s[j], 0) + 1` | Tally the incoming character |
| `all(count.get(c, 0) >= need[c] for c in need)` | True once every needed character is fully covered |
| `if best == "" or (j - i + 1) < len(best): best = s[i:j+1]` | Keep the shortest covering window seen so far |
| `break` | Once covered, no shorter window exists for this start; move to next `i` |

### Step-by-step trace (canonical example `s = "ADOBECODEBANC"`, `t = "ABC"`)

`need = {A:1, B:1, C:1}`. Indices: `0:A 1:D 2:O 3:B 4:E 5:C 6:O 7:D 8:E 9:B 10:A 11:N 12:C`

Per-start summary (each row = one outer `i`; inner `j` extends until coverage is found or the string ends):

| `i` | Extends to `j=` | Window when covered (or "never") | `best` after this `i` |
| --- | ---------------- | ------------------------------------ | ------------------------ |
| 0 | 5 | `"ADOBEC"` (len 6) -> best is empty, so best = `"ADOBEC"` | `"ADOBEC"` |
| 1 | 10 | `"DOBECODEBA"` (len 10) -> 10 < 6? no | `"ADOBEC"` |
| 2 | 10 | `"OBECODEBA"` (len 9) -> 9 < 6? no | `"ADOBEC"` |
| 3 | 10 | `"BECODEBA"` (len 8) -> 8 < 6? no | `"ADOBEC"` |
| 4 | 10 | `"ECODEBA"` (len 7) -> 7 < 6? no | `"ADOBEC"` |
| 5 | 10 | `"CODEBA"` (len 6) -> 6 < 6? no | `"ADOBEC"` |
| 6 | 12 | `"ODEBANC"` (len 7) -> 7 < 6? no | `"ADOBEC"` |
| 7 | 12 | `"DEBANC"` (len 6) -> 6 < 6? no | `"ADOBEC"` |
| 8 | 12 | `"EBANC"` (len 5) -> 5 < 6? yes | `"EBANC"` |
| 9 | 12 | `"BANC"` (len 4) -> 4 < 5? yes | `"BANC"` |
| 10 | 12 (no break) | never covered (`count` reaches `{A:1,N:1,C:1}`, missing `B`) | `"BANC"` |
| 11 | 12 (no break) | never covered (`count` reaches `{N:1,C:1}`) | `"BANC"` |
| 12 | 12 (no break) | never covered (`count = {C:1}`) | `"BANC"` |

**Final output on `("ADOBECODEBANC", "ABC")`:** `"BANC"` (matches the assert)

### Mental model

- For a fixed start `i`, the *first* moment coverage is achieved is automatically the shortest window for that start — extending further can only make it longer, hence the `break`.
- `all(...)` is an O(`len(need)`) check performed on every extension, which is what pushes this to `O(n^2 * m)` overall (`m` = size of the alphabet of `t`).
- Later starts (10, 11, 12) never reach coverage because `t` requires one each of A, B, C but the remaining suffix of `s` is missing at least one of them — the inner loop runs to the end without a `break`.

### Common confusions

- **`best == "" or (j - i + 1) < len(best)`:** the empty-string check is necessary because `""` would otherwise never be "shorter than" a real window under plain length comparison in the wrong direction — this guards the very first assignment.
- **`need[c]` on a `Counter`:** missing keys default to `0`, so `all(...)` only ever iterates over the keys actually present in `t`.
- **No `break` when never covered:** if the inner loop runs to the end without covering `t`, nothing is recorded for that `i` — that's expected, not a bug.

### Complexity

- **Time:** `O(n^2 * m)` — up to `n` starts, each extending up to `n` steps, each step doing an `O(m)` coverage check (`m` = distinct characters in `t`)
- **Space:** `O(m)` — `need` and `count` are bounded by the alphabet involved

---

## `min_window_slide` — Sliding Window (optimal)

### What it does

Keeps one window `[left, right)` across the whole string with a persistent `need` counter (can go negative for over-collected characters) and a single integer `missing` — the total remaining characters (with multiplicity) still required to cover `t`. Grows `right`; every time `missing` hits `0` (full coverage), enters a `while` loop that records the window if it's the smallest so far and then shrinks from the left, restoring `missing` the instant a still-needed character would be lost.

### Code

```python
from collections import Counter

def min_window_slide(s: str, t: str) -> str:
    if not t or not s:
        return ""
    need = Counter(t)                      # remaining count needed for each character
    missing = len(t)                       # total characters still to cover (with repeats)
    left = 0                               # left edge of the window
    best = (float("inf"), 0, 0)            # (window length, start, end+1) of the best so far
    for right, c in enumerate(s):          # right edge sweeps across s
        if need[c] > 0:                    # c is a character we still needed
            missing -= 1                   # one fewer to cover
        need[c] -= 1                       # (can go negative for extra copies)
        while missing == 0:                # window covers all of t -> try to shrink it
            if right - left + 1 < best[0]:
                best = (right - left + 1, left, right + 1)   # record a smaller window
            need[s[left]] += 1             # about to drop the leftmost char
            if need[s[left]] > 0:          # dropping it breaks coverage
                missing += 1               # we now need that character again
            left += 1                      # move the left edge right
    return "" if best[0] == float("inf") else s[best[1]:best[2]]
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `need = Counter(t); missing = len(t)` | Start with every character of `t` counted as "still needed" |
| `left = 0; best = (inf, 0, 0)` | Window left edge; best window as `(length, start, end+1)`, initially "none found" |
| `for right, c in enumerate(s):` | Right edge sweeps once across `s` |
| `if need[c] > 0: missing -= 1` | Only counts down `missing` if `c` was actually still required (not an already-satisfied surplus) |
| `need[c] -= 1` | Always decrement, even into negative territory for extra copies |
| `while missing == 0:` | Window fully covers `t` — try to shrink it as far as possible |
| `if right - left + 1 < best[0]: best = (...)` | Smaller valid window found -> record it |
| `need[s[left]] += 1` | Give back the leftmost character before dropping it from the window |
| `if need[s[left]] > 0: missing += 1` | If that character is now back in deficit, coverage is broken -> stop shrinking after this step |
| `left += 1` | Advance the left edge |
| `return "" if best[0] == inf else s[best[1]:best[2]]` | No covering window was ever found -> `""`; otherwise slice out the recorded best |

### Step-by-step trace (canonical example `s = "ADOBECODEBANC"`, `t = "ABC"`)

`need` starts as `{A:1, B:1, C:1}`, `missing = 3`, `left = 0`, `best = (inf, 0, 0)`.
Indices: `0:A 1:D 2:O 3:B 4:E 5:C 6:O 7:D 8:E 9:B 10:A 11:N 12:C`

| `right` | `c` | `missing` before -> after tally | shrink actions (while `missing==0`) | `left` after | `best` after |
| ------- | --- | ---------------------------------- | -------------------------------------- | -------------- | ------------- |
| 0 | A | 3 -> 2 (`need[A]` 1->0) | — | 0 | `(inf,0,0)` |
| 1 | D | 2 -> 2 (`need[D]` 0->-1) | — | 0 | `(inf,0,0)` |
| 2 | O | 2 -> 2 (`need[O]` 0->-1) | — | 0 | `(inf,0,0)` |
| 3 | B | 2 -> 1 (`need[B]` 1->0) | — | 0 | `(inf,0,0)` |
| 4 | E | 1 -> 1 (`need[E]` 0->-1) | — | 0 | `(inf,0,0)` |
| 5 | C | 1 -> 0 (`need[C]` 1->0) | size=6<inf -> best=(6,0,6) `"ADOBEC"`; drop `s[0]='A'`: `need[A]` 0->1, >0 so `missing`=1, `left`=1; exit (missing!=0) | 1 | `(6,0,6)` |
| 6 | O | 1 -> 1 (`need[O]` -1->-2) | — | 1 | `(6,0,6)` |
| 7 | D | 1 -> 1 (`need[D]` -1->-2) | — | 1 | `(6,0,6)` |
| 8 | E | 1 -> 1 (`need[E]` -1->-2) | — | 1 | `(6,0,6)` |
| 9 | B | 1 -> 1 (`need[B]` 0->-1) | — | 1 | `(6,0,6)` |
| 10 | A | 1 -> 0 (`need[A]` 1->0) | size=10<6? no; drop `s[1]='D'`: `need[D]`-2->-1, not>0, `left`=2 -> missing still 0, loop again: size=9<6? no; drop `s[2]='O'`: `need[O]`-2->-1, not>0, `left`=3 -> loop: size=8<6? no; drop `s[3]='B'`: `need[B]`-1->0, not>0, `left`=4 -> loop: size=7<6? no; drop `s[4]='E'`: `need[E]`-2->-1, not>0, `left`=5 -> loop: size=6<6? no; drop `s[5]='C'`: `need[C]`0->1, >0 so `missing`=1, `left`=6; exit | 6 | `(6,0,6)` |
| 11 | N | 1 -> 1 (`need[N]` 0->-1) | — | 6 | `(6,0,6)` |
| 12 | C | 1 -> 0 (`need[C]` 1->0) | size=7<6? no; drop `s[6]='O'`: `need[O]`-1->0, not>0, `left`=7 -> loop: size=6<6? no; drop `s[7]='D'`: `need[D]`-1->0, not>0, `left`=8 -> loop: size=5<6? yes -> best=(5,8,13) `"EBANC"`; drop `s[8]='E'`: `need[E]`-1->0, not>0, `left`=9 -> loop: size=4<5? yes -> best=(4,9,13) `"BANC"`; drop `s[9]='B'`: `need[B]`0->1, >0 so `missing`=1, `left`=10; exit | 10 | `(4,9,13)` |

**Final:** `best = (4, 9, 13)` -> `s[9:13] = "BANC"` (matches the assert)

### Mental model

- `missing == 0` is a single O(1) test for "the window currently covers all of `t`" — no rescanning needed, because `need`/`missing` are kept in sync incrementally.
- Grow to find *any* covering window, then greedily shrink to find the *smallest* covering window ending at (or before) the current `right` — that's why the shrink is a `while`, not an `if`: keep squeezing until coverage would actually break.
- `need[c]` going negative is intentional and harmless — it just means "we're currently holding more copies of `c` than required," and giving one back (`+= 1`) during a shrink won't cross back above zero until the true surplus is used up.

### Common confusions

- **`need[c] > 0` guard before decrementing `missing`:** only characters that are *actually still required* should reduce `missing`; collecting an eighth `E` when only zero were needed must not touch `missing`.
- **Restoring counts on shrink:** `need[s[left]] += 1` must happen for every character dropped, needed or not — otherwise the counts drift and future coverage checks become wrong.
- **`missing += 1` only when `need[s[left]] > 0` after restoring:** this is the signal that the character just dropped was actually load-bearing for coverage; dropping a surplus character (`need` still `<= 0` after the `+= 1`) does not break coverage.
- **Shrinking before validity:** the `while missing == 0` guard is what prevents shrinking a window that doesn't yet cover `t` — shrinking only ever happens *after* full coverage is confirmed.

### Complexity

- **Time:** `O(n)` — amortized; `left` and `right` each traverse `s` at most once (plus `O(m)` to build `need`)
- **Space:** `O(m)` — `need` is bounded by the distinct characters in `t`

---

## Quick reference

| Function | Technique | Output on `("ADOBECODEBANC", "ABC")` | Time | Space |
| -------- | --------- | ---------------------------------------- | ---- | ----- |
| `min_window_brute` | Try every start, `all(...)` coverage check | `"BANC"` | `O(n^2 * m)` | `O(m)` |
| `min_window_slide` | Sliding window with `need`/`missing` counters | `"BANC"` | `O(n)` | `O(m)` |

## Patterns to remember

- **Grow-then-shrink window:** for "shortest stretch that contains X", expand until valid, then contract to minimal — the classic variable-size window.
- **A single "missing" counter:** track coverage in O(1) per step instead of re-scanning counts with `all(...)` every time.
- **Signal words:** "smallest/shortest substring containing all of ...", "minimum window".
- **Related problems:** Longest Substring Without Repeating Characters, Longest Repeating Character Replacement, Permutation in String.
- **Common pitfalls:** (1) recomputing coverage from scratch each step instead of maintaining `missing` incrementally; (2) shrinking before the window is valid (must gate on `missing == 0`); (3) not restoring counts (`need[s[left]] += 1`) when shrinking, which corrupts future coverage checks.
