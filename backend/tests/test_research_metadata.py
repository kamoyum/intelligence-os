from intelligence_os.research import _HTMLTextExtractor, source_authority_hint
from intelligence_os.verification import _source_quality
from intelligence_os.storage import init_db, insert_memory
from intelligence_os.knowledge import register_provenance


def test_html_publication_date_extraction():
    p = _HTMLTextExtractor()
    p.feed('<html><head><meta property="article:published_time" content="2026-09-01T10:00:00Z"><title>X</title></head><body>Body</body></html>')
    assert p.published_at == '2026-09-01T10:00:00Z'


def test_source_classes_distinguish_government_and_vendor():
    g, gc = source_authority_hint('https://www.mhlw.go.jp/test')
    v, vc = source_authority_hint('https://openai.com/test')
    assert gc == 'government_primary_hint'
    assert vc == 'vendor_primary_hint'
    assert g > v


def test_vendor_quality_is_capped_for_normative_claim(tmp_path):
    db = tmp_path / 'v.db'
    init_db(db)
    mid, _ = insert_memory(source_type='web_research', source_key='x', title='Vendor', url='https://openai.com/x', content='Product A is best.', importance=.5, tags=[], summary='x', sensitivity='public', allow_external_llm=True, db_path=db)
    register_provenance(mid, title='Vendor', content='Product A is best.', url='https://openai.com/x', source_kind='web_research', publisher='openai.com', authority=.84, trust='vendor_primary_hint', db_path=db)
    q = _source_quality({'id': mid}, 'Product A is best and should be used.', db_path=db)
    assert q <= .62
