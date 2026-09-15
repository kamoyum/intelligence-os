from intelligence_os.evals import evaluate_answer, heuristic_evaluate


def test_heuristic_eval_is_labeled_and_bounded():
    out = heuristic_evaluate("次に公式資料を確認する必要があります。", [{"title":"x"}])
    assert out["method"] == "heuristic"
    for key in ["accuracy","groundedness","relevance","actionability","calibration","safety"]:
        assert 0 <= out[key] <= 1
    assert "does not fact-check" in out["notes"]


def test_adaptive_evals_light_skips_external_judge():
    out = evaluate_answer(
        "このメモを整理して",
        "整理しました。",
        [{"title": "x"}],
        eval_profile={"level": "light", "label": "Level 1 — Light", "external_judge": "skip"},
        allow_external=True,
    )
    assert out["method"] == "heuristic"
    assert out["eval_level"] == "light"
    assert "Level 1" in out["notes"]


def test_deep_eval_fallback_is_explicit_when_external_judge_unavailable():
    out = evaluate_answer(
        "最新情報を確認して",
        "追加検証が必要です。",
        [],
        eval_profile={"level": "deep", "label": "Level 3 — Deep", "external_judge": "preferred"},
        allow_external=False,
    )
    assert out["eval_level"] == "deep"
    assert "degraded" in out["notes"]
    assert "Verification layer" in out["notes"]
