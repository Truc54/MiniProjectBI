"""Atomic stage writes and audit compatible with Dung commit 5b7113f."""

from contextlib import contextmanager
from datetime import datetime, timezone
import os
import uuid

from sqlalchemy import MetaData, Table, bindparam, create_engine, delete, text
from sqlalchemy.engine import URL

from .contract import LINEAGE, QualityError, TABLES, resolve_request
from .source import safe_error, typed_rows, validate_payload


class EtlRunError(RuntimeError):
    pass


def utcnow():
    # SQL DATETIME2 stores UTC without a timezone offset.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_sqlserver_engine():
    required = ('MSSQL_HOST', 'MSSQL_PORT', 'MSSQL_DATABASE', 'MSSQL_USERNAME',
                'MSSQL_PASSWORD', 'MSSQL_ODBC_DRIVER')
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise QualityError(f'Missing SQL Server environment variables: {missing}')
    url = URL.create(
        'mssql+pyodbc', username=os.environ['MSSQL_USERNAME'],
        password=os.environ['MSSQL_PASSWORD'], host=os.environ['MSSQL_HOST'],
        port=int(os.environ['MSSQL_PORT']), database=os.environ['MSSQL_DATABASE'],
        query={'driver': os.environ['MSSQL_ODBC_DRIVER'],
               'Encrypt': os.environ.get('MSSQL_ENCRYPT', 'yes'),
               'TrustServerCertificate': os.environ.get('MSSQL_TRUST_CERTIFICATE', 'no')},
    )
    return create_engine(url, future=True, fast_executemany=True, hide_parameters=True,
                         pool_pre_ping=True, connect_args={'timeout': 10})


@contextmanager
def table_lock(conn, table):
    """Serialize full/incremental runs on a table, including audit state changes."""
    locked = False
    resource = f'f1_source_to_stage:stg.{table}'
    try:
        if conn.dialect.name == 'mssql':
            with conn.begin():
                code = conn.execute(text("""
                    DECLARE @result INT;
                    EXEC @result = sys.sp_getapplock @Resource=:resource,
                        @LockMode='Exclusive', @LockOwner='Session', @LockTimeout=30000;
                    SELECT @result;
                """), {'resource': resource}).scalar_one()
                if code < 0:
                    raise QualityError('Could not acquire ETL table lock; retry later')
            locked = True
        yield
    finally:
        if locked and not conn.invalidated:
            try:
                with conn.begin():
                    conn.execute(text("""
                        EXEC sys.sp_releaseapplock @Resource=:resource, @LockOwner='Session';
                    """), {'resource': resource})
            except Exception:
                conn.invalidate()  # Closing the DB session releases its locks.


def set_batch(conn, params, status, row_count=0):
    values = dict(params, batch_status=status, row_count=row_count,
                  loaded_at=utcnow() if status == 'success' else None)
    found = conn.execute(text("""
        SELECT batch_status FROM ctl.etl_batch_state
        WHERE source_name=:source_file AND source_table=:target_table AND batch_key=:batch_key
    """), values).first()
    if found:
        conn.execute(text("""
            UPDATE ctl.etl_batch_state SET source_row_count=:row_count,
                last_run_id=:run_id, loaded_at_utc=:loaded_at, batch_status=:batch_status
            WHERE source_name=:source_file AND source_table=:target_table AND batch_key=:batch_key
        """), values)
    else:
        conn.execute(text("""
            INSERT INTO ctl.etl_batch_state
                (source_name, source_table, batch_key, source_row_count,
                 last_run_id, loaded_at_utc, batch_status)
            VALUES (:source_file, :target_table, :batch_key, :row_count,
                    :run_id, :loaded_at, :batch_status)
        """), values)


def reflect_stage(conn, table_name):
    stage = Table(table_name, MetaData(), schema='stg', autoload_with=conn)
    if set(stage.c.keys()) != set(TABLES[table_name].columns) | set(LINEAGE):
        raise QualityError(f'stg.{table_name}: columns differ from Dung contract 5b7113f')
    if [col.name for col in stage.primary_key] != [TABLES[table_name].key]:
        raise QualityError(f'stg.{table_name}: natural primary key differs from contract')
    return stage


def write_stage(conn, payload, run_id):
    context = resolve_request(payload['context'])
    stage = reflect_stage(conn, context['table_name'])
    records = typed_rows(payload)
    ingested = utcnow()
    for row in records:
        row.update(_source_file=context['file_name'], _batch_key=context['batch_key'],
                   _load_mode=context['load_mode'], _ingested_at_utc=ingested)
    key = TABLES[context['table_name']].key
    if context['load_mode'] == 'full':
        conn.execute(delete(stage))
    else:
        # Batch labels alone never determine deletes or cause successful runs to be skipped.
        keys = [row[key] for row in records]
        statement = delete(stage).where(stage.c[key].in_(bindparam('keys', expanding=True)))
        for offset in range(0, len(keys), 500):
            conn.execute(statement, {'keys': keys[offset:offset + 500]})
    for offset in range(0, len(records), 500):
        conn.execute(stage.insert(), records[offset:offset + 500])
    return len(records)


def export_payload(payload, engine=None, writer=None):
    """Audit source/validation/load failures; success state shares the data commit.

    SQLite engines are accepted only for local transaction tests. Production
    engine creation always uses mssql+pyodbc and does not create/replace tables.
    """
    own_engine = engine is None
    run_id = str(uuid.uuid4())
    context = payload.get('context', {})
    params = dict(run_id=run_id, pipeline_name='f1_source_to_stage',
                  source_file=context.get('file_name'), target_schema='stg',
                  target_table=context.get('target_table') or context.get('table_name'),
                  load_mode=context.get('load_mode'), batch_key=context.get('batch_key'),
                  started_at=utcnow(), rows_read=payload.get('rows_read', 0))
    valid_context = False
    try:
        try:
            resolved = resolve_request(context)
            valid_context = True
            params.update(source_file=resolved['file_name'], target_table=resolved['table_name'],
                          load_mode=resolved['load_mode'], batch_key=resolved['batch_key'])
        except QualityError:
            pass  # Invalid requests are audited, never passed to write_stage.
        engine = engine or create_sqlserver_engine()
        with engine.connect() as conn, table_lock(conn, params['target_table'] or 'invalid'):
            with conn.begin():
                conn.execute(text("""
                    INSERT INTO ctl.etl_run_log
                        (run_id, pipeline_name, source_file, target_schema, target_table,
                         load_mode, batch_key, run_status, started_at_utc,
                         rows_read, rows_written, rows_rejected)
                    VALUES (:run_id, :pipeline_name, :source_file, :target_schema, :target_table,
                            :load_mode, :batch_key, 'running', :started_at, :rows_read, 0, 0)
                """), params)
                if valid_context:
                    set_batch(conn, params, 'in_progress')
            try:
                checked = payload if payload.get('error') else validate_payload(payload)
                if checked.get('error'):
                    raise QualityError(checked['error'], checked.get('rows_rejected', 0))
                if not valid_context:
                    raise QualityError('Invalid ETL runtime variables')
                with conn.begin():
                    written = (writer or write_stage)(conn, checked, run_id)
                    if resolved['load_mode'] == 'full':
                        # Full snapshots supersede earlier checkpoints, but retain run history.
                        conn.execute(text("""
                            DELETE FROM ctl.etl_batch_state
                            WHERE source_name=:source_file AND source_table=:target_table
                        """), params)
                    set_batch(conn, params, 'success', written)
                    conn.execute(text("""
                        UPDATE ctl.etl_run_log SET run_status='success',
                            completed_at_utc=:completed_at, rows_written=:written,
                            rows_read=:read, rows_rejected=0 WHERE run_id=:run_id
                    """), dict(params, completed_at=utcnow(), written=written, read=checked['rows_read']))
                return dict(status='success', run_id=run_id, table=f'stg.{resolved["table_name"]}',
                            batch_key=resolved['batch_key'], rows_read=checked['rows_read'],
                            rows_written=written, rows_rejected=0)
            except Exception as exc:
                message = safe_error(exc)
                with conn.begin():
                    conn.execute(text("""
                        UPDATE ctl.etl_run_log SET run_status='failed',
                            completed_at_utc=:completed_at, rows_written=0,
                            rows_rejected=:rejected, error_message=:error WHERE run_id=:run_id
                    """), dict(params, completed_at=utcnow(), rejected=getattr(exc, 'rejected', 0), error=message))
                    if valid_context:
                        set_batch(conn, params, 'failed')
                raise EtlRunError(f'run_id={run_id}: {message}') from None
    except EtlRunError:
        raise
    except Exception as exc:
        raise EtlRunError(f'run_id={run_id}: {safe_error(exc)}; ctl audit may be unavailable') from None
    finally:
        if own_engine and engine is not None:
            engine.dispose()


def check_stage(engine):
    """Final FK acceptance after all parent/child tables have been loaded."""
    counts, relationships = {}, []
    with engine.connect() as conn:
        for name, spec in TABLES.items():
            reflect_stage(conn, name)
            key = spec.key
            counts[name] = conn.execute(text(f'SELECT COUNT(*) FROM stg.[{name}]')).scalar_one()
            invalid = conn.execute(text(f"""
                SELECT [{key}] FROM stg.[{name}]
                GROUP BY [{key}] HAVING COUNT(*) > 1 OR [{key}] IS NULL
            """)).first()
            if invalid:
                raise QualityError(f'stg.{name}: NULL/duplicate natural key')
            for column, parent, parent_key in spec.references:
                query = (f'FROM stg.[{name}] c LEFT JOIN stg.[{parent}] p '
                         f'ON c.[{column}]=p.[{parent_key}] WHERE p.[{parent_key}] IS NULL')
                count = conn.execute(text(f'SELECT COUNT(*) {query}')).scalar_one()
                prefix = 'TOP (5) ' if conn.dialect.name == 'mssql' else ''
                suffix = '' if prefix else ' LIMIT 5'
                sample = conn.execute(text(
                    f'SELECT DISTINCT {prefix}c.[{column}] {query} ORDER BY c.[{column}]{suffix}'
                )).scalars().all()
                relationships.append(dict(relationship=f'{name}.{column}->{parent}.{parent_key}',
                                          orphan_count=count, sample=sample))
    return dict(counts=counts, relationships=relationships)
