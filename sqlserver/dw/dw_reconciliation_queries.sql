-- ============================================================================
-- Script: dw_reconciliation_queries.sql
-- Description: Bo truy van SQL doi soat chat luong toan dien giua Staging (stg) 
--              va Data Warehouse (dw) cho Phase 2 (dbt Transformation & DW)
-- Tac gia: Dung (Database Administrator & Physical DW Optimization Specialist)
-- Phuc vu: Nghiem thu Phase 2, bao cao Seminar va Evidence cho Phuc/Truc
-- ============================================================================

USE F1_BI;
GO

PRINT N'====================================================================';
PRINT N'1. DOI SOAT SO LUONG DONG (ROW COUNT RECONCILIATION: STG VS DW)';
PRINT N'Expected:';
PRINT N'  - FactRaceResult khop 100% stg.results (27.568 dong)';
PRINT N'  - Moi Dimension khop so dong nguon + 1 ban ghi Unknown (SK = -1)';
PRINT N'====================================================================';

-- 1.1. Fact vs Staging Results
SELECT 
    'Fact vs Staging' AS Comparison,
    (SELECT COUNT(*) FROM stg.results) AS Staging_Results_Rows,
    (SELECT COUNT(*) FROM dw.FactRaceResult) AS DW_Fact_Rows,
    (SELECT COUNT(*) FROM dw.FactRaceResult) - (SELECT COUNT(*) FROM stg.results) AS Difference,
    CASE 
        WHEN (SELECT COUNT(*) FROM dw.FactRaceResult) = (SELECT COUNT(*) FROM stg.results) THEN N'MATCH (100%)'
        ELSE N'DISCREPANCY'
    END AS Status;

-- 1.2. Dimensions vs Staging Sources (+1 Unknown record)
SELECT 
    'dw.DimCircuit' AS Dimension_Table,
    (SELECT COUNT(*) FROM dw.DimCircuit) AS DW_Count,
    (SELECT COUNT(*) FROM stg.circuits) + 1 AS Expected_With_Unknown,
    CASE WHEN (SELECT COUNT(*) FROM dw.DimCircuit) = (SELECT COUNT(*) FROM stg.circuits) + 1 THEN N'MATCH' ELSE N'DIFF' END AS Status
UNION ALL
SELECT 
    'dw.DimConstructor',
    (SELECT COUNT(*) FROM dw.DimConstructor),
    (SELECT COUNT(*) FROM stg.constructors) + 1,
    CASE WHEN (SELECT COUNT(*) FROM dw.DimConstructor) = (SELECT COUNT(*) FROM stg.constructors) + 1 THEN N'MATCH' ELSE N'DIFF' END
UNION ALL
SELECT 
    'dw.DimDriver',
    (SELECT COUNT(*) FROM dw.DimDriver),
    (SELECT COUNT(*) FROM stg.drivers) + 1,
    CASE WHEN (SELECT COUNT(*) FROM dw.DimDriver) = (SELECT COUNT(*) FROM stg.drivers) + 1 THEN N'MATCH' ELSE N'DIFF' END
UNION ALL
SELECT 
    'dw.DimStatus',
    (SELECT COUNT(*) FROM dw.DimStatus),
    (SELECT COUNT(*) FROM stg.status) + 1,
    CASE WHEN (SELECT COUNT(*) FROM dw.DimStatus) = (SELECT COUNT(*) FROM stg.status) + 1 THEN N'MATCH' ELSE N'DIFF' END
UNION ALL
SELECT 
    'dw.DimRace',
    (SELECT COUNT(*) FROM dw.DimRace),
    (SELECT COUNT(*) FROM stg.races) + 1,
    CASE WHEN (SELECT COUNT(*) FROM dw.DimRace) = (SELECT COUNT(*) FROM stg.races) + 1 THEN N'MATCH' ELSE N'DIFF' END;
GO

PRINT N'====================================================================';
PRINT N'2. KIEM TRA CHECKSUM DO DO TONG HOP (MEASURE CHECKSUM VERIFICATION)';
PRINT N'Expected: Do lech SUM(points) phai bang dung 0.00';
PRINT N'====================================================================';

SELECT 
    'Points Checksum' AS Measure_Name,
    CAST(SUM(s.points) AS DECIMAL(12, 2)) AS Staging_Total,
    CAST(SUM(f.points) AS DECIMAL(12, 2)) AS DW_Total,
    CAST(SUM(f.points) - SUM(s.points) AS DECIMAL(12, 2)) AS Difference,
    CASE 
        WHEN CAST(SUM(f.points) - SUM(s.points) AS DECIMAL(12, 2)) = 0.00 THEN N'EXACT MATCH'
        ELSE N'MISMATCH'
    END AS Integrity_Status
FROM stg.results s
FULL OUTER JOIN dw.FactRaceResult f ON s.resultId = f.source_result_id;
GO

PRINT N'====================================================================';
PRINT N'3. KIEM TRA TINH DUY NHAT VA KHONG NULL CUA KHOA (PK & NK UNIQUENESS)';
PRINT N'Expected: Tat ca cac cot Null_Count = 0 va Duplicate_Count = 0';
PRINT N'====================================================================';

SELECT 
    'FactRaceResult' AS Table_Name,
    'source_result_id' AS Key_Column,
    SUM(CASE WHEN source_result_id IS NULL THEN 1 ELSE 0 END) AS Null_Count,
    COUNT(*) - COUNT(DISTINCT source_result_id) AS Duplicate_Count
FROM dw.FactRaceResult
UNION ALL
SELECT 
    'DimDate', 'date_sk',
    SUM(CASE WHEN date_sk IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT date_sk)
FROM dw.DimDate
UNION ALL
SELECT 
    'DimRace', 'race_sk',
    SUM(CASE WHEN race_sk IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT race_sk)
FROM dw.DimRace
UNION ALL
SELECT 
    'DimCircuit', 'circuit_sk',
    SUM(CASE WHEN circuit_sk IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT circuit_sk)
FROM dw.DimCircuit
UNION ALL
SELECT 
    'DimDriver', 'driver_sk',
    SUM(CASE WHEN driver_sk IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT driver_sk)
FROM dw.DimDriver
UNION ALL
SELECT 
    'DimConstructor', 'constructor_sk',
    SUM(CASE WHEN constructor_sk IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT constructor_sk)
FROM dw.DimConstructor
UNION ALL
SELECT 
    'DimStatus', 'status_sk',
    SUM(CASE WHEN status_sk IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT status_sk)
FROM dw.DimStatus;
GO

PRINT N'====================================================================';
PRINT N'4. KIEM TRA TOAN VEN KHOA NGOAI CUA FACT (ORPHAN FOREIGN KEY CHECK)';
PRINT N'Expected: Tat ca cac quan he deu co Orphan_Count = 0';
PRINT N'====================================================================';

SELECT 
    'FactRaceResult -> DimDate' AS Relationship,
    COUNT(*) AS Orphan_Count
FROM dw.FactRaceResult f
WHERE NOT EXISTS (SELECT 1 FROM dw.DimDate d WHERE d.date_sk = f.date_sk)
UNION ALL
SELECT 
    'FactRaceResult -> DimRace',
    COUNT(*)
FROM dw.FactRaceResult f
WHERE NOT EXISTS (SELECT 1 FROM dw.DimRace d WHERE d.race_sk = f.race_sk)
UNION ALL
SELECT 
    'FactRaceResult -> DimCircuit',
    COUNT(*)
FROM dw.FactRaceResult f
WHERE NOT EXISTS (SELECT 1 FROM dw.DimCircuit d WHERE d.circuit_sk = f.circuit_sk)
UNION ALL
SELECT 
    'FactRaceResult -> DimDriver',
    COUNT(*)
FROM dw.FactRaceResult f
WHERE NOT EXISTS (SELECT 1 FROM dw.DimDriver d WHERE d.driver_sk = f.driver_sk)
UNION ALL
SELECT 
    'FactRaceResult -> DimConstructor',
    COUNT(*)
FROM dw.FactRaceResult f
WHERE NOT EXISTS (SELECT 1 FROM dw.DimConstructor d WHERE d.constructor_sk = f.constructor_sk)
UNION ALL
SELECT 
    'FactRaceResult -> DimStatus',
    COUNT(*)
FROM dw.FactRaceResult f
WHERE NOT EXISTS (SELECT 1 FROM dw.DimStatus d WHERE d.status_sk = f.status_sk);
GO

PRINT N'====================================================================';
PRINT N'5. PHAN PHOI BAN GHI UNKNOWN (UNKNOWN MEMBER DISTRIBUTION: SK = -1)';
PRINT N'Expected: Ty le Unknown phai < 0.1% tren moi chieu';
PRINT N'====================================================================';

SELECT 
    'date_sk = -1' AS Dimension_FK,
    SUM(CASE WHEN date_sk = -1 THEN 1 ELSE 0 END) AS Unknown_Rows,
    COUNT(*) AS Total_Fact_Rows,
    CAST(100.0 * SUM(CASE WHEN date_sk = -1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2)) AS Unknown_Pct
FROM dw.FactRaceResult
UNION ALL
SELECT 
    'race_sk = -1',
    SUM(CASE WHEN race_sk = -1 THEN 1 ELSE 0 END),
    COUNT(*),
    CAST(100.0 * SUM(CASE WHEN race_sk = -1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2))
FROM dw.FactRaceResult
UNION ALL
SELECT 
    'circuit_sk = -1',
    SUM(CASE WHEN circuit_sk = -1 THEN 1 ELSE 0 END),
    COUNT(*),
    CAST(100.0 * SUM(CASE WHEN circuit_sk = -1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2))
FROM dw.FactRaceResult
UNION ALL
SELECT 
    'driver_sk = -1',
    SUM(CASE WHEN driver_sk = -1 THEN 1 ELSE 0 END),
    COUNT(*),
    CAST(100.0 * SUM(CASE WHEN driver_sk = -1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2))
FROM dw.FactRaceResult
UNION ALL
SELECT 
    'constructor_sk = -1',
    SUM(CASE WHEN constructor_sk = -1 THEN 1 ELSE 0 END),
    COUNT(*),
    CAST(100.0 * SUM(CASE WHEN constructor_sk = -1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2))
FROM dw.FactRaceResult
UNION ALL
SELECT 
    'status_sk = -1',
    SUM(CASE WHEN status_sk = -1 THEN 1 ELSE 0 END),
    COUNT(*),
    CAST(100.0 * SUM(CASE WHEN status_sk = -1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2))
FROM dw.FactRaceResult;
GO

PRINT N'====================================================================';
PRINT N'6. PHAN PHOI CAC NHOM TRANG THAI NGHIỆP VỤ (OUTCOME GROUP AUDIT)';
PRINT N'Expected: Day du 5 nhom: CLASSIFIED, RETIREMENT_DNF, DNS, DSQ, OTHER';
PRINT N'====================================================================';

SELECT 
    s.outcome_group,
    COUNT(DISTINCT s.source_status_id) AS Distinct_Status_Codes,
    COUNT(f.source_result_id) AS Total_Fact_Results,
    CAST(100.0 * COUNT(f.source_result_id) / NULLIF((SELECT COUNT(*) FROM dw.FactRaceResult), 0) AS DECIMAL(5, 2)) AS Pct_Of_All_Results
FROM dw.DimStatus s
LEFT JOIN dw.FactRaceResult f ON s.status_sk = f.status_sk
GROUP BY s.outcome_group
ORDER BY Total_Fact_Results DESC;
GO

PRINT N'====================================================================';
PRINT N'7. DUNG LUONG & HIỆU QUẢ NÉN CỦA CLUSTERED COLUMNSTORE INDEX';
PRINT N'====================================================================';

SELECT 
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    COUNT(rg.row_group_id) AS RowGroupsCount,
    SUM(rg.total_rows) AS TotalRowsIndexed,
    CAST(SUM(rg.size_in_bytes) / 1024.0 / 1024.0 AS DECIMAL(10, 2)) AS CompressedSizeMB,
    SUM(CASE WHEN rg.state_desc = 'COMPRESSED' THEN 1 ELSE 0 END) AS CompressedGroups
FROM sys.tables t
JOIN sys.indexes i ON t.object_id = i.object_id
LEFT JOIN sys.dm_db_column_store_row_group_physical_stats rg 
    ON i.object_id = rg.object_id AND i.index_id = rg.index_id
WHERE t.schema_id = SCHEMA_ID('dw') AND t.name = 'FactRaceResult'
GROUP BY t.name, i.name, i.type_desc;
GO

PRINT N'====================================================================';
PRINT N'[HOAN TAT] Bo truy van doi soat dw_reconciliation_queries.sql hoan thanh!';
PRINT N'====================================================================';
GO

