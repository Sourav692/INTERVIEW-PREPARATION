# Greedy Algorithms & Amortized Analysis — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problems that use greedy/amortized reasoning (3 — Content Popularity Tracker, 13 — Tennis Club).

**Corresponds to README.md sections:**
- §1 — the exchange argument (read the concept, skip the coin-change worked example)
- §3 — Interval partitioning
- §4 — Amortized analysis
- ~~§2~~ — interval scheduling (max non-overlapping) — a different problem shape than Tennis Club's partitioning; not needed — see the full tutorial if you want it

---

- **Interval partitioning** (Tennis Club): sort by **start time**, keep a **min-heap of resource-availability times**; reuse the earliest-freeing resource if it's already free, otherwise open a new one. Min resources needed = max simultaneous overlap.
- **The exchange argument**, in one sentence: a greedy choice is provably safe if you can always swap it into *any* optimal solution without making that solution worse. This is the actual justification behind "always reuse the earliest-freeing court."
- **Amortized analysis**, in one sentence: a single call can look expensive, but if the *total* cost across a whole sequence of calls is bounded, the average cost per call is small. This is exactly the justification for Content Popularity Tracker's `max_score` walk-down loop (each score value can only be vacated once, ever — so the walking work sums to O(N) across N calls, not O(N) *per* call).
- You do **not** need the coin-change-fails counterexample or the formal aggregate/accounting proof methods to solve either problem — those are there to deepen understanding, not required.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for interval scheduling and the formal amortized-analysis proof methods.
