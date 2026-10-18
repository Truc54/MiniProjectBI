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
3. Run `sqlserver/ddl/01_create_schemas.sql` and `sqlserver/ddl/02_create_control_tables.sql` against that database.
4. Make the Microsoft ODBC Driver 18 for SQL Server available to the Mage runtime. The Dockerfile installs unixODBC build dependencies but does not install Microsoft's driver.
5. Configure SQL Server network access, then start Mage with Docker Compose.

The Compose service assumes the SQL Server instance is outside Compose and reachable as `host.docker.internal:1433` from Docker Desktop. Adjust the Mage environment if your instance uses another host or port. If dbt runs directly on Windows, `MSSQL_HOST` in `.env` should resolve to SQL Server from Windows (often `localhost`).

The Mage blocks are starter templates. Complete and review the exporter load strategy before loading data: a repeatable full load and an idempotent incremental load must not create duplicate source rows. The table-level runtime variables are `file_name`, `table_name`, `target_table`, and `load_mode`.

## Phase 1

Prioritize source profiling, source-to-stage mapping, Mage ingestion into SQL Server staging, schema/data checks, run logging, and a repeatable full/incremental demonstration. See `docs/phase1_checklist.md`. The dimensional model is the target design; dbt warehouse models and Power BI are downstream work.
