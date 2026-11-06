-- ============================================================================
-- Script: 03_apply_columnstore_indexes.sql
-- Description: Ap dung Clustered Columnstore Index (CCI) cho FactRaceResult
--              va toi uu hoa chi muc B-Tree cho cac bang Dimensions
-- Tac gia: Dung (Database Administrator & Physical DW Optimization Specialist)
-- Phase: 2 - Data Transformation & Data Warehouse
-- ============================================================================

USE F1_BI;
GO

PRINT N'====================================================================';
PRINT N'1. KIEM TRA VA KHOI TAO BANG FactRaceResult (NEU CHUA CO)';
PRINT N'====================================================================';

IF OBJECT_ID(N'dw.FactRaceResult', N'U') IS NULL
BEGIN
    CREATE TABLE dw.FactRaceResult (
        RaceResultSK        INT IDENTITY(1, 1) NOT NULL,
        SourceResultId      INT NOT NULL,
        DateSK              INT NOT NULL,
        RaceSK              INT NOT NULL,
        CircuitSK           INT NOT NULL,
        DriverSK            INT NOT NULL,
        ConstructorSK       INT NOT NULL,
        StatusSK            INT NOT NULL,
        Points              DECIMAL(6, 2) NOT NULL,
        Laps                INT NOT NULL,
        GridPosition        INT NOT NULL,
        FinishPosition      INT NULL,
        PositionOrder       INT NOT NULL,
        PositionText        NVARCHAR(10) NOT NULL,
        Milliseconds        INT NULL,
        FastestLap          INT NULL,
        FastestLapTime      NVARCHAR(50) NULL,
        FastestLapSpeed     DECIMAL(7, 3) NULL,
        PlacesGained        INT NULL,
        IsWin               TINYINT NOT NULL,
        IsPodium            TINYINT NOT NULL,
        IsClassified        TINYINT NOT NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_FactRaceResult_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_FactRaceResult PRIMARY KEY NONCLUSTERED (RaceResultSK),
        CONSTRAINT UQ_FactRaceResult_SourceResultId UNIQUE NONCLUSTERED (SourceResultId)
    );
    PRINT N'[SUCCESS] Da tao bang dw.FactRaceResult voi Primary Key NONCLUSTERED.';
END
GO

PRINT N'====================================================================';
PRINT N'2. AP DUNG CLUSTERED COLUMNSTORE INDEX (CCI) CHO FactRaceResult';
PRINT N'====================================================================';

-- Neu bang dang co Clustered Index (B-Tree), ta can loai bo hoac chuyen thanh NONCLUSTERED truoc khi tao CCI
DECLARE @ExistingClusteredIndex NVARCHAR(128);
SELECT @ExistingClusteredIndex = name
FROM sys.indexes
WHERE object_id = OBJECT_ID(N'dw.FactRaceResult') 
  AND type_desc = 'CLUSTERED' 
  AND type <> 5; -- 5 la Clustered Columnstore

IF @ExistingClusteredIndex IS NOT NULL
BEGIN
    DECLARE @DropSql NVARCHAR(500);
    -- Neu la Primary Key Clustered, xoa Constraint
    IF EXISTS (
        SELECT 1 FROM sys.key_constraints 
        WHERE parent_object_id = OBJECT_ID(N'dw.FactRaceResult') 
          AND name = @ExistingClusteredIndex
    )
    BEGIN
        SET @DropSql = N'ALTER TABLE dw.FactRaceResult DROP CONSTRAINT [' + @ExistingClusteredIndex + N']';
        EXEC sp_executesql @DropSql;
        PRINT N'[INFO] Da drop Clustered PK Constraint cu [' + @ExistingClusteredIndex + N'].';
        
        -- Tao lai PK duoi dang NONCLUSTERED
        ALTER TABLE dw.FactRaceResult 
        ADD CONSTRAINT PK_FactRaceResult PRIMARY KEY NONCLUSTERED (RaceResultSK);
        PRINT N'[SUCCESS] Da tao lai PK_FactRaceResult duoi dang NONCLUSTERED.';
    END
    ELSE
    BEGIN
        SET @DropSql = N'DROP INDEX [' + @ExistingClusteredIndex + N'] ON dw.FactRaceResult';
        EXEC sp_executesql @DropSql;
        PRINT N'[INFO] Da drop Clustered Index cu [' + @ExistingClusteredIndex + N'].';
    END
END
GO

-- Tao Clustered Columnstore Index neu chua ton tai
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID(N'dw.FactRaceResult') 
      AND (name = N'CCI_FactRaceResult' OR type_desc = 'CLUSTERED COLUMNSTORE')
)
BEGIN
    CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactRaceResult 
    ON dw.FactRaceResult;
    PRINT N'[SUCCESS] Da khoi tao thanh cong Clustered Columnstore Index (CCI_FactRaceResult) cho dw.FactRaceResult.';
END
ELSE
BEGIN
    PRINT N'[INFO] Clustered Columnstore Index da ton tai tren dw.FactRaceResult.';
END
GO

PRINT N'====================================================================';
PRINT N'3. TOI UU HOA B-TREE INDEXES CHO CAC BANG DIMENSIONS';
PRINT N'====================================================================';

-- 3.1. Index cho dw.DimDate
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimDate_FullDate' AND object_id = OBJECT_ID(N'dw.DimDate'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimDate_FullDate ON dw.DimDate(FullDate);
    PRINT N'[SUCCESS] Da tao index IX_DimDate_FullDate.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimDate_CalendarYear' AND object_id = OBJECT_ID(N'dw.DimDate'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimDate_CalendarYear ON dw.DimDate(CalendarYear, QuarterNumber, MonthNumber);
    PRINT N'[SUCCESS] Da tao index IX_DimDate_CalendarYear.';
END
GO

-- 3.2. Index cho dw.DimRace
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimRace_SourceRaceId' AND object_id = OBJECT_ID(N'dw.DimRace'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimRace_SourceRaceId ON dw.DimRace(SourceRaceId);
    PRINT N'[SUCCESS] Da tao index IX_DimRace_SourceRaceId.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimRace_SeasonYear' AND object_id = OBJECT_ID(N'dw.DimRace'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimRace_SeasonYear ON dw.DimRace(SeasonYear, RoundNumber);
    PRINT N'[SUCCESS] Da tao index IX_DimRace_SeasonYear.';
END
GO

-- 3.3. Index cho dw.DimCircuit
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimCircuit_SourceCircuitId' AND object_id = OBJECT_ID(N'dw.DimCircuit'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimCircuit_SourceCircuitId ON dw.DimCircuit(SourceCircuitId);
    PRINT N'[SUCCESS] Da tao index IX_DimCircuit_SourceCircuitId.';
END
GO

-- 3.4. Index cho dw.DimDriver
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimDriver_SourceDriverId' AND object_id = OBJECT_ID(N'dw.DimDriver'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimDriver_SourceDriverId ON dw.DimDriver(SourceDriverId);
    PRINT N'[SUCCESS] Da tao index IX_DimDriver_SourceDriverId.';
END
GO

-- 3.5. Index cho dw.DimConstructor
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimConstructor_SourceConstructorId' AND object_id = OBJECT_ID(N'dw.DimConstructor'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimConstructor_SourceConstructorId ON dw.DimConstructor(SourceConstructorId);
    PRINT N'[SUCCESS] Da tao index IX_DimConstructor_SourceConstructorId.';
END
GO

-- 3.6. Index cho dw.DimStatus
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimStatus_SourceStatusId' AND object_id = OBJECT_ID(N'dw.DimStatus'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimStatus_SourceStatusId ON dw.DimStatus(SourceStatusId);
    PRINT N'[SUCCESS] Da tao index IX_DimStatus_SourceStatusId.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DimStatus_OutcomeGroup' AND object_id = OBJECT_ID(N'dw.DimStatus'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_DimStatus_OutcomeGroup ON dw.DimStatus(OutcomeGroup);
    PRINT N'[SUCCESS] Da tao index IX_DimStatus_OutcomeGroup.';
END
GO

PRINT N'====================================================================';
PRINT N'4. DUNG LUONG VA MUC DO NEN CUA CLUSTERED COLUMNSTORE INDEX';
PRINT N'====================================================================';

SELECT 
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    COUNT(rg.row_group_id) AS TotalRowGroups,
    SUM(rg.total_rows) AS TotalRows,
    CAST(SUM(rg.size_in_bytes) / 1024.0 / 1024.0 AS DECIMAL(10, 2)) AS SizeInMB,
    SUM(CASE WHEN rg.state_description = 'COMPRESSED' THEN 1 ELSE 0 END) AS CompressedRowGroups
FROM sys.tables t
JOIN sys.indexes i ON t.object_id = i.object_id
LEFT JOIN sys.dm_db_column_store_row_group_physical_stats rg ON i.object_id = rg.object_id AND i.index_id = rg.index_id
WHERE t.schema_id = SCHEMA_ID('dw') AND t.name = 'FactRaceResult'
GROUP BY t.name, i.name, i.type_desc;
GO

PRINT N'====================================================================';
PRINT N'[HOAN TAT] Script 03_apply_columnstore_indexes.sql da thuc thi thanh cong!';
PRINT N'====================================================================';
GO
