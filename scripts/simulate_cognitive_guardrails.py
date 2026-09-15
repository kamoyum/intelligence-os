#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from intelligence_os.attention import attention_items, create_goal, due_expectations
from intelligence_os.executive import plan
from intelligence_os.learning import create_expectation
from intelligence_os.query_safety import redact_query_for_external
from intelligence_os.research import research_permission
from intelligence_os.retrieval import index_memory
from intelligence_os.storage import clean_summary, init_db, insert_memory


def add_memory(db: Path, title: str, content: str, importance: float) -> int:
    mid, _ = insert_memory(source_type='sim', source_key=title, title=title, url=None, content=content,
                           importance=importance, tags=[], summary=clean_summary(content), db_path=db)
    index_memory(mid, title, content, clean_summary(content), db_path=db)
    return mid


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / 'sim.db'
        init_db(db)
        create_goal('脳卒中歩行研究', description='前脛骨筋と歩行', priority=1.0, db_path=db)
        unrelated = add_memory(db, '重要AIニュース', '新しいAIモデルのニュース', 0.92)
        related = add_memory(db, '歩行研究メモ', '脳卒中 歩行 前脛骨筋 研究', 0.58)
        attention = attention_items(2, db_path=db)

        secret_plan = plan('最新情報を調べて key=supersecretvalue')
        permission = research_permission(secret_plan.to_dict(), explicit=True, mode='auto_public')
        redacted = redact_query_for_external('contact user@example.com key=supersecretvalue')

        now = datetime.now(timezone.utc)
        create_expectation('Pilot should improve speed', '20% improvement', 0.7,
                           due_at=(now - timedelta(hours=2)).isoformat(), db_path=db)
        due = due_expectations(include_upcoming_hours=24, db_path=db)

        checks = {
            'goal_changes_attention': attention and attention[0]['id'] == related and related != unrelated,
            'secret_research_blocked_even_if_explicit': permission == (False, 'secret_redaction_required'),
            'secret_and_email_redacted': 'supersecretvalue' not in redacted and 'user@example.com' not in redacted,
            'overdue_outcome_surfaced': bool(due) and due[0]['due_state'] == 'overdue',
        }
        print({'attention': attention, 'permission': permission, 'redacted': redacted, 'due': due, 'pass_conditions': checks, 'all_pass': all(checks.values())})
        return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
