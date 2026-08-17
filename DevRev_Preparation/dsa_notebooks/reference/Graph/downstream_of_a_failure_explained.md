# Downstream of a Failure (Blast Radius) — Explained Simply

## The Problem

You have a bunch of services or tasks, and some depend on others (a graph of arrows: "A unlocks B" means B depends on A). If task/service `A` **fails**, you want to know: **everything that gets affected**, directly or indirectly — the "blast radius."

Example:

```
Auth(0) -> API(1), Auth(0) -> Billing(2)
API(1) -> Notif(3), API(1) -> Dashboard(4)
Billing(2) -> Dashboard(4)
Dashboard(4) -> Reports(5)

If API (1) fails -> affected = {Notif(3), Dashboard(4), Reports(5)}
(Auth and Billing are NOT affected — they don't depend on API)
```

## Why the Obvious Way Is Slow

The obvious way: keep a set of "affected" nodes, and repeatedly scan **every single dependency edge** to see if anything new should be added, over and over, until nothing changes anymore.

```
affected = {failed_node}
repeat until nothing new gets added:
    scan every edge
    if the edge starts at an affected node, mark its endpoint affected too
```

If the graph is a long chain, you might need almost as many rounds as there are nodes, and each round re-scans every edge — that's `O(nodes × edges)`, too slow for large graphs.

## The Simple Trick: Walk Outward Once, Remembering Where You've Been

Instead of repeatedly re-scanning everything, just walk outward from the failed node **once**, like ripples spreading from a stone dropped in water:

1. Start at the failed node.
2. Look at everything that directly depends on it — mark them as affected, and add them to a queue to explore next.
3. Pop the next node from the queue, look at everything that depends on *it*, mark and queue any new ones.
4. Keep going until the queue is empty.

This is called **BFS** (Breadth-First Search) when using a queue, or **DFS** (Depth-First Search) if you use a stack instead — both find the same "who's affected" answer. The key ingredient is a **visited set**, so you never revisit the same node twice (which also protects you from looping forever if there's a cycle).

## Step-by-Step Example

```
Auth(0) -> API(1), Auth(0) -> Billing(2)
API(1) -> Notif(3), API(1) -> Dashboard(4)
Billing(2) -> Dashboard(4)
Dashboard(4) -> Reports(5)

Failure at API (1)
```

| Step | Process | Newly discovered | seen so far |
|------|---------|-------------------|--------------|
| Start | queue = [1] | — | {1} |
| 1 | pop 1, look at its dependents: 3, 4 | 3, 4 | {1, 3, 4} |
| 2 | pop 3, no dependents | — | {1, 3, 4} |
| 3 | pop 4, look at its dependents: 5 | 5 | {1, 3, 4, 5} |
| 4 | pop 5, no dependents | — | {1, 3, 4, 5} |

Remove the failed node itself from the result: **affected = {3, 4, 5}** ✅

## Plain-English Walkthrough

1. Build a lookup: for each node, know exactly who depends on it (its "dependents").
2. Start a queue with just the failed node, and mark it "seen."
3. Repeatedly take a node out of the queue, look at everyone who depends on it, and for each one not already seen: mark it seen, add it to the result, and put it in the queue to explore later.
4. Once the queue is empty, you've found everyone reachable from the failure — that's your blast radius.
5. Report everyone found, except the original failed node itself.

## Simple Python Code

```python
from collections import deque, defaultdict

def downstream_of_failure(n, edges, source):
    # Build: who depends on each node?
    graph = defaultdict(list)
    for u, v in edges:
        graph[u].append(v)   # v depends on u

    seen = {source}
    queue = deque([source])

    while queue:
        node = queue.popleft()
        for dependent in graph[node]:
            if dependent not in seen:
                seen.add(dependent)
                queue.append(dependent)

    seen.discard(source)   # don't report the failed node itself
    return seen

edges = [[0,1],[0,2],[1,3],[1,4],[2,4],[4,5]]
print(downstream_of_failure(6, edges, 1))  # {3, 4, 5}
```

## Why a "Seen" Set Matters

Real dependency graphs can accidentally have cycles (A depends on B, B depends on A). Without tracking what you've already visited, you could loop forever bouncing between the same nodes. The `seen` set guarantees each node is processed exactly once, which also keeps the whole thing fast.

## Complexity

- **Time:** O(nodes + edges) — every node and edge is looked at exactly once.
- **Space:** O(nodes + edges) — for the lookup table, the seen set, and the queue.

## The Reusable Pattern

This is the **"reachability from a source"** pattern (BFS/DFS with a visited set). Use it whenever you see:
- "What's affected if X fails / breaks?"
- "Blast radius" or "cascading failure"
- "Everything downstream of / reachable from a node"

To go the *other* direction — "what did this depend on, i.e. what's the root cause?" — just reverse the arrows and do the same walk.

Related classics: Number of Islands, Clone Graph — same core idea of "walk outward, mark what you've seen."
