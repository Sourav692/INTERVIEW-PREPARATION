# Chapter 7 — Data Security Design Patterns — CRAM SHEET

> Last-minute interview review. 9 patterns, 2-3 lines each. Full detail lives in `ch07_data_security_design_patterns.md`.

**The connecting thread:** Data security in this chapter moves through four layers — *comply* (delete on request), *restrict* (fine-grained access), *protect* (make stolen data useless), *connect* (authenticate without leaking credentials). Each layer assumes the previous one can fail, so it doesn't rely on it alone — access control exists even though removal patterns exist; encryption exists even though access control exists.

---

## One-Page Recall Table

| # | Pattern | Problem | Fix | #1 Gotcha |
|---|---|---|---|---|
| 1 | **Vertical Partitioner** | Immutable PII repeated in every record bloats removal cost | Split rows into mutable/immutable stores, joined by a merge key | Extra join hurts read performance |
| 2 | **In-Place Overwriter** | Legacy system, no removal design, must still comply | Delete/filter in place; stage-then-promote for raw formats | Reads + rewrites the *entire* dataset — costly |
| 3 | **Fine-Grained Accessor for Tables** | Table-level grants aren't granular enough (need column/row control) | GRANT, catalog tags, masking, or row policies | Row policies limited to session-derivable attributes |
| 4 | **Fine-Grained Accessor for Resources** | Cloud jobs have overly broad resource permissions | IAM resource- or identity-based least-privilege policies | Many narrow policies = maintenance burden; hard quotas exist |
| 5 | **Encryptor** | Data at rest/in transit could be intercepted or physically stolen | Server/client-side encryption + TLS, backed by a key management service | Lost key = lost data (mitigated by soft delete) |
| 6 | **Anonymizer** | Dataset has PII users haven't consented to share externally | Remove, perturb, or synthetically replace sensitive columns | Destroys analytical value (information loss) |
| 7 | **Pseudo-Anonymizer** | Fully anonymized data is too degraded for analytics | Mask, tokenize, hash, or encrypt while preserving structure | Re-identifiable when joined with other datasets |
| 8 | **Secrets Pointer** | Credentials risk leaking from Git/code | Store in a secrets manager; consumers fetch by reference at runtime | Cached credentials go stale, especially for streaming jobs |
| 9 | **Secretless Connector** | Team wants zero credentials to manage at all | IAM-role-based or certificate-based authentication | Setup and cert rotation still require real work |

---

## 1. Vertical Partitioner

**Problem:** Immutable PII (birthday, ID number) repeats in every record, making removal expensive.
**Solution:** Split each row into a mutable store and an immutable/PII store, linked by a merge key (e.g. `user_id`).
**Gotcha:** Reads now need a join across the split — query performance and complexity go up for consumers.

> **📌 Note:** Vertical partitioning here is a *security* specialization — Chapter 8 reuses the same mechanic purely for storage/performance, not compliance.

> **✅ Say this in interview:** "We isolate PII into a single-occurrence store so a deletion touches one row instead of thousands — we trade that for a read-side join, which we hide behind a view."

> **🎯 FAANG pointer:** Expect "how would you make GDPR deletes cheap at scale?" — the correct shape is *reduce what a deletion has to touch*, not *make deletion faster*. Vertical Partitioner is the textbook answer.

> **Databricks:** Confirmed — implement the immutable-attribute store as a Delta table and use `MERGE INTO` to deduplicate/upsert user context, exactly as the book's example does with Delta Lake's `DeltaTable.merge()`.

---

## 2. In-Place Overwriter

**Problem:** Legacy system, terabytes of data, no removal strategy, but new regulation forces compliance now.
**Solution:** `DELETE ... WHERE` if natively supported (+ vacuum for table formats); otherwise filter the whole dataset and stage-then-promote.
**Gotcha:** Touches *all* rows, not just the target — 2,000 records to remove one user, vs. 1 with Vertical Partitioner.

> **📌 Note:** Two delete-management strategies in table formats — deletion vectors (mark removed rows in a side file, reader-filtered) vs. full rewrite (writer-heavy, reader-clean).

> **✅ Say this in interview:** "When we can't redesign storage, we fall back to a full filter-and-rewrite — expensive, but universal, and we batch multiple removal requests into one run to amortize the cost."

> **🎯 FAANG pointer:** If asked to compare against Vertical Partitioner, lead with cost-at-scale (touches N rows vs. 1) and mention the "impossible rollback" risk if you skip the staging step.

> **Databricks:** Confirmed — Delta Lake `DeltaTable.delete()` + `VACUUM` is the exact mechanism; without vacuum, time travel still exposes "deleted" data.

---

## 3. Fine-Grained Accessor for Tables

**Problem:** Whole-table grants aren't enough — need column- and row-level restriction within an authorized table.
**Solution:** `GRANT` on columns, catalog policy tags, or masking functions for columns; dynamic `WHERE`-injecting policies for rows.
**Gotcha:** Row policies typically only condition on session attributes (user, group, IP) — not arbitrary business logic.

> **📌 Note:** Nested/complex column types can't take simple column-level policies directly — unnest first or expose via a materialized view.

> **✅ Say this in interview:** "We layer row-level security on top of table grants using session-derived predicates, and fall back to a permission-scoped materialized view if policy evaluation overhead becomes a latency problem."

> **🎯 FAANG pointer:** They may probe "how do you hide a column from some users but not others in the same table?" — answer with masking (Databricks/Snowflake) as the cleanest modern answer, GRANT(cols) as the classic SQL answer.

> **Databricks:** Confirmed — Unity Catalog supports column masking functions (`... STRING MASK ip_mask`) and `ROW FILTER` for row-level security, exactly as shown in the book.

---

## 4. Fine-Grained Accessor for Resources

**Problem:** Audit finds a job can overwrite *all* datasets in an object store — permissions are too broad.
**Solution:** At-least-privilege via IAM — resource-based (policy on the bucket) or identity-based (role on the job/user).
**Gotcha:** Strict least-privilege creates many small policies to maintain; IAM services have hard quotas (AWS: 1,500 policies; GCP: 300 custom roles/project).

> **📌 Note:** Wildcard prefixes (`visits*`) reduce policy sprawl but weaken the guarantee for future resources — flag this trade-off explicitly with security teams.

> **✅ Say this in interview:** "We prefer identity-based IAM roles over resource policies for application jobs, since a job's permissions travel with its role rather than needing per-bucket edits."

> **🎯 FAANG pointer:** A common follow-up is "resource-based vs identity-based IAM — when do you pick each?" Resource-based = fine when few consumers hit one resource; identity-based = scales better when one identity touches many resources.

> **Databricks:** Not a dedicated Databricks feature — this is standard cloud-provider IAM (AWS/GCP/Azure) that Databricks compute (clusters, jobs) assumes via service principals/instance profiles; Unity Catalog adds its own object-level grants on top but the book's examples here are pure cloud IAM.

---

## 5. Encryptor

**Problem:** Stakeholders worry about interception in transit and physical data theft at rest.
**Solution:** Server/client-side encryption at rest (via a key management service — KMS/Key Vault) + TLS in transit.
**Gotcha:** Losing the key locks out authorized users too — mitigated by soft-delete/restore-window on key deletion.

> **📌 Note:** Server-side encryption fully abstracts the encrypt/decrypt exchange from the client — you just manage access to the store and the key service.

> **✅ Say this in interview:** "Encryption doesn't replace access control — it's the layer that protects you if access control is somehow bypassed, since stolen ciphertext is useless without the key."

> **🎯 FAANG pointer:** Expect "what happens if you lose the encryption key?" — the right answer names the actual risk (data loss) and the actual mitigation (KMS soft-delete grace window), not "you shouldn't lose it."

> **Databricks:** Confirmed at the platform level — Databricks integrates with cloud KMS (AWS KMS, Azure Key Vault, GCP KMS) for customer-managed keys on workspace storage; this is the same server-side-encryption mechanism the book describes, not a Databricks-invented one.

---

## 6. Anonymizer

**Problem:** Sharing a dataset externally, but some users never consented to sharing their PII.
**Solution:** Remove, perturb (add noise), or synthetically replace (e.g. via Faker) sensitive columns.
**Gotcha:** Real information loss — technical consumers can't rely on those columns anymore; risks bad downstream models.

> **📌 Note:** Anonymized data stays unidentifiable *even when combined* with other datasets — that's the key distinction from pseudo-anonymization.

> **✅ Say this in interview:** "Anonymization is the strong guarantee — irreversible and safe under dataset joins — but it costs real analytical value, so we only apply it where consent or regulation actually requires it."

> **🎯 FAANG pointer:** If asked "anonymize vs pseudo-anonymize — which do you pick for a data-sharing deal?" — answer depends on whether the *recipient* needs residual business signal (salary bands, geography) or true opacity.

> **Databricks:** No dedicated product feature — this is implemented as ordinary column transforms (`.drop()`, `.withColumn()`) in a Spark/Databricks job, same as the book's PySpark + Faker example; nothing Unity-Catalog-specific here.

---

## 7. Pseudo-Anonymizer

**Problem:** Fully anonymized data removed too much — analysts can't answer basic business questions anymore.
**Solution:** Mask, tokenize (vault-backed), hash, or encrypt values to preserve structure/business meaning.
**Gotcha:** False sense of security — combining two pseudo-anonymized tables can re-identify a person (the "John Doe in San Marino" example).

> **📌 Note:** Tokenization's security is only as strong as the token vault — compromise the vault, and tokens become reversible.

> **✅ Say this in interview:** "Pseudo-anonymization preserves usability but not safety under joins — we treat it as a usability trade-off, not a compliance-grade anonymization technique, and we're explicit about that with data-sharing partners."

> **🎯 FAANG pointer:** A classic gotcha question: "is masking an SSN's last 4 digits enough for compliance?" — no, because combined with other quasi-identifiers (country, role, DOB) it can still re-identify someone.

> **Databricks:** Confirmed — Unity Catalog column masking functions can implement masking directly (same mechanism as Fine-Grained Accessor for Tables); tokenization/hashing are just UDFs, not a dedicated Databricks feature.

---

## 8. Secrets Pointer

**Problem:** Credentials in Git/code risk leaking (the book's example: an accidental leak spiked API billing).
**Solution:** Store credentials in a secrets manager (AWS Secrets Manager, GCP Secret Manager); consumers fetch by name at runtime.
**Gotcha:** Cached credentials can go stale — especially painful for long-running streaming jobs.

> **📌 Note:** Two protection layers stack here — access to the secrets manager itself, *and* the credential's own validity.

> **✅ Say this in interview:** "We never hardcode credentials — jobs resolve a secret name against a managed store at runtime, so rotating a credential doesn't require touching or redeploying consumer code."

> **🎯 FAANG pointer:** "How do you handle credential rotation for a long-running streaming job?" — the book's honest answer is: let it fail and restart to reload fresh creds (paired with idempotency), since async refresh risks mid-flight write issues.

> **Databricks:** Confirmed — Databricks Secrets (`dbutils.secrets.get(...)`) is the platform-native version of exactly this pattern, backed by Databricks-managed or Azure Key Vault-backed secret scopes.

---

## 9. Secretless Connector

**Problem:** A team wants zero credentials to manage at all — no API keys anywhere in code.
**Solution:** IAM-role-based access (assume-role/service account) or certificate-based authentication.
**Gotcha:** Not actually "workless" — assume-role/STS setup and certificate rotation both require real ongoing effort.

> **📌 Note:** Certificate-based auth swaps the IAM service for a certificate authority (CA) in the same four-step validation workflow.

> **✅ Say this in interview:** "Secretless is strictly better than Secrets Pointer where the platform supports it — there's simply nothing to leak — but it's not zero-effort; someone still owns the IAM role or cert lifecycle."

> **🎯 FAANG pointer:** "What's the most secure way to connect a Spark job to a database?" — the strongest answer is certificate-based or IAM-role-based (Secretless), not "use a secrets manager" (Secrets Pointer is second-best).

> **Databricks:** Confirmed — Databricks jobs commonly run under a cloud service principal / instance profile (AWS instance profiles, Azure managed identities) to reach cloud storage with zero stored credentials, matching the book's identity-based Secretless Connector approach.

---

## Before You Close the Laptop

Four layers, each assuming the last one can fail: **removal** (Vertical Partitioner cheap-but-narrow vs. In-Place Overwriter universal-but-costly) → **access control** (table-level vs. resource-level fine-grained IAM) → **protection** (Encryptor keeps data usable-but-locked; Anonymizer/Pseudo-Anonymizer trade safety for usability) → **connectivity** (Secrets Pointer good, Secretless Connector better). If you remember one line per pattern, remember the **Gotcha** column above — that's what interviewers probe.
