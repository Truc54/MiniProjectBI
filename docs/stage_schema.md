# Đặc tả Schema Staging (SQL Server) - Phase 1

**Tác giả:** Dũng (Phụ trách SQL Server & Staging)  
**Phiên bản:** 1.0 (Chốt ngày 21/10/2026 với Phúc và Lộc)  
**Mục tiêu:** Cung cấp table contract chuẩn xác giữa nguồn Kaggle CSV, Mage pipeline và SQL Server, phục vụ Seminar 1.

---

## 1. Tổng quan kiến trúc Schema

Cơ sở dữ liệu dự án trên SQL Server (`F1_BI`) được phân tách thành 3 schemas logic:
* `stg` (Staging): Chứa dữ liệu thô được nạp từ các file CSV của Kaggle sau khi qua bước làm sạch sơ bộ (xử lý `\N` -> NULL). Cấu trúc bảng bám sát nguồn (source-aligned), giữ nguyên natural key và tên cột gốc.
* `ctl` (Control & Audit): Quản lý metadata, trạng thái chạy của pipeline (runs), thông tin từng đợt nạp (batches), số dòng xử lý và lịch sử lỗi phục vụ rerun / audit.
* `dw` (Data Warehouse): Schema đích cho mô hình Dimensional (Fact/Dimension), sẽ được triển khai và nạp bằng dbt ở Phase 2.

---

## 2. Quy ước Interface chốt với Mage ETL (Lộc)

Để pipeline của Lộc có thể nạp dữ liệu độc lập và truy vết chính xác, các bảng thuộc schema `stg` tuân thủ các quy tắc sau:

### 2.1. Tên bảng và tên cột
* **Tên bảng:** Tương ứng 1-1 với file nguồn (ví dụ: `circuits.csv` -> `stg.circuits`).
* **Cột nghiệp vụ:** Giữ nguyên 100% tên cột từ file CSV (camelCase như `circuitId`, `driverRef`, `fastestLapSpeed`).
* **Cột kỹ thuật (Audit / Lineage Metadata):** Được đặt tiền tố `_` để tách biệt hoàn toàn khỏi dữ liệu nguồn:

| Cột kỹ thuật | Kiểu dữ liệu | Nullable | Mô tả & Quy ước |
|---|---|:---:|---|
| `_source_file` | `NVARCHAR(260)` | YES | Tên file nguồn (ví dụ: `'results.csv'`) |
| `_batch_key` | `NVARCHAR(100)` | YES | Mã định danh batch (ví dụ: `'full_20261021'`, `'year_2024'`) |
| `_load_mode` | `VARCHAR(20)` | YES | Chế độ nạp: `'full'` hoặc `'incremental'` |
| `_ingested_at_utc` | `DATETIME2(3)` | NO | Mốc thời gian nạp vào SQL Server (mặc định `SYSUTCDATETIME()`) |

### 2.2. Xử lý giá trị thiếu (Missing Values)
* Ký hiệu `\N` từ file CSV được Mage chuyển thành `NULL` của SQL Server.
* Tuyệt đối không thay thế `NULL` bằng `0` hoặc chuỗi rỗng `""` vì sẽ làm sai lệch các chỉ số thống kê (như vị trí kết thúc cuộc đua, thời gian hoàn thành lap, điểm số).
* Các cột không bắt buộc trong lịch sử F1 (như số xe thời kỳ trước 2014, mã 3 chữ số, ngày sinh của một số tay đua cổ điển, vòng chạy nhanh nhất, tốc độ) đều cho phép `NULL`.

---

## 3. Chi tiết 7 bảng Staging lõi (`stg.*`)

### 3.1. `stg.circuits` (circuits.csv - 78 dòng)
Grain: Một dòng cho mỗi trường đua.
* `circuitId` (`INT`, NOT NULL) - **Primary Key**
* `circuitRef` (`NVARCHAR(100)`, NOT NULL)
* `name` (`NVARCHAR(200)`, NOT NULL)
* `location` (`NVARCHAR(100)`, NULL)
* `country` (`NVARCHAR(100)`, NULL)
* `lat` (`DECIMAL(9, 6)`, NULL) - Vĩ độ địa lý
* `lng` (`DECIMAL(9, 6)`, NULL) - Kinh độ địa lý
* `alt` (`INT`, NULL) - Độ cao so với mực nước biển (mét)
* `url` (`NVARCHAR(500)`, NULL)
* Các cột lineage: `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`

### 3.2. `stg.constructors` (constructors.csv - 214 dòng)
Grain: Một dòng cho mỗi đội đua (nhà sản xuất xe).
* `constructorId` (`INT`, NOT NULL) - **Primary Key**
* `constructorRef` (`NVARCHAR(100)`, NOT NULL)
* `name` (`NVARCHAR(200)`, NOT NULL)
* `nationality` (`NVARCHAR(100)`, NULL)
* `url` (`NVARCHAR(500)`, NULL)
* Các cột lineage: `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`

### 3.3. `stg.drivers` (drivers.csv - 879 dòng)
Grain: Một dòng cho mỗi tay đua F1.
* `driverId` (`INT`, NOT NULL) - **Primary Key**
* `driverRef` (`NVARCHAR(100)`, NOT NULL)
* `number` (`INT`, NULL) - Số xe cố định (816 dòng `NULL` ở các thời kỳ cũ)
* `code` (`NVARCHAR(10)`, NULL) - Mã 3 chữ cái viết tắt (ví dụ `'HAM'`, `'VER'`; 771 dòng `NULL`)
* `forename` (`NVARCHAR(100)`, NOT NULL)
* `surname` (`NVARCHAR(100)`, NOT NULL)
* `dob` (`DATE`, NULL) - Ngày sinh (14 dòng cổ điển `NULL`)
* `nationality` (`NVARCHAR(100)`, NULL)
* `url` (`NVARCHAR(500)`, NULL)
* Các cột lineage: `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`

### 3.4. `stg.status` (status.csv - 141 dòng)
Grain: Một dòng cho mỗi mã trạng thái kết thúc chặng đua.
* `statusId` (`INT`, NOT NULL) - **Primary Key**
* `status` (`NVARCHAR(100)`, NOT NULL) - Mô tả (ví dụ: Finished, Disqualified, Collision, Engine)
* Các cột lineage: `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`

### 3.5. `stg.seasons` (seasons.csv - 77 dòng)
Grain: Một dòng cho mỗi mùa giải từ 1950 đến 2026.
* `year` (`INT`, NOT NULL) - **Primary Key**
* `url` (`NVARCHAR(500)`, NULL)
* Các cột lineage: `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`

### 3.6. `stg.races` (races.csv - 1,164 dòng)
Grain: Một dòng cho mỗi sự kiện Grand Prix.
* `raceId` (`INT`, NOT NULL) - **Primary Key**
* `year` (`INT`, NOT NULL) - Khóa tham chiếu `seasons.year`
* `round` (`INT`, NOT NULL) - Chặng đua thứ mấy trong mùa giải
* `circuitId` (`INT`, NOT NULL) - Khóa tham chiếu `circuits.circuitId`
* `name` (`NVARCHAR(200)`, NOT NULL)
* `date` (`DATE`, NOT NULL) - Ngày diễn ra chặng đua chính thức
* `time` (`TIME(0)`, NULL) - Giờ xuất phát (UTC)
* `url` (`NVARCHAR(500)`, NULL)
* `fp1_date` (`DATE`, NULL), `fp1_time` (`TIME(0)`, NULL)
* `fp2_date` (`DATE`, NULL), `fp2_time` (`TIME(0)`, NULL)
* `fp3_date` (`DATE`, NULL), `fp3_time` (`TIME(0)`, NULL)
* `quali_date` (`DATE`, NULL), `quali_time` (`TIME(0)`, NULL)
* `sprint_date` (`DATE`, NULL), `sprint_time` (`TIME(0)`, NULL)
* Các cột lineage: `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`
* **Indexes:** `IX_stg_races_year`, `IX_stg_races_circuitId`

### 3.7. `stg.results` (results.csv - 27,568 dòng)
Grain: Kết quả phân hạng của 1 tay đua trong 1 chặng đua (bảng sự kiện trung tâm).
* `resultId` (`INT`, NOT NULL) - **Primary Key**
* `raceId` (`INT`, NOT NULL) - Tham chiếu `races.raceId`
* `driverId` (`INT`, NOT NULL) - Tham chiếu `drivers.driverId`
* `constructorId` (`INT`, NOT NULL) - Tham chiếu `constructors.constructorId`
* `number` (`INT`, NULL) - Số xe trong chặng
* `grid` (`INT`, NOT NULL) - Vị trí xuất phát
* `position` (`INT`, NULL) - Vị trí về đích chính thức (NULL nếu bỏ cuộc DNF/DSQ/DNS)
* `positionText` (`NVARCHAR(10)`, NOT NULL) - Ký tự hiển thị ('1', '2', 'R', 'D', 'W')
* `positionOrder` (`INT`, NOT NULL) - Thứ tự sắp xếp vị trí
* `points` (`DECIMAL(6, 2)`, NOT NULL) - Điểm số đạt được
* `laps` (`INT`, NOT NULL) - Số vòng đua hoàn thành
* `time` (`NVARCHAR(50)`, NULL) - Thời gian về đích hoặc khoảng cách (+5.478s)
* `milliseconds` (`INT`, NULL) - Tổng thời gian chạy (mili-giây)
* `fastestLap` (`INT`, NULL) - Vòng đua đạt tốc độ nhanh nhất
* `rank` (`INT`, NULL) - Xếp hạng vòng chạy nhanh nhất trong chặng
* `fastestLapTime` (`NVARCHAR(50)`, NULL) - Thời gian vòng nhanh nhất (ví dụ: '1:27.452')
* `fastestLapSpeed` (`DECIMAL(7, 3)`, NULL) - Vận tốc vòng nhanh nhất (km/h)
* `statusId` (`INT`, NOT NULL) - Tham chiếu `status.statusId`
* Các cột lineage: `_source_file`, `_batch_key`, `_load_mode`, `_ingested_at_utc`
* **Indexes:** `IX_stg_results_raceId`, `IX_stg_results_driverId`, `IX_stg_results_constructorId`, `IX_stg_results_statusId`

---

## 4. Chi tiết bảng kiểm soát ETL (`ctl.*`)

### 4.1. `ctl.etl_run_log`
Lưu trữ toàn bộ phiên thực thi của pipeline Mage:
* `run_id` (`UNIQUEIDENTIFIER`, PK, DEFAULT `NEWID()`): Mã phiên chạy.
* `pipeline_name` (`SYSNAME`, NOT NULL): Tên pipeline trong Mage (ví dụ: `'f1_source_to_stage'`).
* `source_file` (`NVARCHAR(260)`, NULL): Tên file nguồn xử lý.
* `target_schema` (`SYSNAME`, NULL): Mặc định `'stg'`.
* `target_table` (`SYSNAME`, NULL): Bảng đích.
* `load_mode` (`VARCHAR(20)`, NULL): `'full'` hoặc `'incremental'`.
* `batch_key` (`NVARCHAR(100)`, NULL): Khóa đợt nạp.
* `run_status` (`VARCHAR(20)`, NOT NULL): `'running'`, `'success'`, `'failed'`.
* `started_at_utc` (`DATETIME2(3)`, NOT NULL, DEFAULT `SYSUTCDATETIME()`).
* `completed_at_utc` (`DATETIME2(3)`, NULL).
* `rows_read` (`BIGINT`, NOT NULL, DEFAULT 0).
* `rows_written` (`BIGINT`, NOT NULL, DEFAULT 0).
* `rows_rejected` (`BIGINT`, NOT NULL, DEFAULT 0).
* `error_message` (`NVARCHAR(MAX)`, NULL).

### 4.2. `ctl.etl_batch_state`
Quản lý trạng thái và ngăn chặn việc nạp trùng lặp batch cho nguồn tĩnh:
* Khóa chính kép: `(source_name, source_table, batch_key)`
* `source_row_count` (`BIGINT`, NULL): Số dòng của batch.
* `last_run_id` (`UNIQUEIDENTIFIER`, NULL): Trỏ tới `run_id` gần nhất.
* `loaded_at_utc` (`DATETIME2(3)`, NULL).
* `batch_status` (`VARCHAR(20)`, NOT NULL): `'success'`, `'failed'`, `'in_progress'`.

---

## 5. Thứ tự triển khai DDL

Khi khởi tạo cơ sở dữ liệu mới, chạy các file script trong thư mục `sqlserver/ddl/` theo thứ tự:
1. `00_create_database_and_user.sql`: Khởi tạo DB `F1_BI`, login và user `f1_loader`.
2. `01_create_schemas.sql`: Khởi tạo schemas `stg`, `ctl`, `dw`.
3. `02_create_control_tables.sql`: Khởi tạo các bảng audit trong `ctl`.
4. `03_create_staging_tables.sql`: Khởi tạo 7 bảng Staging lõi trong `stg`.
