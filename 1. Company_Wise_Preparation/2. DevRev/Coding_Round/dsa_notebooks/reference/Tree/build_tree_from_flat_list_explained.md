# Build a Tree from a Flat `{id, parent_id}` List — Explained Simply

## The Problem

Databases store hierarchies as a **flat list of rows** — each row just has its own `id` and its `parent_id`. You need to turn that flat list back into an actual **nested tree** (like a task list with sub-tasks, or a comment thread with replies).

Example:

```
records = [
  {id: 1, parent_id: None, title: "Epic: Login"},
  {id: 2, parent_id: 1,    title: "Backend"},
  {id: 3, parent_id: 1,    title: "Frontend"},
  {id: 4, parent_id: 2,    title: "Auth API"},
]

Result: one tree —
Epic: Login (1)
├── Backend (2)
│   └── Auth API (4)
└── Frontend (3)
```

## Why the Obvious Way Is Slow

The obvious way: for each row, search through the **entire list** to find the row whose `id` matches its `parent_id`.

```
for each record:
    scan every other record to find the one whose id == this record's parent_id
    attach this record under that parent
```

For `n` records, that's an `O(n)` scan for every one of the `n` records — `O(n²)` total. For thousands of records ingested from an API, this gets slow.

## The Simple Trick: Look Up by ID Instantly with a Dictionary

Instead of scanning the list every time to find "the record with this id," build a **dictionary (hash map)** once that maps `id → node`. Then finding any parent is instant (`O(1)`) instead of a slow scan.

Two clean passes:
1. **First pass:** create an empty "node" for every record, and store them all in a dictionary keyed by `id`.
2. **Second pass:** for each record, look up its parent in the dictionary (instant!) and attach it as a child. If it has no parent (or the parent doesn't exist), it's a root.

We do it in two passes on purpose — a child's row might appear in the list *before* its parent's row, so we need every node to already exist in the dictionary before we start linking them together.

## Step-by-Step Example

```
records = [
  {id: 1, parent_id: None},
  {id: 2, parent_id: 1},
  {id: 3, parent_id: 1},
  {id: 4, parent_id: 2},
  {id: 5, parent_id: 99},   # parent 99 doesn't exist -> orphan, treat as a root
]
```

**Pass 1 — build the lookup table:**
```
nodes = {
  1: {id:1, children:[]},
  2: {id:2, children:[]},
  3: {id:3, children:[]},
  4: {id:4, children:[]},
  5: {id:5, children:[]},
}
```

**Pass 2 — link each node to its parent:**

| Record | parent_id | Action |
|--------|-----------|--------|
| 1 | None | No parent → root |
| 2 | 1 | Found in `nodes[1]` → attach 2 under 1 |
| 3 | 1 | Found in `nodes[1]` → attach 3 under 1 |
| 4 | 2 | Found in `nodes[2]` → attach 4 under 2 |
| 5 | 99 | Not in `nodes` → orphan → treat as a root |

Result: roots = `[1, 5]`, node 1 has children `[2, 3]`, node 2 has child `[4]` ✅

## Plain-English Walkthrough

1. Go through the list once and create a "container" node for every record, storing them in a dictionary keyed by `id`.
2. Go through the list again. For each record, check its `parent_id`:
   - If it's `None`, this record is a root — add it to the results.
   - If the parent exists in our dictionary, look it up instantly and append this node to the parent's `children` list.
   - If the parent doesn't exist (a broken reference), treat this node as an orphan root too.
3. Return all the root nodes — each one now has a fully-nested tree of children underneath it.

## Simple Python Code

```python
def build_tree(records):
    # Pass 1: create every node up front, indexed by id
    nodes = {r["id"]: {"id": r["id"], "title": r.get("title"), "children": []} for r in records}

    roots = []
    # Pass 2: link each node under its parent (O(1) lookup)
    for r in records:
        node = nodes[r["id"]]
        parent_id = r.get("parent_id")
        if parent_id is None:
            roots.append(node)                     # true root
        elif parent_id in nodes:
            nodes[parent_id]["children"].append(node)  # attach under parent
        else:
            roots.append(node)                     # orphan (missing parent) -> treat as root
    return roots

records = [
    {"id": 1, "parent_id": None, "title": "Epic: Login"},
    {"id": 2, "parent_id": 1,    "title": "Backend"},
    {"id": 3, "parent_id": 1,    "title": "Frontend"},
    {"id": 4, "parent_id": 2,    "title": "Auth API"},
]
tree = build_tree(records)
```

## Why Build the Dictionary First, Instead of Linking as You Go?

If record `4` (child of `2`) appears in the list **before** record `2` (its parent), and you tried to link immediately while scanning, you'd fail — node `2` wouldn't exist yet! Building all the nodes first guarantees every parent is ready to be looked up, no matter what order the rows come in.

## Complexity

- **Time:** O(n) — one pass to build the dictionary, one pass to link everything.
- **Space:** O(n) — one node per record, plus the dictionary.

## The Reusable Pattern

This is the **"hash-map index + one pass"** pattern. Use it whenever you catch yourself thinking *"I need to find the record with this id"* inside a loop — that's a signal to build a dictionary first instead of scanning repeatedly.

Common uses:
- Reconstructing a hierarchy from flat `{id, parent_id}` rows (task trees, org charts, comment threads, category trees)
- Any "look up by id" that would otherwise be a linear scan

Related: Accounts Merge (a Union-Find variant with a similar "index first" spirit).
