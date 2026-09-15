from __future__ import annotations

import json
from typing import Any

from .config import settings
from .content_safety import memory_has_injection_risk
from .privacy import external_memories


def heuristic_evaluate(answer: str, memories: list[dict[str, Any]]) -> dict[str, float | str]:
    grounded = 0.78 if memories else 0.42
    relevance = 0.80 if len(answer.strip()) > 40 else 0.52
    actionability = 0.72 if any(k in answer for k in ["次", "確認", "実行", "設定", "next", "check"]) else 0.58
    calibration = 0.70 if any(k in answer for k in ["不明", "未確認", "必要", "推測", "uncertain", "verify"]) else 0.58
    safety = 0.94
    accuracy = min(0.84, grounded + 0.04)
    return {
        "method": "heuristic",
        "accuracy": round(accuracy, 2),
        "groundedness": round(grounded, 2),
        "relevance": round(relevance, 2),
        "actionability": round(actionability, 2),
        "calibration": round(calibration, 2),
        "safety": round(safety, 2),
        "notes": "Fallback heuristic only. This does not fact-check external claims.",
    }


def llm_evaluate(query: str, answer: str, memories: list[dict[str, Any]], *, allow_external: bool = True) -> dict[str, float | str]:
    model = settings.eval_model or settings.model
    if not allow_external:
        out = heuristic_evaluate(answer, memories)
        out["notes"] = "External evaluator withheld by Query Safety policy; local heuristic only."
        return out
    if not (settings.openai_api_key and model):
        return heuristic_evaluate(answer, memories)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        shared_memories = [m for m in external_memories(memories) if not memory_has_injection_risk(m)]
        context = "\n\n".join(
            f"[{m['id']}] {m['title']}\n{m['summary'] or m['content'][:1800]}" for m in shared_memories
        )
        prompt = f"""Evaluate this Intelligence OS answer. Judge ONLY against the user query and supplied memory.
Do not assume external facts are true. If an external factual claim cannot be verified from supplied context, lower accuracy/groundedness and say fresh verification is needed.
Return JSON only with keys: accuracy, groundedness, relevance, actionability, calibration, safety, notes.
All scores must be numbers from 0 to 1.

QUERY:\n{query}\n\nMEMORY:\n{context or '(none)'}\n\nANSWER:\n{answer}"""
        resp = client.responses.create(model=model, input=prompt, store=False)
        raw = getattr(resp, "output_text", "") or ""
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start:end+1])
        out: dict[str, float | str] = {"method": "llm"}
        for k in ["accuracy", "groundedness", "relevance", "actionability", "calibration", "safety"]:
            out[k] = round(max(0.0, min(1.0, float(data.get(k, 0.5)))), 2)
        out["notes"] = str(data.get("notes", "LLM evaluator"))[:1200]
        return out
    except Exception as exc:
        out = heuristic_evaluate(answer, memories)
        out["notes"] = f"LLM eval failed ({type(exc).__name__}); heuristic fallback."
        return out


def evaluate_answer(query: str, answer: str, memories: list[dict[str, Any]], *, eval_profile: dict | None = None, allow_external: bool = True) -> dict[str, float | str]:
    """Adaptive Evals wrapper. Base Policy remains always-on; this only scales extra evaluation effort."""
    profile = eval_profile or {}
    level = str(profile.get("level") or "standard")
    label = str(profile.get("label") or level)
    external_judge = str(profile.get("external_judge") or "optional")

    if level == "light" or external_judge == "skip":
        out = heuristic_evaluate(answer, memories)
        out["notes"] = f"{label}. " + str(out["notes"])
        out["eval_level"] = level
        return out

    out = llm_evaluate(query, answer, memories, allow_external=allow_external)
    if out.get("method") == "heuristic" and level in {"deep", "high_stakes"}:
        out["notes"] = f"{label}. Evaluation degraded to local heuristic; required verification must be satisfied separately by the Verification layer. " + str(out.get("notes", ""))
    else:
        out["notes"] = f"{label}. " + str(out.get("notes", ""))
    out["eval_level"] = level
    return out
