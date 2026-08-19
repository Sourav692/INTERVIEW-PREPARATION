# 5. Longest Palindromic Substring — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 2_expand-around-center/longest_palindromic_substring.ipynb`
> **LeetCode:** https://leetcode.com/problems/longest-palindromic-substring/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Brute force | Check every substring; keep the longest one that reads the same reversed |
| Dynamic programming | `dp[i][j]` = is `s[i..j]` a palindrome? True when ends match and the inside (`dp[i+1][j-1]`) is already a palindrome |
| Expand around center | Every palindrome has a middle (a character, or a gap between two); grow outward from each of the ~2n centers while both sides match |
| Odd vs even centers | Odd-length palindromes center on a single index `i`; even-length ones center on the gap `(i, i+1)` |

**Canonical example** (from notebook's test list, first case):

```
"babad" -> "bab"   (or "aba" — both are valid length-3 answers)
```

Expected outputs (from notebook asserts — `assert len(a) == len(b) == len(c) == ln and ok(s,a) and ok(s,b) and ok(s,c)`, where `ok` only checks that the output is a palindrome of the correct length found in `s`):

| Input `s` | Expected length | `lps_brute` | `lps_dp` | `lps_expand` |
| --------- | ---------------- | ----------- | -------- | ------------- |
| `"babad"` | `3` | `"bab"` | `"bab"` | `"bab"` |
| `"cbbd"` | `2` | `"bb"` | `"bb"` | `"bb"` |
| `"a"` | `1` | `"a"` | `"a"` | `"a"` |
| `"ac"` | `1` | `"a"` | `"a"` | `"a"` |
| `"forgeeksskeegfor"` | `10` | (a 10-char palindrome) | (a 10-char palindrome) | (a 10-char palindrome) |

(All three implementations actually return `"bab"` on `"babad"`, verified by hand-tracing below — not just `"aba"`, which is also a valid answer under `ok`.)

---

## `lps_brute` — Check Every Substring

### What it does

Tries every possible substring `s[i:j+1]`, and whenever one is both longer than the current best *and* reads the same reversed, it becomes the new best.

### Code

```python
def lps_brute(s: str) -> str:
    best = ""
    n = len(s)
    for i in range(n):                     # start of the substring
        for j in range(i, n):              # end of the substring
            # Only bother checking if this substring is longer than our current best.
            if j - i + 1 > len(best) and s[i:j+1] == s[i:j+1][::-1]:
                best = s[i:j+1]            # it's a longer palindrome -> keep it
    return best
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `best = ""` | No palindrome found yet |
| `for i in range(n):` | Try every possible start index |
| `for j in range(i, n):` | Try every possible end index `>= i` |
| `if j - i + 1 > len(best) and ...` | Short-circuit: only reverse-check if this substring could beat the current best |
| `s[i:j+1] == s[i:j+1][::-1]` | Palindrome test — string equals its own reverse |
| `best = s[i:j+1]` | Longer palindrome found — replace the best |
| `return best` | Longest palindrome found across all substrings |

### Step-by-step trace (canonical example `"babad"`)

`s = "babad"` (indices `0=b, 1=a, 2=b, 3=a, 4=d`), `best = ""` initially.

| Step | `i` | `j` | Substring `s[i:j+1]` | Longer than `best`? | Palindrome? | `best` after |
| ---- | --- | --- | --------------------- | -------------------- | ----------- | ------------- |
| 1 | 0 | 0 | `"b"` | yes (1 > 0) | yes | `"b"` |
| 2 | 0 | 1 | `"ba"` | yes (2 > 1) | no (`"ba"` != `"ab"`) | `"b"` |
| 3 | 0 | 2 | `"bab"` | yes (3 > 1) | yes | `"bab"` |
| 4 | 0 | 3 | `"baba"` | yes (4 > 3) | no (`"baba"` != `"abab"`) | `"bab"` |
| 5 | 0 | 4 | `"babad"` | yes (5 > 3) | no | `"bab"` |
| 6 | 1 | 1 | `"a"` | no (1 > 3 false) | — skipped | `"bab"` |
| 7 | 1 | 2 | `"ab"` | no (2 > 3 false) | — skipped | `"bab"` |
| 8 | 1 | 3 | `"aba"` | no (3 > 3 false) | — skipped | `"bab"` |
| 9 | 1 | 4 | `"abad"` | yes (4 > 3) | no (`"abad"` != `"daba"`) | `"bab"` |
| 10 | 2 | 2 | `"b"` | no | — skipped | `"bab"` |
| 11 | 2 | 3 | `"ba"` | no | — skipped | `"bab"` |
| 12 | 2 | 4 | `"bad"` | no | — skipped | `"bab"` |
| 13 | 3 | 3 | `"a"` | no | — skipped | `"bab"` |
| 14 | 3 | 4 | `"ad"` | no | — skipped | `"bab"` |
| 15 | 4 | 4 | `"d"` | no | — skipped | `"bab"` |

**Final output:** `"bab"` — matches the notebook's expected length `3` and passes `ok(s, out)`.

### Mental model

- Generate all `O(n^2)` substrings; each palindrome check is `O(n)`, so total work is `O(n^3)`.
- The length guard (`j - i + 1 > len(best)`) is a cheap pruning trick — it skips the expensive reverse-check for substrings that couldn't possibly improve the answer, but it doesn't change the asymptotic complexity.

### Common confusions

- **This is a baseline, not a real solution:** `O(n^3)` is only here to show the naive approach before optimizing.
- **`s[i:j+1][::-1]` recomputes the reversal every time** — no memoization, so identical work is repeated across overlapping substrings.
- **Length guard order matters:** because `and` short-circuits, the cheap length check always runs before the expensive reverse-and-compare.

### Complexity

- **Time:** `O(n^3)` — `O(n^2)` substrings, each palindrome check costs up to `O(n)`
- **Space:** `O(1)` extra (not counting the substrings themselves, which Python creates as new strings)

---

## `lps_dp` — Dynamic Programming

### What it does

Builds a table `dp[i][j]` = "is `s[i..j]` a palindrome?" bottom-up, from spans of length 1 up to length `n`. A span is a palindrome if its two end characters match **and** the span strictly inside it (`dp[i+1][j-1]`) is already known to be a palindrome. Tracks the best `(start, maxlen)` seen while filling the table.

### Code

```python
def lps_dp(s: str) -> str:
    n = len(s)
    if n < 2:
        return s                           # empty or single char is already a palindrome
    dp = [[False] * n for _ in range(n)]   # dp[i][j] = is s[i..j] a palindrome?
    start, maxlen = 0, 1                   # best palindrome found so far (position + length)
    for i in range(n):
        dp[i][i] = True                    # every single character is a palindrome
    for length in range(2, n + 1):         # build up from length 2 to n
        for i in range(n - length + 1):    # left index of the window
            j = i + length - 1             # right index of the window
            # It's a palindrome if the ends match AND the inside is already a palindrome.
            if s[i] == s[j] and (length == 2 or dp[i+1][j-1]):
                dp[i][j] = True
                if length > maxlen:        # remember the longest one seen
                    start, maxlen = i, length
    return s[start:start + maxlen]
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if n < 2: return s` | Empty string or single char is trivially its own longest palindrome |
| `dp = [[False]*n for _ in range(n)]` | `n x n` table, all spans initially assumed non-palindromic |
| `start, maxlen = 0, 1` | Best answer defaults to the first single character |
| `for i in range(n): dp[i][i] = True` | Base case — every length-1 span is a palindrome |
| `for length in range(2, n+1):` | Grow window size from 2 up to `n` |
| `for i in range(n - length + 1): j = i + length - 1` | Slide the window of this `length` across the string |
| `if s[i] == s[j] and (length == 2 or dp[i+1][j-1]):` | Ends match, and either the window is length 2 (no "inside" to check) or the inside span is already a palindrome |
| `dp[i][j] = True` | Record this span as a palindrome |
| `if length > maxlen: start, maxlen = i, length` | New longest palindrome found — remember its position and length |
| `return s[start:start + maxlen]` | Slice out the best palindrome found |

### Step-by-step trace (canonical example `"babad"`)

`s = "babad"` (indices `0=b, 1=a, 2=b, 3=a, 4=d`), `n = 5`. Initial: `dp[i][i] = True` for all `i`; `start, maxlen = 0, 1`.

| `length` | `i` | `j` | `s[i]` vs `s[j]` | Inside check | `dp[i][j]` | `(start, maxlen)` after |
| -------- | --- | --- | ------------------ | -------------- | ---------- | ------------------------- |
| (base) | 0-4 | 0-4 | `dp[i][i]=True` (5 cells) | — | `True` | `(0, 1)` |
| 2 | 0 | 1 | `b` vs `a` — no | — | `False` | `(0, 1)` |
| 2 | 1 | 2 | `a` vs `b` — no | — | `False` | `(0, 1)` |
| 2 | 2 | 3 | `b` vs `a` — no | — | `False` | `(0, 1)` |
| 2 | 3 | 4 | `a` vs `d` — no | — | `False` | `(0, 1)` |
| 3 | 0 | 2 | `b` vs `b` — yes | `dp[1][1] = True` | `True` | `3 > 1` -> `(0, 3)` |
| 3 | 1 | 3 | `a` vs `a` — yes | `dp[2][2] = True` | `True` | `3 > 3` false -> `(0, 3)` |
| 3 | 2 | 4 | `b` vs `d` — no | — | `False` | `(0, 3)` |
| 4 | 0 | 3 | `b` vs `a` — no | — | `False` | `(0, 3)` |
| 4 | 1 | 4 | `a` vs `d` — no | — | `False` | `(0, 3)` |
| 5 | 0 | 4 | `b` vs `d` — no | — | `False` | `(0, 3)` |

**Final:** `start, maxlen = 0, 3` -> `s[0:3] = "bab"` — matches the expected length `3` and passes `ok(s, out)`.

### Mental model

- Build from the inside out: short spans first, so any span's "is the inside a palindrome" question is already answered by the time it's asked.
- The `length == 2` special case exists because a 2-character window has no "inside" span to look up (`dp[i+1][j-1]` would be `dp[j][i]`, an invalid/empty range).
- The 2-D table trades brute force's repeated re-checking for O(1) lookups of previously solved subproblems.

### Common confusions

- **`length == 2` short-circuit:** without it, `dp[i+1][j-1]` for a 2-char window would index `dp[i+1][i]`, which is nonsensical (the "inside" of a 2-char span is empty and vacuously true) — the `or` correctly treats that case as "no inside constraint."
- **Fill order matters:** the outer loop *must* go by increasing `length` — `dp[i+1][j-1]` (a shorter, inner span) must already be computed before `dp[i][j]` needs it.
- **`O(n^2)` space:** unlike expand-around-center's `O(1)`, the DP table itself costs `O(n^2)` memory, even though the runtime is the same order.

### Complexity

- **Time:** `O(n^2)` — the table has `O(n^2)` cells, each filled in `O(1)`
- **Space:** `O(n^2)` — the full `dp` table

---

## `lps_expand` — Expand Around Center

### What it does

For every index `i`, treats `i` as the center of an odd-length palindrome and the gap `(i, i+1)` as the center of an even-length palindrome. A helper `grow(l, r)` pushes `l` left and `r` right while `s[l] == s[r]`, then steps back to the last valid matching bounds. Whichever expansion (odd or even) produces a longer span than the current best replaces it.

### Code

```python
def lps_expand(s: str) -> str:
    if not s:
        return ""
    start, end = 0, 0                      # bounds of the best palindrome found
    def grow(l, r):                        # expand outward from a center while sides match
        while l >= 0 and r < len(s) and s[l] == s[r]:
            l -= 1; r += 1                 # step both ends outward
        return l + 1, r - 1                # step back to the last valid (matching) bounds
    for i in range(len(s)):
        l1, r1 = grow(i, i)                # odd-length palindrome centered on i
        l2, r2 = grow(i, i + 1)            # even-length palindrome centered between i and i+1
        if r1 - l1 > end - start:          # found a longer odd palindrome?
            start, end = l1, r1
        if r2 - l2 > end - start:          # found a longer even palindrome?
            start, end = l2, r2
    return s[start:end + 1]
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not s: return ""` | Empty string edge case |
| `start, end = 0, 0` | Best palindrome bounds default to `s[0:1]`, the first character |
| `def grow(l, r):` | Expands outward from center `(l, r)` while both sides match |
| `while l >= 0 and r < len(s) and s[l] == s[r]:` | Keep expanding as long as in-bounds and mirrored characters match |
| `l -= 1; r += 1` | Step both pointers outward one position |
| `return l + 1, r - 1` | The loop always overshoots by one step on the failing check — step back in to the last valid bounds |
| `for i in range(len(s)):` | Try every index as a potential center |
| `l1, r1 = grow(i, i)` | Odd-length center: single character `i` |
| `l2, r2 = grow(i, i + 1)` | Even-length center: the gap between `i` and `i+1` |
| `if r1 - l1 > end - start:` | Compare candidate span length (as `r - l`) against current best; update if longer |
| `if r2 - l2 > end - start:` | Same check for the even-length candidate |
| `return s[start:end + 1]` | Slice out the best palindrome found |

### Step-by-step trace (canonical example `"babad"`)

`s = "babad"` (indices `0=b, 1=a, 2=b, 3=a, 4=d`), `n = 5`. Initial `start, end = 0, 0`.

| `i` | Center | `grow` start `(l, r)` | Expansion steps (`l -= 1; r += 1` while `s[l]==s[r]`) | Final `(l, r)` returned | Span length (`r - l`) | New best? |
| --- | ------ | ----------------------- | -------------------------------------------------------- | -------------------------- | ---------------------- | --------- |
| 0 | odd `(0,0)` | `(0,0)` | `s[0]==s[0]` match -> `l=-1,r=1`; loop stops (`l<0`) | `(0, 0)` | `0` | no (`0 > 0` false) |
| 0 | even `(0,1)` | `(0,1)` | `s[0]='b'` vs `s[1]='a'` — no match, loop never runs | `(1, 0)` | `-1` | no |
| 1 | odd `(1,1)` | `(1,1)` | `s[1]==s[1]` match -> `l=0,r=2`; `s[0]='b'==s[2]='b'` match -> `l=-1,r=3`; loop stops (`l<0`) | `(0, 2)` | `2` | **yes** (`2 > 0`) -> `start,end=0,2` |
| 1 | even `(1,2)` | `(1,2)` | `s[1]='a'` vs `s[2]='b'` — no match, loop never runs | `(2, 1)` | `-1` | no |
| 2 | odd `(2,2)` | `(2,2)` | `s[2]==s[2]` match -> `l=1,r=3`; `s[1]='a'==s[3]='a'` match -> `l=0,r=4`; `s[0]='b'` vs `s[4]='d'` — no match, loop stops | `(1, 3)` | `2` | no (`2 > 2` false) |
| 2 | even `(2,3)` | `(2,3)` | `s[2]='b'` vs `s[3]='a'` — no match, loop never runs | `(3, 2)` | `-1` | no |
| 3 | odd `(3,3)` | `(3,3)` | `s[3]==s[3]` match -> `l=2,r=4`; `s[2]='b'` vs `s[4]='d'` — no match, loop stops | `(3, 3)` | `0` | no |
| 3 | even `(3,4)` | `(3,4)` | `s[3]='a'` vs `s[4]='d'` — no match, loop never runs | `(4, 3)` | `-1` | no |
| 4 | odd `(4,4)` | `(4,4)` | `s[4]==s[4]` match -> `l=3,r=5`; loop stops (`r >= len(s)`) | `(4, 4)` | `0` | no |
| 4 | even `(4,5)` | `(4,5)` | `r=5 >= len(s)`, loop never runs | `(5, 4)` | `-1` | no |

**Final:** `start, end = 0, 2` -> `s[0:3] = "bab"` — matches the expected length `3` and passes `ok(s, out)`.

### Mental model

- Every palindrome has a unique center; there are exactly `2n - 1` possible centers (`n` single-character, `n-1` gaps) — checking all of them covers every possible palindrome.
- `grow` always overshoots by exactly one step before its `while` condition fails, so `l + 1, r - 1` un-does that last bad step to land back on the true palindrome bounds.
- Comparing spans via `r - l` (not `r - l + 1`) is fine as long as it's used consistently — it's a relative-length comparison, not the true length.

### Common confusions

- **Odd vs even centers:** `grow(i, i)` only ever finds odd-length palindromes (equal `l`/`r` start). You must *also* call `grow(i, i+1)` for even-length ones — forgetting this silently misses answers like `"bb"` in `"cbbd"`.
- **Why `l + 1, r - 1` and not `l, r`:** the `while` loop's last iteration is the one that *failed* the match (or went out of bounds), so `l`/`r` at that point are one step too far outward.
- **Comparing `r - l` instead of `r - l + 1`:** both sides of every comparison use the same (off-by-one-consistent) formula, so the relative comparison is still correct — but it's easy to mistakenly "fix" this into an actual bug if refactored carelessly.

### Complexity

- **Time:** `O(n^2)` — up to `2n - 1` centers, each can expand up to `O(n)` steps
- **Space:** `O(1)` — only a few pointers, no extra data structure

---

## Quick reference

| Function | Technique | Output on `"babad"` | Time | Space |
| -------- | --------- | --------------------- | ---- | ----- |
| `lps_brute` | Check every substring | `"bab"` | `O(n^3)` | `O(1)` extra |
| `lps_dp` | DP table (`dp[i][j]` = is palindrome) | `"bab"` | `O(n^2)` | `O(n^2)` |
| `lps_expand` | Expand around center | `"bab"` | `O(n^2)` | `O(1)` |

## Patterns to remember

- **Expand around center template:** for each of the `2n - 1` centers (every index, and every gap between adjacent indices), grow two pointers outward while the mirrored characters match; track the best span seen.
- **DP-on-substrings template:** "is span `[i, j]` valid?" often reduces to "ends match AND the strictly-inside span `[i+1, j-1]` is already valid" — fill the table from short spans to long.
- **Signal words:** "longest palindromic substring", "longest symmetric substring", "palindrome around a center".
- **Related problems:** Palindromic Substrings, Longest Palindromic Subsequence, Valid Palindrome.
- **Common pitfalls:** (1) only checking odd-length centers and missing even-length palindromes; (2) off-by-one errors when converting `grow`'s overshot `(l, r)` back into valid bounds; (3) in the DP version, filling the table in the wrong order (must go shortest-span-first) so a needed sub-answer isn't ready yet.
