# 242. Valid Anagram — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 3_Other Patterns/valid_anagram.ipynb`
> **LeetCode:** https://leetcode.com/problems/valid-anagram/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Sorting | Anagrams become identical strings once both are sorted |
| Hash map / counting | Compare "letter recipes" — same letters, same counts, regardless of order |
| Early reject | Different lengths can never be anagrams — check that first |

**Canonical examples** (from notebook asserts):

| `s` | `t` | Expected |
| --- | --- | -------- |
| `"anagram"` | `"nagaram"` | `True` |
| `"rat"` | `"car"` | `False` |
| `"a"` | `"ab"` | `False` |
| `""` | `""` | `True` |

---

## `is_anagram_sort` — Sort Both

### What it does

Sorts both strings' characters and compares the results. If `s` and `t` are anagrams, sorting lines up their letters identically, so the sorted forms are equal.

### Code

```python
def is_anagram_sort(s: str, t: str) -> bool:
    # Two words are anagrams if they contain the exact same letters.
    # Sorting each word lines its letters up in the same order, so
    # anagrams become identical strings we can compare directly.
    return sorted(s) == sorted(t)          # e.g. sorted("nag") == sorted("gan")
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `sorted(s)` | Returns a list of `s`'s characters in sorted order |
| `sorted(t)` | Same for `t` |
| `sorted(s) == sorted(t)` | Two words are anagrams iff their sorted character lists are identical |

### Step-by-step trace (canonical example `s="anagram"`, `t="nagaram"`)

| Step | Expression | Result |
| ---- | ---------- | ------ |
| 1 | `sorted("anagram")` | `['a','a','a','g','m','n','r']` |
| 2 | `sorted("nagaram")` | `['a','a','a','g','m','n','r']` |
| 3 | Compare lists element-wise | all equal |

**Final result:** `True` ✓ matches the notebook's `exp=True`.

Also trace the rejecting case `s="rat"`, `t="car"`:

| Step | Expression | Result |
| ---- | ---------- | ------ |
| 1 | `sorted("rat")` | `['a','r','t']` |
| 2 | `sorted("car")` | `['a','c','r']` |
| 3 | Compare lists element-wise | index 1: `'r' != 'c'` — not equal |

**Final result:** `False` ✓ matches the notebook's `exp=False`.

### Mental model

- Sorting is a "canonicalization" trick: any two multisets of characters map to the same sorted sequence.
- Simple and correct, but pays an `O(n log n)` sort cost per string when a linear count comparison would do.

### Common confusions

- **This does not check length explicitly** — but sorted lists of different lengths are automatically unequal, so it's implicitly handled.
- **Case/whitespace sensitivity:** `sorted()` treats `'A'` and `'a'` as different characters — the notebook's tests are all lowercase, so this isn't exercised, but it's a real-world trap.

### Complexity

- **Time:** `O(n log n)` — dominated by the two sorts (`n` = string length)
- **Space:** `O(n)` — `sorted()` returns new lists for both strings

---

## `is_anagram_count` — Count Letters

### What it does

Rejects immediately if lengths differ. Otherwise, tallies every letter of `s` into a count dict, then "spends" one occurrence per letter of `t` — if `t` needs a letter `s` doesn't have, or counts don't fully cancel to zero, they aren't anagrams.

### Code

```python
def is_anagram_count(s: str, t: str) -> bool:
    # Quick reject: different lengths can never be anagrams.
    if len(s) != len(t):
        return False
    count = {}                             # letter -> how many times it appears in s
    for c in s:                            # step 1: tally every letter of the first word
        count[c] = count.get(c, 0) + 1     # add one to this letter's running total
    for c in t:                            # step 2: "spend" one of each letter for word t
        if c not in count:                 # t needs a letter that s never had -> not anagram
            return False
        count[c] -= 1                      # use up one occurrence of this letter
        if count[c] == 0:                  # exhausted this letter -> drop it from the map
            del count[c]
    return len(count) == 0                 # anagram only if every letter was used up exactly
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if len(s) != len(t): return False` | Fast fail — different lengths can never be anagrams |
| `count = {}` | Letter → running count, built from `s` |
| `for c in s: count[c] = count.get(c,0)+1` | Tally every letter of `s` |
| `for c in t:` | Second pass, over `t`, "spending" the tally |
| `if c not in count: return False` | `t` has a letter `s` never had — immediate fail |
| `count[c] -= 1` | Use up one occurrence of `c` |
| `if count[c] == 0: del count[c]` | Once a letter's count hits zero, remove it (so a leftover key means "unbalanced") |
| `return len(count) == 0` | True only if every letter tallied from `s` was fully spent by `t` |

### Step-by-step trace (canonical example `s="rat"`, `t="car"`)

`len("rat") == len("car") == 3`, so the length check passes.

**Pass 1 — build `count` from `s = "rat"`:**

| c | `count` after |
| - | -------------- |
| `'r'` | `{'r': 1}` |
| `'a'` | `{'r': 1, 'a': 1}` |
| `'t'` | `{'r': 1, 'a': 1, 't': 1}` |

**Pass 2 — spend using `t = "car"`:**

| c | Check | Action | `count` after |
| - | ----- | ------ | -------------- |
| `'c'` | `'c' not in count` → True | `return False` immediately | — |

**Final result:** `False` ✓ matches the notebook's `exp=False` for `("rat","car")`.

Also trace the accepting case `s="anagram"`, `t="nagaram"` (both length 7, so the length check passes):

**Pass 1 — build `count` from `"anagram"`:**

| c | `count` after |
| - | -------------- |
| `'a'` | `{'a':1}` |
| `'n'` | `{'a':1,'n':1}` |
| `'a'` | `{'a':2,'n':1}` |
| `'g'` | `{'a':2,'n':1,'g':1}` |
| `'r'` | `{'a':2,'n':1,'g':1,'r':1}` |
| `'a'` | `{'a':3,'n':1,'g':1,'r':1}` |
| `'m'` | `{'a':3,'n':1,'g':1,'r':1,'m':1}` |

**Pass 2 — spend using `"nagaram"`:**

| c | `count[c]` before | after decrement | deleted if 0? | `count` after |
| - | ------------------ | ----------------- | --------------- | -------------- |
| `'n'` | 1 | 0 | yes | `{'a':3,'g':1,'r':1,'m':1}` |
| `'a'` | 3 | 2 | no | `{'a':2,'g':1,'r':1,'m':1}` |
| `'g'` | 1 | 0 | yes | `{'a':2,'r':1,'m':1}` |
| `'a'` | 2 | 1 | no | `{'a':1,'r':1,'m':1}` |
| `'r'` | 1 | 0 | yes | `{'a':1,'m':1}` |
| `'a'` | 1 | 0 | yes | `{'m':1}` |
| `'m'` | 1 | 0 | yes | `{}` |

`count` is empty after pass 2. **Final result:** `len(count) == 0` → `True` ✓ matches the notebook's `exp=True`.

### Mental model

- Think of `count` as a "budget" built from `s`; `t` must spend exactly that budget, no more, no less.
- Deleting a key when it hits zero turns "is everything balanced?" into a single `len(count) == 0` check instead of scanning all values.
- The length check upfront prevents wasted work and also guarantees a clean pass/fail even without it (extra letters in `t` are caught by `c not in count`, but a `t` *shorter* than `s` needs the length guard to be safely caught).

### Common confusions

- **Why check length first if the algorithm "would still work"?** Without it, a `t` that's a strict prefix of `s`'s letters could leave `count` non-empty but the logic still works correctly by falling through to `len(count)==0` — the explicit check is really an optimization / fast-fail, not strictly required for correctness given the final `len(count)==0` check, but it avoids scanning `t` needlessly when lengths already prove mismatch.
- **`count.get(c, 0)` vs `count[c]`:** using plain indexing without `.get` would `KeyError` on a letter's first appearance.
- **Assuming lowercase-only input:** the counting approach works for any character (unicode, spaces, mixed case) as-is — it's the `sorted()` approach that risks confusing case if not normalized, and neither approach here does `.lower()` (input is already lowercase in the notebook's tests).

### Complexity

- **Time:** `O(n)` — two linear passes, dict operations are `O(1)` average
- **Space:** `O(1)` for lowercase-English-letter inputs (at most 26 distinct keys); `O(k)` in general for `k` distinct characters

---

## Quick reference

| Function | Technique | Output on `("anagram","nagaram")` | Output on `("rat","car")` | Time | Space |
| -------- | --------- | ------------------------------------ | ---------------------------- | ---- | ----- |
| `is_anagram_sort` | Sort and compare | `True` | `False` | `O(n log n)` | `O(n)` |
| `is_anagram_count` | Letter-count hash map | `True` | `False` | `O(n)` | `O(1)` (fixed alphabet) |

## Patterns to remember

- **Compare recipes, not items:** counting letters (a frequency map) reduces "are these the same multiset?" to comparing counts — `O(n)`.
- **Sort to normalize:** sorting maps every anagram to one canonical form; slower but tiny to write.
- **Signal words:** "same letters rearranged", "permutation of", "same characters".
- **Related problems:** Group Anagrams, Valid Parentheses (matching), Find All Anagrams in a String.
- **Common pitfalls:** (1) forgetting the length check; (2) assuming only lowercase when input may have unicode/spaces.
