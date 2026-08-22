# -*- coding: utf-8 -*-
"""The ingestion pipeline: load -> validate ACLs -> chunk -> embed -> index.

The validation step is deliberately loud. A document that reaches the index without
usable access-control metadata is a latent data leak, so the pipeline refuses it
rather than defaulting it to "internal" and hoping.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..config import SETTINGS
from ..llm.client import LLMClient
from ..models import SENSITIVITY_RANK, Chunk, Document
from . import catalog, store
from .chunker import chunk_corpus
from .loader import load_corpus


@dataclass
class IngestReport:
    documents: int = 0
    chunks: int = 0
    embedded: int = 0
    rejected: List[str] = field(default_factory=list)
    by_source: Dict[str, int] = field(default_factory=dict)
    by_sensitivity: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0

    def render(self) -> str:
        lines = [f"documents indexed : {self.documents}",
                 f"chunks indexed    : {self.chunks}",
                 f"embedding cost    : ${self.cost_usd:.5f}"]
        if self.rejected:
            lines.append(f"REJECTED          : {len(self.rejected)}")
            lines.extend(f"    - {r}" for r in self.rejected)
        lines.append("by source         : " + ", ".join(
            f"{k}={v}" for k, v in sorted(self.by_source.items())))
        lines.append("by sensitivity    : " + ", ".join(
            f"{k}={v}" for k, v in sorted(self.by_sensitivity.items(),
                                          key=lambda kv: SENSITIVITY_RANK[kv[0]])))
        return "\n".join(lines)


def validate_acl(doc: Document) -> Optional[str]:
    """Refuse anything we cannot enforce a policy on. Returns an error string or None."""
    a = doc.attrs
    if a.sensitivity not in SENSITIVITY_RANK:
        return f"{a.doc_id}: unknown sensitivity '{a.sensitivity}'"
    if not a.allowed_groups:
        return f"{a.doc_id}: no allowed_groups - refusing to index an unowned document"
    if a.region not in {"EU", "US", "GLOBAL"}:
        return f"{a.doc_id}: unknown region '{a.region}'"
    if a.sensitivity == "public" and "public" not in a.allowed_groups:
        return f"{a.doc_id}: marked public but the 'public' group is not in allowed_groups"
    if a.sensitivity != "public" and "public" in a.allowed_groups:
        return f"{a.doc_id}: non-public document grants the 'public' group"
    return None


def ingest(tenant_id: str = "meridian",
           reset: bool = True,
           batch_size: int = 64,
           settings=SETTINGS) -> IngestReport:
    report = IngestReport()

    if reset:
        store.reset_store(settings)
        catalog.reset_catalog(settings)

    docs = load_corpus(settings.corpus_dir, tenant_id)
    accepted: List[Document] = []
    for d in docs:
        err = validate_acl(d)
        if err:
            report.rejected.append(err)
        else:
            accepted.append(d)
    report.documents = len(accepted)

    # The ACL catalog is the authoritative source (Layer 2 reads it fresh on every
    # request). It is populated here, independently of embedding/chunking below -
    # a permission-only change later never needs to touch this step again.
    catalog.upsert_many([d.attrs for d in accepted], settings)

    chunks: List[Chunk] = chunk_corpus(accepted, settings)
    report.chunks = len(chunks)
    for c in chunks:
        report.by_source[c.attrs.source] = report.by_source.get(c.attrs.source, 0) + 1
        report.by_sensitivity[c.attrs.sensitivity] = \
            report.by_sensitivity.get(c.attrs.sensitivity, 0) + 1

    llm = LLMClient(settings)
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        vectors = llm.embed([c.text for c in batch], purpose="embed_document")
        report.embedded += store.upsert_chunks(tenant_id, batch, vectors, settings)

    report.cost_usd = llm.usage.cost_usd
    return report
