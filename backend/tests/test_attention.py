from datetime import datetime, timedelta, timezone

from intelligence_os.attention import attention_items, create_goal, due_expectations, list_goals
from intelligence_os.retrieval import index_memory
from intelligence_os.storage import clean_summary, init_db, insert_memory
from intelligence_os.learning import create_expectation


def _memory(db, title, content, importance=0.5):
    mid, _ = insert_memory(
        source_type='test', source_key=title, title=title, url=None, content=content,
        importance=importance, tags=[], summary=clean_summary(content), db_path=db,
    )
    index_memory(mid, title, content, clean_summary(content), db_path=db)
    return mid


def test_attention_follows_human_goal(tmp_path):
    db = tmp_path / 'a.db'
    init_db(db)
    create_goal('脳卒中歩行研究', description='前脛骨筋と歩行', priority=1.0, db_path=db)
    _memory(db, '一般AIニュース', '新しいモデルのニュース', importance=0.9)
    target = _memory(db, '歩行研究', '脳卒中 歩行 前脛骨筋 研究メモ', importance=0.55)
    items = attention_items(5, db_path=db)
    assert items[0]['id'] == target
    assert items[0]['goal_relevance'] > 0
    assert any(x.startswith('goal:') for x in items[0]['why'])


def test_due_expectations_surface_overdue_and_due_soon(tmp_path):
    db = tmp_path / 'l.db'
    init_db(db)
    now = datetime.now(timezone.utc)
    create_expectation('A', 'B', 0.5, due_at=(now - timedelta(hours=1)).isoformat(), db_path=db)
    create_expectation('C', 'D', 0.5, due_at=(now + timedelta(hours=2)).isoformat(), db_path=db)
    create_expectation('E', 'F', 0.5, due_at=(now + timedelta(days=3)).isoformat(), db_path=db)
    due = due_expectations(include_upcoming_hours=24, db_path=db)
    assert [x['due_state'] for x in due] == ['overdue', 'due_soon']


def test_unified_attention_queue_prioritizes_conflict_and_overdue(tmp_path):
    from intelligence_os.attention import attention_queue
    from intelligence_os.storage import connect, now_iso
    db = tmp_path / 'q.db'
    init_db(db)
    _memory(db, '普通のメモ', '一般情報', importance=0.95)
    create_expectation('期限切れ予測', '結果', 0.7, due_at=(datetime.now(timezone.utc)-timedelta(hours=3)).isoformat(), db_path=db)
    with connect(db) as conn:
        conn.execute("INSERT INTO claims(created_at,claim_text,status,confidence,verification_method) VALUES(?,?,?,?,?)",
                     (now_iso(),'矛盾している重要Claim','contested',0.9,'test'))
    queue = attention_queue(5, db_path=db)
    types = [x['type'] for x in queue[:3]]
    assert 'knowledge_conflict' in types
    assert 'outcome_due' in types
