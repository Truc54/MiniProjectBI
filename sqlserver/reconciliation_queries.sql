-- ============================================================================
-- Script: reconciliation_queries.sql
-- Description: Bo truy van SQL doi soat chat luong du lieu Staging (Phase 1)
-- Phuc vu nghiem thu, bao cao Seminar 1 va Evidence cho Truc
-- Phien ban: 2.0 (Dong bo hoan toan voi Section 7 cua Source-to-Stage Mapping Contract)
-- ============================================================================

USE F1_BI;
GO

PRINT N'====================================================================';
PRINT N'7.1 DOI SOAT SO DONG (ROW COUNTS) TUNG BANG STAGING VS BASELINE';
PRINT N'Expected: 78, 214, 879, 141, 77, 1164, 27568';
PRINT N'====================================================================';

SELECT 'stg.circuits'      AS tbl, COUNT(*) AS rows_count, 78 AS expected,
       CASE WHEN COUNT(*) = 78 THEN N'MATCH' ELSE N'DIFF' END AS [status] FROM stg.circuits      UNION ALL
SELECT 'stg.constructors'  AS tbl, COUNT(*) AS rows_count, 214,
       CASE WHEN COUNT(*) = 214 THEN N'MATCH' ELSE N'DIFF' END FROM stg.constructors  UNION ALL
SELECT 'stg.drivers'       AS tbl, COUNT(*) AS rows_count, 879,
       CASE WHEN COUNT(*) = 879 THEN N'MATCH' ELSE N'DIFF' END FROM stg.drivers       UNION ALL
SELECT 'stg.status'        AS tbl, COUNT(*) AS rows_count, 141,
       CASE WHEN COUNT(*) = 141 THEN N'MATCH' ELSE N'DIFF' END FROM stg.status        UNION ALL
SELECT 'stg.seasons'       AS tbl, COUNT(*) AS rows_count, 77,
       CASE WHEN COUNT(*) = 77 THEN N'MATCH' ELSE N'DIFF' END FROM stg.seasons       UNION ALL
SELECT 'stg.races'         AS tbl, COUNT(*) AS rows_count, 1164,
       CASE WHEN COUNT(*) = 1164 THEN N'MATCH' ELSE N'DIFF' END FROM stg.races         UNION ALL
SELECT 'stg.results'       AS tbl, COUNT(*) AS rows_count, 27568,
       CASE WHEN COUNT(*) = 27568 THEN N'MATCH' ELSE N'DIFF' END FROM stg.results;
GO

PRINT N'====================================================================';
PRINT N'7.2 KIEM TRA KHOA CHINH: NULL HOAC TRUNG LAP (PK NULL & DUP CHECK)';
PRINT N'Expected: Tat ca null_pk = 0, dup_pk = 0';
PRINT N'====================================================================';

SELECT 'circuits'     AS tbl, SUM(CASE WHEN circuitId     IS NULL THEN 1 ELSE 0 END) AS null_pk, COUNT(*) - COUNT(DISTINCT circuitId)     AS dup_pk FROM stg.circuits     UNION ALL
SELECT 'constructors' AS tbl, SUM(CASE WHEN constructorId IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT constructorId) FROM stg.constructors UNION ALL
SELECT 'drivers'      AS tbl, SUM(CASE WHEN driverId      IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT driverId)      FROM stg.drivers      UNION ALL
SELECT 'status'       AS tbl, SUM(CASE WHEN statusId      IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT statusId)      FROM stg.status       UNION ALL
SELECT 'seasons'      AS tbl, SUM(CASE WHEN [year]        IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT [year])        FROM stg.seasons      UNION ALL
SELECT 'races'        AS tbl, SUM(CASE WHEN raceId        IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT raceId)        FROM stg.races        UNION ALL
SELECT 'results'      AS tbl, SUM(CASE WHEN resultId      IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT resultId)      FROM stg.results;
GO

PRINT N'====================================================================';
PRINT N'7.3 KIEM TRA KHOA NGOAI MOI COI (FK ORPHAN CHECKS)';
PRINT N'Expected: Tat ca orphans = 0';
PRINT N'====================================================================';

SELECT 'results->races'        AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.races        p WHERE p.raceId        = r.raceId)        UNION ALL
SELECT 'results->drivers'      AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.drivers      p WHERE p.driverId      = r.driverId)      UNION ALL
SELECT 'results->constructors' AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.constructors p WHERE p.constructorId = r.constructorId) UNION ALL
SELECT 'results->status'       AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.status       p WHERE p.statusId      = r.statusId)       UNION ALL
SELECT 'races->circuits'       AS fk, COUNT(*) AS orphans FROM stg.races          r WHERE NOT EXISTS (SELECT 1 FROM stg.circuits     p WHERE p.circuitId     = r.circuitId)      UNION ALL
SELECT 'races->seasons'        AS fk, COUNT(*) AS orphans FROM stg.races          r WHERE NOT EXISTS (SELECT 1 FROM stg.seasons      p WHERE p.[year]        = r.[year]);
GO

PRINT N'====================================================================';
PRINT N'7.4 RESULTS.POSITION NULL RATE (SO VOI SOURCE: ~40.2%)';
PRINT N'Expected: ~11,074 NULL (~40.2%) - DNF / unclassified finishes';
PRINT N'====================================================================';

SELECT
    COUNT(*)                                              AS total_rows,
    SUM(CASE WHEN position IS NULL THEN 1 ELSE 0 END)    AS position_null,
    CAST(100.0 * SUM(CASE WHEN position IS NULL THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,1)) AS pct_null
FROM stg.results;
GO

PRINT N'====================================================================';
PRINT N'7.5 RESULTS.FASTESTLAPSPEED NULL RATE (SO VOI SOURCE: ~70.1%)';
PRINT N'Expected: ~19,316 NULL (~70.1%) - Source limitation';
PRINT N'====================================================================';

SELECT
    COUNT(*)                                              AS total_rows,
    SUM(CASE WHEN fastestLapSpeed IS NULL THEN 1 ELSE 0 END) AS fls_null,
    CAST(100.0 * SUM(CASE WHEN fastestLapSpeed IS NULL THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,1)) AS pct_null
FROM stg.results;
GO

PRINT N'====================================================================';
PRINT N'7.6 KIEM TRA \N KHONG CON TON TAI DANG STRING TRONG STAGE';
PRINT N'Expected: 0 rows';
PRINT N'====================================================================';

SELECT 'results.positionText' AS check_col, COUNT(*) AS invalid_sentinel_count
FROM stg.results WHERE positionText = N'\N'
UNION ALL
SELECT 'drivers.code', COUNT(*)
FROM stg.drivers WHERE code = N'\N';
GO

PRINT N'====================================================================';
PRINT N'7.7 KIEM TRA LOG BATCH VA RUN (CTL TABLES)';
PRINT N'====================================================================';

-- 1. Trang thai tung batch (ctl.etl_batch_state)
SELECT source_name, source_table, batch_key, batch_status, source_row_count, loaded_at_utc
FROM ctl.etl_batch_state
ORDER BY loaded_at_utc DESC;

-- 2. Lich su cac run gan nhat (ctl.etl_run_log)
SELECT TOP 10
    run_id, pipeline_name, source_file, target_table, load_mode,
    batch_key, run_status, rows_read, rows_written, rows_rejected,
    started_at_utc, completed_at_utc, error_message
FROM ctl.etl_run_log
ORDER BY started_at_utc DESC;
GO
