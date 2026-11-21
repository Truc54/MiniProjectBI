# Kế hoạch Cá nhân Phase 4 (Luồng 3 - Độc lập): View Giám sát SQL, User Read-Only & Power BI Trang 4 (ETL Monitoring)

**Thành viên:** Dũng  
**Vai trò:** SQL Server Observability DBA & Power BI Trang 4 + Master PBIX Finalizer  
**Điểm tải công việc:** **25 điểm**  
**Bắt đầu:** **NGAY LẬP TỨC** (Không cần chờ thành viên nào — bảng `ctl.etl_run_log` & `ctl.etl_batch_state` và các file PBIX Phase 3 đã có sẵn!)  
**Hạn hoàn thành:** Tối 21/11 xong 1 file SQL; Chiều 22/11 (18:00) xong Trang 4 & đóng gói `F1_Analytics_Final.pbix`  
**Trạng thái:** **[ ] SẴN SÀNG LÀM NGAY**

---

> [!IMPORTANT]
> ### Phạm vi Tinh gọn cho Dũng (Chỉ 1 file SQL + 1 trang Power BI, không tạo thêm bảng log mới)
> - **Không tạo** thêm bảng `ctl.dbt_run_log` hay `ctl.ai_insight_log` — dùng thẳng `ctl.etl_run_log` và `ctl.etl_batch_state` đã có sẵn từ [`sqlserver/ddl/02_create_control_tables.sql`](../../sqlserver/ddl/02_create_control_tables.sql).
> - **Không sửa** Star Schema `dw.*` hay bảng `_Measures` F1 của Phase 3; đặt toàn bộ measure giám sát ETL trong bảng riêng `_ETL_Measures`.

---

## 1. Nhiệm vụ Chi tiết & Phân bổ 25 Điểm

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí hoàn thành (DoD) |
|:---:|---|:---:|:---:|---|
| **1** | **Viết & chạy 1 file SQL duy nhất: `sqlserver/ctl/01_etl_monitoring_view_and_reader.sql`**<br/>Gồm 2 phần idempotent:<br/>(a) Tạo view `ctl.vw_etl_run_monitoring` từ `ctl.etl_run_log` tính sẵn `duration_sec`, `is_success`, `is_failed`, `reject_rate_pct`, `run_date_utc`.<br/>(b) Tạo Role `db_ai_reader` + Login/User `f1_ai_reader` **chỉ có quyền `SELECT` trên schema `dw` và `ctl`** (chặn hoàn toàn ghi/xóa và đọc `stg`). | **8** | 21/11 (22:00) | - Script chạy lại nhiều lần không lỗi.<br/>- Test đăng nhập `f1_ai_reader`: đọc `dw.FactRaceResult` và `ctl.vw_etl_run_monitoring` thành công; thử `DELETE` / `DROP` / đọc `stg.results` bị SQL Server từ chối.<br/>- Gửi thông tin user `f1_ai_reader` cho Trực điền vào `.env` (không chặn Trực code trước đó). |
| **2** | **Dựng Trang 4 Power BI: ETL Monitoring Dashboard (`F1_Analytics_Dev_Page4_ETL_Monitoring_Dung.pbix`)**<br/>Nạp `ctl.vw_etl_run_monitoring` và `ctl.etl_batch_state`, tạo bảng `_ETL_Measures` và thiết kế trang giám sát ETL ngay trên dữ liệu log đã có từ Phase 1–2. | **11** | 22/11 (16:00) | - Hiển thị đủ 5 KPI Cards: Total Runs, Success Rate (%), Avg Duration (s), Total Rows Written, Total Rows Rejected.<br/>- Biểu đồ xu hướng thời gian chạy & dòng nạp theo lần chạy / `target_table` / `load_mode` (`full` vs `incremental`).<br/>- Bảng chi tiết các lần chạy gần nhất tô màu trạng thái (`success` xanh / `failed` đỏ) kèm `batch_key`, `rows_rejected`, `error_message`.<br/>- Slicer lọc theo `target_table`, `load_mode`, `run_status`, ngày chạy + nút quay lại Trang 1. |
| **3** | **Tích hợp Trang 4 vào `powerbi/F1_Analytics_Final.pbix` & Đối soát Số liệu**<br/>Bấm **Refresh** đón bộ log mới của Lộc (Full + Incremental + 1 case lỗi), tích hợp Trang 4 cùng nút điều hướng Trang 1 <-> Trang 4 vào `powerbi/F1_Analytics_Final.pbix` và đối soát 5 KPI Cards với truy vấn SQL trực tiếp trên `ctl.etl_run_log`. | **6** | 22/11 (18:00) | - `powerbi/F1_Analytics_Final.pbix` chứa trọn 4 trang (3 trang F1 + Trang 4 ETL Monitoring), không lỗi visual.<br/>- 100% số liệu Trang 4 khớp với `SELECT` trực tiếp trên `ctl.etl_run_log` (PASS QA-03).<br/>- Case giả lập lỗi của Lộc hiện rõ dòng đỏ kèm `error_message` trên Trang 4. |
| **TỔNG** | **Điểm tải công việc Phase 4 của Dũng** | **25** | | **Hoàn tất độc lập `sqlserver/ctl/` và `F1_Analytics_Final.pbix` 4 trang** |

---

## 2. Đặc tả Kỹ thuật Nhanh

### 2.1. View `ctl.vw_etl_run_monitoring`
- `run_date_utc = CAST(started_at_utc AS DATE)`
- `duration_sec = CASE WHEN completed_at_utc IS NOT NULL THEN CAST(DATEDIFF(MILLISECOND, started_at_utc, completed_at_utc) / 1000.0 AS DECIMAL(12,3)) ELSE NULL END`
- `is_success = CASE WHEN run_status = 'success' THEN 1 ELSE 0 END`
- `is_failed = CASE WHEN run_status = 'failed' THEN 1 ELSE 0 END`
- `reject_rate_pct = CASE WHEN rows_read > 0 THEN CAST(rows_rejected * 100.0 / rows_read AS DECIMAL(6,2)) ELSE 0.00 END`

### 2.2. Measures DAX gợi ý trong `_ETL_Measures`
- `ETL Total Runs = COUNTROWS('ctl vw_etl_run_monitoring')`
- `ETL Success Runs = SUM('ctl vw_etl_run_monitoring'[is_success])`
- `ETL Failed Runs = SUM('ctl vw_etl_run_monitoring'[is_failed])`
- `ETL Success Rate = DIVIDE([ETL Success Runs], [ETL Total Runs], 0)`
- `ETL Avg Duration (s) = AVERAGE('ctl vw_etl_run_monitoring'[duration_sec])`
- `ETL Rows Written = SUM('ctl vw_etl_run_monitoring'[rows_written])`
- `ETL Rows Rejected = SUM('ctl vw_etl_run_monitoring'[rows_rejected])`

---

## 3. Điểm Giao tiếp Tối thiểu (Không chặn công việc)
- **Với Trực:** Xong `f1_ai_reader` thì gửi tên user/mật khẩu qua kênh nội bộ nhóm để Trực điền vào `.env`.
- **Với Phúc:** Gửi file `powerbi/F1_Analytics_Final.pbix` và câu SQL đối soát 5 KPI để Phúc kiểm định QA-03 & QA-08 (`f1_ai_reader`).
