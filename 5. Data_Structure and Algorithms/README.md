# DSA Preparation

Two complementary tracks, each self-contained and organized by topic (not by content-type — every tutorial, notebook, visualization, and cheat sheet for a topic lives in that topic's own folder).

| Track | Use it for | Start here |
|---|---|---|
| [**DSA_Deep_Dive**](DSA_Deep_Dive/README.md) | Learning the *data structures and algorithms themselves* — trees, graphs, heaps, tries, shortest paths, MST, topological sort, SCCs — from first principles, in order, before you touch interview problems. | [`DSA_Deep_Dive/README.md`](DSA_Deep_Dive/README.md) · [`DSA_Deep_Dive/index.html`](DSA_Deep_Dive/index.html) |
| [**DSA_Blind 75**](DSA_Blind%2075/README.md) | Drilling the classic 75 *interview problems*, grouped by pattern (two pointers, sliding window, DFS/BFS, DP, etc.) once you know the underlying structures. | [`DSA_Blind 75/README.md`](DSA_Blind%2075/README.md) · [`DSA_Blind 75/index.html`](DSA_Blind%2075/index.html) |

## Suggested order

1. Work through **DSA_Deep_Dive** topic by topic (numbered 01–15) to build the concepts.
2. Move to **DSA_Blind 75** and work topic by topic, applying those concepts to real interview problems.
3. Revisit whichever single topic folder needs a refresh before an interview — everything about it (tutorial, notebook, visualization, cheat sheet) is in that one folder in both tracks.

## Shape shared by both tracks

```
<Track>/
├── README.md          — track-level index (this pattern, one level up)
├── index.html           — visual hub linking every topic
└── <Topic>/
    ├── README.md         — concept tutorial for the topic
    ├── index.html / patterns.html  — interactive visuals + cheat sheet (Blind 75 only)
    ├── <problem_or_concept>.ipynb  — runnable Python notebook
    ├── <problem_or_concept>.html   — interactive step-through
    └── <problem_or_concept>_explained.md  — deep-dive writeup (where one exists)
```
