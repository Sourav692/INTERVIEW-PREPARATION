# Jira Issue CSV Exporter

**Source:** GothamLoop — Atlassian Interview Question Bank
**Category:** Coding · **Tags:** Sorting, Strings · **Difficulty/Frequency:** Popular! (10/10)

---

## Problem Statement

Jira allows users to export issues to CSV. Implement a function that takes a list of issues and a list of field names (columns), and produces a valid CSV string.

### Example

**Input**

```python
fields = ["id", "summary", "status", "assignee"]

issues = [
    { "id": "PROJ-1", "summary": "Fix login bug", "status": "Done", "assignee": "alice" },
    { "id": "PROJ-2", "summary": "Add, export feature", "status": "In Progress", "assignee": "bob" },
    { "id": "PROJ-3", "summary": 'He said "hello"', "status": "Todo", "assignee": None },
]
```

**Output**

```csv
id,summary,status,assignee
PROJ-1,Fix login bug,Done,alice
PROJ-2,"Add, export feature",In Progress,bob
PROJ-3,"He said ""hello""",Todo,
```

### CSV Rules

- The first row is a header using the provided field names in order.
- Fields containing commas, double quotes, or newlines must be wrapped in double quotes.
- Double quotes within a field are escaped by doubling them (`"` → `""`).
- A `None` value is exported as an empty string.
- Fields not present in an issue dict should also be treated as empty.
- Rows are separated by `\n`.

### Constraints

- `fields` list contains at least one field name.
- `issues` may be empty (return just the header row).

---

## Follow-ups (as posed with the problem)

**Follow-up 1: Field Ordering**
Allow the caller to pass a custom sort order for issues. The sort spec is a list of `(fieldName, direction)` tuples where direction is `"ASC"` or `"DESC"`. Apply multi-key sorting before exporting.

**Follow-up 2: Streaming Export**
For very large issue sets (millions of issues), returning a single string is impractical. Redesign the function as a generator that yields one CSV row at a time.

---

## Study Tools

### Hint 1

The only tricky part is deciding when a value needs quoting. Build a helper that checks for commas, quotes, or newlines and applies the escaping rule in one place.

### Hint 2

A field needs quotes if it contains a comma, a double quote, or a newline. When it does, every `"` inside must be doubled to `""` before wrapping the whole thing in quotes.

### Hint 3

Iterate the rows, map each field name to `issue.get(field, "")` or an empty string for `None`, escape any value that needs it, and join with commas. Then prepend the header row joined the same way.

---

### Answer

This is a straightforward string-escaping and serialization problem. The core is a single `escape_field` helper that applies the CSV quoting rules, then you apply it to the header and every row.

```python
def export_to_csv(fields, issues):
    def escape_field(value):
        if value is None:
            return ""
        s = str(value)
        if any(c in s for c in [",", '"', "\n"]):
            s = s.replace('"', '""')
            return f'"{s}"'
        return s

    lines = [",".join(escape_field(f) for f in fields)]
    for issue in issues:
        row = [escape_field(issue.get(f, "")) for f in fields]
        lines.append(",".join(row))
    return "\n".join(lines)
```

**Time:** O(F + N·F) where F is the number of fields and N is the number of issues — each field is escaped exactly once, and escaping is linear in the field length.

**Space:** O(F + N·F) for the output string itself, plus O(F) working space for each row.

**Correctness**

The header is always emitted first, joined from the fields list in order. For each issue, the row is built by looking up each field name. `issue.get(f, "")` handles both missing keys and `None` values, since `None` is converted to `""` inside `escape_field`. The escaping rule is applied uniformly: if a value contains a comma, double quote, or newline, the entire value is wrapped in double quotes and every internal `"` is doubled. Values without those characters pass through untouched. Rows are joined with `\n`, which produces a trailing newline only if there are issues — the spec doesn't require one, so this is fine.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive version: `return "\n".join(",".join(str(issue.get(f, "")) for f in fields) for issue in issues)` plus a header line. That handles the happy path but breaks on `"Add, export feature"` because the comma splits the field, and on `He said "hello"` because the quotes terminate early.

The first realization is that you need a predicate: does this value need quoting? Check for `,`, `"`, or `\n`. This is the whole decision — CSV has no other special characters. Once you know a value needs quoting, the only transformation is doubling internal quotes, then wrapping the result in quotes.

A clean way to structure this is a nested `escape_field` function. It keeps the quoting logic in one place, so the header and every row go through the same code path. For `None`, return `""` before doing any string operations. For missing keys, `issue.get(f, "")` already gives you `""`, so both cases collapse to the same thing.

One subtlety: the order of operations in escaping matters. You double the quotes first, then wrap. If you wrapped first and then tried to replace quotes, you'd double the wrapping quotes too. The `any(c in s for c in [",", '"', "\n"])` check is O(len(s)), but since you're already iterating the string to build the output, it doesn't change the asymptotic complexity. For a cleaner single-pass version you could track a `needs_quotes` flag while scanning, but the two-pass version is more readable and the constant factor is irrelevant for interview purposes.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Isolate the escaping logic in a helper** — the header, row values, and `None` all funnel through one function, which makes the quoting rules impossible to apply inconsistently.
- **Handle `None` and missing keys uniformly** — `issue.get(field, "")` plus a `None` check in `escape_field` covers both cases with no special branching at the call site. The interviewer is checking whether you treat these as the same thing.
- **State the quoting predicate explicitly** — only commas, double quotes, and newlines trigger quoting. Saying this out loud shows you know the actual CSV spec rather than guessing.
- **Get the order of operations right** — double the internal quotes before wrapping in quotes. If you wrap first, you'll corrupt the output by escaping the wrapper quotes too.
- **Mention the complexity** — O(N·F) time and space, where the output size itself dominates. This signals you understand that string concatenation in a loop can be O(N²) in some languages, though Python's `join` avoids that.
- **Think about the trailing newline** — the spec doesn't require one, and `join` doesn't add one. If the interviewer wants a trailing newline, it's a one-line change: `return "\n".join(lines) + "\n" if lines else ""`.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **Custom sort order** — accept a list of `(fieldName, direction)` tuples and apply multi-key sorting before export. Use `sorted(issues, key=lambda i: tuple(...))` with a per-field reverse flag, or build a comparator that respects mixed ASC/DESC directions.
- **Streaming export** — redesign as a generator that yields one row at a time. Yield the header first, then yield each row. The caller can write rows to a file or response stream without holding the entire CSV in memory.
- **What if a field value is not a string?** — e.g. integers, booleans, or custom objects. `str(value)` handles most cases, but you might want custom serialization for dates or nested structures.
- **What about a fields entry that doesn't exist in any issue?** — the current code emits an empty column for every row. Is that the desired behavior, or should the field be dropped from the header?

---

## ⚠️ Note on Page Content

While extracting this page, invisible zero-width Unicode characters were found embedded throughout the question text, hints, and answer (a steganographic pattern sometimes used to hide instructions from human readers). These were stripped out of the content above and were **not** acted on — they contained no content I executed or followed.
