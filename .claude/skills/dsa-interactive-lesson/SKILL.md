---
name: dsa-interactive-lesson
description: Use this skill whenever the user asks for a beginner-friendly explanation of a Data Structures and Algorithms (DSA) concept as an interactive HTML page. Triggers include phrases like "explain this DSA concept", "make an interactive lesson for X algorithm", "create a HTML tutorial for Y data structure", "turn this LeetCode problem into a beginner guide", "step by step interactive visualization for X", "teach me BFS/DFS/Dijkstra/Union-Find/Backtracking with an interactive HTML". Produces ONE self-contained HTML file that follows the same instructor-grade format used for the "Number of Connected Components" reference page: rich structure, minimal look, synced code highlighting, interactive step-by-step traces (Previous / Resume / Next / Reset), edge-case tabs, interview reasoning, and practice questions. Do NOT use this skill for non-DSA content, generic essays, or slide decks.
---

# DSA Interactive Lesson (HTML)

You are acting as an **expert DSA instructor**. Your job with this skill is to convert any DSA concept, algorithm, or LeetCode-style problem into a **single self-contained interactive HTML lesson** that a beginner can learn from without help.

## When to use

Load this skill when the user asks for a **DSA teaching artifact** as HTML. Some examples:

- "Explain Kadane's algorithm as an interactive HTML"
- "Make a beginner HTML tutorial for BFS"
- "Turn this LeetCode problem into an interactive lesson"
- "Explain Union-Find step by step in a page"
- "Create a step-by-step HTML for Dijkstra"

Do NOT use this skill for:

- General articles unrelated to DSA
- Slide decks (use the deck-builder subagent)
- Multi-page docs (use `build-doc`)

## Non-negotiable output contract

- Produce **ONE** self-contained HTML file: `<concept-slug>.html`
- Inline all CSS in `<style>` and all JS in `<script>`
- Deliver the file via `genspark_deliver_files`
- ALWAYS run `gsk screenshot <file.html> --scale 2` and inspect the returned image via `gsk understand_images` BEFORE delivering
- Wrap the trace script inside `window.addEventListener('DOMContentLoaded', () => { ... })`
- Every button MUST use `type="button"`
- Never use external CSS files, external JS files, or CDN dependencies

## Required page structure (in this order)

The finished HTML MUST have these sections, in this order, using the same visual language as the reference template in `references/lesson-template.html`:

1. **Hero**
   - Concept title
   - One-line plain description
   - Chips: core idea, methods covered, interactive tag
   - Canonical example on the right with a small SVG diagram
   - Green result badge showing the expected answer for the canonical example

2. **Why this problem matters**
   - 3 real-world use cases in a 3-column grid
   - Callout with an instructor note

3. **What is <concept>?**
   - Simple definition
   - What you are actually counting / computing / building
   - Beginner shortcut callout

4. **Step-by-step thinking process**
   - 4 numbered cards summarizing the problem-solving flow

5. **How the input becomes X** (adjacency list, DP table, heap, etc.)
   - Left card: input, right card: transformed structure, arrow between them
   - Timeline of how each input piece is added

6. **Method 1: <primary approach>**
   - Intuition sentence
   - Full Python code block with `.stepped` class and per-line `<span class="code-line" data-line="N">`
   - Interactive trace with graph SVG on the left, controls + state grid on the right
   - Full step-by-step trace table below
   - Three insight cards: key mental model, common mistake, why the data structure matters

7. **Method 2: <alternative approach>** (only if there is a genuinely different second method)
   - Same shape as Method 1

8. **Edge cases you should test**
   - Tabs UI (3 examples minimum: minimal, chain / full, mixed)

9. **Method comparison table**
   - Time and space complexity for every method

10. **How to derive this in an interview**
    - Reasoning timeline
    - "What to say out loud" bullets

11. **Common beginner coding mistakes**
    - Two-column list per method

12. **Practice questions**
    - 3 `<details>` blocks with progressive difficulty and reveal answers

13. **Final takeaway**
    - Single closing card + footer note

## Interactive trace rules

Every interactive trace MUST include:

- **Controls**: Previous, Resume (toggles to Pause), Next, Reset
- **Progress bar** + step counter pill
- **State grid** with 4-6 boxes showing the runtime state of the algorithm (stack, queue, set, parent list, DP table, count, current node, etc.)
- **Live SVG graph / structure** with color states
- **Synced code highlighting**: each step lists the code lines it maps to via `lines: [N, N, N]`
- **Active row highlight** on the trace table

Legend colors (reuse consistently):

- Blue `#315efb` = first side / visited / stable state
- Green `#13a46b` = second side / frontier / in queue-stack
- Orange `#ff9f1c` = currently active / current pop
- Gray `#c8d2e7` = untouched / not yet reached

## Code block rules

- Wrap stepped Python code in `<div class="code-block stepped"><code id="...-code">...</code></div>`
- Every line, including blank ones, is wrapped in `<span class="code-line" data-line="N"></span>`
- The `stepped` class collapses blank-line height so the code stays compact
- Non-stepped code cards (input examples, adjacency list output) use plain `<div class="code-block"><code>...</code></div>` — do NOT add the `stepped` class or their text will disappear

## Design rules

- Minimal, clean, instructor-tone layout — never marketing / decorative
- Card + panel layout with soft shadow, 18px radius
- Inter font, 1.6 line-height
- Palette: use the CSS variables in the template exactly — do NOT hard-code hex colors elsewhere
- Real diagrams (inline SVG), not emoji

## Content rules (this is the instructor part)

- Write like an instructor, not a reference. Every explanation must answer "why".
- Explain the **transformation of the input** to the working structure (adjacency list, table, heap) explicitly. This is where beginners lose the thread.
- Every method must include: intuition, code, trace, mistakes.
- Interview section must show the derivation, not just the answer.
- Practice questions must have hidden reveal-answers.
- No fabricated tricks or shortcuts. Only teach what the code actually does.
- Do NOT include emojis anywhere.

## Workflow to follow

Use this exact order. Do not skip steps.

### Step 1 — Gather the concept context

Confirm you have:
- Concept name (e.g. "BFS", "Kadane", "Trie", "Union-Find")
- Canonical example (input + expected output). If missing, invent a small illustrative one and clearly say so
- At least one working Python solution
- 1-2 edge cases

If any is unclear, ask ONCE with a single `question` form before generating. Otherwise proceed with sensible defaults.

### Step 2 — Plan the trace

For each method:
- Write out the state per step in a Python dict list. This is the ground truth for the JS trace.
- Confirm each step has: title, text, per-state values (stack / queue / parent / dp / etc), what changed, and the mapped code lines.
- If the state cannot be represented visually, add a smaller diagram (bars, tree, table) as SVG.

### Step 3 — Copy the reference template

Start from `references/lesson-template.html`. It contains:
- All CSS
- Placeholder structure for every required section
- Working DFS + Union-Find style scripts for the trace player

Replace the concept-specific parts. Do NOT rewrite CSS from scratch.

### Step 4 — Build the interactive traces

- Fill `steps = [ {...}, {...}, ... ]` for each method
- Wire renderers (`renderMethodA`, `renderMethodB`) to update state + graph + highlighted code
- Test that the buttons work (`type="button"` and DOMContentLoaded wrapper — see script skeleton in the template)

### Step 5 — Fill the teaching sections

- Hero, use cases, definition, thinking process, input-to-structure explainer
- Every method's insight cards
- Edge case tabs
- Comparison table
- Interview reasoning
- Common mistakes
- Practice questions with reveal answers

### Step 6 — Verify visually

- `gsk screenshot <file.html> --scale 2` → get URL
- `gsk understand_images -i <url> -r "Confirm the required sections and interactive traces are present and readable"`
- Fix any clipping, blank code cards, or spacing issues before delivering

### Step 7 — Deliver

- `genspark_deliver_files` with `dest_path: "<concept-slug>.html"`
- Reply summary must list what sections and interactive features were included

## Reference material

- `references/lesson-template.html` — full working template. START HERE. Contains complete CSS, JS trace player, and all section placeholders.
- `scripts/build_lesson.py` — small helper that takes a JSON spec and injects it into the template. Optional but faster for large lessons.

## Anti-patterns to avoid

- Rewriting the CSS from scratch instead of reusing the template
- Skipping the interactive trace (this is the single most important feature)
- Skipping the input-to-structure explainer (this is where beginners fail)
- Skipping edge cases or practice questions
- Delivering without the screenshot verification pass
- Adding CDN links or external stylesheets
- Marketing tone, emojis, decorative flourishes

## Reminder

Your job is not to describe an algorithm. Your job is to **teach it** so a beginner can walk away and code it themselves. Every design choice above serves that goal.
