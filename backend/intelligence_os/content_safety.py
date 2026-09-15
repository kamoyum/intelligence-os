from __future__ import annotations

import re

INJECTION_PATTERNS = (
    r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions?",
    r"system prompt",
    r"developer message",
    r"reveal .*secret",
    r"以前の指示を無視",
    r"システムプロンプト",
    r"秘密.*開示",
)


def contains_prompt_injection(text: str) -> bool:
    """Heuristic signal only; not a complete prompt-injection defense."""
    return any(re.search(p, text or "", re.I) for p in INJECTION_PATTERNS)


def memory_has_injection_risk(memory: dict) -> bool:
    return contains_prompt_injection(f"{memory.get('title','')}\n{memory.get('content','')}")
