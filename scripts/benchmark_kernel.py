#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from intelligence_os.executive import plan
from intelligence_os.knowledge import register_provenance
from intelligence_os.retrieval import index_memory
from intelligence_os.storage import clean_summary, init_db, insert_memory
from intelligence_os.verification import verify_claim


def executive_benchmark() -> tuple[int, int, list[str]]:
    cases = json.loads((ROOT / 'benchmarks' / 'executive_cases.json').read_text(encoding='utf-8'))
    passed = 0
    errors: list[str] = []
    for i, c in enumerate(cases, 1):
        p = plan(c['query']).to_dict()
        ok = True
        for key in ('autonomy', 'risk', 'evidence_requirement', 'human_checkpoint', 'cognitive_mode'):
            if key in c and p.get(key) != c[key]:
                ok = False; errors.append(f'exec#{i} {key}: {p.get(key)!r} != {c[key]!r}')
        if 'query_safety' in c and p.get('query_safety', {}).get('level') != c['query_safety']:
            ok = False; errors.append(f"exec#{i} query_safety: {p.get('query_safety',{}).get('level')} != {c['query_safety']}")
        if 'eval_level' in c and p.get('eval_profile', {}).get('level') != c['eval_level']:
            ok = False; errors.append(f"exec#{i} eval_level: {p.get('eval_profile',{}).get('level')} != {c['eval_level']}")
        for skill in c.get('skills', []):
            if skill not in p.get('skills', []):
                ok = False; errors.append(f'exec#{i} missing skill {skill}')
        passed += int(ok)
    return passed, len(cases), errors


def add_source(db: Path, key: str, text: str, authority: float, trust: str, published='2026-09-01T00:00:00+00:00') -> None:
    mid, _ = insert_memory(source_type='web_research', source_key=key, title=key, url=f'https://example.com/{key}', content=text,
                           importance=.7, tags=[], summary=clean_summary(text), sensitivity='public', allow_external_llm=True, db_path=db)
    index_memory(mid, key, text, clean_summary(text), db_path=db)
    register_provenance(mid, title=key, content=text, url=f'https://example.com/{key}', source_kind='web_research', publisher='benchmark',
                        published_at=published, authority=authority, trust=trust, db_path=db)


def verification_benchmark() -> tuple[int, int, list[str]]:
    scenarios = [
        ('government support', 'Alpha requires 2 sessions weekly.', [('gov','Alpha requires 2 sessions weekly.',.96,'government_primary_hint')], 'verified'),
        ('obsolete mention', 'Alpha requires 2 sessions weekly.', [('gov','Alpha requires 2 sessions weekly. The prior 3-session rule is obsolete.',.96,'government_primary_hint')], 'verified'),
        ('government contradiction', 'Alpha requires 3 sessions weekly.', [('gov','Alpha requires 2 sessions weekly. The prior 3-session rule is obsolete.',.96,'government_primary_hint')], 'contradicted'),
        ('low authority support', 'Alpha requires 2 sessions weekly.', [('blog','Alpha requires 2 sessions weekly.',.48,'public_web')], 'supported'),
        ('vendor normative capped', 'Product A is best and should be used.', [('vendor','Product A is best and should be used.',.84,'vendor_primary_hint')], 'supported'),
        ('contested', 'Alpha is enabled by default.', [('a','Alpha is enabled by default.',.96,'government_primary_hint'),('b','Alpha is disabled by default.',.96,'government_primary_hint')], 'contested'),
    ]
    passed = 0; errors=[]
    for i,(name,claim,sources,expected) in enumerate(scenarios,1):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'b.db'; init_db(db)
            for src in sources: add_source(db,*src)
            got=verify_claim(claim, db_path=db)['status']
            if got==expected: passed+=1
            else: errors.append(f'verify#{i} {name}: {got} != {expected}')
    return passed,len(scenarios),errors


def main() -> int:
    ep,et,ee=executive_benchmark(); vp,vt,ve=verification_benchmark()
    total_p=ep+vp; total_t=et+vt
    report={'executive':{'passed':ep,'total':et},'verification':{'passed':vp,'total':vt},'errors':ee+ve,'score':round(total_p/total_t,3)}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if total_p==total_t else 1

if __name__=='__main__': raise SystemExit(main())
