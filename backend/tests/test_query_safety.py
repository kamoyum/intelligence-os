from intelligence_os.query_safety import classify_query_safety, redact_query_for_external
from intelligence_os.executive import plan
from intelligence_os.research import research_permission


def test_secret_blocks_external_research_even_when_explicit():
    p = plan('latest API docs for sk-abcdefghijklmnop123456')
    assert p.query_safety['level'] == 'secret'
    assert p.human_checkpoint == 'redact'
    assert research_permission(p.to_dict(), explicit=True, mode='auto_public') == (False, 'secret_redaction_required')


def test_sensitive_query_requires_confirmation():
    p = plan('患者の検査値について最新の情報を調べて')
    assert p.query_safety['level'] == 'sensitive'
    assert research_permission(p.to_dict(), mode='auto_public')[0] is False
    assert research_permission(p.to_dict(), explicit=True, mode='auto_public')[0] is True


def test_redaction_masks_email_and_secret():
    out = redact_query_for_external('mail me a@b.com key=supersecretvalue')
    assert 'a@b.com' not in out
    assert 'supersecretvalue' not in out
