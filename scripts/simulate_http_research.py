#!/usr/bin/env python3
"""HTTP-level simulation for v0.5-beta research routing and verification."""
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
        os.environ["INTELLIGENCE_RESEARCH_MODE"] = "auto_public"

        import intelligence_os.research as research
        calls = {"search": 0}

        def fake_search(query: str, max_sources: int):
            calls["search"] += 1
            return (
                "Official 2026 source supports two sessions.",
                [{"url": "https://rules.example.gov/alpha", "title": "Official Alpha 2026"}],
                "http_simulation_search",
            )

        def fake_fetch(url: str, **kwargs):
            return "Official Alpha 2026", "Alpha requires 2 sessions per week.", url

        research._web_search_openai = fake_search
        research.fetch_public_source = fake_fetch

        from fastapi.testclient import TestClient
        from intelligence_os.main import app
        from intelligence_os.security import API_TOKEN

        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        with TestClient(app, base_url="http://127.0.0.1") as client:
            auto = client.post("/api/ask", headers=headers, json={"query": "最新のAlphaルールを調べて"})
            auto.raise_for_status()
            auto_j = auto.json()

            before_high = calls["search"]
            high = client.post("/api/ask", headers=headers, json={"query": "最新の患者治療ルールを調べて"})
            high.raise_for_status()
            high_j = high.json()
            after_high = calls["search"]

            explicit = client.post(
                "/api/ask", headers=headers,
                json={"query": "最新の患者治療ルールを調べて", "allow_external_research": True},
            )
            explicit.raise_for_status()
            explicit_j = explicit.json()

            verify = client.post(
                "/api/research/verify", headers=headers,
                json={"claim": "Alpha requires 2 sessions per week.", "topic_key": "alpha.frequency", "max_sources": 4},
            )
            verify.raise_for_status()
            verify_j = verify.json()

        report = {
            "auto_research": {
                "triggered": bool(auto_j.get("research")),
                "sources_fetched": (auto_j.get("research") or {}).get("sources_fetched"),
                "policy_risk": auto_j.get("executive_plan", {}).get("risk"),
            },
            "high_risk_gate": {
                "search_call_count_unchanged": before_high == after_high,
                "research_error": high_j.get("research_error"),
            },
            "explicit_high_risk": {
                "triggered": bool(explicit_j.get("research")),
            },
            "research_verify": {
                "status": verify_j.get("verification", {}).get("status"),
                "scope": verify_j.get("verification", {}).get("verification_scope"),
                "citations": len(verify_j.get("citations", [])),
            },
        }
        report["pass_conditions"] = {
            "low_medium_auto": report["auto_research"]["triggered"],
            "high_risk_requires_permission": report["high_risk_gate"]["search_call_count_unchanged"] and bool(report["high_risk_gate"]["research_error"]),
            "explicit_permission_unlocks": report["explicit_high_risk"]["triggered"],
            "current_source_verification": report["research_verify"]["status"] == "verified" and report["research_verify"]["scope"] == "web_retrieval+local_memory",
            "citations_present": report["research_verify"]["citations"] >= 1,
        }
        report["all_pass"] = all(report["pass_conditions"].values())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
