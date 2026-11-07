# Stage-to-DW Transformation Mapping (Phase 2)

> **Phiên bản:** P2-v1.2 (bản bàn giao) · **Ngày:** 2026-11-06 · **Tác giả:** Lộc
> **Người dùng tài liệu:** Trực (viết dbt models), Dũng (DW vật lý + đối soát), Phúc (dbt tests + nghiệm thu)
> **Nguồn sự thật:** DDL [`sqlserver/ddl/03_create_staging_tables.sql`](../../sqlserver/ddl/03_create_staging_tables.sql) cho kiểu dữ liệu `stg`; [`dimensional_model.md`](../01_architecture_and_design/dimensional_model.md) cho grain và quy tắc measure.
> **Tài liệu đi kèm:**
> - [`status_outcome_mapping.csv`](status_outcome_mapping.csv): bảng phân nhóm 141 status.
> - [`stg_status_outcome.sql`](stg_status_outcome.sql): SQL `stg_status` đầy đủ (không placeholder), Trực dán thẳng vào dbt.
> - [`dw_data_dictionary.md`](dw_data_dictionary.md): từ điển dữ liệu DW.
> - [`../evidence/loc_phase2_expected_baseline.json`](../evidence/loc_phase2_expected_baseline.json): số liệu kỳ vọng để đối soát.
>
> Ba file CSV, SQL và JSON được sinh lại bằng `python3 tests/phase2_expected_baseline.py`. Tính nhất quán giữa chúng và với hai tài liệu Markdown được kiểm tra bằng `python3 -m unittest tests.test_phase2_mapping -v`.

---

## 1. Các quyết định nhóm cần chốt trước khi viết code

Các kế hoạch Phase 2 của bốn người có một số điểm mâu thuẫn. Bảng dưới đây ghi đề xuất của Lộc. Các phần sau của tài liệu đã viết theo đề xuất này.

| # | Vấn đề | Đề xuất | Ảnh hưởng |
|---|---|---|---|
| **D1** | **Quy ước tên.** Trong kế hoạch, Trực và Phúc dùng `snake_case` (`source_result_id`, `driver_sk`). Dũng và `dimensional_model.md` dùng PascalCase (`DriverSK`, `SourceDriverId`, `dw.FactRaceResult`). | File model dbt đặt tên `snake_case` (`dim_driver.sql`, `fact_race_result.sql`). **Tên bảng vật lý dùng PascalCase qua `alias`**, ví dụ `{{ config(alias='DimDriver') }}`, để khớp DoD và các script của Dũng. **Tên cột dùng `snake_case`** để khớp `unique_key` và `schema.yml`. | Dũng đổi tên cột trong script seed/đối soát. Power BI có thể đổi tên hiển thị sau. |
| **D2** | **Cách sinh surrogate key.** Dim dạng `table` được dựng lại mỗi lần chạy. Nếu SK sinh bằng `ROW_NUMBER()` hoặc `IDENTITY` thì SK có thể đổi giữa các lần build. Khi đó các dòng cũ trong Fact (incremental, không dựng lại) sẽ trỏ sai chiều. | **SK xác định (deterministic).** `*_sk` = khóa nguồn kiểu INT (`driver_sk = driverId`, …). `date_sk = YYYYMMDD` (INT). Unknown member dùng `-1`. Khóa nguồn F1 là số nguyên dương, ổn định và không tái sử dụng, nên cách này an toàn. Các dim là SCD Type 1. | Không cần `IDENTITY`. Fact join bằng khóa nguồn. Rebuild dim không làm hỏng FK. |
| **D3** | **Unknown member (`-1`).** Kế hoạch của Dũng seed dòng `-1` bằng script SQL riêng. Nhưng `materialized='table'` sẽ DROP rồi CREATE lại bảng ở mỗi `dbt run`, nên dòng seed bị mất. | **Tạo dòng `-1` ngay trong model dim** bằng `UNION ALL` (mục 6). Script của Dũng chuyển thành **kiểm tra** "mỗi dim có đúng 1 dòng `-1`", không INSERT nữa. | Dũng dùng bảng giá trị ở mục 6. |
| **D4** | **Tính chất của `stg.results`.** Mục 3.1 kế hoạch của Trực ghi Stage là *transient* (chỉ giữ batch hiện tại). Code Phase 1 ([`sqlserver.py`](../../mage/project/f1_etl/sqlserver.py), dòng 112–117) cho thấy Full thì xóa toàn bảng, còn Incremental thì **xóa theo khóa rồi chèn**. Như vậy Stage **tích lũy** (upsert). | Giữ `incremental_strategy='delete+insert'`, `unique_key='source_result_id'`, vì vẫn đúng và idempotent. Bổ sung bộ lọc `is_incremental()` theo `_ingested_at_utc > max(...)` để chỉ xử lý dòng mới. Dim dựng từ toàn bộ Stage là đúng. | Sửa mô tả trong kế hoạch của Trực. |
| **D5** | **Taxonomy `OutcomeGroup`.** Kế hoạch Phase 2 và `dimensional_model.md` dùng 5 nhóm `CLASSIFIED / DNS / DSQ / RETIREMENT_DNF / OTHER`. Mục 4 của `business_requirements.md` lại dùng 5 nhóm khác: tách *Mechanical* với *Accident*, và gộp DNS với DNQ. | Giữ **5 nhóm của kế hoạch Phase 2** trong `outcome_group` (đã có trong `accepted_values`). Thêm cột phụ **`outcome_category`** để phân tích độ tin cậy, gồm `MECHANICAL`, `ACCIDENT_DAMAGE`, `DRIVER_MEDICAL`, `OTHER_RETIREMENT`. Cột này đáp ứng đúng nhu cầu của `business_requirements.md`. | Cần cập nhật mục 4 của `business_requirements.md` cho khớp (Phúc/Trực). |
| **D6** | **Kết quả ở mức dòng.** Có **108 dòng `positionText = 'W'`** (rút lui, không xuất phát) mang status cơ khí như *Engine* hay *Accident*. Nếu chỉ nhìn `DimStatus` thì các dòng này bị tính là DNF, trong khi thực tế xe không xuất phát. | Fact giữ thêm `position_text` và cột dẫn xuất **`result_outcome_code`** lấy từ `positionText` (mục 5.3). Đây là phân loại chính thức của từng dòng. `OutcomeGroup` chỉ giải thích *lý do*. | Thêm 2 cột vào fact, có `accepted_values`. |

---

## 2. Quy tắc chuyển đổi chung (áp dụng mọi model)

| Quy tắc | Nội dung |
|---|---|
| **Chuỗi** | `NULLIF(LTRIM(RTRIM(col)), '')`. Không dùng `TRIM()` để tương thích SQL Server < 2017. Bắt buộc với `drivers.nationality` vì `driverId = 861` có giá trị `'Argentinian '` (thừa khoảng trắng). |
| **NULL** | Giữ nguyên NULL. **Cấm `COALESCE` trên measure** (`position`, `milliseconds`, `fastest_lap_speed`, …). Chỉ dùng `COALESCE` cho FK về `-1` (mục 5) và cho thuộc tính hiển thị của Unknown member. |
| **Kiểu** | Staging chỉ CAST khi kiểu đích khác DDL `stg`. Ngoài ra giữ đúng kiểu DDL, không mở rộng hay thu hẹp. |
| **Tên cột** | Staging đổi `camelCase` sang `snake_case` tiếng Anh. Tránh từ khóa SQL: `year → season_year`, `round → round_number`, `date → race_date`, `time → race_time / finish_time_text`, `rank → fastest_lap_rank`, `number → driver_number / car_number`. |
| **Lineage** | Staging giữ `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`. Fact giữ `_batch_key` và `_ingested_at_utc` để truy vết và lọc incremental. |
| **Không lọc dòng** | Không model nào được `WHERE` loại dòng nguồn. Mỗi `resultId` phải có đúng 1 dòng trong fact. |

---

## 3. Tầng Staging (`stg_clean`, `materialized='view'`)

Nguồn khai báo trong `sources.yml`: `source('stg', '<table>')`.

### 3.1 `stg_circuits` ← `stg.circuits` (78 dòng)

| Cột nguồn | Cột đích | Kiểu đích | Biến đổi |
|---|---|---|---|
| `circuitId` | `circuit_id` | INT | — |
| `circuitRef` | `circuit_ref` | NVARCHAR(100) | trim |
| `name` | `circuit_name` | NVARCHAR(200) | trim |
| `location` | `locality` | NVARCHAR(100) | trim + NULLIF |
| `country` | `country` | NVARCHAR(100) | trim + NULLIF |
| `lat` | `latitude` | DECIMAL(9,6) | — |
| `lng` | `longitude` | DECIMAL(9,6) | — |
| `alt` | `altitude_m` | INT | Giữ nguyên `0`. Ba circuit có `alt = 0` là placeholder: 35 Korean International Circuit, 79 Miami, 81 Madring. Không đổi thành NULL; ghi chú trong từ điển. |
| `url` | `wiki_url` | NVARCHAR(500) | trim + NULLIF |

### 3.2 `stg_constructors` ← `stg.constructors` (214 dòng)

| Cột nguồn | Cột đích | Kiểu đích | Biến đổi |
|---|---|---|---|
| `constructorId` | `constructor_id` | INT | — |
| `constructorRef` | `constructor_ref` | NVARCHAR(100) | trim |
| `name` | `constructor_name` | NVARCHAR(200) | trim. Giữ đúng tên lịch sử, không gộp đội. |
| `nationality` | `constructor_nationality` | NVARCHAR(100) | trim + NULLIF |
| `url` | `wiki_url` | NVARCHAR(500) | trim + NULLIF |

### 3.3 `stg_drivers` ← `stg.drivers` (879 dòng)

| Cột nguồn | Cột đích | Kiểu đích | Biến đổi |
|---|---|---|---|
| `driverId` | `driver_id` | INT | — |
| `driverRef` | `driver_ref` | NVARCHAR(100) | trim |
| `number` | `permanent_number` | INT | Giữ NULL (816/879 NULL). |
| `code` | `driver_code` | NVARCHAR(10) | trim + NULLIF (771 NULL) |
| `forename` | `forename` | NVARCHAR(100) | trim |
| `surname` | `surname` | NVARCHAR(100) | trim |
| — (dẫn xuất) | `full_name` | NVARCHAR(201) | `CONCAT(LTRIM(RTRIM(forename)), N' ', LTRIM(RTRIM(surname)))` |
| `dob` | `date_of_birth` | DATE | Giữ NULL (14 NULL). |
| `nationality` | `driver_nationality` | NVARCHAR(100) | **trim + NULLIF bắt buộc** (id 861 thừa khoảng trắng; 14 tay đua 864–880 không có quốc tịch nên là NULL) |
| `url` | `wiki_url` | NVARCHAR(500) | trim + NULLIF |

### 3.4 `stg_status` ← `stg.status` (141 dòng)

| Cột nguồn | Cột đích | Kiểu đích | Biến đổi |
|---|---|---|---|
| `statusId` | `status_id` | INT | — |
| `status` | `status_label` | NVARCHAR(100) | trim. Giữ đúng nhãn gốc. |
| — (dẫn xuất) | `outcome_group` | VARCHAR(20) | `CASE WHEN` ở mục 4.3 |
| — (dẫn xuất) | `outcome_category` | VARCHAR(40) | `CASE WHEN` ở mục 4.3 |

### 3.5 `stg_seasons` ← `stg.seasons` (77 dòng)

| Cột nguồn | Cột đích | Kiểu đích | Biến đổi |
|---|---|---|---|
| `year` | `season_year` | INT | — |
| `url` | `season_wiki_url` | NVARCHAR(500) | trim + NULLIF |

Chỉ dùng để kiểm tra độ phủ mùa giải: mọi `stg_races.season_year` phải có trong `stg_seasons` (test `relationships`). Không tạo dim riêng.

### 3.6 `stg_races` ← `stg.races` (1.164 dòng)

| Cột nguồn | Cột đích | Kiểu đích | Biến đổi |
|---|---|---|---|
| `raceId` | `race_id` | INT | — |
| `year` | `season_year` | INT | — |
| `round` | `round_number` | INT | — |
| `circuitId` | `circuit_id` | INT | — |
| `name` | `race_name` | NVARCHAR(200) | trim |
| `date` | `race_date` | DATE | — |
| — (dẫn xuất) | `date_sk` | INT | `CAST(CONVERT(CHAR(8), [date], 112) AS INT)` (ví dụ `20090329`) |
| `time` | `race_start_time_utc` | TIME(0) | Giữ NULL (731 NULL, chủ yếu trước 2005). |
| `url` | `wiki_url` | NVARCHAR(500) | trim + NULLIF |
| `fp1_date`, `fp2_date`, `fp3_date`, `quali_date`, `sprint_date` | `fp1_date`, `fp2_date`, `fp3_date`, `quali_date`, `sprint_date` | DATE | Giữ NULL. Ngoài grain của fact: giữ trong view staging, **không** đưa lên marts. |
| `fp1_time`, `fp2_time`, `fp3_time`, `quali_time`, `sprint_time` | `fp1_time_utc`, `fp2_time_utc`, `fp3_time_utc`, `quali_time_utc`, `sprint_time_utc` | TIME(0) | Giữ NULL. Như trên. |
| — (dẫn xuất) | `has_sprint` | BIT | `CASE WHEN sprint_date IS NOT NULL THEN 1 ELSE 0 END` |

### 3.7 `stg_results` ← `stg.results` (27.568 dòng)

| Cột nguồn | Cột đích | Kiểu đích | Biến đổi |
|---|---|---|---|
| `resultId` | `source_result_id` | INT | — (khóa grain) |
| `raceId` | `race_id` | INT | — |
| `driverId` | `driver_id` | INT | — |
| `constructorId` | `constructor_id` | INT | — |
| `statusId` | `status_id` | INT | — |
| `number` | `car_number` | INT | Giữ NULL |
| `grid` | `grid_position` | INT | Giữ nguyên. `0` = xuất phát từ pit lane hoặc không có vị trí (1.638 dòng). **Không** đổi thành NULL. |
| `position` | `finish_position` | INT | Giữ NULL (11.074 dòng không được xếp hạng). |
| `positionText` | `position_text` | NVARCHAR(10) | trim |
| `positionOrder` | `position_order` | INT | — |
| `points` | `points` | DECIMAL(6,2) | — (không âm, có giá trị lẻ 0.5 hoặc 0.14 do chia điểm) |
| `laps` | `laps_completed` | INT | — |
| `time` | `finish_time_text` | NVARCHAR(50) | trim + NULLIF. Dạng text (`1:34:50.616` hoặc `+5.478`); **không** phải measure. |
| `milliseconds` | `finish_time_ms` | INT | Giữ NULL |
| `fastestLap` | `fastest_lap_number` | INT | Giữ NULL |
| `rank` | `fastest_lap_rank` | INT | Giữ NULL |
| `fastestLapTime` | `fastest_lap_time_text` | NVARCHAR(50) | trim + NULLIF |
| `fastestLapSpeed` | `fastest_lap_speed_kph` | DECIMAL(7,3) | Giữ NULL (toàn bộ 2025/2026 là NULL do giới hạn nguồn) |
| lineage | `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc` | NVARCHAR(260), NVARCHAR(100), VARCHAR(20), DATETIME2(3) | giữ nguyên tên và kiểu |

---

## 4. Phân nhóm trạng thái (`OutcomeGroup`)

### 4.1 Tổng hợp (đã kiểm tra trên dữ liệu)

| `outcome_group` | Số mã status | Số dòng kết quả | Quy tắc |
|---|---:|---:|---|
| `CLASSIFIED` | 35 | 15.839 | `Finished`, `Lapped`, mọi nhãn dạng `+N Lap` / `+N Laps` (33 mã) |
| `DNS` | 2 | 258 | `Did not start`, `Withdrew` |
| `DSQ` | 3 | 162 | `Disqualified`, `Excluded`, `Underweight` |
| `OTHER` | 5 | 1.538 | `Not classified`, `Did not qualify`, `Did not prequalify`, `107% Rule`, `Not restarted`, và **mọi nhãn mới chưa được duyệt** (rơi vào `ELSE`) |
| `RETIREMENT_DNF` | 96 | 9.771 | Danh sách tường minh ở mục 4.2 |
| **Tổng** | **141** | **27.568** | Không còn mã nào rơi vào `ELSE` trên snapshot hiện tại. |

Hai mã `133 '+49 Laps'` và `134 '+38 Laps'` có trong `status.csv` nhưng không có dòng kết quả nào. Vẫn giữ hai mã này trong dim.

Bảng đầy đủ 141 dòng (`statusId`, `status`, `outcome_group`, `outcome_category`, `result_rows`) nằm trong [`status_outcome_mapping.csv`](status_outcome_mapping.csv).

### 4.2 `outcome_category` (chỉ chi tiết hóa `RETIREMENT_DNF`)

| `outcome_category` | Mã | Dòng | Nhãn |
|---|---:|---:|---|
| `MECHANICAL` | 75 | 6.584 | Engine, Gearbox, Transmission, Clutch, Hydraulics, Electrical, Radiator, Suspension, Brakes, Differential, Overheating, Mechanical, Tyre, Driver Seat, Puncture, Driveshaft, Fuel pressure, Water pressure, Wheel, Throttle, Steering, Technical, Electronics, Heat shield fire, Exhaust, Oil leak, Wheel rim, Water leak, Fuel pump, Track rod, Oil pressure, Engine fire, Engine misfire, Tyre puncture, Wheel nut, Pneumatics, Handling, Rear wing, Fire, Wheel bearing, Fuel system, Oil line, Launch control, Fuel, Power loss, Vibrations, Drivetrain, Ignition, Chassis, Battery, Stalled, Halfshaft, Crankshaft, Alternator, Safety belt, Oil pump, Fuel leak, Injection, Distributor, Turbo, CV joint, Water pump, Spark plugs, Fuel pipe, Oil pipe, Axle, Water pipe, Magneto, Supercharger, Power Unit, ERS, Brake duct, Seat, Undertray, Cooling system |
| `ACCIDENT_DAMAGE` | 9 | 2.793 | Accident, Collision, Collision damage, Spun off, Fatal accident, Damage, Debris, Broken wing, Front wing |
| `DRIVER_MEDICAL` | 6 | 65 | Physical, Injured, Injury, Driver unwell, Eye injury, Illness |
| `OTHER_RETIREMENT` | 6 | 329 | Retired, Safety, Safety concerns, Out of fuel, Refuelling, Fuel rig |

Với các nhóm khác, `outcome_category` nhận giá trị cố định: `CLASSIFIED → FINISHED_OR_LAPPED`, `DNS → DID_NOT_START`, `DSQ → DISQUALIFIED`, `OTHER → NOT_QUALIFIED_OR_NOT_CLASSIFIED`. Nhãn chưa duyệt nhận `UNREVIEWED`.

Các trường hợp dễ tranh luận đã quyết định như sau:
- `Front wing` và `Broken wing` xếp vào `ACCIDENT_DAMAGE`, vì thường là hư hỏng do va chạm.
- `Rear wing` xếp vào `MECHANICAL`.
- `Puncture` xếp vào `MECHANICAL`, vì là hỏng lốp.
- `Stalled` xếp vào `MECHANICAL`.
- `Out of fuel` xếp vào `OTHER_RETIREMENT`, vì là vấn đề vận hành hoặc chiến thuật, không phải hỏng xe.

### 4.3 SQL `stg_status.sql` (Trực dùng trực tiếp)

SQL đầy đủ nằm trong [`stg_status_outcome.sql`](stg_status_outcome.sql). File này **sinh tự động** từ cùng bộ nhãn tạo ra CSV, không có placeholder, nên Trực dán nguyên văn thành `dbt/models/staging/stg_status.sql`. Cấu trúc:

1. CTE `src`: `statusId → status_id`, `NULLIF(LTRIM(RTRIM(status)), N'') → status_label`, giữ `_batch_key`, `_ingested_at_utc`.
2. CTE `classified`: một `CASE` duy nhất gán `outcome_category`. Nhãn `Finished`, `Lapped`, `LIKE N'+[0-9]% Lap'`, `LIKE N'+[0-9]% Laps'` → `FINISHED_OR_LAPPED`; tiếp theo là các danh sách `IN (...)` tường minh của mục 4.1–4.2; nhãn không khớp → `UNREVIEWED`.
3. `SELECT` cuối suy ra `outcome_group` từ `outcome_category`, nên hai cột **không thể lệch nhau**. `UNREVIEWED` → `OTHER`.

Đã chạy file này trên SQL Server 2022 (thay `{{ source('stg', 'status') }}` bằng `stg.status`): 141/141 dòng khớp `status_outcome_mapping.csv`, 0 sai lệch (xem [`loc_phase2_validation_run.md`](../evidence/loc_phase2_validation_run.md)).

**Phương án thay thế (nếu nhóm đồng ý):** đưa `status_outcome_mapping.csv` thành dbt seed rồi `LEFT JOIN` theo `status_id`. Kết quả giống hệt, nhưng nhãn mới sẽ không được phân loại tự động theo mẫu `+N Laps`.

### 4.4 Nguyên tắc nghiệp vụ bắt buộc

1. **Không gộp DNS và DSQ vào DNF.** Ba nhóm này phải tách riêng.
2. **`finish_position IS NOT NULL` là tiêu chí xếp hạng chính thức.** `outcome_group` chỉ giải thích lý do kết thúc. Trên dữ liệu thực tế:
   - **679 dòng `RETIREMENT_DNF` vẫn có `finish_position`.** Đây là xe bỏ cuộc sau khi đã chạy trên 90% cự ly nên vẫn được xếp hạng. Trường hợp này hợp lệ, không phải lỗi.
   - **28 dòng `CLASSIFIED` (`+N Laps`) có `finish_position` NULL.** Trong đó 26 dòng có `positionText = 'N'` (không đủ cự ly để xếp hạng) và 2 dòng thuộc race 71 (`resultId` 1149, 1152) có `positionText` dạng số nhưng `position` NULL. Đây là hiện trạng của nguồn: ghi nhận là quality finding và không sửa.
3. Mọi KPI "classified" hay "non-classified rate" phải dựa trên `finish_position`, không dựa trên `outcome_group`.

---

## 5. Tầng Marts (`dw`)

### 5.1 Dimensions (`materialized='table'`, mỗi dim gồm dòng nguồn `UNION ALL` dòng `-1`)

| Model → bảng | Nguồn | SK | Natural key | Thuộc tính |
|---|---|---|---|---|
| `dim_date` → `dw.DimDate` | Sinh lịch liên tục từ `1950-01-01` đến `2026-12-31`, tức từ ngày 1/1 của năm nhỏ nhất đến 31/12 của năm lớn nhất trong `stg_races`. | `date_sk` = `YYYYMMDD` | `full_date` | `day_of_month`, `month_number`, `month_name`, `month_short`, `quarter_number`, `quarter_label`, `year_number`, `day_of_week_number` (Mon = 1), `day_name`, `is_weekend`, `year_month` (`YYYY-MM`), `is_race_day` (ngày có trong `stg_races.race_date`) |
| `dim_race` → `dw.DimRace` | `stg_races` | `race_sk = race_id` | `source_race_id` | `season_year`, `round_number`, `race_name`, `race_date`, `race_label` (`CONCAT(season_year,' R',FORMAT(round_number,'00'),' ',race_name)`), `has_sprint`, `wiki_url` |
| `dim_circuit` → `dw.DimCircuit` | `stg_circuits` | `circuit_sk = circuit_id` | `source_circuit_id` | `circuit_ref`, `circuit_name`, `locality`, `country`, `latitude`, `longitude`, `altitude_m` |
| `dim_driver` → `dw.DimDriver` | `stg_drivers` | `driver_sk = driver_id` | `source_driver_id` | `driver_ref`, `full_name`, `forename`, `surname`, `driver_code`, `permanent_number`, `driver_nationality`, `date_of_birth` |
| `dim_constructor` → `dw.DimConstructor` | `stg_constructors` | `constructor_sk = constructor_id` | `source_constructor_id` | `constructor_ref`, `constructor_name`, `constructor_nationality` |
| `dim_status` → `dw.DimStatus` | `stg_status` | `status_sk = status_id` | `source_status_id` | `status_label`, `outcome_group`, `outcome_category` |

Lưu ý khi viết `dim_date` trên SQL Server:
- **Không dùng `DATENAME` hoặc `DATEPART(weekday)`**, vì kết quả phụ thuộc `SET LANGUAGE` và `SET DATEFIRST`.
- Tính thứ trong tuần bằng `(DATEDIFF(day, '19000101', full_date) % 7) + 1`. Ngày 1900-01-01 là thứ Hai, nên công thức cho Mon = 1 … Sun = 7.
- Tên tháng và tên thứ viết bằng `CASE` tiếng Anh cố định.
- Sinh dãy ngày bằng CTE số (tally) cross join, không dùng recursive CTE vì sẽ chạm `MAXRECURSION`.

### 5.2 Fact `fact_race_result` → `dw.FactRaceResult`

Config: `materialized='incremental'`, `incremental_strategy='delete+insert'`, `unique_key='source_result_id'`, `alias='FactRaceResult'`.

| Cột đích | Kiểu | Nguồn / công thức | Loại |
|---|---|---|---|
| `source_result_id` | INT NOT NULL | `r.source_result_id` | Khóa grain (degenerate) |
| `date_sk` | INT NOT NULL | `COALESCE(d.date_sk, -1)`; join `stg_races.date_sk` với `dim_date` | FK |
| `race_sk` | INT NOT NULL | `COALESCE(ra.race_sk, -1)` | FK |
| `circuit_sk` | INT NOT NULL | `COALESCE(ci.circuit_sk, -1)`, qua `stg_races.circuit_id` | FK |
| `driver_sk` | INT NOT NULL | `COALESCE(dr.driver_sk, -1)` | FK |
| `constructor_sk` | INT NOT NULL | `COALESCE(co.constructor_sk, -1)` | FK |
| `status_sk` | INT NOT NULL | `COALESCE(st.status_sk, -1)` | FK |
| `source_race_id`, `source_driver_id`, `source_constructor_id`, `source_status_id` | INT | giữ khóa nguồn | Lineage / đối soát |
| `car_number` | INT NULL | `r.car_number` | Thuộc tính |
| `position_text` | NVARCHAR(10) | `r.position_text` | Thuộc tính (D6) |
| `result_outcome_code` | VARCHAR(20) | mục 5.3 | Thuộc tính (D6) |
| `finish_time_text` | NVARCHAR(50) NULL | `r.finish_time_text` | Thuộc tính, không tổng hợp |
| `points` | DECIMAL(6,2) | `r.points` | Additive |
| `laps_completed` | INT | `r.laps_completed` | Additive (theo dòng) |
| `result_count` | INT | `1` | Additive |
| `grid_position` | INT | `r.grid_position` | Non-additive |
| `finish_position` | INT NULL | `r.finish_position` | Non-additive |
| `position_order` | INT | `r.position_order` | Non-additive |
| `places_gained` | INT NULL | `CASE WHEN grid_position > 0 AND finish_position > 0 THEN grid_position - finish_position END` | Non-additive (trung bình hoặc trung vị) |
| `is_win` | BIT | `CASE WHEN position_order = 1 THEN 1 ELSE 0 END` | Flag additive |
| `is_podium` | BIT | `CASE WHEN finish_position BETWEEN 1 AND 3 THEN 1 ELSE 0 END` | Flag additive |
| `is_classified` | BIT | `CASE WHEN finish_position IS NOT NULL THEN 1 ELSE 0 END` | Flag additive |
| `is_points_finish` | BIT | `CASE WHEN points > 0 THEN 1 ELSE 0 END` | Flag additive |
| `is_valid_grid_start` | BIT | `CASE WHEN grid_position > 0 THEN 1 ELSE 0 END` | Flag (mẫu số cho places gained) |
| `finish_time_ms` | INT NULL | `r.finish_time_ms` | Non-additive, không bao giờ SUM |
| `fastest_lap_number`, `fastest_lap_rank` | INT NULL | giữ | Thuộc tính |
| `fastest_lap_time_text` | NVARCHAR(50) NULL | giữ | Thuộc tính |
| `fastest_lap_speed_kph` | DECIMAL(7,3) NULL | giữ | Non-additive |
| `_batch_key`, `_ingested_at_utc` | — | từ `stg_results` | Lineage / incremental |

Bộ lọc incremental:

```sql
{% if is_incremental() %}
where r._ingested_at_utc > (select coalesce(max(_ingested_at_utc), '1900-01-01') from {{ this }})
{% endif %}
```

Mọi phép join đều là **`LEFT JOIN`**. Không dùng `INNER JOIN` vì sẽ làm mất dòng fact.

### 5.3 `result_outcome_code` (từ `positionText`)

| `positionText` | `result_outcome_code` | Ý nghĩa | Số dòng |
|---|---|---|---:|
| số (`1`, `2`, …) | `CLASSIFIED` | Được xếp hạng | 16.496 |
| `R` | `RETIRED` | Bỏ cuộc | 9.002 |
| `D` | `DISQUALIFIED` | Bị loại | 157 |
| `E` | `EXCLUDED` | Bị loại khỏi sự kiện | 9 |
| `W` | `WITHDRAWN` | Rút lui hoặc không xuất phát | 346 |
| `F` | `FAILED_TO_QUALIFY` | Không vượt qua vòng loại hoặc tiền vòng loại | 1.368 |
| `N` | `NOT_CLASSIFIED` | Không đủ cự ly để xếp hạng | 190 |
| khác | `UNKNOWN` | Mã mới, cần duyệt | 0 |

```sql
case
    when position_text not like '%[^0-9]%' and position_text <> '' then 'CLASSIFIED'
    when position_text = 'R' then 'RETIRED'
    when position_text = 'D' then 'DISQUALIFIED'
    when position_text = 'E' then 'EXCLUDED'
    when position_text = 'W' then 'WITHDRAWN'
    when position_text = 'F' then 'FAILED_TO_QUALIFY'
    when position_text = 'N' then 'NOT_CLASSIFIED'
    else 'UNKNOWN'
end as result_outcome_code
```

Có 16.496 dòng `positionText` dạng số nhưng chỉ có 16.494 dòng `position` khác NULL. Hai dòng chênh lệch là `resultId` 1149 và 1152 (mục 4.4). KPI "classified" vẫn dùng `finish_position`.

---

## 6. Unknown member (`-1`), dành cho Dũng và Trực

Mỗi dim `UNION ALL` thêm đúng 1 dòng có các giá trị dưới đây. Thuộc tính số và ngày của dòng này để NULL; thuộc tính chuỗi dùng nhãn `Unknown`.

| Bảng | Giá trị dòng `-1` |
|---|---|
| `DimDate` | `date_sk = -1`, `full_date = NULL`, `year_number = NULL`, `month_name = 'Unknown'`, `day_name = 'Unknown'`, `quarter_label = 'Unknown'`, `year_month = 'Unknown'`, `is_weekend = NULL` |
| `DimRace` | `race_sk = -1`, `source_race_id = -1`, `race_name = 'Unknown Race'`, `race_label = 'Unknown Race'`, `season_year = NULL`, `round_number = NULL`, `race_date = NULL`, `has_sprint = NULL` |
| `DimCircuit` | `circuit_sk = -1`, `source_circuit_id = -1`, `circuit_ref = 'unknown'`, `circuit_name = 'Unknown Circuit'`, `locality = 'Unknown'`, `country = 'Unknown'`, toạ độ và độ cao NULL |
| `DimDriver` | `driver_sk = -1`, `source_driver_id = -1`, `driver_ref = 'unknown'`, `full_name = 'Unknown Driver'`, `forename = 'Unknown'`, `surname = 'Driver'`, `driver_code = NULL`, `permanent_number = NULL`, `driver_nationality = 'Unknown'`, `date_of_birth = NULL` |
| `DimConstructor` | `constructor_sk = -1`, `source_constructor_id = -1`, `constructor_ref = 'unknown'`, `constructor_name = 'Unknown Constructor'`, `constructor_nationality = 'Unknown'` |
| `DimStatus` | `status_sk = -1`, `source_status_id = -1`, `status_label = 'Unknown'`, `outcome_group = 'OTHER'`, `outcome_category = 'UNREVIEWED'` |

So với kế hoạch của Dũng có 2 điểm khác:
- `DimDriver.date_of_birth` để **NULL** thay vì `'1900-01-01'`. Ngày giả sẽ làm sai phép tính tuổi tay đua.
- `driver_code` để NULL thay vì `'UNK'`, để không trùng với một mã tay đua thật có thể xuất hiện sau này.

Với dữ liệu hiện tại, **kỳ vọng 0 dòng fact trỏ về `-1`**, vì Stage đã kiểm tra khóa ngoại ở Phase 1. Nếu có dòng trỏ về `-1` thì đó là orphan cần điều tra, không được dùng `-1` để che lỗi.

---

## 7. Danh sách test cho Phúc (`schema.yml`)

| Model.cột | Test |
|---|---|
| `dim_status.outcome_group` | `not_null`, `accepted_values: ['CLASSIFIED','DNS','DSQ','RETIREMENT_DNF','OTHER']` |
| `dim_status.outcome_category` | `not_null`, `accepted_values: ['FINISHED_OR_LAPPED','DID_NOT_START','DISQUALIFIED','NOT_QUALIFIED_OR_NOT_CLASSIFIED','MECHANICAL','ACCIDENT_DAMAGE','DRIVER_MEDICAL','OTHER_RETIREMENT','UNREVIEWED']` |
| `dim_status` | Singular test: `outcome_category = 'UNREVIEWED' AND status_sk <> -1` trả 0 dòng (severity `warn`). Test này phát hiện nhãn mới chưa duyệt. |
| `fact_race_result.result_outcome_code` | `accepted_values: ['CLASSIFIED','RETIRED','DISQUALIFIED','EXCLUDED','WITHDRAWN','FAILED_TO_QUALIFY','NOT_CLASSIFIED','UNKNOWN']` |
| `fact_race_result.places_gained` | Singular test: `places_gained IS NOT NULL AND (grid_position <= 0 OR finish_position IS NULL)` trả 0 dòng |
| `fact_race_result.*_sk` | `not_null`, `relationships` tới dim tương ứng (6 FK, gồm cả `date_sk` và `circuit_sk` mà mẫu trong kế hoạch của Phúc còn thiếu) |
| `fact_race_result` | Singular test: số dòng có `*_sk = -1` bằng 0 (severity `warn`) |
| Mọi dim `*_sk` và `source_*_id` | `unique`, `not_null` |
| `source('stg','races').year` | `relationships` → `source('stg','seasons').year`. Đặt trên source vì `--select +fact_race_result` không build `stg_seasons`. |

Số liệu kỳ vọng để test đối soát nằm trong [`loc_phase2_expected_baseline.json`](../evidence/loc_phase2_expected_baseline.json).

---

## 8. Quy tắc điểm số và measure F1 (nhiệm vụ 3)

### 8.1 Thang điểm theo kỷ nguyên (đối chiếu với dữ liệu `results.csv`)

| Giai đoạn | Thang điểm top-N | Đặc điểm thấy trong dữ liệu |
|---|---|---|
| 1950–1959 | 8-6-4-3-2, **+1 điểm fastest lap** | Người thắng có tối đa 9 điểm. Có điểm lẻ (ví dụ 6.14, 6.5) do chia điểm khi nhiều tay đua chung một xe (shared drive). |
| 1960 | 8-6-4-3-2-1 | Không có điểm fastest lap. |
| 1961–1990 | 9-6-4-3-2-1 | Có luật bỏ kết quả kém (dropped scores) ở nhiều mùa. Nửa điểm: 1975 Tây Ban Nha và Áo, 1984 Monaco (4.5 điểm cho người thắng). |
| 1991–2002 | 10-6-4-3-2-1 | Nửa điểm: 1991 Úc (5 điểm cho người thắng). |
| 2003–2009 | 10-8-6-5-4-3-2-1 | Nửa điểm: 2009 Malaysia. |
| 2010–nay | 25-18-15-12-10-8-6-4-2-1 | **2014 Abu Dhabi tính điểm gấp đôi (50 điểm)**. 2019–2024 có +1 điểm fastest lap (tối đa 26). 2021 Bỉ chia nửa điểm (12.5). Từ 2025 bỏ điểm fastest lap (dữ liệu: tối đa 25). |

Mục 3 kế hoạch cá nhân ghi gộp "1991–2009: 10 điểm". Thực tế 2003–2009 dùng thang 10-8-6-5-4-3-2-1, nên bảng trên đã tách riêng hai giai đoạn này.

`results.points` chỉ là **điểm Grand Prix**, không gồm điểm sprint (nằm ở `sprint_results`, ngoài grain). Vì vậy tổng điểm từ 2021 trở đi **không bằng** điểm vô địch chính thức. Báo cáo phải ghi chú điều này.

### 8.2 Quy tắc measure

| Measure | Quy tắc |
|---|---|
| `points` | SUM được trong cùng mùa hoặc kỷ nguyên. So sánh giữa các kỷ nguyên phải chuẩn hoá (ví dụ % so với điểm tối đa của mùa) hoặc dùng tỉ lệ thắng hoặc podium. |
| `is_win` | Dựa vào `position_order = 1`. Tổng là **1.167 dòng thắng trên 1.164 race**, vì race 780, 784 và 828 (thập niên 1950) có 2 dòng `positionOrder = 1` do shared drive. Đếm "số race thắng" của đội phải dùng `COUNT(DISTINCT race_sk)`. |
| `places_gained` | `grid_position - finish_position`, **chỉ khi `grid_position > 0` và `finish_position` khác NULL**. Có 16.434 dòng hợp lệ, trung bình 2,94. Dương nghĩa là lên hạng. Luôn hiển thị kèm `n`. |
| `finish_position`, `grid_position` | Không SUM. Chỉ AVG hoặc MEDIAN trên tập hợp lệ. |
| `finish_time_ms`, `fastest_lap_speed_kph` | Không SUM. Chỉ so sánh trong cùng race. |
| Tỉ lệ | Tính lại từ tử số và mẫu số trong ngữ cảnh lọc. Không trung bình các tỉ lệ đã tính sẵn. |

---

## 9. Phát hiện chất lượng dữ liệu (không sửa, chỉ ghi nhận)

| # | Phát hiện | Số dòng | Xử lý |
|---|---|---:|---|
| Q1 | Race 452: `position` ≠ `positionOrder` cho 13 dòng (vị trí 3–15 có `positionOrder` 2–14) | 13 | Giữ nguyên. Wins dựa vào `positionOrder`, podium dựa vào `position`. |
| Q2 | Shared drive: race 780, 784, 828 có 2 người thắng | 3 race | Giữ. Ghi chú trong KPI wins. |
| Q3 | Nhóm `CLASSIFIED` nhưng `position` NULL | 28 | Hợp lệ (bị đánh `N`) hoặc là lỗi nguồn (race 71). Ghi nhận. |
| Q4 | Nhóm `RETIREMENT_DNF` nhưng vẫn được xếp hạng | 679 | Hợp lệ (luật 90% cự ly). |
| Q5 | `positionText = 'W'` mang status cơ khí hoặc tai nạn | 108 | Dùng `result_outcome_code` (D6). |
| Q6 | `drivers.nationality` thừa khoảng trắng (id 861) hoặc NULL (14 tay đua 864–880) | 15 | TRIM. NULL giữ nguyên NULL. |
| Q7 | `circuits.alt = 0` là placeholder (id 35, 79, 81) | 3 | Giữ `0` và ghi chú. Không dùng làm measure độ cao. |
| Q8 | Status 133 và 134 không có dòng kết quả | 2 | Giữ trong dim. |

---

## 10. Đối chiếu với script DW của Dũng (nhánh `origin/Dung`, commit `46e72ed`)

Dũng đã đẩy `sqlserver/dw/02_seed_unknown_members.sql` và `03_apply_columnstore_indexes.sql`. Hai script này **tự `CREATE TABLE` các bảng `dw.*` với tên cột PascalCase**, còn đặc tả này (D1) dùng `snake_case`. Nhóm phải chốt **một** quy ước trước khi Trực viết marts. Nếu không, `dbt run` sẽ gặp hai lỗi:

1. Dim (`materialized='table'`): dbt DROP rồi CREATE lại bảng. Bảng và dòng `-1` do Dũng seed **bị xóa** (D3).
2. Fact (`incremental`): nếu `dw.FactRaceResult` đã được tạo trước bằng script của Dũng, dbt coi đó là lần chạy incremental và `INSERT` cột `snake_case` vào bảng PascalCase. Lệnh này **lỗi ngay**.

**Đề xuất của Lộc:** dbt sở hữu DDL của `dw` (D1, D3). Script 02 của Dũng chuyển thành kiểm tra dòng `-1` (đã có sẵn trong `loc_semantic_validation.sql` check 40). Script 03 chỉ cần kiểm tra CCI, vì dbt-sqlserver tự tạo CCI. Nếu nhóm chọn PascalCase, Trực đặt alias cột theo bảng dưới, và `loc_semantic_validation.sql` đổi tên theo đúng bảng này.

| Bảng | Đặc tả Lộc (`snake_case`) | Script Dũng | Ghi chú |
|---|---|---|---|
| Fact | `source_result_id`, `date_sk`, `race_sk`, `circuit_sk`, `driver_sk`, `constructor_sk`, `status_sk` | `SourceResultId`, `DateSK`, `RaceSK`, `CircuitSK`, `DriverSK`, `ConstructorSK`, `StatusSK` | Khớp nghĩa |
| Fact | `points`, `laps_completed`, `grid_position`, `finish_position`, `position_order`, `position_text`, `places_gained` | `Points`, `Laps`, `GridPosition`, `FinishPosition`, `PositionOrder`, `PositionText`, `PlacesGained` | Khớp nghĩa |
| Fact | `finish_time_ms`, `fastest_lap_number`, `fastest_lap_time_text`, `fastest_lap_speed_kph` | `Milliseconds`, `FastestLap`, `FastestLapTime`, `FastestLapSpeed` | Khớp nghĩa |
| Fact | `is_win`, `is_podium`, `is_classified` (BIT) | `IsWin`, `IsPodium`, `IsClassified` (TINYINT) | Khác kiểu; SUM cần CAST nếu dùng BIT |
| Fact | `source_race_id`, `source_driver_id`, `source_constructor_id`, `source_status_id`, `car_number`, `result_outcome_code`, `finish_time_text`, `result_count`, `is_points_finish`, `is_valid_grid_start`, `fastest_lap_rank`, `_batch_key` | *không có* | Script Dũng thiếu 12 cột |
| Fact | *không có* | `RaceResultSK INT IDENTITY` (PK nonclustered) | Grain đã có `source_result_id`. IDENTITY làm SK thay đổi mỗi lần full rebuild (D2) |
| DimDate | `date_sk`, `full_date`, `day_of_month`, `month_number`, `month_name`, `quarter_number`, `year_number`, `day_name` | `DateSK`, `FullDate`, `DayNumber`, `MonthNumber`, `MonthName`, `QuarterNumber`, `CalendarYear`, `WeekdayName` | Dũng thiếu `month_short`, `quarter_label`, `year_month`, `day_of_week_number`, `is_weekend`, `is_race_day` |
| DimRace | `race_sk`, `source_race_id`, `season_year`, `round_number`, `race_name`, `race_date`, `wiki_url` | `RaceSK`, `SourceRaceId`, `SeasonYear`, `RoundNumber`, `RaceName`, `RaceDate`, `Url` | Dũng thiếu `race_label`, `has_sprint`; thừa `CircuitId` (fact đã có `circuit_sk`) |
| DimCircuit | `circuit_sk` … `altitude_m` | `CircuitSK` … `Altitude`, `Url` | Khớp; `Url` có thể thêm |
| DimDriver | `permanent_number`, `driver_nationality`, `full_name` NVARCHAR(201) | `DriverNumber`, `Nationality`, `FullName` NVARCHAR(200) | 200 vẫn đủ: tên dài nhất hiện tại là 29 ký tự |
| DimConstructor | `constructor_nationality` | `Nationality` | Khớp nghĩa |
| DimStatus | `status_label`, `outcome_group` VARCHAR(20), `outcome_category` | `SourceStatusLabel`, `OutcomeGroup` NVARCHAR(50) | Dũng thiếu `outcome_category` |

Khác biệt ở dòng Unknown `-1`:
- Dũng dùng ngày giả `1900-01-01` cho `DimDate.FullDate`, `DimRace.RaceDate`, `DimDriver.DateOfBirth` và `DriverCode = 'UNK'`. Đặc tả này dùng NULL (lý do ở mục 6).
- Nếu giữ `1900-01-01` thì `DimDate` có ngày `1900-01-01` nằm ngoài lịch 1950–2026, và slicer năm trên Power BI sẽ hiện năm 1900.

---

## 11. Change log

| Ngày | Phiên bản | Nội dung |
|---|---|---|
| 2026-11-06 | P2-v1.2 | Rà soát theo kế hoạch cá nhân. (1) Mục 4.3: thay đoạn `CASE WHEN` có placeholder bằng file sinh tự động [`stg_status_outcome.sql`](stg_status_outcome.sql), đã chạy trên SQL Server 2022 và khớp 141/141 dòng CSV. (2) Mục 3.6: bổ sung tên và kiểu cho 10 cột `fp1_*` … `sprint_*`; mục 3.7: ghi rõ kiểu các cột lineage. (3) Script sinh: sửa kiểm tra chồng lấn nhãn (trước chỉ kiểm tra giao của cả 4 tập, nay kiểm tra từng cặp); thêm kiểm tra thang điểm kỷ nguyên. (4) `loc_semantic_validation.sql` tăng từ 30 lên 43 check: đối soát theo khóa hai chiều, so từng giá trị fact với stage, kiểm tra cột dẫn xuất trên từng dòng, cặp group/category, dòng `-1`, SK deterministic, thang điểm kỷ nguyên. Đã thử 8 lỗi cố ý và script bắt được cả 8. (5) Thêm mục 10 đối chiếu với script của Dũng. (6) Thêm `tests/test_phase2_mapping.py`. |
| 2026-11-06 | P2-v1.1 | Thêm script đối soát `sqlserver/dw/loc_semantic_validation.sql` (nhiệm vụ 5). Lộc đã chạy thử đặc tả này trên SQL Server 2022 local và rút ra 3 lưu ý bàn giao. (1) Cho Trực: image Mage hiện có `dbt-fabric 1.8.9`, bản này làm `dbt-sqlserver 1.8.4` lỗi `ImportError`; cần ghim `dbt-fabric==1.8.7`. (2) Cho Trực: dbt-sqlserver tự tạo clustered columnstore index cho model dạng table/incremental (`as_columnstore` mặc định `true`), Dũng cần biết để tránh tạo trùng. (3) Cho Phúc: test mùa giải ở mục 7 nên đặt trên source (`stg.races.year → stg.seasons.year`), vì `--select +fact_race_result` không build `stg_seasons`. |
| 2026-11-06 | P2-v1.0 | Bản đầu: mapping 7 bảng, `OutcomeGroup` 141 mã, quy tắc measure và kỷ nguyên điểm, Unknown member, danh sách test, các quyết định D1–D6. |
