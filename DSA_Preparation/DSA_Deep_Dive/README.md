

# 🌳 DSA Deep Dive

Intuitive, diagram-driven tutorials. The **Trees** track builds from the most general tree to the specialised ones,
then the traversals that tie them together. The **Graphs** track generalises all of it — vertices, edges, how to store
them, and how to walk them. Read each track in order.

## 🌲 Trees

| # | Tutorial                                      | What you'll learn                                                                              | Interactive HTML                          |
| - | --------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------- |
| 1 | [Generic (N-ary) Tree](01_Generic_Tree/README.md)     | tree vocabulary, depth vs height, representations,`{id, parent_id}`, DFS/BFS                 | [open](01_Generic_Tree/01_generic_tree.html)       |
| 2 | [Binary Tree](02_Binary_Tree/README.md)               | left/right children, full/complete/perfect/balanced/skewed, array packing, diameter            | [open](02_Binary_Tree/02_binary_tree.html)        |
| 3 | [Binary Search Tree](03_Binary_Search_Tree/README.md) | the BST invariant, search/insert/delete, validate, balance & self-balancing                    | [open](03_Binary_Search_Tree/03_binary_search_tree.html) |
| 4 | [Tree Traversal](04_Tree_Traversal/README.md)         | pre / in / post / level order, recursive + iterative, when to use each, reconstruction, Morris | [open](04_Tree_Traversal/04_tree_traversal.html)     |

## 🧱 Specialized Structures

| # | Tutorial | What you'll learn | Interactive HTML |
|---|---|---|---|
| 12 | [Heaps & Priority Queues](12_Heaps_Priority_Queues/README.md) | complete-tree-in-an-array, sift up/down, `O(n)` heapify, `heapq`, top-K, two-heap median | [open](12_Heaps_Priority_Queues/12_heaps_priority_queues.html) |
| 13 | [Tries (Prefix Trees)](13_Tries/README.md) | char-keyed tree, `O(L)` insert/search/prefix, autocomplete, vs hash set, radix trees | [open](13_Tries/13_tries.html) |

## 🕸️ Graphs

| # | Tutorial                                          | What you'll learn                                                                         | Interactive HTML                            |
| - | ------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------- |
| 5 | [Graph Fundamentals](05_Graph_Fundamentals/README.md)     | vertices & edges, terminology, directed/weighted/DAG/bipartite, sparse vs dense           | [open](05_Graph_Fundamentals/05_graph_fundamentals.html)   |
| 6 | [Graph Representation](06_Graph_Representation/README.md) | adjacency**matrix** vs **list** (+ edge list), the full space/time comparison | [open](06_Graph_Representation/06_graph_representation.html) |
| 7 | [Graph Traversal](07_Graph_Traversal/README.md)           | BFS & DFS, the visited set, shortest path, components, what each unlocks                  | [open](07_Graph_Traversal/07_graph_traversal.html)      |

## ⚙️ Advanced Graph Algorithms

| # | Tutorial | What you'll learn | Interactive HTML |
|---|---|---|---|
| 8 | [Weighted Shortest Paths](08_Weighted_Shortest_Paths/README.md) | relaxation, **Dijkstra** (non-negative), **Bellman-Ford** (negatives + negative-cycle detection), A*/Floyd-Warshall | [open](08_Weighted_Shortest_Paths/08_weighted_shortest_paths.html) |
| 9 | [Minimum Spanning Tree](09_Minimum_Spanning_Tree/README.md) | spanning trees, the cut property, **Union-Find**, **Kruskal** & **Prim** | [open](09_Minimum_Spanning_Tree/09_minimum_spanning_tree.html) |
| 10 | [Topological Sort](10_Topological_Sort/README.md) | ordering a DAG, **Kahn's** (BFS) & **DFS** methods, cycle detection as a byproduct | [open](10_Topological_Sort/10_topological_sort.html) |
| 11 | [Cycle Detection](11_Cycle_Detection/README.md) | undirected (parent rule / Union-Find) vs directed (**3-colour DFS** / Kahn's) | [open](11_Cycle_Detection/11_cycle_detection.html) |
| 14 | [A* & Floyd-Warshall](14_AStar_Floyd_Warshall/README.md) | **A\*** (`f=g+h`, admissible heuristics) and **Floyd-Warshall** all-pairs shortest paths | [open](14_AStar_Floyd_Warshall/14_astar_floyd_warshall.html) |
| 15 | [Strongly Connected Components](15_Strongly_Connected_Components/README.md) | **Kosaraju** (2-pass) & **Tarjan** (low-link), condensation to a DAG, 2-SAT | [open](15_Strongly_Connected_Components/15_strongly_connected_components.html) |

## 🐍 Runnable notebooks

Every tutorial has a matching Jupyter notebook right alongside it in its topic folder, that **builds and demonstrates**
each concept in plain Python — self-explanatory comments, printed output, and `assert` checks so you can see it work.
All cells run top-to-bottom with the standard library only (no installs).

| Tutorial             | Notebook                                                                       |
| -------------------- | ------------------------------------------------------------------------------ |
| Generic Tree         | [`01_generic_tree.ipynb`](01_Generic_Tree/01_generic_tree.ipynb)                 |
| Binary Tree          | [`02_binary_tree.ipynb`](02_Binary_Tree/02_binary_tree.ipynb)                   |
| Binary Search Tree   | [`03_binary_search_tree.ipynb`](03_Binary_Search_Tree/03_binary_search_tree.ipynb)     |
| Tree Traversal       | [`04_tree_traversal.ipynb`](04_Tree_Traversal/04_tree_traversal.ipynb)             |
| Graph Fundamentals   | [`05_graph_fundamentals.ipynb`](05_Graph_Fundamentals/05_graph_fundamentals.ipynb)     |
| Graph Representation | [`06_graph_representation.ipynb`](06_Graph_Representation/06_graph_representation.ipynb) |
| Graph Traversal      | [`07_graph_traversal.ipynb`](07_Graph_Traversal/07_graph_traversal.ipynb)           |

**Specialized structures:** [`12_heaps_priority_queues.ipynb`](12_Heaps_Priority_Queues/12_heaps_priority_queues.ipynb) ·
[`13_tries.ipynb`](13_Tries/13_tries.ipynb)

**Advanced graph algorithms:** [`08_weighted_shortest_paths.ipynb`](08_Weighted_Shortest_Paths/08_weighted_shortest_paths.ipynb) ·
[`09_minimum_spanning_tree.ipynb`](09_Minimum_Spanning_Tree/09_minimum_spanning_tree.ipynb) ·
[`10_topological_sort.ipynb`](10_Topological_Sort/10_topological_sort.ipynb) ·
[`11_cycle_detection.ipynb`](11_Cycle_Detection/11_cycle_detection.ipynb) ·
[`14_astar_floyd_warshall.ipynb`](14_AStar_Floyd_Warshall/14_astar_floyd_warshall.ipynb) ·
[`15_strongly_connected_components.ipynb`](15_Strongly_Connected_Components/15_strongly_connected_components.ipynb)

Run one with `jupyter notebook 01_Generic_Tree/01_generic_tree.ipynb`.

## How to use

Three views of the same material — pick what suits the moment:

- **📄 Read the markdown** for the concepts and mermaid diagrams (they render on GitHub / VS Code).
- **🐍 Run the notebook** to build each structure yourself and watch it work (see the table above).
- **🖥️ Open the matching HTML** (`index.html`) for **interactive, step-through animations** — walk a
  traversal node by node, watch a BST search halve the tree, and more. Everything runs **offline**.

## The through-line

Each topic is the one before it **with a rule added or dropped** — so the whole series is really one idea, refined
step by step:

```mermaid
flowchart TD
    subgraph TREES [" 🌲 Trees "]
        direction TB
        GT["<b>Generic (N-ary) Tree</b><br/>any number of children"]
        BT["<b>Binary Tree</b><br/>at most 2, ordered L / R"]
        BST["<b>Binary Search Tree</b><br/>left < node < right"]
        GT -->|"restrict to ≤ 2 ordered children"| BT
        BT -->|"add the ordering rule"| BST
    end

    TREES ==>|"drop 'one parent, no cycles'"| G["<b>🕸️ Graph</b><br/>vertices + edges"]
    G -->|"store it as"| REP["<b>🗺️ Adjacency Matrix / List</b>"]
    G -->|"walk it with"| TRAV["<b>🧭 Traversals</b><br/>DFS · BFS"]

    classDef tree fill:#e5edff,stroke:#3563e9,color:#1c2230;
    classDef graph fill:#dcfce7,stroke:#2f9e52,color:#1c2230;
    class GT,BT,BST tree;
    class G,REP,TRAV graph;
```

**How to read it:** start at the most general tree and *add* rules to get the specialised ones; *drop* the defining
tree rules ("one parent, no cycles") and a tree becomes a **graph**. A graph then needs a way to be **stored**
(matrix / list) and **walked** (DFS / BFS) — and every "how do I visit the nodes?" question lands in a **Traversal**
chapter.
