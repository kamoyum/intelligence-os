from __future__ import annotations

import re
from dataclasses import dataclass, asdict


_SECRET_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bsk-[A-Za-z0-9_-]{16,}\b", "api_key"),
    (r"\bAKIA[0-9A-Z]{16}\b", "aws_access_key"),
    (r"\bAIza[0-9A-Za-z_-]{20,}\b", "google_api_key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", "github_token"),
    (r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", "bearer_token"),
    (r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b", "jwt"),
    (r"(?i)\b(?:password|passwd|api[_ -]?key|secret|access[_ -]?token|refresh[_ -]?token|key)\s*[:=]\s*\S{6,}", "credential_assignment"),
)

_PII_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "email"),
    (r"(?<!\d)(?:\+?81[- ]?)?0\d{1,4}[- ]?\d{1,4}[- ]?\d{3,4}(?!\d)", "jp_phone"),
    (r"(?<!\d)\d{3}-\d{4}(?!\d)", "jp_postcode"),
    (r"(?<!\d)\d{12}(?!\d)", "12_digit_identifier"),
)

_SENSITIVE_CONTEXT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"患者|診療録|カルテ|病歴|診断名|処方|検査値", "health_context"),
    (r"口座|カード番号|暗証番号|CVV|銀行", "financial_context"),
    (r"社員番号|職員番号|顧客番号|個人情報", "identity_context"),
)


@dataclass(frozen=True)
class QuerySafety:
    level: str  # safe | sensitive | secret
    findings: tuple[str, ...]
    external_policy: str  # auto | confirm | redact_required

    def to_dict(self) -> dict:
        d = asdict(self)
        d["findings"] = list(self.findings)
        return d


def _hits(text: str, patterns: tuple[tuple[str, str], ...], flags: int = 0) -> list[str]:
    out: list[str] = []
    for pattern, label in patterns:
        if re.search(pattern, text, flags):
            out.append(label)
    return out


def classify_query_safety(text: str) -> QuerySafety:
    secret = _hits(text, _SECRET_PATTERNS)
    if secret:
        return QuerySafety("secret", tuple(sorted(set(secret))), "redact_required")

    pii = _hits(text, _PII_PATTERNS, re.IGNORECASE)
    context = _hits(text, _SENSITIVE_CONTEXT_PATTERNS, re.IGNORECASE)
    findings = sorted(set(pii + context))
    if findings:
        return QuerySafety("sensitive", tuple(findings), "confirm")
    return QuerySafety("safe", tuple(), "auto")


def redact_query_for_external(text: str) -> str:
    """Best-effort local redaction helper.

    This intentionally does not claim perfect de-identification. Secret patterns are replaced;
    PII-like patterns are masked. High-stakes/sensitive context still requires human judgment.
    """
    out = text
    for pattern, label in _SECRET_PATTERNS:
        out = re.sub(pattern, f"[REDACTED:{label}]", out, flags=re.IGNORECASE)
    for pattern, label in _PII_PATTERNS:
        out = re.sub(pattern, f"[REDACTED:{label}]", out, flags=re.IGNORECASE)
    return out
