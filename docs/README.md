# Tài liệu Dự án MiniProject BI - Formula 1 Analytics

Chào mừng bạn đến với kho tài liệu kỹ thuật và nghiệp vụ của dự án **Formula 1 World Championship (1950–2026) Business Intelligence System**. 

Nhóm thực hiện: **Phúc, Dũng, Lộc, Trực**

Hệ thống được thiết kế theo kiến trúc chuẩn doanh nghiệp:
```text
Kaggle CSV (dataset/)
        │
        ▼
Mage.ai Ingestion (Validation & Batch Control)
        │                                 │
        ▼                                 ▼
SQL Server: Schema [stg]          SQL Server: Schema [ctl]
        │
        ▼
dbt Core (Staging Views -> Kimball Star Schema Marts)
        │
        ▼
SQL Server: Schema [dw] (Fact Columnstore Index & Dimensions)
        │
        ▼
Power BI Semantic Model & Dashboards (Phase 3)
```

---

## Cấu trúc Danh mục Tài liệu

Hệ thống tài liệu được phân loại thành 4 trụ cột nghiệp vụ & kỹ thuật chuyên nghiệp, cùng kho lưu trữ bằng chứng thực nghiệm:

```text
docs/
├── README.md                              # Cổng thông tin tài liệu (Tài liệu này)
│
├── 01_architecture_and_design/            # Kiến trúc hệ thống, nghiệp vụ và mô hình dữ liệu
│   ├── architecture.md                    # Kiến trúc tổng thể dữ liệu từ Source -> Staging -> DW -> BI
│   ├── business_requirements.md           # Yêu cầu phân tích, câu hỏi nghiệp vụ và định nghĩa KPI chuẩn
│   └── dimensional_model.md               # Thiết kế mô hình chiều Kimball (Star Schema, Grain, Fact & Dims)
│
├── 02_data_dictionary_and_mapping/        # Từ điển dữ liệu và ánh xạ chuyển đổi
│   ├── source_profile.md                  # Khảo sát dữ liệu nguồn 17 CSV Kaggle, thống kê missing & quyết định phạm vi
│   ├── source_to_stage_mapping.md         # Quy tắc ánh xạ 1:1 từ CSV sang các bảng SQL Server Staging
│   ├── stage_schema.md                    # Chi tiết đặc tả schema Staging ([stg]), kiểu dữ liệu và ràng buộc
│   ├── stage_to_dw_mapping.md             # Phase 2: ánh xạ stg -> dw, OutcomeGroup, quy tắc measure F1
│   ├── status_outcome_mapping.csv         # Phase 2: phân nhóm 141 status (sinh bởi tests/phase2_expected_baseline.py)
│   ├── stg_status_outcome.sql             # Phase 2: SQL stg_status đầy đủ cho dbt (sinh tự động, đã test 141/141)
│   └── dw_data_dictionary.md              # Phase 2: từ điển dữ liệu schema dw (1 fact + 6 dim)
│
├── 03_data_quality_and_governance/        # Quản trị chất lượng dữ liệu và kiểm thử
│   ├── data_quality_rules.md              # Bộ quy tắc kiểm soát chất lượng (Completeness, Uniqueness, Validity)
│   └── phase1_checklist.md                # Bảng kiểm tra điều kiện nghiệm thu Phase 1 (ETL & Staging)
│
├── 04_operations_and_guides/              # Hướng dẫn vận hành, triển khai và Runbook
│   ├── sql_server_setup.md                # Cấu hình SQL Server, mạng TCP/IP, user và phân quyền
│   ├── etl_runbook.md                     # Hướng dẫn chi tiết vận hành pipeline Mage ETL (Full/Incremental/Rerun)
│   ├── mage_sqlserver_integration_contract.md # Giao ước kỹ thuật kết nối giữa Mage container và SQL Server
│   └── deploy_and_evidence_notes.md       # Ghi chú môi trường triển khai thực tế và tái lập kiểm thử
│
├── 05_reports/                           # Các phần báo cáo kỹ thuật theo phase
│   └── phase2_data_transformation_and_modeling.md  # Phase 2 (Lộc): bối cảnh, quy tắc chuyển đổi, đánh giá chất lượng
│
└── evidence/                              # Kho lưu trữ bằng chứng thực nghiệm (Logs, JSON test results)
    ├── README.md                          # Mục lục giải thích các file bằng chứng
    ├── loc_live_sqlserver_mage.json       # Kết quả chạy thực tế Mage -> SQL Server
    ├── loc_live_sqlserver_mage.log        # Log chi tiết quá trình nạp dữ liệu
    └── ...
```

---

## Hướng dẫn Đọc tài liệu theo Vai trò (Role-Based Reading Path)

### 1. Dành cho Ban Giảng viên / Đánh giá Đồ án
1. **Tổng quan kiến trúc:** Đọc [`01_architecture_and_design/architecture.md`](01_architecture_and_design/architecture.md).
2. **Mô hình chiều Kimball & Grain:** Đọc [`01_architecture_and_design/dimensional_model.md`](01_architecture_and_design/dimensional_model.md).
3. **Bằng chứng thực thi (Evidence):** Xem [`evidence/README.md`](evidence/README.md) và kết quả kiểm thử đối soát.
4. **Kế hoạch thực hiện theo thành viên:** Xem thư mục [`../plans/`](../plans/README.md).

### 2. Dành cho Data Engineer (Trực)
1. **Từ điển nguồn & Ánh xạ Staging:** Xem [`02_data_dictionary_and_mapping/source_to_stage_mapping.md`](02_data_dictionary_and_mapping/source_to_stage_mapping.md) và [`stage_schema.md`](02_data_dictionary_and_mapping/stage_schema.md).
2. **Vận hành Mage ETL:** Xem [`04_operations_and_guides/etl_runbook.md`](04_operations_and_guides/etl_runbook.md).
3. **Kế hoạch chuyển đổi dbt sang DW:** Xem [`../plans/phase2_dbt_dw/03_ke_hoach_truc_dbt_mage_etl.md`](../plans/phase2_dbt_dw/03_ke_hoach_truc_dbt_mage_etl.md).

### 3. Dành cho Database Administrator (Dũng)
1. **Thiết lập kết nối & DDL Staging:** Đọc [`04_operations_and_guides/sql_server_setup.md`](04_operations_and_guides/sql_server_setup.md).
2. **Kế hoạch Data Warehouse Schema (`dw`) & Indexing:** Xem [`../plans/phase2_dbt_dw/02_ke_hoach_dung_sqlserver_dw.md`](../plans/phase2_dbt_dw/02_ke_hoach_dung_sqlserver_dw.md).

### 4. Dành cho Business Analyst & Mapping Specialist (Lộc)
1. **Yêu cầu nghiệp vụ & Định nghĩa KPI:** Đọc [`01_architecture_and_design/business_requirements.md`](01_architecture_and_design/business_requirements.md).
2. **Kế hoạch Ánh xạ Chuyển đổi & Từ điển DW:** Xem [`../plans/phase2_dbt_dw/01_ke_hoach_loc_transformation_mapping.md`](../plans/phase2_dbt_dw/01_ke_hoach_loc_transformation_mapping.md).

### 5. Dành cho Kimball Architect & QA Acceptance (Phúc)
1. **Hợp đồng Mô hình Chiều:** Đọc [`01_architecture_and_design/dimensional_model.md`](01_architecture_and_design/dimensional_model.md).
2. **Kế hoạch Kiểm định Chất lượng & Tích hợp:** Xem [`../plans/phase2_dbt_dw/04_ke_hoach_phuc_dimensional_qa.md`](../plans/phase2_dbt_dw/04_ke_hoach_phuc_dimensional_qa.md).
