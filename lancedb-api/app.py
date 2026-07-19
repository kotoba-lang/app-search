import os
import json
from datetime import datetime, timezone
from typing import Any

import lancedb
import pyarrow as pa
from fastapi import FastAPI
from pydantic import BaseModel, Field

APP_NAME = "tonbo"
LANCEDB_URI = os.getenv("LANCEDB_URI", "/data/lancedb")
TABLE_NAME = os.getenv("TABLE_NAME", "crawler_pages")

app = FastAPI(title=APP_NAME)
_db = lancedb.connect(LANCEDB_URI)

SCHEMA = pa.schema([
    pa.field("doc_id", pa.string()),
    pa.field("result_id", pa.string()),
    pa.field("job_id", pa.string()),
    pa.field("url", pa.string()),
    pa.field("domain", pa.string()),
    pa.field("title", pa.string()),
    pa.field("snippet", pa.string()),
    pa.field("text_content", pa.string()),
    pa.field("language", pa.string()),
    pa.field("status", pa.int64()),
    pa.field("size_bytes", pa.int64()),
    pa.field("link_count", pa.int64()),
    pa.field("primary_image", pa.string()),
    pa.field("primary_image_cdn", pa.string()),
    pa.field("indexed_at", pa.string()),
    pa.field("seed_category", pa.string()),
    pa.field("metadata_json", pa.string()),
    pa.field("ogp_json", pa.string()),
])


def _table():
    names = set(_db.table_names())
    if TABLE_NAME not in names:
        return _db.create_table(TABLE_NAME, schema=SCHEMA)
    return _db.open_table(TABLE_NAME)


def _to_int(v: Any) -> int:
    if v is None:
        return 0
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _normalize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    metadata = doc.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    ogp = doc.get("ogp")
    if not isinstance(ogp, dict):
        ogp = {}

    doc_id = _to_str(doc.get("doc_id"))
    if not doc_id:
        rid = _to_str(doc.get("result_id"))
        if rid:
            doc_id = f"res:{rid}"
        else:
            url = _to_str(doc.get("url"))
            job = _to_str(doc.get("job_id"))
            doc_id = f"{job}:{url}" if url else f"job:{job}"

    seed_category = _to_str(doc.get("seed_category"))
    if not seed_category:
        seed_category = _to_str(metadata.get("seed_category"))

    indexed_at = _to_str(doc.get("indexed_at"))
    if not indexed_at:
        indexed_at = datetime.now(timezone.utc).isoformat()

    return {
        "doc_id": doc_id,
        "result_id": _to_str(doc.get("result_id")),
        "job_id": _to_str(doc.get("job_id")),
        "url": _to_str(doc.get("url")),
        "domain": _to_str(doc.get("domain")),
        "title": _to_str(doc.get("title")),
        "snippet": _to_str(doc.get("snippet")),
        "text_content": _to_str(doc.get("text_content")) or _to_str(doc.get("body")),
        "language": _to_str(doc.get("language")),
        "status": _to_int(doc.get("status")),
        "size_bytes": _to_int(doc.get("size_bytes")),
        "link_count": _to_int(doc.get("link_count")),
        "primary_image": _to_str(doc.get("primary_image")),
        "primary_image_cdn": _to_str(doc.get("primary_image_cdn")),
        "indexed_at": indexed_at,
        "seed_category": seed_category,
        "metadata_json": json.dumps(metadata, ensure_ascii=False),
        "ogp_json": json.dumps(ogp, ensure_ascii=False),
    }


class UpsertRequest(BaseModel):
    docs: list[dict[str, Any]] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str
    offset: int = 0
    limit: int = 20
    vertical: str = "web"
    require_thumbnail: bool = False


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    tbl = _table()
    return {"status": "ok", "service": APP_NAME, "table": TABLE_NAME, "rows": tbl.count_rows()}


@app.post("/upsert")
def upsert(req: UpsertRequest) -> dict[str, Any]:
    if not req.docs:
        return {"upserted": 0, "table": TABLE_NAME}

    rows = [_normalize_doc(d) for d in req.docs]
    tbl = _table()
    tbl.merge_insert("doc_id").when_matched_update_all().when_not_matched_insert_all().execute(pa.Table.from_pylist(rows, schema=SCHEMA))
    return {"upserted": len(rows), "table": TABLE_NAME}


@app.post("/search")
def search(req: SearchRequest) -> dict[str, Any]:
    q = (req.query or "").strip().lower()
    if not q:
        return {"num_hits": 0, "hits": []}

    offset = max(0, int(req.offset))
    limit = max(1, min(100, int(req.limit)))
    vertical = (req.vertical or "web").strip().lower()

    rows = _table().to_arrow().to_pylist()
    scored: list[tuple[float, dict[str, Any]]] = []

    for r in rows:
        title = (r.get("title") or "")
        snippet = (r.get("snippet") or "")
        body = (r.get("text_content") or "")
        domain = (r.get("domain") or "")
        seed_category = (r.get("seed_category") or "")
        primary_image = (r.get("primary_image") or "")

        hay = f"{title} {snippet} {body}".lower()
        score = float(hay.count(q))
        if score <= 0:
            continue

        if vertical == "image":
            if not primary_image and seed_category != "image":
                continue
        elif vertical and vertical not in ("web", "webpage"):
            if seed_category != vertical and vertical not in domain:
                continue

        if q in title.lower():
            score += 2.0
        if q in snippet.lower():
            score += 1.0

        doc = {
            "doc_id": r.get("doc_id") or "",
            "result_id": r.get("result_id") or "",
            "job_id": r.get("job_id") or "",
            "url": r.get("url") or "",
            "domain": domain,
            "title": title,
            "snippet": snippet,
            "text_content": body,
            "status": int(r.get("status") or 0),
            "size_bytes": int(r.get("size_bytes") or 0),
            "link_count": int(r.get("link_count") or 0),
            "primary_image": primary_image,
            "primary_image_cdn": r.get("primary_image_cdn") or "",
            "language": r.get("language") or "",
            "seed_category": seed_category,
        }
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    total = len(scored)
    if total == 0:
        # Fallback: return recent/valid docs so web search doesn't become empty
        # when an exact substring match is not found.
        fallback: list[dict[str, Any]] = []
        for r in rows:
            title = (r.get("title") or "")
            snippet = (r.get("snippet") or "")
            body = (r.get("text_content") or "")
            domain = (r.get("domain") or "")
            seed_category = (r.get("seed_category") or "")
            primary_image = (r.get("primary_image") or "")
            if not title and not snippet and not body:
                continue
            if vertical == "image":
                if not primary_image and seed_category != "image":
                    continue
            elif vertical and vertical not in ("web", "webpage"):
                if seed_category != vertical and vertical not in domain:
                    continue
            fallback.append({
                "doc_id": r.get("doc_id") or "",
                "result_id": r.get("result_id") or "",
                "job_id": r.get("job_id") or "",
                "url": r.get("url") or "",
                "domain": domain,
                "title": title,
                "snippet": snippet,
                "text_content": body,
                "status": int(r.get("status") or 0),
                "size_bytes": int(r.get("size_bytes") or 0),
                "link_count": int(r.get("link_count") or 0),
                "primary_image": primary_image,
                "primary_image_cdn": r.get("primary_image_cdn") or "",
                "language": r.get("language") or "",
                "seed_category": seed_category,
            })
        fallback = fallback[offset: offset + limit]
        return {"num_hits": len(fallback), "hits": [{"_score": 0.1, "json": d} for d in fallback]}
    sliced = scored[offset: offset + limit]
    hits = [{"_score": s, "json": d} for s, d in sliced]
    return {"num_hits": total, "hits": hits}
