# 49. Group Anagrams — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 3_Other Patterns/group_anagrams.ipynb`
> **LeetCode:** https://leetcode.com/problems/group-anagrams/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Hash map of key → list | Bucket words by a canonical "fingerprint" they share with their anagrams |
| Sorted-string key | Sort each word's letters; anagrams sort to the identical string |
| Letter-count key | A 26-length count tuple; anagrams have identical counts — no sorting needed |

**Canonical example** (from notebook):

```
["eat","tea","tan","ate","nat","bat"]
-> [["eat","tea","ate"], ["tan","nat"], ["bat"]]  (any order)
```

Expected outputs (from notebook asserts):

| Input | Expected group count |
| ----- | ---------------------- |
| `["eat","tea","tan","ate","nat","bat"]` | `3` |
| `[""]` | `1` |
| `["a"]` | `1` |

---

## `group_sort` — Sorted-String Key

### What it does

For each word, computes its sorted-letter form (e.g. `"eat"` → `"aet"`) and uses that as a dict key. All anagrams sort to the same string, so they land in the same bucket. Returns the buckets as a list of lists.

### Code

```python
def group_sort(strs: List[str]) -> List[List[str]]:
    groups = defaultdict(list)             # fingerprint -> list of words with that fingerprint
    for w in strs:
        key = "".join(sorted(w))           # sorted letters: all anagrams share this key
        groups[key].append(w)              # drop the word into its bucket
    return list(groups.values())           # each bucket is one anagram group
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `groups = defaultdict(list)` | Missing keys auto-create an empty list — no manual `if key not in groups` check needed |
| `for w in strs:` | Process each word once |
| `key = "".join(sorted(w))` | Sort `w`'s characters and rejoin into a string — the canonical fingerprint |
| `groups[key].append(w)` | File `w` into its fingerprint's bucket |
| `return list(groups.values())` | Discard the keys; return just the grouped word-lists |

### Step-by-step trace (canonical example `["eat","tea","tan","ate","nat","bat"]`)

| Word `w` | `sorted(w)` | `key` | `groups` after this word |
| -------- | ------------ | ----- | --------------------------- |
| `"eat"` | `['a','e','t']` | `"aet"` | `{"aet": ["eat"]}` |
| `"tea"` | `['a','e','t']` | `"aet"` | `{"aet": ["eat","tea"]}` |
| `"tan"` | `['a','n','t']` | `"ant"` | `{"aet": ["eat","tea"], "ant": ["tan"]}` |
| `"ate"` | `['a','e','t']` | `"aet"` | `{"aet": ["eat","tea","ate"], "ant": ["tan"]}` |
| `"nat"` | `['a','n','t']` | `"ant"` | `{"aet": ["eat","tea","ate"], "ant": ["tan","nat"]}` |
| `"bat"` | `['a','b','t']` | `"abt"` | `{"aet": ["eat","tea","ate"], "ant": ["tan","nat"], "abt": ["bat"]}` |

**Final output:** `list(groups.values())` = `[["eat","tea","ate"], ["tan","nat"], ["bat"]]` — **3 groups** ✓ matches the notebook's expected `ngroups=3`.

### Mental model

- Sorting is the classic way to make "same multiset of letters" become "identical value" — a natural dict key.
- Using `defaultdict(list)` removes the boilerplate of checking key existence before appending.
- Dict iteration/insertion order (Python 3.7+) is why the groups come back in first-seen order.

### Common confusions

- **Sorting cost:** each word of length `k` costs `O(k log k)` to sort — dominates the overall runtime for long words.
- **`"".join(sorted(w))` vs `sorted(w)`:** `sorted(w)` alone returns a list, which is unhashable — must join it back into a string to use as a dict key.

### Complexity

- **Time:** `O(n · k log k)` — for `n` words of length `k`, each sort costs `O(k log k)`
- **Space:** `O(n · k)` — storing all words (plus their keys) in the buckets

---

## `group_count` — Letter-Count Key

### What it does

For each word, builds a 26-length array counting occurrences of each lowercase letter (`a`..`z`), converts it to a tuple (hashable), and uses that as the dict key. Anagrams produce identical count tuples without any sorting.

### Code

```python
def group_count(strs: List[str]) -> List[List[str]]:
    groups = defaultdict(list)             # fingerprint -> list of words
    for w in strs:
        counts = [0] * 26                  # how many of each letter a..z this word has
        for c in w:
            counts[ord(c) - ord("a")] += 1 # tally the letter (a=0, b=1, ...)
        groups[tuple(counts)].append(w)    # a tuple is hashable, so it works as a dict key
    return list(groups.values())
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `groups = defaultdict(list)` | Same auto-vivifying bucket map as `group_sort` |
| `counts = [0] * 26` | Fresh 26-slot counter for this word, one slot per lowercase letter |
| `for c in w: counts[ord(c) - ord("a")] += 1` | Map each character to its `a=0..z=25` index and increment |
| `groups[tuple(counts)].append(w)` | Convert the list to a tuple (lists aren't hashable) and use it as the key |
| `return list(groups.values())` | Return just the grouped word-lists |

### Step-by-step trace (canonical example `["eat","tea","tan","ate","nat","bat"]`)

For brevity, each `counts` tuple is shown only at the non-zero letter positions (`a,b,e,n,t` are the letters in play).

| Word `w` | Non-zero counts (a,b,e,n,t positions) | `key` (as tuple, sparse view) | `groups` bucket touched |
| -------- | ---------------------------------------- | -------------------------------- | -------------------------- |
| `"eat"` | a=1, e=1, t=1 | `(...,a:1,...,e:1,...,t:1,...)` | new bucket `K1` → `["eat"]` |
| `"tea"` | a=1, e=1, t=1 | same as `"eat"`'s key → `K1` | `K1` → `["eat","tea"]` |
| `"tan"` | a=1, n=1, t=1 | new bucket `K2` → `["tan"]` |
| `"ate"` | a=1, e=1, t=1 | same as `K1` | `K1` → `["eat","tea","ate"]` |
| `"nat"` | a=1, n=1, t=1 | same as `K2` | `K2` → `["tan","nat"]` |
| `"bat"` | a=1, b=1, t=1 | new bucket `K3` → `["bat"]` |

`K1` corresponds to `{a:1,e:1,t:1}` (shared by `"eat"`,`"tea"`,`"ate"` since they're all permutations of the same 3 letters); `K2` to `{a:1,n:1,t:1}` (`"tan"`,`"nat"`); `K3` to `{a:1,b:1,t:1}` (`"bat"` alone).

**Final output:** `list(groups.values())` = `[["eat","tea","ate"], ["tan","nat"], ["bat"]]` — **3 groups** ✓ matches the notebook's expected `ngroups=3`, and identical grouping to `group_sort` (the notebook's correctness check compares `key(g1) == key(g2)` where both normalize to sorted-sorted-groups for comparison).

### Mental model

- A fixed-size count array is a fingerprint that avoids sorting entirely — just tally and compare.
- Tuples are used (not lists) purely because dict keys must be hashable; lists aren't.
- This is the "counting beats sorting" idea: turn an `O(k log k)` step into an `O(k)` step by using structure (fixed alphabet) instead of a general-purpose sort.

### Common confusions

- **`[0]*26` assumes lowercase a-z only:** unicode or uppercase input would need a bigger/different scheme (e.g. a `Counter` or `dict` key) — the notebook's own "Common pitfalls" flags this.
- **Using a `list` as a dict key directly** would raise `TypeError: unhashable type: 'list'` — must convert to `tuple(counts)` first.
- **Same grouping, different key representation:** `group_sort` and `group_count` produce the *same* partition of words, just keyed differently (string vs tuple) — this is exactly what the notebook's correctness check verifies.

### Complexity

- **Time:** `O(n · k)` — for `n` words of length `k`, counting is linear, no sort
- **Space:** `O(n · k)` — storing all words in buckets, plus `O(26)` per word for its count array

---

## Quick reference

| Function | Technique | Output on `["eat","tea","tan","ate","nat","bat"]` | Time | Space |
| -------- | --------- | ----------------------------------------------------- | ---- | ----- |
| `group_sort` | Sorted-string key | `[["eat","tea","ate"],["tan","nat"],["bat"]]` (3 groups) | `O(n·k log k)` | `O(n·k)` |
| `group_count` | 26-letter count-tuple key | `[["eat","tea","ate"],["tan","nat"],["bat"]]` (3 groups) | `O(n·k)` | `O(n·k)` |

## Patterns to remember

- **Canonical key + hash map to group:** turn each item into a form its "siblings" share, then bucket by that form.
- **Counting beats sorting:** a count fingerprint avoids the log factor.
- **Signal words:** "group / bucket things that are equivalent under some transformation".
- **Related problems:** Valid Anagram, Find All Anagrams, Group Shifted Strings.
- **Common pitfalls:** (1) using a `list` as a dict key (not hashable — use a `tuple`); (2) assuming input is lowercase-only.
