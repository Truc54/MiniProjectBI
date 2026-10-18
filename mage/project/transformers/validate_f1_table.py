if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer


REQUIRED_COLUMNS = {
    'results': ['resultId', 'raceId', 'driverId', 'constructorId', 'statusId'],
    'races': ['raceId', 'year', 'round', 'circuitId', 'date'],
    'drivers': ['driverId', 'forename', 'surname'],
    'constructors': ['constructorId', 'name'],
    'circuits': ['circuitId', 'name', 'country'],
    'status': ['statusId', 'status'],
    'seasons': ['year'],
}

UNIQUE_SOURCE_KEYS = {
    'results': ['resultId'],
    'races': ['raceId'],
    'drivers': ['driverId'],
    'constructors': ['constructorId'],
    'circuits': ['circuitId'],
    'status': ['statusId'],
    'seasons': ['year'],
}


@transformer
def validate_f1_table(df, *args, **kwargs):
    """Basic source-structure checks; optional fields are allowed to be NULL."""
    table_name = kwargs.get('table_name', 'results').lower()
    required = REQUIRED_COLUMNS.get(table_name)
    if required is None:
        raise ValueError(f'No Phase 1 validation rules are defined for {table_name!r}')

    missing_columns = [column for column in required if column not in df.columns]
    if missing_columns:
        raise ValueError(f'{table_name}: missing required columns {missing_columns}')

    key_columns = UNIQUE_SOURCE_KEYS[table_name]
    if df[key_columns].isna().any().any():
        raise ValueError(f'{table_name}: source key columns cannot be NULL: {key_columns}')
    if df.duplicated(subset=key_columns).any():
        raise ValueError(f'{table_name}: duplicate source keys detected: {key_columns}')

    return df
