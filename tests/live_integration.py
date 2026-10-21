"""Exercise actual Mage blocks against a disposable SQL Server database.

Run inside the built Mage container, with USER_CODE_PATH and MSSQL_* set.
Requires --reset-stage: replaces all core Stage data, keeping run history.
"""

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import traceback
import uuid

PROJECT = Path(os.environ.get('USER_CODE_PATH', '/home/src/project'))
sys.path.insert(0, str(PROJECT))

import pyodbc
from sqlalchemy import text
import sqlalchemy

from f1_etl.contract import QualityError, TABLES
from f1_etl.source import load_payload, typed_rows, validate_payload
from f1_etl.sqlserver import (EtlRunError, check_stage, create_sqlserver_engine,
                            export_payload, table_lock, write_stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reset-stage', required=True, action='store_true')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    log_path = args.evidence.with_suffix('.log')
    engine = create_sqlserver_engine()
    report = dict(status='running', backend='sqlserver_and_mage',
                  timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  dung_commit='5b7113f64f81b670830f3975bf038dedf58f7b9e',
                  mage_execution=dict(method='Pipeline.execute_sync', run_tests=False,
                                      update_status=False, block_statuses_persisted=False),
                  runs=[], checks=[], failure_checks=[])
    log_buffer = io.StringIO()
    test_id = uuid.uuid4().hex[:8]

    def query(sql, params=None):
        with engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(sql), params or {}).mappings()]

    def snapshot(name, compare_source=True):
        key = TABLES[name].key
        with engine.connect() as conn:
            columns = ','.join(f'[{col}]' for col in TABLES[name].columns)
            actual = [dict(row) for row in conn.execute(text(
                f'SELECT {columns} FROM stg.[{name}] ORDER BY [{key}]'
            )).mappings()]
        keys = [row[key] for row in actual]
        if len(set(keys)) != len(keys):
            raise AssertionError(f'{name}: duplicate keys')
        if compare_source:
            expected = sorted(typed_rows(sources[name]), key=lambda row: row[key])
            if actual != expected:
                raise AssertionError(f'{name}: typed source and SQL data differ')
        return dict(table=name, rows=len(keys),
                    key_sha256=hashlib.sha256(','.join(map(str, keys)).encode()).hexdigest())

    def assert_clean(label):
        state = check_stage(engine)
        if sum(row['orphan_count'] for row in state['relationships']):
            raise AssertionError(f'{label}: orphan foreign keys')
        if state['counts'] != {name: len(p['rows']) for name, p in sources.items()}:
            raise AssertionError(f'{label}: counts differ')
        state['label'] = label
        state['source_stage_comparison'] = [snapshot(name) for name in TABLES]
        report['checks'].append(state)
        return state

    def mage_run(name, batch, mode='full', bounds=None, expect_failure=False):
        from mage_ai.data_preparation.models.pipeline import Pipeline
        variables = dict(file_name=f'{name}.csv', table_name=name, target_table=name,
                         schema_name='stg', load_mode=mode, batch_key=f'live_{test_id}_{batch}',
                         **(bounds or {}))
        pipeline = Pipeline('f1_source_to_stage', repo_path=str(PROJECT))
        error = None
        with redirect_stdout(log_buffer), redirect_stderr(log_buffer):
            try:
                pipeline.execute_sync(global_vars=variables, run_tests=False, update_status=False)
            except Exception as exc:
                error = exc
                traceback.print_exc()
        audits = query('SELECT * FROM ctl.etl_run_log WHERE batch_key=:batch ORDER BY started_at_utc DESC',
                       {'batch': variables['batch_key']})
        if not audits:
            if error:
                raise error
            raise AssertionError('Mage did not create a ctl run record')
        audit = audits[0]
        if expect_failure:
            if error is None or audit['run_status'] != 'failed':
                raise AssertionError('Expected Mage failure and failed SQL audit')
        elif error is not None:
            raise error
        elif audit['run_status'] != 'success':
            raise AssertionError('Mage run did not finish with success SQL audit')
        item = dict(variables=variables, run_id=str(audit['run_id']), status=audit['run_status'],
                    rows_read=audit['rows_read'], rows_written=audit['rows_written'],
                    rows_rejected=audit['rows_rejected'], error_message=audit['error_message'],
                    mage_blocks=list(pipeline.blocks_by_uuid))
        report['runs'].append(item)
        print(f'Mage {name} {mode} {batch}: {audit["run_status"]}, rows={audit["rows_written"]}', flush=True)
        return item

    try:
        from importlib.metadata import version
        report['runtime'] = dict(python=platform.python_version(), machine=platform.machine(),
                                 mage=version('mage-ai'), sqlalchemy=sqlalchemy.__version__,
                                 pyodbc=pyodbc.version, odbc_drivers=pyodbc.drivers())
        report['sqlserver'] = query('SELECT @@VERSION AS version, DB_NAME() AS database_name, '
                                    'ORIGINAL_LOGIN() AS login_name')[0]
        sources = {name: validate_payload(load_payload({'table_name': name})) for name in TABLES}
        for p in sources.values():
            if p['error']:
                raise QualityError(p['error'])
        for iteration in (1, 2):
            for name in TABLES:
                mage_run(name, f'full{iteration}_{name}')
            assert_clean(f'full_{iteration}')
        with engine.begin() as conn:
            for name in reversed(TABLES):
                conn.execute(text(f'DELETE FROM stg.[{name}]'))
            conn.execute(text('DELETE FROM ctl.etl_batch_state'))
        for name in TABLES:
            key = TABLES[name].key
            keys = sorted(int(row[key]) for row in sources[name]['rows'])
            pivot = keys[len(keys) // 2 - 1]
            for label, bounds in (('part1', {'key_max': pivot}),
                                  ('part2', {'key_min': pivot + 1}),
                                  ('part2', {'key_min': pivot + 1})):
                item = mage_run(name, f'{name}_{label}', 'incremental', bounds)
                state = snapshot(name, compare_source=label != 'part1')
                expected_count = sum(value <= pivot for value in keys) if label == 'part1' else len(keys)
                if state['rows'] != expected_count:
                    raise AssertionError(f'{name}: wrong incremental coverage')
                item['stage_after_run'] = state
        assert_clean('incremental_and_rerun')
        # Fail through the actual Mage loader/validator/exporter chain, without changing source CSVs.
        original_data_dir = os.environ.get('F1_DATA_DIR')
        before = snapshot('status')
        with tempfile.TemporaryDirectory() as data_dir:
            Path(data_dir, 'status.csv').write_text('statusId,status\n1,Finished\n1,Duplicate\n')
            os.environ['F1_DATA_DIR'] = data_dir
            try:
                failed = mage_run('status', 'duplicate_failure', expect_failure=True)
            finally:
                if original_data_dir is None:
                    os.environ.pop('F1_DATA_DIR', None)
                else:
                    os.environ['F1_DATA_DIR'] = original_data_dir
        if snapshot('status') != before or failed['rows_written'] != 0 or failed['rows_rejected'] != 1:
            raise AssertionError('Validation failure changed Stage or recorded wrong counters')
        report['failure_checks'].append(dict(kind='mage_duplicate_key', run_id=failed['run_id'], stage_unchanged=True))
        # Real rollback after executing DELETE + INSERT; include an intentional secret marker.
        bad = validate_payload(load_payload({'table_name': 'status', 'batch_key': f'live_{test_id}_rollback'}))
        def fail_after_write(conn, data, run_id):
            write_stage(conn, data, run_id)
            raise RuntimeError('intentional-secret-marker-must-not-be-logged')
        try:
            export_payload(bad, engine, writer=fail_after_write)
        except EtlRunError as exc:
            if 'intentional-secret-marker' in str(exc):
                raise AssertionError('Secret marker escaped sanitization')
        else:
            raise AssertionError('Rollback injection did not fail')
        if snapshot('status') != before:
            raise AssertionError('Rollback did not restore original SQL data')
        rollback_audit = query('SELECT run_id, run_status, rows_written, error_message FROM ctl.etl_run_log '
                               'WHERE batch_key=:batch', {'batch': bad['context']['batch_key']})[0]
        if rollback_audit['run_status'] != 'failed' or rollback_audit['rows_written'] != 0:
            raise AssertionError('Rollback failure audit is incorrect')
        report['failure_checks'].append(dict(kind='sql_write_rollback', audit=rollback_audit, stage_unchanged=True))
        # Verify the SQL Server application lock serializes competing sessions and releases.
        with engine.connect() as first, engine.connect() as second:
            with table_lock(first, 'status'):
                with second.begin():
                    code = second.execute(text("""
                        DECLARE @r INT;
                        EXEC @r=sys.sp_getapplock @Resource='f1_source_to_stage:stg.status',
                            @LockMode='Exclusive', @LockOwner='Session', @LockTimeout=0;
                        SELECT @r;
                    """)).scalar_one()
                    if code != -1:
                        raise AssertionError(f'Competing session acquired table lock: {code}')
            with table_lock(second, 'status'):
                pass
        report['application_lock'] = dict(competing_session_blocked=True, released_after_run=True)
        # End with a successful real Mage run and verify all typed values, not just key counts.
        mage_run('status', 'final_retry')
        assert_clean('final')
        report['audit_statuses'] = query(
            'SELECT run_status, COUNT(*) AS run_count FROM ctl.etl_run_log '
            'WHERE batch_key LIKE :prefix GROUP BY run_status', {'prefix': f'live_{test_id}_%'})
        report['batch_states'] = query(
            'SELECT source_name, source_table, batch_key, batch_status, source_row_count, last_run_id '
            'FROM ctl.etl_batch_state ORDER BY source_table, batch_key')
        report['null_blank_checks'] = query("""
            SELECT (SELECT COUNT(*) FROM stg.results WHERE position IS NULL) AS null_positions,
                   (SELECT COUNT(*) FROM stg.drivers WHERE nationality='' AND url='') AS blank_driver_rows
        """)[0]
        if report['null_blank_checks'] != dict(null_positions=11074, blank_driver_rows=14):
            raise AssertionError('Source NULL/blank semantics differ in SQL Server')
        report['status'] = 'success'
    except Exception as exc:
        report.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        traceback.print_exc(file=log_buffer)
    finally:
        engine.dispose()
        report['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
        raw = json.dumps(report, ensure_ascii=False, indent=2, default=str)
        logs = log_buffer.getvalue()
        for name in ('MSSQL_PASSWORD', 'MSSQL_SA_PASSWORD'):
            secret = os.environ.get(name)
            if secret:
                raw, logs = raw.replace(secret, '[REDACTED]'), logs.replace(secret, '[REDACTED]')
        args.evidence.write_text(raw + '\n')
        log_path.write_text(logs)
        print(json.dumps(dict(status=report['status'], evidence=str(args.evidence),
                              error_type=report.get('error_type'), error=report.get('error')), indent=2), flush=True)
    return 0 if report['status'] == 'success' else 1


if __name__ == '__main__':
    sys.exit(main())
