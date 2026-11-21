# Kế hoạch Cá nhân Phase 4 (Luồng 2 - Độc lập): Lập lịch ETL Mage.ai (Schedule Trigger) & Sinh Lịch sử Vận hành

**Thành viên:** Lộc  
**Vai trò:** Mage.ai Scheduling & ETL Operations Lead (Đúng sở trường Mage ETL từ Phase 1)  
**Điểm tải công việc:** **25 điểm**  
**Bắt đầu:** **NGAY LẬP TỨC** (Không cần chờ thành viên nào — pipeline `f1_source_to_stage` và `ctl.etl_run_log`, `ctl.etl_batch_state` đã có sẵn!)  
**Hạn hoàn thành:** Tối 21/11 bật Trigger; Chiều 22/11 (17:00) hoàn tất lịch sử 3 kịch bản + bằng chứng  
**Trạng thái:** **[ ] SẴN SÀNG LÀM NGAY**

---

> [!IMPORTANT]
> ### Phạm vi Tinh gọn cho Lộc (Chỉ tập trung Mage Scheduling, không code AI trên Mage)
> - **Không thêm** block AI vào Mage và **không tạo** bảng log mới — dùng trực tiếp pipeline [`f1_source_to_stage`](../../mage/project/pipelines/f1_source_to_stage/metadata.yaml) và bảng audit `ctl.etl_run_log`, `ctl.etl_batch_state` đang hoạt động ổn định.
> - Đáp ứng trực tiếp vế 1 của Bonus Seminar 3 (*"Lập lịch ETL"*) và tạo nguồn log thực tế phong phú (cả thành công lẫn sự cố có kiểm soát) cho Trang 4 Power BI (Dũng) và AI Chẩn đoán ETL (Trực).

---

## 1. Nhiệm vụ Chi tiết & Phân bổ 25 Điểm

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí hoàn thành (DoD) |
|:---:|---|:---:|:---:|---|
| **1** | **Cấu hình & Kích hoạt Mage.ai Schedule Trigger Chạy Định kỳ**<br/>Thiết lập Schedule Trigger (`Time` / Cron) cho pipeline `f1_source_to_stage` chạy tự động trọn chuỗi (`load_f1_csv -> validate_f1_table -> load_sqlserver -> dbt_transformation -> commit_watermark`). Dùng chu kỳ ngắn (VD: mỗi 15–30 phút) để ghi nhận nhiều lần tự động chạy thật, kèm cấu hình chuẩn `@daily` cho vận hành. | **10** | 21/11 (22:00) | - Trigger hiển thị trạng thái **ACTIVE** trên Mage UI (`http://localhost:6789`).<br/>- Có tối thiểu 2–3 lần chạy tự động liên tiếp thành công mà không cần bấm tay.<br/>- Xuất file cấu hình trigger / hướng dẫn bật lịch ngắn gọn trong `mage/` hoặc `docs/04_operations_and_guides/etl_runbook.md`. |
| **2** | **Chạy Sinh Dữ liệu Lịch sử Đầy đủ 3 Kịch bản trong `ctl.etl_run_log`**<br/>Đảm bảo bảng `ctl.etl_run_log` & `ctl.etl_batch_state` có đủ dữ liệu vận hành chân thực:<br/>(a) **Full Load** 7 bảng core + `dbt build` PASS.<br/>(b) **Incremental Load** (batch mới + rerun idempotent).<br/>(c) **1 Kịch bản giả lập lỗi kiểm định** (duplicate key / dữ liệu không hợp lệ tương tự cơ chế `--demo` trong [`mage/run_etl.py`](../../mage/run_etl.py), rollback nguyên tử không làm bẩn `stg`/`dw`). | **10** | 22/11 (16:00) | - `ctl.etl_run_log` có đủ các dòng `full` (`success`), `incremental` (`success`), và đúng 1–2 dòng `failed` kèm `rows_rejected > 0` và `error_message` rõ ràng.<br/>- Xác nhận `dw.FactRaceResult` vẫn giữ chuẩn **27.568 dòng** sau khi chạy case lỗi. |
| **3** | **Lưu Bằng chứng Lập lịch & Phối hợp Nghiệm thu QA**<br/>Chụp 3 ảnh bằng chứng rõ nét (Trigger UI `ACTIVE`, danh sách Runs tự động theo mốc giờ, truy vấn `ctl.etl_run_log`) + lưu log tóm tắt tại `docs/evidence/loc_phase4_schedule_runs.json`; phối hợp Phúc xác nhận PASS QA-01 & QA-02. | **5** | 22/11 (17:00) | - Đầy đủ ảnh chụp & JSON bằng chứng sẵn sàng dùng cho Video Demo.<br/>- QA-01 và QA-02 đạt **PASS 100%**. |
| **TỔNG** | **Điểm tải công việc Phase 4 của Lộc** | **25** | | **Hoàn tất độc lập Luồng Mage Scheduling trong thư mục `mage/`** |

---

## 2. Lưu ý Kỹ thuật Nhanh
- **Bảo toàn dữ liệu DW khi giả lập lỗi:** Luôn tận dụng cơ chế validation + rollback có sẵn trong [`mage/project/f1_etl/sqlserver.py`](../../mage/project/f1_etl/sqlserver.py) (`export_payload` tự động ghi `run_status='failed'`, `rows_rejected`, `error_message` vào `ctl.etl_run_log` mà không làm thay đổi dữ liệu hợp lệ trong `stg` và `dw`).
- **Thông báo ngắn cho Dũng & Trực sau khi xong bước 2:** Nhắn nhóm 1 câu *"Đã chạy xong đủ log Full + Incremental + Case lỗi"* để Dũng bấm Refresh Trang 4 Power BI và Trực test AI Chẩn đoán ETL trên dữ liệu mới nhất.
