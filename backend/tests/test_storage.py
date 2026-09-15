from pathlib import Path

from intelligence_os.storage import clean_summary, init_db, connect, daily_usage, record_usage


def test_db_initializes_fts(tmp_path: Path):
    db = tmp_path / "x.db"
    init_db(db)
    with connect(db) as conn:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    assert "memories" in names
    assert "memories_fts" in names


def test_summary_is_bounded():
    s = clean_summary("a" * 1000, 100)
    assert len(s) <= 101
    assert s.endswith("…")


def test_external_usage_counter(tmp_path: Path):
    db = tmp_path / "usage.db"
    init_db(db)
    assert daily_usage("embedding_inputs", db) == 0
    record_usage("embedding_inputs", 3, db)
    record_usage("embedding_inputs", 2, db)
    assert daily_usage("embedding_inputs", db) == 5

def test_memory_privacy_columns_exist(tmp_path: Path):
    db = tmp_path / "privacy.db"
    init_db(db)
    with connect(db) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(memories)")}
    assert {"sensitivity", "allow_external_llm"}.issubset(cols)
