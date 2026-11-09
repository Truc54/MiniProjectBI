-- ============================================================================
-- Script: 02_seed_unknown_members.sql
-- Description: Khoi tao cau truc va seed ban ghi mac dinh Unknown Member (SK = -1)
--              cho cac bang Dimension trong Schema dw
-- ============================================================================

USE F1_BI;
GO

PRINT N'====================================================================';
PRINT N'KHOI TAO BANG CHIEU & SEED UNKNOWN RECORD (SK = -1)';
PRINT N'====================================================================';

-- ----------------------------------------------------------------------------
-- 1. dw.DimDate
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimDate', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimDate (
        DateSK              INT NOT NULL,
        FullDate            DATE NOT NULL,
        DayNumber           INT NOT NULL,
        MonthNumber         INT NOT NULL,
        MonthName           NVARCHAR(20) NOT NULL,
        QuarterNumber       INT NOT NULL,
        CalendarYear        INT NOT NULL,
        WeekdayName         NVARCHAR(20) NOT NULL,
        CONSTRAINT PK_DimDate PRIMARY KEY CLUSTERED (DateSK)
    );
    PRINT N'[SUCCESS] Da khoi tao bang dw.DimDate.';
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimDate WHERE DateSK = -1)
BEGIN
    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimDate'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimDate ON;

    INSERT INTO dw.DimDate (
        DateSK, FullDate, DayNumber, MonthNumber, MonthName,
        QuarterNumber, CalendarYear, WeekdayName
    )
    VALUES (
        -1, '1900-01-01', 1, 1, N'Unknown', 1, 1900, N'Unknown'
    );

    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimDate'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimDate OFF;

    PRINT N'[SUCCESS] Da seed ban ghi Unknown Member (DateSK = -1) cho dw.DimDate.';
END
ELSE
BEGIN
    PRINT N'[INFO] Ban ghi DateSK = -1 da ton tai trong dw.DimDate.';
END
GO

-- ----------------------------------------------------------------------------
-- 2. dw.DimRace
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimRace', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimRace (
        RaceSK              INT NOT NULL,
        SourceRaceId        INT NOT NULL,
        SeasonYear          INT NOT NULL,
        RoundNumber         INT NOT NULL,
        RaceName            NVARCHAR(200) NOT NULL,
        RaceDate            DATE NULL,
        CircuitId           INT NULL,
        Url                 NVARCHAR(500) NULL,
        CONSTRAINT PK_DimRace PRIMARY KEY CLUSTERED (RaceSK)
    );
    PRINT N'[SUCCESS] Da khoi tao bang dw.DimRace.';
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimRace WHERE RaceSK = -1)
BEGIN
    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimRace'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimRace ON;

    INSERT INTO dw.DimRace (
        RaceSK, SourceRaceId, SeasonYear, RoundNumber,
        RaceName, RaceDate, CircuitId, Url
    )
    VALUES (
        -1, -1, 1900, 0, N'Unknown Grand Prix', '1900-01-01', -1, NULL
    );

    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimRace'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimRace OFF;

    PRINT N'[SUCCESS] Da seed ban ghi Unknown Member (RaceSK = -1) cho dw.DimRace.';
END
ELSE
BEGIN
    PRINT N'[INFO] Ban ghi RaceSK = -1 da ton tai trong dw.DimRace.';
END
GO

-- ----------------------------------------------------------------------------
-- 3. dw.DimCircuit
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimCircuit', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimCircuit (
        CircuitSK           INT NOT NULL,
        SourceCircuitId     INT NOT NULL,
        CircuitRef          NVARCHAR(100) NOT NULL,
        CircuitName         NVARCHAR(200) NOT NULL,
        Locality            NVARCHAR(100) NULL,
        Country             NVARCHAR(100) NULL,
        Latitude            DECIMAL(9, 6) NULL,
        Longitude           DECIMAL(9, 6) NULL,
        Altitude            INT NULL,
        Url                 NVARCHAR(500) NULL,
        CONSTRAINT PK_DimCircuit PRIMARY KEY CLUSTERED (CircuitSK)
    );
    PRINT N'[SUCCESS] Da khoi tao bang dw.DimCircuit.';
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimCircuit WHERE CircuitSK = -1)
BEGIN
    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimCircuit'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimCircuit ON;

    INSERT INTO dw.DimCircuit (
        CircuitSK, SourceCircuitId, CircuitRef, CircuitName,
        Locality, Country, Latitude, Longitude, Altitude, Url
    )
    VALUES (
        -1, -1, N'unknown', N'Unknown Circuit', N'Unknown', N'Unknown', NULL, NULL, NULL, NULL
    );

    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimCircuit'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimCircuit OFF;

    PRINT N'[SUCCESS] Da seed ban ghi Unknown Member (CircuitSK = -1) cho dw.DimCircuit.';
END
ELSE
BEGIN
    PRINT N'[INFO] Ban ghi CircuitSK = -1 da ton tai trong dw.DimCircuit.';
END
GO

-- ----------------------------------------------------------------------------
-- 4. dw.DimDriver
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimDriver', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimDriver (
        DriverSK            INT NOT NULL,
        SourceDriverId      INT NOT NULL,
        DriverRef           NVARCHAR(100) NOT NULL,
        DriverNumber        INT NULL,
        DriverCode          NVARCHAR(10) NULL,
        Forename            NVARCHAR(100) NOT NULL,
        Surname             NVARCHAR(100) NOT NULL,
        FullName            NVARCHAR(200) NOT NULL,
        DateOfBirth         DATE NULL,
        Nationality         NVARCHAR(100) NULL,
        Url                 NVARCHAR(500) NULL,
        CONSTRAINT PK_DimDriver PRIMARY KEY CLUSTERED (DriverSK)
    );
    PRINT N'[SUCCESS] Da khoi tao bang dw.DimDriver.';
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimDriver WHERE DriverSK = -1)
BEGIN
    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimDriver'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimDriver ON;

    INSERT INTO dw.DimDriver (
        DriverSK, SourceDriverId, DriverRef, DriverNumber, DriverCode,
        Forename, Surname, FullName, DateOfBirth, Nationality, Url
    )
    VALUES (
        -1, -1, N'unknown', NULL, N'UNK',
        N'Unknown', N'Driver', N'Unknown Driver', '1900-01-01', N'Unknown', NULL
    );

    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimDriver'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimDriver OFF;

    PRINT N'[SUCCESS] Da seed ban ghi Unknown Member (DriverSK = -1) cho dw.DimDriver.';
END
ELSE
BEGIN
    PRINT N'[INFO] Ban ghi DriverSK = -1 da ton tai trong dw.DimDriver.';
END
GO

-- ----------------------------------------------------------------------------
-- 5. dw.DimConstructor
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimConstructor', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimConstructor (
        ConstructorSK       INT NOT NULL,
        SourceConstructorId INT NOT NULL,
        ConstructorRef      NVARCHAR(100) NOT NULL,
        ConstructorName     NVARCHAR(200) NOT NULL,
        Nationality         NVARCHAR(100) NULL,
        Url                 NVARCHAR(500) NULL,
        CONSTRAINT PK_DimConstructor PRIMARY KEY CLUSTERED (ConstructorSK)
    );
    PRINT N'[SUCCESS] Da khoi tao bang dw.DimConstructor.';
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimConstructor WHERE ConstructorSK = -1)
BEGIN
    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimConstructor'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimConstructor ON;

    INSERT INTO dw.DimConstructor (
        ConstructorSK, SourceConstructorId, ConstructorRef,
        ConstructorName, Nationality, Url
    )
    VALUES (
        -1, -1, N'unknown', N'Unknown Constructor', N'Unknown', NULL
    );

    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimConstructor'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimConstructor OFF;

    PRINT N'[SUCCESS] Da seed ban ghi Unknown Member (ConstructorSK = -1) cho dw.DimConstructor.';
END
ELSE
BEGIN
    PRINT N'[INFO] Ban ghi ConstructorSK = -1 da ton tai trong dw.DimConstructor.';
END
GO

-- ----------------------------------------------------------------------------
-- 6. dw.DimStatus
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dw.DimStatus', N'U') IS NULL
BEGIN
    CREATE TABLE dw.DimStatus (
        StatusSK            INT NOT NULL,
        SourceStatusId      INT NOT NULL,
        SourceStatusLabel   NVARCHAR(100) NOT NULL,
        OutcomeGroup        NVARCHAR(50) NOT NULL,
        CONSTRAINT PK_DimStatus PRIMARY KEY CLUSTERED (StatusSK)
    );
    PRINT N'[SUCCESS] Da khoi tao bang dw.DimStatus.';
END
GO

IF NOT EXISTS (SELECT 1 FROM dw.DimStatus WHERE StatusSK = -1)
BEGIN
    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimStatus'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimStatus ON;

    INSERT INTO dw.DimStatus (
        StatusSK, SourceStatusId, SourceStatusLabel, OutcomeGroup
    )
    VALUES (
        -1, -1, N'Unknown Status', N'OTHER'
    );

    IF OBJECTPROPERTY(OBJECT_ID(N'dw.DimStatus'), 'TableHasIdentity') = 1
        SET IDENTITY_INSERT dw.DimStatus OFF;

    PRINT N'[SUCCESS] Da seed ban ghi Unknown Member (StatusSK = -1) cho dw.DimStatus.';
END
ELSE
BEGIN
    PRINT N'[INFO] Ban ghi StatusSK = -1 da ton tai trong dw.DimStatus.';
END
GO

PRINT N'====================================================================';
PRINT N'[HOAN TAT] Script 02_seed_unknown_members.sql da thuc thi thanh cong!';
PRINT N'====================================================================';
GO
