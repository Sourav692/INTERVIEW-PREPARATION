# 207. Course Schedule — Step-by-Step Reference

> **Source notebook:** `DSA_Blind 75/notebooks/Graph/course_schedule.ipynb`
> **LeetCode:** https://leetcode.com/problems/course-schedule/
> **Generated for:** personal study reference

---

## Overview

| Topic                        | Key idea                                                                                                                                      |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Directed graph               | Prerequisite`[a, b]` means "take `b` before `a`" — an edge from the dependency relation                                                |
| DFS cycle detection          | Color each course**unvisited / in-progress / done**; hitting an in-progress course while recursing means a **back-edge** → cycle |
| Kahn's topological sort      | Repeatedly peel off courses with in-degree`0`; if you can't peel all of them, a cycle is blocking the rest                                  |
| Cycle ⇔ impossible schedule | You can finish all courses**iff** the prerequisite graph has no cycle                                                                   |

**Canonical examples** (used for traces below):

```
No cycle (finishable):        Cycle (not finishable):
n = 3, pre = [[1,0],[2,1]]    n = 3, pre = [[0,1],[1,2],[2,0]]

0 -> 1 -> 2   (edges point       0 -> 1 -> 2 -> 0   (a ring —
"course needs" for DFS view;                          0 needs itself
 "unlocks" for Kahn's view)                            indirectly)
```

Expected outputs (from notebook asserts in cell 7):

| `numCourses` | `prerequisites`       | Expected  | `can_finish_dfs` | `can_finish_kahn` |
| -------------- | ----------------------- | --------- | ------------------ | ------------------- |
| `2`          | `[[1,0]]`             | `True`  | ✓ matches         | ✓ matches          |
| `2`          | `[[1,0],[0,1]]`       | `False` | ✓ matches         | ✓ matches          |
| `3`          | `[[1,0],[2,1]]`       | `True`  | ✓ matches         | ✓ matches          |
| `3`          | `[[0,1],[1,2],[2,0]]` | `False` | ✓ matches         | ✓ matches          |

> The notebook does **not** implement Course Schedule II (LeetCode 210, "return the order"); it is listed only as a related follow-up problem in the Patterns section.

---

## `can_finish_dfs` — DFS Cycle Detection (3-color / white-gray-black)

### What it does

Builds an adjacency list where `graph[a]` holds the courses `a` **depends on** (so DFS walks from a course down into its prerequisites). Each course has a `state`: `0` = unvisited (white), `1` = in-progress / on the current recursion stack (gray), `2` = done / proven safe (black). DFS on a course that is already `1` means the recursion looped back onto itself — a cycle — and the whole function returns `False`. If every course's DFS completes without hitting a gray node, `state` ends up all `2` and the function returns `True`.

### Code

```python
from collections import defaultdict, deque

def can_finish_dfs(numCourses, prerequisites):
    graph = defaultdict(list)              # course -> list of courses it depends on
    for a, b in prerequisites:
        graph[a].append(b)                 # a needs b done first
    state = [0] * numCourses               # 0 = unvisited, 1 = in-progress, 2 = safe/done
    def dfs(c):
        if state[c] == 1:
            return False                   # reached a course we're still exploring -> CYCLE
        if state[c] == 2:
            return True                    # already proven safe
        state[c] = 1                       # mark in-progress
        for nxt in graph[c]:               # every prerequisite must be completable
            if not dfs(nxt):
                return False
        state[c] = 2                       # this course (and its chain) is safe
        return True
    return all(dfs(c) for c in range(numCourses))
```

### Line by line

| Line / code                                            | What it does                                                                                                 |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `graph = defaultdict(list)`                          | Adjacency list, missing keys auto-create an empty list                                                       |
| `for a, b in prerequisites: graph[a].append(b)`      | Edge direction is**"needs"**: `a -> b` means `a` depends on `b`                                  |
| `state = [0] * numCourses`                           | Every course starts white/unvisited                                                                          |
| `if state[c] == 1: return False`                     | We are already exploring`c` on this call stack → a **back-edge**, i.e. a cycle                      |
| `if state[c] == 2: return True`                      | `c` was already fully explored and found safe — no need to redo work                                      |
| `state[c] = 1`                                       | Mark`c` gray — "currently on the stack"                                                                   |
| `for nxt in graph[c]: if not dfs(nxt): return False` | Recurse into every prerequisite; bail immediately on the first cycle found                                   |
| `state[c] = 2`                                       | Mark`c` black — `c` and everything it depends on is provably cycle-free                                 |
| `return all(dfs(c) for c in range(numCourses))`      | Run DFS from every course (graph may be disconnected); overall answer is`True` only if none report a cycle |

### Step-by-step trace

**Case A — no cycle:** `n=3, prerequisites=[[1,0],[2,1]]` → `graph = {1: [0], 2: [1]}` (course `0` has no dependencies key, `defaultdict` never populates it), `state = [0,0,0]` initially.

| Step | Call              | state before | Action                                                                   | state after |
| ---- | ----------------- | ------------ | ------------------------------------------------------------------------ | ----------- |
| 1    | `dfs(0)`        | `[0,0,0]`  | `graph[0]=[]` (no deps) → mark `1`, loop does nothing → mark `2` | `[2,0,0]` |
| 2    | `dfs(1)`        | `[2,0,0]`  | mark`1`; `graph[1]=[0]` → recurse `dfs(0)`                        | `[2,1,0]` |
| 2a   | ↳`dfs(0)`      | `[2,1,0]`  | `state[0]==2` → return `True` immediately (no re-exploration)       | `[2,1,0]` |
| 2b   | back in`dfs(1)` | `[2,1,0]`  | all deps returned`True` → mark `2`                                  | `[2,2,0]` |
| 3    | `dfs(2)`        | `[2,2,0]`  | mark`1`; `graph[2]=[1]` → recurse `dfs(1)`                        | `[2,2,1]` |
| 3a   | ↳`dfs(1)`      | `[2,2,1]`  | `state[1]==2` → return `True`                                       | `[2,2,1]` |
| 3b   | back in`dfs(2)` | `[2,2,1]`  | mark`2`                                                                | `[2,2,2]` |

`all(...)` sees `True, True, True` → **result `True`**. Final `state = [2, 2, 2]` — every course proven safe, no gray node ever seen a second time.

**Case B — cycle:** `n=3, prerequisites=[[0,1],[1,2],[2,0]]` → `graph = {0: [1], 1: [2], 2: [0]}`, `state = [0,0,0]`.

| Step | Call             | state before | Action                                                                             | state after |
| ---- | ---------------- | ------------ | ---------------------------------------------------------------------------------- | ----------- |
| 1    | `dfs(0)`       | `[0,0,0]`  | mark`1`; `graph[0]=[1]` → recurse `dfs(1)`                                  | `[1,0,0]` |
| 2    | ↳`dfs(1)`     | `[1,0,0]`  | mark`1`; `graph[1]=[2]` → recurse `dfs(2)`                                  | `[1,1,0]` |
| 3    | ↳↳`dfs(2)`   | `[1,1,0]`  | mark`1`; `graph[2]=[0]` → recurse `dfs(0)`                                  | `[1,1,1]` |
| 4    | ↳↳↳`dfs(0)` | `[1,1,1]`  | `state[0] == 1` (still on the stack!) → **cycle found**, return `False` | `[1,1,1]` |

`False` propagates straight back up through `dfs(2)`, `dfs(1)`, `dfs(0)`, and `all(...)` short-circuits → **result `False`**. Final `state = [1,1,1]` — nobody ever finished; all three courses got stuck gray, which is itself a signature of a cycle in this component.

### Mental model

- Three colors = three questions: white "haven't looked yet", gray "currently investigating, don't come back here", black "fully cleared".
- A cycle is exactly: while walking down the "needs" edges, you land back on a node that is still gray (still an ancestor in the current call chain).
- Memoization via `state[c] == 2` is what keeps this `O(V+E)` instead of exponential — a course proven safe is never re-explored.
- `all(dfs(c) for c in range(numCourses))` restarts DFS from every course so disconnected components are all checked, but the `state==2` check makes already-cleared nodes instant no-ops.

### Common confusions

- **Two-color (visited/unvisited) is not enough:** you need the third "in-progress" state to distinguish "already fully cleared" from "currently being explored" — that distinction is exactly what catches a back-edge vs. a forward/cross edge to an already-safe node.
- **Edge direction:** `graph[a].append(b)` means "`a` needs `b`", the opposite direction from Kahn's `graph[b].append(a)` ("`b` unlocks `a`") below — mixing the two conventions up is the #1 bug source.
- **Forgetting to mark `state[c]=2` after the loop:** without it, every later reference to an already-safe node re-explores it, and worse, could even mis-flag things.
- **`all(dfs(c) for c in range(numCourses))` still calls `dfs` on courses already marked done** — that's fine and cheap (`O(1)` return), not wasted `O(V+E)` work per call.

### Complexity

- **Time:** `O(V + E)` — each course visited once (thanks to the `state==2` short-circuit), each edge traversed once
- **Space:** `O(V + E)` — adjacency list plus recursion stack up to depth `V`

---

## `can_finish_kahn` — Kahn's Topological Sort (BFS with in-degree)

### What it does

Builds the **reverse** adjacency list — `graph[b]` holds the courses that `b` **unlocks** — plus an `indeg` array counting, per course, how many prerequisites it still has outstanding. Seeds a queue with every course that already has zero prerequisites. Repeatedly pops a course, counts it as `done`, and decrements the in-degree of everything it unlocks; any course that hits in-degree `0` gets enqueued. If `done` reaches `numCourses` by the time the queue empties, every course was eventually unlockable — no cycle. If the queue empties early, whatever's left is stuck in a cycle (their in-degree never reaches 0).

### Code

```python
from collections import defaultdict, deque

def can_finish_kahn(numCourses, prerequisites):
    graph = defaultdict(list)              # course -> courses it unlocks
    indeg = [0] * numCourses               # how many prerequisites each course still has
    for a, b in prerequisites:
        graph[b].append(a)                 # finishing b unlocks a
        indeg[a] += 1
    q = deque([c for c in range(numCourses) if indeg[c] == 0])  # courses with no prereqs
    done = 0
    while q:
        c = q.popleft(); done += 1         # take a course with nothing blocking it
        for nxt in graph[c]:
            indeg[nxt] -= 1                # it no longer needs c
            if indeg[nxt] == 0:            # all its prereqs are met now
                q.append(nxt)
    return done == numCourses              # took every course -> no cycle
```

### Line by line

| Line / code                                   | What it does                                                                                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `graph = defaultdict(list)`                 | Adjacency list,**reversed** direction from the DFS version                                                                                       |
| `indeg = [0] * numCourses`                  | One counter per course: how many prerequisites still block it                                                                                          |
| `graph[b].append(a); indeg[a] += 1`         | Edge direction is**"unlocks"**: `b -> a` because finishing `b` removes one blocker from `a`                                                |
| `q = deque([c for c ... if indeg[c] == 0])` | Start the frontier with every course that's immediately takeable                                                                                       |
| `c = q.popleft(); done += 1`                | Take the next unblocked course, count it toward the total                                                                                              |
| `for nxt in graph[c]: indeg[nxt] -= 1`      | Every course`c` unlocks gets one fewer outstanding prerequisite                                                                                      |
| `if indeg[nxt] == 0: q.append(nxt)`         | The moment a course has zero prerequisites left, it becomes takeable                                                                                   |
| `return done == numCourses`                 | If every course was eventually taken, there was no cycle; if some are stuck at`indeg > 0` forever, the queue drained early and `done < numCourses` |

### Step-by-step trace

**Case A — no cycle:** `n=3, prerequisites=[[1,0],[2,1]]` → reversed graph: `graph = {0: [1], 1: [2]}`, `indeg = [0, 1, 1]` (course `0` unlocks `1`, course `1` unlocks `2`).

Initial queue: `[0]` (only course `0` starts with `indeg == 0`).

| Step | Pop   | `done` | Effect on neighbors (`graph[c]`)         | `indeg` after | Queue after |
| ---- | ----- | -------- | ------------------------------------------ | --------------- | ----------- |
| 0    | —    | 0        | —                                         | `[0, 1, 1]`   | `[0]`     |
| 1    | `0` | 1        | `nxt=1`: `indeg[1] 1→0` → enqueue    | `[0, 0, 1]`   | `[1]`     |
| 2    | `1` | 2        | `nxt=2`: `indeg[2] 1→0` → enqueue    | `[0, 0, 0]`   | `[2]`     |
| 3    | `2` | 3        | `graph[2]` doesn't exist → no neighbors | `[0, 0, 0]`   | `[]`      |

Loop ends (`q` empty). `done == 3 == numCourses` → **result `True`**. Topological order taken: `[0, 1, 2]`.

**Case B — cycle:** `n=3, prerequisites=[[0,1],[1,2],[2,0]]` → reversed graph: `graph = {1: [0], 2: [1], 0: [2]}`, `indeg = [1, 1, 1]` (every course has exactly one outstanding prerequisite, forming a ring).

Initial queue: `[]` — **no course starts with `indeg == 0`**, because the ring gives every course exactly one blocker.

| Step | Pop                                                    | `done` | Queue after |
| ---- | ------------------------------------------------------ | -------- | ----------- |
| —   | (loop body never runs —`q` is empty from the start) | 0        | `[]`      |

`done == 0 != numCourses == 3` → **result `False`**. Final `indeg = [1, 1, 1]`, unchanged — the three courses permanently block each other and none ever gets peeled off.

### Mental model

- Think of it as literally taking classes: you can only register for a class once every prerequisite is checked off; the queue is your "currently eligible" list.
- `indeg[c] == 0` is the "no incoming arrows left" condition from Kahn's algorithm — visually, peeling a node off a DAG and deleting its outgoing edges.
- `done == numCourses` is the only signal you need: if a cycle exists, at least one node's in-degree can never reach 0, so it's never enqueued and `done` falls short.
- Edge direction here is the mirror image of the DFS version — Kahn's walks **forward** (prerequisite → dependent), DFS walks **backward** (course → its prerequisite).

### Common confusions

- **Reversed edges vs. DFS version:** `can_finish_dfs` builds `graph[a].append(b)` ("a needs b"); `can_finish_kahn` builds `graph[b].append(a)` ("b unlocks a"). Copy-pasting one edge direction into the other function silently breaks it.
- **Courses with no edges still count:** a course that appears in neither side of any prerequisite pair has `indeg == 0` from the start and is included in the initial queue and in `done` — it's still "takeable", not ignored.
- **Empty initial queue isn't a bug:** if every course has some prerequisite (a full cycle, e.g. Case B), the queue starts empty and the `while` loop simply never executes — that's the correct way a total cycle gets caught.
- **`done` counts courses, not edges:** don't confuse it with a countdown of remaining edges; it's a straightforward "how many courses did we manage to take".

### Complexity

- **Time:** `O(V + E)` — build adjacency list and in-degrees in one pass over `prerequisites` (`O(E)`), then each course enqueued/dequeued once and each edge relaxed once (`O(V + E)`)
- **Space:** `O(V + E)` — adjacency list, `indeg` array, and queue

---

## Quick reference

| Function            | Technique                                   | Edge direction                              | `[3,[[1,0],[2,1]]]`                    | `[3,[[0,1],[1,2],[2,0]]]`                  | Time       | Space      |
| ------------------- | ------------------------------------------- | ------------------------------------------- | ---------------------------------------- | -------------------------------------------- | ---------- | ---------- |
| `can_finish_dfs`  | DFS 3-color cycle detection                 | course → prerequisite (`a needs b`)      | `True` (`state` ends `[2,2,2]`)    | `False` (cycle at `state[0]==1` revisit) | `O(V+E)` | `O(V+E)` |
| `can_finish_kahn` | Kahn's topological sort (in-degree + queue) | prerequisite → dependent (`b unlocks a`) | `True` (`done=3`, order `[0,1,2]`) | `False` (`done=0`, queue starts empty)   | `O(V+E)` | `O(V+E)` |

## Patterns to remember

- **Cycle = impossible schedule:** any "do X before Y" ordering problem is topological sort in disguise; a cycle is exactly what makes an ordering impossible.
- **Two lenses on the same fact:** DFS coloring catches a cycle as a **back-edge** (revisiting a gray/in-progress node); Kahn's catches it as **starvation** (some nodes' in-degree never reaches zero, so the queue drains early).
- **Edge direction matters and differs by technique:** DFS here walks "needs" edges (course → prereq); Kahn's walks "unlocks" edges (prereq → course) — pick one and be consistent within a solution.
- **Isolated nodes still count:** a course with no prerequisites and unlocking nothing is trivially finishable — don't drop it from in-degree-0 seeding or from the DFS-from-every-node loop.
- **Signal words:** "prerequisites", "dependencies", "ordering", "can it be scheduled", "build order".
- **Related problems:** Course Schedule II (LeetCode 210 — return the actual order instead of just yes/no), Alien Dictionary, Build System order / task scheduling with dependencies.
