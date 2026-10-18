import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


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
    """Starter exporter. Implement and review full/incremental idempotency first.

    Do not replace an existing staging table blindly or append reruns. Select a
    per-table source key, record the batch in ctl.etl_batch_state, then implement
    a transaction-safe load/merge strategy before enabling this block.
    """
    schema_name = kwargs.get('schema_name', 'stg')
    table_name = kwargs.get('target_table')
    if not table_name:
        raise ValueError('Set target_table as a Mage runtime variable')

    raise NotImplementedError(
        f'Load strategy for {schema_name}.{table_name} is intentionally left '
        'for the team to implement before writing to SQL Server.'
    )
