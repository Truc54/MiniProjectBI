"""Phase 4 (Lộc): collect Mage schedule + ctl audit evidence and self-check QA-01/QA-02.

Run inside the Mage container (Mage API on localhost:6789, SQL env already set),
feeding the script on stdin because only mage/project and run_etl.py are mounted:
    docker exec -i <mage-container> python - --out /home/src/evidence/loc_phase4_schedule_runs.json \
        < mage/collect_phase4_schedule_evidence.py
Read-only: it only calls Mage GET endpoints and SELECTs on ctl/stg/dw.
Exit code 0 only when QA-01 and QA-02 both PASS.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.request import urlopen

sys.path.insert(0, os.environ.get('USER_CODE_PATH') or str(Path(__file__).resolve().parent / 'project'))

PIPELINE = 'f1_source_to_stage'
SCHEDULE_TRIGGERS = ('f1_full_reload_every_30min', 'f1_incremental_every_30min', 'f1_daily_production')
EXPECTED_FACT_ROWS = 27568
EXPECTED_STAGE = {'circuits': 78, 'constructors': 214, 'drivers': 879, 'status': 141,
                  'seasons': 77, 'races': 1164, 'results': 27568}


def mage_get(base, path):
    with urlopen(f'{base}{path}', timeout=30) as response:
        return json.load(response)


def ts(value):
    """Mage API returns naive UTC strings; normalise both API and SQL values to naive UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed


def iso(value):
    return value.isoformat(sep=' ', timespec='seconds') if value else None


def collect_mage(base):
    schedules = mage_get(base, f'/api/pipelines/{PIPELINE}/pipeline_schedules')['pipeline_schedules']
    triggers = [dict(id=s['id'], name=s['name'], status=s['status'], schedule_type=s['schedule_type'],
                     schedule_interval=s['schedule_interval'], variables=s.get('variables'),
                     settings=s.get('settings'), next_run_utc=s.get('next_pipeline_run_date'))
                for s in schedules if s['name'] in SCHEDULE_TRIGGERS]
    by_id = {t['id']: t['name'] for t in triggers}
    runs = mage_get(base, f'/api/pipeline_runs?pipeline_uuid={PIPELINE}&_limit=200')['pipeline_runs']
    scheduled = []
    for run in sorted((r for r in runs if r['pipeline_schedule_id'] in by_id), key=lambda r: r['id']):
        blocks = mage_get(base, f'/api/block_runs?pipeline_run_id={run["id"]}')['block_runs']
        scheduled.append(dict(
            pipeline_run_id=run['id'], trigger=by_id[run['pipeline_schedule_id']],
            status=run['status'], execution_date_utc=iso(ts(run['execution_date'])),
            started_utc=iso(ts(run.get('started_at') or run['created_at'])),
            completed_utc=iso(ts(run.get('completed_at'))),
            blocks={b['block_uuid']: b['status'] for b in blocks}))
    return triggers, scheduled


def collect_sql(since):
    from sqlalchemy import text
    from f1_etl.sqlserver import create_sqlserver_engine
    engine = create_sqlserver_engine()
    try:
        with engine.connect() as conn:
            log = [dict(row._mapping) for row in conn.execute(text("""
                SELECT run_id, target_table, load_mode, batch_key, run_status,
                       started_at_utc, completed_at_utc, rows_read, rows_written,
                       rows_rejected, error_message
                FROM ctl.etl_run_log WHERE started_at_utc >= :since ORDER BY started_at_utc
            """), {'since': since})]
            summary = [dict(row._mapping) for row in conn.execute(text("""
                SELECT load_mode, run_status, COUNT(*) AS runs, SUM(rows_written) AS rows_written,
                       SUM(rows_rejected) AS rows_rejected
                FROM ctl.etl_run_log GROUP BY load_mode, run_status ORDER BY load_mode, run_status
            """))]
            batch_state = [dict(row._mapping) for row in conn.execute(text("""
                SELECT source_table, batch_key, source_row_count, batch_status, loaded_at_utc
                FROM ctl.etl_batch_state ORDER BY source_table, batch_key
            """))]
            stage = {name: conn.execute(text(f'SELECT COUNT(*) FROM stg.[{name}]')).scalar_one()
                     for name in EXPECTED_STAGE}
            fact = conn.execute(text('SELECT COUNT(*) FROM dw.FactRaceResult')).scalar_one()
    finally:
        engine.dispose()
    for row in log + batch_state:
        for key, value in row.items():
            if isinstance(value, datetime):
                row[key] = iso(value)
            elif key in ('run_id',) and value is not None:
                row[key] = str(value)
    return log, summary, batch_state, stage, fact


def attach_ctl_rows(scheduled, log):
    """A scheduled Mage run owns the ctl rows written between its start and completion."""
    for run in scheduled:
        start, end = ts(run['started_utc']), ts(run['completed_utc'])
        run['ctl_runs'] = [dict(run_id=r['run_id'], load_mode=r['load_mode'], run_status=r['run_status'],
                                rows_written=r['rows_written'])
                           for r in log if start and end and start <= ts(r['started_at_utc']) <= end]


def qa_checks(triggers, scheduled, log, stage, fact):
    active = [t['name'] for t in triggers if t['status'] == 'active' and t['schedule_type'] == 'time']
    done = [r for r in scheduled if r['status'] == 'completed']
    auto_modes = {c['load_mode'] for r in done for c in r['ctl_runs'] if c['run_status'] == 'success'}
    longest = streak = 0
    for run in scheduled:
        streak = streak + 1 if run['status'] == 'completed' else 0
        longest = max(longest, streak)
    failed = [r for r in log if r['run_status'] == 'failed']
    qa01 = {
        'active_schedule_triggers': active,
        'completed_scheduled_runs': len(done),
        'longest_consecutive_success_streak': longest,
        'auto_success_load_modes': sorted(auto_modes),
        'ctl_success_full': sum(r['load_mode'] == 'full' and r['run_status'] == 'success' for r in log),
        'ctl_success_incremental': sum(r['load_mode'] == 'incremental' and r['run_status'] == 'success'
                                       for r in log),
    }
    qa01['pass'] = bool(len(active) >= 1 and longest >= 2 and {'full', 'incremental'} <= auto_modes
                        and qa01['ctl_success_full'] and qa01['ctl_success_incremental'])
    qa02 = {
        'failed_rows': [dict(run_id=r['run_id'], target_table=r['target_table'], batch_key=r['batch_key'],
                             rows_rejected=r['rows_rejected'], error_message=r['error_message'])
                        for r in failed],
        'dw_FactRaceResult_rows': fact,
        'stage_counts_match_source': stage == EXPECTED_STAGE,
    }
    qa02['pass'] = bool(1 <= len(failed) <= 2
                        and all(r['rows_rejected'] > 0 and r['error_message'] for r in failed)
                        and fact == EXPECTED_FACT_ROWS and qa02['stage_counts_match_source'])
    return {'QA-01': qa01, 'QA-02': qa02}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mage-url', default='http://localhost:6789')
    parser.add_argument('--since', default='2026-11-22 00:00:00', help='Phase 4 window start (UTC)')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    triggers, scheduled = collect_mage(args.mage_url)
    log, summary, batch_state, stage, fact = collect_sql(args.since)
    attach_ctl_rows(scheduled, log)
    report = dict(generated_at_utc=iso(datetime.now(timezone.utc).replace(tzinfo=None)),
                  pipeline=PIPELINE, phase4_window_start_utc=args.since,
                  mage_triggers=triggers, mage_scheduled_runs=scheduled,
                  ctl_etl_run_log_phase4=log, ctl_etl_run_log_summary_all_time=summary,
                  ctl_etl_batch_state=batch_state, stg_row_counts=stage,
                  dw_FactRaceResult_rows=fact)
    report['qa'] = qa_checks(triggers, scheduled, log, stage, fact)
    report['status'] = 'PASS' if all(v['pass'] for v in report['qa'].values()) else 'FAIL'
    output = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    print(output)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + '\n', encoding='utf-8')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
