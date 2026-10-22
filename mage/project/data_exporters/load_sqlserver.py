import os
import uuid
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


TABLE_PRIMARY_KEYS = {
    'circuits': 'circuitId',
    'constructors': 'constructorId',
    'drivers': 'driverId',
    'status': 'statusId',
    'seasons': 'year',
    'races': 'raceId',
    'results': 'resultId',
}


def create_sqlserver_engine():
    """Create a SQLAlchemy engine using environment variables, never literals."""
    required = [
        'MSSQL_HOST',
        'MSSQL_PORT',
        'MSSQL_DATABASE',
        'MSSQL_USERNAME',
        'MSSQL_PASSWORD',
        'MSSQL_ODBC_DRIVER',
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError(f'Missing SQL Server environment variables: {missing}')

    connection_url = URL.create(
        'mssql+pyodbc',
        username=os.environ['MSSQL_USERNAME'],
        password=os.environ['MSSQL_PASSWORD'],
        host=os.environ['MSSQL_HOST'],
        port=int(os.environ['MSSQL_PORT']),
        database=os.environ['MSSQL_DATABASE'],
        query={
            'driver': os.environ['MSSQL_ODBC_DRIVER'],
            'Encrypt': os.environ.get('MSSQL_ENCRYPT', 'yes'),
            'TrustServerCertificate': os.environ.get('MSSQL_TRUST_CERTIFICATE', 'no'),
        },
    )
    return create_engine(connection_url, fast_executemany=True)


@data_exporter
def export_data_to_sqlserver(df: pd.DataFrame, **kwargs):
    """Transaction-safe, idempotent exporter to SQL Server staging and ctl audit tables.

    Supports both 'full' and 'incremental' load modes.
    Maintains run history in ctl.etl_run_log and batch states in ctl.etl_batch_state.
    Rerunning the same batch will overwrite existing records without creating duplicates.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError('Expected a non-empty pandas DataFrame to export')

    schema_name = kwargs.get('schema_name', 'stg')
    table_name = kwargs.get('target_table')
    if not table_name:
        table_name = kwargs.get('table_name', 'results')
    table_name = table_name.lower().replace('.csv', '')

    file_name = kwargs.get('file_name', f'{table_name}.csv')
    load_mode = kwargs.get('load_mode', 'full').lower()
    now_utc = datetime.now(timezone.utc)
    batch_key = kwargs.get('batch_key') or f'{load_mode}_{now_utc.strftime("%Y%m%d_%H%M%S")}'
    run_id = str(uuid.uuid4())
    pipeline_name = kwargs.get('pipeline_uuid', 'f1_source_to_stage')

    # Prepare DataFrame and normalize metadata columns per Contract Section 5
    export_df = df.copy()

    # Convert empty strings and literal \N to None (SQL NULL) per Contract Section 1
    export_df = export_df.replace({'': None, r'\N': None})

    # Drop legacy columns if present
    for legacy_col in ['source_file', '_source_file', '_ingested_at_utc']:
        if legacy_col in export_df.columns:
            export_df = export_df.drop(columns=[legacy_col])

    export_df['_src_file'] = file_name
    export_df['_batch_key'] = batch_key
    export_df['_loaded_at_utc'] = now_utc
    export_df['_load_mode'] = load_mode.upper()

    engine = create_sqlserver_engine()

    # 1. Initialize run record in ctl.etl_run_log
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO ctl.etl_run_log (
                    run_id, pipeline_name, source_file, target_schema, target_table,
                    load_mode, batch_key, run_status, started_at_utc,
                    rows_read, rows_written, rows_rejected
                ) VALUES (
                    :run_id, :pipeline_name, :source_file, :target_schema, :target_table,
                    :load_mode, :batch_key, 'running', :started_at,
                    :rows_read, 0, 0
                )
            """),
            {
                'run_id': run_id,
                'pipeline_name': pipeline_name,
                'source_file': file_name,
                'target_schema': schema_name,
                'target_table': table_name,
                'load_mode': load_mode,
                'batch_key': batch_key,
                'started_at': now_utc,
                'rows_read': len(export_df),
            },
        )

    # 2. Execute Data Load Transaction
    try:
        with engine.begin() as conn:
            if load_mode == 'full':
                # Full load: clear existing staging table for fresh snapshot
                conn.execute(text(f"DELETE FROM {schema_name}.{table_name}"))
            elif load_mode == 'incremental':
                # Incremental: remove existing records matching current batch to ensure rerun idempotency
                conn.execute(
                    text(f"DELETE FROM {schema_name}.{table_name} WHERE _batch_key = :bkey"),
                    {'bkey': batch_key},
                )
                pk_col = TABLE_PRIMARY_KEYS.get(table_name)
                if pk_col and pk_col in export_df.columns:
                    pks = export_df[pk_col].dropna().unique().tolist()
                    # Delete any matching natural keys in chunks if needed
                    chunk_size = 1000
                    for i in range(0, len(pks), chunk_size):
                        sub_pks = pks[i:i + chunk_size]
                        in_clause = ', '.join([f"'{k}'" for k in sub_pks])
                        conn.execute(text(f"DELETE FROM {schema_name}.{table_name} WHERE {pk_col} IN ({in_clause})"))

            # Bulk append to staging table
            export_df.to_sql(
                name=table_name,
                con=conn,
                schema=schema_name,
                if_exists='append',
                index=False,
                chunksize=1000,
            )

            # Record batch state in ctl.etl_batch_state
            conn.execute(
                text("""
                    MERGE ctl.etl_batch_state AS target
                    USING (SELECT :source_name AS source_name, :source_table AS source_table, :batch_key AS batch_key) AS source
                    ON (target.source_name = source.source_name AND target.source_table = source.source_table AND target.batch_key = source.batch_key)
                    WHEN MATCHED THEN
                        UPDATE SET
                            source_row_count = :row_count,
                            last_run_id = :run_id,
                            loaded_at_utc = :loaded_at,
                            batch_status = 'success'
                    WHEN NOT MATCHED THEN
                        INSERT (source_name, source_table, batch_key, source_row_count, last_run_id, loaded_at_utc, batch_status)
                        VALUES (:source_name, :source_table, :batch_key, :row_count, :run_id, :loaded_at, 'success');
                """),
                {
                    'source_name': file_name,
                    'source_table': table_name,
                    'batch_key': batch_key,
                    'row_count': len(export_df),
                    'run_id': run_id,
                    'loaded_at': datetime.now(timezone.utc),
                },
            )

        # 3. Log Success
        completed_at = datetime.now(timezone.utc)
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE ctl.etl_run_log
                    SET run_status = 'success',
                        completed_at_utc = :completed_at,
                        rows_written = :rows_written
                    WHERE run_id = :run_id
                """),
                {
                    'run_id': run_id,
                    'completed_at': completed_at,
                    'rows_written': len(export_df),
                },
            )

    except Exception as exc:
        # 4. Log Failure
        failed_at = datetime.now(timezone.utc)
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE ctl.etl_run_log
                    SET run_status = 'failed',
                        completed_at_utc = :failed_at,
                        error_message = :error_message
                    WHERE run_id = :run_id
                """),
                {
                    'run_id': run_id,
                    'failed_at': failed_at,
                    'error_message': str(exc)[:4000],
                },
            )
        raise exc

    return {
        'status': 'success',
        'run_id': run_id,
        'table': f'{schema_name}.{table_name}',
        'rows_written': len(export_df),
        'batch_key': batch_key,
    }
