# Task Scheduler — Explained Simply

## The Problem

Tasks can depend on other tasks. Run them all, but never run something before the things it depends on. And if the dependencies form a loop, say so instead of hanging.

```python
s.add_task("A")                    # no dependencies
s.add_task("B", ["A"])             # B needs A first
s.add_task("C", ["A"])             # C needs A first
s.add_task("D", ["B", "C"])        # D needs both

s.execute_all()                    # -> ["A", "B", "C", "D"]
```

## First: This Is a Graph

Draw it and the whole problem becomes obvious:

```
        A
       ╱ ╲
      B   C
       ╲ ╱
        D
```

- **Tasks** are dots (vertices).
- **"must run before"** is an arrow (a directed edge).

What you're being asked for is a **topological sort**: an ordering where every arrow points forward — everything appears after the things it depends on.

And a loop makes it impossible. If A needs B and B needs A, neither can ever start. So "detect circular dependencies" is really just "check this graph has no loops".

## Why the Obvious Way Is Slow

The obvious approach reads straight off the requirement:

```
while there are tasks left:
    scan every remaining task
    find one whose dependencies are all done
    run it
    start over
```

It works. But after every single completion it **re-examines the entire remaining graph** — including all the tasks that obviously weren't affected. With 2,000 tasks that's millions of redundant checks.

## An Analogy First: Building a House

You have a list of jobs: pour the foundation, frame the walls, install wiring, install plumbing, hang drywall, paint.

**The slow way:** every time a crew finishes something, walk the entire job list from the top asking "can this start now? can this one? this one?" — re-asking about jobs that have nothing to do with what just finished.

**The fast way:** give every job a **counter** — how many things it's still waiting on.

```
foundation:  0   ← can start right now
framing:     1   (waiting on foundation)
wiring:      1   (waiting on framing)
plumbing:    1   (waiting on framing)
drywall:     2   (waiting on wiring AND plumbing)
paint:       1   (waiting on drywall)
```

And on each job, pin a note: **"when I'm done, tell these people."**

```
foundation → tell framing
framing    → tell wiring, plumbing
wiring     → tell drywall
plumbing   → tell drywall
drywall    → tell paint
```

Now when the foundation crew finishes, you don't survey the whole site. You read its note, find framing, and knock its counter from 1 down to 0. **Zero means go.**

That's the entire algorithm. The counter is called the **in-degree**, the note is the **reverse edge list**, and the whole thing is **Kahn's algorithm**.

## The Two Ideas That Make It Fast

**1. Keep a counter instead of re-checking.**

"Is this runnable yet?" stops being a question you recompute and becomes a number you decrement.

**2. Store the arrows *backwards* as well as forwards.**

Your `dependencies` map says "B needs A" — that's the forward direction, and it's what the user gives you. But when A **finishes**, the question you need answered is "who was waiting on A?" — that's the reverse direction.

Without the reverse map you'd have to scan every task asking "did you depend on A?". Building both directions when the task is added makes that step instant.

This single change is the difference between O(V²) and O(V + E).

## Step-by-Step Example (Narrated)

The diamond: `A`, then `B` and `C` both need `A`, then `D` needs both `B` and `C`.

**Setup.** Count dependencies, and record who's waiting on whom:

```
in_degree:  A:0   B:1   C:1   D:2
dependents: A → [B, C]    B → [D]    C → [D]    D → []
```

Seed a queue with everything at **zero**:

```
queue = [A]
```

---

**Round 1 — pop `A`, run it.**

Read A's note: `[B, C]`. Decrement each:

- `B: 1 → 0` ✅ zero → **join the queue**
- `C: 1 → 0` ✅ zero → **join the queue**

```
queue = [B, C]        executed = [A]
```

---

**Round 2 — pop `B`, run it.**

B's note says `[D]`. Decrement: `D: 2 → 1`.

**Not zero.** D is still waiting on C, so it doesn't join yet. *This is exactly what a count of 2 was for.*

```
queue = [C]           executed = [A, B]
```

---

**Round 3 — pop `C`, run it.**

C's note also says `[D]`. Decrement: `D: 1 → 0` ✅ → **join the queue**.

```
queue = [D]           executed = [A, B, C]
```

---

**Round 4 — pop `D`, run it.** Nothing depends on D.

```
queue = []            executed = [A, B, C, D]   ✅
```

We executed 4 out of 4. Done.

## Cycle Detection Is Free

Here's the elegant part. Suppose A needs B, B needs C, and C needs A:

```
in_degree: A:1  B:1  C:1
```

**Nothing is zero.** The queue starts empty, the loop never runs, and:

```
executed = []      total = 3
```

`0 < 3` → there's a cycle.

Why this always works: a task inside a loop can *never* reach zero, because something else in the loop is always still ahead of it. So the queue inevitably drains with work left over.

> **No second pass. No visited-set colouring. Just one length comparison.**

And whatever's left over is precisely the set of tasks stuck in (or downstream of) the cycle — so you can name them in the error message. `"Circular dependency among: [a, b, c]"` is actionable; `False` is not.

## The Sneaky Part: "In the Order They Were Submitted"

The problem says to execute "in the order they were submitted". Taken literally that's **impossible** — if task 1 depends on task 2, submission order breaks the dependency.

The honest reading is: *respect dependencies first; among tasks that could run right now, prefer the earliest submitted.*

And here's where it gets genuinely subtle — **two reasonable implementations give different answers.**

Take `t0`, `t1` (depends on `t0`), and `t2` (no dependencies):

| Policy | Order | Why |
|---|---|---|
| **FIFO queue** | `t0, t2, t1` | `t0` and `t2` are both ready at the start, so both queue before `t1` becomes ready |
| **Earliest submitted** | `t0, t1, t2` | once `t0` runs, `t1` is runnable and has a lower index than `t2` |

Both are perfectly valid topological orders. They differ because:

- A **FIFO queue** breaks ties by *when a task became runnable*.
- **"Earliest submitted"** breaks ties by *submission index*, across everything runnable right now.

If the spec really means the second one, you need a **min-heap keyed by submission index** instead of a queue. It's a two-line change, costing O(V log V) instead of O(V).

> Knowing that these are two different policies — and being able to say which one your code implements — is the difference between an answer that works and an answer that's understood.

## A Container Choice That Isn't About Speed

One more trap, and it's a nasty one.

If you store `dependents` as a **set**:

```python
self.dependents[d].add(task_id)      # a set
```

...your output becomes **non-deterministic**.

Python **dicts** preserve insertion order. **Sets do not** — their iteration order is hash-based. So when a finished task relaxes its edges, its newly-runnable dependents get enqueued in an arbitrary order.

The result is still a *valid* topological sort. It's just a **different one on different runs** — and your tests fail intermittently for reasons that look like magic.

Use a `list`. Duplicates are impossible anyway, since each edge is added exactly once.

> **The lesson:** container choice isn't only about complexity. Sometimes it decides whether your output is reproducible.

## Bonus: The Algorithm Already Told You How to Parallelise

Most people miss this.

Everything sitting in the queue at the start of a round has **zero unmet dependencies** — so they're all mutually independent and can run **at the same time**.

Drain the queue one whole level at a time and you get **waves**:

```
wave 1: [A]
wave 2: [B, C]        ← these two can run concurrently
wave 3: [D]
```

Two things fall out for free:

- **The number of waves is the critical path** — the longest chain of dependencies. It's the hard floor on how fast the job can finish, no matter how many machines you have. Three waves means three rounds even with a thousand workers, because `D` genuinely cannot start until `B` and `C` are done.
- **The widest wave** is the most parallelism you could ever use. Wider than that and workers sit idle.

## Why It's Fast

The notebook benchmark, on a growing dependency graph:

| Tasks | Rescan | Kahn's |
|---|---|---|
| 250 | 0.87 ms | 0.30 ms |
| 500 | 3.07 ms (3.5×) | 0.64 ms (2.1×) |
| 1,000 | 11.7 ms (3.8×) | 1.37 ms (2.1×) |
| 2,000 | 45.7 ms (3.9×) | 2.69 ms (2.0×) |

The rescan **quadruples** every time the task count doubles — textbook quadratic. Kahn's **doubles**, which is the best you can do when you have to touch every task and every edge at least once.

## Common Mistakes

- **Only storing forward edges.** When a task finishes you need "who was waiting on me?" — that's the reverse direction. Without it you scan everything.
- **Using `list.pop(0)` as a queue.** It shifts every remaining element — O(n) per pop, quietly reintroducing a quadratic term. Use `collections.deque`.
- **Using a `set` for `dependents`.** Correct, but non-deterministic output.
- **Rechecking dependency sets instead of keeping a counter.** The counter *is* the optimisation.
- **Returning `False` on a cycle.** Name the stuck tasks — that's what makes the error useful.
- **Accepting a dependency on a task that doesn't exist yet.** Either reject it at `add_task` (clear error, at the exact call that made the mistake), or record it as pending — but if you defer, keep it distinguishable from a cycle at execute time.
- **Forgetting the diamond case.** `D` depending on both `B` and `C` needs an in-degree of **2**. If you only decrement once, `D` runs too early.

## The Takeaway

> "Must happen before" is a **directed edge**. Give every task a **counter** of what it's still waiting on, and every task a list of **who to notify** when it finishes. Run whatever hits zero. If the queue empties with work left over, you've found a cycle — for free.

Build systems, package managers, spreadsheet recalculation, course prerequisites, database migration ordering — all the same graph, all the same algorithm.
