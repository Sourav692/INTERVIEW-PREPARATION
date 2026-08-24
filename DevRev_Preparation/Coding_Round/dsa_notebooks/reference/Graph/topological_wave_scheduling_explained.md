# Topological "Wave" Scheduling — Explained Simply

## The Problem

You have a list of tasks, and some tasks must finish before others can start (dependencies). You want to group tasks into **"waves"**: everything in Wave 1 can run at the same time (no dependencies), everything in Wave 2 can run once Wave 1 is done, and so on.

If the tasks have a **circular dependency** (A needs B, B needs A), it's impossible to schedule — you should detect that.

Example:

```
6 tasks: 0, 1, 2, 3, 4, 5
Dependencies (a, b) means "a needs b done first":
[2,0] [3,0] [4,1] [4,2] [5,3] [5,4]

Task 0 and 1 have no prerequisites  -> Wave 0
Task 2, 3 only need task 0 (done)   -> Wave 1
Task 4 needs 1 and 2 (both done)    -> Wave 2
Task 5 needs 3 and 4 (both done)    -> Wave 3

Result: [[0,1], [2,3], [4], [5]]
```

## Why the Obvious Way Is Slow

The obvious way: each round, re-check **every single dependency** to figure out which tasks are now ready.

```
while tasks remain:
    recompute how many prerequisites each task still has (scan ALL dependencies)
    take the ones with 0 prerequisites left as this wave
    remove them, repeat
```

If there are many waves, you re-scan all the dependencies every single round — that's `O(tasks × dependencies)`, which gets slow fast.

## The Simple Trick: Count Prerequisites Once, Then Just Subtract

Instead of re-counting from scratch every round, count each task's number of prerequisites **once**, up front. Then:

1. Any task with **0 prerequisites** is ready right now — that's Wave 0.
2. When a task finishes, go tell everyone who depends on it: "one of your prerequisites is done, subtract 1 from your remaining count."
3. Whenever someone's count hits 0, they become ready — they go in the *next* wave.
4. Repeat until no more tasks become ready.

This way, you never re-scan the full dependency list — you just walk each dependency edge **once**, when the prerequisite it depends on finishes.

## Step-by-Step Example

```
Dependencies: [2,0] [3,0] [4,1] [4,2] [5,3] [5,4]
(meaning: 2 needs 0, 3 needs 0, 4 needs 1, 4 needs 2, 5 needs 3, 5 needs 4)
```

First, count how many prerequisites each task has:
```
0: 0 prereqs
1: 0 prereqs
2: 1 prereq (needs 0)
3: 1 prereq (needs 0)
4: 2 prereqs (needs 1, 2)
5: 2 prereqs (needs 3, 4)
```

| Wave | Ready tasks (0 prereqs left) | What happens next |
|------|-------------------------------|---------------------|
| 0 | 0, 1 | Finishing 0 → task 2's count drops to 0, task 3's count drops to 0. Finishing 1 → task 4's count drops to 1. |
| 1 | 2, 3 | Finishing 2 → task 4's count drops to 0. Finishing 3 → task 5's count drops to 1. |
| 2 | 4 | Finishing 4 → task 5's count drops to 0. |
| 3 | 5 | Nothing left. |

Result: `[[0,1], [2,3], [4], [5]]` ✅

If a task's count **never** reaches 0 (because it's stuck waiting in a cycle), it never appears in any wave — that's how you detect a cycle: not all tasks got scheduled.

## Plain-English Walkthrough

1. For each task, count how many things it's waiting on (its "prerequisite count").
2. Anything with a count of 0 is ready — that's the first wave.
3. For each task in the current wave, tell its dependents "I'm done" — decrement their counts by 1.
4. Any dependent whose count just hit 0 becomes ready — that's the next wave.
5. Keep going until no wave produces any new ready tasks.
6. If you didn't manage to schedule every task, there's a cycle — return "impossible."

## Simple Python Code

```python
from collections import defaultdict

def schedule_waves(n, deps):
    graph = defaultdict(list)     # b -> tasks that depend on b
    indegree = [0] * n            # how many prerequisites each task still has

    for a, b in deps:              # a needs b
        graph[b].append(a)         # finishing b unlocks a
        indegree[a] += 1

    wave = [t for t in range(n) if indegree[t] == 0]   # tasks ready right now
    waves = []
    scheduled = 0

    while wave:
        waves.append(sorted(wave))
        next_wave = []
        for task in wave:
            scheduled += 1
            for dependent in graph[task]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    next_wave.append(dependent)
        wave = next_wave

    if scheduled != n:
        return None   # a cycle exists — not everything could be scheduled
    return waves

print(schedule_waves(6, [[2,0],[3,0],[4,1],[4,2],[5,3],[5,4]]))
# [[0, 1], [2, 3], [4], [5]]
```

## Why Check `scheduled != n`?

If there's a cycle (say A needs B and B needs A), neither A's nor B's count will ever hit 0 — they'll be stuck forever, waiting on each other. So they never get added to any wave. Comparing how many tasks we actually scheduled against the total `n` tells us instantly whether some tasks got left behind due to a cycle.

## Complexity

- **Time:** O(tasks + dependencies) — each task is processed once, each dependency edge is walked once.
- **Space:** O(tasks + dependencies) — for the prerequisite counts and the graph.

## The Reusable Pattern

This is **"Kahn's algorithm," grouped into levels** — the classic way to do topological sorting when you also want to know which tasks can run **in parallel**.

Use it whenever you see:
- "Schedule tasks with dependencies"
- "What can run in parallel / at the same time"
- "Detect if a set of dependencies has a cycle"
- Build systems, CI/CD pipeline stages, workflow orchestration

Core idea: track how many prerequisites are left per task, and every time one finishes, subtract from its dependents instead of recomputing from scratch.
