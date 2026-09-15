from __future__ import annotations

from typing import Any

from .config import settings

VALID_EXTERNAL_MODES = {"off", "opt_in", "all"}
# Connector-derived personal data is hard-local in the current alpha. A future UI may support
# explicit item-level export, but a global mode must not silently override this boundary.
HARD_LOCAL_SOURCE_TYPES = {"google_calendar", "google_drive", "gmail"}


def external_memory_allowed(memory: dict[str, Any], mode: str | None = None) -> bool:
    mode = (mode or settings.external_llm_mode).strip().lower()
    if mode not in VALID_EXTERNAL_MODES:
        mode = "opt_in"
    if str(memory.get("source_type", "")) in HARD_LOCAL_SOURCE_TYPES:
        return False
    if str(memory.get("sensitivity", "")).lower() in {"sensitive", "highly_sensitive"}:
        return False
    if mode == "off":
        return False
    if mode == "all":
        return True
    return bool(memory.get("allow_external_llm", 0))


def external_memories(memories: list[dict[str, Any]], mode: str | None = None) -> list[dict[str, Any]]:
    return [m for m in memories if external_memory_allowed(m, mode)]


def privacy_stats(memories: list[dict[str, Any]], mode: str | None = None) -> dict[str, int | str]:
    allowed = external_memories(memories, mode)
    return {
        "external_llm_mode": (mode or settings.external_llm_mode),
        "retrieved": len(memories),
        "shared_with_external_llm": len(allowed),
        "withheld_from_external_llm": len(memories) - len(allowed),
    }
