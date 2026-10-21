"""Source guards and actual transaction tests using Dung's DDL snapshot.

SQLite checks rollback/reruns/audit, not SQL Server driver or locking behavior.
Run: python -m unittest discover -s tests -v
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
PROJECT = Path(os.environ.get('USER_CODE_PATH', ROOT / 'mage/project'))
sys.path.insert(0, str(PROJECT))

from f1_etl.contract import LINEAGE, QualityError, TABLES, resolve_request
from f1_etl.source import (check_source_relationships, load_payload, read_source,
                           typed_rows, validate_payload)
from f1_etl.sqlserver import EtlRunError, check_stage, export_payload, write_stage


def payload(name='status', **variables):
    return validate_payload(load_payload(dict(table_name=name, **variables), ROOT / 'dataset'))


def ddl_tables():
    """Extract column definitions and PKs from the immutable handoff (not ETL code)."""
    for path in sorted((ROOT / 'tests/fixtures').glob('dung_5b7113f_*.sql')):
        content = path.read_text()
        for match in re.finditer(r'CREATE TABLE (\w+)\.(\w+)\s*\((.*?)\n    \);', content, re.S):
            schema, name, body = match.groups()
            columns = []
            for line in body.splitlines():
                col = re.match(r'\s*\[?(\w+)\]?\s+([A-Z][A-Z0-9]*(?:\([^)]*\))?)\s+(NOT NULL|NULL)', line)
                if col:
                    columns.append(col.groups())
            pk = re.search(r'PRIMARY KEY(?: CLUSTERED)?\s*\(([^)]+)\)', body)
            yield schema, name, columns, [x.strip(' []\n') for x in pk.group(1).split(',')]


def sqlite_handoff_engine():
    engine = create_engine('sqlite://', future=True)
    with engine.begin() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS stg")
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS ctl")
        for schema, name, columns, keys in ddl_tables():
            parts = []
            for column, sql_type, nullable in columns:
                sql_type = re.sub(r'DATETIME2\(\d+\)', 'DATETIME', sql_type)
                sql_type = sql_type.replace('TIME(0)', 'TIME').replace('SYSNAME', 'NVARCHAR(128)')
                sql_type = sql_type.replace('UNIQUEIDENTIFIER', 'VARCHAR(36)')
                sql_type = sql_type.replace('NVARCHAR(MAX)', 'TEXT')
                # Both backends support explicit values for all audit fields.
                default = ' DEFAULT 0' if column in ('rows_read', 'rows_written', 'rows_rejected') else ''
                parts.append(f'[{column}] {sql_type} {nullable}{default}')
            parts.append('PRIMARY KEY (' + ','.join(f'[{key}]' for key in keys) + ')')
            conn.exec_driver_sql(f'CREATE TABLE {schema}.[{name}] (' + ','.join(parts) + ')')
    return engine


class SourceTests(unittest.TestCase):
    def test_all_core_files_counts_and_relationships(self):
        all_payloads = {name: payload(name) for name in TABLES}
        self.assertEqual(sum(len(p['rows']) for p in all_payloads.values()), 30121)
        self.assertTrue(all(p['validated'] and not p['error'] for p in all_payloads.values()))
        self.assertEqual([r['orphan_count'] for r in check_source_relationships(all_payloads)], [0] * 6)
        json.dumps(all_payloads)  # Mage output stays serializable across blocks.

    def test_bom_null_blank_and_zero(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'status.csv').write_text('\ufeffstatusId,status\n1,\\N\n2,\n3,0\n', encoding='utf-8')
            p = read_source({'table_name': 'status'}, root)
            self.assertEqual([r['status'] for r in p['rows']], [None, '', '0'])

    def test_reject_paths_unknown_files_and_identifier_mismatch(self):
        for variables in ({'file_name': '../results.csv'}, {'file_name': '/tmp/results.csv'},
                          {'file_name': 'lap_times.csv'}, {'table_name': 'results; DROP TABLE x'},
                          {'file_name': 'drivers.csv', 'target_table': 'results'},
                          {'table_name': 'results', 'schema_name': 'dw'}):
            with self.subTest(variables=variables):
                self.assertIsNotNone(load_payload(variables)['error'])

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            source = Path(outside, 'status.csv')
            source.write_text('statusId,status\n1,Finished\n')
            Path(root, 'status.csv').symlink_to(source)
            self.assertIn('escapes', load_payload({'table_name': 'status'}, root)['error'])

    def test_bad_header_row_shape_and_encoding(self):
        for data in (b'statusId,wrong\n1,X\n', b'statusId,status\n1,X,extra\n',
                     b'statusId,status\n1\n', b'statusId,status\n1,\xff\n',
                     b'statusId,status\n1,"unterminated\n'):
            with self.subTest(data=data), tempfile.TemporaryDirectory() as root:
                Path(root, 'status.csv').write_bytes(data)
                self.assertIsNotNone(load_payload({'table_name': 'status'}, root)['error'])

    def test_duplicate_null_blank_and_numeric_key_aliases(self):
        original = payload()
        for key in ('1', None, '', '01', '2147483648'):
            p = deepcopy(original)
            p['rows'].append({'statusId': key, 'status': 'Extra'})
            checked = validate_payload(p)
            self.assertIsNotNone(checked['error'])
            self.assertEqual(checked['rows_rejected'], 1)

    def test_optional_nulls_and_f1_semantics(self):
        p = payload('results')
        self.assertFalse(p['error'])
        self.assertEqual(sum(r['position'] is None for r in p['rows']), 11074)
        row = deepcopy(p['rows'][0])
        row.update(position=None, grid='0', fastestLapSpeed=None)
        p['rows'] = [row]
        checked = validate_payload(p)
        self.assertTrue(checked['validated'])
        self.assertEqual(checked['rows'][0], row)

    def test_typed_values_dates_decimal_precision_and_times(self):
        p = payload('races')
        self.assertFalse(p['error'])
        index = next(i for i, row in enumerate(p['rows']) if (row['time'] or '').endswith('Z'))
        typed = typed_rows(dict(p, rows=[p['rows'][index]]))[0]
        self.assertIsNone(typed['time'].tzinfo)
        self.assertEqual(str(typed['time']), p['rows'][index]['time'].removesuffix('Z'))
        for name, column, value in [('races', 'date', '2026-02-30'),
                                    ('races', 'time', '25:00:00'),
                                    ('results', 'points', '1.001'),
                                    ('results', 'fastestLapSpeed', 'NaN'),
                                    ('results', 'laps', '-1'),
                                    ('drivers', 'forename', 'x' * 101)]:
            with self.subTest(column=column):
                p = payload(name)
                p['rows'][0][column] = value
                self.assertTrue(validate_payload(p)['error'])

    def test_deterministic_batches_cover_exact_key_set(self):
        first = payload('results', load_mode='incremental', batch_key='part1', key_max=14000)
        second = payload('results', load_mode='incremental', batch_key='part2', key_min=14001)
        get_keys = lambda p: {int(r['resultId']) for r in p['rows']}
        self.assertFalse(get_keys(first) & get_keys(second))
        self.assertEqual(get_keys(first) | get_keys(second), get_keys(payload('results')))
        second['rows'].reverse()
        self.assertEqual(get_keys(validate_payload(second)), get_keys(second))
        for variables in ({'load_mode': 'incremental'}, {'key_min': 1},
                          {'load_mode': 'incremental', 'key_min': 10, 'key_max': 2}):
            with self.assertRaises(QualityError):
                resolve_request(variables)
        self.assertTrue(payload('status', load_mode='incremental', key_min=99999)['error'])

    def test_orphan_reports_count_and_sample(self):
        ps = {name: payload(name) for name in TABLES}
        ps['results']['rows'][0]['driverId'] = '999999'
        failures = [r for r in check_source_relationships(ps) if r['orphan_count']]
        self.assertEqual(failures[0]['orphan_count'], 1)
        self.assertEqual(failures[0]['sample'], [999999])

    def test_contract_matches_dung_column_types_nullability_and_keys(self):
        seen = set()
        for schema, name, columns, keys in ddl_tables():
            if schema != 'stg':
                continue
            seen.add(name)
            self.assertEqual([c[0] for c in columns], list(TABLES[name].columns) + list(LINEAGE))
            self.assertEqual(keys, [TABLES[name].key])
            for column, sql_type, nullable in columns:
                if column in LINEAGE:
                    continue
                spec = TABLES[name].columns[column]
                self.assertEqual(spec.nullable, nullable == 'NULL')
                if spec.kind == 'text':
                    self.assertEqual(sql_type, f'NVARCHAR({spec.size})')
                elif spec.kind == 'decimal':
                    self.assertEqual(sql_type.replace(' ', ''), f'DECIMAL({spec.size},{spec.scale})')
                else:
                    self.assertEqual(sql_type, {'int': 'INT', 'date': 'DATE', 'time': 'TIME(0)'}[spec.kind])
        self.assertEqual(seen, set(TABLES))

    def test_mage_block_chain_and_json_transport(self):
        import yaml
        path = PROJECT / 'pipelines/f1_source_to_stage/metadata.yaml'
        blocks = yaml.safe_load(path.read_text())['blocks']
        value = None
        for block in blocks[:2]:
            namespace = {'__name__': '__mage_block__', block['type']: lambda f: f}
            block_path = PROJECT / f'{block["type"]}s' / f'{block["uuid"]}.py'
            exec(compile(block_path.read_text(), str(block_path), 'exec'), namespace)
            fn = namespace[block['uuid']]
            value = fn(value, table_name='status') if value else fn(table_name='status')
            value = json.loads(json.dumps(value))
        self.assertTrue(value['validated'])
        self.assertTrue((PROJECT / 'data_exporters' / f'{blocks[-1]["uuid"]}.py').is_file())


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.engine = sqlite_handoff_engine()

    def tearDown(self):
        self.engine.dispose()

    def query(self, sql):
        with self.engine.connect() as conn:
            return conn.execute(text(sql)).mappings().all()

    def test_full_twice_has_same_keys_data_and_audit(self):
        p = payload()
        export_payload(p, self.engine)
        before = self.query('SELECT statusId,status FROM stg.status ORDER BY statusId')
        export_payload(p, self.engine)
        self.assertEqual(before, self.query('SELECT statusId,status FROM stg.status ORDER BY statusId'))
        logs = self.query('SELECT * FROM ctl.etl_run_log')
        self.assertEqual([r['run_status'] for r in logs], ['success', 'success'])
        self.assertEqual([r['rows_written'] for r in logs], [141, 141])
        self.assertEqual(len(self.query('SELECT * FROM ctl.etl_batch_state')), 1)

    def test_incremental_from_empty_rerun_and_update(self):
        for bound in ({'key_max': 70}, {'key_min': 71}, {'key_min': 71}):
            export_payload(payload(load_mode='incremental', **bound), self.engine)
        self.assertEqual(len(self.query('SELECT * FROM stg.status')), 141)
        p = payload(load_mode='incremental', key_min=71)
        p['rows'][0]['status'] = 'Updated label'
        export_payload(p, self.engine)
        rows = self.query('SELECT * FROM stg.status')
        self.assertEqual(len(rows), 141)
        self.assertEqual(sum(row['status'] == 'Updated label' for row in rows), 1)

    def test_reused_batch_label_does_not_erase_unrelated_keys(self):
        export_payload(payload(load_mode='incremental', batch_key='same', key_max=70), self.engine)
        export_payload(payload(load_mode='incremental', batch_key='same', key_min=71), self.engine)
        self.assertEqual(len(self.query('SELECT * FROM stg.status')), 141)

    def test_failure_after_delete_rolls_back_and_retry_succeeds(self):
        export_payload(payload(), self.engine)
        before = self.query('SELECT * FROM stg.status ORDER BY statusId')
        def fail(conn, data, run_id):
            write_stage(conn, data, run_id)
            raise RuntimeError('password=SHOULD_NEVER_APPEAR')
        with self.assertRaises(EtlRunError) as error:
            export_payload(payload(), self.engine, writer=fail)
        self.assertNotIn('SHOULD_NEVER_APPEAR', str(error.exception))
        self.assertEqual(before, self.query('SELECT * FROM stg.status ORDER BY statusId'))
        log = self.query("SELECT * FROM ctl.etl_run_log WHERE run_status='failed'")[0]
        self.assertEqual(log['rows_written'], 0)
        self.assertNotIn('SHOULD_NEVER_APPEAR', log['error_message'])
        self.assertEqual(self.query('SELECT batch_status FROM ctl.etl_batch_state')[0]['batch_status'], 'failed')
        export_payload(payload(), self.engine)
        self.assertEqual(self.query('SELECT batch_status FROM ctl.etl_batch_state')[0]['batch_status'], 'success')

    def test_success_audit_error_rolls_back_stage(self):
        export_payload(payload(), self.engine)
        before = self.query('SELECT * FROM stg.status ORDER BY statusId')
        with self.engine.begin() as conn:
            conn.exec_driver_sql("""CREATE TRIGGER ctl.reject_success BEFORE UPDATE ON etl_run_log
                WHEN NEW.run_status='success' BEGIN SELECT RAISE(ABORT, 'test audit failure'); END""")
        p = payload()
        p['rows'][0]['status'] = 'Must roll back'
        with self.assertRaises(EtlRunError):
            export_payload(p, self.engine)
        self.assertEqual(before, self.query('SELECT * FROM stg.status ORDER BY statusId'))
        self.assertEqual(len(self.query("SELECT * FROM ctl.etl_run_log WHERE run_status='failed'")), 1)

    def test_source_and_validation_failures_have_ctl_records(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'status.csv').write_text('wrong,header\n1,X\n')
            bad_source = load_payload({'table_name': 'status'}, root)
        bad_key = payload()
        bad_key['rows'][0]['statusId'] = None
        for p in (bad_source, bad_key):
            with self.assertRaises(EtlRunError):
                export_payload(p, self.engine)
        logs = self.query('SELECT * FROM ctl.etl_run_log')
        self.assertEqual([r['run_status'] for r in logs], ['failed', 'failed'])
        self.assertEqual(logs[1]['rows_rejected'], 1)
        self.assertEqual(self.query('SELECT * FROM stg.status'), [])

    def test_missing_incremental_source_preserves_failed_batch_identity(self):
        with tempfile.TemporaryDirectory() as root:
            p = load_payload({'table_name': 'status', 'load_mode': 'incremental',
                              'key_min': 71, 'batch_key': 'missing_source'}, root)
        with self.assertRaises(EtlRunError):
            export_payload(p, self.engine)
        state = self.query('SELECT * FROM ctl.etl_batch_state')[0]
        self.assertEqual((state['source_name'], state['source_table'], state['batch_key'], state['batch_status']),
                         ('status.csv', 'status', 'missing_source', 'failed'))

    def test_all_core_typed_inserts_counts_nulls_and_fk_reconciliation(self):
        for name in TABLES:
            export_payload(payload(name), self.engine)
        report = check_stage(self.engine)
        self.assertEqual(sum(report['counts'].values()), 30121)
        self.assertEqual([r['orphan_count'] for r in report['relationships']], [0] * 6)
        rows = self.query('SELECT position FROM stg.results WHERE position IS NULL')
        self.assertEqual(len(rows), 11074)
        self.assertEqual(len(self.query("SELECT * FROM stg.drivers WHERE nationality='' AND url=''")), 14)
        with self.engine.begin() as conn:
            conn.execute(text('UPDATE stg.results SET driverId=999999 WHERE resultId=1'))
        report = check_stage(self.engine)
        self.assertEqual(sum(r['orphan_count'] for r in report['relationships']), 1)


if __name__ == '__main__':
    unittest.main()
