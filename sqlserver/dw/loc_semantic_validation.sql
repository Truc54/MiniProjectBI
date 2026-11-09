-- ============================================================================
-- Script: loc_semantic_validation.sql
-- Muc dich: Tham dinh ngu nghia dw sau dbt build (Phase 2, nhiem vu 5 cua Loc)
--   * Cot "stage" tinh truc tiep tu stg.* (nguon su that)
--   * Cot "expected" lay tu docs/evidence/loc_phase2_expected_baseline.json (tinh tu CSV)
--   * PASS khi dw = stage; neu check khong co stage thi dw = expected
-- Ten cot dw theo stage_to_dw_mapping.md (snake_case, quyet dinh D1). Neu nhom chot
-- PascalCase, doi ten theo bang doi chieu muc 10 cua tai lieu mapping.
-- Bo sung cho sqlserver/dw/dw_reconciliation_queries.sql cua Dung (row count, checksum, orphan).
-- Chay: sqlcmd -d F1_BI -i sqlserver/dw/loc_semantic_validation.sql
-- Tong ket cuoi script: 0 FAIL moi duoc nghiem thu.
-- ============================================================================
SET NOCOUNT ON;
IF DB_ID(N'F1_BI') IS NOT NULL USE F1_BI;

DECLARE @checks TABLE (
    check_id     INT,
    check_name   NVARCHAR(120),
    expected     DECIMAL(18, 2) NULL,
    stage_value  DECIMAL(18, 2) NULL,
    dw_value     DECIMAL(18, 2) NULL
);

-- ---------------------------------------------------------------------------
-- 1. So dong va measure cong don (fact vs stage)
-- ---------------------------------------------------------------------------
INSERT INTO @checks
SELECT 1, N'fact rows = stg.results rows', 27568,
       (SELECT COUNT(*) FROM stg.results), (SELECT COUNT(*) FROM dw.FactRaceResult)
UNION ALL
SELECT 2, N'distinct source_result_id', 27568,
       (SELECT COUNT(DISTINCT resultId) FROM stg.results),
       (SELECT COUNT(DISTINCT source_result_id) FROM dw.FactRaceResult)
UNION ALL
SELECT 3, N'SUM(points)', 57126.05,
       (SELECT SUM(points) FROM stg.results), (SELECT SUM(points) FROM dw.FactRaceResult)
UNION ALL
-- ---------------------------------------------------------------------------
-- 2. Co dan xuat (KPI contract business_requirements.md muc 3)
-- ---------------------------------------------------------------------------
SELECT 5, N'wins (positionOrder = 1, gom 3 shared drive)', 1167,
       (SELECT COUNT(*) FROM stg.results WHERE positionOrder = 1),
       (SELECT SUM(CAST(is_win AS INT)) FROM dw.FactRaceResult)
UNION ALL
SELECT 6, N'races co nguoi thang', 1164,
       (SELECT COUNT(DISTINCT raceId) FROM stg.results WHERE positionOrder = 1),
       (SELECT COUNT(DISTINCT race_sk) FROM dw.FactRaceResult WHERE is_win = 1)
UNION ALL
SELECT 7, N'podiums (position 1-3)', 3513,
       (SELECT COUNT(*) FROM stg.results WHERE position BETWEEN 1 AND 3),
       (SELECT SUM(CAST(is_podium AS INT)) FROM dw.FactRaceResult)
UNION ALL
SELECT 8, N'classified (position NOT NULL)', 16494,
       (SELECT COUNT(*) FROM stg.results WHERE position IS NOT NULL),
       (SELECT SUM(CAST(is_classified AS INT)) FROM dw.FactRaceResult)
UNION ALL
SELECT 9, N'grid = 0 rows', 1638,
       (SELECT COUNT(*) FROM stg.results WHERE grid = 0),
       (SELECT COUNT(*) FROM dw.FactRaceResult WHERE is_valid_grid_start = 0)
UNION ALL
SELECT 10, N'places_gained eligible rows', 16434,
       (SELECT COUNT(*) FROM stg.results WHERE grid > 0 AND position IS NOT NULL),
       (SELECT COUNT(places_gained) FROM dw.FactRaceResult)
UNION ALL
SELECT 11, N'SUM(places_gained)', 48282,
       (SELECT SUM(grid - position) FROM stg.results WHERE grid > 0 AND position IS NOT NULL),
       (SELECT SUM(places_gained) FROM dw.FactRaceResult)
UNION ALL
-- ---------------------------------------------------------------------------
-- 3. OutcomeGroup (stage_to_dw_mapping.md muc 4.1) - dong ket qua theo nhom.
--    stage: stg.results noi DimStatus qua statusId nguon; dw: fact noi DimStatus qua status_sk.
--    Lech nhau => fact gan sai status_sk.
-- ---------------------------------------------------------------------------
SELECT 14, N'outcome CLASSIFIED rows', 15839,
       (SELECT COUNT(*) FROM stg.results r JOIN dw.DimStatus s ON s.source_status_id = r.statusId WHERE s.outcome_group = 'CLASSIFIED'),
       (SELECT COUNT(*) FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk WHERE s.outcome_group = 'CLASSIFIED')
UNION ALL
SELECT 15, N'outcome RETIREMENT_DNF rows', 9771,
       (SELECT COUNT(*) FROM stg.results r JOIN dw.DimStatus s ON s.source_status_id = r.statusId WHERE s.outcome_group = 'RETIREMENT_DNF'),
       (SELECT COUNT(*) FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk WHERE s.outcome_group = 'RETIREMENT_DNF')
UNION ALL
SELECT 16, N'outcome OTHER rows', 1538,
       (SELECT COUNT(*) FROM stg.results r JOIN dw.DimStatus s ON s.source_status_id = r.statusId WHERE s.outcome_group = 'OTHER'),
       (SELECT COUNT(*) FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk WHERE s.outcome_group = 'OTHER')
UNION ALL
SELECT 17, N'outcome DNS rows', 258,
       (SELECT COUNT(*) FROM stg.results r JOIN dw.DimStatus s ON s.source_status_id = r.statusId WHERE s.outcome_group = 'DNS'),
       (SELECT COUNT(*) FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk WHERE s.outcome_group = 'DNS')
UNION ALL
SELECT 18, N'outcome DSQ rows', 162,
       (SELECT COUNT(*) FROM stg.results r JOIN dw.DimStatus s ON s.source_status_id = r.statusId WHERE s.outcome_group = 'DSQ'),
       (SELECT COUNT(*) FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk WHERE s.outcome_group = 'DSQ')
UNION ALL
SELECT 19, N'status codes UNREVIEWED (khong tinh -1)', 0, NULL,
       (SELECT COUNT(*) FROM dw.DimStatus WHERE outcome_category = 'UNREVIEWED' AND status_sk <> -1)
UNION ALL
SELECT 20, N'result_outcome_code WITHDRAWN rows', 346,
       (SELECT COUNT(*) FROM stg.results WHERE positionText = N'W'),
       (SELECT COUNT(*) FROM dw.FactRaceResult WHERE result_outcome_code = 'WITHDRAWN')
UNION ALL
-- ---------------------------------------------------------------------------
-- 4. Dimension: so dong nguon + 1 Unknown, va Unknown trong fact
-- ---------------------------------------------------------------------------
SELECT 21, N'DimRace rows (+1 unknown)', 1165, (SELECT COUNT(*) + 1 FROM stg.races), (SELECT COUNT(*) FROM dw.DimRace)
UNION ALL
SELECT 22, N'DimCircuit rows (+1 unknown)', 79, (SELECT COUNT(*) + 1 FROM stg.circuits), (SELECT COUNT(*) FROM dw.DimCircuit)
UNION ALL
SELECT 23, N'DimDriver rows (+1 unknown)', 880, (SELECT COUNT(*) + 1 FROM stg.drivers), (SELECT COUNT(*) FROM dw.DimDriver)
UNION ALL
SELECT 24, N'DimConstructor rows (+1 unknown)', 215, (SELECT COUNT(*) + 1 FROM stg.constructors), (SELECT COUNT(*) FROM dw.DimConstructor)
UNION ALL
SELECT 25, N'DimStatus rows (+1 unknown)', 142, (SELECT COUNT(*) + 1 FROM stg.status), (SELECT COUNT(*) FROM dw.DimStatus)
UNION ALL
SELECT 26, N'DimDate rows nam min..max cua races (+1)', 28125,
       (SELECT DATEDIFF(day, DATEFROMPARTS(MIN([year]), 1, 1), DATEFROMPARTS(MAX([year]), 12, 31)) + 2 FROM stg.races),
       (SELECT COUNT(*) FROM dw.DimDate)
UNION ALL
SELECT 27, N'DimDate race days', 1164, (SELECT COUNT(DISTINCT [date]) FROM stg.races),
       (SELECT COUNT(*) FROM dw.DimDate WHERE is_race_day = 1)
UNION ALL
SELECT 28, N'fact rows tro ve Unknown (-1)', 0, NULL,
       (SELECT COUNT(*) FROM dw.FactRaceResult
        WHERE -1 IN (date_sk, race_sk, circuit_sk, driver_sk, constructor_sk, status_sk))
UNION ALL
-- ---------------------------------------------------------------------------
-- 5. Lam sach chuoi va lich
-- ---------------------------------------------------------------------------
SELECT 29, N'driver_nationality con khoang trang thua', 0, NULL,
       (SELECT COUNT(*) FROM dw.DimDriver WHERE driver_nationality <> LTRIM(RTRIM(driver_nationality))
                                             OR DATALENGTH(driver_nationality) <> DATALENGTH(LTRIM(RTRIM(driver_nationality))))
UNION ALL
SELECT 30, N'DimDate day_name 2008-03-16 = Sunday (1 = dung)', 1, NULL,
       (SELECT COUNT(*) FROM dw.DimDate WHERE date_sk = 20080316 AND day_name = 'Sunday' AND day_of_week_number = 7)
UNION ALL
-- ---------------------------------------------------------------------------
-- 6. Doi soat theo khoa va theo tung gia tri (khong chi tong)
-- ---------------------------------------------------------------------------
SELECT 31, N'resultId co o stage nhung thieu trong fact', 0, NULL,
       (SELECT COUNT(*) FROM stg.results r
        WHERE NOT EXISTS (SELECT 1 FROM dw.FactRaceResult f WHERE f.source_result_id = r.resultId))
UNION ALL
SELECT 32, N'source_result_id co trong fact nhung khong co o stage', 0, NULL,
       (SELECT COUNT(*) FROM dw.FactRaceResult f
        WHERE NOT EXISTS (SELECT 1 FROM stg.results r WHERE r.resultId = f.source_result_id))
UNION ALL
-- Moi cot chuyen thang tu stage phai giong het (so sanh null-safe bang INTERSECT)
SELECT 33, N'dong fact lech gia tri voi stage (measure, khoa, SK, date_sk)', 0, NULL,
       (SELECT COUNT(*)
        FROM dw.FactRaceResult f
        JOIN stg.results r ON r.resultId = f.source_result_id
        JOIN stg.races  ra ON ra.raceId  = r.raceId
        WHERE NOT EXISTS (
            SELECT f.points, f.grid_position, f.finish_position, f.position_order,
                   f.position_text,
                   f.race_sk, f.driver_sk, f.constructor_sk, f.status_sk, f.circuit_sk, f.date_sk
            INTERSECT
            SELECT r.points, r.grid, r.position, r.positionOrder,
                   LTRIM(RTRIM(r.positionText)),
                   r.raceId, r.driverId, r.constructorId, r.statusId, ra.circuitId,
                   CAST(CONVERT(CHAR(8), ra.[date], 112) AS INT)))
UNION ALL
-- Cot dan xuat phai dung cong thuc muc 5.2-5.3 tren tung dong
SELECT 34, N'dong fact sai cot dan xuat (flag, places_gained, outcome code)', 0, NULL,
       (SELECT COUNT(*)
        FROM dw.FactRaceResult f
        JOIN stg.results r ON r.resultId = f.source_result_id
        WHERE NOT EXISTS (
            SELECT CAST(f.is_win AS INT), CAST(f.is_podium AS INT), CAST(f.is_classified AS INT),
                   CAST(f.is_points_finish AS INT), CAST(f.is_valid_grid_start AS INT),
                   f.places_gained, f.result_outcome_code
            INTERSECT
            SELECT CASE WHEN r.positionOrder = 1 THEN 1 ELSE 0 END,
                   CASE WHEN r.position BETWEEN 1 AND 3 THEN 1 ELSE 0 END,
                   CASE WHEN r.position IS NOT NULL THEN 1 ELSE 0 END,
                   CASE WHEN r.points > 0 THEN 1 ELSE 0 END,
                   CASE WHEN r.grid > 0 THEN 1 ELSE 0 END,
                   CASE WHEN r.grid > 0 AND r.position IS NOT NULL THEN r.grid - r.position END,
                   CASE
                       WHEN r.positionText NOT LIKE '%[^0-9]%' AND r.positionText <> '' THEN 'CLASSIFIED'
                       WHEN r.positionText = 'R' THEN 'RETIRED'
                       WHEN r.positionText = 'D' THEN 'DISQUALIFIED'
                       WHEN r.positionText = 'E' THEN 'EXCLUDED'
                       WHEN r.positionText = 'W' THEN 'WITHDRAWN'
                       WHEN r.positionText = 'F' THEN 'FAILED_TO_QUALIFY'
                       WHEN r.positionText = 'N' THEN 'NOT_CLASSIFIED'
                       ELSE 'UNKNOWN'
                   END))
UNION ALL
SELECT 35, N'result_outcome_code UNKNOWN rows', 0, NULL,
       (SELECT COUNT(*) FROM dw.FactRaceResult WHERE result_outcome_code = 'UNKNOWN')
UNION ALL
-- ---------------------------------------------------------------------------
-- 7. DimStatus: so ma moi nhom (muc 4.1) va cap group/category hop le
-- ---------------------------------------------------------------------------
SELECT 36, N'DimStatus ma RETIREMENT_DNF', 96, NULL,
       (SELECT COUNT(*) FROM dw.DimStatus WHERE outcome_group = 'RETIREMENT_DNF')
UNION ALL
SELECT 37, N'DimStatus ma CLASSIFIED', 35, NULL,
       (SELECT COUNT(*) FROM dw.DimStatus WHERE outcome_group = 'CLASSIFIED')
UNION ALL
SELECT 38, N'DimStatus cap outcome_group/outcome_category sai', 0, NULL,
       (SELECT COUNT(*) FROM dw.DimStatus
        WHERE NOT (   (outcome_group = 'CLASSIFIED' AND outcome_category = 'FINISHED_OR_LAPPED')
                   OR (outcome_group = 'DNS' AND outcome_category = 'DID_NOT_START')
                   OR (outcome_group = 'DSQ' AND outcome_category = 'DISQUALIFIED')
                   OR (outcome_group = 'OTHER' AND outcome_category IN ('NOT_QUALIFIED_OR_NOT_CLASSIFIED', 'UNREVIEWED'))
                   OR (outcome_group = 'RETIREMENT_DNF' AND outcome_category IN
                       ('MECHANICAL', 'ACCIDENT_DAMAGE', 'DRIVER_MEDICAL', 'OTHER_RETIREMENT'))))
UNION ALL
SELECT 39, N'DimStatus status_label khac stage', 0, NULL,
       (SELECT COUNT(*) FROM dw.DimStatus d JOIN stg.status s ON s.statusId = d.source_status_id
        WHERE d.status_label <> LTRIM(RTRIM(s.status)))
UNION ALL
-- ---------------------------------------------------------------------------
-- 8. Unknown member: dung 1 dong -1 o moi dim (6 dim)
-- ---------------------------------------------------------------------------
SELECT 40, N'so dong SK = -1 tren 6 dim (moi dim dung 1)', 6, NULL,
       (SELECT (SELECT COUNT(*) FROM dw.DimDate WHERE date_sk = -1)
             + (SELECT COUNT(*) FROM dw.DimRace WHERE race_sk = -1)
             + (SELECT COUNT(*) FROM dw.DimCircuit WHERE circuit_sk = -1)
             + (SELECT COUNT(*) FROM dw.DimDriver WHERE driver_sk = -1)
             + (SELECT COUNT(*) FROM dw.DimConstructor WHERE constructor_sk = -1)
             + (SELECT COUNT(*) FROM dw.DimStatus WHERE status_sk = -1))
UNION ALL
SELECT 41, N'dim co SK <> natural key (SK phai deterministic)', 0, NULL,
       (SELECT (SELECT COUNT(*) FROM dw.DimRace WHERE race_sk <> source_race_id)
             + (SELECT COUNT(*) FROM dw.DimCircuit WHERE circuit_sk <> source_circuit_id)
             + (SELECT COUNT(*) FROM dw.DimDriver WHERE driver_sk <> source_driver_id)
             + (SELECT COUNT(*) FROM dw.DimConstructor WHERE constructor_sk <> source_constructor_id)
             + (SELECT COUNT(*) FROM dw.DimStatus WHERE status_sk <> source_status_id))
UNION ALL
SELECT 42, N'DimDriver driver_nationality NULL (khong tinh -1)', 14,
       (SELECT COUNT(*) FROM stg.drivers WHERE NULLIF(LTRIM(RTRIM(nationality)), N'') IS NULL),
       (SELECT COUNT(*) FROM dw.DimDriver WHERE driver_nationality IS NULL AND driver_sk <> -1)
UNION ALL
-- ---------------------------------------------------------------------------
-- 9. Thang diem ky nguyen (muc 8.1): so mua co diem nguoi thang max khac quy dinh
-- ---------------------------------------------------------------------------
SELECT 43, N'mua sai thang diem ky nguyen (max diem nguoi thang)', 0, NULL,
       (SELECT COUNT(*) FROM (
            SELECT r.season_year, MAX(f.points) AS max_points
            FROM dw.FactRaceResult f JOIN dw.DimRace r ON r.race_sk = f.race_sk
            WHERE f.is_win = 1
            GROUP BY r.season_year) w
        WHERE w.max_points <> CASE
                WHEN w.season_year <= 1959 THEN 9
                WHEN w.season_year = 1960 THEN 8
                WHEN w.season_year <= 1990 THEN 9
                WHEN w.season_year <= 2009 THEN 10
                WHEN w.season_year = 2014 THEN 50
                WHEN w.season_year BETWEEN 2019 AND 2024 THEN 26
                ELSE 25 END);

SELECT check_id, check_name, expected, stage_value, dw_value,
       CASE
           WHEN dw_value = COALESCE(stage_value, expected) THEN 'PASS'
           ELSE 'FAIL'
       END AS result,
       CASE
           WHEN stage_value IS NOT NULL AND stage_value <> expected
               THEN N'Stage khac snapshot CSV (batch moi?) - dung stage lam chuan'
       END AS note
FROM @checks
ORDER BY check_id;

SELECT COUNT(*) AS total_checks,
       SUM(CASE WHEN dw_value = COALESCE(stage_value, expected) THEN 1 ELSE 0 END) AS passed,
       SUM(CASE WHEN dw_value = COALESCE(stage_value, expected) THEN 0 ELSE 1 END) AS failed
FROM @checks;

-- ---------------------------------------------------------------------------
-- 10. Truy vet mau 1 dong (business_requirements.md muc 7, diem 2)
--    Mong doi: Hamilton / McLaren / 2008 R01 Australian GP / Finished / 10 diem
-- ---------------------------------------------------------------------------
SELECT f.source_result_id, d.full_name, c.constructor_name, r.race_label, ci.circuit_name,
       dt.full_date, s.status_label, s.outcome_group, f.result_outcome_code,
       f.grid_position, f.finish_position, f.places_gained, f.points, f.is_win, f.is_podium,
       sr.points AS stage_points, sr.position AS stage_position
FROM dw.FactRaceResult f
JOIN dw.DimDriver d       ON d.driver_sk = f.driver_sk
JOIN dw.DimConstructor c  ON c.constructor_sk = f.constructor_sk
JOIN dw.DimRace r         ON r.race_sk = f.race_sk
JOIN dw.DimCircuit ci     ON ci.circuit_sk = f.circuit_sk
JOIN dw.DimDate dt        ON dt.date_sk = f.date_sk
JOIN dw.DimStatus s       ON s.status_sk = f.status_sk
JOIN stg.results sr       ON sr.resultId = f.source_result_id
WHERE f.source_result_id = 1;
