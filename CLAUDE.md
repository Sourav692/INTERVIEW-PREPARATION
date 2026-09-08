# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## What this repo is

A personal interview-preparation knowledge base — not a shipped application. There is no build, test, or lint pipeline; content is Jupyter notebooks (`.ipynb`), Markdown, and standalone HTML visualizations/interactive lessons. `pyproject.toml` / `uv.lock` / `databricks.yml` only configure the Databricks Connect dev environment used to run notebooks (managed by `databricks environments setup-local` — don't hand-edit the `[tool.uv]` constraint block in `pyproject.toml`).

## Directory map

- `0. Roadmap/` — master preparation roadmap and tracker
- `1. Company_Wise_Preparation/` — per-company prep (GreyLabs.ai, DevRev, MongoDB, Atlassian)
- `2. Data_Engineer_Interview_Preparation/`
- `3. AI_Engineer_Interview_Preparation/` — cross-cutting prep, RAG/agentic/multi-agent platform case studies
- `4. FDE_Related_Preparation/`
- `5. Data_Structure and Algorithms/` — the DSA content, two complementary tracks (see below)
- `6. AI_Engineering_Handbook/` — numbered chapters (00_Orientation through 11_Telling_The_Story, plus 99_Appendices)
- `DSA_Practice/` — standalone scratch notebooks (Queue, Stack, sliding window), not part of the two tracks below

### `5. Data_Structure and Algorithms/` tracks

Organized by topic, not by content-type — every tutorial, notebook, visualization, and cheat sheet for a topic lives in that topic's own folder.

- **`DSA_Deep_Dive/`** — the data structures/algorithms themselves, numbered 01–19 (trees, graphs, heaps, tries, shortest paths, MST, topological sort, SCC, hash tables, sorting, binary search, two pointers/sliding window). Work through in order.
- **`DSA_Blind 75/`** — classic interview problems grouped by pattern (Array, Binary, Dynamic Programming, Graph, Heap, Interval, Linked List, Matrix, String, Tree). `Blind75_Tracker.md` tracks progress.
- `Neetcode_150/` exists but is currently just an index shell.

Note: `AGENTS.md` (imported above) predates the current numbered top-level layout — always use the paths in this section, not older references.

## Working here

- Skills for common workflows already exist under `.claude/skills/` (DSA notebook generation, snippet/tree explainers, interactive lesson builder, mock interviews, visualizers) — check there before building new tooling for a repeated task.
- No `gh` CLI is installed even though `origin` points to GitHub (`Sourav692/INTERVIEW-PREPARATION`) — plain `git` only unless the user sets it up.
