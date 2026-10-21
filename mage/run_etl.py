"""Run the same implementation as Mage; --dry-run needs only Python stdlib."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'project'))

from f1_etl.contract import QualityError, TABLES
from f1_etl.source import check_source_relationships, load_payload, safe_error, validate_payload


def source_summary(payload):
    if payload['error']:
        raise QualityError(payload['error'], payload['rows_rejected'])
    name = payload['context']['table_name']
    keys = sorted(int(row[TABLES[name].key]) for row in payload['rows'])
    return dict(table=name, source_rows=payload['source_rows'], batch_rows=len(keys),
                key_min=min(keys), key_max=max(keys),
                key_sha256=hashlib.sha256(','.join(map(str, keys)).encode()).hexdigest(),
                null_cells=sum(value is None for row in payload['rows'] for value in row.values()),
                empty_cells=sum(value == '' for row in payload['rows'] for value in row.values()))


def require_clean(report, payloads=None):
    if any(item['orphan_count'] for item in report['relationships']):
        raise QualityError(f'Orphan foreign keys: {report["relationships"]}')
    if payloads and report['counts'] != {name: len(p['rows']) for name, p in payloads.items()}:
        raise QualityError('Source/stage row counts differ')


def demo(engine, data_dir):
    """Explicit demo: replaces all seven staging tables, preserving ctl history."""
    from copy import deepcopy
    from sqlalchemy import text
    from f1_etl.sqlserver import EtlRunError, check_stage, export_payload
    payloads = {name: validate_payload(load_payload({'table_name': name}, data_dir)) for name in TABLES}
    for p in payloads.values():
        source_summary(p)
    local_fk = check_source_relationships(payloads)
    require_clean({'relationships': local_fk})
    evidence = {'full_runs': [], 'full_checks': [], 'incremental_runs': []}
    for _ in range(2):
        evidence['full_runs'].append([export_payload(p, engine) for p in payloads.values()])
        full_check = check_stage(engine)
        require_clean(full_check, payloads)
        evidence['full_checks'].append(full_check)
    # Only --demo performs this reset; ordinary incremental runs never clear Stage.
    with engine.begin() as conn:
        for name in reversed(TABLES):
            conn.execute(text(f'DELETE FROM stg.[{name}]'))
        conn.execute(text('DELETE FROM ctl.etl_batch_state'))
    for name, original in payloads.items():
        key = TABLES[name].key
        keys = sorted(int(row[key]) for row in original['rows'])
        pivot = keys[len(keys) // 2 - 1]
        for label, bound in [('part1', {'key_max': pivot}), ('part2', {'key_min': pivot + 1}),
                             ('part2', {'key_min': pivot + 1})]:
            variables = dict(table_name=name, load_mode='incremental', batch_key=label, **bound)
            p = validate_payload(load_payload(variables, data_dir))
            result = export_payload(p, engine)
            with engine.connect() as conn:
                actual = sorted(conn.execute(text(f'SELECT [{key}] FROM stg.[{name}]')).scalars())
            expected = [value for value in keys if value <= pivot] if label == 'part1' else keys
            if actual != expected:
                raise QualityError(f'stg.{name}: incremental key set differs from expected batch coverage')
            result.update(target_row_count=len(actual),
                          target_key_sha256=hashlib.sha256(','.join(map(str, actual)).encode()).hexdigest())
            evidence['incremental_runs'].append(result)
    final = check_stage(engine)
    require_clean(final, payloads)
    # Compare natural key sets as well as counts after full + incremental reruns.
    with engine.connect() as conn:
        for name, p in payloads.items():
            key = TABLES[name].key
            actual = set(conn.execute(text(f'SELECT [{key}] FROM stg.[{name}]')).scalars())
            if actual != {int(row[key]) for row in p['rows']}:
                raise QualityError(f'stg.{name}: source/stage key sets differ')
    bad = deepcopy(payloads['status'])
    bad['context']['batch_key'] = 'intentional_duplicate_failure'
    bad['rows'].append(dict(bad['rows'][0]))
    bad['rows_read'] += 1
    try:
        export_payload(bad, engine)
    except EtlRunError as exc:
        evidence['expected_failure'] = str(exc)
    else:
        raise QualityError('Failure demonstration unexpectedly passed')
    require_clean(check_stage(engine), payloads)
    evidence['stage'] = final
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--all', action='store_true', help='Load all seven core files in dependency order')
    action.add_argument('--table', choices=TABLES)
    action.add_argument('--check-stage', action='store_true')
    action.add_argument('--demo', action='store_true', help='Replace Stage; run full x2, incremental x2 + rerun and failure')
    parser.add_argument('--dry-run', action='store_true', help='Read and validate only; no SQL connection')
    parser.add_argument('--mode', choices=('full', 'incremental'), default='full')
    parser.add_argument('--batch-key')
    parser.add_argument('--key-min', type=int)
    parser.add_argument('--key-max', type=int)
    parser.add_argument('--data-dir')
    parser.add_argument('--evidence', type=Path, help='Write a JSON result (including failures)')
    args = parser.parse_args(argv)
    if args.dry_run and (args.demo or args.check_stage):
        parser.error('--dry-run applies to --all or --table')
    if args.all and args.mode == 'incremental':
        parser.error('Incremental bounds are per table; use --table')
    report = dict(status='running', timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  backend='source_only' if args.dry_run else 'sqlserver', runs=[])
    engine = None
    try:
        if not args.dry_run:
            # Does not override exported environment variables.
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).resolve().parents[1] / '.env')
            from f1_etl.sqlserver import check_stage, create_sqlserver_engine, export_payload
            engine = create_sqlserver_engine()
        if args.demo:
            report['demo'] = demo(engine, args.data_dir)
        elif args.check_stage:
            report['stage'] = check_stage(engine)
            require_clean(report['stage'])
        else:
            payloads = {}
            for name in (TABLES if args.all else [args.table]):
                variables = dict(table_name=name, load_mode=args.mode,
                                 batch_key=args.batch_key, key_min=args.key_min, key_max=args.key_max)
                p = validate_payload(load_payload(variables, args.data_dir))
                # Export before source_summary so invalid data gets a failed ctl record.
                if not args.dry_run:
                    report['runs'].append(export_payload(p, engine))
                report.setdefault('source', []).append(source_summary(p))
                payloads[name] = p
            if args.all:
                report['relationships'] = check_source_relationships(payloads)
                require_clean(report)
                if not args.dry_run:
                    report['stage'] = check_stage(engine)
                    require_clean(report['stage'], payloads)
        report['status'] = 'success'
    except Exception as exc:
        from f1_etl.source import safe_error
        # EtlRunError already contains a sanitized message and the audit run ID.
        message = str(exc) if type(exc).__name__ == 'EtlRunError' else safe_error(exc)
        report.update(status='failed', error=message)
    finally:
        if engine is not None:
            engine.dispose()
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(output + '\n', encoding='utf-8')
    return 0 if report['status'] == 'success' else 1


if __name__ == '__main__':
    sys.exit(main())
