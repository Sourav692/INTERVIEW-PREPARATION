# Content Popularity Tracker

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Hash Tables, Heaps · **Difficulty/Frequency:** Very Common (8/10)

---

## Problem Statement

**Content Popularity Tracking System**

Implement a system to track the popularity of content based on user interactions (thumbs up or thumbs down).

Design an interface called `ContentPopularity` with the following methods:

- `increasePopularity(contentId: int) -> None` — Increases the popularity of the specified content ID by one (represents a thumbs up).
- `decreasePopularity(contentId: int) -> None` — Decreases the popularity of the specified content ID by one (represents a thumbs down).
- `mostPopular() -> int` — Returns the content ID with the highest popularity. If there are ties, return any one of them. Return `-1` if no content exists.

---

## Study Tools

### Hint 1

Maintain a running maximum so `mostPopular()` doesn't scan every content ID on each call. The challenge is updating that maximum efficiently when the current leader gets a thumbs down.

### Hint 2

Keep a hash map from popularity score to the set of content IDs currently at that score, plus a hash map from content ID to its current score. When a score changes, move the ID between sets.

### Hint 3

Track the current maximum score as a variable. On `decreasePopularity`, if the set for the old max becomes empty, walk the max score down until you find a non-empty set.

---

### Answer

This is a frequency-tracking problem where `mostPopular()` needs O(1) access to the current maximum. Use a hash map `score` mapping content ID to its current popularity, a hash map `buckets` mapping a popularity value to the set of IDs at that value, and a variable `max_score` tracking the highest non-empty bucket. `increasePopularity` and `decreasePopularity` move an ID between adjacent buckets in O(1), and `mostPopular()` returns any ID from `buckets[max_score]` in O(1).

```python
class ContentPopularity:
    def __init__(self):
        self.score = {}       # contentId -> current popularity
        self.buckets = {}     # popularity -> set of contentIds at that popularity
        self.max_score = 0    # highest non-empty popularity bucket

    def _move(self, content_id, old_score, new_score):
        """Move content_id from old_score bucket to new_score bucket."""
        # Remove from old bucket
        if old_score in self.buckets:
            self.buckets[old_score].discard(content_id)
            if not self.buckets[old_score]:
                del self.buckets[old_score]
        # Add to new bucket
        if new_score not in self.buckets:
            self.buckets[new_score] = set()
        self.buckets[new_score].add(content_id)
        self.score[content_id] = new_score

    def increasePopularity(self, contentId: int) -> None:
        old_score = self.score.get(contentId, 0)
        new_score = old_score + 1
        self._move(contentId, old_score, new_score)
        if new_score > self.max_score:
            self.max_score = new_score

    def decreasePopularity(self, contentId: int) -> None:
        if contentId not in self.score:
            return  # Or handle as a no-op; content with no interactions stays at 0
        old_score = self.score[contentId]
        new_score = old_score - 1
        self._move(contentId, old_score, new_score)
        # If the old max bucket is now empty, walk down to find the new max
        if old_score == self.max_score and old_score not in self.buckets:
            while self.max_score > 0 and self.max_score not in self.buckets:
                self.max_score -= 1

    def mostPopular(self) -> int:
        if not self.buckets or self.max_score not in self.buckets:
            return -1
        # Return any ID from the max bucket
        return next(iter(self.buckets[self.max_score]))
```

**Time:** O(1) for all three operations — hash map lookups and set insertions/deletions are amortized O(1), and the while loop in `decreasePopularity` walks down at most as many scores as have ever existed, but each score value is vacated at most once, so it's amortized O(1) per operation.

**Space:** O(n) where n is the number of distinct content IDs — the `score` map stores one entry per ID, and `buckets` stores each ID exactly once across all sets.

**Correctness:** The invariant is that `buckets[s]` contains exactly the IDs with `score == s`, and `max_score` equals the largest `s` with a non-empty bucket. `increasePopularity` preserves the invariant and correctly updates `max_score` upward when the new score exceeds it. `decreasePopularity` preserves the invariant and, when the old max bucket becomes empty, walks `max_score` down to the next non-empty bucket. `mostPopular` then returns an arbitrary ID from that bucket, satisfying the tie-breaking requirement.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive approach: keep a `Counter` from content ID to score, and have `mostPopular()` scan all entries to find the max. That's O(1) for updates but O(n) for `mostPopular()`, which is bad if queries are frequent. The bottleneck is the linear scan for the max.

To speed up `mostPopular()`, you need to know the max without scanning. One idea: maintain a max-heap keyed by score. But `increasePopularity`/`decreasePopularity` would need to update heap entries, and Python's `heapq` doesn't support efficient arbitrary updates — you'd have to push duplicates and lazily discard stale entries, which complicates tie-breaking and can degrade to O(n log n) per query in the worst case.

So step back. The scores are integers, and each update changes a score by exactly ±1. That suggests bucketing: group content IDs by their current score. If you keep a hash map from score to a set of IDs, moving an ID from score `s` to `s+1` is just a set removal and a set insertion — both O(1). And if you track the current maximum score as a separate variable, `mostPopular()` is just a lookup in the max bucket.

The only tricky part is `decreasePopularity` when the ID being decremented was the sole occupant of the max bucket. If that bucket becomes empty, the new max is the next non-empty score below it. Since scores only change by 1, you can walk `max_score` down until you hit a non-empty bucket. Each score value gets vacated at most once, so across all operations this walking costs O(total distinct scores) — amortized O(1) per operation.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Name the amortized analysis** — The while loop in `decreasePopularity` looks like it could be O(n) per call, but each score value is vacated at most once, so the total work across all operations is bounded by the number of distinct scores ever seen. Saying this out loud shows you understand the difference between worst-case per operation and amortized cost.
- **Justify the data structure choice** — Explain why a heap fails here: arbitrary score updates require lazy deletion, which means `mostPopular()` may need to pop multiple stale entries before finding a valid one, and that's no longer O(1). The bucket approach gives true O(1) for all three methods.
- **Handle `decreasePopularity` on a non-existent ID** — Decide and state your policy: treating it as a no-op is reasonable, but you could also initialize the ID at score 0 and let it go negative. Pick one and be consistent.
- **Discuss tie-breaking semantics** — The problem says "return any one of them," so `next(iter(set))` is fine. But if the interviewer asks for deterministic tie-breaking (e.g., smallest ID), mention you'd swap the set for a sorted structure or a heap within each bucket, which changes the complexity.
- **Consider score 0 and negative scores** — Clarify whether content with no interactions (score 0) should be returned by `mostPopular()`. If `increasePopularity` is the only way content enters the system, then `buckets` only contains IDs with score ≥ 1, and `mostPopular()` returns -1 only when `buckets` is empty. If `decreasePopularity` can push scores to 0 or below, decide whether those IDs should be eligible for `mostPopular()`.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if `decreasePopularity` is called on a content ID that doesn't exist?** — Decide whether to initialize it at score 0, ignore it, or raise an exception; discuss the trade-offs.
- **How would you modify this to return the top K most popular content IDs?** — You'd need to maintain more than just the max bucket; consider a sorted structure or a heap of buckets.
- **What if popularity scores can change by more than 1 at a time (e.g., a "super like" worth +10)?** — The bucket approach still works, but the amortized walking argument in `decreasePopularity` needs revisiting.
- **How would you handle content IDs being removed entirely from the system?** — You'd need a `removeContent` method that deletes the ID from its bucket and updates `max_score` if necessary.
- **Can you make `mostPopular()` deterministic (e.g., always return the smallest ID among ties)?** — Swap the set for a sorted set or a min-heap within each bucket, and analyze the new complexity.

---

## ⚠️ Note on Page Content

As with the previous extraction, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
