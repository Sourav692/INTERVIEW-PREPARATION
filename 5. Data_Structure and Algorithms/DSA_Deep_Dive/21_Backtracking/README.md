# 🔙 Backtracking

> **Backtracking** is DFS over a tree of *decisions* instead of a tree of nodes. At every step you **choose** one
> option, **explore** what follows from it, and then **un-choose** it so the next option starts from a clean slate.
> It is the only general tool for problems that ask for *every* valid arrangement — every subset, every permutation,
> every path — or for *one* arrangement satisfying constraints too tangled for a greedy rule or a DP table.
> This chapter teaches the one template and the seven shapes it takes, covering every backtracking problem in
> **Blind 75** and **NeetCode 150**.

Prerequisite: [Tree Traversal](../04_Tree_Traversal/README.md) (recursive DFS is the engine here) and
[Graph Traversal](../07_Graph_Traversal/README.md) (Word Search is DFS on a grid).

---

## 1. The template — choose, explore, un-choose

Every backtracking function has the same skeleton. Learn it once and every problem below is a small edit:

```python
def backtrack(state, choices):
    if is_complete(state):          # base case: a full, valid arrangement
        record(state)               # save a COPY, not a reference (see §9)
        return
    for choice in choices:
        if not allowed(choice):     # pruning: skip branches that can't succeed
            continue
        state.append(choice)        # CHOOSE
        backtrack(state, next_choices(choice))   # EXPLORE
        state.pop()                 # UN-CHOOSE — restore state for the next sibling
```

The **un-choose** step is what separates backtracking from ordinary recursion. `state` is one shared list that
every recursive call mutates in place. Without the `pop()`, the second sibling would inherit the first sibling's
choice — the path `[1, 2]` would become `[1, 2, 3]` instead of `[1, 3]`. Every bug in this chapter is, at root,
a missing or misplaced un-choose.

### The recursion tree

Picture the calls as a tree. The root is the empty state. Each edge is one choice. Each node is one partial
arrangement. Leaves are the complete arrangements you record — or dead ends you prune.

```
subsets of [1, 2, 3]  (include/exclude each element in turn)

                          []
                 ┌────────┴────────┐
              +1 │                 │ skip 1
                [1]               []
           ┌─────┴─────┐     ┌─────┴─────┐
          [1,2]       [1]   [2]         []
         ┌──┴──┐    ┌──┴──┐  ┌──┴──┐   ┌──┴──┐
      [1,2,3] [1,2] [1,3] [1] [2,3] [2] [3]  []
```

Eight leaves, eight subsets. The shape of this tree is what determines the running time (§8).

---

## 2. Pattern 1 — Subsets (include / exclude)

**LC 78 Subsets · LC 90 Subsets II** — NeetCode 150

Every element is either *in* or *out*. Two ways to write it; know both, because interviewers ask for either.

**Include / exclude** — a binary decision per index. Produces the tree above:

```python
def subsets(nums):
    out, path = [], []
    def backtrack(i):
        if i == len(nums):
            out.append(path[:])     # leaf: one complete subset
            return
        path.append(nums[i]);  backtrack(i + 1);  path.pop()   # INCLUDE nums[i]
        backtrack(i + 1)                                        # EXCLUDE nums[i]
    backtrack(0)
    return out
```

**Start-index loop** — record *every* node, not just the leaves, and only ever move forward:

```python
def subsets(nums):
    out, path = [], []
    def backtrack(start):
        out.append(path[:])         # EVERY prefix is a subset — record on entry
        for i in range(start, len(nums)):
            path.append(nums[i]);  backtrack(i + 1);  path.pop()
    backtrack(0)
    return out
```

The `start` index is what prevents `[1, 2]` and `[2, 1]` from both appearing: once you have used index `i`, you
may only add indices *after* it. That single idea — **"only move forward"** — is the whole difference between
subsets/combinations (order does not matter) and permutations (it does).

**Subsets II — duplicates in the input.** Sort first, then skip an element if it equals the previous one *and*
the previous one was not used in this branch:

```python
def subsets_with_dup(nums):
    nums.sort()                                   # duplicates become adjacent
    out, path = [], []
    def backtrack(start):
        out.append(path[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue                          # same value as the sibling we just finished — skip
            path.append(nums[i]);  backtrack(i + 1);  path.pop()
    backtrack(0)
    return out
```

`i > start` is the precise condition. At the *first* position of a loop (`i == start`) a duplicate value is
legitimately a new branch; at later positions it would only re-create a subset the previous sibling already
produced. This "sort + skip the sibling duplicate" move recurs in Combination Sum II and Permutations II.

---

## 3. Pattern 2 — Combinations & Combination Sum

**LC 77 Combinations · LC 39 Combination Sum · LC 40 Combination Sum II** — 39 is Blind 75; all three NeetCode 150

Same start-index loop as subsets, with a different base case: record only when the path has hit its target
(length `k`, or sum `target`).

```python
def combination_sum(candidates, target):          # LC 39 — each candidate may be reused
    out, path = [], []
    def backtrack(start, remaining):
        if remaining == 0:
            out.append(path[:]);  return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break                             # PRUNE: sorted input, so nothing after fits either
            path.append(candidates[i])
            backtrack(i, remaining - candidates[i])   # `i`, not `i + 1`: reuse allowed
            path.pop()
    candidates.sort()
    backtrack(0, target)
    return out
```

Two things to notice:

- **`backtrack(i, ...)` vs `backtrack(i + 1, ...)`.** Passing `i` lets the same candidate be chosen again;
  passing `i + 1` forbids it. That one character is the difference between LC 39 (unlimited reuse) and LC 40
  (each element once).
- **The `break`.** Because the candidates are sorted, the moment one is too large, every later one is too. The
  prune itself is what matters — on `[2, 3, 5, 7]` with target `20` it cuts the recursive calls from 246 to 133
  (measured in the notebook). `break` and `continue` skip exactly the same *branches* on sorted input; `break`
  is still the right choice because it also skips the leftover loop iterations for free.

**Combination Sum II** combines both ideas: `i + 1` (no reuse) and the sibling-duplicate skip from Subsets II.

---

## 4. Pattern 3 — Permutations (order matters)

**LC 46 Permutations · LC 47 Permutations II** — NeetCode 150

When order matters, the start index is *wrong* — `[2, 1]` is a different permutation from `[1, 2]`. Instead,
every level considers *every* element and tracks which are already on the path:

```python
def permute(nums):
    out, path, used = [], [], [False] * len(nums)
    def backtrack():
        if len(path) == len(nums):
            out.append(path[:]);  return
        for i in range(len(nums)):
            if used[i]:
                continue                          # already on the path
            used[i] = True;   path.append(nums[i])    # CHOOSE
            backtrack()                               # EXPLORE
            path.pop();       used[i] = False         # UN-CHOOSE — both pieces of state
    backtrack()
    return out
```

The `used` array is the second piece of state that must be un-chosen. Forgetting to reset `used[i] = False` is
the classic permutations bug: the first full permutation is found and then every other branch is starved.

**Permutations II** adds the sort + skip rule with one twist: skip `nums[i]` if it equals `nums[i-1]` **and
`nums[i-1]` is not currently used**. That extra clause means "the earlier duplicate has already been tried at this
level and finished" — if it is *currently* on the path, this is a legitimately different position for the twin.

---

## 5. Pattern 4 — Grid backtracking

**LC 79 Word Search** — Blind 75 & NeetCode 150

DFS on a grid where the *cell itself* is the state you mark and unmark. Instead of a separate `visited` set,
overwrite the cell with a sentinel and restore it on the way out:

```python
def exist(board, word):
    R, C = len(board), len(board[0])
    def dfs(r, c, k):                             # k = index into `word` we are trying to match
        if k == len(word):
            return True                           # matched every character
        if not (0 <= r < R and 0 <= c < C) or board[r][c] != word[k]:
            return False
        saved, board[r][c] = board[r][c], "#"     # CHOOSE: mark this cell as on-path
        found = (dfs(r+1, c, k+1) or dfs(r-1, c, k+1) or
                 dfs(r, c+1, k+1) or dfs(r, c-1, k+1))   # EXPLORE 4 neighbours
        board[r][c] = saved                       # UN-CHOOSE: restore, whether or not we found it
        return found
    return any(dfs(r, c, 0) for r in range(R) for c in range(C))
```

Notice this variant **returns a boolean and stops at the first success** (`or` short-circuits) instead of
collecting every solution. Backtracking for a *yes/no* question is the same template with `return True`
threaded up through the recursion.

---

## 6. Pattern 5 — Partitioning a string

**LC 131 Palindrome Partitioning** — NeetCode 150

The choice at each step is *where to cut next*. From position `start`, try every end position; if
`s[start:end]` is valid, choose it and recurse from `end`:

```python
def partition(s):
    out, path = [], []
    def backtrack(start):
        if start == len(s):
            out.append(path[:]);  return
        for end in range(start + 1, len(s) + 1):
            piece = s[start:end]
            if piece == piece[::-1]:              # PRUNE: only palindromic pieces are allowed
                path.append(piece);  backtrack(end);  path.pop()
    backtrack(0)
    return out
```

This is the subsets start-index loop in disguise: instead of "which element next", the question is "how long is
the next piece". Any "split this into valid chunks" problem (IP addresses, word break with enumeration) is this
pattern.

---

## 7. Pattern 6 — Mapping / Cartesian product

**LC 17 Letter Combinations of a Phone Number** — NeetCode 150

One position at a time, one choice per letter mapped to that digit. No start index, no `used` set — every level
is independent:

```python
def letter_combinations(digits):
    if not digits:
        return []
    phone = {"2":"abc","3":"def","4":"ghi","5":"jkl","6":"mno","7":"pqrs","8":"tuv","9":"wxyz"}
    out, path = [], []
    def backtrack(i):
        if i == len(digits):
            out.append("".join(path));  return
        for ch in phone[digits[i]]:
            path.append(ch);  backtrack(i + 1);  path.pop()
    backtrack(0)
    return out
```

Recognise this shape by its tree: every node at depth `d` has exactly as many children as the `d`-th digit has
letters. Time is the product of the branching factors — up to `4^n`.

---

## 8. Pattern 7 — Constraint satisfaction with pruning sets

**LC 51 N-Queens** — NeetCode 150

Place one queen per row; the choice at each row is the column. The art is making the "is this placement safe?"
check **O(1)** by tracking three sets — used columns, used `r - c` diagonals, and used `r + c` anti-diagonals —
instead of rescanning the board:

```python
def solve_n_queens(n):
    out, cols, diag, anti = [], set(), set(), set()
    board = [["."] * n for _ in range(n)]
    def backtrack(r):
        if r == n:
            out.append(["".join(row) for row in board]);  return
        for c in range(n):
            if c in cols or (r - c) in diag or (r + c) in anti:
                continue                          # PRUNE: attacked by an earlier queen
            cols.add(c);  diag.add(r - c);  anti.add(r + c);  board[r][c] = "Q"    # CHOOSE
            backtrack(r + 1)                                                        # EXPLORE
            cols.remove(c);  diag.remove(r - c);  anti.remove(r + c);  board[r][c] = "."   # UN-CHOOSE
    backtrack(0)
    return out
```

Why `r - c` and `r + c`? Every cell on a `\` diagonal shares the same `r - c`; every cell on a `/` diagonal
shares the same `r + c`. Two queens attack diagonally exactly when one of those numbers matches. Three sets,
three `O(1)` lookups, and the placement check no longer touches the board at all.

Note the **four** pieces of state that must be un-chosen. The more state a pattern tracks, the more important it
is to write the un-choose line as an exact mirror of the choose line.

---

## 9. The pruning and dedup toolkit

Everything above is exponential. What makes it *fast enough* is refusing to explore branches that cannot
succeed. In order of how often they come up:

| Technique                                   | When                                          | Example                                             |
| ------------------------------------------- | --------------------------------------------- | --------------------------------------------------- |
| **Start index** — only move forward  | order does not matter (subsets, combinations) | `for i in range(start, n)`                        |
| **Sort + skip the sibling duplicate** | input has duplicate values                    | `if i > start and nums[i] == nums[i-1]: continue` |
| **`break` on sorted overflow**      | sorted input, additive target                 | `if candidates[i] > remaining: break`             |
| **Constraint sets**                   | each choice must avoid conflicts              | N-Queens`cols` / `diag` / `anti`              |
| **Validity check before recursing**   | only some choices are legal                   | `if piece == piece[::-1]`                         |
| **Return on first success**           | yes/no or find-one questions                  | Word Search`or` chain                             |
| **Feasibility bound**                 | remaining slots cannot reach the goal         | `if len(path) + (n - i) < k: return`              |

Each prune is a `continue`, `break`, or early `return` placed *before* the choose line, so the choose/un-choose
pair is never entered for a doomed branch.

### Copy the path when you record it

`out.append(path)` stores a *reference* to the one shared list, which every later call keeps mutating — you end
up with `k` copies of an empty list. Always `out.append(path[:])` (or `list(path)`, or `"".join(path)` for
strings). This is the second most common backtracking bug after a missing un-choose.

---

## 10. Complexity — count the leaves, multiply by the copy

Backtracking time is (number of recursion-tree nodes) × (work per node). The dominant term is almost always the
number of complete arrangements times the cost of copying each one:

| Problem                       | Arrangements                       | Copy cost     | Time                                       | Recursion depth     |
| ----------------------------- | ---------------------------------- | ------------- | ------------------------------------------ | ------------------- |
| Subsets (78)                  | `2^n`                            | `O(n)`      | `O(n · 2^n)`                            | `O(n)`            |
| Permutations (46)             | `n!`                             | `O(n)`      | `O(n · n!)`                             | `O(n)`            |
| Combination Sum (39)          | ≤`2^target` paths, pruned       | `O(target)` | exponential in`target / min(candidates)` | `O(target / min)` |
| Word Search (79)              | one path per start cell            | —            | `O(R·C · 3^L)`                         | `O(L)`            |
| Palindrome Partitioning (131) | `2^(n-1)` cut patterns           | `O(n)`      | `O(n · 2^n)`                            | `O(n)`            |
| Letter Combinations (17)      | up to`4^n`                       | `O(n)`      | `O(n · 4^n)`                            | `O(n)`            |
| N-Queens (51)                 | far fewer than`n!` after pruning | `O(n²)`    | `O(n!)` upper bound                      | `O(n)`            |

The recursion depth — and therefore the call-stack space — is always the length of one arrangement, never the
number of arrangements. That is why a `2^n` enumeration is fine at `n = 20` but a `2^n` *stack* would not be.

---

## 11. Blind 75 & NeetCode 150 coverage

| #   | Problem                 | List                               | Pattern (section)                                  |
| --- | ----------------------- | ---------------------------------- | -------------------------------------------------- |
| 78  | Subsets                 | NeetCode 150                       | §2 include/exclude · start index                 |
| 90  | Subsets II              | NeetCode 150                       | §2 + sort & skip sibling duplicate                |
| 39  | Combination Sum         | **Blind 75** · NeetCode 150 | §3 start index, reuse via`i`, sorted `break`  |
| 40  | Combination Sum II      | NeetCode 150                       | §3`i + 1` + sort & skip                         |
| 46  | Permutations            | NeetCode 150                       | §4`used` array                                  |
| 47  | Permutations II         | (bonus)                            | §4 + sort & skip with the`not used[i-1]` clause |
| 79  | Word Search             | **Blind 75** · NeetCode 150 | §5 grid, mark-in-place, return on first success   |
| 131 | Palindrome Partitioning | NeetCode 150                       | §6 cut positions + validity check                 |
| 17  | Letter Combinations     | NeetCode 150                       | §7 mapping / product                              |
| 51  | N-Queens                | NeetCode 150                       | §8 constraint sets                                |

Every one of these is in the companion notebook with `assert` checks, and the interactive lesson traces
subsets, combination sum, and N-Queens step by step.

---

## 12. Cheat sheet

| Question                     | Answer                                                                                                                        |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| The template?                | **choose → explore → un-choose**, with pruning checks placed before the choose line.                                  |
| What does un-choose do?      | restores the shared`path` (and any `used` / set state) so the next sibling starts clean.                                  |
| Subsets vs permutations?     | subsets use a**start index** (only move forward); permutations use a **`used` array** (any element, any level). |
| Allow reusing a candidate?   | recurse with`i` instead of `i + 1`.                                                                                       |
| Input has duplicates?        | **sort**, then `if i > start and nums[i] == nums[i-1]: continue`.                                                     |
| Cheapest big prune?          | sorted input + additive target →`break` (not `continue`) the moment a candidate is too large.                            |
| N-Queens safe check in O(1)? | three sets:`cols`, `r - c` (diagonal), `r + c` (anti-diagonal).                                                         |
| Grid problems?               | mark the cell itself (`"#"`), recurse 4 ways, restore the cell.                                                             |
| Find one vs find all?        | find-one returns`True` up the chain and short-circuits with `or`; find-all records and continues.                         |
| Recording a result?          | always copy —`path[:]` — never append the shared list itself.                                                             |
| Time complexity?             | (number of complete arrangements) × (cost to copy one); depth is the arrangement length.                                     |
