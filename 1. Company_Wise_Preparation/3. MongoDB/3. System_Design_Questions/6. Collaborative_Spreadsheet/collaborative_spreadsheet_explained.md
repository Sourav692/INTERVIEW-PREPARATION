# Collaborative Spreadsheet — Explained Simply

## The Problem

Build Google Sheets. Many people editing the same grid at once, changes appearing instantly, nobody's work lost — including the person who went offline on a train.

## An Analogy First: The Shared Ledger and the Ticket Machine

Picture a room of accountants all updating one big ledger.

**The naive version:** everyone photocopies the whole ledger, edits their copy, and hands it back. Whoever hands it in last wins, and every other change that hour is erased.

**The real version:** nobody edits the ledger directly. Instead, you write your change on a slip — *"row 3, column B, now says 'hello'"* — and drop it in a box. A clerk takes each slip, **stamps it with the next number from a ticket machine**, and pins it to the wall in order.

The ledger is now just *what you get if you apply every slip in stamp order.*

Three things fall out for free:

1. **Conflicts resolve themselves.** Two slips for the same cell? The higher number wins. No negotiation, no lock.
2. **Nothing is lost on a crash.** The slips are on the wall; rebuild the ledger any time.
3. **You can see history.** Stop replaying at slip 400 and you have the ledger as it was.

One atomic ticket machine replaced an entire agreement protocol.

**But notice what the stamp actually records.** It's *when the clerk received the slip* — not when you wrote it. While everyone is in the room those are the same thing. The moment someone writes a slip on the train and hands it in an hour later, they are very different — and everything built on the stamp inherits that gap.

## Operations, Not State

This is the decision the whole design rests on.

| | State-based | **Operation-based** |
|---|---|---|
| What you send | "here's the document" | "B2 became `hello`" |
| Message size | megabytes | ~400 bytes |
| Conflicts | last full upload wins | resolved per cell |
| Crash recovery | whatever was last saved | replay the log |
| History | separate feature | free |

**And the cell is the unit of change** — not the row, not the document. Two people editing different cells then have no conflict *at all*, which is most of the traffic in a real spreadsheet.

## How a Conflict Actually Resolves

```
Alice's browser:  setCell(B2, "cat")  --sent-->
                                                 server assigns seq 41  --> everyone
Bob's browser:    setCell(B2, "dog")  --sent-->
                                                 server assigns seq 42  --> everyone

Both clients apply 41 then 42.  Final: B2 = "dog".
Alice saw "cat" for ~40ms (optimistic apply), then it flipped.
```

Nobody negotiated. **The counter decided.** That optimistic apply is why typing feels instant — the client doesn't wait for the round trip; it shows the edit immediately and corrects if the server disagrees.

## The Serious Bug: Going Offline Wins the Argument

Here's the answer's offline handling:

> *"On reconnect, the client sends all pending operations to the server. **The server assigns `seq` numbers in the order received.**"*

Watch what that does:

```
09:00  Alice goes offline.  Edits B2 = "old draft"       (queued locally)
09:05  Bob   edits B2 = "reviewed"                        seq 100
09:20  Carol edits B2 = "final, approved by legal"        seq 340
09:30  Alice reconnects. Her 09:00 edit arrives now...    seq 341
                                                          ↑ HIGHEST
       LWW: higher seq wins  →  B2 = "old draft"
```

**The person who was offline longest wins.** Thirty minutes of reviewed, approved work replaced by a stale draft — with no warning to anyone.

The answer calls this a "rebase". That word does a lot of concealing: **git's rebase stops on a conflict and asks you.** This one applies silently.

### The fix: carry the version you edited against

```json
{"type": "setCell", "cell": {...}, "value": {...}, "baseSeq": 99}
```

If the cell's current `seq` is higher than `baseSeq`, this edit was made against a version that no longer exists. The server must not apply it silently.

```
WITH baseSeq: THE STALE EDIT IS CAUGHT
  State before Alice  final, approved by legal
  FINAL VALUE         final, approved by legal
  Conflicts surfaced  [('old draft', 'final, approved by legal')]
```

What to do *with* the conflict is a product decision — name it explicitly:

| Policy | Behaviour |
|---|---|
| **Reject + surface** | show both, let Alice choose (what Sheets effectively does) |
| **Keep both** | write the loser into a comment or "conflicting copy" |
| **LWW by wall clock** | compare timestamps, not seq — better, but client clocks lie |
| **Blind LWW by seq** | as written: **silent data loss** |

> LWW isn't the mistake. LWW keyed on **arrival** order is a different rule from LWW keyed on **edit** order, and only one of them matches what a user expects.

### Why this survives testing

Cells the offline client *didn't* touch are completely fine — both edits survive, exactly as the answer claims. The bug only bites on the same cell, which is the rare case, which is why it ships.

**Silent data loss in the uncommon path is the worst bug class there is.**

## The Missing Column

The conflict rule is *"the operation with the higher `seq` wins."* Now look at what the `cells` table stores:

```sql
value, format, updated_at, updated_by      -- no seq
```

The materialized view has **no record of which operation produced its current value**. So when a materializer, a recovering replica, or a client filling a gap receives an operation, it cannot tell whether that operation is newer or older than what it already holds.

Measured over 200 random deliveries of the same 4 operations:

```
seq column ABSENT   149 / 200 orderings give the WRONG value
seq column PRESENT    0 / 200 orderings give the WRONG value
```

The fix is one column and a compare-and-set:

```sql
ALTER TABLE cells ADD COLUMN seq BIGINT NOT NULL;
```
```python
if op.seq > cell.seq:
    cell.value, cell.seq = op.value, op.seq
```

### This also repairs a hand-wave

> *"Operations are idempotent and commutative enough for our purposes."*

As written they are **neither**. `setCell(B2,"a")` then `setCell(B2,"b")` is obviously not the same as the reverse — that's *why* you needed the counter.

But with a per-cell `seq` and max-wins, they genuinely become both. Apply them in any order, apply them twice, apply them a hundred times — same answer. And *that* is what makes replay, crash recovery, and at-least-once delivery safe.

> Idempotent and commutative are properties you **build**, not adjectives you assert.

## The Bandwidth Number Is Missing Its Multiplier

> *"At 30,000 ops/sec × 400 bytes ≈ 12 MB/s of operation traffic. That's trivially handled by a handful of relay servers."*

12 MB/s is **ingress** — what arrives. Every operation is then broadcast to every *other* subscriber of that document. That's the entire point of a collaborative app.

```
INGRESS (as stated)          12.00 MB/s

EGRESS at   2 collaborators  12.00 MB/s   (1x)
EGRESS at   5 collaborators  48.00 MB/s   (4x)
EGRESS at  10 collaborators  108.00 MB/s  (9x)
EGRESS at 100 collaborators  1.19 GB/s    (99x)
```

At 100 editors — the case the answer names in the very next bullet — that's **95% of a 10 Gb/s NIC, for one document.**

This is **fan-out on write**, the exact concept that's the headline insight of the [chat application](../1.%20Chat_Application_WhatsApp/README.md) question. Here it's dropped.

It doesn't break the design — relays are stateless and scale horizontally. But 12 MB/s is the number that sizes your relay fleet, and it's off by the collaboration factor, which is the whole product.

**And note the asymmetry it creates:**

| | Grows with |
|---|---|
| Storage | ops |
| Bandwidth | ops × collaborators |

Compaction fixes the first and does **nothing** for the second.

## Why Snapshots Aren't Optional

```
Live state per doc    750 KB
Log per doc per year   40 MB
Compaction ratio      53 : 1
```

The log is ~50× the state it produces. Opening a one-year-old document:

```
Replay from scratch  100,000 ops
Snapshot + tail      1 fetch + 200 ops
Speedup              500x
```

Snapshotting isn't an optimization — **it's what makes document load possible at all.** Fetch the latest snapshot, then only the operations after its version.

And retention has two different answers, which is worth separating:

- **For correctness:** the log can be truncated behind the latest snapshot.
- **For product:** "see version history" is a feature, so keep the log as long as you promise that — and not a day longer.

## The Follow-Ups Worth Preparing

**Two people typing in the same cell.** Cell-level LWW means one of them loses their *entire entry*, not one character — jarring to watch happen live. Sheets' answer is **presence**: show that someone else is in the cell, and don't merge. If you genuinely want character-level merging you need OT or a text CRDT *inside* the cell, and now a cell is a small collaborative document of its own. Say which you're building; they're very different systems.

**Two people formatting the same cell.** This is the argument for splitting `setValue` and `setFormat` into separate operation types. Packed into one operation, bolding a cell and typing in it conflict for no reason — and worse, an operation carrying `format: null` silently wipes formatting someone else just applied. **Independent operations never conflict; make them independent.**

**Circular references.** Check the dependency graph for cycles *before* accepting the formula, not during evaluation — Kahn's algorithm or DFS with a visiting set. Same rule as everywhere: validate at write time or hang at read time. But surface it as `#REF!` rather than rejecting the keystroke, because users often build a cycle *en route* to a valid formula.

**Copy-pasting a range.** One operation, not N — otherwise a 10,000-cell paste becomes 10,000 broadcasts and everyone watches it dribble in. Treat the range as one atomic entry in the total order: it wins over everything before it, loses to everything after.

**A 100,000-row sheet.** Don't send it. The client renders a viewport, so fetch a viewport — request cells by rectangle, with the sparse map making empty regions free. The subtlety: a client must still *receive operations* for cells it isn't displaying, or it silently misses updates when the user scrolls. Either subscribe to the whole op stream (cheap — ops are tiny) and materialize lazily, or re-fetch on scroll and accept a seam.

## Common Mistakes

- **Syncing state instead of operations.** Loses durability, ordering, conflict resolution and history in one move.
- **Making the document or row the unit of change.** Kills message size and manufactures conflicts.
- **Reaching for consensus.** One atomic per-document counter is enough.
- **Assigning `seq` on arrival for offline edits.** The longest-offline client wins.
- **Calling silent overwrite a "rebase."** Rebase stops on conflict.
- **A materialized view without the key its consistency rule uses.** `cells` needs `seq`.
- **Asserting commutativity instead of building it.** Max-wins makes it true; the phrase alone doesn't.
- **Quoting ingress as if it were total traffic.** Egress is `(C−1)×`.
- **No snapshots.** Replaying a year to open a file.
- **One operation type for value and format.** Manufactured conflicts and accidental format-wiping.

## The Takeaway

> Don't store the document — store the slips, and let a ticket machine number them. The document is what you get when you apply them in order.

Three ideas carry it: **operations, not state** (durability, ordering, conflicts and history all fall out of one decision), **one atomic counter beats a consensus protocol** (a per-document `seq` gives a total order for free), and **count egress, not just ingress** (in any broadcast system, bandwidth is ops × collaborators).

And the question that found the worst bug: **ask what your ordering key actually measures.** `seq` records when the server *heard* about an edit, not when someone *made* it. Online those coincide. Offline they don't — and every guarantee built on `seq` quietly inherits the gap.
