# Kế hoạch Cá nhân Phase 2: Xây dựng Mô hình dbt & Điều phối Mage Pipeline

**Thành viên:** Trực  
**Vai trò:** Data Engineer & dbt-Mage Orchestration Specialist  
**Điểm tải công việc:** **25 điểm**  
**Thời hạn hoàn thành:** Mốc từng phần từ 28/10 đến 04/11/2026; nghiệm thu trước 23:00 ngày 05/11/2026  
**Tài liệu tham chiếu bắt buộc:** `03_dbt_Mage.docx.pdf` và `03_Appendix_Huong_dan_co_ban_ve_dbt.docx.pdf`  
**Phối hợp với:** Lộc (nhận bảng ánh xạ chuyển đổi và phân nhóm status), Dũng (kết nối database SQL Server), Phúc (nhận bộ test và nghiệm thu pipeline)

---

## 1. Mục tiêu & Trách nhiệm của Trực trong Phase 2

Trong Phase 2, nhiệm vụ cốt lõi của Trực là hiện thực hóa toàn bộ các phép chuyển đổi dữ liệu từ `stg` sang `dw` bằng công cụ chuẩn công nghiệp **dbt Core** và điều phối tự động qua **Mage**:
1. **Thiết lập Môi trường dbt Project:** Cấu hình `dbt-sqlserver`, hoàn thiện file cấu hình kết nối `profiles.yml` và dự án `dbt_project.yml`.
2. **Triển khai Macro Custom Schema (`generate_schema_name.sql`):** Vận dụng kỹ thuật từ tài liệu Appendix dbt (Trang 2 & 4) để ghi đúng vào schema `dw` và `stg_clean`, không để dbt ghép tiền tố schema mặc định.
3. **Lập trình 7 Staging Models (`models/staging/`):** Xây dựng các view chuẩn hóa dữ liệu, loại bỏ khoảng trắng (`TRIM`), ép kiểu dữ liệu và phân nhóm `OutcomeGroup` cho `stg_status.sql` dựa trên đặc tả của Lộc.
4. **Lập trình 6 Dimensions & 1 Fact Model (`models/marts/`):**
   - 6 Dimension models (`table`): sinh Surrogate Key (`*SK`) tự động, lưu giữ Natural Key và bản ghi Unknown (`-1`).
   - 1 Fact model `fact_race_result.sql` (`incremental`): cấu hình chiến lược `delete+insert`, khóa duy nhất `source_result_id`, nối các chiều qua khóa đại diện.
5. **Tích hợp DBT Model Block vào Mage Pipeline:** Tích hợp khối dbt vào Mage container, cấu hình volume mount, thiết lập selector `--select +fact_race_result` và đảm bảo an toàn giao dịch cho watermark.

---

## 2. Phân rã Công việc & Điểm số (25 Điểm)

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí nghiệm thu |
|:---:|---|:---:|:---:|---|
| **1** | **Khởi tạo dbt Project & Custom Schema Macro**<br/>Cấu hình `dbt_project.yml`, `profiles.yml` (đọc biến môi trường từ `.env`), macro `generate_schema_name.sql` và khai báo 7 bảng nguồn tại `sources.yml`. | **4** | 28/10 | Lệnh `dbt debug` trả về `All checks passed!`. Các bảng/view sinh ra đúng schema `dw` và `stg_clean`. |
| **2** | **Lập trình 7 Staging Models (`view`)**<br/>Viết `stg_circuits.sql`, `stg_constructors.sql`, `stg_drivers.sql`, `stg_status.sql`, `stg_seasons.sql`, `stg_races.sql`, `stg_results.sql`. Tích hợp phân loại 5 nhóm `OutcomeGroup`. | **6** | 30/10 | `dbt run --select staging` tạo thành công 7 views; không lỗi kiểu dữ liệu, các cột được đặt tên chuẩn tiếng Anh. |
| **3** | **Lập trình 6 Dimensions & 1 Fact Model (`marts`)**<br/>Viết `dim_date.sql`, `dim_race.sql`, `dim_circuit.sql`, `dim_driver.sql`, `dim_constructor.sql`, `dim_status.sql` và `fact_race_result.sql` với chiến lược `incremental`. | **7** | 01/11 | `dbt run --select marts` nạp đầy đủ dữ liệu vào SQL Server schema `dw`. Bảng Fact có đủ các measures cộng dồn và phi cộng dồn. |
| **4** | **Nâng cấp Docker & Tích hợp DBT Block vào Mage Pipeline**<br/>Cập nhật `mage/requirements.txt` (`dbt-sqlserver`), mount `./dbt` vào Mage container trong `compose.yaml`; tạo block DBT Model trong pipeline sau bước `load_sqlserver`. | **5** | 03/11 | Giao diện Mage hiển thị khối dbt; trigger pipeline chạy xuyên suốt từ CSV -> Stage -> dbt -> DW; log ghi nhận chi tiết. |
| **5** | **Thử nghiệm Incremental Rerun & Bàn giao Pipeline**<br/>Thực hiện nạp batch mới và chạy lại (rerun) trên cùng một batch để kiểm chứng tính bền bỉ (idempotent); tài liệu hóa runbook vận hành dbt trên Mage. | **3** | 05/11 | Chạy lại batch không làm nhân đôi số dòng; hoàn thiện tài liệu hướng dẫn vận hành pipeline Mage + dbt. |

---

## 3. Chi tiết Kỹ thuật: dbt Incremental Strategy & Mage Integration

### 3.1. Cấu hình Incremental cho `fact_race_result.sql`
Theo hướng dẫn tại Mục 6.1 của `03_Appendix_Huong_dan_co_ban_ve_dbt.docx.pdf`:
Vì `stg.results` là transient stage (chỉ giữ dữ liệu của batch hiện tại), Fact sử dụng chiến lược `delete+insert` để ghi đè các dòng cùng khóa `source_result_id` trong batch hiện tại mà không làm mất dữ liệu lịch sử của các batch trước đó:

```sql
{{
    config(
        schema='dw',
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key='source_result_id'
    )
}}
```

### 3.2. Cấu hình Pipeline Dependencies trong Mage
Theo cấu trúc chuẩn tại Hình 1, Trang 7 của tài liệu `03_dbt_Mage.docx.pdf`:
```text
load_f1_csv (Data Loader)
       │
       ▼
validate_f1_table (Transformer)
       │
       ▼
load_sqlserver (Data Exporter -> ghi vào stg.*)
       │
       ▼
dbt_transformation (DBT Model Block -> lệnh run --select +fact_race_result)
       │
       ▼
commit_watermark (Custom SQL/Python -> cập nhật ctl.etl_batch_state)
```

> **Nguyên tắc an toàn giao dịch:** Block `commit_watermark` bắt buộc phải là downstream của `dbt_transformation`. Nếu dbt gặp sự cố, watermark không được ghi nhận, đảm bảo hệ thống có thể chạy lại batch an toàn.

---

## 4. Các Giao diện Phối hợp & Bàn giao

- **Tiếp nhận từ Lộc:** Đặc tả ánh xạ kiểu dữ liệu và danh mục phân nhóm `OutcomeGroup` để áp dụng vào `stg_status.sql`.
- **Tiếp nhận từ Dũng:** Quyền truy cập SQL Server và cơ chế index Columnstore sau khi nạp Fact.
- **Bàn giao cho Phúc:** Toàn bộ dbt project hoàn chỉnh để Phúc bổ sung bộ kiểm thử `schema.yml`, singular tests và tiến hành nghiệm thu end-to-end.
