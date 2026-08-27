# 20. Valid Parentheses — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/String/Group 3_Other Patterns/valid_parentheses.ipynb`
> **LeetCode:** https://leetcode.com/problems/valid-parentheses/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Stack | "Last in, first out" — the most-recent opener must be the first to close |
| Repeated-removal | Brute-force: keep deleting adjacent matching pairs until nothing changes |
| Matching map | `{")": "(", "]": "[", "}": "{"}` maps each closer to the opener it requires |

**Canonical examples** (from notebook asserts):

| Input | Expected |
| ----- | -------- |
| `"()[]{}"` | `True` |
| `"(]"` | `False` |
| `"([)]"` | `False` |
| `"{[]}"` | `True` |
| `"("` | `False` |
| `""` | `True` |

---

## `valid_paren_brute` — Repeatedly Remove Pairs

### What it does

Keeps stripping the simple adjacent pairs `"()"`, `"[]"`, `"{}"` out of the string, pass after pass, until a full pass makes no change. The string is valid only if it has been completely whittled down to empty.

### Code

```python
def valid_paren_brute(s: str) -> bool:
    prev = None
    # Keep deleting adjacent matching pairs until the string stops changing.
    while prev != s:                       # loop again only if last pass removed something
        prev = s                           # remember the string before this cleanup pass
        s = s.replace("()", "").replace("[]", "").replace("{}", "")  # strip simple pairs
    return s == ""                         # valid only if everything cancelled out
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `prev = None` | Sentinel so the loop always runs at least once |
| `while prev != s:` | Keep cleaning up as long as the last pass changed the string |
| `prev = s` | Snapshot before this pass, to detect "no more change" next iteration |
| `s.replace("()", "").replace("[]", "").replace("{}", "")` | Remove every adjacent simple pair of each type in one pass |
| `return s == ""` | Valid only if everything eventually cancelled out to nothing |

### Step-by-step trace (canonical example `"{[]}"`)

Note: the three `.replace` calls are **chained within one pass** (`prev = s` is snapshotted first, then all three replaces run in sequence before the `while` re-checks).

| Pass | `prev` (snapshot) | after `.replace("()","")` | after `.replace("[]","")` | after `.replace("{}","")` | `s` at end of pass | Loop condition (`prev != s`) |
| ---- | ------------------ | ---------------------------- | --------------------------- | --------------------------- | -------------------- | -------------------------------- |
| 1 | `"{[]}"` | `"{[]}"` (no `"()"` substring) | `"{}"` (removed inner `[]`) | `""` (removed `{}`) | `""` | `"{[]}" != ""` → continue |
| 2 | `""` | `""` | `""` | `""` | `""` | `"" != ""` → false, loop exits |

**Final result:** `s == ""` → `True` ✓ matches the notebook's `"{[]}" -> True` assertion.

Also verify a failing case, `"([)]"`:

| Pass | `prev` (before) | after all three `.replace` calls | Changed? |
| ---- | ---------------- | ---------------------------------- | -------- |
| 1 | `"([)]"` | `"([)]"` (no `()`, no `[]`, no `{}` adjacent — the pairs are interleaved, not adjacent) | no — loop exits immediately |

`s == "([)]" != ""` → returns `False` ✓ — the brute-force approach correctly rejects interleaved (non-nested) brackets because interleaved pairs are never *adjacent*, so `.replace` never touches them.

### Mental model

- Simple, "physical" simulation: valid nesting always reduces to nothing when you keep popping the innermost matched pair.
- Interleaved (wrong-order) brackets never become adjacent, so they survive every pass and the string never empties.
- Costs a full string scan (three `.replace` calls) per pass, and nested brackets need one pass per nesting level.

### Common confusions

- **Passes needed = nesting depth:** a string like `"((((()))))"` needs many passes, not one — this is where the `O(n^2)` cost comes from.
- **`.replace` removes *all* non-overlapping occurrences per call**, not just one — easy to think it only removes one pair at a time.
- **Only handles adjacent pairs by construction:** it works because a valid nested string always has *some* innermost adjacent pair to remove; malformed strings simply stop changing.

### Complexity

- **Time:** `O(n^2)` — each cleanup pass is `O(n)`, and up to `O(n)` passes may be needed (one per nesting level)
- **Space:** `O(n)` — each `.replace` call builds a new string

---

## `valid_paren_stack` — Stack

### What it does

Scans left to right. Every opening bracket is pushed onto a stack. Every closing bracket must match the opener currently on top of the stack (via the `match` map) — if it doesn't, or the stack is empty, the string is invalid immediately. At the end, the string is valid only if the stack is empty (every opener was closed).

### Code

```python
def valid_paren_stack(s: str) -> bool:
    match = {")": "(", "]": "[", "}": "{"}  # each closer mapped to the opener it needs
    stack = []                             # holds the openers we've seen but not yet closed
    for c in s:                            # scan the string left to right
        if c in match:                     # c is a CLOSER
            # It's valid only if the most recent opener (top of stack) matches.
            if not stack or stack[-1] != match[c]:
                return False               # nothing to close, or wrong type -> invalid
            stack.pop()                    # matched -> remove that opener
        else:                              # c is an OPENER
            stack.append(c)                # remember it until its closer arrives
    return not stack                       # valid only if no opener was left unclosed
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `match = {")": "(", "]": "[", "}": "{"}` | Lookup: given a closer, what opener must be on top of the stack |
| `stack = []` | Holds unmatched openers in the order they were seen |
| `for c in s:` | One left-to-right pass over the string |
| `if c in match:` | Branch: `c` is a closing bracket |
| `if not stack or stack[-1] != match[c]: return False` | Invalid if there's nothing to close, or the top opener is the wrong type |
| `stack.pop()` | Matched — remove that opener, it's now closed |
| `else: stack.append(c)` | `c` is an opener — remember it for later |
| `return not stack` | Valid only if every pushed opener was eventually popped |

### Step-by-step trace (canonical example `"{[]}"`)

| i | char | Type | Action | Stack after |
| - | ---- | ---- | ------ | ----------- |
| 0 | `{` | opener | push | `['{']` |
| 1 | `[` | opener | push | `['{', '[']` |
| 2 | `]` | closer | `match[']']='['`, top is `'['` → matches, pop | `['{']` |
| 3 | `}` | closer | `match['}']='{'`, top is `'{'` → matches, pop | `[]` |

Loop ends. `return not stack` → `not []` → `True` ✓ matches notebook's `exp=True` for `"{[]}"`.

Also trace the failing case `"([)]"`:

| i | char | Type | Action | Stack after |
| - | ---- | ---- | ------ | ----------- |
| 0 | `(` | opener | push | `['(']` |
| 1 | `[` | opener | push | `['(', '[']` |
| 2 | `)` | closer | `match[')']='('`, top is `'['` → **mismatch** → `return False` | — |

**Final output:** `False` ✓ matches notebook's `exp=False` for `"([)]"`.

### Mental model

- The stack top is always "the most recently opened, still-unclosed bracket" — exactly what a closer must match.
- A single left-to-right pass suffices because a stack naturally encodes "innermost first" resolution order.
- Empty stack at the end = every opener found its partner; leftover openers or an empty stack hit by a closer are both instant failures.

### Common confusions

- **Forgetting the final `not stack` check:** a string like `"(("` never triggers an early `False` but leaves openers unmatched — must check emptiness at the end.
- **Popping an empty stack:** a stray closer like `")"` alone must be caught by `not stack` in the guard, not by calling `.pop()` blindly.
- **Direction of the `match` dict:** it maps closer → opener, so `stack[-1] != match[c]` reads "top of stack is not the opener this closer needs."

### Complexity

- **Time:** `O(n)` — one pass, O(1) work per character
- **Space:** `O(n)` — worst case (all openers) the stack holds every character

---

## Quick reference

| Function | Technique | Output on `"{[]}"` | Output on `"([)]"` | Time | Space |
| -------- | --------- | -------------------- | --------------------- | ---- | ----- |
| `valid_paren_brute` | Repeated adjacent-pair removal | `True` | `False` | `O(n^2)` | `O(n)` |
| `valid_paren_stack` | Stack of openers | `True` | `False` | `O(n)` | `O(n)` |

## Patterns to remember

- **Stack for nesting / "most recent must resolve first":** whenever the latest thing opened must be the first closed, reach for a stack.
- **Signal words:** "balanced brackets", "matching pairs", "valid nesting", "undo the last".
- **Related problems:** Min Stack, Generate Parentheses, Evaluate Reverse Polish Notation, Daily Temperatures.
- **Common pitfalls:** (1) forgetting to check the stack is empty at the end; (2) popping an empty stack on a stray closer.
