# Connection Pool

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** Coding · **Tags:** Live Screen, Onsite Loop, Concurrency, OOP & Design Patterns · **Difficulty/Frequency:** Very Common (7/10)

---

## Problem Statement

Implement a `ConnectionPool` class with reusable connections.

Each request to get a connection should take one from the pool or create a new one if the pool is empty. The pool must be **thread-safe**.

```java
class Connection {
    public Connection() {}

    // Must be called once before any read/write calls.
    // This is an expensive operation.
    public void open() {}

    public String read() {
        return null;
    }

    public void write(String data) {}

    // After close is called, read/write may not be called.
    public void close() {}
}
```

**Where can you put the lock for better efficiency?** Note that opening a connection is an expensive operation.

---

## Study Tools

### Hint 1

The expensive part is `open()`, so you want to avoid holding any lock while a connection is being opened. Think about which state transitions actually need mutual exclusion.

### Hint 2

Keep a stack or deque of available connections guarded by a lock, but move the `open()` call outside the critical section. A semaphore or a size counter can track how many connections are checked out.

### Hint 3

Use a `Semaphore` initialized to the pool size for checkout accounting, and synchronize only the available-stack operations. When the stack is empty and the semaphore has permits, release the lock, construct and open the connection, then reacquire to push it.

---

### Answer

This is a thread-safe object pool with lazy connection creation. The key insight is that `open()` is expensive, so it must happen outside any lock. Use a `Semaphore` to block when the pool is exhausted, and a synchronized stack for the available connections. When a thread needs a connection and the stack is empty, it releases the stack lock, creates and opens a new connection, then acquires the lock again to push it.

```java
import java.util.Stack;
import java.util.concurrent.Semaphore;

public class ConnectionPool {
    private final int maxSize;
    private final Stack<Connection> available = new Stack<>();
    private final Semaphore semaphore;
    private int totalCreated = 0;

    public ConnectionPool(int maxSize) {
        this.maxSize = maxSize;
        this.semaphore = new Semaphore(maxSize, true);
    }

    public Connection getConnection() throws InterruptedException {
        semaphore.acquire();
        Connection conn = null;
        synchronized (available) {
            if (!available.isEmpty()) {
                conn = available.pop();
            }
        }
        if (conn == null) {
            conn = new Connection();
            conn.open();   // expensive, done outside lock
            synchronized (available) {
                totalCreated++;
            }
        }
        return conn;
    }

    public void releaseConnection(Connection conn) {
        if (conn == null) {
            return;
        }
        synchronized (available) {
            available.push(conn);
        }
        semaphore.release();
    }

    public void closeAll() {
        synchronized (available) {
            for (Connection conn : available) {
                conn.close();
            }
            available.clear();
            totalCreated = 0;
        }
    }
}
```

**Time:** O(1) for both `getConnection()` and `releaseConnection()` — the semaphore acquisition is O(1) and the stack operations are O(1).

**Space:** O(n) where n is the maximum pool size — the stack holds at most n connections.

**Correctness argument:** The semaphore guarantees at most `maxSize` connections are checked out at any time. The `available` stack is guarded by a `synchronized` block, so push/pop operations are atomic. The `open()` call happens outside the synchronized block, so other threads can acquire and release connections while one thread is opening a new connection. This prevents the expensive operation from blocking the entire pool.

One subtlety: `totalCreated` is incremented inside a synchronized block but never checked against `maxSize`. In practice, since the semaphore limits concurrent checkouts to `maxSize`, the number of created connections will never exceed `maxSize` because a new connection is only created when a permit is available and no connection is in the stack.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest version: a `synchronized getConnection()` method that checks a stack and creates a connection if empty. That's O(1) but it holds the lock during `open()`, which could take hundreds of milliseconds. Every other thread blocks, even if there are idle connections in the stack.

The first improvement is to move `open()` outside the synchronized block. But now you have a race: two threads could both see an empty stack, both create connections, and you'd exceed the pool size. You need a way to track how many connections are checked out.

A `Semaphore` initialized to `maxSize` solves this cleanly. Each thread must acquire a permit before getting a connection. If all connections are checked out, the semaphore blocks. When a connection is released, the permit is returned. This gives you bounded pool size without holding a lock during `open()`.

The remaining synchronization is just the stack of available connections. A synchronized block around `pop()` and `push()` is sufficient and cheap. The critical section is tiny — just a stack operation — so contention is minimal.

An alternative is to use `ConcurrentLinkedDeque` and a counter, but the semaphore approach is cleaner because it handles the blocking semantics for free.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Lock granularity** — the interviewer is watching whether you understand that holding a lock during I/O or expensive operations is a performance killer. Moving `open()` outside the critical section is the core insight.
- **Semaphore over manual counters** — using `Semaphore` for checkout accounting is cleaner than a manual counter with `wait()`/`notifyAll()`. It handles spurious wakeups and fairness automatically.
- **Fairness parameter** — passing `true` to the `Semaphore` constructor gives FIFO ordering, which prevents starvation. Mention this if the interviewer asks about fairness.
- **Idle connection eviction** — real pools (like HikariCP) evict connections that have been idle too long. You could add a background thread that periodically checks `available` and closes stale connections.
- **Validation on checkout** — a real pool validates connections before handing them out. You could add an `isValid()` check in `getConnection()` and discard broken connections.
- **Exception safety** — if `open()` throws, the semaphore permit must be released. Wrap the creation in a try-catch and release the permit on failure.
- **Double-checked locking pitfall** — if the interviewer asks about double-checked locking for lazy creation, explain why it's broken without `volatile` and why the semaphore approach avoids it entirely.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you handle the case where `open()` throws an exception?** — Think about releasing the semaphore permit in a `finally` block.
- **Add a timeout to `getConnection()` so callers don't block forever.** — Use `semaphore.tryAcquire(timeout, TimeUnit.MILLISECONDS)`.
- **How would you implement idle connection eviction?** — A background thread that periodically checks `available` and closes connections idle for more than a threshold.
- **What if connections become stale (e.g., the server closed them)?** — Add a validation check before returning a connection, and discard broken ones.
- **How would you make this pool support dynamic resizing?** — The semaphore has a fixed size; you'd need to replace it with a custom counter and condition variable.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

**Language note:** the official answer is written in Java. The accompanying notebook implements the same design in Python (`threading.Semaphore` / `threading.Lock` in place of `Semaphore` / `synchronized`) so every claim is executable and testable under real threads; the Java reference above is reproduced unchanged.
