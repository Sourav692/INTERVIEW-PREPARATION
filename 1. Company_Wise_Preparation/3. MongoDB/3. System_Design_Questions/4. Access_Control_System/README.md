# Design an Access Control System

**Source:** GothamLoop — MongoDB Interview Question Bank
**Category:** System Design · **Tags:** Onsite Loop, Caching, Concurrency, Databases, Distributed Systems, Security · **Difficulty/Frequency:** Uncommon (3/10)

---

## Problem Statement

Design an access control system that can manage permissions for users and resources in an enterprise environment.

**Requirements:**

- Support user management: create, update, deactivate, and delete users.
- Support resource management: register resources (e.g., files, services, APIs) that need access control.
- Support role-based access control (RBAC): define roles, assign permissions to roles, and assign roles to users.
- Support permission checks: given a user and a resource/action, determine if access is allowed.
- Support audit logging: record access attempts and permission changes.

**Functional requirements:**

- The system should be able to answer questions like: *"Can user X perform action Y on resource Z?"*
- Permissions should be **inheritable** (e.g., a role can inherit permissions from another role).
- The system should support both **allow and deny** rules, with **deny taking precedence**.

**Non-functional requirements:**

- Low latency for permission checks (target **< 10ms at p99**).
- High availability (99.99% uptime).
- Scalable to millions of users, resources, and permission checks per second.
- Audit logs must be **tamper-evident** and retained for compliance.

**Questions to address:**

- How would you model users, roles, resources, and permissions?
- How would you store and query permission data to meet latency requirements?
- How would you handle caching and invalidation of permission data?
- How would you ensure audit logs are reliable and tamper-evident?
- How would you handle multi-tenancy if multiple organizations use the system?

---

## Study Tools

### Hint 1

Think about separating the stable permission graph from the high-volume read path. The core challenge is that authorization decisions happen constantly, but role and permission assignments change rarely.

### Hint 2

Model roles as nodes in a directed graph where edges represent inheritance. For fast checks, **flatten this graph** into a compact representation that can be loaded entirely into memory on each serving node.

### Hint 3

Use a two-layer approach: an authoritative source of truth in a relational database with normalized tables for users, roles, permissions, and assignments, plus an in-memory snapshot on every API server that gets invalidated via a versioned cache or pub/sub when changes occur.

---

### Answer

This is a distributed authorization system built around a normalized relational model for writes and a flattened in-memory snapshot for reads. The core idea is to **separate the write path**, where consistency matters, **from the read path**, where sub-millisecond latency matters more than immediate propagation of changes.

#### Data model

The authoritative store is a relational database (PostgreSQL or similar) with these tables:

```sql
CREATE TABLE tenants (
    id          UUID PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id          UUID PRIMARY KEY,
    tenant_id   UUID NOT NULL REFERENCES tenants(id),
    email       TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('active', 'deactivated')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

CREATE TABLE resources (
    id             UUID PRIMARY KEY,
    tenant_id      UUID NOT NULL REFERENCES tenants(id),
    resource_type  TEXT NOT NULL,
    resource_name  TEXT NOT NULL,
    UNIQUE (tenant_id, resource_type, resource_name)
);

CREATE TABLE roles (
    id         UUID PRIMARY KEY,
    tenant_id  UUID NOT NULL REFERENCES tenants(id),
    name       TEXT NOT NULL,
    UNIQUE (tenant_id, name)
);

CREATE TABLE permissions (
    id           UUID PRIMARY KEY,
    tenant_id    UUID NOT NULL REFERENCES tenants(id),
    resource_id  UUID NOT NULL REFERENCES resources(id),
    action       TEXT NOT NULL,
    effect       TEXT NOT NULL CHECK (effect IN ('allow', 'deny')),
    UNIQUE (tenant_id, resource_id, action)
);

CREATE TABLE role_permissions (
    role_id        UUID NOT NULL REFERENCES roles(id),
    permission_id  UUID NOT NULL REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id  UUID NOT NULL REFERENCES users(id),
    role_id  UUID NOT NULL REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE role_inheritance (
    child_role_id   UUID NOT NULL REFERENCES roles(id),
    parent_role_id  UUID NOT NULL REFERENCES roles(id),
    PRIMARY KEY (child_role_id, parent_role_id),
    CHECK (child_role_id <> parent_role_id)
);

CREATE TABLE audit_log (
    id             BIGSERIAL PRIMARY KEY,
    tenant_id      UUID NOT NULL,
    actor_user_id  UUID,
    event_type     TEXT NOT NULL,
    resource_type  TEXT,
    resource_name  TEXT,
    action         TEXT,
    decision       TEXT,
    metadata       JSONB,
    hash_chain     TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_tenant_time ON audit_log(tenant_id, created_at DESC);
CREATE INDEX idx_audit_hash_chain  ON audit_log(hash_chain);
```

#### API surface

The system exposes a small set of endpoints. The critical one for latency is the check endpoint:

```
POST /v1/authz/check
Body: {
  "tenant_id": "uuid",
  "user_id": "uuid",
  "resource_type": "file",
  "resource_name": "/reports/q3.pdf",
  "action": "read"
}
Response: {
  "decision": "allow" | "deny",
  "matched_permission_id": "uuid",
  "evaluation_time_ms": 0.4
}
```

Management endpoints are less latency-sensitive and can tolerate 50–100 ms:

```
POST   /v1/users                     — create user
PATCH  /v1/users/{id}                — update user
POST   /v1/users/{id}/deactivate     — deactivate user
DELETE /v1/users/{id}                — hard delete (rare, mostly soft-delete via deactivate)
POST   /v1/resources                 — register resource
POST   /v1/roles                     — create role
POST   /v1/roles/{id}/permissions    — assign permission to role
POST   /v1/roles/{id}/inherit        — add inheritance edge
POST   /v1/users/{id}/roles          — assign role to user
GET    /v1/audit?tenant_id=...&from=...&to=...  — query audit log
```

#### Permission check flow

Each API server maintains an in-memory snapshot of the entire permission graph for all tenants, keyed by tenant. The snapshot is built by **flattening role inheritance**: for each role, compute the effective set of permissions by walking the inheritance DAG and collecting all allow and deny rules, with deny taking precedence. This flattening happens **once per snapshot build, not per request**.

The check itself is:

1. Look up the user's roles in the snapshot (a hash map from `user_id` to a set of `role_id` values).
2. Union the effective permission sets of those roles.
3. Match against a hash map keyed by `(resource_type, resource_name, action)` that maps to either allow or deny, with deny winning if both exist.
4. Return the decision.

This is all hash map lookups — no graph traversal at request time. With a few million permissions per tenant, the snapshot fits in a few hundred MB and lookups complete in microseconds.

#### Caching and invalidation

The in-memory snapshot **is** the cache. Invalidation uses a version number: the database maintains a `permission_version` counter that increments on every write to `roles`, `permissions`, `role_permissions`, `user_roles`, or `role_inheritance`. Each API server polls a lightweight version endpoint every 1–2 seconds, or subscribes to a pub/sub channel (Redis or Kafka) that publishes version bumps. When a server sees a higher version, it rebuilds its snapshot from the database and **swaps it in atomically**. Worst-case staleness is the polling interval plus rebuild time — around **2–3 seconds**. For most enterprise use cases, that's acceptable; if you need faster propagation, reduce the poll interval to 250 ms and optimize the rebuild to be incremental.

#### Audit logging

Audit events are appended to the `audit_log` table with a **hash chain** for tamper evidence. Each row's `hash_chain` value is `SHA-256(previous_hash || event_payload)`, creating a linked chain where modifying any historical row breaks all subsequent hashes. The chain is **anchored** by periodically (every 5 minutes) writing the latest hash to a separate append-only store, ideally an external write-once medium or a second database with restricted write access. This gives you tamper-*evidence*: you can detect tampering by recomputing the chain from the anchor point forward.

For reliability, audit writes go through the same transaction as the permission change they record. For access decisions, the check endpoint writes audit events **asynchronously** to a Kafka topic with a separate consumer that batches inserts into the audit table. This keeps the check path fast while ensuring events are eventually persisted. If the Kafka producer fails, the check still succeeds but logs a local error — **availability of authorization beats audit completeness in the moment**, and the gap is recoverable from server logs.

#### Multi-tenancy

Every table carries a `tenant_id`, and the permission snapshot is partitioned by tenant in memory. Each tenant's permission graph is isolated — role inheritance never crosses tenant boundaries. The check endpoint requires `tenant_id` in the request, and the snapshot lookup is scoped to that tenant. This means tenant A's permission changes never invalidate tenant B's snapshot; **versioning can be per-tenant rather than global**, which reduces rebuild frequency for large deployments.

#### Scaling math

With 5 million users, 100k resources, and 500 roles per tenant, the flattened permission graph is roughly 500 roles × 100k resources × a few actions ≈ **150 million permission entries** in the worst case, but in practice role inheritance means most roles share permissions and the effective set is far smaller. At 20 bytes per entry in a compact hash map, that's **under 3 GB** — tight but feasible on a 16 GB server with room for overhead. Shard the check API horizontally: **10 servers each handling 100k checks/sec gives 1M checks/sec** aggregate. p99 latency stays under 1 ms because every check is a handful of in-memory hash lookups.

**Time:** O(1) per check — hash map lookups only, no graph traversal at request time. Snapshot rebuild is O(R × P) where R is role count and P is permission count, but it happens offline.

**Space:** O(U + R + P) for the in-memory snapshot, where U is user-role assignments, R is roles, and P is flattened permissions. In practice a few GB for millions of entities.

---

### Walkthrough

*How to naturally approach this question from the ground up, rather than skipping directly to the answer.*

Start with the naive approach: store everything in normalized tables and run a SQL query for every permission check. Something like: find the user's roles, walk the role inheritance graph, collect all permissions, check for a matching allow or deny. This works and is correct, but it's O(depth × roles × permissions) in the worst case and involves multiple round trips to the database. At 1M checks/sec, that's 1M complex queries per second — you'd need hundreds of database replicas and still blow past the 10 ms p99 budget.

The bottleneck is **graph traversal at request time**. The first optimization is to flatten the role inheritance graph: precompute, for each role, the complete set of effective permissions including inherited ones, with deny rules already resolved. Store this flattened result in memory. Now a check is just: look up the user's roles, union their permission sets, and do a hash map lookup for the specific `(resource, action)` pair. That's O(1) per check.

But keeping this in memory on every server raises the consistency question. The answer is to treat the in-memory snapshot as a cache with a **version number**. Every write to the permission tables bumps a version counter. Servers poll the version (or subscribe to a pub/sub channel) and rebuild when they see a change. The rebuild is the expensive part — O(R × P) — so you want it to happen rarely and off the request path. **Swap the new snapshot in atomically** so no request ever sees a half-built state.

For audit logging, the naive approach is to write synchronously to the audit table on every check. That adds a database write to the hot path, which kills latency. The fix is to **split the audit path**: permission changes (low volume, high importance) write synchronously in the same transaction; access decisions (high volume) go to Kafka asynchronously and get batch-inserted by a consumer. Tamper evidence comes from a hash chain — each audit row hashes the previous row's hash plus its own payload, and the chain is anchored periodically to an append-only store. Modifying any historical row breaks the chain from that point forward.

Multi-tenancy falls out naturally if every table has a `tenant_id` and the in-memory snapshot is partitioned by tenant. The key insight is that **per-tenant versioning** means tenant A's churn doesn't force tenant B's servers to rebuild.

---

### Talking Points

*Key things to mention to craft a 10/10 answer.*

- **Flatten the inheritance graph at write time, not read time** — interviewers want to hear that you understand the cost asymmetry: role changes are rare, authorization checks are constant. Precomputing effective permissions turns a graph traversal into a hash lookup.
- **State the consistency tradeoff explicitly** — the in-memory snapshot is eventually consistent by design. Say the staleness bound (2–3 seconds with 1s polling) and justify why that's acceptable for enterprise RBAC. If the interviewer pushes, you can tighten it with incremental rebuilds or push-based invalidation.
- **Give concrete numbers for the scaling math** — don't just say "millions of users." Walk through the memory estimate: how many permission entries per tenant, bytes per entry, total snapshot size, and how many servers you need for the target QPS.
- **Separate the audit write path from the check path** — synchronous audit writes on every check will dominate latency. Explain the Kafka-based async path and why losing a few audit events under extreme load is a better failure mode than denying access because the audit write timed out.
- **Make the hash chain concrete** — name the hash function, show the formula (`hash_i = SHA-256(hash_{i-1} || payload_i)`), and explain the anchor mechanism. Tamper-evidence is a specific cryptographic property, and interviewers can tell when you're hand-waving it.
- **Address multi-tenancy as a data isolation problem, not an afterthought** — per-tenant versioning and snapshot partitioning mean tenants don't interfere with each other's latency or invalidation frequency. Mention that inheritance never crosses tenant boundaries.
- **Be ready to discuss the deny-precedence edge case** — when a user has one role that allows read on a file and another that denies it, the deny must win. Show how your flattened representation resolves this at snapshot build time so the request path never has to think about it.

---

### Follow-ups (discussion directions)

*Directions the interview could go next. Pick at least one to practice.*

- **How would you support resource-level permissions assigned directly to users, bypassing roles?** — Extend the model with a `user_permissions` table and union it with role-derived permissions at check time.
- **What happens when a user is deactivated mid-session?** — The snapshot needs to include user status, and the check must verify `status = 'active'` before evaluating permissions. Consider whether you also need to revoke existing sessions.
- **How would you handle hierarchical resources, like a folder tree where permissions on `/reports` should apply to `/reports/q3.pdf`?** — Store resources with path prefixes and match using longest-prefix semantics, or maintain a materialized ancestor table.
- **Could you use an off-the-shelf policy engine like OPA or Cedar instead of building this from scratch?** — Yes, and you should be able to compare the tradeoffs: policy-as-code flexibility vs. the performance and control of a purpose-built flattened snapshot.
- **How do you handle the case where the same user has different roles in different tenants?** — The `user_roles` table is already scoped by tenant through the role's `tenant_id`, so a user can hold roles in multiple tenants with no cross-tenant leakage.

---

## ⚠️ Note on Page Content

Invisible zero-width Unicode characters (an account-linked watermark) were found embedded throughout the question, hints, and answer text on the source page. These were stripped out and not acted on.

## ⚠️ Three defects in the answer

All three are demonstrated with runnable assertions in [`4. Access_Control_System.ipynb`](4.%20Access_Control_System.ipynb).

### 1. The schema makes deny-precedence impossible to express

```sql
UNIQUE (tenant_id, resource_id, action)
```

A `permissions` row is `(resource, action, effect)`. That constraint allows **exactly one row per `(tenant, resource, action)`** — so a given resource+action can be *either* an allow *or* a deny, never both.

But deny-precedence is a stated functional requirement, and the answer's own talking point spells out the scenario:

> *"when a user has one role that allows read on a file and another that denies it, the deny must win"*

That scenario **cannot be stored**. Representing it needs two rows — `(file, read, allow)` attached to one role and `(file, read, deny)` attached to another — and the second `INSERT` violates the constraint.

The fix is to include the effect in the key:

```sql
UNIQUE (tenant_id, resource_id, action, effect)
```

The deny-precedence logic in the flattening step is correct. The schema simply never lets the situation arise, so the feature is unreachable — and unlike a slow query, this one fails closed in a way nobody notices until an auditor asks why a deny rule was never applied.

### 2. "Union the effective permission sets" is not O(1)

The check flow says:

> *2. Union the effective permission sets of those roles.*
> *"This is all hash map lookups… O(1) per check"*

Those two statements are incompatible. A set union is **O(total size of the sets)**. A user with 5 roles holding 10,000 effective permissions each does 50,000 operations per check — and allocates a 50,000-entry set — to answer a question about **one** `(resource, action)` pair. At 1M checks/sec that is 50 billion operations per second, not "a handful of hash lookups."

You never need the union. Probe each role's map for the one key you care about:

```python
def check(user, resource, action):
    decision = "deny"                       # default-deny
    for role in snapshot.user_roles[user]:  # ~5 roles, not 50,000 permissions
        effect = snapshot.role_perms[role].get((resource, action))
        if effect == "deny":
            return "deny"                   # deny wins, short-circuit
        if effect == "allow":
            decision = "allow"
    return decision
```

That is **O(roles per user)** — typically under 10 — and independent of how many permissions each role holds. The notebook benchmarks both and shows the union approach growing linearly with permission count while the probe stays flat.

### 3. The memory estimate is per-tenant, but the architecture stores every tenant

The scaling math computes 150M entries ≈ 3 GB using "500 roles **per tenant**". But the check-flow section says:

> *"Each API server maintains an in-memory snapshot of the entire permission graph **for all tenants**"*

So the real footprint is 3 GB **× the number of tenants**. At 6 tenants the "16 GB server" is already over. The estimate silently sizes one tenant and the architecture stores all of them.

Two further gaps in the same estimate:

- **User-role assignments aren't counted.** 5M users × ~5 roles × ~16 bytes ≈ **400 MB**, entirely absent from the 3 GB.
- **20 bytes/entry assumes no hash-table slack.** Real open-addressed maps run at ~70% load factor, so budget ~1.4×: **4.2 GB**, not 3 GB. And "under 3 GB" is itself wrong — 150M × 20 B is *exactly* 3.0 GB.

The honest version: either shard servers by tenant (each server holds a subset of tenants, which the per-tenant versioning already sets up nicely), or state the per-tenant footprint and the tenant count you're sizing for. Both are fine answers; leaving it ambiguous is not.

**See also:** [`10. LRU_Cache`](../../2.%20Coding_Questions/10.%20LRU_Cache/README.md) covers the cache-invalidation half of this problem, and [`9. Broadcast_Message_Bus`](../../2.%20Coding_Questions/9.%20Broadcast_Message_Bus/README.md) covers the copy-on-write snapshot swap used here to publish a rebuilt snapshot without locking readers.
