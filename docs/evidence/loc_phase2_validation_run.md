# Evidence Phase 2 của Lộc: kiểm thử đặc tả mapping (06/11/2026)

**Môi trường:** SQL Server 2022 Developer `16.0.4305.5` (Docker local), database `F1_BI`. Schema `stg` đã nạp đủ bằng ETL Phase 1 (27.568 dòng `stg.results`). Python 3 + pandas.

**Phạm vi:** chỉ kiểm thử sản phẩm của Lộc (mapping, `OutcomeGroup`, quy tắc measure, từ điển dữ liệu, script đối soát). Tại thời điểm chạy, dbt models của Trực **chưa có** trên bất kỳ nhánh nào. Để chạy thử đặc tả, Lộc dựng tạm một bản DW bằng T-SQL theo đúng [`stage_to_dw_mapping.md`](../02_data_dictionary_and_mapping/stage_to_dw_mapping.md) trong schema riêng `loc_ref`, không đụng vào `dw`. Bản dựng tạm này **không** thay thế dbt models và không được commit. Khi Trực có `dbt build`, cần chạy lại `loc_semantic_validation.sql` trên `dw` thật.

| # | Kiểm thử | Kết quả | File |
|---|---|---|---|
| 1 | `python3 tests/phase2_expected_baseline.py` sinh lại CSV, SQL, JSON | CSV giống hệt bản trước. 77/77 mùa giải đúng thang điểm kỷ nguyên (`points_eras.seasons_violating = []`) | [`loc_phase2_expected_baseline.json`](loc_phase2_expected_baseline.json) |
| 2 | `python3 -m unittest tests.test_phase2_mapping -v` | **17/17 pass**. CSV ↔ bộ phân loại ↔ SQL sinh ra ↔ JSON ↔ hai tài liệu Markdown nhất quán | [`loc_phase2_unit_tests.txt`](loc_phase2_unit_tests.txt) |
| 3 | Chạy [`stg_status_outcome.sql`](../02_data_dictionary_and_mapping/stg_status_outcome.sql) trên `stg.status` thật | **141/141** dòng khớp `status_outcome_mapping.csv` (nhãn, `outcome_group`, `outcome_category`), 0 sai lệch | — |
| 4 | `loc_semantic_validation.sql` trên bản dựng tạm `loc_ref` | **43/43 PASS**. Dòng mẫu `resultId = 1`: Lewis Hamilton / McLaren / 2008 R01 Australian Grand Prix / Finished / 10 điểm | [`loc_phase2_semantic_validation.txt`](loc_phase2_semantic_validation.txt) |
| 5 | Kiểm thử âm: cố ý làm hỏng 8 chỗ rồi chạy lại script | **18 check FAIL, bắt đủ 8/8 lỗi**: lệch điểm (3, 33), sai nhóm status (36, 38), sai FK (14, 18, 33), mất dòng (1, 2, 4, 8, 31), sai `places_gained` (11, 34), trùng dòng `-1` (23, 40), chuỗi chưa TRIM (29), sai thang điểm (43). Sau đó dựng lại bản sạch → 43/43 PASS | — |
| 6 | `loc_semantic_validation.sql` trên `dw` hiện có trong container (bản build cũ từ phiên kiểm thử trước, không phải code của Trực) | 43/43 PASS | — |

**Chưa kiểm thử được (phụ thuộc thành viên khác):**
- `dbt build --select +fact_race_result` trên dbt models thật của Trực.
- Script của Dũng dùng tên cột PascalCase, còn đặc tả dùng `snake_case`. Nhóm cần chốt quy ước (mục 10 tài liệu mapping) thì `loc_semantic_validation.sql` mới chạy được trên DW cuối cùng.
