from f1_etl.source import load_payload

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader


@data_loader
def load_f1_csv(*args, **kwargs):
    """Carry source errors to exporter so ctl can audit failed ingestion."""
    return load_payload(kwargs)
