from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    'README.md', 'LICENSE', 'NOTICE', 'INTELLIGENCE_OS.md', 'SECURITY.md', 'CONTRIBUTING.md',
    'GOVERNANCE.md', 'EVALS.md', 'KNOWN_LIMITATIONS.md', 'CHANGELOG.md',
    '.github/workflows/ci.yml', '.github/workflows/codeql.yml',
    'docs/STATUS.md', 'docs/THREAT_MODEL.md', 'docs/GITHUB_PUBLICATION_CHECKLIST.md',
]

FORBIDDEN_NAMES = {
    'intelligence.db', 'intelligence.db-shm', 'intelligence.db-wal',
    'local_api_token.txt', 'google_token.json', 'google_client_secret.json', '.env',
}
FORBIDDEN_PARTS = {'.git', '.venv', '__pycache__', '.pytest_cache'}
SECRET_PATTERNS = [
    re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9_]{20,}\b'),
    re.compile(r'\bAIza[0-9A-Za-z_-]{20,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]
SYNTHETIC_MARKERS = ('abcdefghijkl', 'dummy', 'example', 'synthetic', 'test-secret', 'fake')
TEXT_SUFFIXES = {'.py', '.md', '.txt', '.json', '.yml', '.yaml', '.html', '.js', '.sh', '.bat', '.command'}

errors: list[str] = []

for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        errors.append(f'missing required public file: {rel}')

for path in ROOT.rglob('*'):
    rel = path.relative_to(ROOT)
    if any(part in FORBIDDEN_PARTS for part in rel.parts):
        continue
    if path.name in FORBIDDEN_NAMES or path.suffix in {'.pyc', '.pyo'}:
        if rel.parts[:2] == ('backend', 'data') and path.name in FORBIDDEN_NAMES:
            continue
        errors.append(f'forbidden generated/sensitive artifact: {rel}')
        continue
    if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    for n, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for pattern in SECRET_PATTERNS:
            if pattern.search(line) and not any(marker in low for marker in SYNTHETIC_MARKERS):
                errors.append(f'possible secret in {rel}:{n}')

issue_cfg = ROOT / '.github/ISSUE_TEMPLATE/config.yml'
if issue_cfg.exists() and 'OWNER/' in issue_cfg.read_text(encoding='utf-8'):
    errors.append('GitHub issue config still contains OWNER placeholder')

readme = (ROOT / 'README.md').read_text(encoding='utf-8') if (ROOT/'README.md').exists() else ''
for required_phrase in ('Developer Alpha', 'Capability ≠ authority', 'Apache License 2.0'):
    if required_phrase not in readme:
        errors.append(f'README missing public-boundary phrase: {required_phrase}')

if errors:
    print('PUBLIC REPO AUDIT: FAIL')
    for item in errors:
        print(' -', item)
    raise SystemExit(1)

print('PUBLIC REPO AUDIT: PASS')
print(f'required files: {len(REQUIRED)}')
print('secret/generated-artifact scan: PASS')
