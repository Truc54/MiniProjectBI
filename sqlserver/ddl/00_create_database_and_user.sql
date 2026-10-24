-- ============================================================================
-- Script: 00_create_database_and_user.sql
-- Description: Khoi tao Database F1_BI va cap quyen cho user f1_loader
-- Chay bang quyen sysadmin (sa hoac Windows Authentication) tren master
-- ============================================================================

USE master;
GO

-- 1. Tao Database neu chua ton tai
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'F1_BI')
BEGIN
    CREATE DATABASE F1_BI;
    PRINT N'Da tao Database F1_BI thanh cong.';
END
ELSE
BEGIN
    PRINT N'Database F1_BI da ton tai.';
END
GO

USE F1_BI;
GO

-- 2. Tao Login o muc Server (neu chua co)
-- Luu y: Thay doi mat khau phu hop voi gia tri trong file .env (MSSQL_PASSWORD)
IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = N'f1_loader')
BEGIN
    CREATE LOGIN f1_loader WITH PASSWORD = N'F1Loader@2026_SecurePwd!', CHECK_POLICY = ON;
    PRINT N'Da tao Login f1_loader tren Server.';
END
ELSE
BEGIN
    PRINT N'Login f1_loader da ton tai.';
END
GO

-- 3. Tao User trong Database F1_BI
IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = N'f1_loader')
BEGIN
    CREATE USER f1_loader FOR LOGIN f1_loader;
    PRINT N'Da tao Database User f1_loader trong F1_BI.';
END
ELSE
BEGIN
    PRINT N'Database User f1_loader da ton tai.';
END
GO

-- 4. Cap quyen co ban de tao/nap du lieu va thao tac schema
-- User can quyen tren stg, ctl, dw
ALTER ROLE db_datareader ADD MEMBER f1_loader;
ALTER ROLE db_datawriter ADD MEMBER f1_loader;
ALTER ROLE db_ddladmin ADD MEMBER f1_loader;

GRANT CREATE TABLE TO f1_loader;
GRANT CREATE VIEW TO f1_loader;
GRANT CREATE SCHEMA TO f1_loader;
GRANT EXECUTE TO f1_loader;

PRINT N'Da phan quyen thanh cong cho user f1_loader tren Database F1_BI.';
GO
