#!/usr/bin/env python3
"""HTTP-level Outcome Learning simulation."""
from __future__ import annotations

import json
import os
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        os.environ["INTELLIGENCE_DATA_DIR"] = str(root / "data")
        os.environ["INTELLIGENCE_DB"] = str(root / "data" / "sim.db")
        os.environ["INTELLIGENCE_TOKEN_PATH"] = str(root / "data" / "token.txt")

        from fastapi.testclient import TestClient
        from intelligence_os.main import app
        from intelligence_os.security import API_TOKEN
        headers = {"Authorization": f"Bearer {API_TOKEN}"}

        with TestClient(app, base_url="http://127.0.0.1") as client:
            exp = client.post("/api/learning/expectations", headers=headers, json={
                "prediction_text": "Automation A will reduce processing time materially.",
                "expected_result": "At least 30% shorter processing time.",
                "confidence": 0.8,
            })
            exp.raise_for_status(); exp_id = exp.json()["id"]
            dec = client.post("/api/learning/decisions", headers=headers, json={
                "title": "Pilot A", "choice": "Use A", "rationale": "Expected efficiency", "expectation_id": exp_id,
            })
            dec.raise_for_status(); dec_id = dec.json()["id"]
            out = client.post("/api/learning/outcomes", headers=headers, json={
                "expectation_id": exp_id, "decision_id": dec_id,
                "observed_text": "Only 5% improvement; manual review stayed dominant.", "match_score": 0.2,
            })
            out.raise_for_status()
            ref = client.post(f"/api/learning/reflect/{exp_id}", headers=headers)
            ref.raise_for_status(); lesson = ref.json()
            accepted = client.post(f"/api/learning/lessons/{lesson['id']}", headers=headers, json={
                "accept": True, "human_note": "Measure the full workflow bottleneck before automating a sub-step."
            })
            accepted.raise_for_status(); accepted_j = accepted.json()
            detail = client.get(f"/api/learning/expectations/{exp_id}", headers=headers)
            detail.raise_for_status(); detail_j = detail.json()
            status = client.get("/api/learning/status", headers=headers)
            status.raise_for_status(); status_j = status.json()

        report = {
            "expectation": detail_j["status"],
            "lesson_status": accepted_j["status"],
            "memory_id": accepted_j["memory_id"],
            "outcome_mismatch": lesson["outcome_mismatch"], "surprise_score": lesson["surprise_score"],
            "learning_status": status_j,
            "pass_conditions": {
                "http_expectation_to_outcome": bool(detail_j["outcomes"]),
                "reflection_proposed": lesson["status"] == "proposed",
                "human_acceptance_closed_loop": accepted_j["status"] == "accepted" and accepted_j["memory_id"] is not None,
                "expectation_learned": detail_j["status"] == "learned",
            },
        }
        report["all_pass"] = all(report["pass_conditions"].values())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
