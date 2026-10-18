# Phase 1 checklist: source -> SQL Server staging

Phase 1 hướng đến mốc Seminar 1 ETL (23:00, 25/10/2026 theo lịch nhóm đã cung cấp). Bản nạp phải có thể tái lập và trình bày được.

## Phạm vi và thiết kế

- [ ] Ghi nguồn Kaggle, license, phiên bản/ngày snapshot và mô tả dataset.
- [ ] Profile đủ 17 CSV: header, loại dữ liệu, số dòng, khóa ứng viên, phạm vi thời gian và NULL/blank.
- [ ] Chốt bảy bảng Stage lõi: results, races, drivers, constructors, circuits, status, seasons; ghi lý do với các bảng còn lại.
- [ ] Chốt grain quy trình kết quả đua, khóa tự nhiên, quan hệ tham chiếu, source-to-stage mapping.
- [ ] Thiết kế mục tiêu một FactRaceResult ở grain resultId và các dimensions cần thiết; định nghĩa measure, hierarchy, và cách xử lý số đo không cộng.
- [ ] Chốt câu hỏi nghiệp vụ, người dùng, KPI và quy tắc không suy diễn từ NULL.

## SQL Server và Mage

- [ ] Tạo/cấu hình cơ sở dữ liệu; chạy DDL idempotent cho `stg`, `ctl`, `dw` và các bảng kiểm soát.
- [ ] Tạo các bảng `stg.*` theo contract đã duyệt, giữ lại khóa nguồn và nguồn gốc dữ liệu.
- [ ] Hoàn thiện Mage loader, validation và exporter cho các file trong phạm vi.
- [ ] Chuyển token nguồn `\N` thành SQL NULL; giữ phân biệt giữa NULL và giá trị 0.
- [ ] Kiểm tra header/schema, khóa không NULL/trùng, khóa ngoại và số dòng đọc/ghi.
- [ ] Hỗ trợ Full Load và Incremental Load. Với nguồn tĩnh, mô phỏng batch xác định, có thể chạy lại.
- [ ] Ghi run ID, file/bảng nguồn, batch, chế độ nạp, trạng thái, thời điểm, dòng đọc/ghi/từ chối và lỗi.
- [ ] Nạp thành công full load; nạp batch incremental; chạy lại cùng batch và chứng minh không tạo bản ghi trùng.
- [ ] Có đường dẫn xử lý lỗi và bằng chứng truy vấn SQL về số dòng, khóa, quan hệ tham chiếu và log.

## Bàn giao

- [ ] Cập nhật `docs/source_profile.md`, `docs/source_to_stage_mapping.md`, `docs/business_requirements.md`, `docs/dimensional_model.md`, `docs/data_quality_rules.md` và runbook.
- [ ] Lưu mã Mage, SQL scripts và file hướng dẫn cấu hình; không commit `.env`/mật khẩu.
- [ ] Ghi các giả định, lỗi còn tồn tại và bước Phase 2: dbt transformations/tests/docs, nạp mô hình dimensional vào `dw`, Power BI.

## Điều kiện hoàn tất

Một thành viên khác có thể làm theo README/runbook trên máy có SQL Server, chạy pipeline từ đầu, xem trạng thái và số dòng trong SQL Server, chạy lại batch mà không tăng bản ghi trùng, và truy lần được dòng Stage về file/batch nguồn. Có ảnh chụp hoặc truy vấn làm bằng chứng.
