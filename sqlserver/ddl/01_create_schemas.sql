-- Run this script in the project database, not in master.
IF DB_ID(N'F1_BI') IS NOT NULL
BEGIN
    USE F1_BI;
END
GO

IF SCHEMA_ID(N'stg') IS NULL EXEC(N'CREATE SCHEMA stg');
IF SCHEMA_ID(N'ctl') IS NULL EXEC(N'CREATE SCHEMA ctl');
IF SCHEMA_ID(N'dw') IS NULL EXEC(N'CREATE SCHEMA dw');
GO
