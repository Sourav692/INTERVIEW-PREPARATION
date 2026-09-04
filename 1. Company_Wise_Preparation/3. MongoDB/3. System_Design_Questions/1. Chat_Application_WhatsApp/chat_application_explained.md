# Chat Application (WhatsApp) — Explained Simply

## The Problem

Build WhatsApp. 500 million people, 50 messages each per day, delivered in under half a second, never lost, and the server isn't allowed to read any of them.

## An Analogy First: The Post Office and the Pigeonholes

Picture an old-fashioned mail room.

**The naive version:** everyone's post sits in one giant pile. To check your mail, you sift through the whole pile looking for your name. Slow, and it gets slower as more people join.

**The pigeonhole version:** every person has their own numbered slot. When a letter arrives for you, the clerk **copies it into your slot immediately** — before you've even walked in. Checking your mail is now: go to slot 47, take what's there. Instant, no matter how big the building.

That's the **inbox table**, and it's the single most important idea in the design.

The cost is real: a letter to 10 people gets copied 10 times. But people check their mail far more often than they send it, so you pay once at write time to make every read free.

And the encryption twist: the letters are in **sealed envelopes the clerk cannot open**. They can read the address on the outside — enough to sort it into the right slot — but never the contents.

## The Core Decision: Fan-Out on Write

When Alice sends a message to a group of 10, you have two options:

| | **Fan-out on write** | **Fan-out on read** |
|---|---|---|
| On send | write 10 inbox rows | write 1 row |
| On open | read your own inbox — **O(1)** | gather from the conversation — O(k) |
| Storage | 10× amplification | none |

Chat is overwhelmingly **read-heavy** — you open the app dozens of times a day and send far less. So you pay the storage cost once and make every read trivial.

That's fan-out on write, and it's why the `inbox` table exists.

### Why the inbox table is doing three jobs

1. **Offline delivery.** The message is *already sitting in Carol's inbox* before she reconnects. "Delivering" it is just telling her something's there.
2. **O(1) sync.** Reconnecting after a week is one query: `WHERE user_id = ? AND message_id > ?`. It hits exactly one shard.
3. **Per-recipient status.** "Delivered" and "read" are facts about a *person*, not about a message. Bob read it; Carol didn't. A single status field on the message can't express that.

## The Three Ticks Are Three Different Events

This is what interviewers probe, and conflating them is the classic mistake.

| Tick | Means | When |
|---|---|---|
| **One tick** | the **server** durably stored it | after the database write replicates |
| **Two ticks** | the recipient's **device** has it | after the device ACKs the push |
| **Blue ticks** | the recipient **opened** the chat | after a read receipt |

The critical boundary is the first one:

> **The sender's ✓ must mean "durably stored", not "accepted".**

If you acknowledge before the write is replicated and the server crashes, Alice believes she sent a message that no longer exists. Everything *after* that ✓ — the fan-out, the pushes — can be asynchronous. That split is what lets a message to a 1,000-person group feel instant.

## Step-by-Step: Alice Sends "hi" to a Group of Four

---

**1. Alice's phone encrypts it.** The plaintext never leaves her device. What goes on the wire is a ciphertext blob.

---

**2. The Chat Service writes one row to `messages`.** Durable, replicated.

**Alice sees one tick.** Note what this does *not* mean: nobody has received anything yet.

---

**3. The Chat Service writes four `inbox` rows** — Bob, Carol, Dan, and Alice's own copy.

This is the fan-out. Four rows for one message.

---

**4. It publishes a `MessageCreated` event to the queue** and returns. The expensive part is now somebody else's problem.

---

**5. A delivery worker picks up the event** and checks each recipient's presence:

- **Bob is online** → push through his gateway → his phone ACKs → his inbox row becomes `delivered` → **Alice sees two ticks**
- **Carol is offline** → do nothing. Her row is already in her inbox; she'll get it on reconnect.
- **Dan is offline with the app killed** → send an Apple/Google push notification saying *"New message"* — **with no content**, because the server can't read it anyway.
- **Alice's own copy** → already marked read.

---

**6. Bob opens the conversation.** His phone sends a read receipt → his inbox row becomes `read` → **Alice sees blue ticks**.

## Why WebSockets, Not Polling

Polling means asking "anything new?" every few seconds.

- **Latency:** on average you wait half the poll interval. A 5-second poll means 2.5 seconds of delay — five times over the 500 ms budget on its own.
- **Waste:** 500M users polling every 5 seconds is 100M requests/second, almost all returning "nothing".

A **WebSocket** stays open, so the server can push the instant a message arrives. That's the only way to hit sub-500 ms.

The cost: 60 million open connections to hold. Which is why **gateways are separate from everything else** — they hold sockets and no data, so you can scale them independently of the database.

## Does It Actually Fit in 500 ms?

The notebook adds up a realistic budget:

| Step | Cost |
|---|---|
| Client encrypt | 5 ms |
| Client → Gateway | **40 ms** |
| Gateway → Chat Service | 2 ms |
| Write `messages` (replicated) | 15 ms |
| Write inbox rows | 10 ms |
| Publish to queue | 5 ms |
| Queue → delivery worker | 20 ms |
| Presence lookup | 2 ms |
| Worker → recipient's Gateway | 5 ms |
| Gateway → recipient | **40 ms** |
| Client decrypt + render | 10 ms |
| **Total** | **154 ms** |

Comfortably inside budget — but look at what dominates: **the two network hops, at 80 ms combined.** Everything the server does costs 59 ms; the speed of light costs 80.

That's the argument for putting gateways close to users. Route a message through a datacenter on another continent and those two hops become 300 ms, and the budget is gone.

## The Number That Decides the Architecture

Here's the arithmetic that matters most, all derived from "500M users × 50 messages":

```
25 billion messages/day
  → 289,000/sec average, ~1.16M/sec at peak

Text storage:
  25B messages × 4 inbox rows × 200 bytes  = 20 TB/day
  + the messages table                     =  5 TB/day
                                             ─────────
                                              25 TB/day

Media storage:
  10% of messages × 500 KB average         = 1.25 PB/day
```

> **Media is 50× text.**

That single ratio justifies the entire media architecture. You cannot put 1.25 PB/day through a database. So media goes to object storage with a CDN, and messages carry only a **media ID** — a pointer.

Say the number out loud in an interview and the design decision defends itself.

### And know which assumption you're standing on

The notebook runs a sensitivity analysis, and the result is worth internalising:

| Change | Effect on storage |
|---|---|
| Fan-out 4 → 20 (group-heavy product) | **5× more text storage** |
| Media 500 KB → 2 MB (video-heavy) | **4× more media storage** |
| Row size 200 → 300 bytes | barely moves |

**The point of a capacity estimate isn't the number — it's knowing which input the number hangs on.** Here it's fan-out and media size. Tuning row sizes is noise.

## End-to-End Encryption: What It Costs You

The server relays sealed envelopes. It knows *who* sent *what size* message to *whom, when* — and nothing else.

That's the guarantee. Here's the bill:

| You can't | Because |
|---|---|
| **Search messages server-side** | there's nothing readable to index |
| **Show message text in a push notification** | the server can't read it — so the push says "New message" and the app fetches the real one after waking up |
| **Recover history for a lost phone** | the keys were on the phone |
| **Filter spam by content** | you only have metadata and behaviour |

**Enumerating what encryption forbids is worth more than describing how it works.** It shows you understand the trade rather than reciting a protocol name.

*(Mechanically: one-on-one chats use X3DH to agree a shared secret and the Double Ratchet to rotate keys per message. Groups use **sender keys** — each member has one key they encrypt with — so a message costs one encryption instead of k.)*

## Where This Design Breaks: The 100,000-Person Group

Fan-out on write means one message becomes 100,000 inbox rows. A chatty group that size would generate more writes than the rest of the system combined.

**The fix is to switch strategies by size:**

- **Small groups** → fan out on write. Reads stay O(1), and most groups are small.
- **Huge groups** → fan out on read. Store once; members gather from the conversation when they open it.

This is exactly what Twitter does for celebrity accounts — you don't copy a tweet into 100 million timelines. The hybrid is the answer, and knowing *where* the crossover sits is the interesting part.

## Common Mistakes

- **Polling instead of pushing.** Blows the latency budget before you've written a line.
- **Acknowledging the sender before the write is durable.** Loses messages on crash.
- **One status field on the message.** Can't express "Bob read it, Carol didn't".
- **Pushing media through the message pipeline.** 1.25 PB/day doesn't belong in a database.
- **Claiming accurate presence.** Heartbeats are periodic, mobile OSes kill sockets. It's best-effort with a 30–60 second staleness window — say so.
- **Promising exactly-once delivery.** It's at-least-once; the client de-duplicates on `message_id`.
- **Sorting by client timestamp.** Two phones' clocks disagree. Sort by the server-assigned `message_id`.
- **Hand-waving the encryption limits.** "We'll add search later" isn't an answer when the server can't read anything.

## The Takeaway

> The server is a **dumb relay for sealed envelopes** that knows just enough addressing to sort them into the right pigeonholes.

Three ideas carry the whole design: **fan-out on write** (pay at send time so every read is O(1)), **durable before ACK** (the sender's tick is a storage guarantee, everything after it can be async), and **media is 50× text** (which is why it never touches the database).

And the transferable skill isn't the architecture — it's doing the arithmetic *first*, then letting the numbers choose the design.
