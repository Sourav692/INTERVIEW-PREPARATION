# Design an Online Collaborative Spreadsheet

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** System Design · **Tags:** Onsite Loop, API Design, Caching, Concurrency, Databases, Distributed Systems · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Design an online collaborative spreadsheet application (similar to Google Sheets) that allows multiple users to view and edit spreadsheets in real time.

**Requirements:**

- Users should be able to create, view, and edit spreadsheets.
- Multiple users should be able to collaborate on the same spreadsheet simultaneously, with changes reflected in real time.
- The system should handle conflicts when users edit the same cell concurrently.
- The system should support basic spreadsheet operations such as entering data, formulas, and formatting.
- The system should scale to support a large number of users and spreadsheets.

**Consider the following in your design:**

- How to model and store spreadsheet data.
- How to propagate changes between collaborators in real time.
- How to resolve conflicts and maintain consistency.
- How to handle offline edits and reconnection.
- How to ensure performance and scalability.

---

## Study Tools

### Hint 1

The core problem is synchronizing a shared state across many clients. Think about what the **minimal unit of change** is and how you can give every edit a stable, orderable identity.

### Hint 2

Model the spreadsheet as a set of individually addressable cells, each with a version history. Operations on a cell can be transformed against concurrent operations to achieve convergence without a central lock.

### Hint 3

Use a centralized relay that assigns **monotonically increasing sequence numbers** to operations per document. Clients send operations, the server broadcasts them, and clients apply them in order; for concurrent edits to the same cell, use a **last-writer-wins** policy keyed by the server-assigned sequence number.

---

### Answer

This is a collaborative editing problem that boils down to operational transformation (OT) or CRDTs layered on top of a cell-based data model with a centralized relay server. The most standard interpretation for an interview is a Google Sheets-like system where a server is the source of truth and clients are mostly-thin editors.

#### High-level architecture

```
Client (Browser) <--WebSocket--> Gateway/Relay <---> Spreadsheet Service <---> Storage
                                       |
                                       v
                              Pub/Sub (per-document channel)
```

- **Client:** React or similar SPA. Renders a grid, captures edits, maintains a local model, applies remote operations.
- **Gateway/Relay:** Terminates WebSocket connections, authenticates, routes messages to the right document's channel, assigns sequence numbers to operations, broadcasts to all subscribers, and persists operations to a durable log.
- **Spreadsheet Service:** Handles document CRUD, permission checks, snapshotting, and formula evaluation.
- **Storage:** A durable operation log (e.g., Kafka or a database with ordered writes) plus periodic snapshots of the document state.

#### Data model

The core unit is a **cell**. A spreadsheet is a collection of cells, each addressed by `(sheetId, row, col)`. We do not store a 2D array; we store a **sparse map** of only non-empty cells.

```sql
CREATE TABLE spreadsheets (
    id            UUID PRIMARY KEY,
    owner_id      UUID NOT NULL,
    name          TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL,
    version       BIGINT NOT NULL DEFAULT 0,   -- last applied op sequence number
    snapshot_ref  TEXT,                        -- pointer to latest snapshot in object storage
    settings      JSONB
);

CREATE TABLE cells (
    spreadsheet_id  UUID NOT NULL,
    sheet_id        TEXT NOT NULL,
    row             INT NOT NULL,
    col             INT NOT NULL,
    value           JSONB,   -- {type: "number"|"string"|"formula", raw: "...", formatted: "..."}
    format          JSONB,   -- {bold, italic, bgColor, ...}
    updated_at      TIMESTAMPTZ NOT NULL,
    updated_by      UUID NOT NULL,
    PRIMARY KEY (spreadsheet_id, sheet_id, row, col)
);

CREATE TABLE operations (
    spreadsheet_id  UUID NOT NULL,
    seq             BIGINT NOT NULL,   -- per-spreadsheet monotonic sequence
    user_id         UUID NOT NULL,
    op              JSONB NOT NULL,    -- the actual operation payload
    applied_at      TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (spreadsheet_id, seq)
);
```

The `operations` table is the **source of truth** for the document's history. The `cells` table is a materialized view of the latest state, rebuilt from the operation log when needed.

#### Operation format

Every edit is an operation with this shape:

```json
{
  "opId": "uuid",
  "spreadsheetId": "uuid",
  "seq": 42,
  "userId": "uuid",
  "type": "setCell",
  "cell": {"sheetId": "Sheet1", "row": 3, "col": 2},
  "value": {"type": "string", "raw": "hello"},
  "format": null,
  "timestamp": 1717000000000
}
```

Operations are idempotent and commutative enough for our purposes. The server assigns `seq` from a per-spreadsheet counter. This gives us a **total order** for every operation on a given spreadsheet.

#### Real-time propagation flow

1. User A edits cell B2. The client creates an operation locally, applies it **optimistically**, and sends it over the WebSocket.
2. The relay server validates the operation (permissions, well-formedness), assigns it the next `seq` for that spreadsheet, persists it to the operation log, and broadcasts it to all subscribers of that document's channel.
3. User B's client receives the operation. Since `seq` is monotonically increasing per spreadsheet, B's client can **detect gaps** (missed operations) and request missing ones before applying.
4. Both clients now have the same state.

#### Conflict resolution

For concurrent edits to the same cell, we use **last-writer-wins (LWW) keyed by the server-assigned `seq`**. Since the server assigns `seq` atomically, there is a single total order. The operation with the higher `seq` wins. This is simple, predictable, and matches what Google Sheets actually does in practice for cell-level edits.

For edits to different cells, there is no conflict. They apply independently.

For **formulas**, we store the formula string as the cell's raw value and evaluate it server-side (or in a formula engine). If a formula references a cell that changes, the dependent cell's displayed value is recomputed. We can maintain a **dependency graph** per spreadsheet to know which cells to recompute when a change arrives.

#### Offline edits and reconnection

When a client goes offline:

1. The client keeps a local queue of pending operations with locally generated op IDs.
2. On reconnect, the client sends all pending operations to the server.
3. The server assigns `seq` numbers **in the order received**, broadcasts them, and the client reconciles.
4. If the client's local state diverged from the server's (because other users edited while it was offline), the client first fetches all operations with `seq` greater than its last known `seq`, applies them, then applies its own pending operations on top. This is a simplified OT approach — for cell-level LWW, it reduces to *"rebase my pending ops on top of the server state."*

#### Capacity estimates

Say we have **10 million daily active users**, each making an average of **50 edits per day**. That's **500 million operations per day**.

- 500,000,000 ops/day ÷ 86,400 seconds/day ≈ **5,800 ops/sec average**. Peak is typically 3–5× average, so **~20,000–30,000 ops/sec peak**.
- Each operation is small — maybe 200–500 bytes on the wire. At 30,000 ops/sec × 400 bytes ≈ **12 MB/s** of operation traffic. That's trivially handled by a handful of relay servers.
- For storage, 500M ops/day × 400 bytes ≈ **200 GB/day** of operation log. Over a year that's **~73 TB**. We'd compact this aggressively: snapshot the document state periodically and truncate the operation log, keeping only recent operations plus snapshots.
- A single spreadsheet with **100 concurrent editors** is the extreme case. A relay server handling a single popular document can easily handle 100–1000 messages/sec on one WebSocket channel. We shard documents across relay servers by `spreadsheetId` hash, and for very hot documents, we can fan out via a pub/sub system.

#### Scalability

- **Relay servers** are stateless (or nearly stateless — they cache the latest `seq` per active document). Scale horizontally behind a load balancer, routing by `spreadsheetId`.
- The **operation log** is partitioned by `spreadsheetId`. Each partition can be served by a different Kafka partition or database shard.
- **Snapshots** are stored in object storage (S3/GCS). A client loading a spreadsheet fetches the latest snapshot plus any operations with `seq` greater than the snapshot's version.
- **Formula evaluation** is done asynchronously. A change triggers a recompute of dependent cells, and the results are written back as new operations (or as derived state, not as user operations).

**Time:** O(1) per operation for the relay path (validate, assign seq, broadcast). Client-side apply is O(1) per operation for cell edits, O(dependents) for formula recomputation.
**Space:** O(n) where n is the number of non-empty cells for the live state; the operation log grows at O(ops) but is compacted via snapshots.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest thing that could work: a single server holding the entire spreadsheet in memory, clients sending full cell updates over WebSocket, and the server broadcasting to everyone. This works for one spreadsheet with a few users, but it breaks down quickly — every keystroke becomes a full document broadcast, and the server's memory becomes the bottleneck.

The first refinement is to **make the cell the unit of change**. Instead of sending the whole document, send `{cell: B2, value: "hello"}`. This cuts message size by orders of magnitude and lets different users edit different cells without stepping on each other.

Next, you realize you need **ordering**. If two users edit the same cell at the same time, you need a rule for who wins. The cleanest approach is to have the server assign a monotonically increasing sequence number to every operation. Now every operation has a stable position in a total order, and LWW falls out naturally: higher `seq` wins.

At this point, you have a working system for online collaboration. The next question is **durability and scale**. A single server holding everything in memory will lose data on crash and can't handle many documents. So you introduce a durable operation log — every operation is persisted before it's broadcast. This gives you crash recovery: on restart, replay the log to rebuild state.

Then you add **snapshots**. Replaying a year's worth of operations to load a document is too slow. Periodically write the full cell state to object storage, and on load, fetch the snapshot plus only the operations since the snapshot's version. This is the standard log-compaction pattern.

Finally, you handle **offline edits**. The client keeps a queue of pending operations. On reconnect, it fetches all operations with `seq` greater than its last seen `seq`, applies them, then applies its own pending operations on top. Since cell edits are mostly independent, this "rebase" is usually trivial. For same-cell conflicts, the server's `seq` ordering decides.

The key insight throughout is that you're building an **operation-based system, not a state-based one**. State is derived from the operation log. This gives you ordering, durability, and the ability to reconstruct any historical state.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Start with the operation log as the source of truth** — this single decision makes durability, ordering, and conflict resolution fall out naturally, and it's the thing that separates a real design from a hand-wavy "just use WebSockets" answer.
- **Make the cell the unit of change** — sending whole-document updates or whole-row updates doesn't scale; cell-level operations keep messages small and make concurrent edits to different cells trivially conflict-free.
- **Assign sequence numbers server-side, atomically** — this gives you a total order for free, which means LWW conflict resolution is well-defined and every client converges to the same state without needing a distributed consensus protocol.
- **Walk through the offline reconciliation flow explicitly** — name the client's pending queue, the gap detection via `seq`, and the rebase step; interviewers want to see you've thought about what happens when a client reconnects after 30 minutes and 200 remote operations.
- **Put concrete numbers on the board** — 5,800 ops/sec average, 12 MB/s of traffic, 200 GB/day of log growth; these show you can do back-of-the-envelope math and that your design actually fits the scale.
- **Address formula dependencies** — mention the dependency graph and asynchronous recomputation; it's a detail many people skip, and it shows you understand that a spreadsheet is more than a grid of strings.
- **Explain snapshotting and log compaction** — this is the difference between a design that works for a week and one that works for years; state grows linearly with the log unless you compact it.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you handle a user editing a cell while another user is typing in the same cell?** — Think about per-cell locking or character-level operations vs. cell-level LWW.
- **What happens if two users format the same cell differently at the same time?** — Consider whether formatting is part of the cell operation or a separate operation type.
- **How do you handle a formula that creates a circular reference?** — Think about cycle detection in the dependency graph and how to surface the error to users.
- **How would you support copy-paste of a range of cells as a single operation?** — Consider range operations and how they interact with concurrent edits to cells inside the range.
- **How do you handle a spreadsheet with 100,000 rows — do you send the whole thing to the client?** — Think about virtualized rendering and server-side pagination of the cell map.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Three problems with the answer

All three are demonstrated with runnable assertions in [`6. Collaborative_Spreadsheet.ipynb`](6.%20Collaborative_Spreadsheet.ipynb).

### 1. Offline reconnection silently destroys other people's work

This is the serious one, and the answer presents it as a solved detail.

> *"On reconnect, the client sends all pending operations to the server. **The server assigns `seq` numbers in the order received**… for cell-level LWW, it reduces to 'rebase my pending ops on top of the server state.'"*

Assigning `seq` on **arrival** means an operation's position in the total order reflects *when it reached the server*, not when it was made. So:

```
09:00  Alice goes offline.  Edits B2 = "old draft"        (queued locally)
09:05  Bob   edits B2 = "reviewed"                        seq 100
09:20  Carol edits B2 = "final, approved by legal"        seq 340
09:30  Alice reconnects. Her 30-minute-old edit gets      seq 341
       -> LWW: highest seq wins -> B2 = "old draft"
```

**The person who was offline longest wins.** Thirty minutes of newer, reviewed work is overwritten by a stale edit, with no warning to anyone. Calling this a "rebase" obscures it: git's rebase *stops* on a conflict; this one applies silently.

The fix is to make each pending operation carry the `seq` it was based on, and check it at apply time:

```json
{"type": "setCell", "cell": {...}, "value": {...}, "baseSeq": 99}
```

If the cell's current `seq` is greater than `baseSeq`, the operation is **stale** and the server must not silently apply it. What to do instead is a product decision worth naming explicitly:

| Policy | Behaviour |
|---|---|
| **Reject + surface** | tell Alice her offline edit conflicts, show both values, let her choose (what Google Sheets effectively does) |
| **Keep both** | write Alice's value into a comment or a "conflicting copy", never lose data |
| **Last-writer-by-wall-clock** | compare `timestamp`, not `seq` — better, but client clocks lie |
| **Blind LWW-by-seq** | as written — silent data loss |

The point isn't that LWW is wrong. It's that LWW keyed on *arrival order* is not the same rule as LWW keyed on *edit order*, and only one of them is what a user expects.

### 2. The `cells` table has no `seq` column — so LWW cannot actually be enforced there

The conflict rule is *"the operation with the higher `seq` wins."* But look at what `cells` stores:

```sql
value, format, updated_at, updated_by      -- no seq
```

The materialized view has no record of which operation produced its current value. So when the materializer (or a recovering replica, or a client replaying a gap-fill) receives an operation, **it cannot tell whether that operation is newer or older than what's already there.** Any out-of-order or duplicate delivery corrupts the state, and re-running the log is only safe if it's replayed in exact order from the beginning.

Add the column:

```sql
ALTER TABLE cells ADD COLUMN seq BIGINT NOT NULL;
```

and make the apply function compare-and-set:

```python
if op.seq > cell.seq:
    cell.value, cell.seq = op.value, op.seq
```

This also repairs the answer's claim that *"operations are idempotent and commutative enough for our purposes."* As written they are neither — `setCell(B2,"a")` then `setCell(B2,"b")` is plainly not the same as the reverse. **With a per-cell `seq` and a max-wins apply, they genuinely become both**, which is exactly why the column matters: it turns a hand-wave into a property you can rely on for replay, recovery, and out-of-order delivery.

### 3. The bandwidth estimate ignores fan-out — the whole point of a collaborative app

> *"At 30,000 ops/sec × 400 bytes ≈ 12 MB/s of operation traffic. That's trivially handled by a handful of relay servers."*

12 MB/s is **ingress**. Every operation is then broadcast to every other subscriber of that document. With an average of *C* concurrent collaborators, egress is `(C − 1) ×` ingress:

| Avg. concurrent editors | Egress |
|---|---|
| 2 | 12 MB/s |
| 5 | 48 MB/s |
| 10 | 108 MB/s |
| 100 (the stated extreme, one hot doc) | ~1.2 GB/s |

The answer *names* the 100-editor case in the very next bullet and never multiplies it through. And note this is the same **fan-out on write** that the [chat application](../1.%20Chat_Application_WhatsApp/README.md) question makes its central insight — here it's dropped.

It doesn't break the design (relays are stateless and scale horizontally), but "12 MB/s, trivially handled" is the wrong number to say out loud: it's the one that decides how many relay servers you need, and it's off by the collaboration factor — which is the entire product.

**See also:** [`1. Chat_Application_WhatsApp`](../1.%20Chat_Application_WhatsApp/README.md) for fan-out done properly, [`11. Task_Scheduler`](../../2.%20Coding_Questions/11.%20Task_Scheduler/README.md) for the topological sort behind formula dependency graphs, and [`21. SnapID`](../../2.%20Coding_Questions/21.%20SnapID/README.md) for the log-plus-snapshot pattern.
