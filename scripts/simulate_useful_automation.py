#!/usr/bin/env python3
from __future__ import annotations
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from intelligence_os.actions import propose_action,undo_action,list_actions
from intelligence_os.storage import connect,init_db

def main():
  with tempfile.TemporaryDirectory() as td:
    db=Path(td)/'a.db'; init_db(db)
    local=propose_action('create_local_note','remember this',{'title':'Auto note','content':'A reversible local action'},db_path=db)
    ext=propose_action('gmail_draft','prepare draft',{'to':'person@example.com','body':'draft only'},db_path=db)
    send=propose_action('email_send','send now',{'to':'person@example.com'},db_path=db)
    undone=undo_action(local['id'],db_path=db)
    with connect(db) as conn:
      mstatus=conn.execute("SELECT status FROM memories WHERE id=?",(local['result']['memory_id'],)).fetchone()['status']
      pending=conn.execute("SELECT COUNT(*) n FROM approvals WHERE status='pending'").fetchone()['n']
    checks={
      'local_reversible_auto':local['status']=='done' and local['approval_id'] is None,
      'local_undo':undone['status']=='undone' and mstatus=='archived',
      'external_draft_not_executed':ext['status']=='awaiting_approval' and ext['result']=={},
      'send_human_only':send['policy']['mode']=='approve' and send['status']=='awaiting_approval',
      'approvals_created':pending==2,
    }
    print(json.dumps({'local':local,'external_draft':ext,'send':send,'actions':list_actions(db_path=db),'checks':checks,'all_pass':all(checks.values())},ensure_ascii=False,indent=2))
    return 0 if all(checks.values()) else 1
if __name__=='__main__': raise SystemExit(main())
