# Broadcast Message Bus

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Concurrency, Hash Tables · **Difficulty/Frequency:** Common (5/10)

---

## Problem Statement

Implement a simple in-process `MessageBus` supporting publish/subscribe semantics, similar to change stream notifications in MongoDB.

```java
class MessageBus {
    // Subscribe to a topic; handler is called for each published message.
    public String subscribe(String topic, Consumer<String> handler) {}

    // Publish a message to all current subscribers of the topic.
    public void publish(String topic, String message) {}

    // Unsubscribe using the token returned by subscribe.
    public void unsubscribe(String subscriptionToken) {}
}
```

**Requirements:**

- Multiple subscribers on the same topic each receive every message.
- **Unsubscribing during a publish must not cause exceptions or missed deliveries to other subscribers.**
- The bus must be thread-safe.
- Publishing to a topic with no subscribers is a no-op.

### Follow-up (as posed with the problem)

How would you add support for **durable subscriptions** where a subscriber can reconnect and receive messages it missed while offline? What data structure would you use to bound memory?

---

## Study Tools

### Hint 1

The tricky part is not the happy path — it's what happens when a handler calls `unsubscribe` while you're mid-iteration over the subscriber list. Think about which thread owns the data structure and what copy semantics buy you.

### Hint 2

You need a way to snapshot the subscriber list at the start of each publish so the iteration is isolated from concurrent structural changes. Consider whether the token should carry the topic or just the handler reference.

### Hint 3

Use a `ConcurrentHashMap<String, CopyOnWriteArrayList<Subscription>>` keyed by topic. `publish` grabs the list reference and iterates it directly — the snapshot is built into the collection type, and a concurrent `unsubscribe` only affects future iterations.

---

### Answer

This is a snapshot-iteration problem wrapped in a thread-safe map. The core idea is that `publish` iterates over an immutable view of the subscriber list, so a concurrent `unsubscribe` (which mutates the live list) can't corrupt the iteration or cause a `ConcurrentModificationException`.

The cleanest fit in Java is `ConcurrentHashMap<String, CopyOnWriteArrayList<Subscription>>`. `CopyOnWriteArrayList` gives you snapshot iteration on every read (which is exactly what `publish` does), and `ConcurrentHashMap` handles the topic-to-list mapping without locking the whole bus. The subscription token needs to carry both the topic and the handler so `unsubscribe` can find the right list and remove the right entry.

```java
import java.util.concurrent.*;
import java.util.function.Consumer;

class MessageBus {
    private static class Subscription {
        final String topic;
        final Consumer<String> handler;

        Subscription(String topic, Consumer<String> handler) {
            this.topic = topic;
            this.handler = handler;
        }
    }

    private final ConcurrentHashMap<String, CopyOnWriteArrayList<Subscription>> topics =
        new ConcurrentHashMap<>();

    public String subscribe(String topic, Consumer<String> handler) {
        Subscription sub = new Subscription(topic, handler);
        topics.computeIfAbsent(topic, t -> new CopyOnWriteArrayList<>()).add(sub);
        // Use identity-based token; a UUID also works but identity is simpler.
        return Integer.toHexString(System.identityHashCode(sub));
    }

    public void publish(String topic, String message) {
        CopyOnWriteArrayList<Subscription> subs = topics.get(topic);
        if (subs == null) {
            return;   // no-op for topics with no subscribers
        }
        for (Subscription sub : subs) {
            sub.handler.accept(message);
        }
    }

    public void unsubscribe(String subscriptionToken) {
        // We can't reverse an identity hash to the Subscription object,
        // so we need to scan. For a small number of topics this is fine;
        // for production, use a UUID -> Subscription map instead.
        for (CopyOnWriteArrayList<Subscription> subs : topics.values()) {
            for (Subscription sub : subs) {
                if (Integer.toHexString(System.identityHashCode(sub)).equals(subscriptionToken)) {
                    subs.remove(sub);
                    // Clean up empty topic lists to avoid unbounded map growth.
                    if (subs.isEmpty()) {
                        topics.remove(sub.topic, subs);
                    }
                    return;
                }
            }
        }
    }
}
```

**Time:** O(1) amortized for `subscribe`, O(n) for `publish` where n is the number of subscribers on that topic, O(m) for `unsubscribe` where m is the total number of subscriptions across all topics (or O(1) if you maintain a token-to-subscription index).

**Space:** O(s) where s is the total number of active subscriptions, plus O(n) per publish call for the copy-on-write snapshot (amortized over the list's lifetime).

**Correctness argument:** The invariant is that `topics.get(topic)` returns a list reference that is never mutated in place. `CopyOnWriteArrayList.add` and `remove` replace the underlying array with a new one, so any iterator created before the mutation continues to see the old array. This means `publish` iterates over a consistent snapshot: every subscriber that was present when `publish` started will receive the message, and no subscriber added mid-publish will receive it for that call. A concurrent `unsubscribe` during `publish` mutates a different array (the new copy), so the iteration is unaffected. Thread safety of `subscribe`/`unsubscribe` against each other is handled by `ConcurrentHashMap`'s per-key locking and `CopyOnWriteArrayList`'s internal synchronization.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive version: a `HashMap<String, List<Consumer<String>>>` with synchronized methods. It's correct for the happy path, but it fails requirement 2 — if a handler calls `unsubscribe` while you're iterating the list in `publish`, you get a `ConcurrentModificationException` (or worse, you skip a subscriber). It also serializes all publishes across all topics, which is a throughput bottleneck.

The first fix most people reach for is iterating over a copy: `for (Consumer<String> h : new ArrayList<>(list))`. That solves the concurrent-modification problem, but you still need to synchronize the copy operation itself, and you're paying O(n) allocation on every publish even when nothing changed. The insight is that `CopyOnWriteArrayList` already does this — it snapshots on *write*, not on read, so iteration is lock-free and allocation-free. You pay the copy cost only when the subscriber list actually changes, which is rare relative to publishes.

For the topic map, `ConcurrentHashMap` is the natural choice: `computeIfAbsent` handles the first-subscriber race without external locking, and `get` is lock-free for the common publish path.

The token design is the part that trips people up. If the token is just the topic name, you can't distinguish between two subscriptions to the same topic. If it's just the handler, you can't find which topic to remove from. You need a token that identifies the specific subscription. A UUID stored in a `Subscription` object and a parallel `Map<String, Subscription>` index gives you O(1) unsubscribe. The identity-hash approach shown above is simpler but requires a scan; mention the tradeoff.

Finally, think about what happens when the last subscriber unsubscribes. If you leave empty lists in the map, you leak memory. The `topics.remove(topic, subs)` call is a conditional remove that only succeeds if the list is still the one mapped to that topic, which handles a race where a new subscriber was added between your `isEmpty()` check and the remove.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Explain why `CopyOnWriteArrayList` is the right tool, not just that it's thread-safe** — the interviewer wants to hear that you understand snapshot iteration semantics: reads are lock-free and see a consistent view, writes are expensive but rare. That's the exact tradeoff for a pub/sub bus where publishes vastly outnumber subscribes/unsubscribes.
- **Talk through the unsubscribe-during-publish race explicitly** — walk through the interleaving: thread A is iterating the old array, thread B calls `remove` which creates a new array, thread A continues on the old array. No exception, no missed delivery to other subscribers. Showing you can reason about the interleaving is worth more than the code.
- **Design the token carefully** — a token that's just the topic name breaks when you have two subscriptions to the same topic; a token that's just the handler breaks when you need to find the topic. The token must identify the *subscription* itself. Mention the UUID + index map tradeoff vs. the scan approach.
- **Handle the empty-topic cleanup** — if you never remove empty lists, a long-running bus with churn leaks memory. The conditional `remove(topic, subs)` is a subtle detail that shows you've thought about races in the cleanup path itself.
- **State the complexity of each operation and justify it** — `publish` is O(n) in subscribers *on that topic*, not O(total subscribers), because the map lookup is O(1). `unsubscribe` is O(1) with an index or O(total) with a scan. Being precise about which n you mean separates a solid answer from a great one.
- **Mention the limitation of copy-on-write** — if a topic has thousands of subscribers and high subscribe/unsubscribe churn, the copy cost on every mutation becomes a problem. Acknowledging when you'd switch to a `ReadWriteLock`-guarded `ArrayList` or a lock-free linked list shows you understand the tradeoff space.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you add durable subscriptions where a subscriber can reconnect and receive messages it missed while offline?** — Think about a per-subscription offset or cursor into a per-topic log; the subscriber resumes from its last acknowledged position.
- **What data structure would you use to bound memory for durable subscriptions?** — A ring buffer or a log with retention limits; consider what happens when a slow subscriber falls behind the retention window.
- **How would you handle a handler that throws an exception during publish?** — Decide whether to catch and continue, catch and log, or propagate; consider whether one bad handler should block delivery to others.
- **How would you support wildcard or pattern-based topic subscriptions?** — Think about topic hierarchies (`orders.created`, `orders.updated`) and a trie or prefix tree for matching.
- **What changes if the bus needs to be distributed across multiple processes?** — You need a network protocol, serialization, and a broker or gossip-based routing layer; the in-process concurrency primitives no longer apply.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Language note:** the official answer is written in Java. The accompanying notebook implements the same design in Python — a `threading.Lock`-guarded topic map plus explicit tuple snapshots in place of `CopyOnWriteArrayList` — so every claim is exercised by real threads; the Java reference above is reproduced unchanged.
