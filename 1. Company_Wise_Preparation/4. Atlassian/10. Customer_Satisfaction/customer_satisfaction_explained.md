# Customer Satisfaction — Explained Simply

## The Problem

Agents receive 1-5 star ratings over time. You need: `accept_rating(agent, rating, month)`, and `get_all_agents_sorted()` returning everyone's **average** rating, highest first.

```
accept_rating("agent_a", 5, "2024-01")
accept_rating("agent_a", 4, "2024-01")
get_all_agents_sorted()   # -> [("agent_a", 4.5), ...]
```

## Why the Obvious Way Is Slow

The obvious approach: just keep a growing list of every rating ever given, `[(agent, rating, month), ...]`. Recording a new rating is instant (just append). But to answer "what's everyone's average?", you have to walk the **entire history** every single time, re-summing and re-counting from scratch.

```
def get_all_agents_sorted_naive(history):
    totals = {}
    for agent, rating, month in history:   # re-scans EVERYTHING, every call
        ...
```

If ratings come in constantly and the leaderboard is checked often (which is the whole point of a leaderboard), you're redoing more and more work forever — the history only ever grows, so every query gets slower than the last.

## The Simple Trick: You Don't Need the History, You Need the Average — So Just Track That

You never actually need to look at an individual rating again once it's been recorded. All an average needs is two running numbers: the **total** of all ratings, and the **count** of how many there were. `average = total / count`. Update those two numbers when a rating comes in; never rescan anything.

## An Analogy First: A Bank Balance vs. a Shoebox of Receipts

Imagine tracking your finances by throwing every single receipt into a shoebox, then every time you want to know your balance, dumping out the whole box and adding every receipt up from scratch. That gets slower every single day, forever, as the box fills up.

Compare that to just keeping a running balance in a checkbook: each transaction updates one number by a small, fixed amount of work, and checking your balance is just reading that one number. The shoebox holds strictly more information (every individual transaction) — but for the question you're actually asking ("what's my balance?"), the checkbook's running total is all you ever needed.

## Step-by-Step Example (Narrated)

```
accept_rating("agent_a", 5, "2024-01")
accept_rating("agent_a", 4, "2024-01")
accept_rating("agent_b", 4, "2024-01")
```

We keep `stats[agent] = [total, count]`.

---

**`accept_rating("agent_a", 5, ...)`**
`agent_a` hasn't been seen — create `[0, 0]` for them.
Add 5 to the total, add 1 to the count: `stats["agent_a"] = [5, 1]`.

---

**`accept_rating("agent_a", 4, ...)`**
`agent_a` already exists at `[5, 1]`.
Add 4 to the total (5+4=9), add 1 to the count (1+1=2): `stats["agent_a"] = [9, 2]`.

---

**`accept_rating("agent_b", 4, ...)`**
`agent_b` hasn't been seen — create `[0, 0]`.
Add 4, add 1: `stats["agent_b"] = [4, 1]`.

---

**Now call `get_all_agents_sorted()`**

For each agent, compute `average = total / count`:
- `agent_a`: `9 / 2 = 4.5`
- `agent_b`: `4 / 1 = 4.0`

No history was rescanned — we just read the two running numbers we've been maintaining and divided them. Sort descending by average: **`[("agent_a", 4.5), ("agent_b", 4.0)]`**.

### The one detail that's easy to miss: ties need a second, deterministic rule

If two agents land on the exact same average, sorting by average alone leaves their relative order up to chance (whatever order the dictionary happens to iterate in). Sorting by `(-average, agent_id)` instead makes the tiebreak explicit and repeatable: same average → alphabetical by agent ID, every time, on every run.

## Plain-English Walkthrough

1. Keep a dictionary mapping each agent to `[running_total, running_count]`.
2. When a new rating comes in, look up (or create) that agent's pair, and add the rating to the total and 1 to the count.
3. To list agents by average, compute `total / count` for each one on the fly — this is cheap because you're never re-deriving the total or count, just dividing two numbers you already have.
4. Sort by `(-average, agent_id)` so the order is both correct (highest first) and deterministic (alphabetical tiebreak).

## Simple Python Code

```python
from collections import defaultdict

class RatingSystem:
    def __init__(self):
        self.stats = defaultdict(lambda: [0, 0])   # agent -> [total, count]

    def accept_rating(self, agent, rating, month=None):
        self.stats[agent][0] += rating
        self.stats[agent][1] += 1

    def get_all_agents_sorted(self):
        results = [(agent, total / count) for agent, (total, count) in self.stats.items()]
        results.sort(key=lambda x: (-x[1], x[0]))
        return results

system = RatingSystem()
system.accept_rating("agent_a", 5)
system.accept_rating("agent_a", 4)
system.accept_rating("agent_b", 4)
print(system.get_all_agents_sorted())   # [('agent_a', 4.5), ('agent_b', 4.0)]
```

## Why Store `[total, count]` and Not Just the Average Directly?

If you stored only the running average, you couldn't correctly update it when a new rating arrives — averages don't combine by simple addition (`(4.5 + 5) / 2` is *not* the new average). But `[total, count]` pairs combine perfectly with plain addition: `new_total = old_total + rating`, `new_count = old_count + 1`, and the average is always just one division away, computed fresh whenever it's needed.

## Complexity

- **Time:** O(1) for `accept_rating`. O(m log m) for `get_all_agents_sorted`, where m is the number of distinct agents — **not** the number of ratings ever given.
- **Space:** O(m) — one `[total, count]` pair per agent.

## The Reusable Pattern

This is the **"store the aggregate, not the raw history"** pattern:
- Any running average, running sum, or running count (this problem)
- Streaming statistics (Welford's algorithm generalizes this to running variance)
- Leaderboards, dashboards, any "top sellers this month" style report

Core idea: figure out the *smallest* summary that's enough to answer your actual question and still be updated in O(1), then never store more than that — `[sum, count]` is enough for an average; you don't need the individual numbers that produced it.
