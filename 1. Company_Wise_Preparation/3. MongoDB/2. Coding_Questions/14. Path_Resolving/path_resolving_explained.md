# Path Resolving — Explained Simply

## The Problem

You have JSON — objects inside objects, with arrays mixed in. You're given a **path** like `["a", "b", "c"]`. Return **every value** that path leads to.

```python
{"a": {"b": [{"c": "foo"}, {"c": "baz"}]}}    path: ["a", "b", "c"]
→ ["foo", "baz"]
```

Notice it's a **list** of results, not one value. That's because of arrays — and arrays are the entire difficulty of this problem.

## The One Rule Everything Hinges On

When you're following a path through nested data, each step asks: *"does this thing consume a path segment?"*

| You're standing on | What the segment means | Path index |
|---|---|---|
| **an object** `{...}` | look up this key | **advances** |
| **an array** `[...]` | apply the *same* segment to every element | **stays put** |
| a string / number / bool | you can't index into it | no match |

> **An array is not a level of the path.** It's a container the path passes straight *through*.

Get that one sentence right and the problem is solved. Get it wrong and you'll quietly lose results or index off the end.

## An Analogy First: A Filing System with Duplicate Drawers

You're told: *"go to the **Sales** cabinet, open the **Regions** drawer, and get the **Manager** file."*

If each of those is a single thing, you end up with one file.

But suppose the **Regions** drawer isn't one drawer — it's a **rack of five identical drawers**, one per region.

The instruction doesn't say "the third drawer". It says "the Regions drawer". So you open **all five** and get the **Manager** file from each. You come back with five files, not one.

Crucially: opening the rack **didn't use up part of your instruction**. You still have "get the Manager file" left to do — you just now have to do it five times.

That's array fan-out. The rack is the array; the instruction step is the path segment; and the rack doesn't consume a step.

## Step-by-Step Example (Narrated)

`{"a": {"b": [{"c": "foo"}, {"c": "baz"}]}}` with path `["a", "b", "c"]`.

Think of a cursor `idx` pointing at which segment we're on.

---

**Start:** node = the whole document, `idx = 0` (segment is `"a"`).

It's an **object**, and `"a"` is a key. Descend into its value, and **advance**: `idx = 1`.

---

**Now:** node = `{"b": [...]}`, `idx = 1` (segment is `"b"`).

Object again, `"b"` is a key. Descend, **advance**: `idx = 2`.

---

**Now:** node = `[{"c": "foo"}, {"c": "baz"}]`, `idx = 2` (segment is `"c"`).

**It's an array.** So: apply the *same* segment to every element. **`idx` does not move.**

We now have two independent branches to explore, both still at `idx = 2`:

---

**Branch 1:** node = `{"c": "foo"}`, `idx = 2`.

Object, `"c"` is a key. Descend, advance: `idx = 3`.

`idx == len(path)` → **the path is used up.** This node is a match: `["foo"]`

---

**Branch 2:** node = `{"c": "baz"}`, `idx = 2`.

Same story → `["baz"]`

---

**Combine:** `["foo"] + ["baz"]` = **`["foo", "baz"]`** ✅

Note that we **`extend`**, not `append`. Appending would give `[["foo"], ["baz"]]` — nested, wrong.

## The Trickiest Example (and What It's Testing)

The problem statement includes this, with an explicit warning:

```python
{"a": [{"b": [{"c": "foo"}, {"c": "bar"}]},
       {"b": [{"c": "blah"}, {"c": ["baz"]}]}]}

path ["a", "b", "c"]  →  ["foo", "bar", "blah", ["baz"]]
```

> *"Note: We're **not** returning `"baz"` by itself here."*

Why does `["baz"]` stay wrapped, when every other array got flattened?

**Because of *when* you meet the array.**

- The arrays under `"a"` and `"b"` are encountered **while path segments remain**. They're containers → fan out through them.
- The `["baz"]` under `"c"` is reached **after the path is fully consumed**. There's nothing left to look up. So it's not a container to walk through — it **is the answer**, exactly as stored.

> **The same list is a thing to walk *through* mid-path, and a thing to *return whole* at the end.**

That distinction is the whole point of this example, and it's what the interviewer is checking.

## The Code

```python
def resolve_path(data, path):
    def resolve(node, idx):
        if idx == len(path):
            return [node]                 # path used up -> this node IS the answer

        if isinstance(node, dict):
            key = path[idx]
            if key in node:
                return resolve(node[key], idx + 1)     # advance
            return []                                  # key absent -> no match

        if isinstance(node, list):
            results = []
            for item in node:
                results.extend(resolve(item, idx))     # SAME idx
            return results

        return []                         # a primitive with path left over

    return resolve(data, 0)
```

Four cases, and each one maps directly to a rule from the table above. The recursion mirrors the data's own shape, so the awkward "arrays don't consume a segment" rule appears exactly **once** instead of being re-derived at every level.

## Three Details That Trip People Up

### 1. Every branch must return a *list*

The contract is "a list of all values". So:

- No match → `[]`
- One match → `[node]`, **not** `node`

Return a bare value from one branch and a list from another, and the caller can't tell what it's holding. This is the single most common way this solution breaks.

### 2. `extend`, not `append`

Each recursive call hands back a *collection*. To combine them into one flat list you splice the items in:

```python
results.extend(resolve(item, idx))     # ✅ ["foo", "bar"]
results.append(resolve(item, idx))     # ❌ [["foo"], ["bar"]]
```

### 3. Falsy values are real matches

`0`, `""`, `False`, `None`, `[]`, `{}` are all legitimate JSON values, and all falsy in Python.

```python
if key in node:      # ✅ asks "does the key exist?"
if node.get(key):    # ❌ drops every falsy value
```

## Bonus: Wildcards Come Almost Free

A follow-up: what if a path segment is `*`, meaning "any key"?

The change is tiny, because the machinery for producing *many* results from one call already exists:

```python
if seg == "*":
    for v in node.values():                # every key instead of one
        results.extend(resolve(v, idx + 1))
```

Note the asymmetry: `*` **does** consume a segment in an object (it stands in for one key), but consumes **nothing** in an array — because arrays never consume segments, wildcard or not.

This is exactly JSONPath's `$.a.*.c`.

## Recursion Depth

Python allows about 1,000 nested calls. Deeply nested JSON — accidentally or maliciously — will blow past that.

The fix is your own stack:

```python
stack = [(data, 0)]
while stack:
    node, idx = stack.pop()
    ...
    for item in reversed(node):     # <- note reversed
        stack.append((item, idx))
```

**Watch the `reversed()`.** A stack pops in the *opposite* order you push. Push elements left-to-right and they come out right-to-left, so your results arrive in scrambled order. Reversing on the way in fixes it.

The nasty part: without `reversed()`, the code still returns all the right *values* — just in the wrong *order*. It passes a `sorted()` comparison and fails on real data.

## How This Differs From "Find a Key Anywhere"

Worth studying alongside [Deep Key Search in Nested JSON](../7.%20Deep_Key_Search_Nested_JSON/README.md), because they look similar and are opposites:

| | Deep key search | Path resolving |
|---|---|---|
| **Question** | "where is this key, anywhere?" | "what's at exactly this route?" |
| **Traversal** | wanders into every value | follows one route, never deviates |
| **Result** | usually the first hit | **everything** the route reaches |
| **Stops early?** | yes, on first match | no — it must find them all |

One is a **search**. The other is a **directed walk with fan-out**.

## Why It's Fast

An interesting finding from the notebook benchmark: the first version grew the document *width* — thousands of sibling keys the path never visits — expecting the slower approach to degrade.

**It didn't.** All approaches stayed flat.

The reason: none of them ever touch an unreachable branch. A key that doesn't match is never followed. **Document size simply isn't a variable.**

So the benchmark was changed to grow what actually matters — the number of *matches*:

| Matches | Frontier | Recursive | Stack |
|---|---|---|---|
| 500 | 14.9 ms | 35.8 ms | 32.0 ms |
| 1,000 | 29.5 ms (2.0×) | 64.2 ms (1.8×) | 66.4 ms (2.1×) |
| 2,000 | 58.6 ms (2.0×) | 133 ms (2.1×) | 131 ms (2.0×) |
| 4,000 | 122 ms (2.1×) | 249 ms (1.9×) | 279 ms (2.1×) |

All linear in the **output** size — which is the best possible, since you have to produce every result.

> **The real takeaway:** cost scales with the size of the *answer*, not the size of the *input*. The genuine difference between the three is **space** and whether they survive deep nesting, not speed.

## Common Mistakes

- **Advancing the path index on arrays.** The single biggest bug. You'll skip a level and silently return nothing.
- **Flattening the final matched value.** `["baz"]` must stay `["baz"]`. Fan-out applies only *before* the path runs out.
- **Returning `node` instead of `[node]`** at the base case.
- **Using `append` instead of `extend`.** Gives nested lists.
- **Branching on truthiness instead of key presence.** Drops `0`, `""`, `False`, `None`.
- **Forgetting the primitive case.** Trying to index into a string should return `[]`, not raise.
- **Forgetting `reversed()` in the iterative version.** Right values, wrong order.

## The Takeaway

> Two kinds of container, two different behaviours. An **object consumes** a path segment; an **array consumes nothing** and multiplies your results instead. Write one recursive function whose branches mirror those cases exactly, make every branch return a list, and combine with `extend`.

And remember the boundary that the `["baz"]` example exists to test: **a container is something to walk through — right up until the path runs out, at which point it becomes the answer.**
