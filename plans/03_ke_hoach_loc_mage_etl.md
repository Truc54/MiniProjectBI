# Kế hoạch cá nhân - Lộc: Mage ETL source-to-stage

**Tổng tải Phase 1: 25/100 điểm (25%).** Lộc hoàn thiện Mage pipeline để đọc CSV và nạp Staging SQL Server. Loader, schema validation, và logic batch có thể phát triển trước khi database DDL tích hợp xong.

## Mục tiêu và sản phẩm bàn giao

- Pipeline Mage trong `mage/project/pipelines/f1_source_to_stage` chạy các file được chọn theo biến runtime.
- Data loader đọc CSV UTF-8/UTF-8 BOM và xử lý `\N` thành NULL; transformer kiểm tra schema, keys, domains cơ bản.
- Exporter ghi vào `stg` trên SQL Server với Full Load và Incremental Load mô phỏng batch cho source tĩnh.
- Log/audit vào `ctl` theo Dũng; rerun không tạo duplicate và lỗi được lưu.
- `docs/etl_runbook.md`: cấu hình, thao tác chạy, biến runtime, truy vấn kiểm tra và xử lý lỗi.

## Công việc chi tiết

### L1. Loader và pipeline contract - 5 điểm

- [ ] Giữ loader generic cho tên file trong whitelist; mặc định/cấu hình theo table mapping được Phúc chốt.
- [ ] Chặn path traversal; file phải tồn tại; báo rõ file/table khi đọc lỗi.
- [ ] Đọc UTF-8 BOM; bảo toàn giá trị nguồn; parse đúng literal `\N` thành null mà không biến 0 hoặc chuỗi rỗng thành null.
- [ ] Thêm source metadata cần thiết (file, batch, ingestion timestamp) theo interface đã thống nhất với Dũng.
- [ ] Truyền rõ `file_name`, `table_name`, `target_table`, `load_mode`, `batch_key` và các tham số kết nối qua môi trường an toàn.

**Hoàn tất khi:** loader đọc được từng file lõi ở local/Mage block và kết quả giữ đúng schema/nulls.

### L2. Data quality transformer - 5 điểm

- [ ] Kiểm tra tập cột/header bắt buộc và row shape; chỉ cho phép các bảng trong source mapping.
- [ ] Kiểm tra natural key không NULL, không trùng trong file/batch ở grain đã chốt.
- [ ] Kiểm tra kiểu/format số và ngày cần thiết; không reject optional measures chỉ vì NULL.
- [ ] Kiểm tra FK sau khi đủ các bảng liên quan; báo orphan count và mẫu khóa thay vì âm thầm xóa.
- [ ] Áp dụng domain checks an toàn: không kết luận DNF từ `position` NULL hoặc DNS từ `grid=0`.

**Hoàn tất khi:** thiếu cột, duplicate key, hoặc file sai format được chặn/log; NULL hợp lệ qua được.

### L3. Full Load và incremental static batches - 8 điểm

- [ ] Implement Full Load theo transaction hoặc staging-swap an toàn đã chốt; chạy lại cùng source/snapshot cho cùng tập rows/keys.
- [ ] Với nguồn tĩnh, tạo batch xác định có thể tái tạo, dùng natural-key range hoặc partition ổn định; không chia theo thứ tự ngẫu nhiên giữa các lần chạy.
- [ ] Implement incremental upsert/merge theo natural key; xác định rõ insert/update behavior và state/checkpoint của từng batch.
- [ ] Chỉ đánh dấu batch thành công sau khi dữ liệu ghi thành công; lỗi rollback hoặc giữ trạng thái có thể retry.
- [ ] Chạy full -> batch incremental -> rerun cùng batch, so counts và uniqueness với trước rerun.
- [ ] Đảm bảo bảng `stg` không tích lũy duplicate khi một run bị gián đoạn và khởi động lại.

**Hoàn tất khi:** có ít nhất một batch incremental được mô phỏng, tải lại được và không tăng số dòng trùng.

### L4. Logging, error path và observability - 4 điểm

- [ ] Ghi mỗi run vào `ctl.etl_run_log`: run ID, file/table, mode/batch, started/completed, status, rows read/written/rejected, error.
- [ ] Ghi/cập nhật `ctl.etl_batch_state` theo khóa batch; không để trạng thái success trước commit dữ liệu.
- [ ] Log exception có ngữ cảnh nhưng không ghi password/connection string bí mật.
- [ ] Cho phép truy vấn log theo run, file, batch và kiểm tra trạng thái khi chạy lại.

**Hoàn tất khi:** demo được run thành công và lỗi có status/error record, secret không xuất hiện trong log.

### L5. Runbook và demo package - 3 điểm

- [ ] Ghi cách copy `.env.example` thành `.env`, cấu hình SQL Server/ODBC, start Mage, chạy pipeline với runtime variables.
- [ ] Ghi thứ tự load, batch test, expected counts, SQL query kiểm tra và cách đọc log.
- [ ] Lưu output/error evidence và hướng dẫn cách xử lý retry.

**Hoàn tất khi:** thành viên khác làm theo runbook và tái lập được pipeline.

## Tiến độ và phụ thuộc

| Thời điểm | Kết quả |
|---|---|
| 18-19/10 | Loader, path guard, null normalization, basic transformer phát triển song song DDL |
| 20-21/10 | Chốt runtime vars, output columns và log schema với Dũng; pipeline local hoàn chỉnh |
| 22-23/10 | Kết nối SQL Server; full load các bảng core; kiểm tra counts/keys/FKs |
| 24/10 | Incremental batch, rerun, failure logging và evidence |
| 25/10 | Freeze pipeline/runbook và diễn tập demo |

**Đầu vào:** file list/source contract từ Phúc và table/log contract từ Dũng. Lộc có thể hoàn tất loader/transformer trước khi DDL chạy; chỉ exporter tích hợp cần SQL Server online. Trực cung cấp tiêu chí/model để validation không hiểu sai trạng thái F1.

## Review chéo và nghiệm thu

- Phúc review việc map source values/NULL và file coverage.
- Dũng review transaction, keys, bảng log/batch và truy vấn SQL.
- Trực review status/KPI semantics và rerun acceptance.
- Lộc bàn giao pipeline source code, requirements/runtime config, runbook và evidence.

## Trách nhiệm tiếp nối để hoàn thành project

Các việc sau thuộc Phase 2/3, không tính vào 25 điểm tải Phase 1:

- **Phase 2:** xây dbt models từ Stage sang DW: source/staging models, clean/standardize/integrate, FactRaceResult/Dimensions; thêm transformation cần cho câu hỏi đã chốt; viết dbt tests cho uniqueness, not-null, relationships và business rules; tổ chức dependencies; sinh/cập nhật dbt docs/lineage; chứng minh dbt nạp được DW trên SQL Server.
- **Phase 3:** triển khai phần service/backend gọi LLM hoặc GenAI để tạo summary và giải thích thay đổi từ KPI/breakdowns đã tính; đưa dữ liệu số liệu có kiểm soát vào prompt/context, trả về period/filter/measure/evidence, hướng dẫn “không đủ bằng chứng” khi cần; không để mô hình tự truy vấn tuỳ ý hoặc bịa measure.
- **Final handoff:** bàn giao source code, cách cài/config API key bằng env secret, lỗi/rate limit behavior, và một luồng demo từ Mage -> dbt -> Power BI -> AI.
