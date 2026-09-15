from intelligence_os.development_governance import evaluate_capability, policy_snapshot


def test_policy_is_safety_limited_velocity():
    p = policy_snapshot()
    assert p["name"] == "safety_limited_velocity"
    assert p["max_new_authority_boundaries_per_release"] == 1
    assert p["freeze_on_privacy_regression"] is True


def test_local_reversible_capability_can_expand_when_evidence_is_good():
    r = evaluate_capability(
        capability="local_note",
        risk="low",
        external_side_effect=False,
        permission_expansion=False,
        reversible=True,
        eval_coverage=1.0,
        redteam_coverage=1.0,
        rollback_tested=True,
    )
    assert r["decision"] == "ELIGIBLE_FOR_BOUNDED_EXPANSION"
    assert r["authority"] == "bounded_auto"


def test_privacy_regression_freezes_release():
    r = evaluate_capability(
        capability="research",
        risk="medium",
        external_side_effect=False,
        permission_expansion=False,
        reversible=True,
        eval_coverage=1.0,
        redteam_coverage=1.0,
        rollback_tested=True,
        privacy_regression=True,
    )
    assert r["decision"] == "HOLD"
    assert "privacy_regression" in r["blockers"]


def test_external_write_requires_observation_and_real_world_evidence():
    r = evaluate_capability(
        capability="gmail_draft_write",
        risk="medium",
        external_side_effect=True,
        permission_expansion=False,
        reversible=True,
        eval_coverage=1.0,
        redteam_coverage=1.0,
        rollback_tested=True,
        observation_days=0,
        real_world_evidence=False,
    )
    assert r["decision"] == "CONTAINED_ALPHA"
    assert r["authority"] == "human_only"
    assert "no_real_world_evidence" in r["cautions"]


def test_permission_expansion_is_held():
    r = evaluate_capability(
        capability="admin_permission_change",
        risk="critical",
        external_side_effect=True,
        permission_expansion=True,
        reversible=False,
        eval_coverage=1.0,
        redteam_coverage=1.0,
        rollback_tested=False,
        observation_days=100,
        real_world_evidence=True,
    )
    assert r["decision"] == "HOLD"
    assert "permission_expansion_requires_separate_human_governance" in r["blockers"]
    assert "irreversible_autonomy_not_allowed" in r["blockers"]


def test_too_many_authority_boundaries_in_release_is_held():
    r = evaluate_capability(
        capability="multiple_connectors",
        risk="medium",
        external_side_effect=False,
        permission_expansion=False,
        reversible=True,
        eval_coverage=1.0,
        redteam_coverage=1.0,
        rollback_tested=True,
        new_authority_boundaries=2,
    )
    assert r["decision"] == "HOLD"


def test_capability_registry_separates_capability_from_authority():
    from intelligence_os.development_governance import capability_registry
    reg = {x["capability"]: x for x in capability_registry()}
    assert reg["create_local_note"]["state"] == "bounded_auto"
    assert reg["gmail_draft"]["state"] == "proposal_only"
    assert reg["email_send"]["authority"] == "human_only"
    assert reg["mobile_client"]["authority"] == "thin_client"
