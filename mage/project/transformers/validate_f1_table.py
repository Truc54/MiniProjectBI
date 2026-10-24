from f1_etl.source import validate_payload

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer


@transformer
def validate_f1_table(payload, *args, **kwargs):
    return validate_payload(payload)
