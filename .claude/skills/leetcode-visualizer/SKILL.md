---
name: leetcode-visualizer
description: Turn the LeetCode / Blind 75 study notebooks for a topic into interactive, self-contained HTML explainers. For each problem it builds one HTML page with plain-language explanations and interactive step-through diagrams of the problem and every solution; then it builds one final "patterns" HTML for the whole topic that summarizes the reusable patterns learned and how to use them in an interview. Invoke when the user asks to "make HTML", "visualize", "create diagrams", "interactive explainer", or "visual walkthrough" for a topic or problem.
---

# LeetCode Visual Explainer Generator

Convert notebooks into **interactive HTML pages** a beginner can open in a browser and *play* with. The goal is understanding through animation and plain words — not walls of text or jargon.

Two kinds of output per topic:
1. **One page per problem** — explains the problem and each solution with interactive, step-through diagrams.
2. **One final "patterns" page** for the whole topic — the reusable patterns learned across all its problems, in simple language, plus how to use each in an interview.

## When to use

- User asks to "make HTML / visualize / create interactive diagrams / visual walkthrough" for a topic (e.g. "Array") or a single problem.
- Runs **after** the notebooks exist (see the `leetcode-notebook` skill). Source the problem statement, the approaches, and the "Patterns Learned" straight from each notebook so the page and notebook agree.

## Inputs

- A **topic** (build a page for every notebook in `DSA_Blind 75/notebooks/<Topic>/`, then the patterns page), or a **single problem** (just its page).
- If the notebooks are missing, say so and offer to generate them first.

## Output location & naming

- Per-problem pages: `DSA_Blind 75/visualizations/<Topic>/<snake_case>.html` (same base name as the notebook).
- Final patterns page: `DSA_Blind 75/visualizations/<Topic>/patterns.html`.
- Also write/refresh an `index.html` in the topic folder linking every problem page + the patterns page.
- Do **not** overwrite an existing page without asking.

## Hard technical rules (every HTML file)

- **Fully self-contained & offline:** inline **all** CSS and JS in the one `.html`. **No external CDNs, no web fonts, no network calls** — it must work with no internet. Prefer **vanilla JS + inline SVG or `<canvas>`**; do not pull in D3/React/mermaid.
- **Responsive & theme-aware:** readable on a laptop or phone; works in light and dark (respect `prefers-color-scheme`). Give `body` an explicit background and text color.
- **No build step:** double-clicking the file must just work.
- **Self-verify:** after writing, open the file and confirm the HTML is well-formed and the interactive controls are wired (see Build & verify).

## Plain-language rule (most important)

Write for someone new to the topic.
- **No unnecessary jargon.** If a term is genuinely needed (e.g. "pointer", "hash map"), explain it in **one short sentence** the first time, using an everyday analogy.
- Prefer verbs and pictures over definitions. Show *what happens*, then name it.
- Short sentences. One idea per line. No paragraph longer than ~3 lines.
- Every diagram has a one-line caption saying, in plain words, what the reader should notice.

## Per-problem page structure

Build the page in this order.

1. **Header:** problem number + title, difficulty (colored dot), topic, and a link back to `index.html`.
2. **"The problem in plain words":** 2–4 sentences, plus a tiny worked example the reader can relate to (use a real-world framing when it helps, e.g. "find two receipts that add up to the bill").
3. **Interactive problem demo:** a small diagram of one example input the reader can step through to *feel* the task before any solution.
4. **One interactive section per solution** (brute → better → optimal, matching the notebook):
   - A plain-words idea (2–3 sentences: what it does and why it works).
   - An **interactive step-through diagram** (controls below) that animates the algorithm on a sample input, highlighting the current state at each step (which items are compared, what's stored, which pointer moved, what got ruled out).
   - A one-line **speed & memory** note in plain words ("checks every pair, so it gets slow fast" alongside the Big-O).
5. **"When you'd use this":** one or two lines on the signal that suggests this approach.

### Interactive controls (required for each diagram)
Provide at minimum: **Prev**, **Next**, **Play/Pause**, **Reset**, and a **step counter / caption** that updates to explain the current step in one plain sentence. Optional: a small input the reader can change (e.g. edit the array) and re-run. Keep the step model simple: precompute an ordered list of "frames" (state snapshots), and the buttons just move an index through them.

### How to visualize common techniques
- **Two pointers:** a row of boxes; two colored arrows that move; shade the region being considered; caption why a pointer moved.
- **Hash map / set:** the array on top, a growing "memory" table below; highlight the lookup ("have I seen its partner?") and the insert.
- **Sliding window:** a highlighted band over the array that grows/shrinks; show the running total.
- **Binary search:** show `low`/`mid`/`high`; grey out the half that gets discarded each step.
- **Dynamic programming:** a table (1-D or 2-D) that fills cell by cell; arrows from the cells a value depends on.
- **Recursion / divide & conquer:** a tree that expands as it recurses and collapses as it returns values.
- **Graph / grid (DFS/BFS):** nodes/cells that change color as they're visited; show the stack/queue beside them.
Pick the one that matches each solution; the point is to make the *mechanism* visible, not to be fancy.

## Final patterns page (`patterns.html`)

Built after all problem pages. It is the topic's "cheat sheet you actually understand".

- **Intro:** one short paragraph — what this topic is really about, in plain words.
- **One card per pattern** found across the topic's "Patterns Learned" (dedupe similar ones). Each card, in simple language:
  - **Name** of the pattern + a one-line "what it is" analogy.
  - **The tell:** how to recognize in an interview that this pattern applies (the words/shape in the question that hint at it).
  - **How it works:** 2–3 lines, ideally with a tiny inline diagram or animation reused from the problem pages.
  - **Problems here that use it:** links to those problem pages.
  - **How to say it in an interview:** a sample sentence the reader could actually speak ("I notice we're searching for a pair, so I'll use a hash map to look up the partner in one step, which makes this linear time.").
- **Optional interactive:** tabs or a filter to jump between patterns; a small "pattern → problems" map.
- **Interview tips (plain):** a short closing list — how to spot which pattern to reach for, and what to say out loud while solving.

## Build & verify

- Write each `.html` with the Write tool.
- **Verify** every file before finishing: confirm it exists, parse/lint the markup (e.g. load it and check the tags balance), and check that the control elements and their JS handlers are present (search the file for the button ids and the functions they call). Fix anything that isn't wired.
- Report the list of files created and their paths, and offer to open the `index.html`.

## Quality bar

- Opens offline, no console errors, controls actually step the diagram.
- Language stays simple — re-read and cut jargon; every needed term is explained once.
- Page content matches the notebook (same approaches, same complexities, same patterns).
- Looks clean in light and dark; usable on a phone.
- The patterns page is genuinely useful as pre-interview revision, not a data dump.
