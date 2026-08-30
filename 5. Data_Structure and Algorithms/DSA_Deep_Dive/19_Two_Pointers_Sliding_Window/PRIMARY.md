# Two Pointers & Sliding Window — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problems that use this technique (7 — CI/CD Jobs, and the `max_overlap` sanity-check helper in 13 — Tennis Club).

**Corresponds to README.md sections:**
- §4 — Event/sweep-line (the only section you need)
- ~~§1~~ — opposite-ends two pointers — not used in these 13 problems
- ~~§2~~ — sliding window — not used in these 13 problems
- ~~§3~~ — fast/slow pointers — not used in these 13 problems — see the full tutorial if you want them

---

- Only the **event / sweep-line** variant is used — not opposite-ends two pointers, not sliding window, not fast/slow pointers.
- **The pattern:** turn each interval into a `(start, +1)` / `(end, -1)` event pair, sort all events by time, sweep through keeping a running "how many active right now" counter.
  ```python
  events = [(s, 1) for s, e in intervals] + [(e, -1) for s, e in intervals]
  events.sort(key=lambda ev: (ev[0], -ev[1]))   # tie-break controls whether touching counts as overlap
  ```
- The tie-break rule (`-ev[1]` vs `ev[1]`) is what decides whether touching endpoints count as overlapping — get this backwards and your answer for boundary cases flips.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for opposite-ends two pointers, sliding window, and fast/slow pointers.
