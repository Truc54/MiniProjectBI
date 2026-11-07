# Kế hoạch Tổng quát MiniProject BI - Phase 2: dbt Transformation & Data Warehouse

**Học phần:** Data Warehouse & Business Intelligence  
**Đồ án:** Formula 1 Analytics (1950–2026)  
**Nhóm sinh viên:** Phúc, Dũng, Lộc, Trực  
**Phạm vi Phase 2:** Chuyển đổi dữ liệu từ Stage sang Data Warehouse (`stg` -> `dw`) bằng dbt Core, tối ưu hóa vật lý DW trên SQL Server, điều phối tự động qua Mage và kiểm định chất lượng đối soát.

---

## 1. Bối cảnh & Ranh giới Phase 2

### 1.1. Kế thừa từ Phase 1 (Đã hoàn thành)
- 7 bảng dữ liệu CSV lõi (`circuits`, `constructors`, `drivers`, `status`, `seasons`, `races`, `results` - hơn 30.000 dòng) đã được nạp thành công và kiểm định chặt chẽ vào SQL Server schema `stg`.
- Hệ thống theo dõi trạng thái batch và audit log đã hoạt động trong schema `ctl`.
- Thiết kế mô hình chiều Kimball đã được định hình tại [`docs/01_architecture_and_design/dimensional_model.md`](../../docs/01_architecture_and_design/dimensional_model.md).

### 1.2. Trọng tâm của Phase 2 (Data Transformation & Warehouse Implementation)
> **Lưu ý về phạm vi:** Phase 2 tập trung hoàn toàn vào tầng **Data Transformation (dbt) & Data Warehouse (SQL Server `dw`)**. Các công việc trực quan hóa Power BI thuộc giai đoạn sau.

Mục tiêu chính của Phase 2:
1. **Áp dụng dbt Core (`dbt-sqlserver`):**
   - Xây dựng tầng Staging (`models/staging/`): tạo các view làm sạch, ép kiểu (CAST), loại khoảng trắng thừa (TRIM), chuẩn hóa các trường dữ liệu và phân nhóm trạng thái nghiệp vụ `OutcomeGroup`.
   - Xây dựng tầng Marts (`models/marts/`): hiện thực hóa mô hình Kimball Star Schema gồm 1 Fact (`fact_race_result`) và 6 Dimensions (`dim_date`, `dim_race`, `dim_circuit`, `dim_driver`, `dim_constructor`, `dim_status`).
   - Cấu hình chiến lược nạp tăng dần (Incremental loading: `delete+insert`, `unique_key='source_result_id'`) cho bảng Fact.
   - Sử dụng macro `generate_schema_name.sql` để ghi chuẩn xác vào schema `dw` và `stg_clean`.
2. **Triển khai Vật lý Kho dữ liệu trên SQL Server:**
   - Cấu hình schema `dw`, bảo mật và phân quyền tài khoản.
   - Áp dụng **Clustered Columnstore Index (CCI)** cho bảng Fact nhằm tối ưu hiệu năng nén và tăng tốc truy vấn phân tích.
   - Tạo bản ghi mặc định **Unknown Member (`SK = -1`)** cho tất cả các chiều để đảm bảo tính toàn vẹn tham chiếu.
3. **Điều phối Tự động qua Mage Pipeline (Mage Orchestration):**
   - Tích hợp **DBT Model block** trong pipeline của Mage sau bước nạp Staging (`load_stage`).
   - Cấu hình selector `--select +fact_race_result` để tự động hóa chu trình biến đổi toàn bộ cây quan hệ phụ thuộc.
   - Thiết lập cơ chế kiểm soát: commit watermark trong `ctl` chỉ chạy sau khi dbt hoàn tất thành công.
4. **Kiểm thử Chất lượng Dữ liệu & Đối soát (Data Quality & Reconciliation):**
   - Bộ kiểm thử tự động `dbt test` (not_null, unique, relationships, accepted_values) và singular SQL tests.
   - Bộ truy vấn SQL đối soát số lượng dòng, checksum điểm số giữa `stg` và `dw`.

```text
[KIẾN TRÚC LUỒNG DỮ LIỆU PHASE 2]

SQL Server [stg]                 dbt Transformation                SQL Server [dw]
┌──────────────────┐         ┌──────────────────────────┐       ┌──────────────────────┐
│  stg.circuits    │         │  models/staging/         │       │  dw.DimCircuit       │
│  stg.constructors│ ──────> │   stg_circuits.sql       │ ────> │  dw.DimConstructor   │
│  stg.drivers     │ (views) │   stg_constructors.sql   │(table/│  dw.DimDriver        │
│  stg.status      │         │   stg_status.sql...      │increm)│  dw.DimStatus        │
│  stg.seasons     │         └─────────────┬────────────┘       │  dw.DimRace          │
│  stg.races       │                       │                    │  dw.DimDate          │
│  stg.results     │                models/marts/               │  dw.FactRaceResult   │
└──────────────────┘                 dim_*.sql                  │  (Columnstore Index) │
                                     fact_race_result.sql       └──────────────────────┘
                                           │                               ▲
                                           ▼                               │
                                   dbt Data Tests &                 Reconciliation
                                   Lineage/Docs                     Queries Verify
```

---

## 2. Phân công Công việc Cân bằng (25 điểm / thành viên)

Mỗi thành viên đảm nhận đúng **25 điểm tải công việc**, phân chia độc lập nhưng kết nối qua các interface rõ ràng:

| Thành viên | Vai trò Phase 2 | Nhiệm vụ chính | File kế hoạch chi tiết | Điểm |
|---|---|---|---|:---:|
| **Lộc** | Transformation Mapping & Semantic QA | Xác định chi tiết logic chuyển đổi từ `stg` sang `dw` (phân loại 141 mã status thành 5 nhóm `OutcomeGroup`, quy tắc xử lý điểm số các thời kỳ F1), xây dựng từ điển dữ liệu DW và soạn thảo tài liệu Phase 2. | [`01_ke_hoach_loc_transformation_mapping.md`](01_ke_hoach_loc_transformation_mapping.md) | **25** |
| **Dũng** | SQL Server DBA & Physical DW | Quản trị schema `dw` trên SQL Server, cấp phát quyền, áp dụng Clustered Columnstore Index (CCI) cho Fact, seed bản ghi Unknown (`-1`) cho các chiều, viết script SQL đối soát toàn diện (`stg` vs `dw`). | [`02_ke_hoach_dung_sqlserver_dw.md`](02_ke_hoach_dung_sqlserver_dw.md) | **25** |
| **Trực** | Data Engineer & dbt-Mage Orchestration | Xây dựng dbt project (`dbt_project.yml`, `profiles.yml`, `macros`), lập trình 7 Staging models (`view`), 6 Dimension models (`table`) và 1 Fact model (`incremental`). Tích hợp DBT Model block vào pipeline Mage. | [`03_ke_hoach_truc_dbt_mage_etl.md`](03_ke_hoach_truc_dbt_mage_etl.md) | **25** |
| **Phúc** | Kimball Architecture & QA Lead | Giám sát kiến trúc Star Schema (Grain 1 dòng/`resultId`), thiết lập bộ `dbt test` (generic tests + singular tests), thiết kế kịch bản thử nghiệm nạp tăng dần (Incremental/Rerun/Rollback) và nghiệm thu Phase 2. | [`04_ke_hoach_phuc_dimensional_qa.md`](04_ke_hoach_phuc_dimensional_qa.md) | **25** |

---

## 3. Lộ trình Thực hiện & Các Mốc Bàn giao (Timeline)

| Mốc thời gian | Trọng tâm công việc | Đầu ra bắt buộc | Người phụ trách chính |
|---|---|---|---|
| **Mốc 1 (26/10 – 28/10)** | - Lộc chốt bảng đặc tả mapping chi tiết từ `stg` sang `dw`<br/>- Trực dựng môi trường dbt Core, macro `generate_schema_name`, `sources.yml`<br/>- Dũng chuẩn bị schema `dw` trên SQL Server | Bảng mapping chốt; `dbt debug` kết nối thành công | Lộc, Trực, Dũng |
| **Mốc 2 (29/10 – 31/10)** | - Trực viết 7 Staging views và 6 Dimension models<br/>- Dũng seed bản ghi Unknown (`SK = -1`) cho 6 chiều<br/>- Trực hoàn thành `fact_race_result.sql` với incremental `delete+insert` | `dbt run --select staging marts` thành công trên SQL Server | Trực, Dũng |
| **Mốc 3 (01/11 – 02/11)** | - Dũng tạo Clustered Columnstore Index cho bảng Fact<br/>- Phúc cấu hình toàn bộ `schema.yml` (tests) và singular SQL tests<br/>- Trực tích hợp DBT Model block vào Mage pipeline | `dbt test` PASS 100%; Pipeline Mage kích hoạt dbt tự động | Phúc, Trực, Dũng |
| **Mốc 4 (03/11 – 04/11)** | - Thử nghiệm nạp Batch ban đầu và Batch kế tiếp qua Mage + dbt<br/>- Dũng & Phúc chạy bộ script đối soát số liệu (`stg` vs `dw`)<br/>- Lộc hoàn thiện Data Dictionary và thẩm định số liệu | Bằng chứng chạy nạp thành công (Logs/Evidence JSON) | Cả nhóm |
| **Mốc 5 (05/11 trước 23:00)** | - Rà soát chéo toàn bộ hệ thống, freeze code dbt và DDL<br/>- Tổng hợp báo cáo kỹ thuật Phase 2 và sẵn sàng bảo vệ Seminar | Báo cáo Phase 2 hoàn chỉnh & mã nguồn sẵn sàng | Cả nhóm (Phúc & Trực điều phối) |

---

## 4. Tiêu chí Nghiệm thu Phase 2 (Definition of Done)

- [x] Lệnh `dbt build --select +fact_race_result` chạy trơn tru, không phát sinh lỗi trên SQL Server.
- [x] Bảng Fact `dw.FactRaceResult` đạt chuẩn Grain 1 dòng cho mỗi `resultId` (không có duplicate key).
- [x] 100% Foreign Keys trong Fact liên kết hợp lệ với 6 Dimension (không có orphan key, trường hợp thiếu trỏ về `SK = -1`).
- [x] Bảng Fact được đánh Clustered Columnstore Index (CCI).
- [x] Bộ `dbt test` kiểm tra not_null, unique, relationships và accepted_values đạt kết quả `PASS` 100%.
- [x] Khối DBT Model block trong Mage pipeline thực thi tuần tự sau khi nạp Stage và chặn commit watermark nếu dbt thất bại.
- [x] Chạy lại (rerun) trên cùng một batch không làm nhân đôi số dòng trong Fact (idempotent).
- [x] Số dòng và tổng điểm số giữa `stg.results` và `dw.FactRaceResult` đối khớp chính xác 100%.
