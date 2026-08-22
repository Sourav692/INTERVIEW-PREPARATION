# -*- coding: utf-8 -*-
"""Load corpus documents and their ACL frontmatter.

In production these attributes come from the *source system* - Confluence space
permissions, SharePoint groups, Zendesk brand/organisation. The connector's real
job is to faithfully translate that system's permission model into ours. Getting
this translation wrong is the number one cause of enterprise RAG leaks, which is
why it lives in its own, boringly explicit function.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional

from ..config import SETTINGS
from ..models import Document, ResourceAttributes

DEFAULT_TENANT = "meridian"


def _parse_frontmatter(text: str) -> (Dict[str, str], str):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    meta: Dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    return meta, body


def _csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [s.strip() for s in value.split(",") if s.strip()]


def attrs_from_frontmatter(meta: Dict[str, str], tenant_id: str = DEFAULT_TENANT) -> ResourceAttributes:
    """The connector's translation step: source metadata -> our ABAC attributes."""
    return ResourceAttributes(
        doc_id=meta["doc_id"],
        tenant_id=tenant_id,
        source=meta["source"],
        sensitivity=meta["sensitivity"],
        allowed_groups=_csv(meta.get("allowed_groups")),
        region=meta.get("region", "GLOBAL"),
        product=meta.get("product", "platform"),
        owner=meta.get("owner", "unassigned"),
        contains_pii=str(meta.get("contains_pii", "false")).lower() == "true",
        need_to_know=_csv(meta.get("need_to_know")),
        valid_from=meta.get("valid_from") or None,
        valid_until=meta.get("valid_until") or None,
    )


def load_corpus(corpus_dir: Optional[Path] = None,
                tenant_id: str = DEFAULT_TENANT) -> List[Document]:
    corpus_dir = Path(corpus_dir or SETTINGS.corpus_dir)
    docs: List[Document] = []
    for path in sorted(corpus_dir.glob("*.md")):
        raw = io.open(path, encoding="utf-8").read()
        meta, body = _parse_frontmatter(raw)
        if not meta.get("doc_id"):
            raise ValueError(f"{path.name} has no doc_id in frontmatter - refusing to index "
                             f"a document with no identity or ACL")
        attrs = attrs_from_frontmatter(meta, tenant_id)
        docs.append(Document(attrs=attrs,
                             title=meta.get("title", attrs.doc_id),
                             text=body,
                             uri=f"file://{path.as_posix()}"))
    return docs
