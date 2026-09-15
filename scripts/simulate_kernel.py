#!/usr/bin/env python3
"""Deterministic synthetic simulation of the v0.5-alpha knowledge lifecycle.

No internet, no external model, and no real medical/legal/financial facts are used.
The purpose is to test whether the OS *mechanism* works end-to-end.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from intelligence_os.executive import plan
from intelligence_os.knowledge import claim_detail, knowledge_status, register_provenance, supersede_claim
from intelligence_os.retrieval import index_memory
from intelligence_os.storage import clean_summary, init_db, insert_memory
from intelligence_os.verification import verify_claim


def capture(db: Path, key: str, text: str, published: str, authority: float) -> int:
    mid, _ = insert_memory(
        source_type="synthetic_official", source_key=key, title=key, content=text,
        url=f"https://synthetic.invalid/{key}", importance=0.85, tags=["simulation"],
        summary=clean_summary(text), allow_external_llm=False, db_path=db,
    )
    index_memory(mid, key, text, clean_summary(text), db)
    register_provenance(
        mid, title=key, content=text, url=f"https://synthetic.invalid/{key}", source_kind="synthetic_official",
        publisher="Synthetic Authority", published_at=published, authority=authority,
        trust="synthetic_untrusted", db_path=db,
    )
    return mid


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "simulation.db"
        init_db(db)

        executive = plan("最新のAlpha運用ルールを調べて、以前の知識と矛盾がないか確認して")
        capture(db, "Alpha rule 2025", "Alpha requires 3 sessions per week.", "2025-01-01T00:00:00+00:00", 0.90)
        old = verify_claim("Alpha requires 3 sessions per week.", topic_key="alpha.frequency", db_path=db)

        capture(db, "Alpha rule 2026", "Updated rule effective in 2026: Alpha requires 2 sessions per week. The previous 3-session rule is obsolete.", "2026-09-01T00:00:00+00:00", 0.98)
        old_recheck = verify_claim("Alpha requires 3 sessions per week.", topic_key="alpha.frequency", db_path=db)
        new = verify_claim("Alpha requires 2 sessions per week.", topic_key="alpha.frequency", db_path=db)

        # Human confirms the lifecycle transition rather than the OS silently rewriting history.
        supersede_claim(old["claim_id"], new["claim_id"], db_path=db)
        final_old = claim_detail(old["claim_id"], db_path=db)
        status = knowledge_status(db_path=db)

        report = {
            "simulation": "synthetic_only",
            "executive": {"autonomy": executive.autonomy, "skills": list(executive.skills), "freshness": executive.freshness},
            "phase_1_old_claim": {"status": old["status"], "confidence": old["confidence"]},
            "phase_2_old_claim_recheck": {"status": old_recheck["status"], "confidence": old_recheck["confidence"], "evidence": [(e["title"], e["stance"], e["score"]) for e in old_recheck["evidence"]]},
            "phase_3_new_claim": {"status": new["status"], "confidence": new["confidence"], "evidence": [(e["title"], e["stance"], e["score"]) for e in new["evidence"]]},
            "human_confirmed_supersession": {"old_claim_status": final_old["status"], "superseded_by": final_old["superseded_by"]},
            "knowledge_status": status,
            "pass_conditions": {
                "executive_selected_research_verify": "research" in executive.skills and "verify" in executive.skills,
                "old_claim_initially_supported": old["status"] == "verified",
                "new_source_creates_conflict": old_recheck["status"] in {"contested", "contradicted"},
                "new_claim_has_support": new["status"] in {"verified", "contested"},
                "human_controls_supersession": final_old["status"] == "superseded" and final_old["superseded_by"] == new["claim_id"],
            },
        }
        report["all_pass"] = all(report["pass_conditions"].values())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
