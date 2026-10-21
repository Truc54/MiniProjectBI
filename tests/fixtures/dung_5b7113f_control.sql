-- Run after 01_create_schemas.sql in the project database.
IF DB_ID(N'F1_BI') IS NOT NULL
BEGIN
    USE F1_BI;
END
GO
IF OBJECT_ID(N'ctl.etl_run_log', N'U') IS NULL
BEGIN
    CREATE TABLE ctl.etl_run_log (
        run_id UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT DF_etl_run_log_run_id DEFAULT NEWID(),
        pipeline_name SYSNAME NOT NULL,
        source_file NVARCHAR(260) NULL,
        target_schema SYSNAME NULL,
        target_table SYSNAME NULL,
        load_mode VARCHAR(20) NULL,
        batch_key NVARCHAR(100) NULL,
        run_status VARCHAR(20) NOT NULL,
        started_at_utc DATETIME2(3) NOT NULL
            CONSTRAINT DF_etl_run_log_started DEFAULT SYSUTCDATETIME(),
        completed_at_utc DATETIME2(3) NULL,
        rows_read BIGINT NOT NULL CONSTRAINT DF_etl_run_log_read DEFAULT 0,
        rows_written BIGINT NOT NULL CONSTRAINT DF_etl_run_log_written DEFAULT 0,
        rows_rejected BIGINT NOT NULL CONSTRAINT DF_etl_run_log_rejected DEFAULT 0,
        error_message NVARCHAR(MAX) NULL,
        CONSTRAINT PK_etl_run_log PRIMARY KEY (run_id)
    );
END;
GO

IF OBJECT_ID(N'ctl.etl_batch_state', N'U') IS NULL
BEGIN
    CREATE TABLE ctl.etl_batch_state (
        source_name NVARCHAR(260) NOT NULL,
        source_table SYSNAME NOT NULL,
        batch_key NVARCHAR(100) NOT NULL,
        source_row_count BIGINT NULL,
        last_run_id UNIQUEIDENTIFIER NULL,
        loaded_at_utc DATETIME2(3) NULL,
        batch_status VARCHAR(20) NOT NULL,
        CONSTRAINT PK_etl_batch_state
            PRIMARY KEY (source_name, source_table, batch_key)
    );
END;
GO
