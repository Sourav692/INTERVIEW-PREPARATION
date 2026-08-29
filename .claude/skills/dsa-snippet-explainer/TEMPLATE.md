# Markdown cell template

Paste this structure into the new notebook cell. Replace heap-specific lines with the snippet’s DSA. The heap walkthrough in `12_heaps_priority_queues.ipynb` is the filled example.

```markdown
### Step-by-step: what this cell actually does

<INVARIANT in one sentence>. <How it is stored>. After the demo, the notebook prints <EXACT OUTPUT>; <asserts if any>.

#### <Primer title — e.g. Array packing (why those formulas)>

<One sentence why the formulas exist.>

| relation | formula |
|----------|---------|
| … | `…` |

Example — <post-build structure>:

```
index:  …
value: […]

    <ASCII of that structure with i= labels>
```

- Worked lookup 1.
- Worked lookup 2.

<What push-like vs pop-like does in one sentence each.>

`<index variable>` is <meaning> — not a scan of the whole structure.

---

#### `<fn_a>` — <short recipe>

`<fn_a>(…)`:

1. …
2. …

Demo input: `[…]`.

**1. <op>** — <indices, comparison, swap or not>.

```
array: […]

    <ASCII>
```

**2. <op>** — …

---

#### `<fn_b>` — <short recipe>

(same pattern; show state **after** the critical assignment, then after the loop finishes)

**pop → <returned value>.** …

```
after: […]

    <ASCII>
```

<Tie to assert. Complexity one-liner.>

#### Mental model

- **<structure>** → <consequence>.
- **<fn_a>** = “<verb phrase>.”
- **<fn_b>** = “<verb phrase>.”
- Stopping early (`break` / …) means <invariant restored> — you do not <wrong mental model>.
```

## Depth variants

**Full:** one `**N. op**` block per mutation, including every pop until empty (or every BFS dequeue until the queue is empty).

**First-class + one unwind:** full build; only the first inverse op in full; then one sentence that the rest repeat and the assert holds.

**Compact:**

```markdown
| Step | Op | Why | State after |
|------|----|-----|-------------|
| 1 | push 5 | empty | `[5]` |
```

ASCII only after the last build step (and after the first pop if you still show one).
