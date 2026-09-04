# Scores Finding — Explained Simply

## The Problem

You have a list of `(player_name, score)` records. Players appear **many times** with different scores.

1. Keep only each player's **best** score.
2. Return the **top 50**, highest first.

```
[("ann", 10), ("bob", 30), ("ann", 25), ("cy", 5), ("bob", 20)]

→ best scores: ann=25, bob=30, cy=5
→ top 2:       [("bob", 30), ("ann", 25)]
```

## It's Really Two Problems

That's the whole insight. Read the task again and you'll see two completely different questions:

| Phase | Question | Right tool |
|---|---|---|
| **1** | "What's each player's best score?" | **hash map** |
| **2** | "Who are the top 50?" | **size-50 heap** |

Most people solve both with one tool — sorting — and that's what makes the naive version slow.

## An Analogy First: Marking Exam Papers

A pile of exam papers. Students sat the exam several times, so there are duplicates. You want the top 50 students by their best attempt.

**The slow way:** sort the entire pile alphabetically so each student's papers group together. Find each student's best. Then sort *those* by grade and take the top 50.

You've now sorted the whole pile — **twice**.

**The fast way:**

- **Phase 1:** walk the pile once with a scoreboard. For each paper, look up that student and write down the score if it beats what's there. One pass. No sorting — because "what's the best for this student?" doesn't need anything to be in order.

- **Phase 2:** you want the top 50, not a full ranking of all 3,000 students. So keep a **shortlist of exactly 50**. For each student, if they beat the *worst* person currently on the shortlist, swap them in.

The key: you need instant access to the **weakest person on the shortlist** — the one to bump. That's what a heap gives you.

## Phase 1: Why a Hash Map, Not a Sort

"Keep the best score per player" is a **grouping** operation. Sorting would achieve it, but sorting answers a much harder question — *the complete order of everything* — than the one you asked.

```python
best = {}
for name, score in records:
    if name not in best or score > best[name]:
        best[name] = score
```

One pass. O(n). No ordering involved at all.

> **Reaching for `sorted()` to group things is the single most common trap in this family of problems.**

### The invariant

Worth being able to state: *after processing any prefix of the input, `best[name]` is the maximum score seen so far for that name.* Each new record either beats it (update) or doesn't (skip). That's a two-line proof of correctness.

### Watch out: the max, not the latest

```
bob 30   →  best = {bob: 30}
bob 20   →  best = {bob: 30}    ← unchanged! 20 < 30
```

A common bug is `best[name] = score`, which keeps the **last** score rather than the **best** one. The test suite checks both orderings deliberately.

## Phase 2: Top-K Without a Full Sort

You have 3,000 unique players. You want 50. Sorting all 3,000 costs `m log m`.

But you don't need them ordered — you need the **50 largest**.

### The min-heap trick

Keep a heap of size 50:

- Push each player.
- If the heap grows past 50, **pop the smallest**.

After scanning all `m` players, the heap holds exactly the 50 largest. Cost: **O(m log 50)**.

### "Wait — a *min*-heap to find the *largest*?"

Yes, and it's the part that feels backwards until it clicks.

You're maintaining a shortlist. The operation you do constantly is: *"is this new person better than the worst one on my list?"* — and if so, evict the worst.

So the thing you need instantly available is the **weakest survivor**. That's the minimum. A min-heap puts it right at the top, ready to be thrown out.

```python
heapq.nlargest(50, best.items(), key=lambda kv: kv[1])
```

## Step-by-Step Example (Narrated)

`[("ann",10), ("bob",30), ("ann",25), ("cy",5), ("bob",20)]`, top 2.

### Phase 1 — build the scoreboard

---

**`("ann", 10)`** — ann isn't on the board. Add her.
`best = {ann: 10}`

---

**`("bob", 30)`** — new. Add.
`best = {ann: 10, bob: 30}`

---

**`("ann", 25)`** — ann is on the board at 10. Is 25 > 10? **Yes** → update.
`best = {ann: 25, bob: 30}`

---

**`("cy", 5)`** — new. Add.
`best = {ann: 25, bob: 30, cy: 5}`

---

**`("bob", 20)`** — bob is on the board at 30. Is 20 > 30? **No** → leave it.
`best = {ann: 25, bob: 30, cy: 5}`

*This is the case that catches people. Bob's later, lower score must not overwrite his best.*

### Phase 2 — take the top 2

Min-heap of size 2, streaming through `{ann: 25, bob: 30, cy: 5}`:

- push ann (25) → heap holds `[25]`
- push bob (30) → heap holds `[25, 30]` — full
- push cy (5) → over capacity → **pop the smallest**, which is 5 → heap holds `[25, 30]`

Read out descending: **`[("bob", 30), ("ann", 25)]`** ✅

## The Bug Hiding in the Hint

The official Hint 3 suggests:

```python
best[name] = max(best.get(name, 0), score)
```

Elegant — and **broken if scores can be negative.**

A player whose only score is `-5`:

```python
max(0, -5) = 0        # ← invents a score they never had
```

Now they're recorded at 0, ranking them **above** someone who genuinely scored `-1`.

The notebook demonstrates it directly: with `{a: -5, b: -1, c: -100}`, the buggy version produces `{a: 0, b: 0, c: 0}` — every real score erased.

**Fixes:**

```python
if name not in best or score > best[name]:      # ✅ membership test
best[name] = max(best.get(name, float("-inf")), score)   # ✅ correct default
```

> **Never default a maximum to zero.** Zero is a legitimate value, not an "empty" one.

## Ties: The Bug That Only Bites at the Boundary

Two players on the same score have no defined order. In the middle of a list, who cares.

**At the cut-off, it matters a lot.** If players #50 and #51 are tied, whether you make the leaderboard could change **between runs** — for identical data. That's a leaderboard that generates support tickets.

The fix costs nothing:

```python
key = (-score, name)      # score descending, then name alphabetically
```

Flagging the ambiguity is worth more than either choice. What you can't do is leave it unspecified and hope.

## Naming Your Variables in the Complexity

The complexity here has **three** quantities, and conflating them hides the whole design:

| | meaning | typical |
|---|---|---|
| `n` | input rows | 1,000,000 |
| `m` | unique players | 1,000 |
| `k` | results wanted | 50 |

**O(n + m log k)** says something real. **O(n log n)** hides it entirely.

And since `k = 50` is a **constant**, `log k` is a constant too — so the whole function is effectively **O(n)**. That's the sentence to say out loud.

## The Follow-Up That Breaks Everything

*"What if scores can go **down**?"*

The max-dict silently assumes scores only improve. `max()` records a **high-water mark** — the best ever achieved.

But if a player can lose points, "best ever" and "current standing" are **different questions**, and `max()` is answering the wrong one.

They look identical on data where scores only rise, which is exactly why this bug ships.

### The live-leaderboard fix

You need:

- A **dict** with each player's *current* score — the source of truth.
- A **heap** for fast ranking.

But here's the catch: **a heap can't update an entry in place.** There's no "find this player and change their priority".

The standard workaround is **lazy deletion**:

1. Never remove the stale entry — just push the new one.
2. When popping, check the dict. If the score doesn't match, that entry is stale — **discard it and keep popping**.
3. Stale entries pile up, so rebuild the heap once it outgrows the live set.

That keeps updates at O(log n) amortised.

## Why It's Fast

| Unique players | Sort twice | Map + sort | Map + heap |
|---|---|---|---|
| 2,000 | 4.9 ms | 1.6 ms | 1.3 ms |
| 4,000 | 10.9 ms | 3.0 ms | 2.6 ms |
| 8,000 | 26.1 ms | 7.5 ms | 5.6 ms |
| 16,000 | 62.7 ms | 17.2 ms | 12.4 ms |

Fixing phase 1 (sort → hash map) is the big win: **3.6× faster**. Fixing phase 2 (sort → heap) adds another ~40%.

**An honest note:** the heap's advantage here is a **constant factor**, not a change in shape. Across this range `log m` grows from 11 to 14 while `log k` stays at ~5.6 — a steady ratio. "Top-K without a full sort" is a real win, but it becomes an *asymptotic* one only when `k` is genuinely tiny relative to `m`.

And when does the heap stop being worth it? As `k → m` the two converge, and past roughly `k > m / log m` the sort's better constant factor wins outright. Knowing the heap is only better **because k is small and fixed** is the real answer to that follow-up.

## Common Mistakes

- **Sorting to group.** Aggregation needs a hash map, not an ordering.
- **`max(best.get(name, 0), score)`.** Erases negative scores.
- **`best[name] = score`.** Keeps the latest, not the best.
- **Sorting all `m` to take 50.** That's what the heap is for.
- **Leaving ties unspecified.** Non-deterministic membership at the cut-off.
- **Saying O(n log n).** Distinguish `n`, `m`, and `k`.
- **Assuming scores only go up.** `max()` is "best ever", not "current".

## The Takeaway

> When a problem has two verbs — *"dedupe, then rank"* — it has two sub-problems, and each has its own right tool. A **hash map** groups without ordering; a **size-K min-heap** ranks without sorting everything.

The min-heap-for-max-K inversion is worth internalising: when you're maintaining a shortlist, the item you need at your fingertips isn't the best one — it's the **worst one you're still keeping**, because that's the one you'll throw away next.
