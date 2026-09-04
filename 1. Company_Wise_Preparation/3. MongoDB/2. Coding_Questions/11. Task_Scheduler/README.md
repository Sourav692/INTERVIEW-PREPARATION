# Task Scheduler

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Onsite Loop, Graphs, Hash Tables · **Difficulty/Frequency:** Common (5/10)

---

## Problem Statement

Design a task scheduler with the following functionalities:

**`addTask(task, dependencies)`:**

- Add a task to the scheduler.
- Each task can optionally have dependencies, which must be executed before the task itself.
- Tasks are identified by unique identifiers (e.g., strings or integers).

**`executeAll()`:**

- Execute all tasks in the order they were submitted, while ensuring that dependencies are resolved before executing a task.
- Detect and handle circular dependencies. If a cycle is detected, the execution should fail or provide appropriate feedback.

---

## Study Tools

### Hint 1

The phrase "order they were submitted" is doing a lot of work here. If you execute strictly in submission order, you'll violate dependency constraints the moment a task depends on something submitted after it. Decide what "order" actually means for a valid execution, and what structure that implies.

### Hint 2

You need two things: a way to know how many unmet dependencies each task has, and a way to know which tasks become runnable when a given task completes. That suggests maintaining an **in-degree** count per task plus an **adjacency map** from task to its dependents.

### Hint 3

This is topological sort with cycle detection. Use **Kahn's algorithm**: repeatedly execute tasks whose unmet dependency count is zero, decrementing counts of their dependents. If you finish with tasks left over, the remaining ones form a cycle.

---

### Answer

This is topological sorting with cycle detection, implemented with Kahn's algorithm. The scheduler maintains a directed dependency graph, and `executeAll()` repeatedly runs tasks whose in-degree (unmet dependency count) is zero. If the number of executed tasks is less than the total number of tasks, a cycle exists.

#### Design

Keep three data structures:

- `tasks`: a dict mapping task ID to the task itself (callable or value).
- `deps`: a dict mapping task ID to a set of its direct dependencies.
- `dependents`: a dict mapping task ID to a set of tasks that depend on it. This lets us decrement in-degrees efficiently when a task completes.

`addTask(task, dependencies)` does a few things:

- If the task ID already exists, raise an error (or overwrite — pick one and document it).
- Validate that every dependency exists. If a dependency hasn't been added yet, raise an error. This is the cleanest contract: you must add dependencies before the tasks that need them.
- Store the task, record its dependency set, and register it in each dependency's `dependents` set.

`executeAll()` runs Kahn's algorithm:

- Compute in-degree for each task as `len(deps[task])`.
- Seed a queue with all tasks whose in-degree is zero, in submission order. Since tasks are added in submission order and we iterate insertion order of the dict, this preserves "run as early as possible, with ties broken by submission order."
- Pop a task, execute it, then for each dependent, decrement its in-degree. When a dependent's in-degree hits zero, enqueue it.
- If the executed count is less than the total task count, there's a cycle. Raise an error listing the remaining tasks.

```python
from collections import deque


class TaskScheduler:
    def __init__(self):
        self.tasks = {}        # id -> task (callable or value)
        self.deps = {}         # id -> set of dependency ids
        self.dependents = {}   # id -> set of ids that depend on this id

    def addTask(self, task_id, dependencies=None):
        dependencies = dependencies or []
        if task_id in self.tasks:
            raise ValueError(f"Task '{task_id}' already exists.")
        for dep in dependencies:
            if dep not in self.tasks:
                raise ValueError(f"Dependency '{dep}' not found for task '{task_id}'.")

        self.tasks[task_id] = task_id     # store the task; here the task is its own ID
        self.deps[task_id] = set(dependencies)
        self.dependents[task_id] = set()
        for dep in dependencies:
            self.dependents[dep].add(task_id)

    def executeAll(self):
        n = len(self.tasks)
        in_degree = {t: len(self.deps[t]) for t in self.tasks}
        queue = deque(t for t in self.tasks if in_degree[t] == 0)
        executed = []

        while queue:
            task_id = queue.popleft()
            executed.append(task_id)
            for dependent in self.dependents[task_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(executed) < n:
            remaining = [t for t in self.tasks if t not in executed]
            raise RuntimeError(f"Circular dependency detected among tasks: {remaining}")

        return executed
```

**Time:** O(V + E) for `executeAll()` — each task is enqueued and dequeued once, and each dependency edge is processed once when decrementing in-degrees. `addTask()` is O(d) where d is the number of dependencies.

**Space:** O(V + E) — the graph is stored as adjacency sets, plus the in-degree map and queue.

#### Correctness

**Invariant:** at every step, `in_degree[t]` equals the number of unexecuted dependencies of task `t`. Tasks in the queue have zero unexecuted dependencies, so executing them is always valid. When a task executes, we decrement the in-degree of every dependent, so the invariant holds for the next iteration.

**Cycle detection:** if a cycle exists, tasks in that cycle never reach in-degree zero because each depends on another in the cycle. Kahn's algorithm will exhaust the queue with those tasks unexecuted, so `len(executed) < n` detects it.

**Submission order:** ties are broken by insertion order of the dict, which matches submission order. When multiple tasks become runnable after a task completes, they're enqueued in the order they appear in the `dependents` set, which is insertion order in Python, so submission order is preserved among them.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the brute-force mental model: scan all tasks, find one whose dependencies are all executed, run it, repeat. That's O(V²) per scan, O(V³) total — too slow for anything real. The bottleneck is re-scanning every task after each execution.

Better: precompute how many unmet dependencies each task has (`in_degree`). When a task runs, decrement the in-degree of its dependents. Now we only touch tasks that are directly affected by the execution. This gets us to O(V + E).

For the queue, use `collections.deque` for O(1) pops from the front. Seed it with all in-degree-zero tasks in submission order. When a task completes, decrement its dependents and enqueue any that hit zero. This preserves "run as early as possible, ties broken by submission order."

Cycle detection falls out naturally: if the executed count is less than the total, the remaining tasks form a cycle. Raise an error with the remaining task IDs so the caller gets actionable feedback.

One design decision: what if a dependency doesn't exist yet when `addTask` is called? The cleanest answer is to reject it — the caller must add dependencies first. This avoids ambiguity about whether the task should wait for a future dependency or fail at execution time.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Preserving submission order among ready tasks** — the interviewer wants to see that you break ties deterministically. Using a deque seeded in dict insertion order gives you this for free in Python.
- **Rejecting unknown dependencies at add time** — stating this contract explicitly shows you've thought about error handling. Silently accepting them forces you to handle the failure later, when the graph is more complex.
- **Raising an error with the remaining task IDs on cycle detection** — just returning `False` or a partial list hides useful debugging information. Listing the tasks stuck in the cycle tells the caller exactly what to fix.
- **Using `dependents` (reverse adjacency) instead of scanning all tasks** — this is the difference between O(V²) and O(V + E). Mention it explicitly when you explain the complexity.
- **Handling duplicate task IDs** — decide whether `addTask` raises or overwrites, and say so. Interviewers probe edge cases, and duplicate IDs are the first one they'll try.
- **What "execute" means** — if tasks are callables, you'd call them; if they're just IDs, you return the execution order. Clarify this before writing code so the interface matches the question.
- **Testing with a diamond dependency (A→B, A→C, B→D, C→D)** — this catches off-by-one errors in in-degree counting. Walk through it out loud if asked to test your solution.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if `addTask` is called with a dependency that doesn't exist yet?** — Allow forward references by storing pending edges, or reject them. Discuss the tradeoffs.
- **What if tasks have different execution times or priorities?** — This becomes a scheduling problem; you'd use a priority queue instead of a deque, keyed by priority or deadline.
- **How would you parallelize execution?** — You can run all currently-runnable tasks concurrently, but you need to track which tasks are in-flight and only decrement in-degrees when they complete.
- **What if a task fails at runtime?** — Should dependent tasks still run? You'd need a policy: skip dependents, retry the failed task, or halt everything.
- **Can you detect cycles at `addTask` time instead of `executeAll` time?** — You'd run a cycle check on each insertion, which is O(V + E) per add. Discuss when this is worth it.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Two corrections to the official answer

Both were found by running the code; see the notebook, where each is covered by an assertion.

**1. `dependents` must not be a `set` if you want deterministic output.**

The official answer's correctness section claims:

> *"they're enqueued in the order they appear in the `dependents` set, which is insertion order in Python, so submission order is preserved among them."*

Python **dicts** preserve insertion order; **sets do not** — set iteration order is hash-based. With `dependents` as a `set`, the relaxation loop enqueues newly-runnable tasks in an arbitrary order. The result is still a *valid* topological order, but a **non-deterministic** one that can differ between runs. The notebook uses a `list` for the reverse edges, which fixes it (duplicates are impossible, since each edge is added exactly once).

**2. A FIFO queue does not give "earliest submitted first".**

Kahn's with a `deque` breaks ties by *when a task became runnable*, not by submission index. With `t0`, `t1` (depends on `t0`), and `t2` (no dependencies):

| policy | order |
|---|---|
| FIFO `deque` | `t0, t2, t1` — `t0` and `t2` are both ready at the start |
| earliest-submitted | `t0, t1, t2` — once `t0` runs, `t1` outranks `t2` by submission index |

Both are valid. If the spec genuinely means "prefer the earliest submitted", you need a **min-heap keyed by submission index** rather than a FIFO queue — a two-line change, costing O((V+E) log V). The notebook implements both and asserts the difference.
