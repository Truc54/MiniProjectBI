-- ============================================================================
-- Script: 03_create_staging_tables.sql
-- Description: DDL Idempotent tao 7 bang Staging loi (stg) cho Formula 1 Dataset
-- Tac gia: Dung (SQL Server & Staging)
-- Phien ban: 1.0 (Phase 1 Contract - Chot voi Loc & Phuc)
-- Thu tu tao: circuits, constructors, drivers, status, seasons, races, results
-- ============================================================================

-- Chay trong database project (F1_BI), khong chay trong master.
IF DB_ID(N'F1_BI') IS NOT NULL
BEGIN
    USE F1_BI;
END
GO

-- ----------------------------------------------------------------------------
-- 1. stg.circuits (circuits.csv - 78 rows)
-- Grain: Mot dong moi circuit
-- Natural key: circuitId
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.circuits', N'U') IS NULL
BEGIN
    CREATE TABLE stg.circuits (
        circuitId           INT NOT NULL,
        circuitRef          NVARCHAR(100) NOT NULL,
        name                NVARCHAR(200) NOT NULL,
        location            NVARCHAR(100) NULL,
        country             NVARCHAR(100) NULL,
        lat                 DECIMAL(9, 6) NULL,
        lng                 DECIMAL(9, 6) NULL,
        alt                 INT NULL,
        url                 NVARCHAR(500) NULL,

        -- Metadata Lineage columns
        _source_file        NVARCHAR(260) NULL,
        _batch_key          NVARCHAR(100) NULL,
        _load_mode          VARCHAR(20) NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_circuits_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_stg_circuits PRIMARY KEY CLUSTERED (circuitId)
    );
    PRINT N'Da tao bang stg.circuits.';
END
GO

-- ----------------------------------------------------------------------------
-- 2. stg.constructors (constructors.csv - 214 rows)
-- Grain: Mot dong moi constructor (doi dua)
-- Natural key: constructorId
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.constructors', N'U') IS NULL
BEGIN
    CREATE TABLE stg.constructors (
        constructorId       INT NOT NULL,
        constructorRef      NVARCHAR(100) NOT NULL,
        name                NVARCHAR(200) NOT NULL,
        nationality         NVARCHAR(100) NULL,
        url                 NVARCHAR(500) NULL,

        -- Metadata Lineage columns
        _source_file        NVARCHAR(260) NULL,
        _batch_key          NVARCHAR(100) NULL,
        _load_mode          VARCHAR(20) NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_constructors_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_stg_constructors PRIMARY KEY CLUSTERED (constructorId)
    );
    PRINT N'Da tao bang stg.constructors.';
END
GO

-- ----------------------------------------------------------------------------
-- 3. stg.drivers (drivers.csv - 879 rows)
-- Grain: Mot dong moi driver (tay dua)
-- Natural key: driverId
-- Luu y: number, code, dob co gia tri \N trong nguon -> NULL hop le
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.drivers', N'U') IS NULL
BEGIN
    CREATE TABLE stg.drivers (
        driverId            INT NOT NULL,
        driverRef           NVARCHAR(100) NOT NULL,
        number              INT NULL,
        code                NVARCHAR(10) NULL,
        forename            NVARCHAR(100) NOT NULL,
        surname             NVARCHAR(100) NOT NULL,
        dob                 DATE NULL,
        nationality         NVARCHAR(100) NULL,
        url                 NVARCHAR(500) NULL,

        -- Metadata Lineage columns
        _source_file        NVARCHAR(260) NULL,
        _batch_key          NVARCHAR(100) NULL,
        _load_mode          VARCHAR(20) NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_drivers_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_stg_drivers PRIMARY KEY CLUSTERED (driverId)
    );
    PRINT N'Da tao bang stg.drivers.';
END
GO

-- ----------------------------------------------------------------------------
-- 4. stg.status (status.csv - 141 rows)
-- Grain: Mot dong moi finishing status code
-- Natural key: statusId
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.status', N'U') IS NULL
BEGIN
    CREATE TABLE stg.status (
        statusId            INT NOT NULL,
        status              NVARCHAR(100) NOT NULL,

        -- Metadata Lineage columns
        _source_file        NVARCHAR(260) NULL,
        _batch_key          NVARCHAR(100) NULL,
        _load_mode          VARCHAR(20) NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_status_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_stg_status PRIMARY KEY CLUSTERED (statusId)
    );
    PRINT N'Da tao bang stg.status.';
END
GO

-- ----------------------------------------------------------------------------
-- 5. stg.seasons (seasons.csv - 77 rows)
-- Grain: Mot dong moi championship season
-- Natural key: year
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.seasons', N'U') IS NULL
BEGIN
    CREATE TABLE stg.seasons (
        [year]              INT NOT NULL,
        url                 NVARCHAR(500) NULL,

        -- Metadata Lineage columns
        _source_file        NVARCHAR(260) NULL,
        _batch_key          NVARCHAR(100) NULL,
        _load_mode          VARCHAR(20) NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_seasons_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_stg_seasons PRIMARY KEY CLUSTERED ([year])
    );
    PRINT N'Da tao bang stg.seasons.';
END
GO

-- ----------------------------------------------------------------------------
-- 6. stg.races (races.csv - 1,164 rows)
-- Grain: Mot dong moi race event
-- Natural key: raceId
-- Tham chieu: circuitId -> stg.circuits, year -> stg.seasons
-- Luu y: cac cot session schedule (fp1-3, quali, sprint) va time co \N -> NULL
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.races', N'U') IS NULL
BEGIN
    CREATE TABLE stg.races (
        raceId              INT NOT NULL,
        [year]              INT NOT NULL,
        [round]             INT NOT NULL,
        circuitId           INT NOT NULL,
        name                NVARCHAR(200) NOT NULL,
        [date]              DATE NOT NULL,
        [time]              TIME(0) NULL,
        url                 NVARCHAR(500) NULL,
        fp1_date            DATE NULL,
        fp1_time            TIME(0) NULL,
        fp2_date            DATE NULL,
        fp2_time            TIME(0) NULL,
        fp3_date            DATE NULL,
        fp3_time            TIME(0) NULL,
        quali_date          DATE NULL,
        quali_time          TIME(0) NULL,
        sprint_date         DATE NULL,
        sprint_time         TIME(0) NULL,

        -- Metadata Lineage columns
        _source_file        NVARCHAR(260) NULL,
        _batch_key          NVARCHAR(100) NULL,
        _load_mode          VARCHAR(20) NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_races_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_stg_races PRIMARY KEY CLUSTERED (raceId)
    );

    CREATE NONCLUSTERED INDEX IX_stg_races_year ON stg.races ([year]);
    CREATE NONCLUSTERED INDEX IX_stg_races_circuitId ON stg.races (circuitId);

    PRINT N'Da tao bang stg.races va cac index kem theo.';
END
GO

-- ----------------------------------------------------------------------------
-- 7. stg.results (results.csv - 27,568 rows)
-- Grain: Mot dong cho ket qua cua mot tay dua trong mot race event
-- Natural key: resultId
-- Tham chieu: raceId -> races, driverId -> drivers, constructorId -> constructors, statusId -> status
-- Luu y: position, time, milliseconds, fastestLapSpeed co the la NULL do DNF/chua co thong ke
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.results', N'U') IS NULL
BEGIN
    CREATE TABLE stg.results (
        resultId            INT NOT NULL,
        raceId              INT NOT NULL,
        driverId            INT NOT NULL,
        constructorId       INT NOT NULL,
        number              INT NULL,
        grid                INT NOT NULL,
        position            INT NULL,
        positionText        NVARCHAR(10) NOT NULL,
        positionOrder       INT NOT NULL,
        points              DECIMAL(6, 2) NOT NULL,
        laps                INT NOT NULL,
        [time]              NVARCHAR(50) NULL,
        milliseconds        INT NULL,
        fastestLap          INT NULL,
        [rank]              INT NULL,
        fastestLapTime      NVARCHAR(50) NULL,
        fastestLapSpeed     DECIMAL(7, 3) NULL,
        statusId            INT NOT NULL,

        -- Metadata Lineage columns
        _source_file        NVARCHAR(260) NULL,
        _batch_key          NVARCHAR(100) NULL,
        _load_mode          VARCHAR(20) NULL,
        _ingested_at_utc    DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_results_ingested DEFAULT SYSUTCDATETIME(),

        CONSTRAINT PK_stg_results PRIMARY KEY CLUSTERED (resultId)
    );

    CREATE NONCLUSTERED INDEX IX_stg_results_raceId ON stg.results (raceId);
    CREATE NONCLUSTERED INDEX IX_stg_results_driverId ON stg.results (driverId);
    CREATE NONCLUSTERED INDEX IX_stg_results_constructorId ON stg.results (constructorId);
    CREATE NONCLUSTERED INDEX IX_stg_results_statusId ON stg.results (statusId);

    PRINT N'Da tao bang stg.results va cac index kem theo.';
END
GO
