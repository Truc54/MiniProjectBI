# Bản Giao Diện Tích Hợp Mage ETL & SQL Server Staging (Table & Log Contract)

**Người bàn giao:** Dũng (SQL Server & Staging)  
**Người nhận bàn giao:** Lộc (Mage ETL)  
**Phiên bản:** 1.0 (Hoàn tất ngày 20/10/2026)  
**Tài liệu liên quan:** [stage_schema.md](file:///d:/MiniProjectBI/docs/stage_schema.md), [sql_server_setup.md](file:///d:/MiniProjectBI/docs/sql_server_setup.md)

---

## 1. Mục đích
Tài liệu này cung cấp toàn bộ quy chuẩn, thông số runtime, cấu trúc bảng, quy tắc ghi log kiểm soát và chiến lược nạp dữ liệu Idempotent để **Lộc** hoàn thiện các block trong pipeline `f1_source_to_stage` mà không gặp bất kỳ xung đột nào với cấu trúc cơ sở dữ liệu SQL Server.

---

## 2. Thông số Runtime Variables trong Mage

Khi thực thi pipeline `f1_source_to_stage`, các biến sau cần được truyền vào context hoặc runtime variables:

| Biến Runtime | Kiểu | Bắt buộc | Mặc định | Mô tả & Ví dụ |
|---|---|:---:|---|---|
| `file_name` | string | CÓ | `'results.csv'` | Tên file CSV nguồn (ví dụ: `'races.csv'`, `'drivers.csv'`). |
| `target_table` | string | CÓ | Tên theo file | Tên bảng đích trong SQL Server (ví dụ: `'results'`, `'races'`). |
| `schema_name` | string | KHÔNG | `'stg'` | Schema đích trong SQL Server (luôn là `'stg'`). |
| `load_mode` | string | KHÔNG | `'full'` | Chế độ nạp: `'full'` (nạp toàn bộ) hoặc `'incremental'` (nạp theo batch). |
| `batch_key` | string | KHÔNG | Tự động tạo | Mã định danh batch (ví dụ: `'full_snapshot_2026'`, `'batch_2024'`). |

---

## 3. Quy ước Khóa tự nhiên & Cột Metadata Lineage

### 3.1. Danh mục Natural Keys của 7 bảng lõi
Mỗi bảng trong `stg` đều có Primary Key Clustered trên natural key gốc:

| Tên bảng Stage | File CSV nguồn | Natural Key (Primary Key) | Kiểu dữ liệu PK |
|---|---|---|---|
| `stg.circuits` | `circuits.csv` | `circuitId` | `INT` |
| `stg.constructors` | `constructors.csv` | `constructorId` | `INT` |
| `stg.drivers` | `drivers.csv` | `driverId` | `INT` |
| `stg.status` | `status.csv` | `statusId` | `INT` |
| `stg.seasons` | `seasons.csv` | `year` | `INT` |
| `stg.races` | `races.csv` | `raceId` | `INT` |
| `stg.results` | `results.csv` | `resultId` | `INT` |

### 3.2. Cột Metadata Lineage (Bắt buộc)
Trước khi ghi vào SQL Server, DataFrame cần được chuẩn hóa có 4 cột kỹ thuật sau:
```python
df['_source_file'] = file_name          # string (VD: 'results.csv')
df['_batch_key'] = batch_key            # string (VD: 'full_20261020')
df['_load_mode'] = load_mode            # string: 'full' hoặc 'incremental'
df['_ingested_at_utc'] = pd.Timestamp.utcnow()  # UTC datetime
```
*(Nếu trong `load_f1_csv.py` đã tạo cột `source_file`, exporter sẽ tự động map thành `_source_file`)*.

---

## 4. Chiến lược Nạp Idempotent (Chống trùng lặp dữ liệu)

Để thỏa mãn yêu cầu của đề bài: **"Rerun không tạo duplicate dữ liệu"**, exporter trong Mage cần tuân theo chiến lược sau:

### 4.1. Chế độ Full Load (`load_mode = 'full'`)
1. Mở transaction trên SQL Server.
2. Kiểm tra xem bảng đích đã có dữ liệu chưa.
3. Thực hiện xóa dữ liệu cũ:
   ```sql
   DELETE FROM stg.{target_table}; -- Hoặc TRUNCATE TABLE stg.{target_table};
   ```
4. Ghi toàn bộ dữ liệu mới từ DataFrame vào `stg.{target_table}`.
5. Commit transaction.
* **Kết quả:** Khi chạy lại Full Load bao nhiêu lần thì số dòng và tập khóa vẫn giữ nguyên, không sinh duplicate.

### 4.2. Chế độ Incremental Load cho nguồn tĩnh (`load_mode = 'incremental'`)
Với bộ dữ liệu tĩnh, chia batch theo quy tắc xác định (deterministic) dựa trên Natural Key hoặc năm:
1. **Kiểm tra trạng thái Batch:** Trước khi nạp, truy vấn bảng `ctl.etl_batch_state`:
   ```sql
   SELECT batch_status FROM ctl.etl_batch_state
   WHERE source_name = ? AND source_table = ? AND batch_key = ?;
   ```
   * Nếu batch đã có trạng thái `'success'`, và cờ rerun không ép buộc: thông báo batch đã được nạp thành công trước đó.
2. **Delete-Insert theo Key Range hoặc Batch:**
   * Mở transaction.
   * Xóa các dòng thuộc batch hoặc có Primary Key trùng với tập keys của batch chuẩn bị nạp:
     ```sql
     DELETE FROM stg.{target_table} WHERE {natural_key} IN ({danh_sach_keys_cua_batch});
     -- Hoặc: DELETE FROM stg.{target_table} WHERE _batch_key = '{batch_key}';
     ```
   * Insert các dòng mới của batch vào bảng Stage.
   * Commit transaction.
* **Kết quả:** Khi rerun cùng một batch, các dòng cũ của batch đó được ghi đè/thay thế sạch sẽ, tổng số dòng của bảng không bị tăng lên.

---

## 5. Quy trình Ghi Log Kiểm soát (`ctl.*`)

Exporter cần tích hợp chặt chẽ với schema `ctl` theo vòng đời sau:

```text
[Mage Pipeline Bắt Đầu]
         │
         ▼
1. Sinh run_id (UUID4)
2. Ghi 1 dòng vào ctl.etl_run_log (run_status = 'running', started_at_utc = UTC_NOW)
3. Cập nhật ctl.etl_batch_state (batch_status = 'in_progress')
         │
         ▼
4. Thực thi nạp dữ liệu vào stg.{target_table} (Transaction an toàn)
         │
    ┌────┴──────────────────────────┐
    ▼                               ▼
[Thành Công]                    [Thất Bại / Lỗi]
    │                               │
    ├─> Commit Data Transaction     ├─> Rollback Data Transaction
    ├─> Cập nhật ctl.etl_run_log:   ├─> Cập nhật ctl.etl_run_log:
    │     run_status = 'success'    │     run_status = 'failed'
    │     rows_written = N          │     error_message = str(e)
    │     completed_at_utc = NOW    │     completed_at_utc = NOW
    └─> Cập nhật batch_state:       └─> Cập nhật batch_state:
          batch_status = 'success'        batch_status = 'failed'
```

---

## 6. Gợi ý Kịch bản Chia Batch Incremental cho Lộc

Để demo thuyết phục cho Seminar 1:
* **Demo với bảng `races` (1,164 dòng):**
  * `Batch 1` (`batch_key = 'races_hist_to_2023'`): Các chặng đua có `year <= 2023` (1,101 dòng).
  * `Batch 2` (`batch_key = 'races_2024_2026'`): Các chặng đua có `year >= 2024` (63 dòng).
  * **Test Rerun:** Sau khi nạp Batch 2, chạy lại Batch 2 lần nữa -> số dòng vẫn giữ nguyên đúng 1,164 dòng.
* **Demo với bảng `results` (27,568 dòng):**
  * `Batch 1` (`batch_key = 'results_part_1'`): `raceId <= 1000`.
  * `Batch 2` (`batch_key = 'results_part_2'`): `raceId > 1000`.
  * **Test Rerun:** Nạp lại `Batch 2` -> số dòng không thay đổi, log ghi nhận 2 lần chạy thành công.
