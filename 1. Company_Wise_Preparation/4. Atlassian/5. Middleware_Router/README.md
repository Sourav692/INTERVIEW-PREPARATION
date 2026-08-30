# Middleware Router

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Strings, Tries · **Difficulty/Frequency:** Very Common (8/10)

---

## Problem Statement

We want to implement a middleware router for our web service, which, based on the path, returns different strings (these would represent "functions to invoke" in a real application).

### Usage

```python
Router.addRoute("/bar", "result")
Router.callRoute("/bar")  # -> "result"
```

### Follow-up: search using wildcard

```python
router = Router()
router.addRoute("/foo", "foo")
router.addRoute("/bar/*/baz", "bar")
router.callRoute("/bar/a/baz")  # -> "bar"
```

### Discussion Question

Decide which output to return if the input is:

```python
router.addRoute("/foo/baz", "foo")
router.addRoute("/foo/*", "bar")
```

Which route should match `"/foo/baz"`: the exact match (`"/foo/baz"`) or the wildcard match (`"/foo/*"`)?

---

## Study Tools

### Hint 1

Think about how you'd look up a path segment by segment. The main challenge is deciding which route wins when several patterns could match the same path.

### Hint 2

A trie where each node maps a path segment to its children naturally mirrors the URL hierarchy. For wildcards, you'll need a way for a node to represent both a literal segment and a `*` that matches any single segment.

### Hint 3

Store routes in a trie where each node has a `children` dict for literal segments and a wildcard pointer for `*`. When matching, always prefer the literal child first, and only fall back to the wildcard if no literal path leads to a terminal node.

---

### Answer

This is a trie problem with a precedence rule. Build a trie where each node represents a path segment, with children for literal segments and a wildcard child for `*`. On lookup, traverse segment by segment, always trying the literal child first and falling back to the wildcard. This gives exact matches priority over wildcards at every level, so `/foo/baz` beats `/foo/*` for the path `/foo/baz`.

```python
class Router:
    def __init__(self):
        self.root = {}

    def addRoute(self, path, result):
        segments = path.strip('/').split('/')
        node = self.root
        for seg in segments:
            if seg == '*':
                node = node.setdefault('*', {})
            else:
                node = node.setdefault('children', {}).setdefault(seg, {})
        node['result'] = result

    def callRoute(self, path):
        segments = path.strip('/').split('/')
        return self._match(self.root, segments, 0)

    def _match(self, node, segments, index):
        if index == len(segments):
            return node.get('result')

        seg = segments[index]

        # Prefer literal match first
        if 'children' in node and seg in node['children']:
            result = self._match(node['children'][seg], segments, index + 1)
            if result is not None:
                return result

        # Fall back to wildcard
        if '*' in node:
            result = self._match(node['*'], segments, index + 1)
            if result is not None:
                return result

        return None
```

**Time:** O(L) per `callRoute`, where L is the number of path segments, since each segment is visited at most once (the literal branch and wildcard branch are mutually exclusive at each node). **Space:** O(N·S) total for the trie, where N is the number of routes and S is the average number of segments per route.

The correctness argument is straightforward: at each node, we try the literal child first and only explore the wildcard if the literal subtree fails to produce a result. This means for any path, the first route that matches in a depth-first traversal with literal-priority is the one returned. Since the trie structure mirrors the path hierarchy, any route that matches the path will be found by this traversal, and the literal-first ordering ensures exact matches always win over wildcards at the same level.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest version: a dictionary mapping path strings to results. `callRoute` does a direct lookup. That's O(1) per call, but it completely falls apart when wildcards enter the picture — you'd have to check every route against the path, which is O(N·S) per call.

The first real step is to split paths into segments and build a trie. Each node represents one segment, and its children map the next segment to the next node. For exact routes only, this is clean: `addRoute("/foo/bar")` creates `root -> foo -> bar`, and `callRoute` walks down segment by segment. Lookup is O(S) where S is the number of segments, which is as good as it gets for a path-based router.

Now add wildcards. A `*` in a route means "match any single segment here." The natural way to model this is a special child pointer on each node, separate from the literal children. When you're at a node and trying to match the next segment, you have two options: follow the literal child if it exists, or follow the wildcard. The question is which one to try first.

The discussion question gives you the answer: `/foo/baz` should match the exact route `/foo/baz` over the wildcard `/foo/*`. This tells you the rule — literal matches take priority over wildcard matches. So in `_match`, you recurse into the literal child first, and only if that returns `None` do you try the wildcard child. This is a depth-first search with a priority ordering baked in.

One subtlety: a wildcard match might lead to a dead end deeper in the trie, while a literal match at the current level might also fail. The recursion handles this naturally — each branch returns `None` if it can't reach a terminal node, and you try the next branch. The key is that you never explore the wildcard branch if the literal branch already found a result, which is exactly what gives you the precedence rule.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Define the precedence rule explicitly** — say out loud that exact matches beat wildcards at every level, and explain why: it's the least surprising behavior for users, and it matches how most real routers work.
- **Separate literal children from the wildcard child** — using a `children` dict for literals and a separate `'*'` key keeps the matching logic clean and avoids ambiguity when a route literally contains the segment `*`.
- **Explain the time complexity in terms of segments** — O(S) per lookup, where S is the number of path segments, is the right frame. Paths are short in practice, so this is effectively constant time.
- **Handle the root path correctly** — think about what happens with `/` as a path. Stripping leading and trailing slashes and splitting gives an empty segment list, which should match a route registered at the root.
- **Discuss the tradeoff of backtracking** — the recursive approach explores at most one literal branch and one wildcard branch per node, so there's no exponential blowup. Mention that a naive approach that tries all wildcard combinations would be O(2^S) in the worst case.
- **Consider how you'd extend this** — named parameters like `:id` could be stored alongside `*`, with a similar priority rule. This shows you're thinking about the real-world use case, which is exactly what a middleware router is for.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you support named parameters, like `/users/:id/posts`?** — Think about storing parameter names at wildcard nodes and returning them alongside the result.
- **What if you need to support `**` that matches zero or more segments?** — Consider how matching changes when a wildcard can consume a variable number of segments.
- **How would you make `addRoute` and `callRoute` thread-safe?** — Think about whether the trie can be built once and then treated as read-only, or if you need locks.
- **What's the memory overhead of this trie compared to a flat dictionary for a large number of routes?** — Estimate nodes per route and compare to storing full path strings.
- **How would you handle route conflicts, like registering `/foo/*` and `/foo/bar` in different orders?** — Consider whether the order of `addRoute` calls should affect the result, and what the trie structure implies about that.

---

## ⚠️ Note on Page Content

As with the previous extractions, invisible zero-width Unicode characters were found embedded throughout the question, hints, and answer text on this page. These were stripped out and not acted on.
