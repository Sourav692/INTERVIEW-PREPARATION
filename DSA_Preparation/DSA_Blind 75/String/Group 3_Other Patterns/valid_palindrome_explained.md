# 125. Valid Palindrome — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 3_Other Patterns/valid_palindrome.ipynb`
> **LeetCode:** https://leetcode.com/problems/valid-palindrome/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Clean-then-compare | Build a filtered, lowercased copy and check it equals its own reverse |
| Two pointers | Walk inward from both ends, skipping non-alphanumeric characters, comparing lowercased mirrors |
| Filtering | Only letters/digits count (`str.isalnum()`); case is ignored (`str.lower()`) |

**Canonical examples** (from notebook asserts):

| Input | Expected |
| ----- | -------- |
| `"A man, a plan, a canal: Panama"` | `True` |
| `"race a car"` | `False` |
| `" "` | `True` |
| `"0P"` | `False` |
| `"aba"` | `True` |

---

## `is_palindrome_clean` — Clean, Then Reverse

### What it does

Builds a new list containing only the lowercased alphanumeric characters of `s`, in order, then checks whether that list equals its own reverse.

### Code

```python
def is_palindrome_clean(s: str) -> bool:
    # Build a cleaned copy: keep only letters/digits, all lowercased.
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]        # a palindrome reads the same reversed
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `[c.lower() for c in s if c.isalnum()]` | List comprehension: keep only letters/digits, lowercase each one |
| `cleaned == cleaned[::-1]` | Compare the cleaned list to its reverse — equal means palindrome |

### Step-by-step trace (canonical example `"race a car"`)

**Build `cleaned`** (filter + lowercase each character):

| Char | `isalnum()`? | Included (lowercased)? |
| ---- | ------------ | ------------------------ |
| `'r'` | yes | `'r'` |
| `'a'` | yes | `'a'` |
| `'c'` | yes | `'c'` |
| `'e'` | yes | `'e'` |
| `' '` | no | skipped |
| `'a'` | yes | `'a'` |
| `' '` | no | skipped |
| `'c'` | yes | `'c'` |
| `'a'` | yes | `'a'` |
| `'r'` | yes | `'r'` |

`cleaned = ['r','a','c','e','a','c','a','r']`

**Compare to reverse:**

| Expression | Value |
| ---------- | ----- |
| `cleaned` | `['r','a','c','e','a','c','a','r']` |
| `cleaned[::-1]` | `['r','a','c','a','e','c','a','r']` |
| `cleaned == cleaned[::-1]` | index 2 differs (`'c'` vs `'c'` ok, index 3 `'e'` vs index 3 of reverse `'a'`) → `False` |

**Final result:** `False` ✓ matches the notebook's `exp=False` for `"race a car"`.

### Mental model

- Filtering first turns "ignore punctuation/case" into a solved, separate problem — the palindrome check itself becomes a trivial list-reverse comparison.
- Simple and very readable, at the cost of an extra `O(n)` array.

### Common confusions

- **`cleaned[::-1]` creates a new list** — this is why the approach is `O(n)` space, unlike the two-pointer version.
- **`isalnum()` already handles unicode letters/digits**, not just ASCII — broader than a hand-rolled regex might assume.

### Complexity

- **Time:** `O(n)` — one pass to filter/lower, one to reverse-compare
- **Space:** `O(n)` — the `cleaned` list (and its reversed copy)

---

## `is_palindrome_twoptr` — Two Pointers

### What it does

Keeps a left pointer `i` and right pointer `j` at the two ends of the string. Each step, it skips forward/backward past any non-alphanumeric characters, then compares the lowercased characters at `i` and `j`. Any mismatch means not a palindrome; if the pointers meet without a mismatch, it is one.

### Code

```python
def is_palindrome_twoptr(s: str) -> bool:
    i, j = 0, len(s) - 1                   # one pointer at each end
    while i < j:                           # walk them toward the middle
        while i < j and not s[i].isalnum():
            i += 1                         # skip non-letters/digits on the left
        while i < j and not s[j].isalnum():
            j -= 1                         # skip non-letters/digits on the right
        if s[i].lower() != s[j].lower():   # mirror characters must match (ignore case)
            return False                   # mismatch -> not a palindrome
        i += 1; j -= 1                     # both matched -> step inward
    return True                            # met in the middle with no mismatch
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `i, j = 0, len(s) - 1` | Start pointers at the first and last index |
| `while i < j:` | Outer loop — stop once pointers meet or cross |
| `while i < j and not s[i].isalnum(): i += 1` | Advance `i` past punctuation/spaces |
| `while i < j and not s[j].isalnum(): j -= 1` | Retreat `j` past punctuation/spaces |
| `if s[i].lower() != s[j].lower(): return False` | Mirror characters must match, case-insensitively |
| `i += 1; j -= 1` | Both matched — step both pointers inward |
| `return True` | Loop finished with no mismatch — it's a palindrome |

### Step-by-step trace (canonical example `"0P"`)

`s = "0P"`, `i=0`, `j=1` (`len(s)-1 = 1`).

| Iteration | `i` (start) | `j` (start) | Skip left? | Skip right? | `s[i].lower()` | `s[j].lower()` | Compare | Action |
| --------- | ----------- | ----------- | ---------- | ----------- | ---------------- | ---------------- | ------- | ------ |
| 1 | 0 | 1 | `'0'.isalnum()` True, no skip | `'P'.isalnum()` True, no skip | `'0'` | `'p'` | `'0' != 'p'` | mismatch → `return False` |

**Final result:** `False` ✓ matches the notebook's `exp=False` for `"0P"`.

Also trace the longer accepting case `"aba"` (`i=0, j=2`):

| Iteration | `i` (start) | `j` (start) | `s[i].lower()` | `s[j].lower()` | Compare | Action | `i,j` after |
| --------- | ----------- | ----------- | ---------------- | ---------------- | ------- | ------ | -------------- |
| 1 | 0 | 2 | `'a'` | `'a'` | equal | step inward | `i=1, j=1` |
| — | — | — | `while i < j` now `1 < 1` False | | | loop exits | |

**Final result:** `True` ✓ matches the notebook's `exp=True` for `"aba"`.

### Mental model

- Two pointers closing in from both ends is the natural way to check "same forwards and backwards" without materializing a cleaned copy.
- The two inner `while` loops act as "smart skips" — they only ever move a pointer past junk characters, never past each other (guarded by `i < j`).
- As soon as one mismatch is found, the function can bail immediately — no need to finish scanning.

### Common confusions

- **Forgetting `i < j` inside the inner skip loops:** without it, `i` or `j` could run off the string or the pointers could cross while skipping trailing punctuation (e.g., a string ending in all punctuation).
- **Comparing before lowering:** `s[i] != s[j]` without `.lower()` would incorrectly reject case-differing mirrors like `'A'` vs `'a'`.
- **Single space `" "`:** both pointers point at the same non-alphanumeric character; the inner skip loops can't advance past each other (`i < j` becomes false first), so the outer loop never runs a comparison and it correctly returns `True` vacuously.

### Complexity

- **Time:** `O(n)` — each character is visited at most once total across both pointers
- **Space:** `O(1)` — only two integer pointers, no extra copy

---

## Quick reference

| Function | Technique | Output on `"race a car"` | Output on `"0P"` | Time | Space |
| -------- | --------- | --------------------------- | -------------------- | ---- | ----- |
| `is_palindrome_clean` | Filter + lowercase, compare to reverse | `False` | `False` | `O(n)` | `O(n)` |
| `is_palindrome_twoptr` | Two pointers, skip + compare inward | `False` | `False` | `O(n)` | `O(1)` |

## Patterns to remember

- **Two pointers from both ends:** the go-to for "same forwards and backwards" and for comparing mirror positions with `O(1)` memory.
- **Filter while you scan:** skip unwanted characters in place instead of building a new string.
- **Signal words:** "palindrome", "reads the same reversed", "mirror".
- **Related problems:** Valid Palindrome II, Reverse String, Two Sum II, Container With Most Water.
- **Common pitfalls:** (1) forgetting to lowercase; (2) not skipping punctuation on *both* sides; (3) letting pointers cross while skipping.
