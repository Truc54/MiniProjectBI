# Lộ trình & Kế hoạch Thực hiện Dự án MiniProject BI

**Học phần:** Business Intelligence / Data Warehouse  
**Bộ dữ liệu:** Formula 1 World Championship (1950–2026)  
**Nhóm sinh viên thực hiện:** Phúc, Dũng, Lộc, Trực  

---

## Tổng quan Lộ trình Dự án (Project Milestones)

Dự án được chia làm 4 giai đoạn (Phases) kế thừa chặt chẽ theo chu trình phát triển Data Warehouse, Business Intelligence, DataOps & Generative AI chuẩn công nghiệp:

```mermaid
flowchart LR
    P1["Phase 1: Ingestion & Staging (Da hoan thanh - 25/10/2026)"]
    P2["Phase 2: dbt Transformation & Kimball DW (Da hoan thanh - 05/11/2026)"]
    P3["Phase 3: Power BI Semantic Model & 3 Dashboards F1 (Hoan thien)"]
    P4["Phase 4: ETL Scheduling, Monitoring & Generative AI (Hien tai - Han 23/11/2026)"]

    P1 --> P2 --> P3 --> P4
```

---

## Cấu trúc Thư mục Kế hoạch (`plans/`)

Nhằm đảm bảo tính chuyên nghiệp, dễ theo dõi và bàn giao qua từng giai đoạn, toàn bộ kế hoạch được tổ chức thành các thư mục phase riêng biệt, mỗi phase chia thành kế hoạch tổng thể và kế hoạch chi tiết cho từng thành viên:

```text
plans/
├── README.md                                                     # Tài liệu tổng quan lộ trình (File này)
│
├── phase1_etl_staging/                                           # Phase 1: Ingestion & Staging (Đã nghiệm thu)
│   ├── 00_ke_hoach_tong_quat_phase1.md                           # Kế hoạch tổng quát Phase 1 (Mage + SQL Server Stage)
│   ├── 01_ke_hoach_phuc_source_profile.md                        # Kế hoạch chi tiết Phúc: Source profiling & data contract
│   ├── 02_ke_hoach_dung_sqlserver_staging.md                     # Kế hoạch chi tiết Dũng: SQL Server setup & DDL staging
│   ├── 03_ke_hoach_loc_mage_etl.md                               # Kế hoạch chi tiết Lộc: Xây dựng pipeline Mage ETL & tests
│   └── 04_ke_hoach_truc_model_qa.md                              # Kế hoạch chi tiết Trực: Thiết kế dimensional & QA
│
├── phase2_dbt_dw/                                                # Phase 2: dbt Transformation & Data Warehouse (Đã hoàn thành)
│   ├── 00_ke_hoach_tong_quat_phase2.md                           # Kế hoạch tổng quát Phase 2 (dbt, Kimball DW, Mage, QA)
│   ├── 01_ke_hoach_loc_transformation_mapping.md                 # Kế hoạch chi tiết Lộc: Ánh xạ chuyển đổi & từ điển DW (25đ)
│   ├── 02_ke_hoach_dung_sqlserver_dw.md                          # Kế hoạch chi tiết Dũng: Quản trị SQL Server, Columnstore & Seed (25đ)
│   ├── 03_ke_hoach_truc_dbt_mage_etl.md                          # Kế hoạch chi tiết Trực: Lập trình dbt models & điều phối Mage (25đ)
│   └── 04_ke_hoach_phuc_dimensional_qa.md                        # Kế hoạch chi tiết Phúc: Quản trị Kimball & bộ dbt tests (25đ)
│
├── phase3_powerbi/                                               # Phase 3: Semantic Model & Power BI Dashboard
│   ├── 00_ke_hoach_tong_quat_phase3_powerbi.md                   # Kế hoạch tổng quát Phase 3 (Semantic Model, 3 trang dashboard, QA)
│   ├── 01_ke_hoach_truc_semantic_model_master_pbix.md            # Kế hoạch chi tiết Trực: Semantic Model & Master PBIX (25đ)
│   ├── 02_ke_hoach_phuc_overview_dashboard_qa.md                 # Kế hoạch chi tiết Phúc: Trang 1 Overview & QA Lead (25đ)
│   ├── 03_ke_hoach_dung_performance_dynamics_page2.md            # Kế hoạch chi tiết Dũng: Trang 2 Thành tích & Biến động (25đ)
│   └── 04_ke_hoach_loc_circuit_outcomes_page3.md                 # Kế hoạch chi tiết Lộc: Trang 3 Trường đua & Kết quả (25đ)
│
└── phase4_genai_etlops/                                          # Phase 4: Generative AI, Lập lịch ETL, Giám sát ETL & QA (Độc lập - Hạn 23/11/2026)
    ├── 00_ke_hoach_tong_quat_phase4_genai_etlops.md              # Kế hoạch tổng quát Phase 4 (4 luồng kỹ thuật độc lập, 0% chờ nhau)
    ├── 01_ke_hoach_truc_ai_assistant_streamlit_text_to_sql.md    # Luồng 1 - Trực: Trọn gói `ai_assistant/` (1 trang Streamlit + Safe Text-to-SQL) (25đ)
    ├── 02_ke_hoach_loc_mage_etl_scheduler.md                     # Luồng 2 - Lộc: Mage Schedule Triggers & chạy lịch sử ETL (Full/Inc/Lỗi) (25đ)
    ├── 03_ke_hoach_dung_sql_monitoring_powerbi_page4.md          # Luồng 3 - Dũng: 1 file SQL (`vw_etl_run_monitoring` + `f1_ai_reader`), Trang 4 Power BI & Final PBIX (25đ)
    └── 04_ke_hoach_phuc_qa_security_demo.md                      # Luồng 4 - Phúc: Test tự động 8 kịch bản QA, Bảo mật SQL & Kịch bản Video Demo (25đ)
```

---

## Chi tiết các Tài liệu Kế hoạch Phase 4 (Bản Tinh Gọn & Độc Lập — Hạn 23:00 ngày 23/11/2026)

Nhấn vào từng file bên dưới để xem kế hoạch hành động chi tiết của từng thành viên (cả 4 luồng kỹ thuật đều bắt đầu được **ngay lập tức**, không chờ nhau):
1. [Kế hoạch tổng quát Phase 4: Generative AI, Lập lịch ETL, Giám sát ETL & QA](phase4_genai_etlops/00_ke_hoach_tong_quat_phase4_genai_etlops.md) (Cả nhóm)
2. [Luồng 1 — Trực: Trọn gói Ứng dụng AI Streamlit (1 Trang) & Chatbot Safe Text-to-SQL](phase4_genai_etlops/01_ke_hoach_truc_ai_assistant_streamlit_text_to_sql.md)
3. [Luồng 2 — Lộc: Lập lịch ETL Mage.ai (Schedule Trigger) & Sinh Lịch sử Vận hành](phase4_genai_etlops/02_ke_hoach_loc_mage_etl_scheduler.md)
4. [Luồng 3 — Dũng: View SQL Monitoring, User Read-Only & Power BI Trang 4 + Final PBIX](phase4_genai_etlops/03_ke_hoach_dung_sql_monitoring_powerbi_page4.md)
5. [Luồng 4 — Phúc: Lead QA Kiểm định Tự động (AI Grounding, Bảo mật, ETL) & Kịch bản Video Demo](phase4_genai_etlops/04_ke_hoach_phuc_qa_security_demo.md)

---

## Ma trận Phân công 4 Luồng Độc lập Phase 4 (25 điểm / thành viên — 0% Chờ nhau)

| Thành viên | Luồng độc lập | Nhiệm vụ cốt lõi (Bắt đầu được ngay từ phút 0) | Điểm Phase 4 |
|---|---|---|:---:|
| **Trực** | **Luồng 1:** Trọn gói `ai_assistant/` | Tự chủ **3 file gọn** (`ai_core.py`, `text_to_sql.py`, `app.py`) nối thẳng `dw.*` & `ctl.etl_run_log` đã có: **1 trang Streamlit duy nhất** gồm AI Tóm tắt F1/ETL (+ up ảnh biểu đồ) và Chatbot Hỏi–Đáp Safe Text-to-SQL + cập nhật `.env.example`. | **25** |
| **Lộc** | **Luồng 2:** `mage/` | Bật **Mage Schedule Trigger** chạy định kỳ trên `f1_source_to_stage`, chạy sinh lịch sử Full/Incremental + 1 case lỗi giả lập vào `ctl.etl_run_log`, lưu bằng chứng Trigger UI & log vận hành. | **25** |
| **Dũng** | **Luồng 3:** `sqlserver/ctl/` & `powerbi/` | Viết **1 file SQL** tạo view `ctl.vw_etl_run_monitoring` (từ `ctl.etl_run_log` sẵn có) + user chỉ đọc `f1_ai_reader`, dựng **Trang 4 Power BI (ETL Monitoring)** và đóng gói `powerbi/F1_Analytics_Final.pbix` 4 trang. | **25** |
| **Phúc** | **Luồng 4:** `tests/` & `docs/evidence/` | Viết bộ test tự động `tests/test_phase4_qa.py` (10+ mẫu SQL Injection, test `f1_ai_reader`, Ground Truth SQL), thực thi **8 kịch bản QA cốt lõi** và soạn **Kịch bản Video Demo (5–7 phút)**. | **25** |

---

## Chi tiết các Tài liệu Kế hoạch Phase 3 (Power BI)

Nhấn vào từng file bên dưới để xem kế hoạch hành động chi tiết của từng thành viên trong Phase 3:
1. [Kế hoạch tổng quát Phase 3 Power BI](phase3_powerbi/00_ke_hoach_tong_quat_phase3_powerbi.md) (Cả nhóm)
2. [Kế hoạch chi tiết: Trực - Semantic Model, Hierarchies & Master PBIX](phase3_powerbi/01_ke_hoach_truc_semantic_model_master_pbix.md)
3. [Kế hoạch chi tiết: Phúc - Dashboard Overview & Lead QA Specialist](phase3_powerbi/02_ke_hoach_phuc_overview_dashboard_qa.md)
4. [Kế hoạch chi tiết: Dũng - Dashboard Thành tích & Biến động (BQ1, BQ2, BQ6)](phase3_powerbi/03_ke_hoach_dung_performance_dynamics_page2.md)
5. [Kế hoạch chi tiết: Lộc - Dashboard Trường đua & Kết quả (BQ3, BQ4, BQ5)](phase3_powerbi/04_ke_hoach_loc_circuit_outcomes_page3.md)

---

## Ma trận Phân công Công việc Cân bằng Phase 3 (25 điểm / thành viên)

| Thành viên | Vai trò Phase 3 | Nhiệm vụ chính Phase 3 | Điểm Phase 3 |
|---|---|---|:---:|
| **Trực** | Semantic Model Architect & Master Integrator | Khởi tạo kết nối SQL Server DW, cấu hình Star Schema thuần túy, 6 Hierarchies, thư viện tập trung hơn 15 DAX measures trong bảng `_Measures`, tạo Master Template và tích hợp visual của cả 3 trang vào file PBIX cuối cùng. | **25** |
| **Phúc** | Overview Dashboard Lead & Lead QA Specialist | Thiết kế Trang 1: Overview (4 KPI cards, Line & Column xu hướng theo mùa, Donut chart cơ cấu kết quả, Top 10 tay đua chiến thắng, navigation buttons) và chủ trì kiểm thử đối soát chéo số liệu Power BI vs SQL Server DW. | **25** |
| **Dung** | Performance Dynamics Specialist | Thiết kế Trang 2: Thành tích và biến động, giải quyết triệt để **BQ1** (xu hướng theo mùa/chặng), **BQ2** (so sánh Driver vs Constructor), **BQ6** (Waterfall chart phân tích đóng góp tăng giảm điểm so với chặng trước, tuân thủ nguyên tắc phi nhân quả). | **25** |
| **Lộc** | Circuit Constraints & Reliability Specialist | Thiết kế Trang 3: Trường đua và kết quả, giải quyết triệt để **BQ3** (Bản đồ phân bố địa lý trường đua & quốc gia), **BQ4** (Scatter plot tương quan Grid vs Finish với bộ lọc nghiêm ngặt `grid > 0` và có vị trí phân loại), **BQ5** (Phân tích tỷ lệ không phân loại theo 5 `OutcomeGroup` và status gốc). | **25** |

---

## Ma trận Phân công Công việc Cân bằng (25 điểm / thành viên)

| Thành viên | Trách nhiệm chính trong Phase 1 (Đã hoàn thành) | Trách nhiệm chính trong Phase 2 (Đang triển khai) | Điểm Phase 2 |
|---|---|---|:---:|
| **Lộc** | Xây dựng pipeline Mage ETL, xử lý NULL `\N`, Full/Incremental load, cơ chế ghi log vào `ctl`. | Thẩm định chi tiết logic biến đổi từ `stg` sang `dw` (phân loại 141 mã status thành 5 nhóm `OutcomeGroup`, quy tắc xử lý điểm số các thời kỳ F1), xây dựng từ điển dữ liệu DW và soạn thảo tài liệu Phase 2. | **25** |
| **Dũng** | Cài đặt SQL Server, cấp phát user, viết DDL 7 bảng Staging (`stg`) và bảng Control (`ctl`). | Thiết lập vật lý schema Data Warehouse (`dw`), cấp phát quyền, áp dụng **Clustered Columnstore Index (CCI)** cho Fact, tạo bản ghi mặc định **Unknown Member (`SK = -1`)**, viết script SQL đối soát toàn diện (`stg` vs `dw`). | **25** |
| **Trực** | Định hình grain, thiết kế Star Schema logic, quy chuẩn KPI và kiểm thử đối soát Phase 1. | Thiết kế và lập trình **dbt project** (7 Staging views, 6 Dimensions, 1 Incremental Fact, macro `generate_schema_name`). Nâng cấp Docker và tích hợp DBT Model block vào pipeline điều phối Mage. | **25** |
| **Phúc** | Profile 17 CSV nguồn, xác định missing value, lập source mapping và data quality contract. | Quản trị thiết kế mô hình chiều Kimball (Grain 1 dòng/`resultId`), xây dựng bộ **dbt Data Tests** tự động (`schema.yml` + singular SQL tests), thực thi 4 kịch bản thử nghiệm nạp/chạy lại/sự cố và nghiệm thu Phase 2. | **25** |

---

## Chi tiết các Tài liệu Kế hoạch Phase 2

Nhấn vào từng file bên dưới để xem kế hoạch hành động chi tiết của từng thành viên:
1. [Kế hoạch tổng quát Phase 2](phase2_dbt_dw/00_ke_hoach_tong_quat_phase2.md)
2. [Kế hoạch chi tiết: Lộc - Transformation Mapping & Semantic QA](phase2_dbt_dw/01_ke_hoach_loc_transformation_mapping.md)
3. [Kế hoạch chi tiết: Dũng - SQL Server DW Physical & Optimization](phase2_dbt_dw/02_ke_hoach_dung_sqlserver_dw.md)
4. [Kế hoạch chi tiết: Trực - dbt Models & Mage Orchestration](phase2_dbt_dw/03_ke_hoach_truc_dbt_mage_etl.md)
5. [Kế hoạch chi tiết: Phúc - Kimball Architecture & QA Acceptance](phase2_dbt_dw/04_ke_hoach_phuc_dimensional_qa.md)
