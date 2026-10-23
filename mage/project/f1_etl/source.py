"""Strict CSV ingestion. Payloads contain only JSON-compatible values for Mage."""

import csv
from datetime import datetime, timezone
import os
from pathlib import Path

from .contract import QualityError, TABLES, resolve_request


def safe_error(exc):
    # Never expose driver exception strings: they can include URLs, SQL and credentials.
    if isinstance(exc, QualityError):
        return str(exc)
    if isinstance(exc, FileNotFoundError):
        return 'Source CSV was not found'
    if isinstance(exc, (csv.Error, UnicodeError)):
        return 'Source CSV cannot be decoded/parsed as UTF-8 CSV'
    return f'{type(exc).__name__}: ETL operation failed; check connection, DDL and runtime configuration'


def read_source(variables, data_dir=None):
    context = resolve_request(variables)
    # Default also works for host CLI without an .env file.
    root = Path(data_dir or os.environ.get('F1_DATA_DIR') or
                Path(__file__).resolve().parents[3] / 'dataset').resolve()
    path = (root / context['file_name']).resolve()
    if path.parent != root:
        raise QualityError('Source path escapes dataset directory (including symlinks)')
    rows = []
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader, None)
        if header != list(TABLES[context['table_name']].columns):
            raise QualityError(f'{context["file_name"]}: header/order does not match source contract')
        for values in reader:
            if len(values) != len(header):
                raise QualityError(f'{context["file_name"]}: row shape error at CSV line {reader.line_num}', 1)
            # Contract P3-v1.0 (Phuc/Dung): both literal \N and empty string become SQL NULL.
            rows.append(dict(zip(header, (None if v in (r'\N', '') else v for v in values))))
    context['ingested_at_utc'] = datetime.now(timezone.utc).isoformat()
    return dict(context=context, rows=rows, source_rows=len(rows), rows_read=len(rows),
                rows_rejected=0, error=None, validated=False)


def load_payload(variables, data_dir=None):
    """Carry source failures to exporter so they too get ctl audit records."""
    context = None
    try:
        context = resolve_request(variables)
        return read_source(context, data_dir)
    except Exception as exc:
        # Values are audit-only until resolve_request succeeds; SQL uses bound parameters.
        if context is None:
            context = {k: str(variables[k])[:100] for k in
                       ('file_name', 'table_name', 'target_table', 'load_mode', 'batch_key', 'schema_name')
                       if variables.get(k) is not None}
        return dict(context=context, rows=[], source_rows=0, rows_read=0,
                    rows_rejected=getattr(exc, 'rejected', 0), error=safe_error(exc), validated=False)


def validate_payload(payload):
    if payload.get('error'):
        return payload
    result = dict(payload)
    try:
        context = resolve_request(payload['context'])
        spec = TABLES[context['table_name']]
        seen, rejected, first_error = set(), 0, None
        selected = []
        for index, row in enumerate(payload['rows'], 2):
            try:
                if set(row) != set(spec.columns):
                    raise QualityError('row columns do not match contract')
                parsed = {name: col.parse(row[name], f'{context["file_name"]}:{index}:{name}')
                          for name, col in spec.columns.items()}
                key = parsed[spec.key]
                if key in seen:
                    raise QualityError(f'{context["file_name"]}: duplicate natural key {key}')
                seen.add(key)
                if ((context['key_min'] is None or key >= context['key_min']) and
                        (context['key_max'] is None or key <= context['key_max'])):
                    selected.append(row)
            except QualityError as exc:
                rejected += 1
                first_error = first_error or str(exc)
        if rejected:
            raise QualityError(f'{first_error}; invalid rows={rejected}', rejected)
        if not selected:
            raise QualityError('Empty source/batch refused; no staging rows will be deleted')
        result.update(rows=selected, rows_read=len(selected), validated=True)
    except Exception as exc:
        result.update(error=safe_error(exc), rows_rejected=getattr(exc, 'rejected', 0), validated=False)
    return result


def typed_rows(payload):
    spec = TABLES[payload['context']['table_name']]
    return [{name: column.parse(row[name], name) for name, column in spec.columns.items()}
            for row in payload['rows']]


def check_source_relationships(payloads):
    """Run after all seven files are validated; report orphans without deleting rows."""
    reports = []
    keys = {name: {int(row[TABLES[name].key]) for row in p['rows']}
            for name, p in payloads.items()}
    for name, payload in payloads.items():
        for column, parent, parent_key in TABLES[name].references:
            if parent not in keys:
                raise QualityError(f'Missing parent source: {parent}')
            orphans = [None if row[column] is None else int(row[column]) for row in payload['rows']
                       if row[column] is None or int(row[column]) not in keys[parent]]
            reports.append(dict(relationship=f'{name}.{column}->{parent}.{parent_key}',
                                orphan_count=len(orphans), sample=sorted(set(orphans), key=str)[:5]))
    return reports
