# Source-to-Stage Mapping — Formula 1 World Championship

> **Contract version:** P3-v1.0 · **Locked:** 2026-10-22 · **Author:** Phúc  
> Thay đổi sau ngày này phải được ghi change note ở cuối file và thông báo Dũng + Lộc.

---

## 1. Quy tắc chung áp dụng cho mọi bảng

| Quy tắc | Nội dung |
|---|---|
| **Tên cột** | Giữ nguyên tên cột nguồn (camelCase theo Kaggle). Không đổi tên trong Stage. |
| **Null marker** | Literal `\N` trong CSV → `NULL` trong SQL Server. ETL phải nhận diện chuỗi `"\N"` và chuyển thành `NULL`, không lưu nguyên chuỗi. |
| **Empty string** | Chuỗi rỗng `""` trong CSV cũng → `NULL` trong SQL Server (áp dụng cho `drivers.nationality`, `drivers.url`, `qualifying.q2`, `qualifying.q3` và các cột tương tự). |
| **Không fill NULL** | Không đổi NULL thành `0`, `''`, `'unknown'`, hay bất cứ giá trị mặc định nào. |
| **Không drop row** | Không xóa dòng chỉ vì một cột tùy chọn là NULL. Dòng chỉ bị reject khi PK/composite key là NULL hoặc có lỗi parse nghiêm trọng. |
| **Metadata columns** | Cột kỹ thuật (`_src_file`, `_batch_key`, `_loaded_at_utc`, `_load_mode`) thêm vào Stage **sau** tất cả cột nguồn. Không ghi đè cột nguồn. |
| **Unicode** | Cột tên, ref, url, nationality dùng `NVARCHAR`. |
| **Numeric cast** | Cast số chỉ khi giá trị nguồn hợp lệ (không phải `\N` hoặc `""`). |
| **Thứ tự nạp** | Lookup/dimension trước, fact sau. Xem Section 3. |
| **Idempotency** | Full Load: TRUNCATE rồi INSERT. Incremental: MERGE/UPSERT theo natural key, không INSERT trùng. |

---

## 2. Bảng lõi Phase 1 — Mapping chi tiết cột theo cột

### 2.1 `circuits.csv` → `stg.circuits`

**Grain:** Một dòng mỗi circuit (đường đua).  
**Natural key:** `circuitId` (INT, NOT NULL, UNIQUE).  
**FK đến bảng này:** `races.circuitId`.  
**Rows (snapshot 2026-10-22):** 78.

| Cột nguồn | SQL Server type | Nullable | Ghi chú |
|---|---|---|---|
| `circuitId` | `INT` | NOT NULL | PK nguồn; enforce UNIQUE trong Stage |
| `circuitRef` | `NVARCHAR(100)` | NOT NULL | Slug URL-safe, duy nhất |
| `name` | `NVARCHAR(255)` | NOT NULL | Tên circuit đầy đủ |
| `location` | `NVARCHAR(100)` | NOT NULL | Thành phố/địa danh |
| `country` | `NVARCHAR(100)` | NOT NULL | Quốc gia |
| `lat` | `FLOAT` | NOT NULL | Vĩ độ |
| `lng` | `FLOAT` | NOT NULL | Kinh độ |
| `alt` | `INT` | NOT NULL | Độ cao (m); `0` = placeholder cho circuit mới sau 2024 — không phải NULL |
| `url` | `NVARCHAR(500)` | NOT NULL | Wikipedia URL |
| `_src_file` | `NVARCHAR(260)` | NOT NULL | Tên file nguồn, ví dụ `circuits.csv` |
| `_batch_key` | `NVARCHAR(100)` | NOT NULL | Batch identifier |
| `_loaded_at_utc` | `DATETIME2(3)` | NOT NULL | Thời điểm nạp UTC |
| `_load_mode` | `VARCHAR(20)` | NOT NULL | `FULL` hoặc `INCREMENTAL` |

**NULL notes:** Không có `\N` trong file này. `alt = 0` là giá trị thực (không phải NULL) theo source schema.

---

### 2.2 `constructors.csv` → `stg.constructors`

**Grain:** Một dòng mỗi constructor (đội đua).  
**Natural key:** `constructorId` (INT, NOT NULL, UNIQUE).  
**FK đến bảng này:** `results.constructorId`, `qualifying.constructorId`, `sprint_results.constructorId`, `constructor_standings.constructorId`, `constructor_results.constructorId`.  
**Rows:** 214.

| Cột nguồn | SQL Server type | Nullable | Ghi chú |
|---|---|---|---|
| `constructorId` | `INT` | NOT NULL | PK nguồn |
| `constructorRef` | `NVARCHAR(100)` | NOT NULL | Slug URL-safe |
| `name` | `NVARCHAR(255)` | NOT NULL | Tên đội |
| `nationality` | `NVARCHAR(100)` | NOT NULL | Quốc tịch |
| `url` | `NVARCHAR(500)` | NOT NULL | Wikipedia URL |
| `_src_file` | `NVARCHAR(260)` | NOT NULL | |
| `_batch_key` | `NVARCHAR(100)` | NOT NULL | |
| `_loaded_at_utc` | `DATETIME2(3)` | NOT NULL | |
| `_load_mode` | `VARCHAR(20)` | NOT NULL | |

**NULL notes:** Không có `\N` hay empty string trong file này.

---

### 2.3 `drivers.csv` → `stg.drivers`

**Grain:** Một dòng mỗi tay đua.  
**Natural key:** `driverId` (INT, NOT NULL, UNIQUE).  
**FK đến bảng này:** `results.driverId`, `qualifying.driverId`, `sprint_results.driverId`, `driver_standings.driverId`, `lap_times.driverId`, `pit_stops.driverId`, `practice_results.driverId`, `tire_stints.driverId`.  
**Rows:** 879.

| Cột nguồn | SQL Server type | Nullable | Ghi chú |
|---|---|---|---|
| `driverId` | `INT` | NOT NULL | PK nguồn |
| `driverRef` | `NVARCHAR(100)` | NOT NULL | Slug URL-safe |
| `number` | `INT` | **NULL** | `\N` = số xe vĩnh viễn chưa được cấp (816 rows) |
| `code` | `NCHAR(3)` | **NULL** | `\N` = mã 3 chữ chưa được cấp (771 rows) |
| `forename` | `NVARCHAR(100)` | NOT NULL | Tên |
| `surname` | `NVARCHAR(100)` | NOT NULL | Họ |
| `dob` | `DATE` | **NULL** | `\N` = ngày sinh không rõ (14 rows) |
| `nationality` | `NVARCHAR(100)` | **NULL** | Empty string `""` → NULL (14 rows) |
| `url` | `NVARCHAR(500)` | **NULL** | Empty string `""` → NULL (14 rows) |
| `_src_file` | `NVARCHAR(260)` | NOT NULL | |
| `_batch_key` | `NVARCHAR(100)` | NOT NULL | |
| `_loaded_at_utc` | `DATETIME2(3)` | NOT NULL | |
| `_load_mode` | `VARCHAR(20)` | NOT NULL | |

**NULL notes:**
- `number`: 816 `\N` → NULL. Tay đua lịch sử không có số xe vĩnh viễn.
- `code`: 771 `\N` → NULL. Mã 3 ký tự chỉ được cấp từ thời hiện đại.
- `dob`: 14 `\N` → NULL. DOB không có trong nguồn cho tay đua rất cổ.
- `nationality`, `url`: 14 empty string `""` → NULL. ETL phải xử lý riêng empty string (không phải `\N`).

---

### 2.4 `status.csv` → `stg.status`

**Grain:** Một dòng mỗi mã kết quả kết thúc race.  
**Natural key:** `statusId` (INT, NOT NULL, UNIQUE).  
**FK đến bảng này:** `results.statusId`, `sprint_results.statusId`.  
**Rows:** 141.

| Cột nguồn | SQL Server type | Nullable | Ghi chú |
|---|---|---|---|
| `statusId` | `INT` | NOT NULL | PK nguồn |
| `status` | `NVARCHAR(255)` | NOT NULL | Mô tả kết quả, ví dụ `'Finished'`, `'+1 Lap'`, `'Engine'` |
| `_src_file` | `NVARCHAR(260)` | NOT NULL | |
| `_batch_key` | `NVARCHAR(100)` | NOT NULL | |
| `_loaded_at_utc` | `DATETIME2(3)` | NOT NULL | |
| `_load_mode` | `VARCHAR(20)` | NOT NULL | |

**NULL notes:** Không có `\N`. Bảng lookup hoàn chỉnh, 141 dòng.

---

### 2.5 `seasons.csv` → `stg.seasons`

**Grain:** Một dòng mỗi mùa giải (năm).  
**Natural key:** `year` (INT, NOT NULL, UNIQUE).  
**FK đến bảng này:** `races.year`.  
**Rows:** 77. **Year range:** 1950–2026.

| Cột nguồn | SQL Server type | Nullable | Ghi chú |
|---|---|---|---|
| `year` | `SMALLINT` | NOT NULL | PK nguồn (1950–2026) |
| `url` | `NVARCHAR(500)` | NOT NULL | Wikipedia URL cho mùa giải |
| `_src_file` | `NVARCHAR(260)` | NOT NULL | |
| `_batch_key` | `NVARCHAR(100)` | NOT NULL | |
| `_loaded_at_utc` | `DATETIME2(3)` | NOT NULL | |
| `_load_mode` | `VARCHAR(20)` | NOT NULL | |

**NULL notes:** Không có `\N`. Bảng anchor cho season filtering.

---

### 2.6 `races.csv` → `stg.races`

**Grain:** Một dòng mỗi sự kiện race (Grand Prix).  
**Natural key:** `raceId` (INT, NOT NULL, UNIQUE).  
**Candidate join key:** `(year, round)` — duy nhất trong file.  
**FK ra ngoài:** `circuitId → stg.circuits`, `year → stg.seasons`.  
**FK đến bảng này:** `results.raceId`, `qualifying.raceId`, `sprint_results.raceId`, `driver_standings.raceId`, `constructor_standings.raceId`, `constructor_results.raceId`, `lap_times.raceId`, `pit_stops.raceId`, `practice_results.raceId`, `tire_stints.raceId`, `weather.raceId`.  
**Rows:** 1,164. **Year range:** 1950–2026.

| Cột nguồn | SQL Server type | Nullable | Ghi chú |
|---|---|---|---|
| `raceId` | `INT` | NOT NULL | PK nguồn |
| `year` | `SMALLINT` | NOT NULL | FK → seasons.year |
| `round` | `TINYINT` | NOT NULL | Số thứ tự vòng trong mùa |
| `circuitId` | `INT` | NOT NULL | FK → circuits.circuitId |
| `name` | `NVARCHAR(255)` | NOT NULL | Tên chính thức, ví dụ `'Monaco Grand Prix'` |
| `date` | `DATE` | NOT NULL | Ngày race (YYYY-MM-DD) |
| `time` | `TIME(0)` | **NULL** | Giờ khởi đầu UTC; `\N` = không rõ (731 rows — race cổ) |
| `url` | `NVARCHAR(500)` | NOT NULL | Wikipedia URL |
| `fp1_date` | `DATE` | **NULL** | Ngày FP1; `\N` = race cũ hoặc chưa có lịch (1,035 rows) |
| `fp1_time` | `TIME(0)` | **NULL** | Giờ FP1 UTC (1,057 rows NULL) |
| `fp2_date` | `DATE` | **NULL** | Ngày FP2 (1,046 rows NULL) |
| `fp2_time` | `TIME(0)` | **NULL** | Giờ FP2 UTC (1,068 rows NULL) |
| `fp3_date` | `DATE` | **NULL** | Ngày FP3 (1,064 rows NULL) |
| `fp3_time` | `TIME(0)` | **NULL** | Giờ FP3 UTC (1,083 rows NULL) |
| `quali_date` | `DATE` | **NULL** | Ngày qualifying (1,035 rows NULL) |
| `quali_time` | `TIME(0)` | **NULL** | Giờ qualifying UTC (1,057 rows NULL) |
| `sprint_date` | `DATE` | **NULL** | Ngày sprint; `\N` = không có sprint weekend (~1,135 rows) |
| `sprint_time` | `TIME(0)` | **NULL** | Giờ sprint UTC (~1,138 rows NULL) |
| `_src_file` | `NVARCHAR(260)` | NOT NULL | |
| `_batch_key` | `NVARCHAR(100)` | NOT NULL | |
| `_loaded_at_utc` | `DATETIME2(3)` | NOT NULL | |
| `_load_mode` | `VARCHAR(20)` | NOT NULL | |

**NULL notes:**
- `time`: 731 rows — giờ race UTC không có cho race lịch sử. Expected.
- `fp1/fp2/fp3/quali_date/time`: NULL cho race trước khi có lịch session cấu trúc. Expected.
- `sprint_date/sprint_time`: NULL cho khoảng 97.5% race không có sprint weekend. Expected — không phải data lỗi.

---

### 2.7 `results.csv` → `stg.results`

**Grain:** Một kết quả của một tay đua trong một race. Đây là bảng fact trung tâm.  
**Natural key:** `resultId` (INT, NOT NULL, UNIQUE).  
**Candidate join key:** `(raceId, driverId)` — duy nhất trong file.  
**FK ra ngoài:** `raceId → stg.races`, `driverId → stg.drivers`, `constructorId → stg.constructors`, `statusId → stg.status`.  
**Rows:** 27,568.

| Cột nguồn | SQL Server type | Nullable | Ghi chú |
|---|---|---|---|
| `resultId` | `INT` | NOT NULL | PK nguồn |
| `raceId` | `INT` | NOT NULL | FK → races.raceId |
| `driverId` | `INT` | NOT NULL | FK → drivers.driverId |
| `constructorId` | `INT` | NOT NULL | FK → constructors.constructorId |
| `number` | `INT` | **NULL** | Số xe trong race; 6 rows NULL — anomaly cần điều tra |
| `grid` | `INT` | NOT NULL | Vị trí xuất phát |
| `position` | `INT` | **NULL** | Vị trí về đích phân loại; `\N` = không phân loại DNF/DSQ/DNS (11,074 rows — 40.2%) |
| `positionText` | `NVARCHAR(10)` | NOT NULL | Vị trí dạng text: số hoặc `'R'`/`'D'`/`'W'`/`'N'`/`'F'` |
| `positionOrder` | `INT` | NOT NULL | Thứ tự số để sắp xếp — luôn có giá trị, dùng thay `position` khi sort |
| `points` | `DECIMAL(6,2)` | NOT NULL | Điểm championship |
| `laps` | `INT` | NOT NULL | Số vòng hoàn thành |
| `time` | `NVARCHAR(20)` | **NULL** | Thời gian race (leader) hoặc gap; `\N` nếu không phân loại (19,212 rows) |
| `milliseconds` | `INT` | **NULL** | Thời gian race (ms); `\N` nếu không áp dụng (19,200 rows) |
| `fastestLap` | `INT` | **NULL** | Số vòng chạy nhanh nhất; `\N` = không theo dõi (18,542 rows) |
| `rank` | `INT` | **NULL** | Hạng fastest lap trong race; `\N` = không theo dõi (18,284 rows) |
| `fastestLapTime` | `NVARCHAR(15)` | **NULL** | Thời gian fastest lap dạng string; `\N` = không theo dõi (18,542 rows) |
| `fastestLapSpeed` | `DECIMAL(8,3)` | **NULL** | Tốc độ trung bình fastest lap (km/h); `\N` cho toàn bộ 2025/2026 + race cũ (19,316 rows) |
| `statusId` | `INT` | NOT NULL | FK → status.statusId |
| `_src_file` | `NVARCHAR(260)` | NOT NULL | |
| `_batch_key` | `NVARCHAR(100)` | NOT NULL | |
| `_loaded_at_utc` | `DATETIME2(3)` | NOT NULL | |
| `_load_mode` | `VARCHAR(20)` | NOT NULL | |

**NULL notes quan trọng:**
- `position`: **PRIMARY expected-NULL column** — 40.2% rows là NULL hợp lệ (unclassified results). Không bao giờ filter `WHERE position IS NOT NULL` mà không chủ ý.
- `fastestLapSpeed`: 70.1% NULL — nguồn API Jolpica không cung cấp cho 2025/2026. Documented trong source README.
- `time`, `milliseconds`: ~69.7% NULL — chỉ leader có absolute time; gap dùng cho classified finishers.
- `number`: 6 NULL — anomaly, không phải pattern có chủ đích; cần ghi lại và kiểm tra trước staging.
- `positionOrder` luôn có giá trị — dùng cho ORDER BY thay vì `position`.

---

## 3. Thứ tự nạp cho Phase 1

```
Bước 1 (Lookups — không có FK nội bộ):
  circuits, constructors, drivers, status, seasons

Bước 2 (Race dimension — FK → circuits, seasons):
  races

Bước 3 (Central fact — FK → races, drivers, constructors, status):
  results
```

Bước 1 có thể nạp song song. Bước 2 phải sau Bước 1. Bước 3 phải sau Bước 2.  
FK constraint trong SQL Server chỉ enable sau khi đủ dữ liệu hoặc disable trong quá trình nạp và validate bằng query riêng.

---

## 4. Bảng phụ — Profile và quyết định phạm vi

Các bảng dưới đây được profile đầy đủ ở P2. Chỉ thêm vào Stage khi có câu hỏi phân tích cụ thể yêu cầu. Grain khác với `stg.results` — không join tùy tiện để tránh nhân bản fact.

| Source file | Grain | Natural / Composite key | \N notable | Coverage | Quyết định Phase 1 |
|---|---|---|---|---|---|
| `qualifying.csv` | 1 driver trong 1 qualifying session | `qualifyId` | q1: 184, q2: 4,855, q3: 7,251 (expected — knockout format) | 1950–2026 | **Không nạp** — grain khác; Q2/Q3 NULL expected |
| `sprint_results.csv` | 1 driver trong 1 sprint race | `resultId` (sprint) | position: 34, time: 40 (expected) | Sprint weekends only | **Không nạp** — grain riêng, subset weekend |
| `driver_standings.csv` | 1 driver sau 1 race (cumulative) | `driverStandingsId` | Không có \N | 1950–2026 | **Không nạp** — lũy kế, có thể derive từ fact |
| `constructor_standings.csv` | 1 constructor sau 1 race (cumulative) | `constructorStandingsId` | Không có \N | 1950–2026 | **Không nạp** — lũy kế, có thể derive |
| `constructor_results.csv` | 1 constructor trong 1 race | `constructorResultsId` | status: 13,009 (\N = not DSQ — semantic flag) | 1950–2026 | **Không nạp** — derivable từ results |
| `lap_times.csv` | 1 lap của 1 driver trong 1 race | `(raceId, driverId, lap)` | Không có \N | **1950–2024 only** | **Không nạp** — 632,937 rows; không có 2025/2026 |
| `pit_stops.csv` | 1 pit stop của 1 driver | `(raceId, driverId, stop)` | duration: 1 (anomaly) | 1950–2026 | **Không nạp** — grain pit stop, không có câu hỏi Phase 1 |
| `practice_results.csv` | 1 driver trong 1 FP session | `(raceId, driverId, session)` | Không có \N | **2025/2026 only** | **Không nạp** — coverage thiếu 1950–2024 |
| `tire_stints.csv` | 1 stint lốp của 1 driver | `(raceId, driverId, stint)` | compound: 5 (unknown) | **2025/2026 only** | **Không nạp** — coverage thiếu 1950–2024 |
| `weather.csv` | 1 tóm tắt thời tiết mỗi race | `raceId` | Không có \N | **2025/2026 only, 39 rows** | **Không nạp** — coverage thiếu, không có câu hỏi Phase 1 |

---

## 5. Metadata columns contract (interface cho Lộc/Dũng)

Mỗi bảng Stage thêm 4 cột kỹ thuật ở cuối, sau tất cả cột nguồn:

| Cột | SQL Server type | NOT NULL | Mô tả |
|---|---|---|---|
| `_src_file` | `NVARCHAR(260)` | YES | Tên file CSV nguồn, ví dụ `results.csv` |
| `_batch_key` | `NVARCHAR(100)` | YES | Batch identifier do Mage gán, ví dụ `results_full_20261022` |
| `_loaded_at_utc` | `DATETIME2(3)` | YES | Thời điểm nạp row vào Stage (UTC) |
| `_load_mode` | `VARCHAR(20)` | YES | `FULL` hoặc `INCREMENTAL` |

> **Lưu ý Lộc:** `_batch_key` phải khớp với `batch_key` trong `ctl.etl_run_log` và `ctl.etl_batch_state` để traceable.

---

## 6. Null handling rules tóm tắt (checklist cho ETL)

```
[1] Đọc CSV bằng Python csv.DictReader hoặc tương đương — giữ nguyên encoding UTF-8.
[2] Với mỗi cell:
    - Nếu cell == "\N"  → truyền NULL (None) vào SQL Server
    - Nếu cell == ""    → truyền NULL (None) vào SQL Server
    - Ngược lại         → giữ nguyên giá trị, parse theo kiểu cột
[3] Không thay NULL bằng 0 hoặc string mặc định ở bất kỳ cột nào.
[4] Log row bị reject chỉ khi: PK/composite key là NULL, hoặc parse lỗi trên cột NOT NULL.
[5] results.position = NULL là hợp lệ và phổ biến (40.2%) — không reject.
[6] qualifying.q2 / q3 = NULL là hợp lệ — không reject.
[7] races.*_date / *_time = NULL là hợp lệ — không reject.
[8] results.fastestLapSpeed = NULL là hợp lệ — không reject (source limitation).
```

---

## 7. Reconciliation queries (interface cho Dũng)

Sau khi nạp đủ 7 bảng, chạy các truy vấn sau để nghiệm thu:

```sql
-- 7.1 Row count theo bảng (so với baseline source profile)
SELECT 'stg.circuits'      AS tbl, COUNT(*) AS rows FROM stg.circuits      UNION ALL
SELECT 'stg.constructors'  AS tbl, COUNT(*) AS rows FROM stg.constructors  UNION ALL
SELECT 'stg.drivers'       AS tbl, COUNT(*) AS rows FROM stg.drivers       UNION ALL
SELECT 'stg.status'        AS tbl, COUNT(*) AS rows FROM stg.status        UNION ALL
SELECT 'stg.seasons'       AS tbl, COUNT(*) AS rows FROM stg.seasons       UNION ALL
SELECT 'stg.races'         AS tbl, COUNT(*) AS rows FROM stg.races         UNION ALL
SELECT 'stg.results'       AS tbl, COUNT(*) AS rows FROM stg.results;
-- Expected: 78, 214, 879, 141, 77, 1164, 27568

-- 7.2 PK NULL / duplicate check
SELECT 'circuits'     AS tbl, SUM(CASE WHEN circuitId     IS NULL THEN 1 ELSE 0 END) AS null_pk, COUNT(*) - COUNT(DISTINCT circuitId)     AS dup_pk FROM stg.circuits     UNION ALL
SELECT 'constructors' AS tbl, SUM(CASE WHEN constructorId IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT constructorId) FROM stg.constructors UNION ALL
SELECT 'drivers'      AS tbl, SUM(CASE WHEN driverId      IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT driverId)      FROM stg.drivers      UNION ALL
SELECT 'status'       AS tbl, SUM(CASE WHEN statusId      IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT statusId)      FROM stg.status       UNION ALL
SELECT 'seasons'      AS tbl, SUM(CASE WHEN [year]        IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT [year])        FROM stg.seasons      UNION ALL
SELECT 'races'        AS tbl, SUM(CASE WHEN raceId        IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT raceId)        FROM stg.races        UNION ALL
SELECT 'results'      AS tbl, SUM(CASE WHEN resultId      IS NULL THEN 1 ELSE 0 END), COUNT(*) - COUNT(DISTINCT resultId)      FROM stg.results;
-- Expected: tất cả null_pk = 0, dup_pk = 0

-- 7.3 FK orphan check (chạy sau khi nạp đủ 7 bảng)
SELECT 'results->races'        AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.races        p WHERE p.raceId        = r.raceId)        UNION ALL
SELECT 'results->drivers'      AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.drivers      p WHERE p.driverId      = r.driverId)      UNION ALL
SELECT 'results->constructors' AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.constructors p WHERE p.constructorId = r.constructorId) UNION ALL
SELECT 'results->status'       AS fk, COUNT(*) AS orphans FROM stg.results        r WHERE NOT EXISTS (SELECT 1 FROM stg.status       p WHERE p.statusId      = r.statusId)       UNION ALL
SELECT 'races->circuits'       AS fk, COUNT(*) AS orphans FROM stg.races          r WHERE NOT EXISTS (SELECT 1 FROM stg.circuits     p WHERE p.circuitId     = r.circuitId)      UNION ALL
SELECT 'races->seasons'        AS fk, COUNT(*) AS orphans FROM stg.races          r WHERE NOT EXISTS (SELECT 1 FROM stg.seasons      p WHERE p.[year]        = r.[year]);
-- Expected: tất cả orphans = 0

-- 7.4 results.position NULL rate (so với source: ~40.2%)
SELECT
    COUNT(*)                                              AS total_rows,
    SUM(CASE WHEN position IS NULL THEN 1 ELSE 0 END)    AS position_null,
    CAST(100.0 * SUM(CASE WHEN position IS NULL THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,1)) AS pct_null
FROM stg.results;
-- Expected: ~11074 NULL, ~40.2%

-- 7.5 results.fastestLapSpeed NULL (so với source: ~70.1%)
SELECT
    SUM(CASE WHEN fastestLapSpeed IS NULL THEN 1 ELSE 0 END) AS fls_null,
    COUNT(*) AS total
FROM stg.results;
-- Expected: ~19316 NULL

-- 7.6 Kiểm tra \N không còn tồn tại dạng string trong Stage
SELECT TOP 5 * FROM stg.results WHERE positionText = N'\N';
-- Expected: 0 rows

-- 7.7 Batch log check
SELECT source_name, source_table, batch_key, batch_status, source_row_count
FROM ctl.etl_batch_state
ORDER BY loaded_at_utc DESC;
```

---

## 8. Change log

| Version | Ngày | Tác giả | Nội dung |
|---|---|---|---|
| P3-v1.0 | 2026-10-22 | Phúc | Initial full mapping — 7 bảng lõi cột-theo-cột, SQL types, NULL rules, thứ tự nạp, 10 bảng phụ quyết định, metadata contract, reconciliation queries |
