# 417. Pacific Atlantic Water Flow — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/pacific_atlantic_water_flow.ipynb`
> **LeetCode:** https://leetcode.com/problems/pacific-atlantic-water-flow/
> **Generated for:** personal study reference

---

## Overview

| Topic                          | Key idea                                                                                                      |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| Grid DFS/BFS                   | Water flows from a cell to an equal-or-lower neighbor                                                         |
| Search backwards from the goal | Instead of asking "can cell X reach an ocean?" for every cell, climb*uphill* from each ocean's border cells |
| Multi-source flood fill        | Seed the search from**every** border cell of an ocean at once, not just one                             |
| Intersect two reachable sets   | The answer is exactly the cells reachable from**both** oceans' border searches                          |

**Canonical example** (from notebook):

```
heights =
[1, 2, 2, 3, 5]
[3, 2, 3, 4, 4]
[2, 4, 5, 3, 1]
[6, 7, 1, 4, 5]
[5, 1, 1, 2, 4]
```

- **Pacific** touches the **top row** (`r = 0`) and **left column** (`c = 0`).
- **Atlantic** touches the **bottom row** (`r = 4`) and **right column** (`c = 4`).
- Water at `(r, c)` may flow to a neighbor `(nr, nc)` only if `heights[nr][nc] <= heights[r][c]`.

Expected outputs (from notebook asserts):

| Input                 | Expected cells reaching both oceans             | `pacific_atlantic_brute` | `pacific_atlantic_optimal` |
| --------------------- | ----------------------------------------------- | -------------------------- | ---------------------------- |
| `heights` above     | `[[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]` | ✓ matches                 | ✓ matches                   |
| Known-cell spot check | `[0, 4]` and `[4, 0]` must be present       | ✓                         | ✓                           |

---

## `pacific_atlantic_brute` — Search From Every Cell

### What it does

For **every** cell in the grid, runs an independent DFS that follows downhill (equal-or-lower) neighbors, tracking whether the flood from that cell ever touches a Pacific border (`x == 0 or y == 0`) and an Atlantic border (`x == rows-1 or y == cols-1`). The cell is added to the answer only if both flags become `True`. This repeats the traversal from scratch for each of the `rows * cols` starting cells.

### Code

```python
def pacific_atlantic_brute(heights):
    if not heights or not heights[0]:
        return []
    rows, cols = len(heights), len(heights[0])
    def reaches_both(sr, sc):              # from this cell, can water reach both oceans?
        seen = set(); stack = [(sr, sc)]; pac = atl = False
        while stack:
            x, y = stack.pop()
            if (x, y) in seen: continue
            seen.add((x, y))
            if x == 0 or y == 0: pac = True        # touched a Pacific border
            if x == rows-1 or y == cols-1: atl = True  # touched an Atlantic border
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = x+dx, y+dy
                if 0 <= nx < rows and 0 <= ny < cols and heights[nx][ny] <= heights[x][y]:
                    stack.append((nx, ny))  # water flows to equal-or-lower neighbors
        return pac and atl
    return [[r, c] for r in range(rows) for c in range(cols) if reaches_both(r, c)]
```

### Line by line

| Line / code                                                                         | What it does                                                            |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `if not heights or not heights[0]: return []`                                     | Empty-grid edge case                                                    |
| `rows, cols = len(heights), len(heights[0])`                                      | Grid dimensions                                                         |
| `def reaches_both(sr, sc):`                                                       | Local helper — DFS flood fill starting at`(sr, sc)`                  |
| `seen = set(); stack = [(sr, sc)]; pac = atl = False`                             | Iterative DFS state plus two "did we touch this ocean" flags            |
| `x, y = stack.pop()`                                                              | Pop the next cell (LIFO — depth-first)                                 |
| `if (x, y) in seen: continue`                                                     | Skip cells already flooded from this start                              |
| `seen.add((x, y))`                                                                | Mark visited for this cell's flood fill                                 |
| `if x == 0 or y == 0: pac = True`                                                 | Cell sits on the Pacific border                                         |
| `if x == rows-1 or y == cols-1: atl = True`                                       | Cell sits on the Atlantic border                                        |
| `for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):`                                      | Check all 4 neighbors                                                   |
| `if 0 <= nx < rows and 0 <= ny < cols and heights[nx][ny] <= heights[x][y]:`      | Bounds check +**downhill/level** flow condition                   |
| `stack.append((nx, ny))`                                                          | Push the reachable neighbor to keep flooding                            |
| `return pac and atl`                                                              | True only if this cell's flood touched**both** borders            |
| `return [[r, c] for r in range(rows) for c in range(cols) if reaches_both(r, c)]` | Rerun the whole flood fill from**every** cell and collect winners |

### Step-by-step trace (canonical example, starting cell `(2,2)` — height `5`)

`(2,2)` is one of the 7 cells in the final answer. Tracing `reaches_both(2, 2)`:

| Step | Pop`(x, y)`                                     | height | `pac` after         | `atl` after           | Neighbors pushed (downhill/level only)                                                                                                                                   |
| ---- | ------------------------------------------------- | ------ | --------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1    | `(2,2)`                                         | 5      | False                 | False                   | `(3,2)`h1, `(1,2)`h3, `(2,3)`h3 *(not `(2,1)` h4 — that's uphill relative? 4<=5 ✓ actually pushed too)* → pushes `(3,2)`, `(1,2)`, `(2,3)`, `(2,1)` |
| 2    | `(2,1)`                                         | 4      | False                 | False                   | pushes`(1,1)`h2                                                                                                                                                        |
| 3    | `(1,1)`                                         | 2      | False                 | False                   | pushes`(0,1)`h2, `(1,0)`h3 *(3<=2? no, skipped)* → only `(0,1)`                                                                                                 |
| 4    | `(0,1)`                                         | 2      | **True** (x==0) | False                   | pushes`(0,0)`h1, `(0,2)`h2                                                                                                                                           |
| 5    | `(0,2)`                                         | 2      | True                  | False                   | pushes`(1,2)` (already queued)                                                                                                                                         |
| 6    | `(0,0)`                                         | 1      | True                  | False                   | pushes nothing new in-bounds beyond seen                                                                                                                                 |
| 7    | `(2,3)`                                         | 3      | True                  | False                   | pushes`(3,3)`? h4<=3 no. `(2,4)`h1<=3 yes                                                                                                                            |
| 8    | `(2,4)`                                         | 1      | True                  | True (y==cols-1==4) | pushes`(3,4)`? h5<=1 no. `(1,4)`h4<=1 no                                                                                                                             |
| —   | (remaining stack drains:`(3,2)`, `(1,2)`, …) | —     | True                  | True                    | loop continues but`pac and atl` already satisfiable                                                                                                                    |

Once `x == 0` was hit at step 4 and `y == cols-1` was hit at step 8, `pac = atl = True`. The DFS still finishes draining the stack (it doesn't early-exit), but the result is already decided: `reaches_both(2, 2)` returns `True`, so `[2, 2]` is added to the answer.

This whole `reaches_both` call is then **repeated independently for all 25 cells** in the 5×5 grid — that repetition (each flood fill touching up to `O(mn)` cells) is what makes this approach `O((mn)²)`.

### Mental model

- "Can I get from here to the sea?" — literally simulate the water flowing downhill from each candidate cell.
- Every cell pays for its own full flood fill; nothing is shared between cells even though their downhill paths overlap heavily.
- `pac`/`atl` are just booleans — once both are `True` the answer for that cell is locked in, but the code doesn't short-circuit the traversal early.

### Common confusions

- **Direction of the inequality:** `heights[nx][ny] <= heights[x][y]` — water flows to an equal-or-**lower** neighbor. This is the "forward" (natural) direction, opposite of the optimal solution's uphill climb.
- **Border check uses absolute grid edges**, not "is this the start cell" — any cell on row 0/col 0 counts as touching Pacific, any cell on row `rows-1`/col `cols-1` counts as touching Atlantic, no matter which cell the flood started from.
- **Wasted work:** the same downhill paths get re-explored from scratch for every one of the `mn` starting cells — this redundancy is exactly what approach 2 eliminates.

### Complexity

- **Time:** `O((mn)²)` — one `O(mn)` flood fill per cell, `mn` cells total
- **Space:** `O(mn)` — `seen` set and stack per call (plus result list)

---

## `pacific_atlantic_optimal` — Climb From the Borders

### What it does

Instead of asking each cell whether it can reach the oceans, this runs the search **backwards**: starting from every Pacific-border cell (top row + left column), it climbs to neighbors whose height is **equal or higher** (the reverse of natural water flow), marking every cell reached in `pac`. It repeats the same climb from every Atlantic-border cell (bottom row + right column) into `atl`. A cell that appears in both sets can drain downhill to both oceans, since the climb is exactly the reverse of the flow.

### Code

```python
def pacific_atlantic_optimal(heights):
    if not heights or not heights[0]:
        return []
    rows, cols = len(heights), len(heights[0])
    pac, atl = set(), set()                # cells that can drain to each ocean
    def dfs(r, c, seen, prev):             # CLIMB inland from the border (uphill/level)
        if (r, c) in seen or r < 0 or c < 0 or r >= rows or c >= cols or heights[r][c] < prev:
            return
        seen.add((r, c))
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            dfs(r+dx, c+dy, seen, heights[r][c])   # move to equal-or-higher neighbors
    for c in range(cols):                  # seed from the top (Pacific) and bottom (Atlantic) rows
        dfs(0, c, pac, heights[0][c]); dfs(rows-1, c, atl, heights[rows-1][c])
    for r in range(rows):                  # seed from the left (Pacific) and right (Atlantic) columns
        dfs(r, 0, pac, heights[r][0]); dfs(r, cols-1, atl, heights[r][cols-1])
    return [[r, c] for r in range(rows) for c in range(cols) if (r, c) in pac and (r, c) in atl]
```

### Line by line

| Line / code                                                                                      | What it does                                                                                                          |
| ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `if not heights or not heights[0]: return []`                                                  | Empty-grid edge case                                                                                                  |
| `pac, atl = set(), set()`                                                                      | Two separate reachable-cell sets, one per ocean                                                                       |
| `def dfs(r, c, seen, prev):`                                                                   | Recursive climb;`seen` is `pac` or `atl`, `prev` is the height just came from                                 |
| `if (r, c) in seen or ... or heights[r][c] < prev: return`                                     | Stop if already visited, out of bounds,**or this cell is lower than where we came from** (can't climb downhill) |
| `seen.add((r, c))`                                                                             | Mark this cell as able to drain to the current ocean                                                                  |
| `for dx, dy in (...): dfs(r+dx, c+dy, seen, heights[r][c])`                                    | Recurse into all 4 neighbors, passing**this** cell's height as the new `prev`                                 |
| `for c in range(cols): dfs(0, c, pac, heights[0][c]); dfs(rows-1, c, atl, heights[rows-1][c])` | Seed Pacific from every cell of the**top row**, Atlantic from every cell of the **bottom row**            |
| `for r in range(rows): dfs(r, 0, pac, heights[r][0]); dfs(r, cols-1, atl, heights[r][cols-1])` | Seed Pacific from every cell of the**left column**, Atlantic from every cell of the **right column**      |
| `return [[r, c] for r in range(rows) for c in range(cols) if (r, c) in pac and (r, c) in atl]` | Answer = cells present in**both** reachable sets                                                                |

### Step-by-step trace (canonical example)

Grid recap:

```
r0: 1 2 2 3 5
r1: 3 2 3 4 4
r2: 2 4 5 3 1
r3: 6 7 1 4 5
r4: 5 1 1 2 4
```

**Pacific climb** — seeded from top row `(0,0)…(0,4)` and left column `(0,0)…(4,0)` (9 seed cells). Each DFS only advances to a neighbor whose height is `>=` the cell just left:

| Frontier step | Cells added to`pac` this round                                                 | Why                                                                                                                                 |
| ------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Seeds         | `(0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(2,0),(3,0),(4,0)`                        | All Pacific-border cells                                                                                                            |
| Round 1       | `(1,1)`h2, `(1,2)`h3, `(1,3)`h4, `(2,1)`h4, `(3,1)`h7                  | e.g. from`(0,1)`h2 → `(1,1)`h2 (2≥2 ✓); from `(2,0)`h2 → `(2,1)`h4 (4≥2 ✓); from `(3,0)`h6 → `(3,1)`h7 (7≥6 ✓) |
| Round 2       | `(2,2)`h5, `(1,4)`h4                                                         | from`(1,2)`h3 → `(2,2)`h5 (5≥3 ✓); from `(1,3)`h4 → `(1,4)`h4 (4≥4 ✓)                                                 |
| Round 3       | *(none — e.g. `(2,2)`h5 → `(3,2)`h1 fails 1≥5, `(2,3)`h3 fails 3≥5)* | climb blocked everywhere                                                                                                            |

Final `pac = {(0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,1),(1,2),(1,3),(1,4),(2,0),(2,1),(2,2),(3,0),(3,1),(4,0)}` (16 cells).

**Atlantic climb** — seeded from bottom row `(4,0)…(4,4)` and right column `(0,4)…(4,4)` (9 seed cells):

| Frontier step | Cells added to`atl` this round                                             | Why                                                                                                                                 |
| ------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Seeds         | `(4,0),(4,1),(4,2),(4,3),(4,4),(0,4),(1,4),(2,4),(3,4)`                    | All Atlantic-border cells                                                                                                           |
| Round 1       | `(3,0)`h6, `(3,1)`h7, `(3,2)`h1, `(3,3)`h4, `(1,3)`h4, `(2,3)`h3 | e.g. from`(4,0)`h5 → `(3,0)`h6 (6≥5 ✓); from `(4,2)`h1 → `(3,2)`h1 (1≥1 ✓); from `(1,4)`h4 → `(1,3)`h4 (4≥4 ✓) |
| Round 2       | `(2,2)`h5                                                                  | from`(3,2)`h1 → `(2,2)`h5 (5≥1 ✓)                                                                                            |
| Round 3       | *(none)*                                                                   | climb blocked everywhere else                                                                                                       |

Final `atl = {(4,0),(4,1),(4,2),(4,3),(4,4),(0,4),(1,4),(2,4),(3,4),(3,0),(3,1),(3,2),(3,3),(1,3),(2,3),(2,2)}` (16 cells).

**Intersection** `pac ∩ atl`:

| Cell            | In`pac`?      | In`atl`? | In answer? |
| --------------- | --------------- | ---------- | ---------- |
| `(0,4)`       | ✓              | ✓         | ✓         |
| `(1,3)`       | ✓              | ✓         | ✓         |
| `(1,4)`       | ✓              | ✓         | ✓         |
| `(2,2)`       | ✓              | ✓         | ✓         |
| `(3,0)`       | ✓              | ✓         | ✓         |
| `(3,1)`       | ✓              | ✓         | ✓         |
| `(4,0)`       | ✓              | ✓         | ✓         |
| all other cells | at most one set | —         | ✗         |

**Result:** `[[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]` — matches the expected output.

### Mental model

- Flip the question: don't ask "can I flow out", ask "who could have flowed into me" — climbing uphill from the ocean border is the exact reverse of water flowing downhill toward it.
- `prev` threads the "height I just came from" down the recursion so the `heights[r][c] < prev` check enforces "only climb to equal-or-higher ground."
- Two independent multi-source flood fills (one per ocean), then a plain set intersection — no per-cell repeated work.
- Multi-source seeding: every border cell is its own DFS start, not just the corners.

### Common confusions

- **Inequality direction is flipped vs. the brute-force version:** here it's `heights[r][c] < prev` → stop (i.e., only continue if `heights[r][c] >= prev`), because we're climbing uphill, not flowing downhill.
- **`prev` starts as the seed cell's own height** (`heights[0][c]`, `heights[rows-1][c]`, etc.), not `-infinity` — so the first check `heights[r][c] < prev` is comparing the seed cell against itself, which trivially passes.
- **`pac` and `atl` are separate sets** — a cell can be in one, both, or neither; only "both" makes the final answer.
- **Recursive DFS depth:** unlike the brute-force iterative stack version, this uses actual Python recursion — deep/large grids could hit recursion limits (not an issue for typical LeetCode-sized grids).

### Complexity

- **Time:** `O(mn)` — each of the two flood fills visits each cell at most once
- **Space:** `O(mn)` — `pac`/`atl` sets plus recursion stack

---

## Quick reference

| Function                     | Technique                                           | Direction of flow check                              | Result on canonical grid                        | Time          | Space     |
| ---------------------------- | --------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------- | ------------- | --------- |
| `pacific_atlantic_brute`   | DFS from every cell, forward flow                   | `heights[neighbor] <= heights[current]` (downhill) | `[[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]` | `O((mn)²)` | `O(mn)` |
| `pacific_atlantic_optimal` | Multi-source DFS from ocean borders, reversed climb | `heights[neighbor] >= heights[current]` (uphill)   | `[[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]` | `O(mn)`     | `O(mn)` |

## Patterns to remember

- **Search backwards from the goal:** when many sources must each test reachability to the same destinations, flip it — search from the destinations instead and check membership.
- **Multi-source flood fill:** seed a single flood fill from *all* border/goal cells at once rather than one-at-a-time.
- **Intersect two reachable sets:** "reaches condition A AND condition B" = run two searches, intersect their visited sets.
- **Signal words:** "which cells can reach X and Y", "flow / spread on a grid", "water flows downhill", "multiple oceans/sources".
- **Related problems:** Number of Islands, Surrounded Regions, Walls and Gates.
- **Common pitfalls:** (1) searching forward from every cell instead of backward from the borders; (2) using the wrong height-comparison direction when climbing (uphill) vs. flowing (downhill).
