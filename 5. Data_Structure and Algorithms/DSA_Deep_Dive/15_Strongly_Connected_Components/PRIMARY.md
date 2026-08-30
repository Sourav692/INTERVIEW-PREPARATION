# Strongly Connected Components — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problem that uses SCCs (9 — Confluence Page Link Graph).

**Corresponds to README.md sections:**
- §1 — What "strongly connected" means + condensation
- §3 — Tarjan's algorithm
- ~~§2~~ — Kosaraju's algorithm — not needed here
- ~~§4~~ — Kosaraju vs Tarjan comparison — not needed here — see the full tutorial if you want them

---

- **What an SCC is:** a maximal group of vertices where every one can reach every other one — that's the literal definition of what `find_cycles` returns (any SCC of size > 1 is a genuine multi-page cycle).
- **Tarjan's algorithm specifically** (not Kosaraju's) is what's implemented: one DFS pass, tracking `disc`/`low` per vertex and a stack of "currently open" vertices; `low[v] == disc[v]` marks the root of a finished SCC, popped off the stack.
- You don't need Kosaraju's two-pass alternative to solve this problem — it's a valid different way to get the same answer, not a prerequisite.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for Kosaraju's algorithm.
