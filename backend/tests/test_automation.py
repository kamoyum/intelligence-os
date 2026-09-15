from intelligence_os.automation import action_policy


def test_low_risk_reversible_action_can_auto():
    p = action_policy(risk="low", reversible=True, external_side_effect=False)
    assert p["auto_execute"] is True
    assert p["approval_required"] is False


def test_external_side_effect_requires_approval():
    p = action_policy(risk="low", reversible=True, external_side_effect=True)
    assert p["auto_execute"] is False
    assert p["approval_required"] is True
