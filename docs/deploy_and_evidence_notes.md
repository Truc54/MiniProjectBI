# Hướng dẫn Triển khai & Thu thập Bằng chứng Nghiệm thu (Seminar 1 - Phase 1)

**Tác giả:** Dũng (SQL Server & Staging)  
**Phối hợp:** Lộc (Mage ETL) & Trực (Dimensional Design & QA Acceptance)  
**Mục tiêu:** Cung cấp quy trình từng bước để nhóm triển khai từ đầu, nạp dữ liệu, kiểm tra tính Idempotent và xuất ảnh/kết quả truy vấn làm evidence nộp Seminar 1.

---

## 1. Trình tự Triển khai từ Đầu (Zero-to-Hero Deployment)

### Bước 1: Khởi động SQL Server & Cấu hình môi trường
1. Khởi động instance SQL Server trên máy (hoặc Docker). Đảm bảo cổng `1433` và TCP/IP đã bật theo [docs/sql_server_setup.md](file:///d:/MiniProjectBI/docs/sql_server_setup.md).
2. Tạo file `.env` từ file mẫu:
   ```bash
   cp .env.example .env
   ```
   Điền mật khẩu của user `sa` hoặc tài khoản quản trị SQL Server.

### Bước 2: Chạy DDL khởi tạo Schemas, Control Tables & 7 bảng Staging
Nhóm có thể lựa chọn 1 trong 2 cách:
* **Cách 1 (Dùng công cụ tự động của Dũng):**
  ```bash
  python sqlserver/run_all_ddl.py
  ```
* **Cách 2 (Chạy thủ công qua SSMS / Azure Data Studio):**
  1. `sqlserver/ddl/00_create_database_and_user.sql`
  2. `sqlserver/ddl/01_create_schemas.sql`
  3. `sqlserver/ddl/02_create_control_tables.sql`
  4. `sqlserver/ddl/03_create_staging_tables.sql`

---

## 2. Kịch bản Thực thi Pipeline Mage (Dành cho Lộc)

### 2.1. Nạp Full Load 7 bảng lõi
Khởi động Mage qua Docker Compose:
```bash
docker compose up -d
```
Truy cập giao diện Mage tại `http://localhost:6789`, mở pipeline `f1_source_to_stage`.

Thực thi tuần tự với runtime variables:
1. `file_name: circuits.csv`, `target_table: circuits`, `load_mode: full`
2. `file_name: constructors.csv`, `target_table: constructors`, `load_mode: full`
3. `file_name: drivers.csv`, `target_table: drivers`, `load_mode: full`
4. `file_name: status.csv`, `target_table: status`, `load_mode: full`
5. `file_name: seasons.csv`, `target_table: seasons`, `load_mode: full`
6. `file_name: races.csv`, `target_table: races`, `load_mode: full`
7. `file_name: results.csv`, `target_table: results`, `load_mode: full`

---

## 3. Kịch bản Chứng minh Tính Idempotent & Incremental (Demo Seminar 1)

Yêu cầu đề bài mục 3.1 & 5: Chứng minh nạp Incremental và chạy lại (Rerun) không tạo duplicate.

### Kịch bản Demo:
1. **Nạp Batch 1:**
   * Chọn `file_name: races.csv`, `target_table: races`, `load_mode: incremental`, `batch_key: races_batch_1`.
   * Ghi nhận số dòng trong SQL Server: giả sử `N1` dòng.
2. **Nạp Batch 2:**
   * Chọn `file_name: races.csv`, `target_table: races`, `load_mode: incremental`, `batch_key: races_batch_2`.
   * Ghi nhận số dòng tăng lên: `N1 + N2` dòng.
3. **Rerun (Chạy lại) Batch 2:**
   * Kích hoạt chạy lại chính xác Batch 2 với cùng `batch_key: races_batch_2`.
   * **Bằng chứng nghiệm thu:** Tổng số dòng trong `stg.races` vẫn giữ nguyên là `N1 + N2`, không có bất kỳ dòng trùng lặp nào!
   * Trong `ctl.etl_run_log` xuất hiện bản ghi thứ 2 của `races_batch_2` với trạng thái `success`.

---

## 4. Cách Lấy Bằng Chứng Nghiệm Thu (Evidence cho Trực)

Sau khi hoàn tất nạp dữ liệu, chạy script đối soát:
```bash
python sqlserver/run_all_ddl.py --reconcile
```
Hoặc mở file [sqlserver/reconciliation_queries.sql](file:///d:/MiniProjectBI/sqlserver/reconciliation_queries.sql) trong SSMS để chụp ảnh kết quả:

### 4.1. Bằng chứng số dòng (Row Count Evidence)
Kết quả kỳ vọng của phần 1:
| Tên bảng Stage | Số dòng Staging | Số dòng Baseline | Trạng thái |
|---|:---:|:---:|:---:|
| `stg.circuits` | 78 | 78 | **MATCH** |
| `stg.constructors` | 214 | 214 | **MATCH** |
| `stg.drivers` | 879 | 879 | **MATCH** |
| `stg.status` | 141 | 141 | **MATCH** |
| `stg.seasons` | 77 | 77 | **MATCH** |
| `stg.races` | 1,164 | 1,164 | **MATCH** |
| `stg.results` | 27,568 | 27,568 | **MATCH** |

### 4.2. Bằng chứng tính duy nhất & Không NULL khóa chính (PK Uniqueness Evidence)
Kết quả kỳ vọng của phần 2:
* Tất cả 7 bảng đều có `NullCount = 0` và `DuplicateKeyCount = 0`.

### 4.3. Bằng chứng toàn vẹn tham chiếu (Orphan Checks)
Kết quả kỳ vọng của phần 3:
* Mọi quan hệ giữa các bảng (`races -> circuits`, `races -> seasons`, `results -> races`, `results -> drivers`, `results -> constructors`, `results -> status`) đều có `OrphanCount = 0`.

### 4.4. Bằng chứng kiểm soát Log & Batch
Kết quả kỳ vọng của phần 5:
* Bảng `ctl.etl_run_log`: Thể hiện đầy đủ `run_id`, `pipeline_name`, `started_at_utc`, `completed_at_utc`, `rows_written`, `run_status = 'success'`.
* Bảng `ctl.etl_batch_state`: Thể hiện các batch đã nạp thành công và thời gian cập nhật.
