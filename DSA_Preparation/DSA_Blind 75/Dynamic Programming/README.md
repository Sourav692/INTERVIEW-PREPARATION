# 🧮 Dynamic Programming — Concept Tutorial

> A plain-language guide to the ideas behind the Blind 75 **Dynamic Programming** problems, with diagrams.
> Pair this with `visualizations/Dynamic Programming/` and `notebooks/Dynamic Programming/`.

---

## 1. What is Dynamic Programming?

**DP** solves a big problem by solving smaller **overlapping** subproblems **once** and reusing the answers. The naive recursion recomputes the same things exponentially; DP remembers them.

Look at plain recursion for "climb n stairs" — notice how `f(3)` gets computed many times:

```mermaid
graph TD
    F5["f(5)"] --> F4["f(4)"]
    F5 --> F3a["f(3)"]
    F4 --> F3b["f(3)"]
    F4 --> F2a["f(2)"]
    F3a --> F2b["f(2)"]
    F3a --> F1a["f(1)"]
    F3b --> F2c["f(2)"]
```

DP computes each state **once** and stores it. Two styles:
- **Memoization** — recursion + a cache.
- **Tabulation** — fill a table from the smallest cases up (usually preferred).

**The recipe:** define the **state** (what does `dp[i]` mean?), write the **recurrence** (how does it use smaller states?), set the **base cases**, pick a **fill order**.

---

## 2. Pattern A — Fibonacci-Style 1-D DP

Each answer is built from the previous one or two.

```mermaid
flowchart LR
    d0["dp[0]"] --> d1["dp[1]"] --> d2["dp[2]"] --> d3["dp[3]"] --> d4["dp[4]"]
    d2 -. "dp[2]=dp[1]+dp[0]" .-> d0
```

Often you only need the last couple of values → **O(1) space** with two rolling variables.
**The tell:** *"count the ways"*, or optimize along a line where each step depends on the last few.
**Problems:** Climbing Stairs, House Robber, House Robber II (circle → run it twice), Decode Ways.

Decode Ways adds validity checks:

```mermaid
flowchart TD
    P["at position i"] --> Q1{"is this digit 1-9?"}
    Q1 -->|yes| A1["add ways(i-1)"]
    P --> Q2{"do these 2 digits form 10-26?"}
    Q2 -->|yes| A2["add ways(i-2)"]
```

---

## 3. Pattern B — Build Up to a Target

To make an amount/prefix, first solve every smaller amount, then combine.

```mermaid
flowchart TD
    A["amount a"] --> C{"try each coin c"}
    C --> S["dp[a] = min(dp[a], dp[a - c] + 1)"]
```

Greedy fails here (biggest coin first can miss the best) — DP tries **all** choices.
**The tell:** *"fewest / number of ways to make a target from reusable parts"*.
**Problems:** Coin Change, Word Break (a prefix works if a word ends here **and** the part before also works).

---

## 4. Pattern C — 2-D Grid DP

Two sequences to compare, or a grid to cross. Each cell leans on already-filled neighbors.

```mermaid
graph TD
    subgraph "match → diagonal + 1, else max(up, left)"
      UL["dp[i-1][j-1]"] --> D["dp[i][j]"]
      U["dp[i-1][j]"] --> D
      Lft["dp[i][j-1]"] --> D
    end
```

**The tell:** *"longest common ... of two strings"*, *"edit distance"*, *"count grid paths"*.
**Problems:** Longest Common Subsequence, Unique Paths (each cell = cell above + cell left).

---

## 5. Pattern D — "Best Ending Here"

For each position, find the best answer that finishes right there; the overall best is the max.

```mermaid
flowchart LR
    subgraph "nums"
      n1["3"] --- n2["1"] --- n3["4"] --- n4["2"] --- n5["5"]
    end
    subgraph "dp = longest increasing run ending here"
      d1["1"] --- d2["1"] --- d3["2"] --- d4["2"] --- d5["3"]
    end
```

**The tell:** longest/optimal **subsequence** where each element extends earlier ones.
**Problems:** Longest Increasing Subsequence (`O(n²)` DP, or `O(n log n)` with binary search).

---

## 6. Pattern E — When Greedy Beats DP

Sometimes one clever running value replaces the whole table.

```mermaid
flowchart LR
    I["sweep index i"] --> F{"i beyond<br/>farthest reach?"}
    F -->|yes| STUCK["can't get here ❌"]
    F -->|no| U["farthest = max(farthest, i + nums[i])"]
    U --> I
```

**Problems:** Jump Game (greedy "farthest reach" is `O(n)`; the reachability DP is `O(n²)`).

---

## 7. Pattern F — Backtracking (list all solutions)

When you must **list** every combination (not just count/optimize), build choices, explore, and **undo**.

```mermaid
flowchart TD
    C["choose a candidate"] --> E["explore (recurse on the remainder)"]
    E --> U["undo the choice (backtrack)"]
    U --> C
    E --> Z{"remainder == 0?"}
    Z -->|yes| REC["record the combination ✅"]
```

**Problems:** Combination Sum (a start index avoids duplicates; sort to prune).

---

## 8. Which Pattern for Which Problem?

```mermaid
mindmap
  root((DP))
    Fibonacci 1-D
      Climbing Stairs
      House Robber
      House Robber II
      Decode Ways
    Build to target
      Coin Change
      Word Break
    2-D grid
      Longest Common Subseq
      Unique Paths
    Best ending here
      Longest Increasing Subseq
    Greedy
      Jump Game
    Backtracking
      Combination Sum
```

---

## 9. Complexity Cheat Sheet

| Pattern | Time | Space |
|---|---|---|
| 1-D DP | `O(n)` | `O(n)` → `O(1)` |
| Build to target | `O(target × choices)` | `O(target)` |
| 2-D grid | `O(m × n)` | `O(m × n)` → `O(n)` |
| Best ending here | `O(n²)` / `O(n log n)` | `O(n)` |
| Greedy | `O(n)` | `O(1)` |

---

## 10. Interview Playbook

1. **Say the brute force** — "try every choice recursively" — then notice it recomputes subproblems (the DP signal).
2. **Name the state** (`dp[i]` means…), write the **recurrence** and **base cases**.
3. **Pick a fill order** so every value is ready when needed; then shrink memory if only recent values matter.
4. **Ask if greedy works** — sometimes a single running value replaces the whole table.

> ▶ **Next:** open `visualizations/Dynamic Programming/index.html` to watch tables fill cell by cell.
