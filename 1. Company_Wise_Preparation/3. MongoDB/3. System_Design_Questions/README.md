# MongoDB Prep — System Design Questions

MongoDB interview questions (GothamLoop question bank), one folder per problem. Each folder holds the problem writeup, a runnable study notebook, and a plain-language explainer side by side, so there's no jumping between locations to review one problem.

All 6 **System Design** questions from the bank are covered.

## Problems

| # | Problem | Frequency | Notebook | Explainer |
|---|---|---|---|---|
| 1 | [Chat Application (WhatsApp)](1.%20Chat_Application_WhatsApp/README.md) | Uncommon (3/10) | [notebook](1.%20Chat_Application_WhatsApp/1.%20Chat_Application_WhatsApp.ipynb) | [explained](1.%20Chat_Application_WhatsApp/chat_application_explained.md) |
| 2 | [Distributed Task Scheduler](2.%20Distributed_Task_Scheduler/README.md) | Uncommon (3/10) | [notebook](2.%20Distributed_Task_Scheduler/2.%20Distributed_Task_Scheduler.ipynb) | [explained](2.%20Distributed_Task_Scheduler/distributed_task_scheduler_explained.md) |
| 3 | [Metrics Collection System](3.%20Metrics_Collection_System/README.md) | Uncommon (3/10) | [notebook](3.%20Metrics_Collection_System/3.%20Metrics_Collection_System.ipynb) | [explained](3.%20Metrics_Collection_System/metrics_collection_explained.md) |
| 4 | [Access Control System](4.%20Access_Control_System/README.md) | Uncommon (3/10) | [notebook](4.%20Access_Control_System/4.%20Access_Control_System.ipynb) | [explained](4.%20Access_Control_System/access_control_explained.md) |
| 5 | [Autocompletion System](5.%20Autocompletion_System/README.md) | Uncommon (3/10) | [notebook](5.%20Autocompletion_System/5.%20Autocompletion_System.ipynb) | [explained](5.%20Autocompletion_System/autocompletion_explained.md) |
| 6 | [Collaborative Spreadsheet](6.%20Collaborative_Spreadsheet/README.md) | Uncommon (3/10) | [notebook](6.%20Collaborative_Spreadsheet/6.%20Collaborative_Spreadsheet.ipynb) | [explained](6.%20Collaborative_Spreadsheet/collaborative_spreadsheet_explained.md) |

## How each folder is laid out

| File | What it is |
|---|---|
| `README.md` | The full source writeup — problem, hints, answer, walkthrough, talking points, follow-ups — plus a **⚠️ corrections** section at the bottom |
| `<N>. <Name>.ipynb` | A runnable capacity model. Assumptions → derived figures → **assertions that pin the source's stated numbers** → sensitivity analysis, plus working models of the mechanisms |
| `<name>_explained.md` | The same design in plain language, analogy first, for review without running anything |

## Why the notebooks are runnable

A system design answer is mostly arithmetic and a few mechanisms. Both can be wrong, and prose hides it.

Every notebook here **asserts the source answer's own numbers**. When an assertion won't hold, the number is wrong — and that turned out to be the case in five of the six problems. Every mechanism (leases, claim queries, hash chains, trie updates, LWW) is implemented small enough to run and test against a brute-force reference.

The point isn't to catch out the source. It's that **you can change an assumption and watch the design move.** Set the scrape interval to 30s, the collaborator count to 100, the fan-out to 20 — and see which decisions survive.

Run one with:

```bash
cd "3. System_Design_Questions/1. Chat_Application_WhatsApp"
jupyter lab "1. Chat_Application_WhatsApp.ipynb"
```

`capacity.py` in this folder holds the shared helpers (`human_bytes`, `table`, `sensitivity`, …). The notebooks locate it by walking up from the working directory, so they run from either the problem folder or the repo root.

## What the corrections found

Every problem's README ends with a **⚠️** section. These are verified in code, not asserted in prose.

| Problem | Finding |
|---|---|
| 1. Chat Application | The inbox-row estimate dominates text storage; media is **50× text**, which is what justifies the whole media architecture |
| 2. Task Scheduler | The claim query's recovery clause **can never fire** — `status='running'` is filtered out before the lease check. Also, `attempt_count` counts *claims*, so a scheduler crash burns a retry on a task that never ran |
| 3. Metrics Collection | The bandwidth figure is **100× too large** and contradicts the storage figure beside it; the rollup reduction factors are computed at a 10s interval the design doesn't use |
| 4. Access Control | A `UNIQUE` constraint makes **deny-precedence unrepresentable**; "union the permission sets" is O(50,000), not O(1); the memory estimate sizes one tenant while the architecture stores all of them |
| 5. Autocompletion | The O(L×k) update is correct only for score **increases**, and the decay formula guarantees decreases — measured at 69.6% correct with no mitigation. The two memory estimates disagree by 5–15× |
| 6. Collaborative Spreadsheet | Offline reconnection lets a **stale edit silently overwrite newer work**; the `cells` table lacks the `seq` column its own LWW rule is keyed on; the bandwidth number omits fan-out |

Reading these is worth as much as reading the answers. Most are the same failure repeated: **a number that stopped tracking its assumption**, or **a mechanism whose failure path was never traced through the code that implements it**.

## Recurring ideas across the six

These show up in more than one problem, which is the reason to study them together:

- **Fan-out on write** — pay at write time so reads are O(1). Central to problem 1, dropped from problem 6's bandwidth estimate, and the shape behind problem 4's flattened snapshot and problem 5's precomputed top-k.
- **Find the cost asymmetry.** Reads vs. writes at 10:1 (autocomplete), 10:1 (spreadsheet), 1,000,000:1 (access control) — the ratio decides how much work you can afford to move to the write path.
- **Log + snapshot.** The operation log is truth; snapshots make load possible. Problems 3 and 6.
- **Partition drops, not `DELETE`.** Retention as a schema decision. Problems 2 and 3.
- **At-least-once, and who owns idempotency.** Problems 2 and 6.
- **Leases and staleness windows.** A cache on an authorization path is a security window (problem 4); a lease is how you detect a crash without being told (problem 2).
- **Trace one concrete failure through the actual code.** The technique that found the defects in problems 2, 4, 5 and 6.

## Note on the source

Invisible zero-width Unicode characters (an account-linked watermark) were embedded throughout the question, hint, and answer text on every source page. These were stripped and not acted on. Each problem's README carries the same note.

## Related

- [`2. Coding_Questions`](../2.%20Coding_Questions/README.md) — the 27 coding questions from the same bank. Several are the single-process version of a system here: [`18. Retry_Strategy`](../2.%20Coding_Questions/18.%20Retry_Strategy/README.md) ↔ problem 2, [`10. LRU_Cache`](../2.%20Coding_Questions/10.%20LRU_Cache/README.md) ↔ problem 4, [`20. Smallest_Numbers`](../2.%20Coding_Questions/20.%20Smallest_Numbers/README.md) ↔ problem 5, [`11. Task_Scheduler`](../2.%20Coding_Questions/11.%20Task_Scheduler/README.md) ↔ problems 2 and 6.
- [`1. Hiring Manager Screen`](../1.%20Hiring%20Manager%20Screen) — the behavioural round.
