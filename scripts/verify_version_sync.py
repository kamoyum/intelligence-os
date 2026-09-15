from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
backend = re.search(r'__version__\s*=\s*"([^"]+)"', (ROOT/'backend/intelligence_os/__init__.py').read_text()).group(1)
native = re.search(r'"version"\s*:\s*"([^"]+)"', (ROOT/'native_host/host.py').read_text()).group(1)
manifest = json.loads((ROOT/'extension/manifest.json').read_text())['version']
readme = (ROOT/'README.md').read_text()
expected_manifest = backend.replace('-alpha','').replace('-beta','')
checks = {
    'native_matches_backend': native == backend,
    'manifest_matches_numeric_version': manifest == expected_manifest,
    'readme_mentions_backend_version': backend in readme,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'), k)
if not all(checks.values()): raise SystemExit(1)
