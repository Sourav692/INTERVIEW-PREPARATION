#!/usr/bin/env python3
"""
build_lesson.py — small helper for the dsa-interactive-lesson skill.

Purpose
-------
Given a JSON spec describing a DSA concept, produce an interactive HTML
lesson by filling placeholders in `references/lesson-template.html`.

This is OPTIONAL. For most concepts you should just adapt the template
directly by hand — it produces a higher-quality output. Use this
script only when you have many concepts to generate in a batch.

Usage
-----
    python3 build_lesson.py spec.json out.html

Where `spec.json` follows the shape below.

Spec shape (all keys are required unless marked optional)
---------------------------------------------------------
{
  "concept": "Concept title",
  "slug": "kebab-case-slug",
  "hero_description": "One-line description shown under the title.",
  "canonical_example": {
    "input": "n = 5, edges = [[0,1],[1,2],[3,4]]",
    "answer_text": "Answer = 2 connected components"
  },
  "use_cases": [
    {"title": "...", "body": "..."},
    {"title": "...", "body": "..."},
    {"title": "...", "body": "..."}
  ],
  "definition_left": "Simple definition text",
  "definition_right": "What you are actually counting/computing",
  "shortcut": "Beginner shortcut line",
  "thinking_steps": [
    {"title": "...", "body": "..."},
    ...
  ],
  "methods": [
    {
      "name": "DFS traversal",
      "intuition": "One-line intuition",
      "code_lines": ["from collections import defaultdict", "", "def count_components_dfs(n, edges):", ...],
      "trace_steps": [
        {
          "title": "Initial state",
          "text": "The adjacency list is built first...",
          "state": {"stack": "[]", "seen": "{}", "count": "0", ...},
          "detail": "What changed sentence",
          "code_lines": [4,6,7],
          "graph": {"current": null, "seen": [], "frontier": [], "active_edge": null}
        },
        ...
      ],
      "mistakes_left": "Common mistake text",
      "mistakes_right": "Why the data structure matters"
    }
  ],
  "edge_cases": [
    {"tab": "No edges", "title": "Case A", "input": "...", "answer": "4", "note": "..."},
    ...
  ],
  "practice": [
    {"summary": "Practice 1 — ...", "answer": "Answer text"},
    ...
  ]
}

Recommendation
--------------
Author the spec by hand, then hand-tune the output HTML for the two
things this script cannot do well: SVG diagrams that fit the concept
and the interactive graph render logic. Both belong in the template
and the trace renderers — write them in HTML/JS directly.
"""

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "references" / "lesson-template.html"


def load_spec(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render(spec: dict) -> str:
    """
    Minimal, honest renderer. It replaces the concept title, hero
    description, and canonical example placeholders in the reference
    template. Everything else is expected to be hand-adapted from the
    template's rich structure — the template already carries a full,
    working lesson to model off.

    Do NOT scale this into a full templating engine. The lessons are
    much better when the instructor adapts sections by hand.
    """
    html = TEMPLATE.read_text(encoding="utf-8")

    concept = spec["concept"]
    slug = spec["slug"]
    hero_description = spec["hero_description"]
    canonical_input = spec["canonical_example"]["input"]
    canonical_answer = spec["canonical_example"]["answer_text"]

    html = html.replace(
        "<title>Number of Connected Components — Interactive DSA Lesson</title>",
        f"<title>{concept} — Interactive DSA Lesson</title>",
    )
    html = html.replace(
        "<h1>Number of Connected Components in an Undirected Graph</h1>",
        f"<h1>{concept}</h1>",
    )
    html = html.replace(
        "This page explains the problem like an instructor would: what the problem means, why it matters, how the graph is built, how DFS and Union-Find change state step by step, and how to reason about edge cases in interviews.",
        hero_description,
    )
    html = html.replace(
        "<p><code>n = 5</code>, <code>edges = [[0,1],[1,2],[3,4]]</code></p>",
        f"<p><code>{canonical_input}</code></p>",
    )
    html = html.replace(
        '<div class="result-badge">Answer = 2 connected components</div>',
        f'<div class="result-badge">{canonical_answer}</div>',
    )

    return html


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: build_lesson.py spec.json out.html", file=sys.stderr)
        return 2

    spec_path = Path(sys.argv[1]).resolve()
    out_path = Path(sys.argv[2]).resolve()

    spec = load_spec(spec_path)
    html = render(spec)
    out_path.write_text(html, encoding="utf-8")

    print(f"wrote {out_path} for concept={spec['concept']} slug={spec['slug']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
