from f1_etl.sqlserver import export_payload

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_sqlserver(payload, **kwargs):
    """Persist audit and fail the Mage run on any rejected input."""
    return export_payload(payload)
