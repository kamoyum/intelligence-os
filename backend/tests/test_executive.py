from intelligence_os.executive import plan


def test_low_value_organization_can_be_automated():
    p = plan("このメモを要約して一覧に整理して")
    assert p.autonomy == "auto"
    assert p.cognitive_value == "low"
    assert "organize" in p.skills


def test_high_value_decision_preserves_human_judgment():
    p = plan("研究テーマを比較してどちらを選ぶべきか判断したい")
    assert p.autonomy == "augment"
    assert p.cognitive_value == "high"
    assert "decision" in p.skills
    assert "verify" in p.skills


def test_high_risk_medical_task_is_not_fully_automated():
    p = plan("この患者の治療方針を判断して")
    assert p.risk == "high"
    assert p.autonomy == "augment"


def test_current_research_selects_research_and_verification():
    p = plan("最新のAI研究を調べてファクトチェックして")
    assert p.freshness == "current"
    assert "research" in p.skills
    assert "verify" in p.skills


def test_cognitive_mode_offloads_mechanical_work_but_collaborates_on_judgment():
    mechanical = plan("このメモを整理して一覧にして")
    judgment = plan("この研究仮説を比較して判断したい")
    assert mechanical.cognitive_mode == "offload"
    assert mechanical.human_first_prompt == ""
    assert judgment.cognitive_mode == "collaborate"
    assert "current hypothesis" in judgment.human_first_prompt


def test_critical_action_is_human_lead():
    p = plan("自動でメール送信して権限も増やして")
    assert p.autonomy == "human_only"
    assert p.cognitive_mode == "human_lead"
    assert p.human_checkpoint == "decide"
