# Confluence Page Link Graph — Explained Simply

## The Problem

Pages link to other pages (a directed graph). `find_path(from_id, to_id)` must return a **shortest** path (fewest hops), or `None` if unreachable.

```
g.add_page("p1", ["p2", "p3"])
g.add_page("p2", ["p3"])
g.add_page("p3", [])
g.find_path("p1", "p3")   # shortest is ["p1", "p3"] (1 hop), NOT ["p1", "p2", "p3"] (2 hops)
```

## Why the Obvious Way Is Slow (Actually — Why It Gives the Wrong Answer)

The obvious first attempt: depth-first search — follow one link as far as it goes, and if you reach the target, return that path.

```
def find_path_dfs(start, target):
    # dive down one branch fully before trying another
    ...
```

DFS *will* find **a** path if one exists — but it commits to whichever branch it tries first and only backs out when it dead-ends. If `p1` happens to link to `p2` before `p3` in its list, DFS might report `["p1", "p2", "p3"]` (2 hops) even though the direct link `p1 -> p3` (1 hop) exists and is clearly shorter. DFS has no concept of "shortest" baked into how it explores.

## The Simple Trick: Explore in Rings, Not Branches

If you explore the graph **level by level** — first everywhere reachable in 1 hop, then everywhere reachable in 2 hops, and so on — the very first time you reach the target, you've necessarily done so by the fewest possible hops. Nothing shorter could exist, because you'd have already found it in an earlier ring.

## An Analogy First: Ripples Spreading Across a Pond

Drop a stone in a pond and watch the ripples spread outward in perfect concentric rings. The first ripple to touch a floating leaf tells you the leaf's exact distance from the stone — because ripples expand uniformly, the leaf couldn't possibly be closer than the ring that first reaches it.

Compare that to instead sending a single beam of light bouncing off the water at a specific angle, hoping it eventually bounces its way to the leaf — it might get there, but by some long, zigzagging path with no guarantee it's the shortest possible route. The ripple approach (spreading evenly, ring by ring) is what makes "first contact = shortest distance" a guarantee.

## Step-by-Step Example (Narrated)

Graph: `p1 -> [p2, p3]`, `p2 -> [p3]`, `p3 -> []`. Find the shortest path from `p1` to `p3`.

We use a **queue** (first-in, first-out) so we always expand the *oldest* discovered page next — that's what produces ring-by-ring, breadth-first spreading. We also track `parent[page]` so we can rebuild the path afterward.

---

**Start:** `parent = {p1: None}`, queue = `[p1]`.

---

**Pop `p1` from the queue.** Look at its outbound links: `p2` and `p3`.

- `p2` hasn't been discovered yet → record `parent[p2] = p1`, add `p2` to the queue. Is `p2` our target (`p3`)? No.
- `p3` hasn't been discovered yet → record `parent[p3] = p1`. **Is `p3` our target? Yes!** Stop immediately — we've found it.

---

We never even need to pop anything else off the queue. Reconstruct the path by walking `parent` backward from `p3`:

`p3`'s parent is `p1`. `p1`'s parent is `None` (the start). Path, in reverse-discovery order: `[p3, p1]`. Reverse it to get forward order: **`[p1, p3]`** — a 1-hop path, matching the expected shortest answer.

### The one detail that's easy to miss: the path length is decided by *when a page is first discovered*, not by which order you happen to check its neighbors

Notice that we looked at `p2` before `p3` in `p1`'s neighbor list, and `p2` **was** discovered first — but `p2` wasn't the target, so we kept going and discovered `p3` on the very same step (still "1 hop away"). Both `p2` and `p3` are correctly recorded as 1 hop from `p1`, because they were both reached while processing `p1`, at the same ring.

## Plain-English Walkthrough

1. Put the start page in a queue, and record that it has no parent.
2. Repeatedly take the oldest page out of the queue and look at everywhere it links to.
3. For each undiscovered neighbor, record who discovered it (its parent) and add it to the queue.
4. The instant you discover the target, stop — walk the parent chain backward from the target to the start, then reverse it. That's your shortest path.
5. If the queue empties without ever discovering the target, there's no path — return `None`.

## Simple Python Code

```python
from collections import deque

def find_path_bfs(out_adj, start, target):
    if start == target:
        return [start]
    parent = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in out_adj.get(current, []):
            if neighbor not in parent:
                parent[neighbor] = current
                if neighbor == target:
                    path = []
                    node = target
                    while node is not None:
                        path.append(node)
                        node = parent[node]
                    return path[::-1]
                queue.append(neighbor)
    return None

graph = {"p1": ["p2", "p3"], "p2": ["p3"], "p3": []}
print(find_path_bfs(graph, "p1", "p3"))   # ['p1', 'p3']
```

## Why a Queue and Not a Stack?

A stack (last-in, first-out) is what DFS uses — it always dives into the *most recently* discovered page next, which is what produces "go deep on one branch first" behavior. A queue (first-in, first-out) always expands the *oldest* discovered page next, which is exactly what makes exploration spread outward ring by ring instead of plunging down one path. Swapping a stack for a queue is the entire difference between DFS and BFS — the rest of the code is nearly identical.

## Complexity

- **Time:** O(V + E) — every page is enqueued at most once, and every outbound link is examined at most once.
- **Space:** O(V) for the parent map and the queue.

## The Reusable Pattern

This is the **"BFS with a parent map"** pattern — the standard way to get shortest paths on any graph where every edge counts equally:
- Word Ladder (each word transformation is one "hop")
- Shortest path in a maze/grid
- "Degrees of separation" (social network shortest connection)

Core idea: BFS's ring-by-ring exploration order is what guarantees "first time reached = shortest path" — the moment you need weighted edges (some links "cost more" than others), plain BFS stops being correct and you need Dijkstra's algorithm instead.
