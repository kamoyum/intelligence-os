from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings
from .storage import connect, update_fts, now_iso, daily_usage, record_usage
from .privacy import external_memory_allowed
from .query_safety import classify_query_safety


def tokenize(text: str) -> list[str]:
    ascii_words = re.findall(r"[A-Za-z0-9_]{2,}", text.lower())
    jp_runs = re.findall(r"[ぁ-んァ-ヶ一-龠]{2,}", text)
    chunks: list[str] = []
    for s in jp_runs:
        if len(s) <= 3:
            chunks.append(s)
        else:
            chunks.extend(s[i:i+3] for i in range(len(s)-2))
    # Preserve deterministic order while deduplicating.
    return list(dict.fromkeys(ascii_words + chunks))


def search_document(title: str, content: str, summary: str = "") -> str:
    tokens = tokenize(f"{title} {summary} {content}")
    return " ".join(tokens[:12000])


def index_memory(memory_id: int, title: str, content: str, summary: str = "", db_path: Path | None = None) -> None:
    update_fts(memory_id, search_document(title, content, summary), db_path)


def rebuild_fts(db_path: Path | None = None) -> int:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT id,title,content,summary FROM memories WHERE status='active'").fetchall()
    for r in rows:
        index_memory(int(r["id"]), r["title"], r["content"], r["summary"], db_path)
    return len(rows)


def _fts_candidates(query: str, candidate_limit: int, db_path: Path | None = None) -> list[dict[str, Any]]:
    q = tokenize(query)
    with connect(db_path) as conn:
        if not q:
            rows = conn.execute(
                "SELECT * FROM memories WHERE status='active' ORDER BY id DESC LIMIT ?", (candidate_limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        match = " OR ".join(f'"{t.replace(chr(34), "")}"' for t in q[:40])
        try:
            rows = conn.execute(
                """
                SELECT m.* FROM memories_fts f
                JOIN memories m ON m.id = CAST(f.memory_id AS INTEGER)
                WHERE f.search_text MATCH ? AND m.status='active'
                LIMIT ?
                """,
                (match, candidate_limit),
            ).fetchall()
            if rows:
                return [dict(r) for r in rows]
        except Exception:
            pass
        # Fallback uses indexed recent rows, not an unbounded full-table scan.
        rows = conn.execute(
            "SELECT * FROM memories WHERE status='active' ORDER BY id DESC LIMIT ?", (candidate_limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na*nb) if na and nb else 0.0


def _openai_client():
    if not (settings.openai_api_key and settings.embedding_model):
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=settings.openai_api_key)
    except Exception:
        return None


def _semantic_scores(query: str, candidates: list[dict[str, Any]], db_path: Path | None = None) -> dict[int, float]:
    if classify_query_safety(query).level != "safe":
        return {}
    client = _openai_client()
    model = settings.embedding_model
    # Embeddings are external transmission too. Only opted-in memories may leave the Core.
    candidates = [c for c in candidates if external_memory_allowed(c)]
    if client is None or not candidates:
        return {}
    used = daily_usage("embedding_inputs", db_path)
    remaining = max(0, settings.embedding_daily_inputs - used)
    if remaining < 1:
        return {}
    ids = [int(c["id"]) for c in candidates]
    cached: dict[int, list[float]] = {}
    with connect(db_path) as conn:
        placeholders = ",".join("?" for _ in ids)
        rows = conn.execute(
            f"SELECT memory_id,vector_json FROM memory_embeddings WHERE model=? AND memory_id IN ({placeholders})",
            [model, *ids],
        ).fetchall()
        for r in rows:
            cached[int(r["memory_id"])] = json.loads(r["vector_json"])
    missing = [c for c in candidates if int(c["id"]) not in cached]
    try:
        # Reserve one external input for the query vector. Each memory input is bounded to ~1800 chars.
        allowed_missing = missing[:max(0, remaining - 1)]
        if allowed_missing:
            texts = [f"{c['title']}\n{c['summary'] or c['content'][:1800]}"[:2000] for c in allowed_missing]
            resp = client.embeddings.create(model=model, input=texts)
            with connect(db_path) as conn:
                for c, item in zip(allowed_missing, resp.data):
                    vec = list(item.embedding)
                    cached[int(c["id"])] = vec
                    conn.execute(
                        "INSERT OR REPLACE INTO memory_embeddings(memory_id,model,vector_json,updated_at) VALUES (?,?,?,?)",
                        (int(c["id"]), model, json.dumps(vec), now_iso()),
                    )
            record_usage("embedding_inputs", len(allowed_missing), db_path)
            remaining -= len(allowed_missing)
        if remaining < 1:
            return {}
        qv = list(client.embeddings.create(model=model, input=[query[:2000]]).data[0].embedding)
        record_usage("embedding_inputs", 1, db_path)
        return {mid: max(0.0, _cosine(qv, vec)) for mid, vec in cached.items()}
    except Exception:
        return {}


def retrieve_memories(query: str, limit: int = 6, candidate_limit: int = 80, db_path: Path | None = None) -> list[dict[str, Any]]:
    candidates = _fts_candidates(query, candidate_limit, db_path)
    q = set(tokenize(query))
    semantic = _semantic_scores(query, candidates[:30], db_path)
    now = datetime.now(timezone.utc)
    scored: list[tuple[float, dict[str, Any]]] = []
    for c in candidates:
        text_tokens = set(tokenize(f"{c['title']} {c['summary']} {c['content'][:4000]}"))
        overlap = len(q & text_tokens) / max(1, len(q)) if q else 0.0
        try:
            age_days = max(0.0, (now - datetime.fromisoformat(c["created_at"])).total_seconds() / 86400)
        except Exception:
            age_days = 365.0
        recency = 1.0 / (1.0 + age_days / 30.0)
        semantic_score = semantic.get(int(c["id"]), 0.0)
        if semantic:
            score = overlap * 0.42 + semantic_score * 0.38 + float(c["importance"]) * 0.15 + recency * 0.05
        else:
            score = overlap * 0.70 + float(c["importance"]) * 0.22 + recency * 0.08
        if overlap > 0 or semantic_score > 0.30 or not q:
            c = dict(c)
            c["retrieval_score"] = round(score, 4)
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]
