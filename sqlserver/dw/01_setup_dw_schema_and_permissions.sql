-- ============================================================================
-- Script: 01_setup_dw_schema_and_permissions.sql
-- Description: Khoi tao Schema dw, stg_clean va phan quyen truy cap cho dbt & BI
-- Tac gia: Dung (Database Administrator & Physical DW Optimization Specialist)
-- Phase: 2 - Data Transformation & Data Warehouse
-- ============================================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'F1_BI')
BEGIN
    CREATE DATABASE F1_BI;
    PRINT N'[INFO] Da tao Database F1_BI.';
END
GO

USE F1_BI;
GO

PRINT N'====================================================================';
PRINT N'1. KHOI TAO CAC SCHEMA: dw VA stg_clean (IDEMPOTENT)';
PRINT N'====================================================================';

-- Schema dw: luu tru cac bang Dimensional Model (Fact & Dimensions)
IF SCHEMA_ID(N'dw') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA dw');
    PRINT N'[SUCCESS] Da tao Schema [dw].';
END
ELSE
BEGIN
    PRINT N'[INFO] Schema [dw] da ton tai san.';
END
GO

-- Schema stg_clean: luu tru cac Staging Views do dbt bien doi tu stg sang marts
IF SCHEMA_ID(N'stg_clean') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA stg_clean');
    PRINT N'[SUCCESS] Da tao Schema [stg_clean].';
END
ELSE
BEGIN
    PRINT N'[INFO] Schema [stg_clean] da ton tai san.';
END
GO

PRINT N'====================================================================';
PRINT N'2. PHAN QUYEN CHO TAI KHOAN ETL / dbt (f1_loader)';
PRINT N'====================================================================';

-- Dam bao Database User f1_loader ton tai
IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = N'f1_loader')
BEGIN
    IF EXISTS (SELECT name FROM sys.server_principals WHERE name = N'f1_loader')
    BEGIN
        CREATE USER f1_loader FOR LOGIN f1_loader;
        PRINT N'[SUCCESS] Da tao Database User f1_loader trong F1_BI.';
    END
    ELSE
    BEGIN
        PRINT N'[WARNING] Login f1_loader chua ton tai o cap server; vui long chay 00_create_database_and_user.sql truoc.';
    END
END
GO

IF EXISTS (SELECT name FROM sys.database_principals WHERE name = N'f1_loader')
BEGIN
    -- Gan cac role co ban
    ALTER ROLE db_datareader ADD MEMBER f1_loader;
    ALTER ROLE db_datawriter ADD MEMBER f1_loader;
    ALTER ROLE db_ddladmin ADD MEMBER f1_loader;

    -- Cap quyen chi tiet tren schema dw va stg_clean
    GRANT CREATE TABLE TO f1_loader;
    GRANT CREATE VIEW TO f1_loader;
    GRANT CREATE SCHEMA TO f1_loader;
    GRANT EXECUTE TO f1_loader;

    GRANT CONTROL ON SCHEMA::dw TO f1_loader;
    GRANT CONTROL ON SCHEMA::stg_clean TO f1_loader;
    GRANT SELECT, INSERT, UPDATE, DELETE, ALTER, REFERENCES ON SCHEMA::dw TO f1_loader;
    GRANT SELECT, INSERT, UPDATE, DELETE, ALTER, REFERENCES ON SCHEMA::stg_clean TO f1_loader;

    PRINT N'[SUCCESS] Da phan quyen CONTROL, DDL va DML toan dien tren dw & stg_clean cho user f1_loader.';
END
GO

PRINT N'====================================================================';
PRINT N'3. KHOI TAO ROLE READ-ONLY CHO POWER BI / ANALYST (db_dw_reader)';
PRINT N'====================================================================';

IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = N'db_dw_reader' AND type = 'R')
BEGIN
    CREATE ROLE db_dw_reader;
    PRINT N'[SUCCESS] Da tao Database Role [db_dw_reader].';
END
GO

GRANT SELECT ON SCHEMA::dw TO db_dw_reader;
PRINT N'[SUCCESS] Da cap quyen SELECT tren Schema [dw] cho role [db_dw_reader].';
GO

PRINT N'====================================================================';
PRINT N'[HOAN TAT] Script 01_setup_dw_schema_and_permissions.sql da thuc thi thanh cong!';
PRINT N'====================================================================';
GO
