# Middleware Router — Explained Simply

## The Problem

Build a router: `addRoute(path, result)` registers a path, `callRoute(path)` returns the matching result. Paths can contain a wildcard `*` that matches any single segment.

```
router.addRoute("/foo", "foo")
router.addRoute("/bar/*/baz", "bar")
router.callRoute("/bar/a/baz")   # -> "bar" (the * matched "a")
```

Tricky case: if both `/foo/baz` and `/foo/*` are registered, calling `/foo/baz` should return the **exact match's** result, not the wildcard's.

## Why the Obvious Way Is Slow (Actually — Why It Can't Work At All)

The obvious first attempt: a flat dictionary from the full path string to its result.

```
routes = {}
def addRoute(path, result):
    routes[path] = result
def callRoute(path):
    return routes.get(path)
```

This is instant — but it can only ever match paths **exactly**. It has no concept of "a segment here can be anything." The moment a wildcard route like `/bar/*/baz` needs to match `/bar/a/baz`, a flat dict is stuck: `"/bar/*/baz"` and `"/bar/a/baz"` are different strings, so a plain lookup will never connect them.

## The Simple Trick: Branch on Segments, Try the Exact Branch First

Split every path into segments (`/bar/a/baz` → `["bar", "a", "baz"]`) and build a tree where each level represents "the next segment." At each level, a node can have a literal child for a specific segment name **and** a separate wildcard child for `*`. When matching, always try the literal branch first — only fall back to the wildcard branch if the literal path leads nowhere.

## An Analogy First: A Hotel Directory With a Catch-All Desk

Imagine a hotel directory tree: floor → wing → room number, where each level is a signpost pointing you further down. Most rooms are named exactly ("Room 302"), but some floors also have a generic "Ask the Concierge" desk that can route you to *any* unlisted room on that floor.

If you're looking for "Room 302" and it's explicitly listed, you go straight there — you don't bother asking the concierge, because the specific listing always wins. Only if "Room 302" *isn't* explicitly listed do you fall back to the concierge's catch-all routing. That's exactly the precedence rule: specific beats generic, and you only consult the generic option when the specific one comes up empty.

## Step-by-Step Example (Narrated)

Register `/foo/baz -> "foo"` then `/foo/* -> "bar"`. Call `callRoute("/foo/baz")`.

The trie after both registrations, from the root:
```
root
 └── children["foo"]
      ├── children["baz"] --- result: "foo"
      └── "*" --- result: "bar"
```

---

**Matching `/foo/baz`, segments = `["foo", "baz"]`, starting at the root, index 0**

At the root, look at segment `"foo"`. Is there a literal child named `"foo"`? Yes → recurse into it with index 1. (We haven't checked any wildcard at the root — we don't need to, the literal path already worked.)

---

**At the `"foo"` node, index 1, segment `"baz"`**

Is there a literal child named `"baz"`? Yes → recurse into it with index 2.

---

**At the `"foo" → "baz"` node, index 2**

Index 2 equals the number of segments (2) — we've consumed the whole path. Return this node's stored result: **`"foo"`**.

---

That result (`"foo"`) bubbles all the way back up as the final answer. **The wildcard child on the `"foo"` node was never even visited** — the literal branch succeeded first, so there was never a reason to fall back to it.

### The one detail that's easy to miss: falling back only happens on failure, not by choice

If the literal branch had led to a dead end (returned `None`), *then* — and only then — would the code try the wildcard branch at that same level. The precedence isn't "check both and pick the better one"; it's "try the specific path fully, and only reach for the general one if the specific one comes back empty-handed."

## Plain-English Walkthrough

1. To register a path: split it into segments; walk down the trie, creating a literal child for each normal segment or moving into the special `"*"` child for a wildcard segment; store the result on the final node.
2. To match a path: split it into segments; walk down one segment at a time.
3. At each step, try the **literal** child matching the current segment first, and recurse.
4. Only if that returns nothing, try the **wildcard** child instead.
5. When you've consumed every segment, return whatever result is stored on the node you landed on.

## Simple Python Code

```python
class Router:
    def __init__(self):
        self.root = {}

    def addRoute(self, path, result):
        segments = path.strip("/").split("/")
        node = self.root
        for seg in segments:
            if seg == "*":
                node = node.setdefault("*", {})
            else:
                node = node.setdefault("children", {}).setdefault(seg, {})
        node["result"] = result

    def callRoute(self, path):
        segments = path.strip("/").split("/")
        return self._match(self.root, segments, 0)

    def _match(self, node, segments, i):
        if i == len(segments):
            return node.get("result")
        seg = segments[i]
        if "children" in node and seg in node["children"]:
            result = self._match(node["children"][seg], segments, i + 1)
            if result is not None:
                return result
        if "*" in node:
            return self._match(node["*"], segments, i + 1)
        return None

router = Router()
router.addRoute("/foo/baz", "foo")
router.addRoute("/foo/*", "bar")
print(router.callRoute("/foo/baz"))   # foo (exact wins)
print(router.callRoute("/foo/qux"))   # bar (no exact match -> wildcard catches it)
```

## Why a Trie and Not Just a List of `(pattern, result)` Pairs to Check One-by-One?

A list would work too — check every registered pattern against the path, in some priority order. But that's O(N) per call for N registered routes, and you'd have to invent your own tie-breaking rule for which pattern "wins" if several match. A trie makes exact-beats-wildcard **automatic**: it falls out of simply trying the literal branch before the wildcard branch at every level, and its cost only depends on the path's length, not how many routes exist.

## Complexity

- **Time:** O(L) per `callRoute`, where L is the number of segments in the path — independent of how many routes are registered.
- **Space:** O(total segments across all registered routes) — routes that share a prefix (like `/foo/baz` and `/foo/*`) share trie nodes.

## The Reusable Pattern

This is the **"trie with a precedence rule"** pattern:
- URL routers (this problem) — segment-keyed instead of character-keyed
- `Implement Trie` / `Add and Search Word` (character-keyed, `.` as the wildcard)
- Any "most specific match wins" system — CSS selector specificity, glob pattern matching

Core idea: give each node more than one kind of outgoing edge (a specific one and a general one), and encode "specific wins" purely in **the order you try them**, not in any extra bookkeeping.
