from intelligence_os.skills import get_skill, list_skills


def test_core_skills_are_registered():
    ids = {s["id"] for s in list_skills()}
    assert {"memory_context", "organize", "research", "verify", "decision", "reflection", "brief"}.issubset(ids)


def test_decision_skill_keeps_human_role():
    s = get_skill("decision")
    assert s.default_automation == "augment"
    assert "final decision" in s.human_role.lower()
