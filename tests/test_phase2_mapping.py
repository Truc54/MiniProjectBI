"""Phase 2 (Loc): consistency tests for the stg -> dw mapping deliverables.

Checks that the status mapping CSV, the generated stg_status SQL, the expected
baseline JSON and the two Markdown specs agree with each other and with the source CSVs.
No database needed. Run: python3 -m unittest tests.test_phase2_mapping -v
"""

import json
from pathlib import Path
import re
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))

import phase2_expected_baseline as base  # noqa: E402

DOCS = ROOT / 'docs/02_data_dictionary_and_mapping'
NA = ['\\N']
GROUPS = {'CLASSIFIED', 'DNS', 'DSQ', 'RETIREMENT_DNF', 'OTHER'}
CATEGORY_GROUP = {
    'FINISHED_OR_LAPPED': 'CLASSIFIED', 'DID_NOT_START': 'DNS', 'DISQUALIFIED': 'DSQ',
    'NOT_QUALIFIED_OR_NOT_CLASSIFIED': 'OTHER', 'MECHANICAL': 'RETIREMENT_DNF',
    'ACCIDENT_DAMAGE': 'RETIREMENT_DNF', 'DRIVER_MEDICAL': 'RETIREMENT_DNF',
    'OTHER_RETIREMENT': 'RETIREMENT_DNF',
}


def result_outcome_code(text: str) -> str:
    """Python port of the SQL CASE in stage_to_dw_mapping.md section 5.3."""
    codes = {'R': 'RETIRED', 'D': 'DISQUALIFIED', 'E': 'EXCLUDED', 'W': 'WITHDRAWN',
             'F': 'FAILED_TO_QUALIFY', 'N': 'NOT_CLASSIFIED'}
    return 'CLASSIFIED' if text.isdigit() else codes.get(text, 'UNKNOWN')


def backtick_names(markdown: str, start: str, end: str) -> list[str]:
    """First-column `names` of the Markdown tables between two headings."""
    section = markdown.split(start, 1)[1].split(end, 1)[0]
    names = []
    for line in section.splitlines():
        first = line.split('|')[1] if line.startswith('|') else ''
        names += re.findall(r'`([a-z_]+)`', first)
    return names


class StatusMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = pd.read_csv(DOCS / 'status_outcome_mapping.csv')
        cls.status = pd.read_csv(ROOT / 'dataset/status.csv')
        cls.results = pd.read_csv(ROOT / 'dataset/results.csv', na_values=NA, keep_default_na=False)

    def test_covers_all_141_source_statuses_once(self):
        self.assertEqual(len(self.mapping), 141)
        self.assertTrue(self.mapping.statusId.is_unique)
        merged = self.status.merge(self.mapping, on='statusId', suffixes=('_src', '_map'))
        self.assertEqual(len(merged), 141)
        self.assertTrue((merged.status_src == merged.status_map).all())

    def test_groups_and_categories_are_valid_and_consistent(self):
        self.assertLessEqual(set(self.mapping.outcome_group), GROUPS)
        self.assertNotIn('UNREVIEWED', set(self.mapping.outcome_category))
        expected = self.mapping.outcome_category.map(CATEGORY_GROUP)
        self.assertTrue((expected == self.mapping.outcome_group).all())

    def test_csv_equals_classifier(self):
        for row in self.mapping.itertuples():
            self.assertEqual(base.classify(row.status), (row.outcome_group, row.outcome_category),
                             row.status)

    def test_dns_dsq_not_merged_into_dnf(self):
        group = dict(zip(self.mapping.status, self.mapping.outcome_group))
        self.assertEqual(group['Did not start'], 'DNS')
        self.assertEqual(group['Withdrew'], 'DNS')
        self.assertEqual(group['Disqualified'], 'DSQ')
        self.assertEqual(group['Excluded'], 'DSQ')
        self.assertEqual(group['Engine'], 'RETIREMENT_DNF')
        self.assertEqual(group['Accident'], 'RETIREMENT_DNF')

    def test_label_sets_are_pairwise_disjoint(self):
        base.assert_disjoint()
        # Guard must catch an overlap between only two sets (old check needed all four).
        base.LABEL_SETS['MECHANICAL'] = base.MECHANICAL | {'Withdrew'}
        try:
            with self.assertRaises(AssertionError):
                base.assert_disjoint()
        finally:
            base.LABEL_SETS['MECHANICAL'] = base.MECHANICAL

    def test_result_rows_column_matches_results(self):
        usage = self.results.statusId.value_counts()
        for row in self.mapping.itertuples():
            self.assertEqual(row.result_rows, int(usage.get(row.statusId, 0)), row.status)
        self.assertEqual(self.mapping.result_rows.sum(), len(self.results))


class GeneratedSqlTests(unittest.TestCase):
    def test_sql_file_is_up_to_date(self):
        current = (DOCS / 'stg_status_outcome.sql').read_text(encoding='utf-8')
        self.assertEqual(current, base.render_status_sql(),
                         'Run python3 tests/phase2_expected_baseline.py')

    def test_every_reviewed_label_appears_exactly_once(self):
        sql = (DOCS / 'stg_status_outcome.sql').read_text(encoding='utf-8')
        for labels in base.LABEL_SETS.values():
            for label in labels:
                self.assertEqual(sql.count(f"N'{label}'"), 1, label)

    def test_laps_like_patterns_match_python_regex(self):
        # SQL: like N'+[0-9]% Lap' or like N'+[0-9]% Laps'  <=>  ^\+[0-9]+ Laps?$ on source labels
        def sql_like(s):
            return bool(re.fullmatch(r'\+[0-9].* Laps?', s))
        for label in pd.read_csv(ROOT / 'dataset/status.csv').status:
            self.assertEqual(sql_like(label), bool(base.LAPS_PATTERN.match(label)), label)


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads((ROOT / 'docs/evidence/loc_phase2_expected_baseline.json').read_text())
        cls.results = pd.read_csv(ROOT / 'dataset/results.csv', na_values=NA, keep_default_na=False)

    def test_outcome_totals_reconcile(self):
        og = self.baseline['outcome_group']
        self.assertEqual(sum(og['status_codes'].values()), 141)
        self.assertEqual(sum(og['result_rows'].values()), len(self.results))
        self.assertEqual(sum(og['result_rows_retirement_category'].values()),
                         og['result_rows']['RETIREMENT_DNF'])

    def test_measures_recomputed_independently(self):
        r, m = self.results, self.baseline['measures']
        self.assertEqual(self.baseline['row_counts']['fact_race_result'], len(r))
        self.assertAlmostEqual(m['sum_points'], round(float(r.points.sum()), 2))
        eligible = (r.grid > 0) & r.position.notna()
        self.assertEqual(m['places_gained_eligible_rows'], int(eligible.sum()))
        self.assertEqual(m['places_gained_sum'], int((r.grid - r.position)[eligible].sum()))
        self.assertEqual(m['win_rows_position_order_1'], int((r.positionOrder == 1).sum()))
        self.assertEqual(m['podium_rows_position_1_to_3'], int(r.position.between(1, 3).sum()))

    def test_result_outcome_code_has_no_unknown(self):
        codes = self.results.positionText.map(result_outcome_code).value_counts()
        self.assertNotIn('UNKNOWN', codes)
        self.assertEqual(int(codes['WITHDRAWN']), self.baseline['position_text_rows']['W'])
        self.assertEqual(int(codes['CLASSIFIED']), self.baseline['position_text_rows']['numeric'])

    def test_dim_date_range_covers_all_race_dates(self):
        races = pd.read_csv(ROOT / 'dataset/races.csv')
        self.assertGreaterEqual(races.date.min(), '1950-01-01')
        self.assertLessEqual(races.date.max(), '2026-12-31')
        days = (pd.Timestamp('2026-12-31') - pd.Timestamp('1950-01-01')).days + 1
        self.assertEqual(days, 28124)

    def test_points_eras_match_spec(self):
        """Max winner points per season = stage_to_dw_mapping.md section 8.1."""
        races = pd.read_csv(ROOT / 'dataset/races.csv')[['raceId', 'year']]
        wins = self.results[self.results.positionOrder == 1].merge(races, on='raceId')
        actual = wins.groupby('year').points.max().to_dict()
        for year, points in actual.items():
            self.assertEqual(points, base.expected_max_winner_points(year), year)


class DocumentConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping_md = (DOCS / 'stage_to_dw_mapping.md').read_text(encoding='utf-8')
        cls.dictionary_md = (DOCS / 'dw_data_dictionary.md').read_text(encoding='utf-8')
        cls.baseline = json.loads((ROOT / 'docs/evidence/loc_phase2_expected_baseline.json').read_text())

    def test_section_4_1_numbers_match_baseline(self):
        og = self.baseline['outcome_group']
        for group in GROUPS:
            codes = og['status_codes'][group]
            rows = f"{og['result_rows'][group]:,}".replace(',', '.')
            self.assertRegex(self.mapping_md, rf"\| `{group}` \| {codes} \| {re.escape(rows)} \|")

    def test_fact_columns_identical_in_mapping_and_dictionary(self):
        mapping_cols = backtick_names(self.mapping_md, '### 5.2', 'Bộ lọc incremental')
        dict_cols = backtick_names(self.dictionary_md, '## 1. `dw.FactRaceResult`', '## 2.')
        self.assertEqual(set(mapping_cols), set(dict_cols))
        self.assertEqual(len(dict_cols), len(set(dict_cols)))

    def test_status_sql_is_referenced(self):
        self.assertIn('stg_status_outcome.sql', self.mapping_md)


if __name__ == '__main__':
    unittest.main()
