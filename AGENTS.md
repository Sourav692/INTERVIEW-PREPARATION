## Learned User Preferences

- When explaining a notebook or DSA snippet, insert a markdown cell immediately after the code; do not rewrite the code cell and do not write a separate `_explained.md` unless the tree-notebook explainer is in play.
- Before writing a step-by-step walkthrough cell, ask depth (full vs compact) and whether to include a formula/invariant primer unless the user already specified (e.g. “same as the heap cell”).
- Walkthroughs should trace the notebook’s own demo data and asserts, with ASCII snapshots after each mutation, not a different tutorial example.
- DSA notebook section headings should open with 2–3 plain-language sentences of intuition before formulas or APIs.
- Prefers converting dense study-guide table cells into per-topic **Skip** bullet lists with the existing “why skip” sentence kept underneath.

## Learned Workspace Facts

- Interview prep lives mainly under `DSA_Preparation/DSA_Deep_Dive/` (topic folders with README/PRIMARY and notebooks) and `DSA_Preparation/Atlassian_Prep/` (including `DSA_Study_Guide.md` and the Jira CSV exporter notebook).
- In-notebook DSA walkthroughs use `.claude/skills/dsa-snippet-explainer/` (`SKILL.md` + `TEMPLATE.md`); the filled canonical example is `DSA_Preparation/DSA_Deep_Dive/12_Heaps_Priority_Queues/12_heaps_priority_queues.ipynb`.
- `.claude/skills/tree-notebook-explainer/` writes a separate `_explained.md` file rather than inserting a notebook markdown cell.
- `DSA_Study_Guide.md` Part 2 (secondary / skip list) is per-topic **Skip** blocks, not a table.
