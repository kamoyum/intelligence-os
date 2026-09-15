from intelligence_os.actions import list_actions, propose_action, undo_action
from intelligence_os.storage import connect, init_db


def test_local_note_auto_executes_and_is_undoable(tmp_path):
    db=tmp_path/'a.db'; init_db(db)
    out=propose_action('create_local_note','save note',{'title':'note','content':'hello'},db_path=db)
    assert out['status']=='done'
    assert out['approval_id'] is None
    mid=out['result']['memory_id']
    with connect(db) as conn:
        assert conn.execute("SELECT status FROM memories WHERE id=?",(mid,)).fetchone()['status']=='active'
    undone=undo_action(out['id'],db_path=db)
    assert undone['status']=='undone'
    with connect(db) as conn:
        assert conn.execute("SELECT status FROM memories WHERE id=?",(mid,)).fetchone()['status']=='archived'


def test_external_action_is_proposal_only(tmp_path):
    db=tmp_path/'b.db'; init_db(db)
    out=propose_action('gmail_draft','draft email',{'to':'a@example.com','body':'hello'},db_path=db)
    assert out['status']=='awaiting_approval'
    assert out['approval_id'] is not None
    assert out['result']=={}
    assert out['external_side_effect'] is True


def test_send_and_permission_change_never_auto_execute(tmp_path):
    db=tmp_path/'c.db'; init_db(db)
    send=propose_action('email_send','send',{'to':'a@example.com'},db_path=db)
    perm=propose_action('permission_change','grant admin',{},db_path=db)
    assert send['status']=='awaiting_approval'
    assert perm['status']=='awaiting_approval'
    assert send['policy']['auto_execute'] is False
    assert perm['policy']['mode']=='human_only'
