# 🕸️ Graph — Concept Tutorial

> A plain-language guide to the ideas behind the Blind 75 **Graph** problems, with diagrams.
> Pair this with `visualizations/Graph/` and `notebooks/Graph/`.

---

## 1. What is a Graph?

A **graph** is dots (**nodes**) joined by lines (**edges**). Edges can be **two-way** (undirected, like friendships) or **one-way** (directed, like prerequisites). A **grid** is just a graph where each cell links to its neighbors.

```mermaid
graph LR
    A((A)) --- B((B))
    B --- C((C))
    A --- C
    C --- D((D))
```

We usually store a graph as an **adjacency list** — a map from each node to the list of nodes it connects to:

```
A: [B, C]
B: [A, C]
C: [A, B, D]
D: [C]
```

**The golden rule:** always keep a **visited** set so you never loop forever.

---

## 2. DFS and BFS (with a visited set)

```mermaid
flowchart TD
    S["start node"] --> V{"visited<br/>already?"}
    V -->|yes| SKIP["skip it"]
    V -->|no| M["mark visited,<br/>then explore its neighbors"]
    M --> S
```

- **DFS** follows one path deep (recursion or a stack).
- **BFS** spreads out in rings (a queue) — best for *fewest steps*.
- Both are **O(V + E)** — every node and edge once.

**Problems:** Clone Graph (copy while walking, keep an original→copy map), Number of Islands.

---

## 3. Flood Fill (graphs on a grid)

An **island** is a connected blob of land. Scan the grid; when you hit new land, "flood fill" the whole blob (sink it so you don't recount) and add one to the count.

```mermaid
flowchart LR
    F["find unvisited land"] --> S["sink the whole connected blob<br/>(DFS/BFS to matching neighbors)"] --> C["count += 1"] --> F
```

A powerful twist: **search backwards from the goal.** For *Pacific Atlantic*, don't test every cell — start at the ocean borders and climb uphill; the cells you reach are exactly those that can drain to that ocean.

**Problems:** Number of Islands, Pacific Atlantic Water Flow.

---

## 4. Topological Sort (ordering with dependencies)

If tasks have "do X before Y" rules, a **topological order** lists them so every arrow points forward. **Kahn's method:** repeatedly take a node with **no remaining prerequisites**, output it, and remove its outgoing arrows.

```mermaid
graph LR
    C0["course 0"] --> C1["course 1"]
    C0 --> C2["course 2"]
    C1 --> C3["course 3"]
    C2 --> C3
    C3 --> C4["course 4"]
```

```mermaid
flowchart TD
    Z["take a node with 0 prerequisites"] --> O["output it"]
    O --> R["remove its arrows<br/>(lower neighbors' counts)"]
    R --> Q{"any node left<br/>with 0 prereqs?"}
    Q -->|yes| Z
    Q -->|"no, but nodes remain"| CYC["there is a CYCLE ❌<br/>(impossible to order)"]
    Q -->|"all placed"| OK["valid order ✅"]
```

**The tell:** *prerequisites*, *dependencies*, *ordering*, *"can it be scheduled?"*
**Problems:** Course Schedule, Alien Dictionary (letter-order clues → arrows → topo sort).

---

## 5. Union-Find (merging groups)

**Union-Find** tracks which items are in the same group. `find(x)` returns x's group leader; `union(a, b)` merges two groups. Joining two nodes that are **already** together reveals a **cycle**.

```mermaid
flowchart LR
    subgraph "start: everyone alone"
      a0((0)) 
      b0((1))
      c0((2))
      d0((3))
    end
```

```mermaid
flowchart TD
    E["for each edge (a,b)"] --> Q{"same group<br/>already?"}
    Q -->|yes| CYC["cycle found (or skip)"]
    Q -->|no| U["union them,<br/>group count − 1"]
    U --> E
```

- **Count components:** start at `n` groups, subtract one per merging edge.
- **Valid tree:** exactly `n−1` edges **and** no cycle **and** all connected.

**Problems:** Number of Connected Components, Graph Valid Tree.

---

## 6. A Set Can Be a Graph

Some problems have **implicit** edges. In *Longest Consecutive Sequence*, the numbers 1-2-3-4 form an invisible chain. Put everything in a set and only start counting a run where its predecessor is missing.

```mermaid
flowchart LR
    n100["100"]
    n4["4"] --- n3?["is 3 present?"]
    subgraph "run grown from its start"
      one["1"] --> two["2"] --> three["3"] --> four["4"]
    end
```

**Problems:** Longest Consecutive Sequence.

---

## 7. Which Pattern for Which Problem?

```mermaid
mindmap
  root((Graph))
    DFS / BFS + visited
      Clone Graph
      Number of Islands
    Flood fill on grid
      Number of Islands
      Pacific Atlantic
    Topological sort
      Course Schedule
      Alien Dictionary
    Union-Find
      Connected Components
      Graph Valid Tree
    Implicit graph / set
      Longest Consecutive Sequence
```

---

## 8. Complexity Cheat Sheet

| Pattern          | Time                | Space               |
| ---------------- | ------------------- | ------------------- |
| DFS / BFS        | `O(V + E)`        | `O(V)`            |
| Flood fill       | `O(rows × cols)` | `O(rows × cols)` |
| Topological sort | `O(V + E)`        | `O(V + E)`        |
| Union-Find       | ~`O(V + E)`       | `O(V)`            |

---

## 9. Interview Playbook

1. **Name the graph:** what are the nodes and edges? Directed? A grid in disguise?
2. **Spot the tell:** reach/copy/connected → *DFS/BFS + visited*; grid regions → *flood fill*; dependencies/order → *topological sort*; count groups / detect cycles → *Union-Find*.
3. **Always track visited** so you never loop, and state the cost (most graph walks are `O(V + E)`).
4. **Mind the edges:** disconnected pieces, isolated nodes, empty graph, cycles.

> ▶ **Next:** open `visualizations/Graph/index.html` to watch traversal, topo sort, and union-find animate.
