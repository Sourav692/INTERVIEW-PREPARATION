# Broadcast Message Bus — Explained Simply

## The Problem

Build a publish/subscribe bus. Anyone can **subscribe** to a named topic with a callback. Anyone can **publish** a message to a topic, and every current subscriber gets called.

```python
token = bus.subscribe("orders", print)    # returns a handle
bus.publish("orders", "order #42")        # -> every subscriber's callback runs
bus.unsubscribe(token)                    # stop listening
```

Sounds like ten lines. It is — and then one requirement makes it a real question:

> **Unsubscribing during a publish must not cause exceptions or missed deliveries to other subscribers.**

## First: What Pub/Sub Is For

The publisher doesn't know who's listening. The subscribers don't know who's sending. The **bus in the middle** is the only thing that knows both.

That decoupling is the whole point — you can add a new listener without touching the code that publishes. It's why MongoDB change streams, Kafka topics, and browser `addEventListener` all have this same shape.

The data model is almost nothing:

```
topics = {
    "orders":    [handler_A, handler_B],
    "shipments": [handler_C],
}
```

Everything hard about this problem is what happens *around* that dictionary.

## The Bug at the Heart of It

Here's the obvious `publish`:

```python
for handler in self.topics[topic]:      # walking the LIVE list
    handler(message)                     # ...and this call can modify it
```

The trouble: **a handler is code you don't control.** And one of the things it might do is call `unsubscribe`.

So the list **shrinks while the for-loop is walking it**.

- In **Java**, this raises `ConcurrentModificationException` — loud, but at least you find out.
- In **Python**, there's no exception. A `for` loop over a list tracks a hidden index. Remove an element and everything after it shifts left by one — but the index doesn't. **The next subscriber gets silently skipped.**

A message quietly not delivered, with no error anywhere, is about the worst failure mode there is.

### Watch it happen

Three subscribers: A, B, C. B unsubscribes itself.

```
list:  [A, B, C]
        ^ index 0  -> call A
```
```
list:  [A, B, C]
           ^ index 1  -> call B  ...B removes itself
list:  [A, C]          (C slid from position 2 to position 1)
```
```
        index moves to 2 -> past the end -> LOOP ENDS
```

**C never got the message.** No exception. No log line. Just a lost message.

## The Fix Is One Line

Walk a **snapshot** — a frozen copy — instead of the live list:

```python
for handler in tuple(self.topics[topic]):    # a copy; nothing can change it
    handler(message)
```

Now B's removal lands on the *real* list, which the loop isn't looking at. The loop finishes over the membership that existed when the publish started.

```
snapshot: (A, B, C)      <- frozen, walked to the end
live:     [A, C]         <- B's removal applied here, effective next publish
```

**The contract this gives you**, and it's worth saying out loud in an interview:

> Everyone subscribed when `publish` started receives the message. Anyone who unsubscribes mid-publish is removed from the *next* one. Anyone who subscribes mid-publish starts from the *next* one.

That's clean, explainable, and exactly what the requirement asks for.

## An Analogy First: The Roll Call

You're calling a register of thirty names.

**The wrong way:** read from the *live* attendance list while people are still adding and removing their own names. Someone crosses out their name, everyone below shifts up a line, and your finger — which was holding a line number — is now pointing one person too far down. You skip someone entirely and never notice.

**The right way:** photocopy the list first, then call from the photocopy. People can scribble on the original all they like. You'll read every name that was there when you started, and their edits apply to tomorrow's roll call.

The photocopy is the snapshot. That's it.

## The Second Bug: Never Hold a Lock Across Someone Else's Code

The naive implementation also wraps `publish` in a lock:

```python
def publish(self, topic, message):
    with self.lock:                       # locked...
        for _, handler in self.topics.get(topic, []):
            handler(message)              # ...while running arbitrary user code
```

Two things go wrong:

**1. Instant deadlock on re-entry.** A handler that calls `bus.publish(...)` or `bus.subscribe(...)` tries to take a lock its own thread already holds. A plain `Lock` isn't reentrant, so it waits forever — for itself.

Handlers doing this is completely normal: "when an order arrives, publish a shipment event."

**2. The whole bus serialises behind the slowest listener.** One handler doing a 500 ms network call blocks every publish on every topic.

### The fix: read under the lock, act outside it

```python
def publish(self, topic, message):
    with self.lock:
        subs = self._topics.get(topic, ())   # just grab the snapshot
    # lock released HERE
    for _, handler in subs:
        handler(message)                     # user code runs lock-free
```

The lock now protects one dictionary read. Handlers can re-enter the bus freely.

> This is the same rule as the [Connection Pool](../4.%20Connection_Pool/README.md) problem: **never hold a lock while doing slow or unknown work.**

## Copy-on-Write: Where the Snapshot Comes From for Free

You can copy the list on every publish (`tuple(...)` each time), but there's a slicker arrangement:

**Store the list as a tuple, and make every *write* build a new one.**

```python
# subscribe: don't append - REPLACE
self._topics[topic] = current + ((token, handler),)

# unsubscribe: don't remove - REPLACE
self._topics[topic] = tuple(s for s in current if s[0] != token)
```

Since a tuple is immutable, a publisher that grabbed a reference to it holds a permanently stable view. **The snapshot is free on the read side** — no copying at publish time at all.

This is exactly what Java's `CopyOnWriteArrayList` does internally, and why the official answer reaches for it.

### The trade-off — and it's a real one

| | Read (publish) | Write (subscribe/unsubscribe) |
|---|---|---|
| Copy-on-write | free | **O(n)** — rebuild the whole tuple |
| Mutable list | needs a copy | O(1) append |

Copy-on-write puts **all** the cost on the rare operation and **none** on the common one. For a pub/sub bus — thousands of publishes, occasional subscription changes — that's the right bet.

But it's a bet you can lose. The notebook benchmark makes the cost visible: subscribing and then unsubscribing *n* handlers is **quadratic**, because each of the n changes copies an n-element tuple.

| Subscribers | Copy-on-write churn | Naive list churn |
|---|---|---|
| 250 | 2.9 ms | 0.5 ms |
| 500 | 9.2 ms (3.2×) | 1.1 ms (2.0×) |
| 1,000 | 34.3 ms (3.7×) | 2.2 ms (2.1×) |
| 2,000 | 131.9 ms (3.9×) | 4.5 ms (2.1×) |

Roughly **4× per doubling** — textbook quadratic. With thousands of subscribers and constant churn you'd switch to a reader-writer lock over a mutable list.

**But note:** you'd still have to copy the list inside the read lock before calling handlers. The snapshot requirement never goes away — only *who pays for it* changes.

## Designing the Token

`subscribe` returns a token; `unsubscribe` takes it. What should it be?

- ❌ **The topic name.** Two subscriptions to `"orders"` get the same token. Which one do you remove?
- ❌ **The handler function.** Which topic is it on? And the same function can be subscribed twice.
- ✅ **A unique id for *this subscription*** — plus a `token -> topic` index so removal is O(1) instead of scanning every topic.

The token should be **opaque**: the caller just holds it and hands it back. That freedom is what lets you change the internals later.

## Step-by-Step Example (Narrated)

Topic `race` has three handlers. `h2` unsubscribes `h3` when it runs.

```
_topics = {"race": (h1, h2, h3)}
_index  = {tok1: "race", tok2: "race", tok3: "race"}
```

---

**`publish("race", "m")`**

Take the lock, read `_topics["race"]` → the tuple `(h1, h2, h3)`. **Release the lock.**

---

**Call `h1`** → records `"h1"`. Nothing changes.

---

**Call `h2`** → records `"h2"`, then calls `unsubscribe(tok3)`.

That takes the lock and **replaces** the tuple:

```
_topics = {"race": (h1, h2)}       <- a NEW tuple
```

But our loop is walking the **old** tuple `(h1, h2, h3)`, which still exists and hasn't changed a byte.

---

**Call `h3`** → records `"h3"`. ✅

Result: `["h1", "h2", "h3"]` — every subscriber present at the start was reached.

---

**`publish("race", "m")` again**

Reads the *current* tuple: `(h1, h2)`.

Result: `["h1", "h2"]` — the removal took effect from this publish onward, exactly as promised.

## What About a Handler That Crashes?

A handler is user code, so it will eventually raise. In the plain implementation, an exception from the **first** handler escapes `publish` — and subscribers 2 through n never get the message. One person's bug silences everyone.

Almost always the right policy for a *broadcast* is **catch, record, continue**:

```python
for token, handler in subs:
    try:
        handler(message)
    except Exception as exc:
        errors.append((token, exc))    # record which one failed, keep going
return errors
```

The three defensible policies:

| Policy | When it fits |
|---|---|
| Catch and continue | Broadcast — delivery to the others matters more |
| Propagate | The publisher genuinely needs every handler to succeed |
| Catch and unsubscribe | A handler that keeps failing is poisoning the topic |

Pick one deliberately and say why. The one universally wrong answer is **swallowing the errors silently** — always return or log them.

## The Follow-Up: Durable Subscriptions

*"What if a subscriber goes offline and wants the messages it missed?"*

The bus so far is **fire-and-forget**: not subscribed at publish time means gone forever.

Two ideas fix it:

**1. A log with sequence numbers, and a cursor per subscriber.**

```
log["news"] = [(0,"n0"), (1,"n1"), (2,"n2"), (3,"n3")]
cursor[tok] = 1            # this subscriber last saw sequence 1
```

Reconnecting means "replay everything after my cursor" → `n2`, `n3`.

This is exactly Kafka's consumer-offset model, and MongoDB change streams' resume token.

**2. A ring buffer, to bound memory.**

You can't keep every message forever. Keep only the last N:

```python
deque(maxlen=100)      # a ring buffer in one line - old entries evict automatically
```

Now memory is **O(topics × capacity)**, independent of how long the bus has been running.

### The honest consequence

A subscriber offline long enough for its cursor to fall off the end of the buffer **cannot be caught up**. Those messages are gone.

That's not a bug — it's the price of bounded memory, and every real system has it (Kafka's `OFFSET_OUT_OF_RANGE`, MongoDB's "resume token no longer in the oplog").

What matters is that you **detect the gap and say so**. Silently resuming from wherever the buffer happens to start, pretending nothing was lost, is the bad implementation.

## Common Mistakes

- **Iterating the live list.** The bug the whole question is built around. Silently drops messages in Python.
- **Holding the lock while calling handlers.** Deadlocks on re-entry; serialises the bus behind the slowest listener.
- **A token that doesn't identify one subscription.** Topic name or handler reference are both ambiguous.
- **Leaving empty topics in the map.** A long-running bus with churn leaks memory. Delete the key when the last subscriber leaves.
- **Letting one handler's exception kill the broadcast.** Decide the policy; don't back into it.
- **Assuming publishing to an unknown topic is an error.** The spec says no-op. `dict.get(topic, ())` handles it in one call — and it must not *create* the topic as a side effect.
- **Reasoning about concurrency instead of testing it.** The mid-publish unsubscribe, the re-entrant handler, the deadlock — all three pass a code review and fail a test.

## The Takeaway

> Never walk a collection that the code inside the loop can change — **take a snapshot**. And never hold a lock while running code you don't control — **read under the lock, act outside it**.

Both rules come from the same place: the moment your loop calls something you didn't write, you've lost control of what happens to your data structures mid-iteration. Freeze what you're iterating, and get out of the lock before you hand over control.
