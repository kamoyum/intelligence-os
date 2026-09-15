from __future__ import annotations

import asyncio
import json
import re
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlencode, urlparse

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import __version__
from .config import settings
from .actions import list_action_specs, list_actions, propose_action, undo_action
from .attention import attention_items, attention_queue, create_goal, due_expectations, list_goals, set_goal_status
from .connectors import google as google_connector
from .evals import evaluate_answer
from .executive import plan as executive_plan
from .knowledge import claim_detail, correct_claim, knowledge_status, register_provenance, supersede_claim
from .verification import verify_answer, verify_claim
from .skills import list_skills
from .llm import reason
from .learning import create_decision, create_expectation, decide_lesson, learning_detail, learning_status, propose_reflection, record_outcome
from .retrieval import index_memory, rebuild_fts, retrieve_memories
from .research import ResearchUnavailable, research_claim, research_permission, run_web_research
from .security import API_TOKEN, require_api_token
from .storage import audit, clean_summary, connect, init_db, insert_memory, now_iso
from .observability import feedback_summary, list_skill_runs, record_feedback, record_skill_run, system_evals
from .development_governance import capability_registry, evaluate_capability, policy_snapshot


def importance_score(title: str, content: str, url: str | None) -> float:
    text = f"{title} {content}".lower()
    score = 0.42
    if len(content) > 1000:
        score += 0.08
    if any(k in text for k in ["research", "study", "guideline", "論文", "研究", "ガイドライン", "重要", "deadline", "締切"]):
        score += 0.16
    if url and any(d in url for d in ["pubmed", "nature.com", "openai.com", "anthropic.com", "github.com"]):
        score += 0.10
    return min(score, 0.95)


class Capture(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    url: str | None = None
    content: str = Field(min_length=1, max_length=200_000)
    source_type: str = "web"
    source_key: str | None = None
    tags: list[str] = Field(default_factory=list)
    sensitivity: str = "private"
    allow_external_llm: bool = False
    source_kind: str = "captured"
    publisher: str | None = None
    published_at: str | None = None
    authority: float = Field(default=0.5, ge=0.0, le=1.0)
    trust: str = "untrusted_external"


class Ask(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)
    allow_external_research: bool = False
    allow_external_reasoning: bool = False


class PlanRequest(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)


class VerifyRequest(BaseModel):
    claim: str = Field(min_length=3, max_length=5000)
    topic_key: str | None = Field(default=None, max_length=300)


class ResearchVerifyRequest(BaseModel):
    claim: str = Field(min_length=3, max_length=5000)
    topic_key: str | None = Field(default=None, max_length=300)
    max_sources: int = Field(default=6, ge=1, le=12)


class ClaimCorrection(BaseModel):
    correction: str = Field(min_length=1, max_length=5000)


class SupersedeRequest(BaseModel):
    new_claim_id: int


class ApprovalCreate(BaseModel):
    action_type: str
    description: str
    risk: str = "medium"
    payload: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    approve: bool




class ExpectationCreate(BaseModel):
    prediction_text: str = Field(min_length=3, max_length=5000)
    expected_result: str = Field(min_length=1, max_length=5000)
    confidence: float = Field(ge=0.0, le=1.0)
    due_at: str | None = None
    origin_task_id: int | None = None


class DecisionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    choice: str = Field(min_length=1, max_length=5000)
    rationale: str = Field(default="", max_length=10000)
    expectation_id: int | None = None


class OutcomeCreate(BaseModel):
    expectation_id: int
    observed_text: str = Field(min_length=1, max_length=10000)
    match_score: float = Field(ge=0.0, le=1.0)
    decision_id: int | None = None
    observed_at: str | None = None


class LessonDecision(BaseModel):
    accept: bool
    human_note: str = Field(default="", max_length=5000)


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    priority: float = Field(default=0.7, ge=0.0, le=1.0)
    due_at: str | None = None
    tags: list[str] = Field(default_factory=list)


class GoalStatus(BaseModel):
    status: str


class FeedbackCreate(BaseModel):
    signal: str
    task_id: int | None = None
    note: str = Field(default="", max_length=2000)


class ActionProposal(BaseModel):
    action_type: str
    description: str = Field(default="", max_length=2000)
    payload: dict[str, Any] = Field(default_factory=dict)


class CapabilityGateRequest(BaseModel):
    capability: str = Field(min_length=1, max_length=200)
    risk: str = "medium"
    external_side_effect: bool = False
    permission_expansion: bool = False
    reversible: bool = True
    eval_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    redteam_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    rollback_tested: bool = False
    open_critical_incidents: int = Field(default=0, ge=0)
    privacy_regression: bool = False
    safety_benchmark_regression: bool = False
    observation_days: int = Field(default=0, ge=0)
    real_world_evidence: bool = False
    new_authority_boundaries: int = Field(default=0, ge=0)


class GoogleSyncRequest(BaseModel):
    calendar: bool = True
    drive: bool = True
    gmail: bool = False


async def consolidation_loop() -> None:
    while True:
        await asyncio.sleep(300)
        with connect() as conn:
            rows = conn.execute(
                "SELECT id,title,content,summary FROM memories WHERE status='active' AND (summary='' OR summary IS NULL) ORDER BY id DESC LIMIT 20"
            ).fetchall()
            for r in rows:
                summary = clean_summary(r["content"])
                conn.execute("UPDATE memories SET summary=? WHERE id=?", (summary, r["id"]))
                index_memory(int(r["id"]), r["title"], r["content"], summary)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rebuild_fts()
    print(f"Intelligence OS v{__version__} Core: {settings.core_origin}")
    if urlparse(settings.core_origin).hostname in {"127.0.0.1", "localhost", "::1"}:
        print("Local API token is available via /setup on loopback only; it is not printed to logs.")
    else:
        print("Non-loopback Core origin detected: /setup is disabled.")
    task = asyncio.create_task(consolidation_loop())
    yield
    task.cancel()


app = FastAPI(title="Intelligence OS Core", version=__version__, lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "::1"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.core_origin, "http://localhost:8765"],
    allow_origin_regex=r"^chrome-extension://[a-z]+$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Intelligence-Token"],
)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "version": __version__,
        "time": now_iso(),
        "reasoning": settings.model or "mock",
        "eval": settings.eval_model or settings.model or "heuristic",
        "semantic_retrieval": bool(settings.embedding_model and settings.openai_api_key),
        "external_llm_mode": settings.external_llm_mode,
        "embedding_daily_inputs": settings.embedding_daily_inputs,
        "kernel": ["memory", "context", "attention", "executive", "skills", "adaptive_evals", "verification", "governance", "outcome", "learning"],
        "verification_scope": "local_memory+optional_current_web",
        "research": {"mode": settings.research_mode, "model": settings.research_model or settings.model or "not_configured", "daily_cap": settings.web_search_daily_queries},
        "knowledge_lifecycle": ["provenance", "claims", "evidence", "contradictions", "correction", "supersession"],
        "outcome_learning": ["expectation", "decision", "outcome", "due_followup", "reflection", "human_acceptance"],
        "cognitive_guardrails": ["goal_aware_attention", "query_safety", "external_reasoning_gate", "secret_redaction"],
        "development_governance": {"policy": "safety_limited_velocity", "authority_expansion": "evidence_gated"},
    }


@app.get("/setup", response_class=HTMLResponse)
def setup_page():
    if urlparse(settings.core_origin).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise HTTPException(403, "Setup token display is disabled for non-loopback Core origins")
    token = API_TOKEN
    return HTMLResponse(f"""<!doctype html><html lang='ja'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Intelligence OS Setup</title>
    <style>body{{font-family:system-ui;max-width:760px;margin:40px auto;padding:20px;background:#0d1117;color:#e6edf3}}code{{display:block;padding:14px;background:#161b22;border:1px solid #30363d;border-radius:10px;word-break:break-all}}a{{color:#58a6ff}}</style>
    <h1>Intelligence OS v{__version__}</h1><p>Chrome拡張のOptionsに、以下のローカルAPIトークンを設定してください。</p><code>{token}</code>
    <p>このトークンは <b>ローカルCore専用</b> です。GitHubや公開チャットへ貼らないでください。</p><p><a href='/console'>Consoleを開く</a></p></html>""", headers={"Cache-Control":"no-store"})


def auth(_: None = Depends(require_api_token)) -> None:
    return None


@app.post("/api/capture")
def capture(item: Capture, _: None = Depends(require_api_token)):
    imp = importance_score(item.title, item.content, item.url)
    summary = clean_summary(item.content)
    source_key = item.source_key or item.url
    mid, created = insert_memory(
        source_type=item.source_type,
        source_key=source_key,
        title=item.title,
        url=item.url,
        content=item.content,
        importance=imp,
        tags=item.tags,
        summary=summary,
        sensitivity=item.sensitivity,
        allow_external_llm=item.allow_external_llm,
    )
    index_memory(mid, item.title, item.content, summary)
    provenance_id = register_provenance(
        mid, title=item.title, content=item.content, url=item.url, source_kind=item.source_kind,
        publisher=item.publisher, published_at=item.published_at, authority=item.authority, trust=item.trust,
    )
    audit("memory.capture", "created" if created else "updated", actor="extension", target=str(mid), detail={"source_type": item.source_type, "provenance_id": provenance_id})
    return {"id": mid, "created": created, "importance": imp, "summary": summary, "provenance_id": provenance_id}


@app.post("/api/plan")
def plan_task(req: PlanRequest, _: None = Depends(require_api_token)):
    return executive_plan(req.query).to_dict()


@app.get("/api/skills")
def skills(_: None = Depends(require_api_token)):
    return list_skills()


@app.post("/api/ask")
def ask(req: Ask, _: None = Depends(require_api_token)):
    plan = executive_plan(req.query).to_dict()
    research = None
    research_error = None
    may_research, research_policy = research_permission(plan, explicit=req.allow_external_research)
    if may_research:
        try:
            research = run_web_research(req.query)
        except ResearchUnavailable as exc:
            research_error = str(exc)
    elif "research" in plan.get("skills", []) and research_policy == "high_risk_confirmation_required":
        research_error = "External research withheld: high-risk query requires explicit allow_external_research=true."
    elif "research" in plan.get("skills", []) and research_policy == "research_mode_off":
        research_error = "External research is disabled by INTELLIGENCE_RESEARCH_MODE."

    memories = retrieve_memories(req.query, 7)
    query_safety = (plan.get("query_safety") or {}).get("level", "safe")
    external_reasoning_allowed = query_safety == "safe" or (query_safety == "sensitive" and req.allow_external_reasoning)
    reasoning = reason(req.query, memories, plan, allow_external=external_reasoning_allowed)
    ev = evaluate_answer(req.query, reasoning["answer"], memories, eval_profile=plan.get("eval_profile"), allow_external=external_reasoning_allowed)
    payload = {"query": req.query, "executive_plan": plan}
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks(created_at,kind,title,status,payload,result) VALUES(?,?,?,?,?,?)",
            (now_iso(), "ask", req.query[:160], "running", json.dumps(payload, ensure_ascii=False), "{}"),
        )
        task_id = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO evals(created_at,task_id,method,accuracy,groundedness,relevance,actionability,calibration,safety,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                now_iso(), task_id, ev["method"], ev["accuracy"], ev["groundedness"], ev["relevance"],
                ev["actionability"], ev["calibration"], ev["safety"], ev["notes"],
            ),
        )
    verification = None
    if "verify" in plan.get("skills", []):
        verification = verify_answer(reasoning["answer"], origin_task_id=task_id)
        # Each claim reports its own scope based on the evidence actually used. Merely running a
        # web search must not relabel unrelated claims as web-verified.
    result = {**reasoning, "executive_plan": plan, "research": research, "research_error": research_error, "verification": verification}
    with connect() as conn:
        conn.execute(
            "UPDATE tasks SET status='done',result=? WHERE id=?",
            (json.dumps(result, ensure_ascii=False), task_id),
        )
    audit(
        "task.ask", "done", target=str(task_id),
        detail={
            "eval_method": ev["method"], "autonomy": plan["autonomy"], "skills": plan["skills"],
            "query_safety": query_safety, "external_reasoning_allowed": external_reasoning_allowed,
            "verification_claims": (verification or {}).get("claims_checked", 0), "research_run_id": (research or {}).get("research_run_id"),
        },
    )
    skill_run_ids: list[int] = []
    skill_run_ids.append(record_skill_run(
        "memory_context", status="done", task_id=task_id, mode="auto", executor="retrieval.retrieve_memories",
        metrics={"retrieved": len(memories), "shared_external": reasoning.get("privacy", {}).get("shared_with_external_llm", 0)},
    ))
    if "research" in plan.get("skills", []):
        if research:
            skill_run_ids.append(record_skill_run(
                "research", status="done", task_id=task_id, mode=plan.get("autonomy", "augment"), executor="research.run_web_research",
                metrics={"sources_fetched": research.get("sources_fetched", 0), "research_run_id": research.get("research_run_id")},
            ))
        else:
            skill_run_ids.append(record_skill_run(
                "research", status="withheld" if research_error else "skipped", task_id=task_id, mode=plan.get("autonomy", "augment"),
                executor="research.run_web_research", metrics={"policy": research_policy}, error=research_error or "",
            ))
    if "verify" in plan.get("skills", []):
        skill_run_ids.append(record_skill_run(
            "verify", status="done" if verification is not None else "skipped", task_id=task_id, mode="augment", executor="verification.verify_answer",
            metrics={"claims_checked": (verification or {}).get("claims_checked", 0), "status_counts": (verification or {}).get("status_counts", {})},
        ))
    for sid in ("organize", "decision", "reflection"):
        if sid in plan.get("skills", []):
            skill_run_ids.append(record_skill_run(
                sid, status="assisted", task_id=task_id, mode="augment" if plan.get("autonomy") != "auto" else "auto",
                executor="reasoning", metrics={"reasoning_mode": reasoning.get("mode", "unknown")},
            ))
    return {
        "task_id": task_id,
        **reasoning,
        "executive_plan": plan,
        "research": research,
        "research_error": research_error,
        "verification": verification,
        "eval": ev,
        "skill_run_ids": skill_run_ids,
        "memories": [
            {"id": m["id"], "title": m["title"], "url": m["url"], "retrieval_score": m.get("retrieval_score")}
            for m in memories
        ],
    }


@app.post("/api/verify")
def verify(req: VerifyRequest, _: None = Depends(require_api_token)):
    result = verify_claim(req.claim, topic_key=req.topic_key)
    audit("knowledge.verify", result["status"], target=str(result["claim_id"]), detail={"topic_key": req.topic_key, "scope": result["verification_scope"]})
    return result


@app.post("/api/research/verify")
def research_verify(req: ResearchVerifyRequest, _: None = Depends(require_api_token)):
    try:
        result = research_claim(req.claim, topic_key=req.topic_key, max_sources=req.max_sources)
    except ResearchUnavailable as exc:
        audit("research.verify", "unavailable", target=req.claim[:120], detail={"error": str(exc)})
        raise HTTPException(503, str(exc))
    audit(
        "research.verify", result["verification"]["status"],
        target=str(result["verification"]["claim_id"]),
        detail={"topic_key": req.topic_key, "run_id": result["research_run_id"], "sources_fetched": result["sources_fetched"]},
    )
    return result


@app.get("/api/research/runs")
def research_runs(limit: int = 30, _: None = Depends(require_api_token)):
    with connect() as conn:
        rows = conn.execute(
            "SELECT id,created_at,query,provider,status,sources_discovered,sources_fetched,summary,error FROM research_runs ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 100)),),
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/claims")
def claims(limit: int = 50, _: None = Depends(require_api_token)):
    with connect() as conn:
        rows = conn.execute(
            "SELECT id,created_at,claim_text,topic_key,status,confidence,verification_method,verified_at,user_correction,superseded_by FROM claims ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 200)),),
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: int, _: None = Depends(require_api_token)):
    row = claim_detail(claim_id)
    if not row:
        raise HTTPException(404, "Claim not found")
    return row


@app.post("/api/claims/{claim_id}/correct")
def claim_correction(claim_id: int, req: ClaimCorrection, _: None = Depends(require_api_token)):
    try:
        correct_claim(claim_id, req.correction)
    except KeyError:
        raise HTTPException(404, "Claim not found")
    audit("knowledge.correct", "corrected", actor="human", target=str(claim_id))
    return {"id": claim_id, "status": "corrected"}


@app.post("/api/claims/{claim_id}/supersede")
def claim_supersede(claim_id: int, req: SupersedeRequest, _: None = Depends(require_api_token)):
    try:
        supersede_claim(claim_id, req.new_claim_id)
    except KeyError:
        raise HTTPException(404, "Claim not found")
    audit("knowledge.supersede", "confirmed", actor="human", target=str(claim_id), detail={"new_claim_id": req.new_claim_id})
    return {"id": claim_id, "status": "superseded", "superseded_by": req.new_claim_id}


@app.get("/api/knowledge/status")
def knowledge_integrity(_: None = Depends(require_api_token)):
    return knowledge_status()


@app.post("/api/learning/expectations")
def learning_expectation(req: ExpectationCreate, _: None = Depends(require_api_token)):
    eid = create_expectation(req.prediction_text, req.expected_result, req.confidence, due_at=req.due_at, origin_task_id=req.origin_task_id)
    audit("learning.expectation", "created", actor="human", target=str(eid), detail={"confidence": req.confidence})
    return {"id": eid, "status": "open"}


@app.post("/api/learning/decisions")
def learning_decision(req: DecisionCreate, _: None = Depends(require_api_token)):
    try:
        did = create_decision(req.title, req.choice, rationale=req.rationale, expectation_id=req.expectation_id)
    except KeyError:
        raise HTTPException(404, "Expectation not found")
    audit("learning.decision", "recorded", actor="human", target=str(did), detail={"expectation_id": req.expectation_id})
    return {"id": did, "status": "active"}


@app.post("/api/learning/outcomes")
def learning_outcome(req: OutcomeCreate, _: None = Depends(require_api_token)):
    try:
        oid = record_outcome(req.expectation_id, req.observed_text, req.match_score, decision_id=req.decision_id, observed_at=req.observed_at)
    except KeyError:
        raise HTTPException(404, "Expectation or decision not found")
    audit("learning.outcome", "recorded", actor="human", target=str(oid), detail={"expectation_id": req.expectation_id, "match_score": req.match_score})
    return {"id": oid, "expectation_id": req.expectation_id}


@app.post("/api/learning/reflect/{expectation_id}")
def learning_reflect(expectation_id: int, _: None = Depends(require_api_token)):
    try:
        lesson = propose_reflection(expectation_id)
    except KeyError:
        raise HTTPException(404, "Expectation not found")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    audit("learning.reflect", "proposed", target=str(lesson["id"]), detail={"expectation_id": expectation_id})
    return lesson


@app.post("/api/learning/lessons/{lesson_id}")
def learning_lesson_decision(lesson_id: int, req: LessonDecision, _: None = Depends(require_api_token)):
    try:
        lesson = decide_lesson(lesson_id, accept=req.accept, human_note=req.human_note)
    except KeyError:
        raise HTTPException(404, "Lesson not found")
    audit("learning.lesson", lesson["status"], actor="human", target=str(lesson_id), detail={"memory_id": lesson.get("memory_id")})
    return lesson


@app.get("/api/learning/expectations/{expectation_id}")
def learning_expectation_detail(expectation_id: int, _: None = Depends(require_api_token)):
    result = learning_detail(expectation_id)
    if not result:
        raise HTTPException(404, "Expectation not found")
    return result


@app.get("/api/learning/status")
def learning_status_api(_: None = Depends(require_api_token)):
    return learning_status()


@app.get("/api/memories")
def memories(limit: int = 30, _: None = Depends(require_api_token)):
    limit = max(1, min(limit, 100))
    with connect() as conn:
        rows = conn.execute(
            "SELECT id,created_at,source_type,title,url,importance,tags,summary FROM memories WHERE status='active' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/attention")
def attention(limit: int = 8, _: None = Depends(require_api_token)):
    return attention_items(limit=limit)


@app.get("/api/attention/queue")
def attention_unified(limit: int = 12, _: None = Depends(require_api_token)):
    return attention_queue(limit=limit)


@app.get("/api/system/evals")
def system_evals_endpoint(_: None = Depends(require_api_token)):
    return system_evals()


@app.get("/api/skills/runs")
def skill_runs_endpoint(limit: int = 100, _: None = Depends(require_api_token)):
    return list_skill_runs(limit=limit)


@app.post("/api/feedback")
def feedback_create(req: FeedbackCreate, _: None = Depends(require_api_token)):
    try:
        fid = record_feedback(req.signal, task_id=req.task_id, note=req.note)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except KeyError:
        raise HTTPException(404, "Task not found")
    audit("feedback.record", req.signal, actor="human", target=str(req.task_id or ""))
    return {"id": fid, "signal": req.signal}


@app.get("/api/feedback/summary")
def feedback_summary_endpoint(_: None = Depends(require_api_token)):
    return feedback_summary()


@app.get("/api/governance/development")
def development_governance(_: None = Depends(require_api_token)):
    return policy_snapshot()


@app.post("/api/governance/capability-eval")
def development_capability_eval(req: CapabilityGateRequest, _: None = Depends(require_api_token)):
    result = evaluate_capability(**req.model_dump())
    audit("governance.capability_eval", result["decision"].lower(), actor="human", target=req.capability, detail={"authority": result["authority"], "blockers": result["blockers"], "cautions": result["cautions"]})
    return result


@app.get("/api/governance/capabilities")
def development_capabilities(_: None = Depends(require_api_token)):
    return capability_registry()


@app.get("/api/actions/specs")
def actions_specs(_: None = Depends(require_api_token)):
    return list_action_specs()


@app.get("/api/actions")
def actions_list(limit: int = 100, _: None = Depends(require_api_token)):
    return list_actions(limit=limit)


@app.post("/api/actions/propose")
def actions_propose(req: ActionProposal, _: None = Depends(require_api_token)):
    try:
        result = propose_action(req.action_type, req.description or req.action_type, req.payload)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit("action.propose", result["status"], actor="human", target=str(result["id"]), detail={"action_type": req.action_type, "approval_id": result.get("approval_id")})
    return result


@app.post("/api/actions/{action_id}/undo")
def actions_undo(action_id: int, _: None = Depends(require_api_token)):
    try:
        result = undo_action(action_id)
    except KeyError:
        raise HTTPException(404, "Action not found")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    audit("action.undo", "undone", actor="human", target=str(action_id))
    return result


@app.post("/api/goals")
def goals_create(req: GoalCreate, _: None = Depends(require_api_token)):
    gid = create_goal(req.title, description=req.description, priority=req.priority, due_at=req.due_at, tags=req.tags)
    audit("goal.create", "active", actor="human", target=str(gid), detail={"priority": req.priority, "due_at": req.due_at})
    return {"id": gid, "status": "active"}


@app.get("/api/goals")
def goals_list(include_inactive: bool = False, _: None = Depends(require_api_token)):
    return list_goals(include_inactive=include_inactive)


@app.post("/api/goals/{goal_id}/status")
def goals_status(goal_id: int, req: GoalStatus, _: None = Depends(require_api_token)):
    try:
        set_goal_status(goal_id, req.status)
    except KeyError:
        raise HTTPException(404, "Goal not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit("goal.status", req.status, actor="human", target=str(goal_id))
    return {"id": goal_id, "status": req.status}


@app.get("/api/learning/due")
def learning_due(hours: int = 24, _: None = Depends(require_api_token)):
    return due_expectations(include_upcoming_hours=max(0, min(hours, 24 * 30)))


@app.get("/api/brief")
def brief(_: None = Depends(require_api_token)):
    with connect() as conn:
        approvals = conn.execute("SELECT id,action_type,description,risk FROM approvals WHERE status='pending' ORDER BY id DESC LIMIT 10").fetchall()
        tasks = conn.execute("SELECT id,kind,title,status FROM tasks ORDER BY id DESC LIMIT 10").fetchall()
    important = attention_items(limit=5)
    queue = attention_queue(limit=8)
    goals = list_goals()
    due = due_expectations(include_upcoming_hours=24)
    kstatus = knowledge_status()
    lstatus = learning_status()
    overdue = sum(1 for x in due if x.get("due_state") == "overdue")
    return {
        "generated_at": now_iso(),
        "attention": important,
        "attention_queue": queue,
        "active_goals": goals,
        "outcomes_due": due,
        "pending_approvals": [dict(r) for r in approvals],
        "recent_tasks": [dict(r) for r in tasks],
        "knowledge": kstatus,
        "learning": lstatus,
        "headline": f"注目 {len(important)}件 / Active goals {len(goals)}件 / Outcome overdue {overdue}件 / 承認待ち {len(approvals)}件",
    }


@app.post("/api/approvals")
def create_approval(req: ApprovalCreate, _: None = Depends(require_api_token)):
    if req.risk not in {"low", "medium", "high", "critical"}:
        raise HTTPException(400, "risk must be low/medium/high/critical")
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO approvals(created_at,action_type,description,risk,status,payload) VALUES(?,?,?,?,?,?)",
            (now_iso(), req.action_type, req.description, req.risk, "pending", json.dumps(req.payload, ensure_ascii=False)),
        )
        aid = int(cur.lastrowid)
    audit("approval.create", "pending", target=str(aid), detail={"risk": req.risk, "action_type": req.action_type})
    return {"id": aid, "status": "pending"}


@app.get("/api/approvals")
def list_approvals(_: None = Depends(require_api_token)):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM approvals ORDER BY id DESC LIMIT 50").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/approvals/{approval_id}")
def decide_approval(approval_id: int, req: ApprovalDecision, _: None = Depends(require_api_token)):
    status = "approved" if req.approve else "rejected"
    with connect() as conn:
        cur = conn.execute("UPDATE approvals SET status=? WHERE id=? AND status='pending'", (status, approval_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Pending approval not found")
    audit("approval.decide", status, actor="human", target=str(approval_id))
    return {"id": approval_id, "status": status, "note": "v0.7.2-alpha records the decision; high-risk external side effects remain disabled."}


@app.get("/api/audit")
def audit_log(limit: int = 100, _: None = Depends(require_api_token)):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/connectors/google/status")
def google_status(_: None = Depends(require_api_token)):
    return google_connector.status()


@app.post("/api/connectors/google/start")
def google_start(_: None = Depends(require_api_token)):
    try:
        return {"authorization_url": google_connector.start_oauth()}
    except Exception as exc:
        raise HTTPException(400, str(exc))


@app.get("/oauth/google/callback")
def google_callback(request: Request, state: str):
    try:
        google_connector.finish_oauth(str(request.url), state)
        audit("connector.google.oauth", "connected", actor="human")
        return RedirectResponse(url="/console?google=connected")
    except Exception as exc:
        return HTMLResponse(f"Google OAuth failed: {type(exc).__name__}: {exc}", status_code=400)


@app.post("/api/connectors/google/sync")
def google_sync(req: GoogleSyncRequest, _: None = Depends(require_api_token)):
    stats = {"calendar": 0, "drive": 0, "gmail": 0}
    try:
        if req.calendar:
            for e in google_connector.list_calendar():
                content = "\n".join(filter(None, [f"Start: {e['start']}", f"End: {e['end']}", e.get("location", ""), e.get("description", "")]))
                mid, _ = insert_memory(
                    source_type="google_calendar", source_key=e.get("id"), title=e.get("summary", "Calendar event"),
                    url=e.get("htmlLink"), content=content or e.get("summary", "Calendar event"), importance=0.70,
                    tags=["google", "calendar"], summary=clean_summary(content or e.get("summary", "")),
                    sensitivity="personal", allow_external_llm=False,
                )
                index_memory(mid, e.get("summary", ""), content, clean_summary(content))
                register_provenance(mid, title=e.get("summary", "Calendar event"), content=content, url=e.get("htmlLink"), source_kind="google_calendar", publisher="Google Calendar", published_at=e.get("start"), authority=0.5, trust="private_connector")
                stats["calendar"] += 1
        if req.drive:
            for f in google_connector.list_drive():
                content = "\n".join(filter(None, [f"MIME: {f.get('mimeType','')}", f"Modified: {f.get('modifiedTime','')}", f.get("description", "")]))
                mid, _ = insert_memory(
                    source_type="google_drive", source_key=f.get("id"), title=f.get("name", "Drive file"),
                    url=f.get("webViewLink"), content=content or f.get("name", "Drive file"), importance=0.58,
                    tags=["google", "drive"], summary=clean_summary(content or f.get("name", "")),
                    sensitivity="personal", allow_external_llm=False,
                )
                index_memory(mid, f.get("name", ""), content, clean_summary(content))
                register_provenance(mid, title=f.get("name", "Drive file"), content=content, url=f.get("webViewLink"), source_kind="google_drive", publisher="Google Drive", published_at=f.get("modifiedTime"), authority=0.5, trust="private_connector")
                stats["drive"] += 1
        if req.gmail:
            for m in google_connector.list_gmail():
                content = "\n".join(filter(None, [f"From: {m.get('from','')}", f"Date: {m.get('date','')}", m.get("snippet", ""), m.get("body", "")]))
                mid, _ = insert_memory(
                    source_type="gmail", source_key=m.get("id"), title=m.get("subject", "Email"), url=None,
                    content=content, importance=0.62, tags=["google", "gmail"], summary=clean_summary(content),
                    sensitivity="sensitive", allow_external_llm=False,
                )
                index_memory(mid, m.get("subject", ""), content, clean_summary(content))
                register_provenance(mid, title=m.get("subject", "Email"), content=content, url=None, source_kind="gmail", publisher=m.get("from") or "Gmail", published_at=m.get("date"), authority=0.5, trust="private_connector")
                stats["gmail"] += 1
        audit("connector.google.sync", "done", actor="human", detail=stats)
        return {"ok": True, "synced": stats}
    except Exception as exc:
        audit("connector.google.sync", "failed", actor="human", detail={"error": type(exc).__name__})
        raise HTTPException(400, f"Google sync failed: {type(exc).__name__}: {exc}")


@app.get("/console", response_class=HTMLResponse)
def console():
    return HTMLResponse(CONSOLE_HTML.replace("__VERSION__", __version__), headers={"Cache-Control":"no-store"})


CONSOLE_HTML = r'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Intelligence OS Console</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,sans-serif;color-scheme:light dark}body{margin:0;background:#0d1117;color:#e6edf3}.wrap{max-width:1150px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:16px}.pill{padding:7px 11px;border:1px solid #30363d;border-radius:999px;color:#8b949e}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px;margin-top:20px}.card{background:#161b22;border:1px solid #30363d;border-radius:16px;padding:18px}.card h2{font-size:15px;margin:0 0 12px;color:#8b949e}.metric{font-size:28px;font-weight:750}.item{padding:10px 0;border-top:1px solid #21262d}.item:first-child{border-top:0}button{background:#238636;color:#fff;border:0;border-radius:10px;padding:9px 12px;cursor:pointer;margin:4px 3px 4px 0}.secondary{background:#30363d}.danger{background:#da3633}textarea{width:100%;box-sizing:border-box;background:#0d1117;border:1px solid #30363d;color:#e6edf3;border-radius:10px;padding:10px;margin:6px 0 10px}a{color:#58a6ff}.muted{color:#8b949e;font-size:13px}.eval{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.eval span{font-size:12px;padding:4px 7px;background:#21262d;border-radius:8px}</style></head>
<body><div class="wrap"><div class="top"><div><h1 style="margin:0">Intelligence OS</h1><div class="muted">Personal Cognitive Infrastructure · v__VERSION__</div></div><span class="pill" id="health">checking…</span></div>
<div class="grid"><div class="card"><h2>THINK</h2><textarea id="q" rows="4" placeholder="何を考えたい？"></textarea><button onclick="ask()">考える</button><div id="answer" class="item muted">Memoryを検索し、推論→Evalします。</div></div>
<div class="card"><h2>ATTENTION</h2><div id="attention">loading…</div></div>
<div class="card"><h2>DAILY BRIEF</h2><div class="metric" id="headline">—</div><div id="brief" class="muted"></div></div>
<div class="card"><h2>KNOWLEDGE INTEGRITY</h2><div id="knowledge" class="muted">loading…</div><textarea id="claim" rows="3" placeholder="検証したい主張"></textarea><button onclick="verifyClaim()">ローカル出典で検証</button><div id="verifyResult" class="item muted">保存済みSourceだけで支持・反証を確認します。</div></div>
<div class="card"><h2>RECENT MEMORY</h2><div id="memories">loading…</div></div>
<div class="card"><h2>APPROVAL GATE</h2><div id="approvals">loading…</div></div>
<div class="card"><h2>GOOGLE CONNECTOR</h2><div id="google" class="muted">loading…</div><button onclick="connectGoogle()">Google接続</button><button class="secondary" onclick="syncGoogle()">Read-only同期</button></div>
<div class="card"><h2>GOVERNANCE</h2><div class="item">Observe / Think は自動化可能。外部変更はリスクに応じHuman Approval。</div><div class="muted">v0.7.2-alpha: Safety-Limited Velocity。能力が上がっても権限は自動拡大しません。Privacy/Safety regressionでは拡張をHOLDし、外部ActionはEvidenceとHuman Authorityが追いつくまでProposal-onlyです。</div></div></div></div>
<script>
let TOKEN=sessionStorage.getItem('ios_token')||'';const headers=()=>({'Authorization':'Bearer '+TOKEN});const esc=s=>String(s??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
async function j(url,opt={}){if(!TOKEN){TOKEN=prompt('Local API Tokenを入力してください')||'';if(TOKEN)sessionStorage.setItem('ios_token',TOKEN)};opt.headers={...(opt.headers||{}),...headers()};let r=await fetch(url,opt);let data=await r.json().catch(()=>({detail:'invalid response'}));if(!r.ok)throw new Error(data.detail||r.statusText);return data}
async function refresh(){let h=await fetch('/api/health').then(r=>r.json());health.textContent=h.ok?'CORE ONLINE · '+h.reasoning:'OFFLINE';let a=await j('/api/attention?limit=5');attention.innerHTML=a.map(x=>`<div class=item><b>${esc(x.title)}</b><div class=muted>importance ${Number(x.importance).toFixed(2)}</div></div>`).join('')||'<span class=muted>まだありません</span>';let b=await j('/api/brief');headline.textContent=b.headline;brief.textContent='最近のTask '+b.recent_tasks.length+'件';let k=await j('/api/knowledge/status');knowledge.innerHTML=`sources <b>${k.sources||0}</b><br>verified <b>${k.verified||0}</b><br>contested <b>${k.contested||0}</b><br>contradicted <b>${k.contradicted||0}</b><br>superseded <b>${k.superseded||0}</b><br>open contradictions <b>${k.open_contradictions||0}</b>`;let m=await j('/api/memories?limit=8');memories.innerHTML=m.map(x=>`<div class=item><b>${esc(x.title)}</b><div class=muted>${esc(x.summary)}</div></div>`).join('')||'<span class=muted>拡張機能からページを記憶してください</span>';let p=await j('/api/approvals');approvals.innerHTML=p.filter(x=>x.status==='pending').map(x=>`<div class=item><b>${esc(x.description)}</b><div class=muted>${esc(x.risk)}</div><button onclick="decide(${x.id},true)">承認</button><button class=danger onclick="decide(${x.id},false)">却下</button></div>`).join('')||'<span class=muted>承認待ちはありません</span>';let g=await j('/api/connectors/google/status');google.innerHTML=`mode: <b>${esc(g.mode)}</b><br>configured: ${g.configured}<br>connected: ${g.connected}<br>${esc(g.warning)}`}
async function ask(){answer.textContent='thinking…';try{let r=await j('/api/ask',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({query:q.value})});answer.innerHTML=`<div>${esc(r.answer).replace(/\n/g,'<br>')}</div><div class=eval>${Object.entries(r.eval).filter(([k])=>!['notes','method'].includes(k)).map(([k,v])=>`<span>${k} ${v}</span>`).join('')}</div><div class=muted>Eval: ${esc(r.eval.method)} · ${esc(r.eval.notes)}<br>Memory: ${r.memories.map(x=>esc(x.title)).join(' / ')||'none'}<br>External memory shared: ${r.privacy?.shared_with_external_llm ?? 'n/a'} / withheld: ${r.privacy?.withheld_from_external_llm ?? 'n/a'}</div>`;refresh()}catch(e){answer.textContent=e.message}}
async function verifyClaim(){verifyResult.textContent='verifying against local sources…';try{let r=await j('/api/verify',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({claim:claim.value})});verifyResult.innerHTML=`<b>${esc(r.status)}</b> · confidence ${r.confidence}<br><span class=muted>scope: ${esc(r.verification_scope)} · ${esc(r.limitations)}</span><br>${r.evidence.slice(0,4).map(e=>`<div class=item>${esc(e.stance)} ${e.score} · ${esc(e.title)}</div>`).join('')}`;refresh()}catch(e){verifyResult.textContent=e.message}}
async function decide(id,approve){await j('/api/approvals/'+id,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({approve})});refresh()}
async function connectGoogle(){try{let r=await j('/api/connectors/google/start',{method:'POST'});window.location.href=r.authorization_url}catch(e){alert(e.message)}}
async function syncGoogle(){try{let r=await j('/api/connectors/google/sync',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({calendar:true,drive:true,gmail:false})});alert(JSON.stringify(r.synced));refresh()}catch(e){alert(e.message)}}
refresh();setInterval(refresh,20000);
</script></body></html>'''
