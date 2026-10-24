# Formula 1 MiniProjectBI

## Repository folders

- `dataset/`: source CSV files from the selected Kaggle dataset; kept unchanged.
- `knowledge/`: course/reference materials.
- `plans/`: one Phase 1 team plan plus detailed plans for Phúc, Dũng, Lộc and Trực.
- `example/`: reference project structure (PostgreSQL example).
- `mage/`, `sqlserver/`, `dbt/`, `docs/`, `powerbi/`: this project's SQL Server-based BI scaffold.

## Data flow

Kaggle CSV files -> Mage.ai ingestion -> SQL Server schema `stg` -> dbt models -> SQL Server schema `dw` -> Power BI.

Mage handles source-to-staging ingestion. dbt is reserved for staging-to-warehouse transformations and dimensional models.

Dataset source: https://www.kaggle.com/datasets/atharvranjan/formula-1-world-championship-1950-present

## Local setup

1. Copy `.env.example` to `.env` and enter credentials for a SQL Server account created for this project. Do not commit `.env`.
2. Create or select the project database in SQL Server.
3. Apply Dung's DDL in `sqlserver/ddl/` (`00`–`03`, or `python sqlserver/run_all_ddl.py`); see [docs/sql_server_setup.md](docs/sql_server_setup.md) and [the ETL runbook](docs/etl_runbook.md).
4. The Mage Dockerfile checks/installs Microsoft ODBC Driver 18 inside the container. Host CLI use needs the driver on the host as well.
5. Configure SQL Server network access, then start Mage with Docker Compose.

The SQL Server instance is outside Compose. Set `MSSQL_HOST` in `.env` to `host.docker.internal` for a server on the Docker host, or Dung's reachable DNS/IP for his remote server. Host CLI/dbt may need a different hostname (often `localhost` for a local instance).

Mage implements strict source validation, transactional full/key-based incremental loads, natural-key reruns and `ctl` auditing against Dung's DDL in `sqlserver/ddl/` (commit `84081c0`); `\N` and empty strings load as NULL. Runtime variables: `file_name`, `table_name`, `target_table`, `load_mode`, `batch_key`, `key_min`, `key_max`. See [docs/etl_runbook.md](docs/etl_runbook.md) for UI steps, errors, retry and SQL Server demo commands. Integration passed on local SQL Server 2022 + Mage 0.9.79 on 2026-10-21; [live evidence](docs/evidence/loc_live_sqlserver_mage.json) records typed source/stage comparisons, reruns, rollback and audit checks. Runs used the Mage execution engine; UI login testing was deferred by the user.

Validate all seven source files without installing dependencies or connecting to SQL Server:

```bash
python3 mage/run_etl.py --all --dry-run
```

## Phase 1

Prioritize source profiling, source-to-stage mapping, Mage ingestion into SQL Server staging, schema/data checks, run logging, and a repeatable full/incremental demonstration. See `docs/phase1_checklist.md`. The dimensional model is the target design; dbt warehouse models and Power BI are downstream work.
