# Tries — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problem that uses a trie (5 — Middleware Router).

**Corresponds to README.md sections:**
- §1 — the idea (letters/segments on edges)
- §2 — the node + insert/search/starts_with operations
- §3 — why a trie beats a hash set for prefixes
- ~~§4~~ — radix-tree compression — not needed here
- ~~§5~~ — use-case list — not needed here — see the full tutorial if you want them

---

- **The core idea:** a tree keyed by "the next unit of the key" (segments here, not characters) — shared prefixes share nodes, and a flag on a node marks "something terminates here."
- **Why a trie beats a flat dict for this problem:** a hash map (`RouterNaive`'s flat `dict`) gives O(1) exact lookup but has no way to represent "matches any single segment here" (a wildcard) — a trie's per-node branching is what makes that expressible at all. This is the exact reasoning behind Middleware Router's Approach 1 → Approach 2 progression.
- You don't need radix-tree compression or the autocomplete/IP-routing use-case list for this problem.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for radix-tree compression and other use cases.
