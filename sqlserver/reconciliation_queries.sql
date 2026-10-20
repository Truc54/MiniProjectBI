-- ============================================================================
-- Script: reconciliation_queries.sql
-- Description: Bo truy van SQL doi soat chat luong du lieu Staging (Phase 1)
-- Phuc vu nghiem thu, bao cao Seminar 1 va Evidence cho Truc
-- ============================================================================

USE F1_BI;
GO

PRINT N'====================================================================';
PRINT N'1. DOI SOAT SO DONG (ROW COUNTS) TUNG BANG STAGING VS CSV GOC';
PRINT N'====================================================================';

SELECT 'stg.circuits' AS TableName, COUNT(*) AS StgRowCount, 78 AS ExpectedBaseline,
       CASE WHEN COUNT(*) = 78 THEN N'MATCH' ELSE N'DIFF' END AS [Status] FROM stg.circuits
UNION ALL
SELECT 'stg.constructors', COUNT(*), 214,
       CASE WHEN COUNT(*) = 214 THEN N'MATCH' ELSE N'DIFF' END FROM stg.constructors
UNION ALL
SELECT 'stg.drivers', COUNT(*), 879,
       CASE WHEN COUNT(*) = 879 THEN N'MATCH' ELSE N'DIFF' END FROM stg.drivers
UNION ALL
SELECT 'stg.status', COUNT(*), 141,
       CASE WHEN COUNT(*) = 141 THEN N'MATCH' ELSE N'DIFF' END FROM stg.status
UNION ALL
SELECT 'stg.seasons', COUNT(*), 77,
       CASE WHEN COUNT(*) = 77 THEN N'MATCH' ELSE N'DIFF' END FROM stg.seasons
UNION ALL
SELECT 'stg.races', COUNT(*), 1164,
       CASE WHEN COUNT(*) = 1164 THEN N'MATCH' ELSE N'DIFF' END FROM stg.races
UNION ALL
SELECT 'stg.results', COUNT(*), 27568,
       CASE WHEN COUNT(*) = 27568 THEN N'MATCH' ELSE N'DIFF' END FROM stg.results;
GO

PRINT N'====================================================================';
PRINT N'2. KIEM TRA KHOA CHINH: NULL HOAC TRUNG LAP (DUPLICATES)';
PRINT N'Ket qua mong muon: Moi bang co NullCount = 0 va DuplicateKeyCount = 0';
PRINT N'====================================================================';

-- circuits
SELECT 'stg.circuits' AS TableName,
       SUM(CASE WHEN circuitId IS NULL THEN 1 ELSE 0 END) AS NullCount,
       COUNT(*) - COUNT(DISTINCT circuitId) AS DuplicateKeyCount
FROM stg.circuits
UNION ALL
-- constructors
SELECT 'stg.constructors',
       SUM(CASE WHEN constructorId IS NULL THEN 1 ELSE 0 END),
       COUNT(*) - COUNT(DISTINCT constructorId)
FROM stg.constructors
UNION ALL
-- drivers
SELECT 'stg.drivers',
       SUM(CASE WHEN driverId IS NULL THEN 1 ELSE 0 END),
       COUNT(*) - COUNT(DISTINCT driverId)
FROM stg.drivers
UNION ALL
-- status
SELECT 'stg.status',
       SUM(CASE WHEN statusId IS NULL THEN 1 ELSE 0 END),
       COUNT(*) - COUNT(DISTINCT statusId)
FROM stg.status
UNION ALL
-- seasons
SELECT 'stg.seasons',
       SUM(CASE WHEN [year] IS NULL THEN 1 ELSE 0 END),
       COUNT(*) - COUNT(DISTINCT [year])
FROM stg.seasons
UNION ALL
-- races
SELECT 'stg.races',
       SUM(CASE WHEN raceId IS NULL THEN 1 ELSE 0 END),
       COUNT(*) - COUNT(DISTINCT raceId)
FROM stg.races
UNION ALL
-- results
SELECT 'stg.results',
       SUM(CASE WHEN resultId IS NULL THEN 1 ELSE 0 END),
       COUNT(*) - COUNT(DISTINCT resultId)
FROM stg.results;
GO

PRINT N'====================================================================';
PRINT N'3. KIEM TRA KHOA NGOAI MOI COI (ORPHAN FOREIGN KEY CHECKS)';
PRINT N'Ket qua mong muon: Tat ca cac truy van tra ve 0 dong orphan';
PRINT N'====================================================================';

-- Orphan check: races.circuitId -> circuits.circuitId
SELECT 'races -> circuits' AS Relationship, COUNT(*) AS OrphanCount
FROM stg.races r
LEFT JOIN stg.circuits c ON r.circuitId = c.circuitId
WHERE c.circuitId IS NULL
UNION ALL
-- Orphan check: races.year -> seasons.year
SELECT 'races -> seasons', COUNT(*)
FROM stg.races r
LEFT JOIN stg.seasons s ON r.[year] = s.[year]
WHERE s.[year] IS NULL
UNION ALL
-- Orphan check: results.raceId -> races.raceId
SELECT 'results -> races', COUNT(*)
FROM stg.results res
LEFT JOIN stg.races r ON res.raceId = r.raceId
WHERE r.raceId IS NULL
UNION ALL
-- Orphan check: results.driverId -> drivers.driverId
SELECT 'results -> drivers', COUNT(*)
FROM stg.results res
LEFT JOIN stg.drivers d ON res.driverId = d.driverId
WHERE d.driverId IS NULL
UNION ALL
-- Orphan check: results.constructorId -> constructors.constructorId
SELECT 'results -> constructors', COUNT(*)
FROM stg.results res
LEFT JOIN stg.constructors c ON res.constructorId = c.constructorId
WHERE c.constructorId IS NULL
UNION ALL
-- Orphan check: results.statusId -> status.statusId
SELECT 'results -> status', COUNT(*)
FROM stg.results res
LEFT JOIN stg.status st ON res.statusId = st.statusId
WHERE st.statusId IS NULL;
GO

PRINT N'====================================================================';
PRINT N'4. XAC MINH XU LY NULL HOP LE (KHONG EP 0 HOAC MAT GIA TRI THIEU)';
PRINT N'====================================================================';

SELECT 'results.position (DNF/unclassified)' AS FieldCheck,
       COUNT(*) AS TotalRows,
       SUM(CASE WHEN position IS NULL THEN 1 ELSE 0 END) AS NullCount,
       SUM(CASE WHEN position = 0 THEN 1 ELSE 0 END) AS ZeroCount
FROM stg.results
UNION ALL
SELECT 'drivers.number (historical)',
       COUNT(*),
       SUM(CASE WHEN number IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN number = 0 THEN 1 ELSE 0 END)
FROM stg.drivers
UNION ALL
SELECT 'races.time (early races)',
       COUNT(*),
       SUM(CASE WHEN [time] IS NULL THEN 1 ELSE 0 END),
       0
FROM stg.races;
GO

PRINT N'====================================================================';
PRINT N'5. KIEM TRA LOG VA TRANG THAI BATCH (CTL TABLES)';
PRINT N'====================================================================';

-- Danh sach cac run gan nhat
SELECT TOP 10
    run_id, pipeline_name, source_file, target_table, load_mode,
    batch_key, run_status, rows_read, rows_written, rows_rejected,
    started_at_utc, completed_at_utc, error_message
FROM ctl.etl_run_log
ORDER BY started_at_utc DESC;

-- Danh sach batch da nap va trang thai
SELECT source_name, source_table, batch_key, source_row_count, batch_status, loaded_at_utc
FROM ctl.etl_batch_state
ORDER BY loaded_at_utc DESC;
GO
