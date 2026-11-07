import os
from datetime import datetime, timezone
from sqlalchemy import text

if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@custom
def commit_batch_watermark(*args, **kwargs):
    """
    Commit batch watermark to ctl.etl_batch_state only after dbt transformation succeeds.
    If dbt fails, this downstream block is aborted and batch_state remains uncommitted.
    """
    context = kwargs.get('context', {})
    execution_date = kwargs.get('execution_date') or datetime.now(timezone.utc)

    table_name = kwargs.get('table_name') or kwargs.get('target_table') or context.get('table_name') or 'all_tables'
    batch_key = (
        kwargs.get('batch_key')
        or context.get('batch_key')
        or (f"batch_{execution_date.strftime('%Y%m%d_%H%M%S')}" if hasattr(execution_date, 'strftime') else str(execution_date))
    )

    result = {
        'status': 'committed',
        'table_name': table_name,
        'batch_key': batch_key,
        'watermark_committed_at_utc': datetime.now(timezone.utc).isoformat()
    }

    try:
        from f1_etl.sqlserver import create_sqlserver_engine
        engine = create_sqlserver_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                MERGE INTO ctl.etl_batch_state AS target
                USING (SELECT :source_name AS source_name, :source_table AS source_table, :batch_key AS batch_key) AS src
                ON (target.source_name = src.source_name AND target.source_table = src.source_table AND target.batch_key = src.batch_key)
                WHEN MATCHED THEN
                    UPDATE SET batch_status = 'success', loaded_at_utc = :loaded_at
                WHEN NOT MATCHED THEN
                    INSERT (source_name, source_table, batch_key, batch_status, loaded_at_utc)
                    VALUES (src.source_name, src.source_table, src.batch_key, 'success', :loaded_at);
            """), {
                'source_name': f"{table_name}.csv",
                'source_table': table_name,
                'batch_key': batch_key,
                'loaded_at': datetime.now(timezone.utc)
            })
            result['db_committed'] = True
    except Exception as exc:
        result['db_committed'] = False
        result['db_error'] = str(exc)

    return result

