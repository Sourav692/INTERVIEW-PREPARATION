# Graph Representation — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problem that uses graph representation (9 — Confluence Page Link Graph).

**Corresponds to README.md sections:**
- §2 — The adjacency list
- §3 — Head-to-head comparison (just enough to justify "list over matrix")
- ~~§1~~ — adjacency matrix — not needed here
- ~~§4~~ — edge list — not needed here — see the full tutorial if you want them

---

- **Adjacency list only** — `dict[node] -> list[neighbors]`. The adjacency matrix and edge-list representations are never used.
- **The one design decision that matters:** Confluence Page Link Graph keeps **both** a forward map (`out_adj`) and a reverse map (`in_adj`) side by side, so `get_inbound` doesn't need an O(V+E) scan — this is a deliberate space-for-speed trade, worth being able to explain out loud.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for the adjacency matrix and edge-list representations.
