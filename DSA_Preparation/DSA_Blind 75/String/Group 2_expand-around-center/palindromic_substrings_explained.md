# 647. Palindromic Substrings — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 2_expand-around-center/palindromic_substrings.ipynb`
> **LeetCode:** https://leetcode.com/problems/palindromic-substrings/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Brute force | Check every substring (`i`, `j` pair); count each one that reads the same reversed |
| Expand around center | Same "grow outward from a center" engine as Longest Palindromic Substring, but instead of tracking the longest span, every successful expansion step is counted as one more palindrome |
| Odd vs even centers | Odd-length palindromes center on a single index `i`; even-length ones center on the gap `(i, i+1)` — both must be summed |

**Canonical example** (from notebook's Problem section and test list):

```
"abc" -> 3    ("a","b","c")
"aaa" -> 6    ("a","a","a","aa","aa","aaa")
```

Expected outputs (from notebook asserts — `assert a == b == exp`):

| Input `s` | Expected count | `count_pal_brute` | `count_pal_expand` |
| --------- | ---------------- | -------------------- | ---------------------- |
| `"abc"` | `3` | `3` | `3` |
| `"aaa"` | `6` | `6` | `6` |
| `"a"` | `1` | `1` | `1` |
| `"aba"` | `4` | `4` | `4` |
| `""` | `0` | `0` | `0` |

`"aaa"` is used below as the canonical trace example since it exercises multi-step expansions on both functions.

---

## `count_pal_brute` — Check Every Substring

### What it does

Tries every possible substring `s[i:j+1]` and increments a running total each time that substring reads the same reversed.

### Code

```python
def count_pal_brute(s: str) -> int:
    n = len(s)
    total = 0
    for i in range(n):                     # substring start
        for j in range(i, n):              # substring end
            sub = s[i:j+1]
            if sub == sub[::-1]:           # reads the same reversed -> a palindrome
                total += 1
    return total
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `total = 0` | Running palindrome count |
| `for i in range(n):` | Try every possible substring start index |
| `for j in range(i, n):` | Try every possible substring end index `>= i` |
| `sub = s[i:j+1]` | Extract the candidate substring |
| `if sub == sub[::-1]:` | Palindrome test — string equals its own reverse |
| `total += 1` | Count this substring as one palindrome |
| `return total` | Total palindromic substrings found |

### Step-by-step trace (canonical example `"aaa"`)

`s = "aaa"` (indices `0=a, 1=a, 2=a`), `n = 3`, `total = 0`.

| Step | `i` | `j` | Substring `s[i:j+1]` | Palindrome? | `total` after |
| ---- | --- | --- | ----------------------- | ----------- | --------------- |
| 1 | 0 | 0 | `"a"` | yes | `1` |
| 2 | 0 | 1 | `"aa"` | yes | `2` |
| 3 | 0 | 2 | `"aaa"` | yes | `3` |
| 4 | 1 | 1 | `"a"` | yes | `4` |
| 5 | 1 | 2 | `"aa"` | yes | `5` |
| 6 | 2 | 2 | `"a"` | yes | `6` |

**Final output:** `6` — matches the notebook's expected count for `"aaa"`.

### Mental model

- Every substring of an all-same-character string is a palindrome, which is exactly why `"a"*n` is used as the benchmark's worst case — no early exits, every check runs to completion.
- Counting is simpler than the "longest" version: there's no need to track start/length, just a running total.

### Common confusions

- **`O(n^3)` cost hides in the reverse:** `sub[::-1]` builds a new string and compares it — an `O(k)` operation for a substring of length `k`, done for each of the `O(n^2)` substrings.
- **No pruning here:** unlike `lps_brute` (Longest Palindromic Substring), there's no "only check if longer than best" shortcut — every substring must be checked because it might contribute to the count regardless of length.

### Complexity

- **Time:** `O(n^3)` — `O(n^2)` substrings, each palindrome check costs up to `O(n)`
- **Space:** `O(1)` extra (aside from the substrings Python allocates during slicing/reversal)

---

## `count_pal_expand` — Expand Around Center

### What it does

Reuses the expand-around-center idea, but instead of remembering the longest span, `grow(l, r)` counts how many successful outward steps it takes before the mirrored characters stop matching — each successful step *is* one more palindrome centered at `(l, r)`. Sums this over both the odd center (`i, i`) and even center (`i, i+1`) for every index `i`.

### Code

```python
def count_pal_expand(s: str) -> int:
    n = len(s)
    def grow(l, r):                        # count palindromes centered at (l, r)
        cnt = 0
        while l >= 0 and r < n and s[l] == s[r]:
            cnt += 1                        # each successful expansion is one more palindrome
            l -= 1; r += 1                  # widen outward
        return cnt
    total = 0
    for i in range(n):
        total += grow(i, i)                 # odd-length palindromes centered on i
        total += grow(i, i + 1)             # even-length palindromes centered between i, i+1
    return total
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `def grow(l, r):` | Counts palindromes expanding outward from center `(l, r)` |
| `cnt = 0` | No palindromes counted for this center yet |
| `while l >= 0 and r < n and s[l] == s[r]:` | Keep expanding as long as in-bounds and mirrored characters match |
| `cnt += 1` | Each successful match is exactly one more palindrome (the current `s[l..r]`) |
| `l -= 1; r += 1` | Widen the window one step further out |
| `return cnt` | Total palindromes found at this one center |
| `for i in range(n):` | Try every index as a potential center |
| `total += grow(i, i)` | Add odd-length palindromes centered on `i` |
| `total += grow(i, i + 1)` | Add even-length palindromes centered on the gap between `i` and `i+1` |
| `return total` | Grand total of palindromic substrings |

### Step-by-step trace (canonical example `"aaa"`)

`s = "aaa"` (indices `0=a, 1=a, 2=a`), `n = 3`, `total = 0`.

| `i` | Center | `grow` expansion (`l`, `r`, match?, `cnt` after) | Final `cnt` returned | `total` after |
| --- | ------ | --------------------------------------------------- | ----------------------- | --------------- |
| 0 | odd `(0,0)` | `(0,0)`: `s[0]==s[0]` match, `cnt=1`, `l=-1,r=1`; loop stops (`l<0`) | `1` | `0 + 1 = 1` |
| 0 | even `(0,1)` | `(0,1)`: `s[0]='a'==s[1]='a'` match, `cnt=1`, `l=-1,r=2`; loop stops (`l<0`) | `1` | `1 + 1 = 2` |
| 1 | odd `(1,1)` | `(1,1)`: `s[1]==s[1]` match, `cnt=1`, `l=0,r=2`; `s[0]='a'==s[2]='a'` match, `cnt=2`, `l=-1,r=3`; loop stops (`l<0`) | `2` | `2 + 2 = 4` |
| 1 | even `(1,2)` | `(1,2)`: `s[1]='a'==s[2]='a'` match, `cnt=1`, `l=0,r=3`; loop stops (`r >= n`) | `1` | `4 + 1 = 5` |
| 2 | odd `(2,2)` | `(2,2)`: `s[2]==s[2]` match, `cnt=1`, `l=1,r=3`; loop stops (`r >= n`) | `1` | `5 + 1 = 6` |
| 2 | even `(2,3)` | `(2,3)`: `r=3 >= n=3`, loop never runs | `0` | `6 + 0 = 6` |

**Final output:** `6` — matches the notebook's expected count for `"aaa"`.

### Mental model

- Counting is a natural by-product of expansion: every time `grow`'s `while` body executes once, that's exactly one valid palindrome (the substring `s[l..r]` at that moment) — no separate bookkeeping needed beyond the increment.
- Same `2n - 1` centers as the "longest palindrome" version, but here every successful step contributes to the answer instead of only the final (longest) one.
- On an all-same-character string, longer centers accumulate more counts (e.g., the middle odd center `(1,1)` contributes `2`, more than the edge centers), which is why palindrome-dense strings like `"aaa"` or `"a"*n` are used to stress-test this function.

### Common confusions

- **Counting steps vs. counting the final span:** this is the key difference from `lps_expand` (Longest Palindromic Substring) — there, only the *final* bounds after the loop matter; here, *every* iteration of the `while` loop itself is a countable palindrome.
- **Forgetting even-length centers:** omitting `grow(i, i+1)` would undercount — e.g., on `"aaa"` it would miss the two length-2 palindromes (`"aa"`, `"aa"`), giving `4` instead of `6`.
- **Double-counting single characters:** each character is counted exactly once via its own odd center (`grow(i, i)`'s first successful step) — the even centers only ever produce length-2-or-more palindromes, so there's no overlap between odd and even center counts.

### Complexity

- **Time:** `O(n^2)` — up to `2n - 1` centers, each can expand up to `O(n)` steps
- **Space:** `O(1)` — only a running counter and a couple of pointers

---

## Quick reference

| Function | Technique | Output on `"aaa"` | Time | Space |
| -------- | --------- | -------------------- | ---- | ----- |
| `count_pal_brute` | Check every substring | `6` | `O(n^3)` | `O(1)` extra |
| `count_pal_expand` | Expand around center (count each successful step) | `6` | `O(n^2)` | `O(1)` |

## Patterns to remember

- **Counting via expansion:** the same "expand around center" engine that finds the *longest* palindrome (see Longest Palindromic Substring) also *counts them all* — just tally each successful `while`-loop step instead of tracking the best final span.
- **`2n - 1` centers rule:** always sum both `grow(i, i)` (odd) and `grow(i, i+1)` (even) for every index `i` to cover all palindrome lengths.
- **Signal words:** "how many palindromic substrings", "count symmetric pieces", "number of palindromes".
- **Related problems:** Longest Palindromic Substring, Palindromic Subsequences.
- **Common pitfalls:** (1) forgetting even-length centers and undercounting; (2) double-counting single characters (doesn't actually happen here since odd/even centers never overlap, but easy to worry about/miscode); (3) reaching for `O(n^3)` brute force on large inputs when `O(n^2)` expand-around-center solves the same problem.
