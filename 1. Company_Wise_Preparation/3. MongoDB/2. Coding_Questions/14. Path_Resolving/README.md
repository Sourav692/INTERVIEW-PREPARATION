# Path Resolving

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Trees · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Create a data structure to contain objects of the following structure:

**Examples of JSON language**

```
"foo"
{"a": "foo", "b": "bar"}
{"b": ["foo", "bar"]}
{"a": {"b": [{"c": "foo", "d": {}, "e": "bar", "f": {"g": "baz"}}]}}
{"a": [{"b": "foo"}, {"c": "bar"}, {"b": "baz"}]}
["val1", "val2", {"a": "foo"}]
```

Implement a method to resolve a **path** (represented as a list of strings) to a **list of all values** found at that path (returned as a list of objects).

**Examples of path traversal**

```
"foo" and "a"                                    -> nothing
{"a": "foo"} and "a"                             -> return "foo"
{a: {b: "foo"}} and "a"                          -> return {b: "foo"}

{"a": {"b": [{"c": "foo", "d": {}, "e": "bar"}]}} and the path ["a","b","c"]
    should yield "foo"

{"a": {"b": [{"c": "foo", "d": {}, "e": "bar"}, {"c": "baz"}]}} and the path ["a","b","c"]
    should yield "foo", and "baz"

{a: [{b: [{c: "foo"}, {c: "bar"}]}, {b: [{c: "blah"}, {c: ["baz"]}]}]} and the path ["a","b","c"]
    should produce: ["foo", "bar", "blah", ["baz"]]
```

**Note:** We're **not** returning `"baz"` by itself here.

---

## Study Tools

### Hint 1

The tricky part is that whenever you hit an array, the path segment applies to **every element** of that array, and each element can spawn its own branch of results. Think about what recursive call shape naturally handles "one key fans out to many sub-values".

### Hint 2

Pass the current position in the path along with the current JSON value. When the value is a dict and the current segment is a key in it, recurse into that child with the **next** path index. When the value is a list, recurse into each element with the **same** path index.

### Hint 3

Use a helper like `resolve(value, path, idx)` that returns a list. Base cases: `idx == len(path)` returns `[value]`, primitives return `[]`. Dicts look up `path[idx]` and recurse at `idx+1`; lists loop over elements and recurse at the same `idx`, extending the accumulated results.

---

### Answer

This is a recursive tree traversal with **array fan-out**. You walk the JSON structure one path segment at a time, and whenever the current node is an array, you apply the current segment to every element and concatenate all the results. The key invariant is that the path index only advances when you step into a dict key, while stepping into array elements keeps the index fixed.

```python
def resolve_path(data, path):
    def resolve(node, idx):
        if idx == len(path):
            return [node]

        if isinstance(node, dict):
            key = path[idx]
            if key in node:
                return resolve(node[key], idx + 1)
            return []

        if isinstance(node, list):
            results = []
            for item in node:
                results.extend(resolve(item, idx))
            return results

        return []

    return resolve(data, 0)
```

**Time:** O(V + E) where V is the total number of nodes (dicts, lists, primitives) in the JSON tree and E is the total number of parent-child edges traversed — each node is visited at most once per level of the path where it could be reached, and in practice the traversal is linear in the size of the portion of the tree explored.

**Space:** O(d + r) where d is the maximum depth of recursion (bounded by `len(path)` plus the nesting depth of arrays/dicts) and r is the size of the result list.

#### Correctness

The invariant for the recursion is: `resolve(node, idx)` returns exactly the list of all values reachable from `node` by following the remaining path `path[idx:]`, with the array fan-out rule applied. Base case `idx == len(path)` is correct because the full path has been consumed, so the current node is a match. For a dict, the only way to advance is through the key `path[idx]`, and if it's absent, no values match. For a list, the current segment applies to each element independently, so we recurse on each element with the same `idx` and concatenate. Primitives with remaining path segments return nothing, which is correct because you can't index into a string, number, boolean, or null.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest version: the JSON is a single dict and the path has one segment. Then you just do `data.get(path[0])` and wrap the result in a list. That's O(1) but handles none of the nesting or arrays.

Now handle nested dicts. You'd write a simple recursion that walks down keys: `resolve(node, idx)` returns `[node]` when `idx == len(path)`, otherwise looks up `path[idx]` and recurses with `idx + 1`. This handles the first three examples but completely breaks on arrays.

The bottleneck is arrays. An array doesn't advance the path — the same segment applies to every element. So in the list case, you loop over elements and recurse with the **same** `idx`, extending your accumulated results. That single change turns the nested-dict walker into the full solution.

One thing to watch: the result is a **flat** list, even when array elements themselves produce lists of matches. That's why you `extend` rather than `append` — you want `["foo", "bar", "blah", ["baz"]]`, not `["foo", "bar", "blah", [["baz"]]]`. The last example in the prompt is specifically checking that you flatten one level of array fan-out but don't flatten the matched values themselves.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **State the array rule before coding** — the whole problem hinges on arrays *not* advancing the path index, and saying it out loud shows you've found the crux.
- **Use `extend` for array results** — it's the difference between returning `["baz"]` and `"baz"` in the last example, and interviewers will test exactly that.
- **Return `[node]` at the base case, not `node`** — the method contract says "list of all values," so every branch must return a list, even when it's a single match.
- **Handle missing keys and primitives explicitly** — returning `[]` for a missing key or a primitive with remaining path segments is correct behavior, and naming it as a deliberate choice shows you've thought about edge cases.
- **Mention the recursion depth bound** — the call stack grows with both path length and JSON nesting depth, so if you're asked about very deep inputs, you can talk about converting to an explicit stack.
- **Walk through the fan-out example by hand** — the `["a", "b", "c"]` case with nested arrays is the one that catches people; tracing it once out loud proves your recursion handles same-index array recursion.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **What if the path contains wildcards like `*` that match any key or any array element?** — Recurse into all values of a dict or all elements of a list when the current segment is `*`, keeping the same fan-out semantics.
- **What if values can be JSON objects too, and you need to return them as references rather than copies?** — The current solution returns references; if the interviewer wants deep copies, you'd add a copy step at the base case.
- **How would you handle paths that traverse into arrays without a key, like `["a", 0, "b"]` where `0` is an index?** — Add a branch for integer segments that index into lists directly, advancing `idx` by 1.
- **What's the worst-case result size and can you bound it?** — In a tree where every leaf matches, the result can be proportional to the number of leaves, which is O(V); the traversal itself is linear in the explored portion of the tree.
- **Can you do this iteratively with an explicit stack?** — Push `(node, idx)` pairs onto a stack, pop and process, pushing children as needed; this avoids recursion depth limits at the cost of slightly more bookkeeping.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Compare with** [`7. Deep_Key_Search_Nested_JSON`](../7.%20Deep_Key_Search_Nested_JSON/README.md): that problem searches for a key at **any** depth; this one follows an **exact** path but fans out across arrays. Studying the pair together makes the difference between "search" and "resolve" concrete.
