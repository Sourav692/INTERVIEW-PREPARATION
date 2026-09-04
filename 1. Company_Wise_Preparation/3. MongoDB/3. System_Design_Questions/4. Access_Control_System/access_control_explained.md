# Access Control System — Explained Simply

## The Problem

Millions of users, thousands of resources, and one question asked a million times a second: **"Can this person do this thing?"** Answer in under 10 milliseconds, never wrongly, and keep a log nobody can quietly edit.

## An Analogy First: The Building Pass Office

Picture a large office building.

**The naive version:** every time someone reaches a door, the guard phones the pass office. "Is Alice allowed in the server room?" The office looks up Alice's job title, checks what that title inherits from, cross-references the door list, and phones back. Correct — and hopeless at a thousand doors and ten thousand people.

**The real version:** once a night, the pass office prints **a card for every job title** listing every door that title opens. The guard at each door has a copy of every card. Alice arrives, the guard looks at her badge (`editor`, `contractor`), checks those two cards, and decides in a second. No phone call.

Two things make this work, and both are worth naming:

1. **Job titles change rarely; people walk through doors constantly.** So do the expensive work when the titles change, not when someone walks up.
2. **The cards are a day old.** If Alice was fired this morning, her card still opens doors. That staleness is the price of speed — and whether it's acceptable depends entirely on *why* the permission changed.

That's the entire design: **flatten at write time, serve from memory, and know exactly how stale you are.**

## The Asymmetry That Decides Everything

> Role assignments change a few times a day. Authorization checks happen a million times a second.

Nine orders of magnitude. When your read:write ratio looks like that, you stop optimising reads and start *eliminating* them — pushing every joule of work onto the rare write.

| | Write path | Read path |
|---|---|---|
| Frequency | a few per day | 1,000,000 per second |
| What matters | correctness, durability | latency |
| Where it lives | normalized SQL tables | flat hash maps in RAM |
| Cost tolerated | seconds | microseconds |

## Flattening: The Core Move

Roles form a **DAG** — `admin` inherits `editor` inherits `viewer`. Walking that graph per request is the thing you're trying to avoid.

So walk it once, at snapshot build time, and write down each role's complete effective permissions:

```
Roles (a DAG):                Flattened at build time:

  viewer ──┐                    viewer      : {(q3.pdf, read): allow}
           ├── editor           editor      : {(q3.pdf, read): allow,
  (base)   │                                   (q3.pdf, write): allow}
           └── contractor       contractor  : {(q3.pdf, write): DENY}
```

Now "can Alice write q3.pdf?" is two hash lookups — one per role she holds. No traversal, no inheritance logic, no conflict resolution. **Deny-precedence was already resolved when the card was printed.**

### Why deny must win

If any applicable rule says deny, the answer is deny — regardless of how many allows exist.

This isn't a tiebreak convention, it's a **security property**. A deny you can override by adding an allow somewhere else isn't a deny; it's a suggestion. Same for **default-deny**: no matching rule means no. Absence of permission is never permission.

## Defect 1: The Schema Forbids the Feature

Here's the `permissions` table constraint:

```sql
UNIQUE (tenant_id, resource_id, action)
```

A row is `(resource, action, effect)`. That constraint allows **one row per (tenant, resource, action)** — so `q3.pdf/read` can be an allow **or** a deny. Never both.

Now read the answer's own talking point:

> *"when a user has one role that allows read on a file and another that denies it, the deny must win"*

That's two rows: `(q3.pdf, read, allow)` and `(q3.pdf, read, deny)`. The second `INSERT` fails:

```
AS SPECIFIED: duplicate key ('acme', 'q3.pdf', 'read')
  -> the deny rule cannot be stored. Deny-precedence is unreachable.
```

The fix is one word:

```sql
UNIQUE (tenant_id, resource_id, action, effect)
```

**What makes this worth studying is the failure mode.** The flattening code that resolves deny-precedence is *correct*. It just never receives a conflict, because the database refused to store one. The requirement doesn't break loudly — it silently never fires, and nobody finds out until an auditor asks why a deny rule was never applied.

> Check that your schema can *represent* your requirements. A constraint that quietly makes a security feature unreachable is worse than a bug that crashes.

## Defect 2: "Union the Sets" Is Not O(1)

The check flow says:

> *2. Union the effective permission sets of those roles.*

and then:

> *"This is all hash map lookups — O(1) per check"*

Both can't be true. **A union is O(the total size of the sets.)**

A user with 5 roles holding 10,000 permissions each does 50,000 operations — and allocates a 50,000-entry map — to answer a question about *one* key.

Measured:

| Permissions per role | Union | Probe |
|---|---|---|
| 10 | 10 µs | 0.96 µs |
| 100 | 83 µs | 0.86 µs |
| 1,000 | 815 µs | 1.16 µs |
| 10,000 | **17,647 µs** | **1.45 µs** |

The union grows ~10× for every 10× more permissions. The probe is flat.

And 17.6 ms already blows the 10 ms p99 budget — with one user, on an idle machine.

### You never needed the union

```python
def check(user, resource, action):
    decision = "deny"                       # default-deny
    for role in snapshot.user_roles[user]:  # ~5 roles
        effect = snapshot.role_perms[role].get((resource, action))
        if effect == "deny":
            return "deny"                   # deny wins, short-circuit
        if effect == "allow":
            decision = "allow"
    return decision
```

**O(roles per user)** — about 5 — completely independent of how many permissions each role holds.

At the stated 1M checks/sec:

```
Union:  50,000 ops/check  →  50,000,000,000 ops/sec
Probe:       5 ops/check  →       5,000,000 ops/sec
```

> 50 billion operations per second is not "a handful of hash lookups." 5 million is.

**The general lesson:** don't build a data structure you're about to throw away. The union computes the answer to every possible question in order to answer one.

## Defect 3: Whose Memory Are We Counting?

The scaling math:

> *"500 roles **per tenant** × 100k resources × a few actions ≈ 150 million entries… at 20 bytes per entry, under 3 GB"*

The architecture:

> *"Each API server maintains an in-memory snapshot of the entire permission graph **for all tenants**"*

Individually fine. Jointly impossible. The real footprint is **3 GB × tenant count**.

And two things are missing from the 3 GB:

| | |
|---|---|
| 150M entries × 20 B | 3.00 GB (exactly 3, not "under") |
| + user-role assignments (5M × 5 × 16 B) | 0.40 GB — never counted |
| + hash-table slack at 70% load factor | 1.29 GB — 20 B/entry assumes zero overhead |
| **Realistic, one tenant** | **4.69 GB** |

On the proposed 16 GB server:

```
  1 tenant    4.69 GB   fits
  2 tenants   9.37 GB   fits
  5 tenants  23.43 GB   DOES NOT FIT
```

**Two tenants, not "all of them."**

The fix is already latent in the design: **shard servers by tenant.** Per-tenant versioning means a server only rebuilds for the tenants it owns — so tenant sharding fixes memory *and* rebuild frequency in one move. Either do that, or state the per-tenant footprint and the tenant count you're sizing for. Leaving it ambiguous is what's not okay.

## The Staleness Window Is a Security Window

The snapshot is a cache. A version counter bumps on every permission write; servers poll every second and rebuild when they see a change.

```
poll interval (1.0s) + rebuild (1.5s) = 2.5s worst-case staleness
```

At 1M checks/sec that's **2.5 million checks served from pre-revocation data.**

Now — is that acceptable? It depends entirely on *why* the permission changed:

| Change | 2.5s stale is… |
|---|---|
| "Alice joined the editors group" | fine. She waits 2.5s for a new capability. |
| "Alice removed from editors" | probably fine. |
| **"Alice was terminated and escorted out"** | **not fine.** |

> Grants may propagate lazily. **Revocations should not.**

Two ways to close it, and they compose:

1. **Push revocations synchronously** — pub/sub, and don't return from the API until servers ack.
2. **A short-lived deny-list**, consulted *before* the snapshot:

```python
def check_with_denylist(user, key, snapshot_version, base_decision):
    v = revoked_until_version.get((user,) + key)
    if v is not None and snapshot_version < v:
        return "deny"          # revocation not yet in this snapshot
    return base_decision
```

The list is tiny, and entries self-expire — once the server's snapshot version passes the revocation version, the entry is inert and gets garbage-collected. **The fast path keeps its shape; the window closes.**

## Tamper-Evident Is Not Tamper-Proof

The audit log chains hashes: `hash_i = SHA-256(hash_{i-1} || payload_i)`.

Edit a historical row and its hash no longer matches, which breaks every hash after it:

```
Edited row 2, hashes untouched  ->  detected at row 2  ✓
```

But an attacker who can write to the table can also **recompute the chain**:

```
Edited row 2 and recomputed the chain  ->  verifies clean. NOT detected.  ✗
```

The chain alone proves only **internal consistency**. What makes it evidence is the **anchor** — periodically publishing the current head hash somewhere the attacker can't rewrite (write-once storage, a separate database with restricted writes, a public timestamping service).

```
Against an anchor published at row 4  ->  DETECTED  ✓
```

> Verification only trusts the segment from the last anchor forward. Say where the anchor lives, or the property you're claiming doesn't exist.

## Audit Writes Must Not Be on the Critical Path

Two audit streams, two different treatments:

| Stream | Volume | Path |
|---|---|---|
| **Permission changes** | a few/day | synchronous, same transaction as the change |
| **Access decisions** | 1M/sec | async to Kafka, batch-inserted by a consumer |

Writing synchronously on every check would put a database round-trip in a 10 ms budget. And if the Kafka producer fails?

> **Availability of authorization beats completeness of audit.** The check still succeeds; log the gap locally.

Denying someone access because your *logging* was down is a self-inflicted outage.

## Common Mistakes

- **Traversing the role DAG per request.** The thing flattening exists to eliminate.
- **Unioning permission sets to answer one question.** 50,000 ops for a 1-key lookup.
- **Letting an allow override a deny.** Then it was never a deny.
- **Defaulting to allow on no match.** Absence of permission is not permission.
- **A `UNIQUE` constraint that forbids a required scenario.** Fails closed and silently.
- **Sizing one tenant, storing all of them.** State the unit.
- **Ignoring hash-table slack.** 20 B/entry is the payload, not the footprint.
- **Treating revocation like any other update.** Grants can lag; revocations can't.
- **Synchronous audit writes on the check path.** A database write in a 10 ms budget.
- **Calling a hash chain tamper-proof.** It's evidence only from the last anchor forward.
- **Inferring `tenant_id` from the user instead of the request.** That's a cross-tenant escalation.

## The Takeaway

> Role changes are rare; checks are constant. So do all the work when roles change, and make a check two hash lookups against a card printed in advance.

Three ideas carry it: **flatten the DAG at write time** (the request path never traverses anything), **probe, don't union** (answer the question you were asked, not every question), and **know your staleness** (a cache on an authorization path is a security window, and revocations don't get to wait for it).

And the habit that found all three defects: **read the design against its own requirements, line by line.** The schema forbade a stated feature. The complexity claim contradicted the algorithm one paragraph above it. The memory estimate used a different unit than the architecture. None of these needed outside knowledge — only checking the document against itself.
