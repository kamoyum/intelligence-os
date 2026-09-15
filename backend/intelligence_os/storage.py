from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(path: Path | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              source_type TEXT NOT NULL,
              source_key TEXT,
              title TEXT NOT NULL,
              url TEXT,
              content TEXT NOT NULL,
              importance REAL NOT NULL DEFAULT 0.5,
              tags TEXT NOT NULL DEFAULT '[]',
              summary TEXT NOT NULL DEFAULT '',
              status TEXT NOT NULL DEFAULT 'active',
              sensitivity TEXT NOT NULL DEFAULT 'private',
              allow_external_llm INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_memories_status_created ON memories(status, id DESC);
            CREATE INDEX IF NOT EXISTS idx_memories_source_key ON memories(source_type, source_key);
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(status, importance DESC);

            CREATE TABLE IF NOT EXISTS tasks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              kind TEXT NOT NULL,
              title TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'queued',
              payload TEXT NOT NULL DEFAULT '{}',
              result TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS approvals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              action_type TEXT NOT NULL,
              description TEXT NOT NULL,
              risk TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              payload TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS evals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              task_id INTEGER,
              method TEXT NOT NULL DEFAULT 'heuristic',
              accuracy REAL,
              groundedness REAL,
              relevance REAL,
              actionability REAL,
              calibration REAL,
              safety REAL,
              notes TEXT NOT NULL DEFAULT '',
              FOREIGN KEY(task_id) REFERENCES tasks(id)
            );
            CREATE TABLE IF NOT EXISTS audit_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              actor TEXT NOT NULL,
              action TEXT NOT NULL,
              target TEXT NOT NULL DEFAULT '',
              status TEXT NOT NULL,
              detail TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS external_usage (
              usage_date TEXT NOT NULL,
              capability TEXT NOT NULL,
              units INTEGER NOT NULL DEFAULT 0,
              PRIMARY KEY(usage_date, capability)
            );
            CREATE TABLE IF NOT EXISTS memory_embeddings (
              memory_id INTEGER NOT NULL,
              model TEXT NOT NULL,
              vector_json TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              PRIMARY KEY(memory_id, model),
              FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS provenance (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              memory_id INTEGER NOT NULL UNIQUE,
              source_kind TEXT NOT NULL DEFAULT 'captured',
              publisher TEXT,
              published_at TEXT,
              retrieved_at TEXT NOT NULL,
              authority REAL NOT NULL DEFAULT 0.5,
              trust TEXT NOT NULL DEFAULT 'untrusted_external',
              canonical_url TEXT,
              fingerprint TEXT NOT NULL,
              FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS claims (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              claim_text TEXT NOT NULL,
              topic_key TEXT,
              origin_memory_id INTEGER,
              origin_task_id INTEGER,
              status TEXT NOT NULL DEFAULT 'unverified',
              confidence REAL NOT NULL DEFAULT 0.0,
              verification_method TEXT NOT NULL DEFAULT 'none',
              verified_at TEXT,
              valid_from TEXT,
              valid_until TEXT,
              user_correction TEXT,
              superseded_by INTEGER,
              FOREIGN KEY(origin_memory_id) REFERENCES memories(id),
              FOREIGN KEY(origin_task_id) REFERENCES tasks(id),
              FOREIGN KEY(superseded_by) REFERENCES claims(id)
            );
            CREATE INDEX IF NOT EXISTS idx_claims_topic ON claims(topic_key,id DESC);
            CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status,id DESC);
            CREATE TABLE IF NOT EXISTS claim_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              claim_id INTEGER NOT NULL,
              previous_status TEXT NOT NULL,
              previous_confidence REAL NOT NULL,
              previous_method TEXT NOT NULL,
              previous_verified_at TEXT,
              FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS evidence (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              claim_id INTEGER NOT NULL,
              memory_id INTEGER NOT NULL,
              stance TEXT NOT NULL,
              score REAL NOT NULL,
              source_quality REAL NOT NULL,
              freshness REAL NOT NULL,
              directness REAL NOT NULL,
              excerpt TEXT NOT NULL,
              rationale TEXT NOT NULL,
              method TEXT NOT NULL,
              injection_risk INTEGER NOT NULL DEFAULT 0,
              FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE,
              FOREIGN KEY(memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence(claim_id,score DESC);
            CREATE TABLE IF NOT EXISTS contradictions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              claim_id INTEGER NOT NULL,
              evidence_id INTEGER NOT NULL,
              severity REAL NOT NULL,
              status TEXT NOT NULL DEFAULT 'open',
              FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE,
              FOREIGN KEY(evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS claim_relations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              from_claim_id INTEGER NOT NULL,
              to_claim_id INTEGER NOT NULL,
              relation TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'open',
              FOREIGN KEY(from_claim_id) REFERENCES claims(id) ON DELETE CASCADE,
              FOREIGN KEY(to_claim_id) REFERENCES claims(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS research_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              query TEXT NOT NULL,
              provider TEXT NOT NULL,
              status TEXT NOT NULL,
              sources_discovered INTEGER NOT NULL DEFAULT 0,
              sources_fetched INTEGER NOT NULL DEFAULT 0,
              summary TEXT NOT NULL DEFAULT '',
              error TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_research_runs_created ON research_runs(id DESC);
            CREATE TABLE IF NOT EXISTS goals (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT NOT NULL DEFAULT '',
              priority REAL NOT NULL DEFAULT 0.7,
              due_at TEXT,
              tags TEXT NOT NULL DEFAULT '[]',
              status TEXT NOT NULL DEFAULT 'active'
            );
            CREATE INDEX IF NOT EXISTS idx_goals_status_priority ON goals(status,priority DESC,id DESC);

            CREATE TABLE IF NOT EXISTS expectations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              prediction_text TEXT NOT NULL,
              expected_result TEXT NOT NULL,
              confidence REAL NOT NULL,
              due_at TEXT,
              origin_task_id INTEGER,
              status TEXT NOT NULL DEFAULT 'open',
              FOREIGN KEY(origin_task_id) REFERENCES tasks(id)
            );
            CREATE INDEX IF NOT EXISTS idx_expectations_status ON expectations(status,id DESC);
            CREATE TABLE IF NOT EXISTS decisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              title TEXT NOT NULL,
              choice TEXT NOT NULL,
              rationale TEXT NOT NULL DEFAULT '',
              expectation_id INTEGER,
              status TEXT NOT NULL DEFAULT 'active',
              FOREIGN KEY(expectation_id) REFERENCES expectations(id)
            );
            CREATE TABLE IF NOT EXISTS outcomes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              expectation_id INTEGER NOT NULL,
              decision_id INTEGER,
              observed_text TEXT NOT NULL,
              match_score REAL NOT NULL,
              observed_at TEXT NOT NULL,
              source TEXT NOT NULL DEFAULT 'human',
              FOREIGN KEY(expectation_id) REFERENCES expectations(id),
              FOREIGN KEY(decision_id) REFERENCES decisions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_outcomes_expectation ON outcomes(expectation_id,id DESC);
            CREATE TABLE IF NOT EXISTS lessons (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              expectation_id INTEGER NOT NULL,
              outcome_id INTEGER NOT NULL,
              lesson_text TEXT NOT NULL,
              proposed_rule TEXT NOT NULL DEFAULT '',
              calibration_error REAL NOT NULL DEFAULT 0.0,
              outcome_mismatch REAL NOT NULL DEFAULT 0.0,
              surprise_score REAL NOT NULL DEFAULT 0.0,
              status TEXT NOT NULL DEFAULT 'proposed',
              human_note TEXT NOT NULL DEFAULT '',
              decided_at TEXT,
              memory_id INTEGER,
              FOREIGN KEY(expectation_id) REFERENCES expectations(id),
              FOREIGN KEY(outcome_id) REFERENCES outcomes(id),
              FOREIGN KEY(memory_id) REFERENCES memories(id)
            );
            CREATE INDEX IF NOT EXISTS idx_lessons_status ON lessons(status,id DESC);
            CREATE TABLE IF NOT EXISTS skill_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              task_id INTEGER,
              skill_id TEXT NOT NULL,
              status TEXT NOT NULL,
              mode TEXT NOT NULL DEFAULT 'observed',
              executor TEXT,
              duration_ms INTEGER,
              metrics TEXT NOT NULL DEFAULT '{}',
              error TEXT NOT NULL DEFAULT '',
              FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_skill_runs_task ON skill_runs(task_id,id);
            CREATE INDEX IF NOT EXISTS idx_skill_runs_skill ON skill_runs(skill_id,status,id DESC);
            CREATE TABLE IF NOT EXISTS feedback_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              task_id INTEGER,
              signal TEXT NOT NULL,
              note TEXT NOT NULL DEFAULT '',
              FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_feedback_signal ON feedback_events(signal,id DESC);
            CREATE TABLE IF NOT EXISTS action_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              action_type TEXT NOT NULL,
              description TEXT NOT NULL,
              risk TEXT NOT NULL,
              mode TEXT NOT NULL,
              status TEXT NOT NULL,
              reversible INTEGER NOT NULL DEFAULT 0,
              external_side_effect INTEGER NOT NULL DEFAULT 0,
              payload TEXT NOT NULL DEFAULT '{}',
              result TEXT NOT NULL DEFAULT '{}',
              approval_id INTEGER,
              undo_payload TEXT NOT NULL DEFAULT '{}',
              undone_at TEXT,
              FOREIGN KEY(approval_id) REFERENCES approvals(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_action_runs_status ON action_runs(status,id DESC);
            """
        )
        # FTS is intentionally separate from raw content. Japanese is pre-tokenized by retrieval.py.
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(memory_id UNINDEXED, search_text, tokenize='unicode61')"
        )
        # Migration compatibility with v0.1 DBs.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(memories)")}
        if "source_key" not in cols:
            conn.execute("ALTER TABLE memories ADD COLUMN source_key TEXT")
        if "sensitivity" not in cols:
            conn.execute("ALTER TABLE memories ADD COLUMN sensitivity TEXT NOT NULL DEFAULT 'private'")
        if "allow_external_llm" not in cols:
            conn.execute("ALTER TABLE memories ADD COLUMN allow_external_llm INTEGER NOT NULL DEFAULT 0")
        lesson_cols = {r[1] for r in conn.execute("PRAGMA table_info(lessons)")}
        if "outcome_mismatch" not in lesson_cols:
            conn.execute("ALTER TABLE lessons ADD COLUMN outcome_mismatch REAL NOT NULL DEFAULT 0.0")
        if "surprise_score" not in lesson_cols:
            conn.execute("ALTER TABLE lessons ADD COLUMN surprise_score REAL NOT NULL DEFAULT 0.0")
        eval_cols = {r[1] for r in conn.execute("PRAGMA table_info(evals)")}
        if "method" not in eval_cols:
            conn.execute("ALTER TABLE evals ADD COLUMN method TEXT NOT NULL DEFAULT 'heuristic'")
        if "calibration" not in eval_cols:
            conn.execute("ALTER TABLE evals ADD COLUMN calibration REAL")


def clean_summary(content: str, max_chars: int = 420) -> str:
    text = re.sub(r"\s+", " ", content).strip()
    return text[:max_chars] + ("…" if len(text) > max_chars else "")


def insert_memory(
    *,
    source_type: str,
    title: str,
    content: str,
    url: str | None,
    importance: float,
    tags: list[str],
    summary: str,
    source_key: str | None = None,
    sensitivity: str = "private",
    allow_external_llm: bool = False,
    db_path: Path | None = None,
) -> tuple[int, bool]:
    with connect(db_path) as conn:
        if source_key:
            row = conn.execute(
                "SELECT id FROM memories WHERE source_type=? AND source_key=? AND status='active' ORDER BY id DESC LIMIT 1",
                (source_type, source_key),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE memories SET created_at=?,title=?,url=?,content=?,importance=?,tags=?,summary=?,sensitivity=?,allow_external_llm=? WHERE id=?",
                    (
                        now_iso(), title, url, content, importance,
                        json.dumps(tags, ensure_ascii=False), summary, sensitivity, int(bool(allow_external_llm)), row["id"],
                    ),
                )
                return int(row["id"]), False
        cur = conn.execute(
            "INSERT INTO memories(created_at,source_type,source_key,title,url,content,importance,tags,summary,sensitivity,allow_external_llm) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                now_iso(), source_type, source_key, title, url, content, importance,
                json.dumps(tags, ensure_ascii=False), summary, sensitivity, int(bool(allow_external_llm)),
            ),
        )
        return int(cur.lastrowid), True


def update_fts(memory_id: int, search_text: str, db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM memories_fts WHERE memory_id=?", (memory_id,))
        conn.execute("INSERT INTO memories_fts(memory_id,search_text) VALUES (?,?)", (memory_id, search_text))


def audit(action: str, status: str, *, actor: str = "core", target: str = "", detail: dict[str, Any] | None = None) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(created_at,actor,action,target,status,detail) VALUES (?,?,?,?,?,?)",
            (now_iso(), actor, action, target, status, json.dumps(detail or {}, ensure_ascii=False)),
        )


def daily_usage(capability: str, db_path: Path | None = None) -> int:
    day = datetime.now(timezone.utc).date().isoformat()
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT units FROM external_usage WHERE usage_date=? AND capability=?",
            (day, capability),
        ).fetchone()
    return int(row["units"]) if row else 0


def record_usage(capability: str, units: int, db_path: Path | None = None) -> None:
    if units <= 0:
        return
    day = datetime.now(timezone.utc).date().isoformat()
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO external_usage(usage_date,capability,units) VALUES(?,?,?) "
            "ON CONFLICT(usage_date,capability) DO UPDATE SET units=units+excluded.units",
            (day, capability, int(units)),
        )
