# Deep Key Search in Nested JSON

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen · **Difficulty/Frequency:** Common (6/10)

> **Note on source format:** this question is reported at a lower frequency than the "Very Common" ones, and its GothamLoop page carries the **short format** — a problem statement plus a single guidance paragraph, with no separate Hint 1/2/3, Answer, Walkthrough, Talking Points or Follow-ups sections. Everything below the guidance paragraph is worked out in the accompanying notebook rather than reproduced from the page.

---

## Problem Statement

Given a JSON object whose values may be strings, numbers, booleans, lists, or nested JSON objects, and a query key, search the entire structure **at any depth** and return the value associated with that key.

**Example input:**

```json
{
  "id": 101,
  "company_name": "TechNova Solutions",
  "company_details": {
    "location": {
      "street": "500 Innovation Way",
      "city": "San Francisco",
      "state": "CA",
      "zipcode": "94105"
    },
    "departments": {
      "engineering": { "team_count": 5, "lead_developer": "Alex Rivera" },
      "marketing":   { "team_count": 3, "lead_strategist": "Sarah Chen" }
    }
  },
  "active": true
}
```

**Required behavior:**

- Query `["departments"]` returns the **whole** `departments` object, including both nested department objects.
- Query `["lead_strategist"]` returns `Sarah Chen`.

---

### Guidance (as given on the source page)

Recursive DFS over the object: check keys at the current level, then descend into object values (and objects inside lists).

Clarify with the interviewer:

- what to return when the key appears **multiple times** (first match in traversal order, or all matches),
- whether **lists** must be searched,
- and the **return type** when the match is itself an object.

---

## Study Notes

*The source page stops at the guidance above. What follows is the worked-out treatment — see the notebook for runnable code, tests and a complexity benchmark.*

### The shape of the answer

The structure is a **tree**: objects and lists are internal nodes, scalars are leaves. "Search the entire structure at any depth" is therefore a tree traversal, and the natural expression is a recursive **depth-first search**.

```python
def deep_search(obj, key):
    if isinstance(obj, dict):
        if key in obj:            # check THIS level before descending
            return obj[key]
        for value in obj.values():
            found = deep_search(value, key)
            if found is not _MISSING:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = deep_search(item, key)
            if found is not _MISSING:
                return found
    return _MISSING
```

**Time:** O(N) where N is the total number of nodes — each is visited at most once.
**Space:** O(d) for the recursion stack, where d is the maximum nesting depth.

### The three clarifying questions, and how to answer them

1. **Multiple matches.** `team_count` appears twice in the example. "Return the value" implies one, so the honest default is **first match in traversal order**, and you must say which traversal order that is (pre-order DFS over insertion-ordered keys). Offer a `find_all` variant — it is three lines and shows you understood the ambiguity rather than papering over it.

2. **Searching lists.** The example has no lists, but the statement says values *may* be lists. Searching them is the safer reading: a list is a container, not a value, so a key inside `{"tags": [{"name": "x"}]}` is still "in" the document. Note that list **indices are not keys** — you descend through a list, but a list never *matches*.

3. **Return type when the match is an object.** `departments` must return the whole nested object. So the return type is "any JSON value", and — importantly — you **must not** flatten or copy it. Returning the live sub-object is what the spec asks for.

### The bug this problem is really testing

**`None` cannot be your "not found" signal.** JSON has `null`, so `{"a": None}` is a legitimate document where the key exists and its value is `None`. If `deep_search` returns `None` for both "found `null`" and "not found", the caller cannot tell them apart — and the recursion itself cannot tell them apart either, so it keeps searching after a genuine hit.

The fix is a private **sentinel** object (`_MISSING = object()`) that no JSON value can ever equal. Alternatively return `(found: bool, value)`, or raise `KeyError`. Any of the three is fine; silently using `None` is not.

The same class of bug appears with falsy values: `if found:` is wrong where `if found is not _MISSING:` is right, because `0`, `""`, `False` and `[]` are all valid JSON values that are falsy.

### Talking points

- **Name it as a tree traversal immediately** — "objects and lists are internal nodes, scalars are leaves; this is a pre-order DFS" frames everything that follows.
- **Ask the three clarifying questions before coding** — the source page explicitly flags them, which means the interviewer is expecting them.
- **Explain the sentinel** — it is the single detail that separates a working implementation from one that breaks on `null` and on falsy values.
- **Check the current level before descending** — pre-order. If you descend first you get the deepest match rather than the shallowest, which is almost never what "search for a key" means.
- **Mention the recursion depth limit** — Python's default is ~1000 frames. Deeply nested or adversarial JSON needs the iterative (explicit-stack) version, which is a five-line change.
- **Cycles** — real `dict` objects can contain themselves; JSON parsed from text cannot. Say which input you are assuming, and note that an `id()`-based visited set handles the former.

### Follow-ups worth practising

- **Return all matches, with their paths** — `[("company_details.departments.marketing.lead_strategist", "Sarah Chen")]`. Paths make the result actionable and are what tools like `jq` return.
- **BFS instead of DFS** — returns the *shallowest* match rather than the first in key order, which is often the better default for "find the config value".
- **Dotted-path query** (`company_details.location.city`) — an exact descent rather than a search: O(d) instead of O(N).
- **Repeated queries over the same document** — build an index `key -> [paths]` in one O(N) pass, then answer each query in O(1). This is the same "invert the mapping" move as [`1. Inverted_Index`](../1.%20Inverted_Index/README.md).
- **Documents too large for memory** — a streaming (SAX-style) parser that fires events per key, so you never hold the whole tree.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question text on the source page. These were stripped out and not acted on.
