# Lộ trình & Kế hoạch Thực hiện Dự án MiniProject BI

**Học phần:** Business Intelligence / Data Warehouse  
**Bộ dữ liệu:** Formula 1 World Championship (1950–2026)  
**Nhóm sinh viên thực hiện:** Phúc, Dũng, Lộc, Trực  

---

## Tổng quan Lộ trình Dự án (Project Milestones)

Dự án được chia làm 3 giai đoạn (Phases) kế thừa chặt chẽ theo chu trình phát triển Data Warehouse & Business Intelligence chuẩn công nghiệp:

```mermaid
flowchart LR
    P1["Phase 1: Ingestion & Staging<br/>(Kaggle -> Mage -> SQL Server stg/ctl)<br/><b>ĐÃ HOÀN THÀNH (25/10/2026)</b>"]
    P2["Phase 2: dbt Transformation & Data Warehouse<br/>(stg -> dbt Core -> dw Kimball -> Mage Orchestration)<br/><b>GIAI ĐOẠN HIỆN TẠI (05/11/2026)</b>"]
    P3["Phase 3: Power BI Dashboards & Generative AI<br/>(Power BI Dashboards, Semantic Model, GenAI Insights)<br/><b>GIAI ĐOẠN TIẾP THEO (14/11/2026)</b>"]

    P1 --> P2 --> P3
```

---

## Cấu trúc Thư mục Kế hoạch (`plans/`)

Nhằm đảm bảo tính chuyên nghiệp, dễ theo dõi và bàn giao qua từng giai đoạn, toàn bộ kế hoạch được tổ chức thành các thư mục phase riêng biệt, mỗi phase chia thành kế hoạch tổng thể và kế hoạch chi tiết cho từng thành viên:

```text
plans/
├── README.md                                         # Tài liệu tổng quan lộ trình (File này)
│
├── phase1_etl_staging/                               # Phase 1: Ingestion & Staging (Đã nghiệm thu)
│   ├── 00_ke_hoach_tong_quat_phase1.md               # Kế hoạch tổng quát Phase 1 (Mage + SQL Server Stage)
│   ├── 01_ke_hoach_phuc_source_profile.md            # Kế hoạch chi tiết Phúc: Source profiling & data contract
│   ├── 02_ke_hoach_dung_sqlserver_staging.md         # Kế hoạch chi tiết Dũng: SQL Server setup & DDL staging
│   ├── 03_ke_hoach_loc_mage_etl.md                   # Kế hoạch chi tiết Lộc: Xây dựng pipeline Mage ETL & tests
│   └── 04_ke_hoach_truc_model_qa.md                  # Kế hoạch chi tiết Trực: Thiết kế dimensional & QA
│
├── phase2_dbt_dw/                                    # Phase 2: dbt Transformation & Data Warehouse (Đã hoàn thành)
│   ├── 00_ke_hoach_tong_quat_phase2.md               # Kế hoạch tổng quát Phase 2 (dbt, Kimball DW, Mage, QA)
│   ├── 01_ke_hoach_loc_transformation_mapping.md     # Kế hoạch chi tiết Lộc: Ánh xạ chuyển đổi & từ điển DW (25đ)
│   ├── 02_ke_hoach_dung_sqlserver_dw.md              # Kế hoạch chi tiết Dũng: Quản trị SQL Server, Columnstore & Seed (25đ)
│   ├── 03_ke_hoach_truc_dbt_mage_etl.md              # Kế hoạch chi tiết Trực: Lập trình dbt models & điều phối Mage (25đ)
│   └── 04_ke_hoach_phuc_dimensional_qa.md            # Kế hoạch chi tiết Phúc: Quản trị Kimball & bộ dbt tests (25đ)
│
└── phase3_powerbi/                                   # Phase 3: Semantic Model & Power BI Dashboard (Hiện tại)
    ├── 00_ke_hoach_tong_quat_phase3_powerbi.md       # Kế hoạch tổng quát Phase 3 (Semantic Model, 3 trang dashboard, QA)
    ├── 01_ke_hoach_truc_semantic_model_master_pbix.md # Kế hoạch chi tiết Trực: Semantic Model & Master PBIX (25đ)
    ├── 02_ke_hoach_phuc_overview_dashboard_qa.md     # Kế hoạch chi tiết Phúc: Trang 1 Overview & QA Lead (25đ)
    ├── 03_ke_hoach_dung_performance_dynamics_page2.md # Kế hoạch chi tiết Dũng: Trang 2 Thành tích & Biến động (25đ)
    └── 04_ke_hoach_loc_circuit_outcomes_page3.md     # Kế hoạch chi tiết Lộc: Trang 3 Trường đua & Kết quả (25đ)
```

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
