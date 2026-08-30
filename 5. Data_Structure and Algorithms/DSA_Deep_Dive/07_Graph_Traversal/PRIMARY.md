# Graph Traversal (BFS & DFS) — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problem that uses graph traversal (9 — Confluence Page Link Graph).

**Corresponds to README.md sections:**
- §1 — The visited set
- §2 — BFS
- §3 — DFS (needed as the rejected-approach comparison)
- §4 — BFS vs DFS table
- ~~§5~~ — the extended toolbox (connected components, cycle detection, topological sort, bipartite check) — not needed here — see the full tutorial if you want it

---

- **The visited set** (or a `parent` map that doubles as one) is what keeps traversal from looping forever on a cyclic graph — non-negotiable.
- **BFS with a parent map** finds a **shortest** path on an unweighted graph, and lets you reconstruct that path by walking `parent` backward from the target. This is `find_path`'s actual implementation.
- **Know the one-line reason BFS beats DFS here:** "BFS explores in order of distance, so the first time it reaches the target is guaranteed shortest; DFS just finds *a* path, with no length guarantee." (The problem's own naive DFS approach exists specifically to make this comparison concrete.)
- You don't need connected-components counting, cycle detection via DFS, topological sort, or bipartite checking for this problem — those are extensions the tutorial covers, not things this problem asks for.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for connected components, cycle detection, topological sort, and bipartite checking.
