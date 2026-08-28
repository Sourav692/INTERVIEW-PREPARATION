---
name: plain-theory-formatter
description: Reformat the "Concepts" / theory markdown cell of an existing study notebook into short, plain-language bullet points instead of dense prose paragraphs, while preserving full technical accuracy (every Big-O claim, definition, and example stays intact). Use when the user asks to make a notebook's concepts/theory section "easier to read", "simpler language", "proper bullet points", or asks to reformat/simplify an existing explanation cell. This is a reformat-in-place skill for a cell that already exists — not for writing a new notebook from scratch (use leetcode-notebook for that).
---

# Plain-Language Theory Formatter

Take a dense, paragraph-heavy "Concepts" (or similarly theory-only) markdown cell in an existing Jupyter notebook and rewrite it as short, scannable bullet points in plain English — without losing or softening any technical content.

## When to use

- The user points at a notebook's Concepts/theory cell and asks for it to be "easier to understand", "simpler language", "proper bullet points", or "reformatted".
- Applying the same treatment across multiple notebooks in a folder ("do this for all the notebooks in this folder").
- Do **not** use this to write a brand-new notebook or a brand-new Concepts section from a problem statement — that's `leetcode-notebook`'s job. This skill only reformats a cell that already has the right content, just in the wrong shape.

## What counts as a "theoretical section"

In the study notebooks this skill targets, that's the **`## Concepts`** cell: the "core concept(s) / why they apply here / key intuition" framing plus the "What is it? — primers for every technique used below" block. Unless the user names a different cell explicitly, reformat only this one — leave Problem Statement, Approach idea/complexity cells, Discussion, and Patterns Learned cells untouched (they're already example- and code-anchored, not prose theory).

## The transformation rules

1. **Every paragraph becomes bullets.** If a paragraph makes two or three separate points, it becomes two or three separate bullet lines — never a wall of text with `--` or semicolons chaining ideas together.
2. **Simplify the wording, not the content.** Replace jargon-dense phrasing with the plainest words that still say the same thing exactly (e.g. "risks O(N²) total work in general, because each append can re-copy everything accumulated so far" → "can silently become O(N²) — slow, and it gets worse as N grows"). Never drop a technical claim, a Big-O bound, a caveat, or an example to make a sentence shorter — shrink the *words*, not the *content*.
3. **Keep every primer's shape, just as bullets.** Each "What is X?" primer keeps its bolded sub-heading, then converts its definition / how-it-works / complexity / "in Python" parts into bullet lines instead of one running paragraph.
4. **Keep all code spans, Big-O notation, and inline code exactly as they were.** `O(N²)`, `` `escape_field` ``, `` `"".join(pieces)` `` etc. are copied verbatim — only the prose around them gets rewritten.
5. **Keep numbered steps as numbered steps.** A rule like "double the quotes, then wrap" stays an ordered list (`1.`, `2.`), since order is the whole point.
6. **End with the same "one thing to remember" framing if the original had one** (a closing intuition/mental-model line) — keep it short and put it up top or as its own short paragraph, not buried in a bullet.
7. **Don't invent new facts, don't cut old ones.** This is a reformat, not a rewrite of substance — if you're unsure whether a sentence is safe to compress further, keep the original claim intact rather than risk losing precision.

## Worked example

**Before (dense paragraph style):**
> **Mutable vs. immutable string building.** In Python, `str` is immutable — `s = s + more` does not grow `s` in place, it allocates a **new** string and copies both halves into it. Doing this in a tight loop (`s += chunk` repeated N times) risks **O(N²)** total work in general, because each append can re-copy everything accumulated so far. The safe pattern is to **collect pieces in a list and call `"".join(pieces)` once at the end** — `join` knows the total length up front and allocates exactly once, so building N pieces is **O(total length)**, i.e. linear.

**After (plain bullet style):**
> **Building strings the fast way (mutable vs. immutable).**
> - In Python, strings can't be changed in place. `s = s + more` actually creates a **brand new string** and copies everything into it.
> - Doing this over and over in a loop (`s += chunk`, N times) can silently become **O(N²)** — slow, and it gets worse as N grows.
> - The safe habit: collect all the pieces in a **list**, then call `"".join(pieces)` **once** at the end. This is **O(total length)** — linear, and always fast.

## How to apply it to a notebook

1. Read the notebook and locate the Concepts cell (its `id`, from the Read tool's `<cell id="...">` output).
2. Rewrite it following the rules above.
3. Use `NotebookEdit` with `edit_mode: replace` on that exact cell id to swap in the new markdown — never touch surrounding cells.
4. Do not re-run or re-validate code cells — this is a pure documentation/formatting change, nothing executable changed.

## Applying across a whole folder

When asked to do this for every notebook in a folder:
- Process one notebook at a time: Read it, find its Concepts cell, rewrite, NotebookEdit.
- Keep each notebook's own technical specifics (its own primers, its own examples) — don't copy one notebook's Concepts content into another. Only the *shape* (bullets, plain words) is shared across notebooks, never the substance.
- After finishing all notebooks, report back the list of files updated — no need to re-run validation scripts, since no code changed.
