# -*- coding: utf-8 -*-
"""Data Transformation — runnable reference for the DevRev technical round.

Covers: flattening nested JSON to dot-notation, normalizing nested payloads into
FK-linked tables, schema-drift adapters, missing-vs-null resolution, timestamp
normalization to ISO-8601, dedupe on business keys, and target-schema validation.

Run:  python data_transformation_reference.py
"""
import hashlib
from datetime import datetime, timezone


# =====================================================================
# 1. FLATTENING
# =====================================================================
def _is_primitive_list(lst):
    return all(not isinstance(x, (dict, list)) for x in lst)


def flatten(obj, parent="", sep="."):
    """Recursively flatten nested dicts (and arrays) into dot-notation keys."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{parent}{sep}{k}" if parent else k
            out.update(flatten(v, key, sep))
    elif isinstance(obj, list):
        if _is_primitive_list(obj):
            out[parent] = obj                          # array of scalars -> keep as one value
        else:
            for i, v in enumerate(obj):                # array of objects -> explode by index
                out.update(flatten(v, f"{parent}{sep}{i}", sep))
    else:
        out[parent] = obj                              # a leaf scalar
    return out


def normalize_ticket(ticket):
    """Explode one nested ticket into rows for 4 relational tables (with foreign keys)."""
    tables = {"tickets": [], "conversations": [], "messages": [], "attachments": []}
    tid = ticket["id"]
    tables["tickets"].append(
        {"id": tid, "subject": ticket.get("subject"), "status": ticket.get("status")}
    )
    for conv in ticket.get("conversations", []):
        cid = conv["id"]
        tables["conversations"].append(
            {"id": cid, "ticket_id": tid, "channel": conv.get("channel")}
        )
        for msg in conv.get("messages", []):
            mid = msg["id"]
            tables["messages"].append(
                {"id": mid, "conversation_id": cid,
                 "author": msg.get("author"), "body": msg.get("body")}
            )
            for att in msg.get("attachments", []):
                tables["attachments"].append(
                    {"id": att["id"], "message_id": mid,
                     "filename": att.get("filename"), "url": att.get("url")}
                )
    return tables


# =====================================================================
# 2. SCHEMA HANDLING
# =====================================================================
def coerce_assignee(value):
    """Accept the string (v1) OR object (v2) form; always return {id, name}."""
    if value is None:
        return None
    if isinstance(value, str):
        return {"id": None, "name": value}
    if isinstance(value, dict):
        return {"id": value.get("id"), "name": value.get("name")}
    raise ValueError(f"unexpected assignee shape: {type(value).__name__}")


def get_field(record, names, default=None):
    """First present, non-None value among candidate key names (handles renamed keys)."""
    for n in names:
        if n in record and record[n] is not None:
            return record[n]
    return default


FIELD_MAP = {
    "id":      ["id", "ticket_id", "uuid"],
    "subject": ["subject", "title", "summary"],
    "created": ["created_at", "createdAt", "created"],
}


def transform(record):
    return {out: get_field(record, aliases) for out, aliases in FIELD_MAP.items()}


_MISSING = object()  # unique sentinel to distinguish "absent" from "None"


def resolve(record, key, on_missing, on_null):
    """Missing key vs explicit null are different — return the right default for each."""
    if key not in record:
        return on_missing
    v = record[key]
    return on_null if v is None else v


# =====================================================================
# 3. DATA CLEANING
# =====================================================================
_DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"]


def to_iso8601(value):
    """Best-effort parse of many date formats into a canonical ISO-8601 UTC string."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1e12 else value      # epoch ms vs seconds
        return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    s = str(value).strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))  # already ISO (incl. 'Z')
    except ValueError:
        dt = None
        for fmt in _DATE_FORMATS:
            try:
                dt = datetime.strptime(s, fmt); break
            except ValueError:
                continue
        if dt is None:
            raise ValueError(f"unparseable date: {value!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)                    # naive -> assume UTC
    return dt.astimezone(timezone.utc).isoformat()


def business_key_hash(record, keys):
    """Stable fingerprint from chosen business keys (normalized for consistency)."""
    parts = [str(record.get(k, "")).strip().lower() for k in keys]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def dedupe(records, keys):
    seen = {}
    for r in records:
        h = business_key_hash(r, keys)
        if h not in seen:                                       # first occurrence wins
            seen[h] = r
    return list(seen.values())


def validate(record, schema):
    """schema: {field: {"type": <type>, "required": <bool>}} -> list of error strings."""
    errors = []
    for field, spec in schema.items():
        present = field in record and record[field] is not None
        if not present:
            if spec.get("required"):
                errors.append(f"missing required field '{field}'")
            continue
        if not isinstance(record[field], spec["type"]):
            errors.append(
                f"'{field}': expected {spec['type'].__name__}, "
                f"got {type(record[field]).__name__}"
            )
    return errors


# =====================================================================
# DEMO / SELF-TEST
# =====================================================================
if __name__ == "__main__":
    print("=== 1. Flatten to dot-notation ===")
    payload = {"customer": {"name": "Ada", "address": {"city": "Pune", "zip": "411001"}},
               "tags": ["urgent", "billing"]}
    flat = flatten(payload)
    for k, v in flat.items():
        print(f"  {k} = {v}")
    assert flat["customer.address.city"] == "Pune"
    assert flat["tags"] == ["urgent", "billing"]   # array of scalars kept as one value

    print("\n=== 1b. Normalize ticket -> FK-linked tables ===")
    ticket = {
        "id": "T1", "subject": "Cannot log in", "status": "open",
        "conversations": [{
            "id": "C1", "channel": "email",
            "messages": [
                {"id": "M1", "author": "user", "body": "help!",
                 "attachments": [{"id": "A1", "filename": "err.png", "url": "http://x/err.png"}]},
                {"id": "M2", "author": "agent", "body": "try reset"},
            ],
        }],
    }
    tables = normalize_ticket(ticket)
    for name, rows in tables.items():
        print(f"  {name}: {len(rows)} row(s)")
    assert tables["conversations"][0]["ticket_id"] == "T1"     # FK check
    assert tables["messages"][0]["conversation_id"] == "C1"
    assert tables["attachments"][0]["message_id"] == "M1"

    print("\n=== 2. Schema drift: assignee string(v1) or object(v2) ===")
    print("  v1:", coerce_assignee("Ada"))
    print("  v2:", coerce_assignee({"id": 7, "name": "Ada"}))
    assert coerce_assignee("Ada") == {"id": None, "name": "Ada"}
    assert coerce_assignee({"id": 7, "name": "Ada"})["id"] == 7

    print("\n=== 2b. Tolerant field mapping (renamed keys) ===")
    print("  v1 record:", transform({"ticket_id": "T9", "title": "Bug", "createdAt": "2024-01-01"}))
    assert transform({"ticket_id": "T9", "title": "Bug"})["id"] == "T9"

    print("\n=== 2c. Missing vs explicit null ===")
    print("  missing phone ->", resolve({}, "phone", on_missing="<keep>", on_null=None))
    print("  null phone    ->", resolve({"phone": None}, "phone", on_missing="<keep>", on_null=None))
    assert resolve({}, "phone", "<keep>", None) == "<keep>"
    assert resolve({"phone": None}, "phone", "<keep>", None) is None

    print("\n=== 3. Dates -> ISO 8601 (UTC) ===")
    for raw in ["2024-03-01", "03/01/2024", 1709294400, "2024-03-01T12:00:00Z"]:
        print(f"  {raw!r:28} -> {to_iso8601(raw)}")
    assert to_iso8601("2024-03-01").startswith("2024-03-01T00:00:00")
    assert to_iso8601("2024-03-01T12:00:00Z") == "2024-03-01T12:00:00+00:00"

    print("\n=== 3b. Dedupe on business keys ===")
    recs = [
        {"email": "A@x.com ", "name": "Ada"},
        {"email": "a@x.com", "name": "Ada A"},   # same person, messy email
        {"email": "b@x.com", "name": "Bo"},
    ]
    unique = dedupe(recs, keys=["email"])
    print(f"  {len(recs)} in -> {len(unique)} unique")
    assert len(unique) == 2

    print("\n=== 3c. Validate against target schema ===")
    schema = {"id": {"type": str, "required": True},
              "count": {"type": int, "required": True}}
    print("  good:", validate({"id": "x", "count": 3}, schema))
    print("  bad :", validate({"count": "3"}, schema))
    assert validate({"id": "x", "count": 3}, schema) == []
    assert len(validate({"count": "3"}, schema)) == 2   # missing id + wrong type for count

    print("\nALL CHECKS PASSED")
