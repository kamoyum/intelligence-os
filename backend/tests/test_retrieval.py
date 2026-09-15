from pathlib import Path

from intelligence_os.retrieval import index_memory, retrieve_memories, tokenize
from intelligence_os.storage import init_db, insert_memory, clean_summary


def test_tokenize_japanese_and_ascii():
    tokens = tokenize("脳卒中の歩行 training guideline")
    assert "training" in tokens
    assert "guideline" in tokens
    assert any("脳卒" in t or "卒中" in t for t in tokens)


def test_fts_retrieval_finds_relevant_memory(tmp_path: Path):
    db = tmp_path / "test.db"
    init_db(db)
    items = [
        ("脳卒中歩行研究", "脳卒中患者の歩行訓練とバランスについての研究メモ"),
        ("AIニュース", "エージェントとハーネスエンジニアリングのニュース"),
        ("家計", "固定費と貯蓄の見直し"),
    ]
    for title, content in items:
        mid, _ = insert_memory(
            source_type="test", source_key=title, title=title, content=content, url=None,
            importance=0.6, tags=[], summary=clean_summary(content), db_path=db,
        )
        index_memory(mid, title, content, clean_summary(content), db)
    result = retrieve_memories("脳卒中 歩行", limit=2, db_path=db)
    assert result
    assert result[0]["title"] == "脳卒中歩行研究"


def test_source_key_upserts_instead_of_duplicating(tmp_path: Path):
    db = tmp_path / "test.db"
    init_db(db)
    a, created_a = insert_memory(
        source_type="web", source_key="https://example.com", title="A", content="old", url="https://example.com",
        importance=0.5, tags=[], summary="old", db_path=db,
    )
    b, created_b = insert_memory(
        source_type="web", source_key="https://example.com", title="A2", content="new", url="https://example.com",
        importance=0.6, tags=[], summary="new", db_path=db,
    )
    assert a == b
    assert created_a is True
    assert created_b is False
