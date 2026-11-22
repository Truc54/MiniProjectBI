"""Phase 4 (Lộc) offline checks: Mage schedule triggers-as-code + QA-01/QA-02 evaluator.

No database or Mage server needed (live checks: mage/collect_phase4_schedule_evidence.py).
Run: python -m unittest tests.test_phase4_loc_schedule -v
"""

import importlib.util
import os
from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROJECT = Path(os.environ.get('USER_CODE_PATH', ROOT / 'mage/project'))
sys.path.insert(0, str(PROJECT))

from f1_etl.contract import resolve_request
from f1_etl.source import load_payload, validate_payload

PIPELINE_DIR = ROOT / 'mage/project/pipelines/f1_source_to_stage'


def load_collector():
    spec = importlib.util.spec_from_file_location(
        'collector', ROOT / 'mage/collect_phase4_schedule_evidence.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TriggerConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.triggers = {t['name']: t for t in
                        yaml.safe_load((PIPELINE_DIR / 'triggers.yaml').read_text())['triggers']}

    def test_expected_schedule_triggers_are_active(self):
        self.assertEqual(set(load_collector().SCHEDULE_TRIGGERS), set(self.triggers))
        for name, trigger in self.triggers.items():
            with self.subTest(name):
                self.assertEqual(trigger['schedule_type'], 'time')
                self.assertEqual(trigger['status'], 'active')
                self.assertTrue(trigger['settings']['skip_if_previous_running'])
                interval = trigger['schedule_interval']
                self.assertTrue(interval.startswith('@') or len(interval.split()) == 5, interval)

    def test_short_demo_cycles_do_not_overlap_and_daily_is_standard(self):
        full = self.triggers['f1_full_reload_every_30min']['schedule_interval'].split()[0]
        inc = self.triggers['f1_incremental_every_30min']['schedule_interval'].split()[0]
        self.assertFalse(set(full.split(',')) & set(inc.split(',')))
        self.assertEqual(self.triggers['f1_daily_production']['schedule_interval'], '@daily')

    def test_trigger_variables_pass_runtime_contract_and_select_rows(self):
        for name, trigger in self.triggers.items():
            with self.subTest(name):
                context = resolve_request(trigger['variables'])
                payload = validate_payload(load_payload(trigger['variables'], ROOT / 'dataset'))
                self.assertIsNone(payload['error'])
                expected = 22 if context['load_mode'] == 'incremental' else 27568
                self.assertEqual(len(payload['rows']), expected)

    def test_pipeline_serializes_runs_across_triggers(self):
        metadata = yaml.safe_load((PIPELINE_DIR / 'metadata.yaml').read_text())
        self.assertEqual(metadata['concurrency_config']['pipeline_run_limit_all_triggers'], 1)
        self.assertEqual([b['uuid'] for b in metadata['blocks']],
                         ['load_f1_csv', 'validate_f1_table', 'load_sqlserver',
                          'dbt_transformation', 'commit_watermark'])


class CommitWatermarkBlockTests(unittest.TestCase):
    """The scheduled run's last block must reuse export_payload's batch label and never fail silently."""

    def run_block(self, engine_factory, **kwargs):
        from unittest import mock
        import f1_etl.sqlserver
        path = PROJECT / 'custom/commit_watermark.py'
        namespace = {'__name__': '__mage_block__', 'custom': lambda f: f, 'test': lambda f: f}
        exec(compile(path.read_text(), str(path), 'exec'), namespace)
        with mock.patch.object(f1_etl.sqlserver, 'create_sqlserver_engine', engine_factory):
            return namespace['commit_batch_watermark'](**kwargs)

    def fake_engine(self):
        from contextlib import contextmanager
        from unittest import mock
        calls = []
        conn = mock.Mock(execute=lambda sql, params: calls.append(params))
        engine = mock.Mock(dispose=mock.Mock())
        engine.begin = contextmanager(lambda: (yield conn))
        return engine, calls

    def test_trigger_variables_map_to_stage_batch_labels(self):
        cases = [(dict(table_name='results', load_mode='full'), 'full'),
                 (dict(table_name='results', load_mode='incremental', key_min=27552, key_max=27573),
                  'keys_27552_27573'),
                 (dict(table_name='results', load_mode='incremental', batch_key='batch_2026_R15_AZE',
                       key_min=27552), 'batch_2026_R15_AZE')]
        for variables, expected in cases:
            engine, calls = self.fake_engine()
            result = self.run_block(lambda: engine, **variables)
            self.assertEqual(result['batch_key'], expected)
            self.assertEqual(calls[0]['batch_key'], expected)
            self.assertEqual(calls[0]['source_name'], 'results.csv')
            engine.dispose.assert_called_once()

    def test_database_error_fails_run_without_leaking_driver_text(self):
        def broken():
            raise ConnectionError('Login failed; PWD=secret-marker')
        with self.assertRaises(RuntimeError) as ctx:
            self.run_block(broken, table_name='results', load_mode='full')
        self.assertNotIn('secret-marker', str(ctx.exception))


class QaEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.c = load_collector()
        self.triggers = [dict(name='f1_full_reload_every_30min', status='active', schedule_type='time')]
        self.stage = dict(self.c.EXPECTED_STAGE)
        self.fail_row = dict(run_id='x', target_table='status', batch_key='b', run_status='failed',
                             load_mode='full', rows_rejected=1, error_message='duplicate natural key 1')

    def run_(self, status, mode):
        return dict(status=status, ctl_runs=[dict(load_mode=mode, run_status='success')])

    def ok_log(self):
        return [dict(load_mode='full', run_status='success'),
                dict(load_mode='incremental', run_status='success'), self.fail_row]

    def test_pass_when_all_criteria_met(self):
        runs = [self.run_('completed', 'incremental'), self.run_('completed', 'full')]
        qa = self.c.qa_checks(self.triggers, runs, self.ok_log(), self.stage, 27568)
        self.assertTrue(qa['QA-01']['pass'])
        self.assertTrue(qa['QA-02']['pass'])

    def test_qa01_needs_two_consecutive_auto_runs_with_both_modes(self):
        single = [self.run_('completed', 'full')]
        broken = [self.run_('completed', 'full'), self.run_('failed', 'full'),
                  self.run_('completed', 'incremental')]
        for runs in (single, broken):
            qa = self.c.qa_checks(self.triggers, runs, self.ok_log(), self.stage, 27568)
            self.assertFalse(qa['QA-01']['pass'])
        inactive = [dict(self.triggers[0], status='inactive')]
        runs = [self.run_('completed', 'incremental'), self.run_('completed', 'full')]
        self.assertFalse(self.c.qa_checks(inactive, runs, self.ok_log(), self.stage, 27568)['QA-01']['pass'])

    def test_qa02_rejects_dirty_dw_missing_failure_or_empty_error(self):
        runs = [self.run_('completed', 'incremental'), self.run_('completed', 'full')]
        cases = [
            (self.ok_log(), self.stage, 27569),
            (self.ok_log()[:2], self.stage, 27568),
            (self.ok_log()[:2] + [dict(self.fail_row, rows_rejected=0)], self.stage, 27568),
            (self.ok_log()[:2] + [dict(self.fail_row, error_message=None)], self.stage, 27568),
            (self.ok_log(), dict(self.stage, status=142), 27568),
            (self.ok_log() + [self.fail_row, self.fail_row], self.stage, 27568),
        ]
        for log, stage, fact in cases:
            self.assertFalse(self.c.qa_checks(self.triggers, runs, log, stage, fact)['QA-02']['pass'])


if __name__ == '__main__':
    unittest.main()
