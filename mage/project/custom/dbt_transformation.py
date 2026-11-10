"""Run dbt build inside the Mage container (replaces buggy YAML dbt block)."""
import shutil
import subprocess
from pathlib import Path

if 'custom' not in globals():
    from mage_ai.data_preparation.decorators import custom
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@custom
def transform_custom(data, *args, **kwargs):
    """Run dbt run --select +fact_race_result via subprocess."""
    # Locate dbt project directory
    candidate_dirs = [
        Path('/home/src/project/dbt'),
        Path('/home/src/dbt'),
    ]
    dbt_dir = None
    for d in candidate_dirs:
        if d.exists() and (d / 'dbt_project.yml').exists():
            dbt_dir = d
            break
    if dbt_dir is None:
        raise RuntimeError('dbt project directory not found')

    dbt_bin = shutil.which('dbt') or 'dbt'

    # 1. dbt deps (install packages if any)
    deps = subprocess.run(
        [dbt_bin, 'deps', '--project-dir', str(dbt_dir), '--profiles-dir', str(dbt_dir)],
        capture_output=True, text=True,
    )
    print(deps.stdout)
    if deps.returncode != 0:
        print(deps.stderr)
        raise RuntimeError(f'dbt deps failed (exit {deps.returncode})')

    # 2. dbt run --select +fact_race_result
    run = subprocess.run(
        [dbt_bin, 'run', '--select', '+fact_race_result',
         '--project-dir', str(dbt_dir), '--profiles-dir', str(dbt_dir)],
        capture_output=True, text=True,
    )
    print(run.stdout)
    if run.returncode != 0:
        print(run.stderr)
        raise RuntimeError(f'dbt run failed (exit {run.returncode})')

    return {'dbt_status': 'success', 'stdout': run.stdout}


@test
def test_output(output, *args) -> None:
    assert output is not None, 'dbt returned no output'
    assert output.get('dbt_status') == 'success', 'dbt did not succeed'

