from pathlib import Path

import pytest

from intelligence_os.research import (
    UnsafeURL,
    _parse_web_search_sources,
    _validate_public_url,
    research_claim,
    run_web_research,
    source_authority_hint,
)
from intelligence_os.storage import init_db, connect


def test_authority_hint_prefers_official():
    official, cls1 = source_authority_hint("https://www.mhlw.go.jp/stf/test.html")
    public, cls2 = source_authority_hint("https://example.com/post")
    assert official > public
    assert cls1 == "government_primary_hint"
    assert cls2 == "public_web"


def test_ssrf_blocks_loopback():
    with pytest.raises(UnsafeURL):
        _validate_public_url("http://127.0.0.1:8000/secret")


def test_parse_web_search_sources_recursively():
    payload = {
        "output": [
            {"type": "web_search_call", "action": {"sources": [
                {"url": "https://example.gov/rule", "title": "Official rule"},
                {"url": "https://example.com/article", "title": "Article"},
            ]}},
            {"type": "message", "content": [{"annotations": [
                {"type": "url_citation", "url": "https://example.gov/rule", "title": "Official rule"}
            ]}]},
        ]
    }
    sources = _parse_web_search_sources(payload)
    assert {s["url"] for s in sources} == {"https://example.gov/rule", "https://example.com/article"}


def test_research_claim_ingests_sources_and_verifies(tmp_path, monkeypatch):
    db = tmp_path / "research.db"
    init_db(db)

    def fake_search(query, max_sources):
        return (
            "Current official source says Alpha requires 2 sessions weekly.",
            [
                {"url": "https://rules.example.gov/alpha", "title": "Alpha Rule 2026"},
                {"url": "https://example.com/commentary", "title": "Commentary"},
            ],
            "fake_web_search",
        )

    def fake_fetch(url, **kwargs):
        if "rules.example.gov" in url:
            return "Alpha Rule 2026", "Alpha requires 2 sessions weekly. The prior 3-session rule is obsolete.", url
        return "Commentary", "Commentary discusses Alpha but does not define the requirement.", url

    import intelligence_os.research as research
    monkeypatch.setattr(research, "_web_search_openai", fake_search)
    monkeypatch.setattr(research, "fetch_public_source", fake_fetch)

    result = research_claim("Alpha requires 2 sessions weekly.", topic_key="alpha_sessions", db_path=db)
    assert result["sources_fetched"] == 2
    assert result["verification"]["status"] == "verified"
    assert result["verification"]["verification_scope"] == "web_retrieval+local_memory"
    assert result["citations"]

    with connect(db) as conn:
        run = conn.execute("SELECT * FROM research_runs").fetchone()
        memories = conn.execute("SELECT source_type,sensitivity,allow_external_llm FROM memories ORDER BY id").fetchall()
    assert run["provider"] == "fake_web_search"
    assert all(r["source_type"] == "web_research" for r in memories)
    assert all(r["sensitivity"] == "public" for r in memories)
    assert all(r["allow_external_llm"] == 1 for r in memories)


def test_research_permission_automates_low_medium_but_gates_high():
    from intelligence_os.research import research_permission
    assert research_permission({"skills": ["research"], "risk": "medium"}, mode="auto_public") == (True, "allowed")
    assert research_permission({"skills": ["research"], "risk": "high"}, mode="auto_public") == (False, "high_risk_confirmation_required")
    assert research_permission({"skills": ["research"], "risk": "high"}, explicit=True, mode="auto_public") == (True, "allowed")


def test_ssrf_blocks_credential_bearing_urls():
    with pytest.raises(UnsafeURL):
        _validate_public_url("https://user:pass@example.com/private")
