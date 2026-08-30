# Content Popularity Tracker — Explained Simply

## The Problem

Track content popularity as thumbs-up (+1) / thumbs-down (-1) come in. `mostPopular()` must instantly return the ID with the highest score.

```
increasePopularity(1)   # score[1] = 1
increasePopularity(1)   # score[1] = 2
increasePopularity(2)   # score[2] = 1
mostPopular()            # -> 1 (score 2)
increasePopularity(2)
increasePopularity(2)   # score[2] = 3
mostPopular()            # -> 2 (score 3, now the leader)
```

## Why the Obvious Way Is Slow

The obvious approach: a plain dict of `id -> score`. Updates are instant, but `mostPopular()` has to scan **every single ID** to find the current max:

```
def most_popular_naive():
    return max(scores, key=scores.get)   # O(n) — must check everyone, every time
```

If `mostPopular()` is called often (as it usually is — that's the whole point of tracking popularity), you're paying O(n) again and again for a question whose answer barely changes between calls.

## The Simple Trick: Group IDs by Their Current Score

The key fact this problem hands you for free: **scores only ever move by exactly 1**. That means you can organize IDs into labeled bins — one bin per score value — and just remember which occupied bin is currently the highest. Moving an ID when its score changes is just "take it out of one bin, drop it into the neighboring bin" — no searching required.

## An Analogy First: A Leaderboard Made of Physical Shelves

Imagine a wall of shelves, one shelf per possible score (0, 1, 2, 3, ...), and each shelf holds name-tags for everyone currently at that score. There's also a sticky note on the wall marking "the highest occupied shelf."

When someone gets a thumbs-up, you don't rescan the whole wall — you just peel their name-tag off shelf `s` and stick it on shelf `s+1`. If that's now a new record height, move the sticky note up. `mostPopular()` never searches anything — it just reads whatever name-tag is sitting on the shelf the sticky note points to.

The only mildly clever part: what if a thumbs-*down* empties out the shelf the sticky note is pointing at? Then you slide the sticky note down, one shelf at a time, until you find a shelf that still has name-tags on it.

## Step-by-Step Example (Narrated)

Sequence: `inc(1)`, `inc(1)`, `inc(2)`, `dec(1)`, `dec(1)`.

We track: `score[id]`, `buckets[s] = {ids at score s}`, and `max_score` (the sticky note).

---

**`inc(1)`** — id 1 currently has no score (treated as 0). New score = 1.
Remove 1 from bucket 0 (it wasn't there, no-op). Add 1 to bucket 1.
`buckets = {1: {1}}`. Is 1 > current max_score (0)? Yes → `max_score = 1`.

---

**`inc(1)`** — id 1's old score is 1. New score = 2.
Remove 1 from bucket 1 → bucket 1 is now empty, delete it. Add 1 to bucket 2.
`buckets = {2: {1}}`. Is 2 > max_score (1)? Yes → `max_score = 2`.

---

**`inc(2)`** — id 2's old score is 0 (never seen). New score = 1.
Add 2 to bucket 1 (bucket 1 is recreated). `buckets = {1: {2}, 2: {1}}`.
Is 1 > max_score (2)? No → max_score stays 2. `mostPopular()` right now would read bucket 2 → returns **id 1** (score 2, still the leader).

---

**`dec(1)`** — id 1's old score is 2. New score = 1.
Remove 1 from bucket 2 → bucket 2 is now **empty**, delete it. Add 1 to bucket 1.
`buckets = {1: {1, 2}}`.
Here's the special case: the bucket we just emptied (2) **was** `max_score`. So we walk `max_score` down: is 2 still in `buckets`? No → step down to 1. Is 1 in `buckets`? Yes → stop. `max_score = 1`.
`mostPopular()` now reads bucket 1 → returns either id (both tied at score 1 — the problem allows any).

---

**`dec(1)`** — id 1's old score is 1. New score = 0.
Remove 1 from bucket 1 → bucket 1 still has `{2}` left (not empty, keep it). Add 1 to bucket 0.
`buckets = {0: {1}, 1: {2}}`.
Was the bucket we removed from (`1`) equal to `max_score` (`1`)? Yes, but is it now empty? **No** — id 2 is still there. So we do **not** walk the pointer down. `max_score` stays 1.
`mostPopular()` reads bucket 1 → returns **id 2** (score 1), correctly still the leader.

### The one detail that's easy to miss: only walk down when the bucket is truly empty

The walk-down step only triggers when the bucket you just vacated is the *current max* **and** it's now completely empty. If someone else is still sitting in that bucket (like id 2 in the last step), the max hasn't actually changed — don't touch the pointer.

## Plain-English Walkthrough

1. Keep `score[id]`, `buckets[s] = set of ids at score s`, and `max_score`.
2. On increase: move the id from its old bucket to `old+1`. If `old+1 > max_score`, update `max_score`.
3. On decrease: move the id from its old bucket to `old-1`. If the old bucket is now empty **and** it was `max_score`, walk `max_score` down one step at a time until you find a non-empty bucket.
4. `mostPopular()`: return any id from `buckets[max_score]`.

## Simple Python Code

```python
class ContentPopularity:
    def __init__(self):
        self.score = {}
        self.buckets = {}
        self.max_score = 0

    def _move(self, cid, old, new):
        if old in self.buckets:
            self.buckets[old].discard(cid)
            if not self.buckets[old]:
                del self.buckets[old]
        self.buckets.setdefault(new, set()).add(cid)
        self.score[cid] = new

    def increasePopularity(self, cid):
        old = self.score.get(cid, 0)
        self._move(cid, old, old + 1)
        self.max_score = max(self.max_score, old + 1)

    def decreasePopularity(self, cid):
        if cid not in self.score:
            return
        old = self.score[cid]
        self._move(cid, old, old - 1)
        if old == self.max_score and old not in self.buckets:
            while self.max_score not in self.buckets:
                self.max_score -= 1

    def mostPopular(self):
        if not self.buckets:
            return -1
        return next(iter(self.buckets[self.max_score]))
```

## Why Not Just Use a Heap?

A heap gives you fast access to the current max, but it has no fast way to **change** an existing entry's score or remove an arbitrary one — only push and pop the extreme. A score that decreases would need a full rebuild or "lazy deletion" tricks, reintroducing the scan you were trying to avoid. The bucket approach sidesteps this entirely by exploiting that scores only ever move by exactly 1.

## Complexity

- **Time:** O(1) for `increasePopularity` and `mostPopular`. `decreasePopularity`'s walk-down is **amortized** O(1): since `_move` deletes a bucket the instant it's empty, `buckets` never has gaps — so the walk-down always finds the next bucket (`old - 1`) already occupied and stops after exactly one step.
- **Space:** O(n) — one entry per distinct id.

## The Reusable Pattern

This is the **"bucket by value"** pattern — used whenever values change in small, predictable steps:
- LeetCode's "All O`one Data Structure" (this problem's direct ancestor)
- LFU cache (bucket by access frequency)
- Bucket sort / counting sort

Core idea: instead of asking "what's the max?" by searching, keep the answer updated as a side effect of every change — and only do extra work in proportion to how far the answer actually needs to move.
