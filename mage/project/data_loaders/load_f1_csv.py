import os
from pathlib import Path

import pandas as pd

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader


@data_loader
def load_f1_csv(*args, **kwargs):
    """Read one source CSV. Set file_name and table_name as runtime variables."""
    file_name = kwargs.get('file_name', 'results.csv')
    if Path(file_name).name != file_name or not file_name.lower().endswith('.csv'):
        raise ValueError('file_name must be a CSV filename without a directory path')

    data_dir = Path(os.environ.get('F1_DATA_DIR', '/home/src/dataset'))
    file_path = data_dir / file_name
    if not file_path.is_file():
        raise FileNotFoundError(f'Source CSV was not found: {file_path}')

    # Preserve source values as text at ingestion. Convert the source sentinel
    # \N to NULL, but do not turn missing values into zero.
    df = pd.read_csv(
        file_path,
        dtype='string',
        encoding='utf-8-sig',
        keep_default_na=False,
        na_values=[r'\N'],
    )
    df['source_file'] = file_name
    return df
