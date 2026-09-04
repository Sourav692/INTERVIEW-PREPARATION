# Design a Chat Application Like WhatsApp

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** System Design · **Tags:** Onsite Loop, Caching, Concurrency, Databases, Distributed Systems, Networking · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Design a chat application like WhatsApp.

**Requirements:**

- One-on-one and group messaging
- Online/offline presence indicators
- Message delivery and read receipts
- Media sharing (images, videos, documents)
- End-to-end encryption
- Push notifications
- Message history sync across multiple devices

**Functional Requirements:**

- Users can register and authenticate
- Users can send text messages, images, videos, and files
- Users can create and manage group chats
- Users can see message status (sent, delivered, read)
- Users can see presence status of their contacts
- Users can search message history

**Non-Functional Requirements:**

- Low latency message delivery (< 500ms)
- High availability (99.99% uptime)
- Scalability to support hundreds of millions of users
- Durability — no message loss
- Security and privacy — end-to-end encryption

**Design Considerations:**

- System architecture (client-server vs peer-to-peer)
- Data model for messages, conversations, users
- Message delivery mechanism (push vs pull, long polling, WebSockets)
- Storage and replication strategy
- Handling offline users
- Media storage and delivery
- Encryption key management

**Estimate scale:**

- 500M daily active users
- Average 50 messages per user per day
- Peak concurrent connections
- Storage requirements for messages and media

---

## Study Tools

### Hint 1

Think about how to separate the **control plane** (connection management, presence, message routing) from the **data plane** (persistent storage, media blobs). Long-lived connections are essential for low latency, but you don't want them tied directly to your primary database.

### Hint 2

Model conversations as a **fan-out** problem: for a group with k members, a single message write can fan out to k inboxes. Decide whether you fan out on write or fan out on read, and what that means for storage amplification versus read latency.

### Hint 3

Focus on the message delivery pipeline: a sender posts to a message queue, the queue fans out to per-user connection nodes, those nodes push via WebSocket if the recipient is online and store to an inbox table if offline. For encryption, keep private keys only on client devices and have the server relay ciphertext blobs it cannot decrypt.

---

### Answer

This is a client-server architecture built around a message queue for fan-out, per-user inbox tables for offline storage, and a separate media service with client-side encryption. The core idea is that the server acts as a **dumb relay for encrypted payloads** while maintaining enough metadata to route messages, track delivery status, and sync history across devices.

#### High-Level Architecture

Three main client-facing components:

- **Gateway Service:** terminates WebSocket/TCP connections from all clients. It authenticates the connection, tracks which user is connected to which gateway node, and forwards messages to and from the connection layer.
- **Chat Service:** handles the business logic for sending messages, creating groups, fetching history, and updating message status. It's a stateless HTTP/WebSocket service.
- **Media Service:** handles upload and download of images, videos, and documents. Clients upload encrypted blobs and receive a media ID that gets embedded in the message payload.

Behind these sit:

- **Message Queue** (e.g., Kafka or a custom pub/sub): the fan-out backbone. When a message is sent, the Chat Service publishes it to a topic. A consumer group fans out to per-user inboxes.
- **User Inbox Table:** one row per `(user_id, message_id)` pair, or per `(user_id, conversation_id, message_id)` for group chats. This is the source of truth for message history and offline delivery.
- **Presence Service:** an in-memory or Redis-backed service tracking online/offline status and last seen timestamps.
- **Object Storage** (e.g., S3): stores encrypted media blobs.

#### Data Model

```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE,
    display_name VARCHAR(100),
    public_key TEXT,                -- public identity key for E2E encryption
    created_at TIMESTAMP
);

CREATE TABLE conversations (
    conversation_id BIGINT PRIMARY KEY,
    type ENUM('one_on_one', 'group'),
    group_name VARCHAR(100),        -- NULL for one-on-one
    created_at TIMESTAMP
);

CREATE TABLE conversation_members (
    conversation_id BIGINT,
    user_id BIGINT,
    joined_at TIMESTAMP,
    last_read_message_id BIGINT DEFAULT 0,
    PRIMARY KEY (conversation_id, user_id)
);

CREATE TABLE messages (
    message_id BIGINT PRIMARY KEY,
    conversation_id BIGINT,
    sender_id BIGINT,
    message_type ENUM('text', 'image', 'video', 'file'),
    content TEXT,                   -- for text messages; for media, a JSON with media_id
    media_id BIGINT,                -- FK to media table, NULL for text
    created_at TIMESTAMP,
    INDEX idx_conversation_time (conversation_id, message_id)
);

CREATE TABLE inbox (
    user_id BIGINT,
    message_id BIGINT,
    conversation_id BIGINT,
    status ENUM('delivered', 'read'),
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    PRIMARY KEY (user_id, message_id)
);

CREATE TABLE media (
    media_id BIGINT PRIMARY KEY,
    uploader_id BIGINT,
    media_type ENUM('image', 'video', 'file'),
    object_key VARCHAR(255),        -- S3 key
    size_bytes BIGINT,
    encryption_key_id BIGINT,       -- reference to the key used
    created_at TIMESTAMP
);
```

The `inbox` table is the key to fan-out. For a one-on-one message, we write two rows: one for the sender (status = `'read'` immediately) and one for the recipient (`'delivered'` when pushed, `'read'` when they read it). For a group with k members, we write k rows. **This is fan-out on write.**

We shard `inbox` by `user_id` so each user's inbox lives on a single shard. `messages` is sharded by `conversation_id`.

#### Message Delivery Pipeline

1. **Sender sends message:** The client encrypts the message with the recipient's public key (or the group key for group chats), then sends the ciphertext to the Chat Service over WebSocket.
2. **Chat Service persists:** Writes the message to the `messages` table, then writes k rows to the `inbox` table (one per recipient, including the sender).
3. **Fan-out:** Publishes a `MessageCreated` event to the message queue with the message ID and recipient list.
4. **Delivery workers:** A consumer picks up the event. For each recipient, it checks the Presence Service. If online, it routes the message to the recipient's Gateway node, which pushes it over the WebSocket. If offline, it does nothing (the message is already in the inbox; the recipient will fetch it on reconnect).
5. **Delivery receipt:** When the recipient's client receives the push, it sends an ACK. The Gateway updates the inbox row status to `'delivered'` and notifies the sender's client.
6. **Read receipt:** When the recipient opens the conversation, the client sends a `ReadReceipt` message. The Chat Service updates the inbox row status to `'read'` and pushes the read receipt to the sender.

For offline users, the message sits in the inbox table. When the user reconnects, the client sends a `SyncRequest` with the last message ID it has. The Chat Service fetches all inbox rows with `message_id > last_message_id`, orders them by conversation, and returns them in batches.

#### Presence Service

Presence is tracked in Redis with a TTL. Each Gateway node maintains a heartbeat from connected clients (every 30 seconds). The Presence Service stores:

- `online:{user_id}` → set of device IDs currently connected
- `last_seen:{user_id}` → timestamp of last disconnect

When a user connects, the Gateway writes to `online:{user_id}` and publishes a `PresenceChanged` event. Contacts subscribed to that user's presence get a push notification. When the last device disconnects, the key expires (or is explicitly deleted), and `last_seen` is updated.

Presence is **eventually consistent**. A user may see a contact as online for up to 30-60 seconds after they actually disconnected. That's acceptable for this use case.

#### Media Sharing

Media files are too large to push through the message queue. The flow:

1. Client generates a random symmetric key for the media file.
2. Client encrypts the media with that key, uploads the ciphertext to the Media Service.
3. Media Service stores the blob in S3, creates a `media` row, returns the `media_id`.
4. Client sends a message with `message_type = 'image'` and `content = {media_id, encryption_key_encrypted_for_recipient}`.
5. Recipient's client downloads the blob from the Media Service, decrypts it with the key from the message payload.

The media key is encrypted with the recipient's public key (or the group key) and included in the message payload, so the server never sees the plaintext media.

#### End-to-End Encryption

E2E encryption uses the Signal protocol (or an equivalent). Key points:

- Each user has a long-term identity key pair. The public key is stored in the `users` table.
- For one-on-one chats, clients establish a shared secret via **X3DH** (extended triple Diffie-Hellman) and derive a chain of message keys via the **Double Ratchet** algorithm.
- For group chats, we use a **sender-key** scheme: each group member generates a sender key and shares it with other members. When a member sends a message, they encrypt with their sender key. This avoids O(k) encryption per message.
- The server only ever sees ciphertext and the metadata needed for routing (sender, recipient, message ID, timestamp).
- When a user gets a new device, they need to re-establish sessions. The server stores encrypted key material in a key backup service, but only the client can decrypt it.

#### Push Notifications

For mobile clients, WebSocket connections are unreliable (OS kills background apps). We need a push notification fallback:

- When a message is fanned out and the recipient is offline (or the WebSocket is dead), the delivery worker sends a push notification via APNs (iOS) or FCM (Android).
- The push payload contains a minimal hint ("New message from Alice") but no message content, preserving E2E encryption.
- The client wakes up on the push, reconnects the WebSocket, and fetches the actual message from the inbox.

#### Multi-Device Sync

Each user can have multiple devices. Each device has its own WebSocket connection to a Gateway node.

- The Presence Service tracks `online:{user_id}` as a set of device IDs.
- When a message is fanned out, it's pushed to all connected devices of the recipient.
- Each device tracks its own `last_read_message_id` in local storage. The inbox table's status field is per-user, not per-device, so we need a separate `device_sync` table if we want per-device read receipts.
- For simplicity, we can say read receipts are per-user: if any device reads the message, it's marked read for the user. This is what WhatsApp does by default.

#### Capacity Estimation

**Message volume:** 500M DAU × 50 messages/day = 25B messages/day. Average rate: 25B / 86400 ≈ **289,000 messages/sec**. Peak is typically 3-5x average, so **~1M messages/sec at peak**.

**Concurrent connections:** Not all 500M DAU are online simultaneously. Peak concurrent users might be 10-15% of DAU, so **50-75M concurrent connections**. Each Gateway node can handle ~100K WebSocket connections (with a decent server, ~1M if optimized). So we need **~500-750 Gateway nodes**.

**Storage for messages:** Average text message is maybe 100 bytes of ciphertext + 100 bytes of metadata. With fan-out, the inbox table multiplies this. For a one-on-one message, 2 inbox rows. For a group of 10, 10 inbox rows. Average group size is maybe 4-5, so average fan-out factor is ~4. Total inbox rows: 25B × 4 = 100B rows/day. Each row is ~200 bytes. That's 100B × 200 bytes = **20 TB/day for inbox**. The messages table adds 25B × 200 bytes = 5 TB/day. Text message storage is **~25 TB/day, ~9 PB/year**.

**Storage for media:** Assume 10% of messages are media. Average media size: images ~200 KB, videos ~2 MB, files ~500 KB. Weighted average maybe ~500 KB. 2.5B media messages/day × 500 KB = **1.25 PB/day**. This dwarfs text storage. Yearly: **~450 PB**. This is why media goes to object storage with a CDN.

**Bandwidth:** 1.25 PB/day for media = 1.25 × 10^15 bytes / 86400 sec ≈ **14.5 GB/s** of media upload bandwidth. This needs a CDN for download; uploads go directly to the Media Service.

#### Failure Modes and Consistency

- **Message loss:** The inbox write must be durable before we publish to the queue. Use synchronous replication (or at least quorum writes) on the inbox shard.
- **Duplicate delivery:** If a Gateway pushes a message but the ACK is lost, the message might be delivered twice. Clients use `message_id` for idempotency.
- **Out-of-order delivery:** Multiple Gateway nodes might push messages out of order. Clients sort by `message_id` (which is monotonically increasing per conversation).
- **Gateway node failure:** If a Gateway node crashes, its connected clients reconnect to another node. The Presence Service detects the disconnect (heartbeat timeout) and updates presence. Messages sent during the gap are fetched on reconnect via the sync mechanism.
- **Queue backlog:** If the delivery workers fall behind, latency increases. We monitor queue depth and scale consumers dynamically.

This design meets the requirements: <500ms latency (WebSocket push, no polling), 99.99% availability (stateless services, replicated storage, multi-region), and no message loss (durable inbox writes before fan-out).

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the simplest thing that works: a single server with a database. Client A sends a message to the server, the server stores it in a `messages` table, and Client B polls the server every few seconds for new messages. This works for a toy system, but polling is slow (average latency is half the polling interval) and wasteful.

The first improvement is to replace polling with long-lived connections. WebSockets are the natural choice. Client A sends a message over WebSocket, the server looks up which server node Client B is connected to, and forwards the message. Now we have a routing problem: how does the server know where Client B is connected? We introduce a **Presence Service** that maps `user_id` to `gateway_node_id`. This is a simple Redis lookup.

Now we have a single point of failure: the database. If the server crashes before storing the message, it's lost. So we write the message to a durable store before acknowledging the sender. The `messages` table is the source of truth.

Next, we need to handle offline users. If Client B is offline, the message can't be forwarded. We need an **inbox table**: one row per (user, message). When a message is sent, we write a row for each recipient. When a user comes online, they fetch all rows with `message_id > last_seen_message_id`. This is the **fan-out on write** pattern.

The bottleneck now is the fan-out itself. For a group with 1000 members, writing 1000 inbox rows synchronously is slow. We decouple the write from the fan-out using a **message queue**. The sender's write to the `messages` table is synchronous and fast. The fan-out to inboxes happens asynchronously by workers consuming from the queue. This means a message might not be in the recipient's inbox for a few hundred milliseconds after the sender gets an ACK. That's acceptable — the sender's ACK means "the server has durably stored your message," not "the recipient has it."

For media, we realize that pushing a 2 MB video through WebSocket and the inbox table is wasteful. We extract a **Media Service**. The client uploads the media to object storage, gets back a media ID, and sends a message containing that ID. The recipient downloads the media separately. This keeps the message pipeline lightweight.

The final piece is encryption. We can't do E2E encryption if the server stores plaintext. The client encrypts before sending, and the server treats the message payload as an opaque blob. The server still needs metadata (sender, recipient, message ID, timestamp) for routing and sync, but the content is ciphertext. Key management is the hard part: we use the Signal protocol's Double Ratchet for one-on-one chats and sender keys for groups.

Now we have a design that scales: stateless Gateway nodes behind a load balancer, a sharded inbox table, a message queue for fan-out, and object storage for media. The remaining details are operational: monitoring queue depth, handling Gateway node failures, and tuning the number of delivery workers.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Fan-out on write vs. fan-out on read** — you should articulate the tradeoff explicitly: fan-out on write costs more storage and write amplification (O(k) inbox rows per message), but gives O(1) reads for history sync. Fan-out on read costs O(k) reads when fetching a group conversation, but saves storage. WhatsApp uses fan-out on write because users read their inbox far more often than they send messages.
- **Durability before fan-out** — the sender's ACK must mean the message is durably stored, not just accepted. If you acknowledge before the `messages` table write is replicated, a crash loses the message. State this explicitly: the write to `messages` is synchronous and replicated before the sender sees the sent receipt.
- **The exact delivery pipeline** — walk through the sequence: encrypt → send → persist to `messages` → publish to queue → fan-out workers → check presence → push via WebSocket or store in inbox → ACK → update status → notify sender. Interviewers listen for whether you understand that delivery and read receipts are separate events.
- **Why the server can't decrypt** — you should explain that the server only sees ciphertext and routing metadata. The encryption keys live on client devices. This means the server can't do server-side search of message content, which is a real limitation you should acknowledge.
- **Presence is eventually consistent** — don't claim you can have perfectly accurate presence. Heartbeats are periodic (30s), network partitions happen, and mobile OSes kill background connections. Say that presence is best-effort with a bounded staleness window, and explain why that's acceptable.
- **Multi-device sync is a hard problem** — each device needs its own connection and its own view of read state. You should discuss whether read receipts are per-user or per-device, and how a new device syncs history without the server being able to decrypt it. This shows you understand the security implications of sync.
- **Media dominates storage** — do the math out loud: text messages are ~25 TB/day, but media at 500 KB average is ~1.25 PB/day. That's a 50x difference. This is why media goes to object storage with a CDN, while text messages live in a sharded database.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you handle a group with 100,000 members?** — Think about whether fan-out on write still works, and what changes when the fan-out factor is very large.
- **How do you handle message ordering when a user has multiple devices and connects from different network paths?** — Consider per-conversation sequence numbers and client-side sorting.
- **How would you implement message search if the server can't decrypt message content?** — Think about client-side indexing, or a tradeoff where some metadata is searchable.
- **What happens when a user's phone is lost and they get a new device? How do they recover their message history?** — Consider encrypted backups and key recovery.
- **How would you handle spam and abuse in a system where the server can't read message content?** — Think about rate limiting, reputation systems, and metadata-based detection.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ One arithmetic correction

The answer's own numbers do not multiply out consistently for text storage.

It computes inbox at **20 TB/day** and the messages table at **5 TB/day**, then states the total as *"~25 TB/day, ~9 PB/year."* But 25 TB/day × 365 = **9.1 PB/year**, which is right — while the **inbox row estimate itself is the shaky part**: 25B messages × fan-out 4 = 100B rows, and at 200 bytes that is 20 TB/day, so the total is dominated by fan-out, not by the message bodies.

The larger point the answer makes correctly, and which the notebook verifies: **media is ~50× text**. 1.25 PB/day versus 25 TB/day. Every storage decision follows from that ratio, so it is the number worth getting right.

The notebook recomputes all of these from the stated assumptions and pins them with assertions, so you can change the fan-out factor or the media share and watch the conclusion move.
