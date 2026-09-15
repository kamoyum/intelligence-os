from intelligence_os.observability import record_skill_run, system_evals
from intelligence_os.storage import connect, init_db, now_iso


def test_system_evals_reports_actual_skill_use(tmp_path):
    db = tmp_path / 'o.db'
    init_db(db)
    with connect(db) as conn:
        cur = conn.execute("INSERT INTO tasks(created_at,kind,title,status,payload,result) VALUES(?,?,?,?,?,?)",
                           (now_iso(),'ask','test','done','{}','{}'))
        tid = int(cur.lastrowid)
    record_skill_run('memory_context', status='done', task_id=tid, mode='auto', metrics={'retrieved':3}, db_path=db)
    record_skill_run('verify', status='done', task_id=tid, mode='augment', metrics={'claims_checked':2}, db_path=db)
    out = system_evals(db_path=db)
    assert out['counts']['tasks_total'] == 1
    assert out['signals']['memory_reuse_rate_per_memory_skill_run'] == 1.0
    assert out['skills']['verify']['done'] == 1
    assert 'no_real_usage_yet' not in out['readiness_flags']


def test_system_evals_is_calibrated_about_no_usage(tmp_path):
    db = tmp_path / 'empty.db'
    init_db(db)
    out = system_evals(db_path=db)
    assert 'no_real_usage_yet' in out['readiness_flags']
    assert out['limitations']


def test_feedback_surfaces_cognitive_agency_warning(tmp_path):
    from intelligence_os.observability import record_feedback
    db = tmp_path / 'f.db'
    init_db(db)
    record_feedback('made_me_think_less', note='too automatic', db_path=db)
    out = system_evals(db_path=db)
    assert out['signals']['thinking_reduction_warning_count'] == 1
    assert 'human_cognitive_agency_warning' in out['readiness_flags']
