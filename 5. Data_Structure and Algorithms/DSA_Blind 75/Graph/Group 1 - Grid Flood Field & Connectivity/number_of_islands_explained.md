# 200. Number of Islands — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/number_of_islands.ipynb`
> **LeetCode:** https://leetcode.com/problems/number-of-islands/
> **Generated for:** personal study reference

---

## Overview

| Topic | Key idea |
| ----- | -------- |
| Flood fill | An island is a connected blob of `"1"`s; flood-fill (DFS or BFS) sinks the whole blob so it is never recounted |
| Sink-as-you-go | Overwriting a visited land cell to `"0"` doubles as the visited marker — no separate `visited` set needed |
| Scan + count | Sweep every cell; each time you land on unvisited `"1"`, that's a **new** island — sink it, then `count += 1` |
| DFS flood fill | Recurse into the 4 neighbors, sinking as you go, until the whole island is drowned |
| BFS flood fill | Same idea, but sink the island with a queue instead of the call stack (safer for huge islands) |

**Canonical example** (from notebook, `g1`):

```
Grid (rows x cols = 4 x 5):
1 1 1 1 0
1 1 0 1 0
1 1 0 0 0
0 0 0 0 0

-> 1 island (all the 1s are connected)
```

Expected outputs (from notebook asserts):

| Input grid | Expected islands | `num_islands_dfs` | `num_islands_bfs` |
| ---------- | ----------------- | ------------------ | ------------------ |
| `g1 = ["11110","11010","11000","00000"]` | `1` | ✓ matches | ✓ matches |
| `g2 = ["11000","11000","00100","00011"]` | `3` | ✓ matches | ✓ matches |
| `["000"]` | `0` | ✓ matches | ✓ matches |

---

## `num_islands_dfs` — DFS Flood Fill

### What it does

Copies the grid so the caller's input isn't mutated. Defines a nested `dfs(r, c)` that: bails out if the cell is off-grid or not land (`"1"`); otherwise sinks the cell (`"0"`) and recurses into all 4 neighbors (down, up, right, left). The outer double loop scans every cell in row-major order; whenever it finds a still-standing `"1"`, that's an unvisited island — increment `count` and flood-fill it away with `dfs`.

### Code

```python
def num_islands_dfs(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    g = [row[:] for row in grid]           # work on a copy so we don't alter the caller's grid
    def dfs(r, c):                         # sink this whole connected island
        if r < 0 or c < 0 or r >= rows or c >= cols or g[r][c] != "1":
            return                         # off the grid or water -> stop
        g[r][c] = "0"                      # mark this land cell visited (sink it)
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1)   # spread to 4 neighbors
    count = 0
    for r in range(rows):
        for c in range(cols):
            if g[r][c] == "1":             # found a new, unvisited island
                count += 1; dfs(r, c)      # count it and sink the whole thing
    return count
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not grid or not grid[0]: return 0` | Empty grid edge case — no islands |
| `rows, cols = len(grid), len(grid[0])` | Grid dimensions for bounds checks |
| `g = [row[:] for row in grid]` | Shallow-copy each row so sinking doesn't mutate the caller's `grid` |
| `if r<0 or c<0 or r>=rows or c>=cols or g[r][c] != "1": return` | Base case — off-grid, water, or already-sunk land all stop the recursion |
| `g[r][c] = "0"` | Sink this cell — doubles as "mark visited" |
| `dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1)` | Recurse down, up, right, left — spreads the flood fill across the whole island |
| `for r ... for c ...: if g[r][c] == "1"` | Row-major scan; a standing `"1"` means an island not yet discovered |
| `count += 1; dfs(r, c)` | Tally one island, then drown it entirely so it's never counted again |
| `return count` | Total islands found |

### Step-by-step trace (canonical grid `g1`)

Starting grid (working copy `g`):

```
1 1 1 1 0
1 1 0 1 0
1 1 0 0 0
0 0 0 0 0
```

The scan hits `(0,0) = "1"` first — that's the only new island the whole scan will find, since every land cell in `g1` is 4-directionally connected. `count` becomes `1`, and `dfs(0,0)` recursively sinks the entire island in this order (down → up → right → left at each node, skipping any off-grid/water/already-sunk neighbor):

| Step | Cell sunk | Triggered from | Grid after this sink (only changed cell shown) |
| ---- | --------- | --------------- | ------------------------------------------------ |
| 1 | `(0,0)` | scan finds it, `count=1` | `(0,0) -> "0"` |
| 2 | `(1,0)` | `dfs(0,0)` → down | `(1,0) -> "0"` |
| 3 | `(2,0)` | `dfs(1,0)` → down | `(2,0) -> "0"` |
| 4 | `(2,1)` | `dfs(2,0)` → right (down/up already water or sunk) | `(2,1) -> "0"` |
| 5 | `(1,1)` | `dfs(2,1)` → up | `(1,1) -> "0"` |
| 6 | `(0,1)` | `dfs(1,1)` → up | `(0,1) -> "0"` |
| 7 | `(0,2)` | `dfs(0,1)` → right | `(0,2) -> "0"` |
| 8 | `(0,3)` | `dfs(0,2)` → right | `(0,3) -> "0"` |
| 9 | `(1,3)` | `dfs(0,3)` → down (all of `(1,3)`'s own neighbors are water/sunk, so recursion unwinds) | `(1,3) -> "0"` |

After step 9 every recursive call returns (all remaining neighbor calls hit water, off-grid, or already-sunk cells). Grid is now all `"0"`:

```
0 0 0 0 0
0 0 0 0 0
0 0 0 0 0
0 0 0 0 0
```

The outer scan continues from `(0,1)` onward but finds only `"0"`s, so no further islands are discovered. `count = 1` is returned.

### Mental model

- Think "paint bucket": land on a `"1"`, drown everything reachable from it, tally one blob.
- Sinking *is* the visited marker — no extra set needed because the grid itself tracks state.
- The outer loop only ever "discovers" the first cell of each island; the recursive `dfs` mops up the rest before the loop can see it again.
- Working on a copy `g` means the caller's original grid is untouched (important if the notebook re-uses `g1`/`g2` across multiple calls, as the tests do).

### Common confusions

- **Forgetting to copy the grid:** mutating the caller's original grid in place can corrupt later calls that reuse the same grid object.
- **Checking `g[r][c] == "1"` instead of `!= "1"` in the base case:** the guard must trigger the *stop* condition (off-grid, water, or already visited), so it's the negation.
- **Order of the 4 recursive calls doesn't affect correctness** — down/up/right/left vs. any other order still sinks the same connected component, just in a different visitation order.
- **Recursion depth:** on one giant island (e.g., all `"1"`s), the call stack can reach `O(rows × cols)` deep — this is why the notebook also gives a BFS version.

### Complexity

- **Time:** `O(rows × cols)` — every cell is visited and sunk at most once
- **Space:** `O(rows × cols)` worst case — recursion stack depth if one island spans the whole grid (plus `O(rows × cols)` for the grid copy)

---

## `num_islands_bfs` — BFS Flood Fill

### What it does

Same scan-and-sink strategy as the DFS version, but each island is drowned with an explicit queue instead of recursion. When the scan finds a standing `"1"`, it sinks that cell immediately, seeds a queue with its coordinates, then repeatedly pops a cell and sinks/enqueues any of its 4 standing neighbors — a classic BFS flood fill.

### Code

```python
from collections import deque

def num_islands_bfs(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    g = [row[:] for row in grid]
    count = 0
    for r in range(rows):
        for c in range(cols):
            if g[r][c] == "1":             # start of a new island
                count += 1
                g[r][c] = "0"; q = deque([(r, c)])   # sink it using a queue (BFS)
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < rows and 0 <= ny < cols and g[nx][ny] == "1":
                            g[nx][ny] = "0"; q.append((nx, ny))   # sink and queue neighbors
    return count
```

### Line by line

| Line / code | What it does |
| ----------- | ------------ |
| `if not grid or not grid[0]: return 0` | Empty grid edge case |
| `g = [row[:] for row in grid]` | Work on a copy, same as the DFS version |
| `for r ... for c ...: if g[r][c] == "1"` | Row-major scan for an unvisited island |
| `count += 1; g[r][c] = "0"; q = deque([(r, c)])` | Found a new island — tally it, sink the seed cell, and seed the BFS queue |
| `while q: x, y = q.popleft()` | Process cells in FIFO order — one "ring" of the island at a time |
| `for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))` | Check down, up, right, left neighbors |
| `if 0 <= nx < rows and 0 <= ny < cols and g[nx][ny] == "1"` | Neighbor must be in bounds and still standing land |
| `g[nx][ny] = "0"; q.append((nx, ny))` | Sink the neighbor immediately (before it can be enqueued twice) and queue it for expansion |
| `return count` | Total islands found |

### Step-by-step trace (canonical grid `g1`)

Same starting grid as above. The scan finds `(0,0) = "1"` first; `count` becomes `1`, `(0,0)` is sunk immediately, and `q = [(0,0)]`.

Queue shown as `[front … back]`; neighbor check order is down, up, right, left; a neighbor is sunk **the moment it's enqueued** (not when it's popped).

| Step | Pop | Neighbors checked (sunk + enqueued) | Queue after this pop |
| ---- | --- | ------------------------------------ | ---------------------- |
| 0 | — (seed) | `(0,0)` sunk before loop starts | `[(0,0)]` |
| 1 | `(0,0)` | down `(1,0)` ✓ sink+enqueue; up oob; right `(0,1)` ✓ sink+enqueue; left oob | `[(1,0), (0,1)]` |
| 2 | `(1,0)` | down `(2,0)` ✓ sink+enqueue; up `(0,0)` sunk skip; right `(1,1)` ✓ sink+enqueue; left oob | `[(0,1), (2,0), (1,1)]` |
| 3 | `(0,1)` | down `(1,1)` already sunk skip; up oob; right `(0,2)` ✓ sink+enqueue; left `(0,0)` sunk skip | `[(2,0), (1,1), (0,2)]` |
| 4 | `(2,0)` | down `(3,0)` water skip; up `(1,0)` sunk skip; right `(2,1)` ✓ sink+enqueue; left oob | `[(1,1), (0,2), (2,1)]` |
| 5 | `(1,1)` | down `(2,1)` already sunk skip; up `(0,1)` sunk skip; right `(1,2)` water skip; left `(1,0)` sunk skip | `[(0,2), (2,1)]` |
| 6 | `(0,2)` | down `(1,2)` water skip; up oob; right `(0,3)` ✓ sink+enqueue; left `(0,1)` sunk skip | `[(2,1), (0,3)]` |
| 7 | `(2,1)` | down `(3,1)` water skip; up `(1,1)` sunk skip; right `(2,2)` water skip; left `(2,0)` sunk skip | `[(0,3)]` |
| 8 | `(0,3)` | down `(1,3)` ✓ sink+enqueue; up oob; right `(0,4)` water skip; left `(0,2)` sunk skip | `[(1,3)]` |
| 9 | `(1,3)` | down `(2,3)` water skip; up `(0,3)` sunk skip; right `(1,4)` water skip; left `(1,2)` water skip | `[]` |

Queue empties after step 9 — all 9 land cells (`(0,0),(1,0),(0,1),(2,0),(1,1),(0,2),(2,1),(0,3),(1,3)`) have been sunk, matching the same island the DFS trace found (just discovered in a different order — ring-by-ring instead of depth-first). The outer scan finds no more `"1"`s. `count = 1` is returned.

### Mental model

- Same "paint bucket," but spreading outward in rings (BFS) instead of down one path first (DFS).
- Sinking happens **at enqueue time**, not at pop time — this is what prevents the same cell from being pushed onto the queue twice.
- The queue only ever holds the current "frontier" of the flood fill, so its size is bounded by the island's perimeter, not its full area.

### Common confusions

- **Sink at enqueue vs. sink at pop:** sinking when a neighbor is *discovered* (enqueued) is required here — if you waited until pop time, the same cell could be pushed onto the queue multiple times by different neighbors before it's processed.
- **BFS visitation order differs from DFS** but the **count** is identical — both are just different traversal orders over the same connected component.
- **`deque` vs. list:** using a plain list with `pop(0)` would make this `O(n)` per dequeue instead of `O(1)`; `popleft()` on `deque` keeps it efficient.

### Complexity

- **Time:** `O(rows × cols)` — every cell is visited and sunk at most once
- **Space:** `O(min(rows, cols))` typically for the queue (bounded by the island's frontier), `O(rows × cols)` worst case for a large, wide island; plus `O(rows × cols)` for the grid copy

---

## Quick reference

| Function | Technique | Islands found on `g1` | Islands found on `g2` | Time | Space |
| -------- | --------- | ---------------------- | ---------------------- | ---- | ----- |
| `num_islands_dfs` | DFS flood fill (recursion) | `1` | `3` | `O(rows·cols)` | `O(rows·cols)` recursion stack worst case |
| `num_islands_bfs` | BFS flood fill (queue) | `1` | `3` | `O(rows·cols)` | `O(min(rows,cols))` typical queue size |

## Patterns to remember

- **Flood fill counts blobs:** scan the whole grid, and each time you land on unvisited `"1"`, sink the entire connected region and add one to the count.
- **Sink-as-you-go:** overwriting visited land to `"0"` doubles as the visited marker, so no separate `visited` set is needed.
- **Signal words:** "connected regions," "islands," "groups," "blobs on a grid," "count clusters."
- **Related problems:** Max Area of Island, Surrounded Regions, Pacific Atlantic Water Flow, Number of Connected Components in an Undirected Graph.
- **Common pitfalls:** (1) recounting a region because it wasn't marked visited immediately upon discovery; (2) a very large single island overflowing the DFS call stack — prefer BFS (or an explicit stack) for huge grids; (3) sinking a neighbor at pop time instead of enqueue time in BFS, which allows duplicate queue entries.
