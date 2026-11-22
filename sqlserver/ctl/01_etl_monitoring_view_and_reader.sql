-- ============================================================================
-- Script: 01_etl_monitoring_view_and_reader.sql
-- Description:
--   1. Tao View ctl.vw_etl_run_monitoring tinh san cac chi so giam sat ETL.
--   2. Tao Database Role db_ai_reader va Login/User f1_ai_reader chi co quyen SELECT
--      tren schema dw va ctl (hoan toan ngan chan ghi/xoa va khong truy cap stg).
-- Tinh lu y: Idempotent (chay lai nhieu lan an toan).
-- ============================================================================

USE F1_BI;
GO

-- ----------------------------------------------------------------------------
-- PHAN 1: TAO HOAC CAP NHAT VIEW GIAM SAT ETL
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'ctl.vw_etl_run_monitoring', N'V') IS NOT NULL
BEGIN
    DROP VIEW ctl.vw_etl_run_monitoring;
END
GO

CREATE VIEW ctl.vw_etl_run_monitoring
AS
SELECT
    run_id,
    pipeline_name,
    source_file,
    target_schema,
    target_table,
    load_mode,
    batch_key,
    run_status,
    started_at_utc,
    completed_at_utc,
    rows_read,
    rows_written,
    rows_rejected,
    error_message,
    -- Cac cot tinh toan phuc vu Semantic Model & Power BI
    CAST(started_at_utc AS DATE) AS run_date_utc,
    CASE 
        WHEN completed_at_utc IS NOT NULL 
        THEN CAST(DATEDIFF(MILLISECOND, started_at_utc, completed_at_utc) / 1000.0 AS DECIMAL(12,3))
        ELSE NULL 
    END AS duration_sec,
    CASE WHEN run_status = 'success' THEN 1 ELSE 0 END AS is_success,
    CASE WHEN run_status = 'failed' THEN 1 ELSE 0 END AS is_failed,
    CASE 
        WHEN rows_read > 0 
        THEN CAST(rows_rejected * 100.0 / rows_read AS DECIMAL(6,2)) 
        ELSE 0.00 
    END AS reject_rate_pct
FROM ctl.etl_run_log;
GO

PRINT N'Da tao View ctl.vw_etl_run_monitoring thanh cong.';
GO

-- ----------------------------------------------------------------------------
-- PHAN 2: TAO ROLE db_ai_reader VA USER f1_ai_reader CHI DOC TREN dw VA ctl
-- ----------------------------------------------------------------------------

-- 2.1 Tao Database Role db_ai_reader neu chua co
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'db_ai_reader' AND type = 'R')
BEGIN
    CREATE ROLE db_ai_reader;
    PRINT N'Da tao Database Role db_ai_reader.';
END
ELSE
BEGIN
    PRINT N'Database Role db_ai_reader da ton tai.';
END
GO

-- 2.2 Cap quyen SELECT tren schema dw va ctl
GRANT SELECT ON SCHEMA::dw TO db_ai_reader;
GRANT SELECT ON SCHEMA::ctl TO db_ai_reader;

-- 2.3 Chan tuong minh quyen ghi/xoa tren dw, ctl va chan truy cap stg
DENY INSERT, UPDATE, DELETE, ALTER, EXECUTE ON SCHEMA::dw TO db_ai_reader;
DENY INSERT, UPDATE, DELETE, ALTER, EXECUTE ON SCHEMA::ctl TO db_ai_reader;
DENY SELECT, INSERT, UPDATE, DELETE, ALTER ON SCHEMA::stg TO db_ai_reader;
GO

-- 2.4 Tao Server Login f1_ai_reader (neu chua co)
USE master;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'f1_ai_reader')
BEGIN
    CREATE LOGIN f1_ai_reader 
    WITH PASSWORD = N'F1AiReader@2026_SecurePwd!', 
         CHECK_POLICY = ON;
    PRINT N'Da tao Server Login f1_ai_reader.';
END
ELSE
BEGIN
    PRINT N'Server Login f1_ai_reader da ton tai.';
END
GO

-- 2.5 Tao Database User f1_ai_reader trong F1_BI va gan vao role db_ai_reader
USE F1_BI;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'f1_ai_reader')
BEGIN
    CREATE USER f1_ai_reader FOR LOGIN f1_ai_reader;
    PRINT N'Da tao Database User f1_ai_reader.';
END
ELSE
BEGIN
    PRINT N'Database User f1_ai_reader da ton tai.';
END
GO

ALTER ROLE db_ai_reader ADD MEMBER f1_ai_reader;
PRINT N'Da gan User f1_ai_reader vao Role db_ai_reader.';
GO
