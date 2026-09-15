#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))

from intelligence_os.attention import attention_queue, create_goal
from intelligence_os.learning import create_expectation
from intelligence_os.observability import record_skill_run, system_evals
from intelligence_os.retrieval import index_memory
from intelligence_os.storage import clean_summary, connect, init_db, insert_memory, now_iso


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'obs.db'; init_db(db)
        create_goal('重要プロジェクト', description='検証と公開', priority=1.0, due_at=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat(), db_path=db)
        mid,_=insert_memory(source_type='test',source_key='m1',title='関連メモ',url=None,content='重要プロジェクト 検証 公開',importance=.6,tags=[],summary='重要プロジェクト 検証 公開',db_path=db)
        index_memory(mid,'関連メモ','重要プロジェクト 検証 公開','重要プロジェクト 検証 公開',db_path=db)
        create_expectation('公開前テストが通る','all tests pass',.8,due_at=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(),db_path=db)
        with connect(db) as conn:
            t=conn.execute("INSERT INTO tasks(created_at,kind,title,status,payload,result) VALUES(?,?,?,?,?,?)",(now_iso(),'ask','test','done','{}','{}'))
            tid=int(t.lastrowid)
            conn.execute("INSERT INTO claims(created_at,claim_text,status,confidence,verification_method) VALUES(?,?,?,?,?)",(now_iso(),'公開可否に影響する矛盾','contested',.9,'sim'))
            conn.execute("INSERT INTO approvals(created_at,action_type,description,risk,status,payload) VALUES(?,?,?,?,?,?)",(now_iso(),'publish','公開する','high','pending','{}'))
        record_skill_run('memory_context',status='done',task_id=tid,mode='auto',metrics={'retrieved':2},db_path=db)
        record_skill_run('verify',status='done',task_id=tid,mode='augment',metrics={'claims_checked':1},db_path=db)
        queue=attention_queue(8,db_path=db)
        evals=system_evals(db_path=db)
        top_types=[x['type'] for x in queue[:5]]
        checks={
            'conflict_surfaced':'knowledge_conflict' in top_types,
            'approval_surfaced':'approval' in top_types,
            'overdue_outcome_surfaced':'outcome_due' in top_types,
            'memory_reuse_measured':evals['signals']['memory_reuse_rate_per_memory_skill_run']==1.0,
            'skill_execution_observed':evals['skills'].get('verify',{}).get('done')==1,
        }
        print(json.dumps({'queue':queue,'system_evals':evals,'checks':checks,'all_pass':all(checks.values())},ensure_ascii=False,indent=2))
        return 0 if all(checks.values()) else 1

if __name__=='__main__': raise SystemExit(main())
