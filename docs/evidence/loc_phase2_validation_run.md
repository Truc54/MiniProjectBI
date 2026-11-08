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

**Chưa kiểm thử được tại thời điểm 06/11 (phụ thuộc thành viên khác):**
- `dbt build --select +fact_race_result` trên dbt models thật của Trực.
- Script của Dũng dùng tên cột PascalCase, còn đặc tả dùng `snake_case`. Nhóm cần chốt quy ước (mục 10 tài liệu mapping) thì `loc_semantic_validation.sql` mới chạy được trên DW cuối cùng.

## Chạy lại trên `dw` thật do dbt tạo (08/11/2026)

Sau khi dbt models của Trực được merge (PR #10), Lộc chạy lại phần thẩm định trên `dw` do chính dbt tạo ra. Model dbt dùng tên bảng PascalCase (`alias`) và tên cột `snake_case` đúng như đặc tả, nên `loc_semantic_validation.sql` chạy được mà không phải sửa.

**Môi trường:** SQL Server 2022 Developer `16.0.4305.5` (Docker local), database `F1_BI`, `stg` giữ nguyên dữ liệu Phase 1 (27.568 dòng `stg.results`). dbt-core 1.8.7 + dbt-sqlserver 1.8.7, chạy trong image Mage của dự án.

| # | Kiểm thử | Kết quả | File |
|---|---|---|---|
| 7 | `dbt build --select +fact_race_result --full-refresh` | **PASS=61, ERROR=0**: 7 view `stg_clean`, 6 dim + `dw.FactRaceResult`, toàn bộ generic và singular tests | [`loc_phase2_dbt_build.log`](loc_phase2_dbt_build.log) |
| 8 | `loc_semantic_validation.sql` trên `dw` vừa build | **43/43 PASS**. Dòng mẫu `resultId = 1` giống hệt bản dựng tạm ngày 06/11 | [`loc_phase2_dw_semantic_validation.txt`](loc_phase2_dw_semantic_validation.txt) |
| 9 | `dbt build` lần 2 (incremental, không `--full-refresh`) rồi chạy lại script | PASS=61; **43/43 PASS**, fact vẫn 27.568 dòng (rerun không nhân đôi) | như trên |
| 10 | So `dw.DimStatus` với `status_outcome_mapping.csv` | **141/141** dòng khớp (`status`, `outcome_group`, `outcome_category`), 0 sai lệch | — |
| 11 | `python3 -m unittest tests.test_phase2_mapping` | 17/17 pass | — |

**Kết luận:** dữ liệu trong `dw` do dbt tạo khớp 100% với đặc tả mapping và với `stg`. Phần thẩm định (nhiệm vụ 5) của Lộc đã hoàn tất.

**Ghi chú cho nhóm (ngoài phạm vi của Lộc, phát hiện khi chạy):**
- Image Mage hiện tại có sẵn `dbt-sqlserver 1.8.4` từ image gốc `mageai`, không tương thích `dbt-fabric 1.8.9` (`ImportError: get_pyodbc_attrs_before`). Vì `mage/requirements.txt` ghi `dbt-sqlserver>=1.8.0,<1.9.0` nên pip không nâng cấp. Lộc chạy bằng image tạm có nâng lên `dbt-sqlserver 1.8.7`. Đề xuất sửa thành `>=1.8.7,<1.9.0` rồi build lại image.
- `02_seed_unknown_members.sql`, `03_apply_columnstore_indexes.sql` (index trên `DimDate`) và `dw_reconciliation_queries.sql` của Dũng vẫn dùng cột PascalCase (`DateSK`, `RaceSK`, `FullDate`), không khớp với bảng dbt tạo ra (`date_sk`, `race_sk`, `full_date`).
- Sau `--full-refresh`, `dw.FactRaceResult` vẫn có Clustered Columnstore Index vì `dbt-sqlserver` mặc định tạo CCI khi tạo bảng (`as_columnstore`), nên không cần chạy lại script CCI của Dũng cho bảng fact.
