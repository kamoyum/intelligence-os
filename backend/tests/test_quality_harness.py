from intelligence_os.executive import plan
from intelligence_os.quality_harness import build_eval_profile


def test_light_for_low_risk_mechanical_task():
    p = plan("このメモを要約して整理して")
    assert p.eval_profile["level"] == "light"
    assert p.eval_profile["external_judge"] == "skip"


def test_standard_for_ordinary_comparison():
    p = plan("PCメモリは16GBと32GBどっちがいい？")
    assert p.eval_profile["level"] == "standard"
    assert p.autonomy == "augment"


def test_deep_for_financial_rule_decision():
    p = plan("NISAとiDeCoどっちを優先すべき？")
    assert p.eval_profile["level"] == "deep"
    assert p.eval_profile["require_primary_sources"] is True


def test_high_stakes_for_postoperative_health_question():
    p = plan("親知らず抜歯後、飲酒はいつからいい？")
    assert p.risk == "high"
    assert p.autonomy == "augment"
    assert p.eval_profile["level"] == "high_stakes"
    assert p.eval_profile["human_review"] == "decide"
    assert "verify" in p.skills


def test_deep_for_current_research():
    p = plan("最新のAI研究を調べてファクトチェックして")
    assert p.eval_profile["level"] == "deep"
    assert p.eval_profile["require_current_sources"] is True
    assert p.eval_profile["require_counterevidence"] is True


def test_secret_uses_highest_eval_and_never_weakens_safety():
    profile = build_eval_profile(
        "最新仕様 key=supersecretvalue",
        risk="low",
        cognitive_value="low",
        freshness="current",
        evidence_requirement="current_primary",
        skills=("memory_context", "research", "verify"),
        query_safety_level="secret",
    )
    assert profile.level == "high_stakes"
    assert profile.human_review == "decide"
    assert profile.verification_required is True
