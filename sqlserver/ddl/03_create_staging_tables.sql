-- ============================================================================
-- Script: 03_create_staging_tables.sql
-- Description: DDL Idempotent tao 7 bang Staging loi (stg) cho Formula 1 Dataset
-- Tac gia: Dung (SQL Server & Staging)
-- Phien ban: 2.0 (Dong bo voi Source-to-Stage Mapping Contract P3-v1.0 cua Phuc & Model cua Truc)
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
-- Grain: Mot dong moi circuit (duong dua)
-- Natural key: circuitId (PK)
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.circuits', N'U') IS NULL
BEGIN
    CREATE TABLE stg.circuits (
        circuitId           INT NOT NULL,
        circuitRef          NVARCHAR(100) NOT NULL,
        name                NVARCHAR(255) NOT NULL,
        location            NVARCHAR(100) NOT NULL,
        country             NVARCHAR(100) NOT NULL,
        lat                 FLOAT NOT NULL,
        lng                 FLOAT NOT NULL,
        alt                 INT NOT NULL,
        url                 NVARCHAR(500) NOT NULL,

        -- Metadata Lineage columns (Contract Section 5)
        _src_file           NVARCHAR(260) NOT NULL,
        _batch_key          NVARCHAR(100) NOT NULL,
        _loaded_at_utc      DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_circuits_loaded DEFAULT SYSUTCDATETIME(),
        _load_mode          VARCHAR(20) NOT NULL,

        CONSTRAINT PK_stg_circuits PRIMARY KEY CLUSTERED (circuitId)
    );
    PRINT N'Da tao bang stg.circuits.';
END
GO

-- ----------------------------------------------------------------------------
-- 2. stg.constructors (constructors.csv - 214 rows)
-- Grain: Mot dong moi constructor (doi dua)
-- Natural key: constructorId (PK)
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.constructors', N'U') IS NULL
BEGIN
    CREATE TABLE stg.constructors (
        constructorId       INT NOT NULL,
        constructorRef      NVARCHAR(100) NOT NULL,
        name                NVARCHAR(255) NOT NULL,
        nationality         NVARCHAR(100) NOT NULL,
        url                 NVARCHAR(500) NOT NULL,

        -- Metadata Lineage columns (Contract Section 5)
        _src_file           NVARCHAR(260) NOT NULL,
        _batch_key          NVARCHAR(100) NOT NULL,
        _loaded_at_utc      DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_constructors_loaded DEFAULT SYSUTCDATETIME(),
        _load_mode          VARCHAR(20) NOT NULL,

        CONSTRAINT PK_stg_constructors PRIMARY KEY CLUSTERED (constructorId)
    );
    PRINT N'Da tao bang stg.constructors.';
END
GO

-- ----------------------------------------------------------------------------
-- 3. stg.drivers (drivers.csv - 879 rows)
-- Grain: Mot dong moi tay dua F1
-- Natural key: driverId (PK)
-- Luu y: number (816 \N), code (771 \N), dob (14 \N), nationality & url (14 "") co NULL
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.drivers', N'U') IS NULL
BEGIN
    CREATE TABLE stg.drivers (
        driverId            INT NOT NULL,
        driverRef           NVARCHAR(100) NOT NULL,
        number              INT NULL,
        code                NCHAR(3) NULL,
        forename            NVARCHAR(100) NOT NULL,
        surname             NVARCHAR(100) NOT NULL,
        dob                 DATE NULL,
        nationality         NVARCHAR(100) NULL,
        url                 NVARCHAR(500) NULL,

        -- Metadata Lineage columns (Contract Section 5)
        _src_file           NVARCHAR(260) NOT NULL,
        _batch_key          NVARCHAR(100) NOT NULL,
        _loaded_at_utc      DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_drivers_loaded DEFAULT SYSUTCDATETIME(),
        _load_mode          VARCHAR(20) NOT NULL,

        CONSTRAINT PK_stg_drivers PRIMARY KEY CLUSTERED (driverId)
    );
    PRINT N'Da tao bang stg.drivers.';
END
GO

-- ----------------------------------------------------------------------------
-- 4. stg.status (status.csv - 141 rows)
-- Grain: Mot dong moi finishing status code
-- Natural key: statusId (PK)
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.status', N'U') IS NULL
BEGIN
    CREATE TABLE stg.status (
        statusId            INT NOT NULL,
        status              NVARCHAR(255) NOT NULL,

        -- Metadata Lineage columns (Contract Section 5)
        _src_file           NVARCHAR(260) NOT NULL,
        _batch_key          NVARCHAR(100) NOT NULL,
        _loaded_at_utc      DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_status_loaded DEFAULT SYSUTCDATETIME(),
        _load_mode          VARCHAR(20) NOT NULL,

        CONSTRAINT PK_stg_status PRIMARY KEY CLUSTERED (statusId)
    );
    PRINT N'Da tao bang stg.status.';
END
GO

-- ----------------------------------------------------------------------------
-- 5. stg.seasons (seasons.csv - 77 rows, 1950-2026)
-- Grain: Mot dong moi championship season
-- Natural key: year (PK)
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.seasons', N'U') IS NULL
BEGIN
    CREATE TABLE stg.seasons (
        [year]              SMALLINT NOT NULL,
        url                 NVARCHAR(500) NOT NULL,

        -- Metadata Lineage columns (Contract Section 5)
        _src_file           NVARCHAR(260) NOT NULL,
        _batch_key          NVARCHAR(100) NOT NULL,
        _loaded_at_utc      DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_seasons_loaded DEFAULT SYSUTCDATETIME(),
        _load_mode          VARCHAR(20) NOT NULL,

        CONSTRAINT PK_stg_seasons PRIMARY KEY CLUSTERED ([year])
    );
    PRINT N'Da tao bang stg.seasons.';
END
GO

-- ----------------------------------------------------------------------------
-- 6. stg.races (races.csv - 1,164 rows, 1950-2026)
-- Grain: Mot dong moi su kien race (Grand Prix)
-- Natural key: raceId (PK)
-- Tham chieu: circuitId -> stg.circuits, year -> stg.seasons
-- Luu y: time va cac session schedule (fp1-3, quali, sprint) co NULL hop le
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'stg.races', N'U') IS NULL
BEGIN
    CREATE TABLE stg.races (
        raceId              INT NOT NULL,
        [year]              SMALLINT NOT NULL,
        [round]             TINYINT NOT NULL,
        circuitId           INT NOT NULL,
        name                NVARCHAR(255) NOT NULL,
        [date]              DATE NOT NULL,
        [time]              TIME(0) NULL,
        url                 NVARCHAR(500) NOT NULL,
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

        -- Metadata Lineage columns (Contract Section 5)
        _src_file           NVARCHAR(260) NOT NULL,
        _batch_key          NVARCHAR(100) NOT NULL,
        _loaded_at_utc      DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_races_loaded DEFAULT SYSUTCDATETIME(),
        _load_mode          VARCHAR(20) NOT NULL,

        CONSTRAINT PK_stg_races PRIMARY KEY CLUSTERED (raceId)
    );

    CREATE NONCLUSTERED INDEX IX_stg_races_year ON stg.races ([year]);
    CREATE NONCLUSTERED INDEX IX_stg_races_circuitId ON stg.races (circuitId);

    PRINT N'Da tao bang stg.races va cac index kem theo.';
END
GO

-- ----------------------------------------------------------------------------
-- 7. stg.results (results.csv - 27,568 rows)
-- Grain: Mot ket qua cua mot tay dua trong mot race event (Central Fact)
-- Natural key: resultId (PK)
-- Tham chieu: raceId -> races, driverId -> drivers, constructorId -> constructors, statusId -> status
-- Luu y: position (40.2% NULL DNF/unclassified), fastestLapSpeed (70.1% NULL)
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
        fastestLapSpeed     DECIMAL(8, 3) NULL,
        statusId            INT NOT NULL,

        -- Metadata Lineage columns (Contract Section 5)
        _src_file           NVARCHAR(260) NOT NULL,
        _batch_key          NVARCHAR(100) NOT NULL,
        _loaded_at_utc      DATETIME2(3) NOT NULL
            CONSTRAINT DF_stg_results_loaded DEFAULT SYSUTCDATETIME(),
        _load_mode          VARCHAR(20) NOT NULL,

        CONSTRAINT PK_stg_results PRIMARY KEY CLUSTERED (resultId)
    );

    CREATE NONCLUSTERED INDEX IX_stg_results_raceId ON stg.results (raceId);
    CREATE NONCLUSTERED INDEX IX_stg_results_driverId ON stg.results (driverId);
    CREATE NONCLUSTERED INDEX IX_stg_results_constructorId ON stg.results (constructorId);
    CREATE NONCLUSTERED INDEX IX_stg_results_statusId ON stg.results (statusId);

    PRINT N'Da tao bang stg.results va cac index kem theo.';
END
GO
