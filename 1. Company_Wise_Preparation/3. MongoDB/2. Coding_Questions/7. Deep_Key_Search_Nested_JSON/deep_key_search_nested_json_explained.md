# Deep Key Search in Nested JSON — Explained Simply

## The Problem

You have a JSON document with objects inside objects inside objects. Given a key name, find its value — **no matter how deep it's buried**.

```json
{
  "id": 101,
  "company_details": {
    "location": { "city": "San Francisco" },
    "departments": {
      "engineering": { "team_count": 5, "lead_developer": "Alex Rivera" },
      "marketing":   { "team_count": 3, "lead_strategist": "Sarah Chen" }
    }
  }
}
```

```
search("lead_strategist")  ->  "Sarah Chen"
search("departments")      ->  the WHOLE departments object, both departments inside
```

## First: A JSON Document Is a Tree

This is the reframe that makes the problem easy.

- Objects `{...}` and lists `[...]` are **branches** — they hold other things.
- Strings, numbers, booleans, and `null` are **leaves** — the ends of the road.

```
                    (root)
        ┌─────────────┼──────────────┐
       id      company_details     active
       101      ┌─────┴─────┐       true
              location  departments
                 │      ┌────┴────┐
               city  engineering marketing
                        │           │
                   team_count   lead_strategist
                        5        "Sarah Chen"
```

"Search at any depth" is just **walk the tree until you find the key**. Once you see it that way, the code writes itself.

## The Walk: Check Here, Then Go Deeper

The whole algorithm is three lines of English:

1. **Am I looking at an object?** If so, check whether the key is right here. If it is, done.
2. **Not here?** Try each of my values in turn, applying these same rules to each.
3. **Am I looking at a list?** Try each item in turn.

That's a **depth-first search** — go all the way down one branch, and only come back up when it dead-ends.

Because you check the current level **before** descending, this is called **pre-order**. And that ordering matters: it means you find the **shallowest** match. If both the top level and a nested object have a key `"x"`, you get the top-level one — which is almost always what someone means by "find this key".

## An Analogy First: Searching a Filing Cabinet

You're looking for a folder labelled "Marketing Leads" in a filing cabinet full of drawers, and inside each drawer, boxes, and inside boxes, more folders.

You don't tip the whole cabinet onto the floor. You:

1. Open drawer 1. **Look at the labels in this drawer** — is "Marketing Leads" here?
2. Not here? Open the first box inside, and apply the same rule.
3. Nothing? Back out, try the second box.
4. Drawer exhausted? Back out, try drawer 2.

And the moment you find it, **you stop**. You don't keep searching the rest of the cabinet out of thoroughness.

That "stop the moment you find it" is called **early exit**, and it's why the search beats the alternative of cataloguing the entire cabinet first.

## Step-by-Step Example (Narrated)

Searching for `"lead_strategist"`.

---

**Level 0 — the root object.** Its keys are `id`, `company_details`, `active`.

Is `lead_strategist` among them? **No.** So descend into each value.

- `id` is `101` — a number, a leaf. Nothing to search. Back up.
- `company_details` is an object → **go in.**

---

**Level 1 — `company_details`.** Keys: `location`, `departments`.

Is `lead_strategist` here? **No.** Descend.

- `location` is an object → go in.

---

**Level 2 — `location`.** Keys: `street`, `city`, `state`, `zipcode`.

**No.** All four values are strings — leaves, nothing to descend into. **Dead end. Back up.**

---

**Back at Level 1**, try the next value: `departments` → go in.

---

**Level 2 — `departments`.** Keys: `engineering`, `marketing`.

**No.** Descend into `engineering` first.

---

**Level 3 — `engineering`.** Keys: `team_count`, `lead_developer`.

**No** — close, but `lead_developer` isn't `lead_strategist`. Both values are leaves. **Back up.**

---

**Back at Level 2**, try `marketing` → go in.

---

**Level 3 — `marketing`.** Keys: `team_count`, `lead_strategist`.

**Found it.** Return `"Sarah Chen"`. ✅

And crucially: we return **immediately**, all the way up through every waiting call. We never look at `active`, and we never would have looked at anything after `marketing` either.

---

### The other required query

`search("departments")` matches at **Level 2**, and the value there is the entire nested object:

```json
{
  "engineering": { "team_count": 5, "lead_developer": "Alex Rivera" },
  "marketing":   { "team_count": 3, "lead_strategist": "Sarah Chen" }
}
```

So the return type isn't "a string" or "a number" — it's **any JSON value**, objects included. And you hand back the object itself, not a flattened or copied version of it.

## The Bug That Breaks Most Implementations

Here's the one thing this problem is really testing.

The natural way to say "not found" is to return `None`:

```
def deep_search(obj, key):
    ...
    return None        # <-- looks fine
```

**It isn't.** Because `null` is a perfectly legal JSON value:

```json
{ "middle_name": null }
```

Now `search("middle_name")` returns `None`, and `search("banana")` returns `None`. **The caller cannot tell "the value is null" from "the key doesn't exist."**

Worse, the *search itself* can't tell either. Look at the recursive step:

```
found = deep_search(value, key)
if found is not None:      # <-- WRONG
    return found
```

After genuinely finding `middle_name: null`, this says "hmm, `None`, must not be here" and **keeps searching other branches** — eventually returning something from the wrong place, or nothing at all.

### The fix: a sentinel

Create one unique object that can never be confused with any piece of data:

```
_MISSING = object()        # a value nothing in JSON can ever equal
```

Return `_MISSING` for "not found", and check it with `is` (identity), never `==`:

```
found = deep_search(value, key)
if found is not _MISSING:
    return found
```

Now `None` is just a value like any other, and "not found" has its own unambiguous signal.

> Other perfectly good answers: return a pair `(found: bool, value)`, or raise `KeyError`. What's *not* acceptable is silently overloading `None`.

### The same trap, with falsy values

Even worse than `if found is not None:` is:

```
if found:        # <-- breaks on FIVE different valid values
```

Because all of these are legal JSON and all of them are falsy in Python:

| Value | Falsy? |
|---|---|
| `0` | yes |
| `""` | yes |
| `false` | yes |
| `[]` | yes |
| `{}` | yes |

A key whose value is `0` would be reported as missing. Always compare against the sentinel by identity.

## The Three Questions to Ask First

The source page for this question explicitly flags three ambiguities. In a real interview, **asking these is part of the answer**:

**1. What if the key appears more than once?**

`team_count` appears twice in the example — 5 and 3. "Return the value" implies one, so the default is *first in traversal order*. But say which order that is, and offer a `find_all` variant. Three extra lines, and it shows you noticed rather than guessed.

**2. Should lists be searched?**

The statement says values may be lists. Searching them is the safer reading — a list is a *container*, not a value, so a key inside `{"tags": [{"name": "x"}]}` is still in the document.

One subtlety: you **descend through** lists, but a list can never **match**. List positions are indices, not keys — `search("0")` should not find the first element.

**3. What's the return type when the match is an object?**

`departments` proves it: the answer can be an entire nested object. So the return type is "any JSON value", and you return the live sub-object unchanged.

## Two Things Worth Knowing About the Alternatives

### "Just flatten it first" — sometimes right, usually not

You could walk the document once, collecting every key into one flat dictionary, then look up the answer.

**Good for:** many queries against the same document. Pay O(n) once, answer every query instantly afterwards.

**Bad as a one-shot answer**, for two reasons:

- **No early exit.** You visit every node even when the answer was in the first key you'd have checked.
- **It destroys duplicates.** `team_count` exists twice; a flat dictionary keeps one. You've thrown away information before the question was even asked.

The benchmark makes the first point sharply. With a query that matches near the front:

| Document size | Flatten first | DFS with early exit |
|---|---|---|
| 1,000 keys | 9.2 ms | 0.02 ms |
| 8,000 keys | 68.4 ms | 0.02 ms |

Flattening doubles as the document doubles. DFS **doesn't move at all** — its cost depends on how far it had to walk to find the answer, not on how big the document is.

### Recursion has a depth limit

Python allows about 1,000 nested function calls before raising `RecursionError`. Each level of nesting in your document costs one call.

A document 5,000 levels deep — whether by accident or by an attacker — crashes the recursive version. The fix is to keep your own stack in a list:

```
stack = [doc]
while stack:
    node = stack.pop()
    ...
    stack.extend(reversed(node.values()))
```

**Watch the `reversed()`.** A stack is last-in-first-out, so pushing children left-to-right makes you visit them right-to-left. Reversing them on the way in restores the same order as the recursive version. Without it the code still "works" — it just quietly picks a different duplicate, which is the nastiest kind of bug.

## A Better Return Value: Paths

Once you're returning *all* matches, return **where** each one was too:

```
[("company_details.departments.engineering.team_count", 5),
 ("company_details.departments.marketing.team_count", 3)]
```

A path is **actionable** — it survives duplicates, it tells you which one you got, and you can use it to read or write that exact spot later. This is what `jq`, JSONPath, and MongoDB's own dotted field notation all give you.

And if the caller already **knows** the path, don't search at all — walk straight down:

```
get_by_path(doc, "company_details.location.city")   # O(depth), no searching
```

Search is for when you don't know where something is. A path is for when you do.

## Common Mistakes

- **Using `None` for "not found".** `null` is valid JSON. Use a sentinel.
- **Writing `if found:` instead of `if found is not _MISSING:`.** Silently drops `0`, `""`, `false`, `[]`, `{}`.
- **Descending before checking the current level.** You'd return the *deepest* match instead of the shallowest.
- **Not stopping after a match.** The early exit is most of the performance win.
- **Treating a list index as a key.** Descend through lists; never let one match.
- **Copying the matched object.** The spec asks for the object, not a snapshot of it.
- **Forgetting `reversed()` in the iterative version.** Same answer set, different pick among duplicates — passes casual testing, fails on real data.
- **Assuming no cycles without saying so.** JSON parsed from text can't have them; a hand-built Python dict can (`d["self"] = d`) and will loop forever. State your assumption.

## The Takeaway

> Nested containers are a **tree**, and "find this anywhere" is a **tree walk**. Check the current level before descending so you get the shallowest match, stop the moment you find it, and — because every value including `null` is a legal answer — use a **sentinel** to say "not found" rather than overloading a real value.

The same walk, with the comparison swapped out, becomes a general query engine: find every key matching a pattern, every value over a threshold, every path to a type. Separating *how you walk* from *what you're looking for* is what turns one function into a tool.
