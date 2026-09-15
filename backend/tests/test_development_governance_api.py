from fastapi.testclient import TestClient

from intelligence_os.main import app
from intelligence_os.security import API_TOKEN


def headers():
    return {"Authorization": f"Bearer {API_TOKEN}"}


def test_development_governance_endpoint():
    with TestClient(app, base_url="http://127.0.0.1:8765") as c:
        r = c.get("/api/governance/development", headers=headers())
        assert r.status_code == 200
        assert r.json()["name"] == "safety_limited_velocity"


def test_capability_eval_holds_permission_expansion():
    with TestClient(app, base_url="http://127.0.0.1:8765") as c:
        r = c.post(
            "/api/governance/capability-eval",
            headers=headers(),
            json={
            "capability": "permission_change",
            "risk": "critical",
            "external_side_effect": True,
            "permission_expansion": True,
            "reversible": False,
            "eval_coverage": 1.0,
            "redteam_coverage": 1.0,
            "rollback_tested": False,
            "observation_days": 30,
            "real_world_evidence": True,
            },
        )
        assert r.status_code == 200
        assert r.json()["decision"] == "HOLD"
