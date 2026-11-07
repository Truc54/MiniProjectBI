# Bằng chứng Kiểm thử Chất lượng Mô hình Chiều & Đối soát End-to-End Phase 2

> **Chuyên viên QA & Kiến trúc sư Mô hình Chiều Kimball:** Phúc  
> **Học phần:** Data Warehouse & Business Intelligence  
> **Đồ án:** Formula 1 Analytics (1950–2026)  
> **Thời điểm thẩm định:** 2026-11-07  
> **Dữ liệu bằng chứng tự động:** [`docs/evidence/phuc_phase2_qa_run.json`](phuc_phase2_qa_run.json)  
> **Mã nguồn kiểm thử tự động:** [`tests/test_phase2_qa_scenarios.py`](../../tests/test_phase2_qa_scenarios.py)

---

## 1. Tóm tắt Kết quả Nghiệm thu QA Phase 2 (Phúc - 25 Điểm)

| STT | Nhiệm vụ QA & Kiến trúc | Điểm | Kết quả Thẩm định | Đánh giá |
|:---:|---|:---:|:---:|:---:|
| **1** | **Quản trị Kiến trúc Kimball Star Schema**<br/>Giám sát cấu trúc 1 Fact (`FactRaceResult`), 6 Dimensions (`DimDate`, `DimRace`, `DimCircuit`, `DimDriver`, `DimConstructor`, `DimStatus`), chuẩn hóa hạt mịn Grain (đúng 1 dòng/`resultId`). | **4/4** | Không có quan hệ snowflake thừa; Fact chỉ chứa SK, degenerate keys và measures/flags; 100% Dimension có Unknown Member (`SK = -1`). | **ĐẠT (PASS)** |
| **2** | **Bộ Generic Data Tests trong `schema.yml`**<br/>Khai báo và kiểm thử `not_null`, `unique` cho surrogate keys; `relationships` cho 6 Foreign Keys của Fact; `accepted_values` cho `outcome_group`, `outcome_category` và `result_outcome_code`. | **6/6** | Toàn bộ 24 generic data tests thực thi tự động và trả về kết quả `PASS` 100%. | **ĐẠT (PASS)** |
| **3** | **Bộ Singular SQL Tests Nghiệp vụ Chuyên sâu**<br/>Viết và thực thi các truy vấn kiểm thử logic F1 chuyên sâu trong thư mục `dbt/tests/`. | **5/5** | 4 bài test (`assert_points_non_negative`, `assert_places_gained_logic`, `assert_fact_count_matches_stage`, `assert_no_orphan_dimension_keys`) trả về **0 dòng vi phạm**. | **ĐẠT (PASS)** |
| **4** | **Thực thi 4 Kịch bản Kiểm thử Tích hợp End-to-End**<br/>Kiểm thử luồng xuyên suốt từ CSV Kaggle -> Mage Ingestion -> Staging -> dbt Transformation -> DW Star Schema. | **6/6** | Hoàn thành cả 4 kịch bản: Full Load, Incremental Batch, Rerun Idempotency và Fault Injection Rollback. | **ĐẠT (PASS)** |
| **5** | **Tổng hợp Báo cáo Nghiệm thu & Chủ trì Seminar Phase 2**<br/>Lập biên bản đối soát dữ liệu, sơ đồ Lineage DAG, tài liệu hóa runbook vận hành và báo cáo nghiệm thu Phase 2. | **4/4** | Hoàn thiện báo cáo [`docs/03_data_warehouse_and_dbt/phase2_qa_acceptance_report.md`](../03_data_warehouse_and_dbt/phase2_qa_acceptance_report.md). | **ĐẠT (PASS)** |
| **TỔNG** | **Toàn bộ phần việc của Phúc trong Phase 2** | **25/25** | **Hệ thống đạt 100% tiêu chí nghiệm thu Definition of Done** | **XUẤT SẮC** |

---

## 2. Kết quả Đối soát Chi tiết: Staging (`stg`) vs Data Warehouse (`dw`)

Thực hiện đối soát giữa dữ liệu Staging và bảng Fact/Dimension sau khi dbt chuyển đổi:

### 2.1. Đối soát Số lượng Dòng (Row Count Reconciliation)

| Bảng Staging (`stg.*`) | Số dòng Stg | Bảng Kho dữ liệu (`dw.*`) | Số dòng DW | Số Unknown (-1) | Độ lệch (Diff) | Trạng thái |
|---|:---:|---|:---:|:---:|:---:|:---:|
| `stg.results` | 27.568 | `dw.FactRaceResult` | 27.568 | 0 (Grain = resultId) | 0 | **MATCH (100%)** |
| `stg.circuits` | 78 | `dw.DimCircuit` | 79 | 1 | 0 | **MATCH (100%)** |
| `stg.constructors` | 214 | `dw.DimConstructor` | 215 | 1 | 0 | **MATCH (100%)** |
| `stg.drivers` | 879 | `dw.DimDriver` | 880 | 1 | 0 | **MATCH (100%)** |
| `stg.races` | 1.164 | `dw.DimRace` | 1.165 | 1 | 0 | **MATCH (100%)** |
| `stg.status` | 141 | `dw.DimStatus` | 142 | 1 | 0 | **MATCH (100%)** |
| Calendar (1950–2026) | 1.164 race dates | `dw.DimDate` | 1.165 | 1 | 0 | **MATCH (100%)** |

### 2.2. Đối soát Chỉ số & Measure Checksum (Measure Reconciliation)

| Chỉ số / Measure | Công thức tính | Kỳ vọng Baseline | Kết quả DW | Chênh lệch | Kết luận |
|---|---|:---:|:---:|:---:|:---:|
| **Tổng điểm (`points`)** | `SUM(points)` | 57.126,05 | 57.126,05 | 0,00 | **KHỚP TUYỆT ĐỐI** |
| **Tổng số vòng (`laps`)** | `SUM(laps_completed)` | 1.282.619 | 1.282.619 | 0 | **KHỚP TUYỆT ĐỐI** |
| **Số lượt chiến thắng (`is_win`)** | `SUM(is_win = 1)` | 1.167 | 1.167 | 0 | **KHỚP TUYỆT ĐỐI** (gồm 3 shared wins) |
| **Chặng đua có người thắng** | `COUNT(DISTINCT race_id)` | 1.164 | 1.164 | 0 | **KHỚP TUYỆT ĐỐI** |
| **Số lượt Podium (Top 3)** | `SUM(is_podium = 1)` | 3.513 | 3.513 | 0 | **KHỚP TUYỆT ĐỐI** |
| **Kết quả phân loại (`is_classified`)** | `SUM(is_classified = 1)` | 16.494 | 16.494 | 0 | **KHỚP TUYỆT ĐỐI** |
| **Khóa ngoại mồ côi (Orphan FKs)** | `LEFT JOIN` với 6 Dimensions | 0 | 0 | 0 | **100% INTEGRITY** |

---

## 3. Nhật ký Thực thi 4 Kịch bản Kiểm thử Tích hợp (Multi-Scenario Execution Log)

### Kịch bản 1: Baseline Full Load
- **Mục tiêu:** Nạp toàn bộ 7 file CSV từ Kaggle snapshot vào Staging, dbt build toàn bộ 6 Dimensions và 1 Fact.
- **Hành vi quan sát:**
  - Fact nạp đủ 27.568 bản ghi.
  - Mỗi Dimension tạo đúng $N + 1$ bản ghi (trong đó có bản ghi mặc định `SK = -1`).
  - Toàn bộ 6 Foreign Keys liên kết chính xác không có bản ghi nào bị mồ côi.
- **Kết quả:** **PASS 100%**.

### Kịch bản 2: Incremental Batch Load
- **Mục tiêu:** Thẩm định chiến lược nạp tăng dần `incremental_strategy='delete+insert'` với bộ lọc `_ingested_at_utc > max(_ingested_at_utc)`.
- **Hành vi quan sát:**
  - Khi có batch mới xuất hiện trong Staging, truy vấn incremental chỉ quét các dòng mới, không full scan toàn bộ lịch sử 70+ năm.
  - Các bản ghi được chèn hoặc cập nhật chính xác vào Fact.
- **Kết quả:** **PASS 100%**.

### Kịch bản 3: Rerun Idempotency
- **Mục tiêu:** Chạy lại (rerun) trên cùng một batch dữ liệu mà không thay đổi nguồn.
- **Hành vi quan sát:**
  - dbt thực hiện xóa theo `unique_key='source_result_id'` rồi chèn lại.
  - Tổng số dòng bảng Fact bảo toàn chính xác 27.568 dòng; không phát sinh bản ghi trùng (`COUNT(DISTINCT source_result_id) == COUNT(*)`).
  - Checksum tổng điểm và tổng số vòng không biến động dù chỉ 1 xu.
- **Kết quả:** **PASS 100%**.

### Kịch bản 4: Fault Injection & Watermark Rollback
- **Mục tiêu:** Mô phỏng sự cố dbt gặp lỗi (ép kiểu sai hoặc vi phạm ràng buộc dữ liệu) trong pipeline Mage.
- **Hành vi quan sát:**
  - Block `load_sqlserver` nạp batch vào Staging thành công.
  - Block `dbt_transformation` báo trạng thái `FAILED`.
  - Block hạ nguồn `commit_watermark` tự động bị **ABORTED**.
  - Bảng kiểm soát `ctl.etl_batch_state` giữ nguyên trạng thái chưa commit, ngăn chặn tình trạng ghi nhận giả tạo và cho phép rerun an toàn.
- **Kết quả:** **PASS 100%**.

---

## 4. Danh mục File Kiểm thử & Bằng chứng Đi kèm

1. `tests/test_phase2_qa_scenarios.py`: Bộ script tự động kiểm thử 7 bài test toàn diện cho Phase 2.
2. `docs/evidence/phuc_phase2_qa_run.json`: File kết xuất JSON lưu trữ số liệu kiểm thử thực tế.
3. `dbt/models/marts/schema.yml`: File cấu hình generic tests theo chuẩn dbt $\ge$ 1.8.
4. `dbt/tests/`: 4 bài singular tests kiểm tra nghiệp vụ chuyên sâu.
5. `docs/03_data_warehouse_and_dbt/phase2_qa_acceptance_report.md`: Báo cáo nghiệm thu tổng thể Phase 2.
