# Staging tables

Create one source-aligned table per selected CSV in schema `stg`. Keep source keys and columns traceable to the CSV. Convert the literal source sentinel `\N` to SQL NULL; do not replace missing values with zero.

## 7 Core Tables (Phase 1)
- `stg.circuits` (circuits.csv)
- `stg.constructors` (constructors.csv)
- `stg.drivers` (drivers.csv)
- `stg.status` (status.csv)
- `stg.seasons` (seasons.csv)
- `stg.races` (races.csv)
- `stg.results` (results.csv)

## DDL & Documentation
- **DDL Script:** [sqlserver/ddl/03_create_staging_tables.sql](file:///d:/MiniProjectBI/sqlserver/ddl/03_create_staging_tables.sql)
- **Detailed Schema Specification:** [docs/stage_schema.md](file:///d:/MiniProjectBI/docs/stage_schema.md)
- **Connection & Setup Guide:** [docs/sql_server_setup.md](file:///d:/MiniProjectBI/docs/sql_server_setup.md)

