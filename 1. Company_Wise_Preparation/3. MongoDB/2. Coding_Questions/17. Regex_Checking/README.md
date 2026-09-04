# Regex Checking

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Dynamic Programming, Strings · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Write a function to determine if a string matches a pattern, where the pattern may contain the `+` operator. The `+` operator signifies that the **preceding character must appear one or more times**.

**Example:**

```
s = "google", p = "go+gle"  →  true
```

---

## Study Tools

### Hint 1

The `+` operator only affects the character immediately before it. Think about how you can consume either one occurrence of that character and move past the `+`, or consume one occurrence and **stay** on the `+` to allow another.

### Hint 2

Scan both strings with two pointers. When you see `p[j+1] == '+'`, you know `s[i]` must match `p[j]`, and you can either advance only `i` (to match another) or advance `j` by 2 (to finish the `+` group).

### Hint 3

Use recursion or an explicit stack over pairs `(i, j)`. At each step, handle the `+` case by branching into the two transitions above, and handle the non-`+` case by requiring a single-character match and advancing both pointers.

---

### Answer

This is a two-pointer string matching problem where the only wildcard is the postfix `+` operator. Walk both strings left to right; when the next pattern character is a `+`, consume one or more copies of the preceding character by branching between staying on the `+` and moving past it.

```python
def matches(s: str, p: str) -> bool:
    def dfs(i: int, j: int) -> bool:
        if j == len(p):
            return i == len(s)

        if j + 1 < len(p) and p[j + 1] == '+':
            # p[j] must appear one or more times
            if i < len(s) and s[i] == p[j]:
                # consume one copy and either stay on '+' or move past it
                return dfs(i + 1, j) or dfs(i + 1, j + 2)
            return False

        # normal character
        if i < len(s) and s[i] == p[j]:
            return dfs(i + 1, j + 1)
        return False

    return dfs(0, 0)
```

**Time:** O(n × m) worst case — each `(i, j)` pair is visited once with memoization, or the recursion tree has at most n × m distinct states without it. **Space:** O(n × m) with memoization for the state table, O(n + m) for the recursion stack without it.

The recursion explores every valid way to match the string against the pattern. When we see `p[j+1] == '+'`, the character `p[j]` must match at least one character in `s`, so we try consuming one copy and either continuing to consume more copies or moving past the `+`. The base case requires **both** pointers to reach the end simultaneously. If any branch returns `True`, the whole match succeeds.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest correct approach: brute force recursion. At each position `(i, j)`, if the next pattern character is not a `+`, just check `s[i] == p[j]` and move both pointers. If it is a `+`, you need one or more copies of `p[j]`, so try every possible number of copies from 1 up to the remaining string length. That gives an O(n²) time blowup in the worst case because you re-check the same suffix many times.

The bottleneck is **redundant recomputation**. Once you realize the decision at each `(i, j)` depends only on those two positions, you can memoize the result of `dfs(i, j)` in a table or dict. Each state is computed once, and there are at most n × m states, so time drops to O(n × m).

A further optimization is to notice that when you consume one copy of `p[j]` and stay on the `+`, you advance `i` but not `j`. When you move past the `+`, you advance `j` by 2. These are the only two transitions needed for the `+` case, so the recursion naturally prunes the search space without explicitly looping over all possible counts.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Define the matching semantics precisely before coding** — clarify whether `+` applies to the immediately preceding character only, whether `++` is valid, and whether the empty string matches `a+`. Interviewers listen for you to pin down these edge cases rather than assume.
- **Trace the two-pointer state explicitly** — write out the transitions for `(i, j)` when `p[j+1] == '+'` versus not, so the interviewer sees you understand the state machine. This makes the recursion easy to verify.
- **Memoize early** — even if you start with brute force, mention that the state space is `(i, j)` and that memoization removes redundant work. Interviewers reward recognizing overlapping subproblems quickly.
- **Handle the `+` at the end of the pattern** — check that `j + 1 < len(p)` before looking at `p[j+1]`, otherwise you index out of bounds. This is a common off-by-one that separates a clean solution from a buggy one.
- **Discuss the two transitions for `+`** — consuming one copy and staying on `+` versus consuming one copy and moving past it. Being explicit about this shows you understand the greedy-versus-exhaustive tradeoff.
- **Mention the worst-case complexity honestly** — O(n × m) is fine for this problem, but say it aloud and explain why. If you claim O(n) without justification, a sharp interviewer will push back.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Extend the pattern to support `*` (zero or more) and `?` (exactly one character)** — how do the transitions change for each operator?
- **Implement the same matching using dynamic programming with a 2D boolean table instead of recursion** — what are the base cases and recurrence?
- **What if the pattern must match the entire string and `+` can apply to a group in parentheses, like `(ab)+c`?** How would you parse and match that?
- **Can you optimize the space complexity to O(m) or O(min(n, m)) using a rolling array?** What information do you need to keep from the previous row?

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One correction to the official answer

The complexity claim is wrong for the code as written. It says:

> *"O(n × m) worst case — each (i, j) pair is visited once with memoization, **or the recursion tree has at most n × m distinct states without it**."*

The number of distinct *states* is indeed n × m, but without memoization what matters is the number of *paths* through them, and that is **exponential**. Each `+` group branches two ways, so a pattern like `a+a+a+a+a+a+a+a+` against a string of 30 `a`s explores an enormous tree of repeated sub-calls.

The code shown has **no memoization**, so its true worst case is exponential — the notebook demonstrates this with a timed comparison where the un-memoized version takes seconds on an input the memoized one answers instantly. Adding `@lru_cache` (or a `dict`) is what actually delivers the advertised O(n × m).
