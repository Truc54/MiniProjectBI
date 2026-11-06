# Kế hoạch Cá nhân Phase 2: Quản trị Mô hình Chiều & Kiểm thử Tích hợp (QA)

**Thành viên:** Phúc  
**Vai trò:** Kimball Dimensional Architect & End-to-End QA Specialist  
**Điểm tải công việc:** **25 điểm**  
**Thời hạn hoàn thành:** Mốc từng phần từ 28/10 đến 04/11/2026; nghiệm thu trước 23:00 ngày 05/11/2026  
**Phối hợp với:** Lộc (nghiệm thu ngữ nghĩa nghiệp vụ), Dũng (phối hợp kiểm thử đối soát DB), Trực (tích hợp bộ test vào dbt & Mage)

---

## 1. Mục tiêu & Trách nhiệm của Phúc trong Phase 2

Ở Phase 2, nhiệm vụ của Phúc là đảm bảo toàn bộ kho dữ liệu vật lý được dbt tạo ra tuân thủ tuyệt đối các nguyên tắc thiết kế chiều Kimball, đạt độ tin cậy 100% qua bộ kiểm thử tự động và hoàn thành nghiệm thu tích hợp end-to-end:
1. **Quản trị Kiến trúc Mô hình Chiều Kimball (Star Schema Governance):** Giám sát chặt chẽ cấu trúc 1 Fact (`FactRaceResult`) và 6 Dimensions (`DimDate`, `DimRace`, `DimCircuit`, `DimDriver`, `DimConstructor`, `DimStatus`), kiểm soát hạt mịn (Grain: đúng 1 dòng cho mỗi `resultId`).
2. **Thiết lập Bộ Kiểm thử Dữ liệu Tự động (dbt Data Tests Suite):**
   - Soạn thảo `models/marts/schema.yml` theo chuẩn dbt $\ge$ 1.8 sử dụng khóa `data_tests`: kiểm tra `not_null`, `unique`, `relationships` (100% tính toàn vẹn khóa ngoại) và `accepted_values`.
   - Viết các bài **Singular SQL Tests** trong thư mục `dbt/tests/` để kiểm tra các ràng buộc nghiệp vụ F1 chuyên sâu.
3. **Thực thi Kịch bản Kiểm thử Đa tầng (Multi-Scenario Testing):**
   - Kịch bản nạp ban đầu (Full/Baseline batch).
   - Kịch bản nạp tăng dần (Incremental batch).
   - Kịch bản chạy lại bảo toàn dữ liệu (Rerun idempotency).
   - Kịch bản mô phỏng sự cố dbt để xác nhận watermark không bị commit sai lệch.
4. **Điều phối Nghiệm thu Toàn diện Phase 2:** Kết hợp bộ script đối soát của Dũng, logic của Lộc và pipeline của Trực để hoàn tất biên bản nghiệm thu trước khi bước sang giai đoạn tiếp theo.

---

## 2. Phân rã Công việc & Điểm số (25 Điểm)

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí nghiệm thu |
|:---:|---|:---:|:---:|---|
| **1** | **Rà soát & Duyệt Cấu trúc dbt Models theo Chuẩn Kimball**<br/>Kiểm tra code các file `models/marts/*.sql` của Trực; đảm bảo không có quan hệ bắc cầu dạng snowflake không cần thiết, Fact chỉ chứa Foreign Keys và Measures. | **4** | 29/10 | Toàn bộ 6 Dimension và 1 Fact thỏa mãn hợp đồng kiến trúc tại `docs/01_architecture_and_design/dimensional_model.md`. |
| **2** | **Xây dựng Bộ Generic Data Tests trong `schema.yml`**<br/>Khai báo test `not_null` & `unique` cho tất cả các khóa đại diện/khóa tự nhiên; khai báo test `relationships` cho 6 Foreign Keys của Fact; test `accepted_values` cho `outcome_group`. | **6** | 01/11 | Lệnh `dbt test --select marts` thực thi tự động, kiểm tra hơn 20 ràng buộc toàn vẹn và trả về kết quả `PASS` 100%. |
| **3** | **Viết & Thực thi Bộ Singular SQL Tests (`tests/`)**<br/>Viết `assert_points_non_negative.sql`, `assert_places_gained_logic.sql`, `assert_fact_count_matches_stage.sql` để phát hiện dữ liệu bất thường. | **5** | 02/11 | Các truy vấn Singular SQL test trả về 0 dòng vi phạm khi chạy `dbt test --select test_type:singular`. |
| **4** | **Thực thi 4 Kịch bản Kiểm thử Tích hợp End-to-End**<br/>Chạy luồng xuyên suốt từ CSV Kaggle -> Mage -> Stage SQL Server -> dbt Transformation -> DW SQL Server: kiểm thử nạp mới, nạp nối tiếp, chạy lại và mô phỏng lỗi rollback. | **6** | 04/11 | Có nhật ký kiểm thử và file bằng chứng ghi nhận đầy đủ 4 kịch bản, chứng minh hệ thống hoạt động ổn định và bền vững. |
| **5** | **Tổng hợp Báo cáo Nghiệm thu & Chủ trì Seminar Phase 2**<br/>Rà soát chất lượng tổng thể tài liệu dự án, xuất bản sơ đồ Lineage DAG bằng `dbt docs generate`, chuẩn bị nội dung thuyết trình Seminar Phase 2. | **4** | 05/11 | Báo cáo hoàn chỉnh, sơ đồ phụ thuộc DAG rõ ràng, sẵn sàng bàn giao toàn bộ sản phẩm Phase 2. |

---

## 3. Chi tiết Bộ Kiểm thử Chất lượng Dữ liệu (dbt Data Tests)

### 3.1. Ràng buộc Toàn vẹn Khóa ngoại trong `models/marts/schema.yml`
Fact liên kết với 6 Dimension qua các khóa đại diện. Kiểm thử `relationships` đảm bảo **100% không có khóa ngoại mồ côi**:
```yaml
models:
  - name: fact_race_result
    columns:
      - name: source_result_id
        data_tests:
          - not_null
          - unique
      - name: driver_sk
        data_tests:
          - not_null
          - relationships:
              to: ref('dim_driver')
              field: driver_sk
      - name: constructor_sk
        data_tests:
          - not_null
          - relationships:
              to: ref('dim_constructor')
              field: constructor_sk
      - name: race_sk
        data_tests:
          - not_null
          - relationships:
              to: ref('dim_race')
              field: race_sk
      - name: status_sk
        data_tests:
          - not_null
          - relationships:
              to: ref('dim_status')
              field: status_sk
```

### 3.2. Singular Tests Kiểm tra Ràng buộc Nghiệp vụ
1. **Kiểm tra điểm không âm (`dbt/tests/assert_points_non_negative.sql`):**
   ```sql
   select source_result_id, points
   from {{ ref('fact_race_result') }}
   where points < 0;
   ```
2. **Kiểm tra tính nhất quán vị trí vượt (`dbt/tests/assert_places_gained_logic.sql`):**
   ```sql
   select source_result_id, grid_position, finish_position, places_gained
   from {{ ref('fact_race_result') }}
   where grid_position > 0 
     and finish_position is not null 
     and places_gained != (grid_position - finish_position);
   ```

---

## 4. Kịch bản Thử nghiệm Bền bỉ & An toàn Giao dịch (Fault Tolerance)

Phúc thiết kế và trực tiếp giám sát kịch bản **Kiểm thử Ngắt quãng (Fault Injection Test)**:
1. Cố tình đưa dữ liệu lỗi vào dbt model (ví dụ ép kiểu sai hoặc sinh trùng khóa).
2. Chạy pipeline Mage `f1_source_to_stage`.
3. **Quan sát hành vi:**
   - Block `load_sqlserver` nạp xong dữ liệu vào `stg.results`.
   - Block `dbt_transformation` thực thi và báo lỗi `FAILED`.
   - Block `commit_watermark` **bị hủy (ABORTED)** và không cập nhật mốc batch mới vào `ctl.etl_batch_state`.
4. **Kết luận nghiệm thu:** Chứng minh được chu trình điều phối bảo vệ an toàn dữ liệu, cho phép sửa lỗi và rerun lại batch mà không mất dấu lịch sử nạp.

---

## 5. Các Giao diện Phối hợp & Bàn giao

- **Phối hợp với Trực:** Tích hợp các file test YAML và SQL vào dbt project; cùng kiểm tra log thực thi trên Mage container.
- **Phối hợp với Dũng:** Sử dụng bộ truy vấn đối soát `dw_reconciliation_queries.sql` của Dũng để kiểm chứng chéo với kết quả của `dbt test`.
- **Phối hợp với Lộc:** Kiểm tra bộ từ điển dữ liệu của Lộc để đảm bảo mô tả trong tài liệu khớp 100% với tên cột và kiểu dữ liệu trong dbt models.
