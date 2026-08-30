# Jira Issue CSV Exporter — Explained Simply

## The Problem

You're given a list of Jira issues (dicts) and a list of field names. Turn them into a valid CSV string — but some values contain commas or quotes, which would normally corrupt a CSV file if you just joined them with commas.

Example:

```
fields = ["id", "summary", "status", "assignee"]

issues = [
    {"id": "PROJ-1", "summary": "Fix login bug",       "status": "Done",        "assignee": "alice"},
    {"id": "PROJ-2", "summary": "Add, export feature",  "status": "In Progress", "assignee": "bob"},
    {"id": "PROJ-3", "summary": 'He said "hello"',      "status": "Todo",        "assignee": None},
]
```

Expected output:

```
id,summary,status,assignee
PROJ-1,Fix login bug,Done,alice
PROJ-2,"Add, export feature",In Progress,bob
PROJ-3,"He said ""hello""",Todo,
```

## Why the Obvious Way Is Slow (Actually — Why It's *Wrong*)

The obvious first attempt:

```
for each issue:
    join its field values with commas
join all rows with newlines
```

This isn't a *speed* problem — it's a **correctness** problem. Look what happens to `PROJ-2`'s summary, `"Add, export feature"`. It has a comma in it. Join naively and you get:

```
PROJ-2,Add, export feature,In Progress,bob
```

That's now **5** comma-separated fields instead of 4 — anyone reading this CSV back would think `"Add"` and `" export feature"` are two separate columns. The row structure is silently destroyed. Same problem with `PROJ-3`'s embedded `"` — it would prematurely look like the start/end of a quoted field.

## The Simple Trick: One Rule, Applied Everywhere

CSV only cares about three characters: comma, double-quote, and newline. The rule:

> If a value contains any of those three characters, double every `"` inside it, then wrap the whole thing in a pair of `"..."`.

That's it. Apply this **one rule** to every single value — header included — and nothing can ever go wrong, no matter what's inside the value.

## An Analogy First: A Suitcase With a Secret Compartment

Think of each CSV field as an item you're mailing in a box. Most items (like `"alice"` or `"Done"`) ship fine in a plain box — nothing about them could be mistaken for packing tape or a shipping label.

But some items are *dangerous* to ship loose — like a `"comma"` or a literal `"` character — because they look exactly like the box's own boundary markers. So for those items, you wrap them in bubble wrap (double the quotes) and put them inside a sealed inner box (`"..."`). Anyone unpacking it knows: "this whole sealed box is ONE item, no matter what's printed on the outside."

## Step-by-Step Example (Narrated)

Let's trace `escape_field` on all four values of `PROJ-3`: `"PROJ-3"`, `'He said "hello"'`, `"Todo"`, `None`.

---

**Value: `"PROJ-3"`**
Does it contain `,`, `"`, or `\n`? No. → Leave it exactly as-is: `PROJ-3`

---

**Value: `'He said "hello"'`** (the raw string is `He said "hello"`)
Does it contain `,`, `"`, or `\n`? Yes — it has two `"` characters.
Step 1 — double every `"` inside: `He said ""hello""`
Step 2 — wrap the whole thing in quotes: `"He said ""hello"""`
That's the final field text.

---

**Value: `"Todo"`**
Contains none of the special characters → leave as-is: `Todo`

---

**Value: `None`**
`None` is a special case handled *before* the character check: it always becomes an empty string `""` (a genuinely empty field, not the two-character text `"None"`).

---

Join these four results with commas: `PROJ-3,"He said ""hello""",Todo,` — which matches the expected output exactly.

### The one detail that's easy to get backwards

You must **double the quotes before wrapping**, not after. If you wrapped first (`"He said "hello""`) and then tried to double the quotes, you'd double the *wrapper* quotes too and corrupt the result. Order matters: escape the inside first, then seal the box.

## Plain-English Walkthrough

1. Build the header row by running every field name through the escape rule and joining with commas.
2. For each issue, look up each field's value (`None` or a missing key both become `""`).
3. Run every value through the same escape rule.
4. Join that row's escaped values with commas.
5. Join all rows (header + data) with newlines.

## Simple Python Code

```python
def escape_field(value):
    if value is None:
        return ""
    s = str(value)
    if "," in s or '"' in s or "\n" in s:
        s = s.replace('"', '""')   # double internal quotes FIRST
        return f'"{s}"'            # then wrap
    return s

def export_to_csv(fields, issues):
    lines = [",".join(escape_field(f) for f in fields)]
    for issue in issues:
        row = [escape_field(issue.get(f, "")) for f in fields]
        lines.append(",".join(row))
    return "\n".join(lines)

fields = ["id", "summary", "status", "assignee"]
issues = [
    {"id": "PROJ-1", "summary": "Fix login bug",      "status": "Done",        "assignee": "alice"},
    {"id": "PROJ-2", "summary": "Add, export feature", "status": "In Progress", "assignee": "bob"},
    {"id": "PROJ-3", "summary": 'He said "hello"',     "status": "Todo",        "assignee": None},
]
print(export_to_csv(fields, issues))
```

## Why Build a List and `join()` Instead of `+=`?

In Python, strings are immutable — `s += chunk` doesn't grow `s` in place, it silently builds a brand-new string and copies everything into it, every single time. Do that in a loop over N rows and you risk O(N²) total work. Collecting every row in a list and calling `"".join(...)` once at the end is always O(total length) — it's the habit that's safe regardless of how many rows there are.

## Complexity

- **Time:** O(N·F) — F field lookups for each of N issues, and escaping a value costs time proportional to its own length, which sums to the total output size.
- **Space:** O(N·F) for the output string.

## The Reusable Pattern

This is the **"one escaping helper, applied uniformly"** pattern — used any time you're serializing data into a text format with special/reserved characters:
- CSV export (this problem)
- JSON string escaping (`\"`, `\\`, `\n`)
- URL encoding (`%20` for spaces, etc.)
- SQL parameter binding / escaping quotes in a literal

Core idea: name the small set of dangerous characters explicitly, write **one** function that neutralizes them, and route every single value — headers included, no exceptions — through that one function.
