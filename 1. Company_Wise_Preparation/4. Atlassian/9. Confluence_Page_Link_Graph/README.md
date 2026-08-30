# Confluence Page Link Graph

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Graphs · **Difficulty/Frequency:** Common (6/10)

---

## Problem Statement

**Build and Query a Confluence Page Link Graph**

Confluence pages can link to other pages within the same space. Implement a class that builds a directed link graph from page data and supports several queries.

### Interface

```python
class PageLinkGraph:
    def add_page(self, page_id: str, outbound_links: list[str]) -> None:
        """Register a page and its outbound links to other page IDs."""

    def get_outbound(self, page_id: str) -> list[str]:
        """Return pages that page_id links to."""

    def get_inbound(self, page_id: str) -> list[str]:
        """Return pages that link to page_id."""

    def find_path(self, from_id: str, to_id: str) -> list[str] | None:
        """Return a shortest path (list of page IDs) from from_id to to_id.
        Return None if no path exists."""

    def orphaned_pages(self) -> list[str]:
        """Return all pages that have no inbound links from any other page."""
```

### Constraints

- A page can link to itself (self-loop) — ignore self-loops in all queries.
- A page may be referenced in `outbound_links` before it has been added via `add_page`.
- Up to 100,000 pages.

### Example

```python
g = PageLinkGraph()
g.add_page("p1", ["p2", "p3"])
g.add_page("p2", ["p3"])
g.add_page("p3", [])

g.get_outbound("p1")        # ["p2", "p3"]
g.get_inbound("p3")         # ["p1", "p2"]
g.find_path("p1", "p3")     # ["p1", "p2", "p3"] or ["p1", "p3"]
g.orphaned_pages()          # ["p1"]
```

### Follow-Up: Strongly Connected Components

Add a method:

```python
def find_cycles(self) -> list[list[str]]:
    """Return all groups of pages involved in a cycle
    (i.e., each strongly connected component of size > 1)."""
```

Discuss what a cycle means in the context of Confluence navigation and whether it is a problem.

---

## Study Tools

### Hint 1

The graph is just adjacency lists, so `get_outbound` is direct and `get_inbound` is a second adjacency map built in reverse. The interesting part is `find_path`: shortest path on an unweighted graph means BFS, not DFS.

### Hint 2

For `orphaned_pages`, track the in-degree of every page as you build the reverse map. A page is orphaned if its in-degree is zero and it was explicitly added — pages only seen as outbound targets don't count until `add_page` registers them.

### Hint 3

Run BFS from `from_id`, using a parent map to reconstruct the path when you reach `to_id`. For `find_cycles`, think Tarjan's algorithm or Kosaraju's — you need strongly connected components, and any SCC with more than one node (or a self-loop) is a cycle.

---

### Answer

This is a directed graph problem with adjacency-list storage, BFS for shortest paths, and Tarjan's algorithm for strongly connected components. The core design decision is maintaining two maps — `out_adj` for forward edges and `in_adj` for reverse edges — plus a `known_pages` set to distinguish explicitly added pages from pages only seen as link targets.

#### Core Implementation

```python
from collections import deque

class PageLinkGraph:
    def __init__(self):
        self.out_adj = {}       # page_id -> list[str] of outbound targets
        self.in_adj = {}        # page_id -> list[str] of inbound sources
        self.known_pages = set()  # pages explicitly added via add_page
        self.in_degree = {}     # page_id -> int

    def add_page(self, page_id: str, outbound_links: list[str]) -> None:
        self.known_pages.add(page_id)
        if page_id not in self.out_adj:
            self.out_adj[page_id] = []
        if page_id not in self.in_adj:
            self.in_adj[page_id] = []
        if page_id not in self.in_degree:
            self.in_degree[page_id] = 0

        for target in outbound_links:
            if target == page_id:
                continue  # ignore self-loops
            if target not in self.out_adj:
                self.out_adj[target] = []
            if target not in self.in_adj:
                self.in_adj[target] = []
            if target not in self.in_degree:
                self.in_degree[target] = 0

            self.out_adj[page_id].append(target)
            self.in_adj[target].append(page_id)
            self.in_degree[target] += 1

    def get_outbound(self, page_id: str) -> list[str]:
        return self.out_adj.get(page_id, [])

    def get_inbound(self, page_id: str) -> list[str]:
        return self.in_adj.get(page_id, [])

    def find_path(self, from_id: str, to_id: str) -> list[str] | None:
        if from_id == to_id:
            return [from_id] if from_id in self.known_pages else None
        if from_id not in self.out_adj or to_id not in self.out_adj:
            return None

        parent = {from_id: None}
        queue = deque([from_id])

        while queue:
            current = queue.popleft()
            for neighbor in self.out_adj.get(current, []):
                if neighbor == current:
                    continue
                if neighbor not in parent:
                    parent[neighbor] = current
                    if neighbor == to_id:
                        # Reconstruct path
                        path = []
                        node = to_id
                        while node is not None:
                            path.append(node)
                            node = parent[node]
                        return path[::-1]
                    queue.append(neighbor)

        return None

    def orphaned_pages(self) -> list[str]:
        return [pid for pid in self.known_pages if self.in_degree.get(pid, 0) == 0]

    def find_cycles(self) -> list[list[str]]:
        # Tarjan's algorithm for SCCs
        index_counter = [0]
        stack = []
        on_stack = set()
        indices = {}
        lowlink = {}
        sccs = []

        def strongconnect(v: str) -> None:
            indices[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack.add(v)

            for w in self.out_adj.get(v, []):
                if w == v:
                    continue
                if w not in indices:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])

            if lowlink[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == v:
                        break
                if len(scc) > 1:
                    sccs.append(scc)

        for pid in self.out_adj:
            if pid not in indices:
                strongconnect(pid)

        return sccs
```

**Time:** O(V + E) for `find_path` (BFS visits each vertex and edge once) and O(V + E) for `find_cycles` (Tarjan's algorithm is linear). `add_page` is O(k) where k is the number of outbound links. `get_outbound`, `get_inbound`, and `orphaned_pages` are O(1) amortized — BFS explores each node and edge exactly once; Tarjan's algorithm also processes each node and edge once.

**Space:** O(V + E) for the adjacency maps (both forward and reverse), plus O(V) for the BFS parent map and Tarjan's stack — we store both `out_adj` and `in_adj`, each holding all edges, so total space is proportional to the graph size.

**Correctness Argument**

For `find_path`: BFS explores nodes in order of increasing distance from `from_id`. The first time we reach `to_id`, the path recorded via the parent map is a shortest path because BFS processes level by level — any shorter path would have been discovered earlier. The parent map reconstruction walks backward from `to_id` to `from_id`, then reverses to give the forward path.

For `orphaned_pages`: a page is orphaned exactly when no other page links to it. We track `in_degree` by incrementing whenever any page adds an outbound link to that target. Self-loops are excluded from this count, so a page with only a self-loop is still orphaned. The `known_pages` filter ensures we only report pages that were explicitly added — a page referenced as a target but never added has `in_degree > 0` and isn't a real page yet, so it shouldn't appear as orphaned.

For `find_cycles`: Tarjan's algorithm correctly identifies all strongly connected components. A cycle exists wherever there's an SCC of size > 1, since any strongly connected component with multiple nodes contains directed cycles. Self-loops are excluded by design, so they don't inflate the SCC count.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest thing that works: store `out_adj` as a dict of lists. `get_outbound` is a direct lookup, O(1). `get_inbound` naively requires scanning all pages and their outbound links — O(V + E) per query, which is too slow if called repeatedly. So we maintain a second map `in_adj` that we update in `add_page`: whenever page A links to page B, append A to `in_adj[B]`. That makes `get_inbound` a direct lookup too.

For `find_path`, the naive approach is DFS, which finds a path but not necessarily the shortest one. Since all edges have weight 1, BFS gives shortest paths naturally. The key insight is that BFS explores nodes in order of distance from the source, so the first time we reach the target, we've found a shortest path. Use a parent dict to reconstruct the path after BFS completes.

For `orphaned_pages`, the naive approach is checking `len(in_adj[pid]) == 0` for every page — O(V) per query, which is fine for a single call but we can do better. Track `in_degree` as we build the graph: increment `in_degree[target]` in `add_page`. Then `orphaned_pages` is just a filter over `known_pages` checking if `in_degree` is zero. The subtlety is that pages referenced as targets but never added should not be reported as orphaned — they don't exist yet. That's why we maintain `known_pages`.

For `find_cycles`, the naive approach is running DFS from every node and detecting back edges — O(V·(V + E)) worst case. Tarjan's algorithm solves this in O(V + E) by computing strongly connected components in a single pass. The implementation is more involved, but the idea is straightforward: use DFS with `indices` (discovery time) and `lowlink` (lowest reachable ancestor), push nodes onto a stack, and when `lowlink[v] == indices[v]`, pop the stack to form an SCC. Any SCC with more than one node represents a cycle.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **You maintain both forward and reverse adjacency maps** — the interviewer is checking whether you recognize that `get_inbound` needs to be O(1) and are willing to pay the extra space for it. Mentioning the space tradeoff explicitly shows you're thinking about the full cost model, which matters at 100k pages.
- **You handle the "referenced before added" case cleanly** — pages that appear as outbound targets but haven't been added yet need entries in both maps, but they shouldn't show up in `orphaned_pages`. The `known_pages` set is the clean way to distinguish these cases, and explaining why you need it demonstrates you thought through the edge cases.
- **You pick BFS over DFS for `find_path` and can justify it in one sentence** — "BFS finds shortest paths on unweighted graphs" is the right answer, but you should also mention that DFS could return a longer path. If you can reconstruct the path from the parent map without storing full paths in the queue, that's a nice efficiency touch.
- **You state the complexity of every method, including the O(V + E) for Tarjan's** — many people implement Tarjan's correctly but can't explain why it's linear. The key insight is that each node is pushed and popped from the stack exactly once, and each edge is examined exactly once.
- **You discuss what cycles mean in Confluence navigation** — a cycle means there's a loop of pages linking to each other, which can be intentional (a documentation hub linking to related pages) or a sign of poor information architecture. You should mention that cycles aren't inherently bad, but large SCCs might indicate pages that are hard to navigate away from.
- **You handle self-loops consistently across all methods** — the spec says to ignore them, but it's easy to forget in `find_cycles` where a self-loop would create an SCC of size 1. Explicitly skipping `target == page_id` in `add_page` and checking `w == v` in Tarjan's shows attention to detail.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if `add_page` is called multiple times for the same page — should it replace or append outbound links?** — Think about whether duplicate edges should be deduplicated and how that affects `in_degree`.
- **How would you handle `find_path` if pages have weights (e.g., some links are more important than others)?** — Dijkstra's algorithm replaces BFS, but only works with non-negative weights.
- **What if the graph is very large and doesn't fit in memory on a single machine?** — Consider sharding by page ID, but be aware that `find_path` and `find_cycles` across shards require distributed graph algorithms.
- **How would you detect pages that are part of a cycle but not strongly connected to any other cycle?** — This is asking about cycle detection per SCC, which Tarjan's already gives you.
- **What if you need to find all paths between two pages, not just the shortest?** — This is exponential in the worst case, so you'd need to discuss pruning strategies or limiting path length.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
