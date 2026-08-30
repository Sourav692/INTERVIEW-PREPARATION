# Hash Tables — Primary (Atlassian Prep)

The trimmed version of [`README.md`](README.md) — only what's needed to solve the `Atlassian_Prep/` problems that use hash maps/sets (1, 2, 3, 4, 6, 8, 9, 10, 11, 12).

**Corresponds to README.md sections:**
- §5 — Hash Map vs Hash Set
- §6 — Python's `dict`/`set`
- §7 — Where hash tables shine
- §1 — worth a skim for context (optional)
- ~~§2–§4~~ — hashing mechanics, collisions, load factor/resizing: internals you never touch when using Python's `dict` — see the full tutorial if you want that depth

---

- **Map vs. Set:** reach for `dict` when you need a value attached to a key; reach for `set` when you only need "have I seen this?" membership.
- **Python's toolkit, not the internals:** `dict.get(key, default)`, `collections.defaultdict(int)` / `defaultdict(list)` (auto-creates missing keys), `collections.Counter` (frequency counting + `.most_common()`).
- **The four patterns that actually appear:**
  - **Complement lookup** — "have I seen `target - x` before?" (turns an O(n²) scan into O(n)).
  - **Frequency counting** — `Counter` for tallying occurrences.
  - **Grouping** — `defaultdict(list)` to bucket items by a derived key (e.g. group prices by timestamp, group files by collection).
  - **Memoization** — cache `key -> result` so repeated lookups are O(1) instead of recomputed.
- You never need to know *why* it's O(1) average to write any of these solutions — just that it is.

**Next:** back to [`../../Atlassian_Prep/DSA_Study_Guide.md`](../../Atlassian_Prep/DSA_Study_Guide.md), or the [full tutorial](README.md) for hashing internals.
