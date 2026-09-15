#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from intelligence_os.development_governance import evaluate_capability


def main() -> None:
    cases = [
        ("local_reversible_good", dict(capability="local_note", risk="low", external_side_effect=False, permission_expansion=False, reversible=True, eval_coverage=1, redteam_coverage=1, rollback_tested=True), "ELIGIBLE_FOR_BOUNDED_EXPANSION"),
        ("privacy_regression", dict(capability="research", risk="medium", external_side_effect=False, permission_expansion=False, reversible=True, eval_coverage=1, redteam_coverage=1, rollback_tested=True, privacy_regression=True), "HOLD"),
        ("external_write_unobserved", dict(capability="gmail_draft", risk="medium", external_side_effect=True, permission_expansion=False, reversible=True, eval_coverage=1, redteam_coverage=1, rollback_tested=True), "CONTAINED_ALPHA"),
        ("permission_expansion", dict(capability="grant_permission", risk="critical", external_side_effect=True, permission_expansion=True, reversible=False, eval_coverage=1, redteam_coverage=1, rollback_tested=False, observation_days=30, real_world_evidence=True), "HOLD"),
        ("weak_evals", dict(capability="new_skill", risk="medium", external_side_effect=False, permission_expansion=False, reversible=True, eval_coverage=.5, redteam_coverage=.4, rollback_tested=True), "CONTAINED_ALPHA"),
        ("external_observed", dict(capability="calendar_write_prototype", risk="medium", external_side_effect=True, permission_expansion=False, reversible=True, eval_coverage=1, redteam_coverage=1, rollback_tested=True, observation_days=30, real_world_evidence=True), "ELIGIBLE_FOR_BOUNDED_EXPANSION"),
    ]
    passed = 0
    for name, kwargs, expected in cases:
        got = evaluate_capability(**kwargs)["decision"]
        ok = got == expected
        print(f"{'PASS' if ok else 'FAIL'} {name}: {got} (expected {expected})")
        passed += int(ok)
    print(f"Development governance benchmark: {passed}/{len(cases)}")
    if passed != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
