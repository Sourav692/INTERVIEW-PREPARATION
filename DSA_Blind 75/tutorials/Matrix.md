# 🔲 Matrix — Concept Tutorial

> A plain-language guide to the ideas behind the Blind 75 **Matrix** problems, with diagrams.
> Pair this with `visualizations/Matrix/` and `notebooks/Matrix/`.

---

## 1. What is a Matrix?

A **matrix** is a grid — a list of rows, each a list of values. You address a cell by `(row, col)`.

```mermaid
flowchart LR
    subgraph "row 0"
      a["(0,0) 1"] --- b["(0,1) 2"] --- c["(0,2) 3"]
    end
    subgraph "row 1"
      d["(1,0) 4"] --- e["(1,1) 5"] --- f["(1,2) 6"]
    end
```

A cell's four neighbors are `(r±1, c)` and `(r, c±1)`.

---

## 2. Pattern A — In-Place Grid Tricks (O(1) space)

Rearrange a grid using **itself** as scratch paper.

**Set Matrix Zeroes:** if a cell is 0, its whole row and column become 0. Instead of separate sets, store the flags in the **first row and column**.

```mermaid
flowchart TD
    P1["pass 1: for each 0 cell,<br/>mark its row & column in the borders"] --> P2["pass 2: zero any cell whose<br/>row/col marker is set"] --> P3["handle the first row/col last"]
```

**Rotate Image (90° clockwise):** two elementary moves — **transpose** (swap `[i][j]`↔`[j][i]`), then **reverse each row**.

```mermaid
flowchart LR
    A["original"] --> T["transpose<br/>(rows ↔ columns)"] --> R["reverse each row"] --> D["rotated 90° ✅"]
```

**Problems:** Set Matrix Zeroes, Rotate Image.

---

## 3. Pattern B — Boundary Walking (Spiral)

A spiral is the four outer edges repeated on an ever-smaller rectangle. Track `top / bottom / left / right` limits and shrink them.

```mermaid
flowchart TD
    T["trace TOP row →"] --> R["trace RIGHT column ↓"]
    R --> B["trace BOTTOM row ←"]
    B --> L["trace LEFT column ↑"]
    L --> S["shrink all four limits"]
    S --> Q{"limits crossed?"}
    Q -->|no| T
    Q -->|yes| DONE["done ✅"]
```

**Problems:** Spiral Matrix.

---

## 4. Pattern C — Grid Backtracking (Word Search)

A word is a path of adjacent cells. From each matching first letter, DFS to neighbors matching the next letter — **mark** the current cell used so a path can't reuse it, and **restore** it when you back out.

```mermaid
flowchart TD
    M["letter matches?"] -->|no| FAIL["dead end, return false"]
    M -->|yes| USE["mark cell used"]
    USE --> EXP["explore 4 neighbors for the next letter"]
    EXP --> RES["restore the cell (backtrack)"]
```

```mermaid
graph LR
    A["A"] --> B["B"] --> C["C"] --> C2["C"] --> E["E"] --> D["D"]
```
*A path spelling "ABCCED".*

**Problems:** Word Search. (Word Search II adds a **trie** — see the Tree tutorial.)

---

## 5. Which Pattern for Which Problem?

```mermaid
mindmap
  root((Matrix))
    In-place tricks
      Set Matrix Zeroes
      Rotate Image
    Boundary walking
      Spiral Matrix
    Grid backtracking
      Word Search
```

---

## 6. Complexity Cheat Sheet

| Pattern | Time | Space |
|---|---|---|
| In-place transform | `O(m × n)` | `O(1)` |
| Spiral traversal | `O(m × n)` | `O(1)` |
| Word search (DFS) | `O(m × n × 4ᴸ)` | `O(L)` |

---

## 7. Interview Playbook

1. **Fix your coordinates:** `(row, col)`, neighbors, and how transpose maps `[i][j] ↔ [j][i]`.
2. **Ask for O(1) space:** can the grid store its own flags, or can moves compose (transpose + reverse)?
3. **For traversal, track boundaries;** for path search, **backtrack** (mark / restore).
4. **Mind the edges:** single row/column, non-square grids, empty grid.

> ▶ **Next:** open `visualizations/Matrix/index.html` to watch spirals trace and grids rotate.
