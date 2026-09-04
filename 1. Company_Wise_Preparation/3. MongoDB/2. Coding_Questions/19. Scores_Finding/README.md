# Scores Finding

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Hash Tables, Sorting · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Given a list of player objects, where each player object has the following attributes:

- `name`: A string representing the player's name.
- `score`: An integer representing the player's score.

Each player may appear **multiple times** in the list with different scores. Your task is to:

1. Retain only the **highest** score for each player.
2. Return the **top 50** players with the highest scores, sorted in **descending** order of their scores.

---

## Study Tools

### Hint 1

You need to collapse duplicate players to their best score before you can think about ranking. A map keyed by player name, keeping the max score seen so far, gets you there in one pass.

### Hint 2

Once you have each player's best score in a map, you need the top 50 entries by value. Python's `heapq.nlargest` with `k=50` gives you that without sorting the entire collection.

### Hint 3

The full approach: iterate the list, update `best[name] = max(best.get(name, 0), score)`, then call `heapq.nlargest(50, best.items(), key=lambda kv: kv[1])`. That returns `(name, score)` pairs sorted descending.

---

### Answer

This is a top-k aggregation problem with deduplication by key. The clean solution is one pass to build a dict of name → max score, then extract the top 50 entries by score using a heap.

```python
import heapq
from collections import namedtuple

Player = namedtuple('Player', ['name', 'score'])


def top_50_players(players):
    """
    players: iterable of Player objects (or anything with .name and .score)
    Returns list of (name, score) tuples, top 50 by score, descending.
    """
    best = {}
    for p in players:
        name, score = p.name, p.score
        if name not in best or score > best[name]:
            best[name] = score

    top = heapq.nlargest(50, best.items(), key=lambda kv: kv[1])
    return top
```

**Time:** O(n + m log k) where n is the total number of player entries, m is the number of unique players, and k = 50. The dict pass is O(n), and `heapq.nlargest` maintains a heap of size k while scanning all m entries, so O(m log k). Since k is constant, this is effectively O(n + m log 50) ≈ O(n).

**Space:** O(m + k) — the dict holds one entry per unique player, and the heap holds at most 50 items. Since k is constant, this is O(m).

**Correctness reasoning:** The dict pass maintains the invariant that after processing any prefix of the input, `best[name]` equals the maximum score seen for that player so far. When a new entry with the same name arrives, the max comparison preserves this invariant. After the full pass, `best` contains exactly the highest score for each player. `heapq.nlargest` is documented to return the k largest elements in descending order, so the result is the top 50 by score. Ties in score are broken arbitrarily by heap order, which is fine since no tie-breaking rule is specified.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute force: sort the entire list by name, then by score descending, and deduplicate by keeping the first occurrence of each name. That's O(n log n) for the sort plus O(n) for the dedup pass. Then sort the unique players by score descending and slice `[:50]` — another O(m log m). Total O(n log n + m log m). It works, but you're sorting twice and paying for full sorts when you only need 50 items.

The first bottleneck is the full sort on the input. You don't need order; you need **aggregation**. A dict keyed by name collapses duplicates in O(n) with O(1) average-case lookups. That eliminates the first sort entirely.

The second bottleneck is sorting all m unique players when you only need the top 50. Python's `heapq.nlargest(k, iterable, key=...)` uses a min-heap of size k: it pushes each element, and when the heap exceeds k, it pops the smallest. After scanning all m items, the heap holds the k largest. This is O(m log k) instead of O(m log m). With k = 50, the log factor is tiny.

One edge case to mention: if there are fewer than 50 unique players, `nlargest` just returns all of them sorted, which is the correct behavior. If the input list is empty, `best` is empty and `nlargest` returns an empty list.

If the interviewer pushes on the heap internals, you can implement the same thing manually: push `(-score, name)` onto a min-heap of size 50, and at the end negate the scores back. But `heapq.nlargest` is the idiomatic Python answer and shows you know the standard library.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Use a dict for deduplication, not sorting** — collapsing duplicates with a hash map is O(n) and shows you understand that aggregation doesn't require ordering. Sorting first is the most common trap here.
- **Know your heap primitives** — `heapq.nlargest` with `k=50` is the right tool because it avoids a full sort of all unique players. Mentioning the O(m log k) vs O(m log m) distinction signals you think about constants and scale.
- **State the complexity in terms of both n and m** — the input size and the number of unique players are different quantities. Interviewers listen for whether you distinguish them.
- **Handle the edge cases explicitly** — fewer than 50 unique players, empty input, and duplicate names with the same score all deserve a one-line mention. It shows you've actually run the code in your head.
- **Name the invariant in your dict pass** — after processing any prefix, `best[name]` is the max score seen so far for that name. Being able to articulate this is the difference between "it works" and "I can prove it works."
- **Consider the tie-breaking question** — if two players have the same score at the boundary of the top 50, what do you do? The spec doesn't say, so you should flag it and propose a deterministic tie-break (e.g., alphabetical by name) if needed.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the input is a stream of player score updates arriving continuously, and you need to maintain the top 50 in real time?** — Think about a heap plus a dict for O(log k) updates, but you also need to handle score decreases.
- **What if players can have scores that decrease (e.g., a game where you can lose points)?** — The simple max-dict breaks; you need a data structure that supports updates, like a balanced BST or a heap with lazy deletion.
- **What if the list is too large to fit in memory?** — External sort by name, then by score, or a map-reduce style aggregation with a combiner that keeps the max per name.
- **What if you need the top 50 by score, but ties are broken by name alphabetically?** — Pass a tuple key to `nlargest` or sort the heap entries by `(-score, name)`.
- **What if k is not fixed at 50 but is a parameter that can be large?** — The heap approach is still O(m log k), but if k approaches m, a full sort is simpler and asymptotically equivalent.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One correction to Hint 3

Hint 3 suggests:

```python
best[name] = max(best.get(name, 0), score)
```

That default of `0` is a bug whenever scores can be **negative**. A player whose only score is `-5` would be recorded as `0`, inventing a score they never had — and potentially ranking them above someone with `-1`.

The Answer's actual code avoids this by testing membership instead:

```python
if name not in best or score > best[name]:
```

Use `float("-inf")` as the default if you prefer the `max` form. The notebook asserts this case directly.
