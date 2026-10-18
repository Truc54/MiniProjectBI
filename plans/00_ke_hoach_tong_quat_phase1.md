# Kế hoạch tổng quát MiniProjectBI - Phase 1

**Nhóm:** Phúc, Dũng, Lộc, Trực  
**Mốc Phase 1:** Seminar 1 - ETL, 23:00 ngày 25/10/2026 (theo lịch nhóm gửi)  
**Mục tiêu:** có một luồng có thể chạy lại từ CSV Kaggle -> Mage -> Staging trên SQL Server; có kiểm tra chất lượng, Full/Incremental Load, log và bằng chứng; đồng thời chốt thiết kế dimensional để Phase 2 có thể tiếp tục mà không đổi grain tùy tiện.

## 1. Bối cảnh và phạm vi

Nguồn hiện có tại `dataset/` là Formula 1 World Championship 1950-2026, gồm 17 CSV. Mô tả, nguồn, license và schema cột nằm trong `dataset/README.md` và `dataset/SCHEMA.md`; Kaggle: https://www.kaggle.com/datasets/atharvranjan/formula-1-world-championship-1950-present. Profile trên bản local ngày 18/10/2026 ghi nhận 754,398 dòng trên cả 17 CSV.

Phase 1 nạp bảy bảng lõi vào Staging: `results`, `races`, `drivers`, `constructors`, `circuits`, `status`, `seasons` (30,121 dòng theo snapshot hiện tại). Chúng đủ để phân tích kết quả một tay đua trong một chặng theo mùa giải, race, circuit, driver, constructor và outcome. Mười bảng còn lại phải được profile và ghi quyết định phạm vi; chỉ nạp thêm khi có câu hỏi phân tích yêu cầu. `lap_times.csv` riêng có 632,937 dòng và grain lap, nên không trộn vào fact kết quả đua.

`\N` là null marker của nguồn. Đây là giá trị thiếu hợp lệ ở nhiều cột, chẳng hạn `results.position`, fastest-lap/time fields, session schedule, và Q2/Q3. Nạp thành SQL NULL; không đổi thành 0, không xóa dòng chỉ vì một measure tùy chọn thiếu. Profile chi tiết ở `docs/source_profile.md`.

## 2. Vai trò Phase 1 và ranh giới với các phase sau

- **Phase 1 - ETL và thiết kế:** profile dataset; chốt quy trình nghiệp vụ/câu hỏi; thiết kế target Fact/Dimensions; tạo SQL Server Staging/control schemas; hoàn thiện Mage source-to-stage; chứng minh kiểm tra chất lượng, full/incremental, logging và rerun. Ở phase này, dimensional model được thiết kế rõ grain và measures; dbt vẫn là công việc triển khai chuyển đổi Staging -> DW của Phase 2.
- **Phase 2 - Dashboard & Report, 23:00 ngày 05/11/2026:** hoàn thiện dbt clean/standardize/integrate, tests, dependencies và docs; triển khai star schema trên SQL Server, nạp DW bằng dbt; xây Power BI Semantic Model, relationships, DAX measures, hierarchies; xây tối thiểu hai dashboard Overview và Detailed/Diagnostic; hoàn tất report PDF.
- **Phase 3 - Bonus, 23:00 ngày 14/11/2026:** tích hợp Generative AI. Đề ghi AI-generated summary và giải thích thay đổi là yêu cầu tối thiểu ở mục 3.5; vì vậy nhóm đưa chúng vào bản bàn giao cuối. Natural-language question/query là phần được khuyến khích. Tên seminar “Bonus” không làm mất yêu cầu viết trong đề, trừ khi giảng viên xác nhận khác.

## 3. Phân công cân bằng Phase 1

Mỗi người nhận **25 điểm tải công việc**. Điểm là cách cân bằng phạm vi và trách nhiệm, không phải điểm môn học.

| Thành viên | Vai trò chính | Phần việc | Điểm |
|---|---|---|---:|
| Phúc | Data source & profiling | Provenance/Kaggle, profile 17 CSV, source contract, mapping và xác nhận các trường thiếu dữ liệu | 25 |
| Dũng | SQL Server staging | Schema/db connection, DDL bảy bảng Stage và control tables, SQL contract/query đối soát | 25 |
| Lộc | Mage ETL | Loader, validation, exporter, full/incremental, rerun idempotent, log và runbook | 25 |
| Trực | Dimensional design & QA | Business process/grain, star schema một fact, KPIs/câu hỏi, quality acceptance, tích hợp/evidence | 25 |

Chi tiết việc, điểm thành phần, thời hạn và tiêu chí nghiệm thu nằm trong bốn file kế hoạch cá nhân cùng thư mục.

## 4. Làm song song và các giao diện chung

| Giao diện | Chốt bởi | Người dùng | Thời điểm |
|---|---|---|---|
| Danh sách bảy CSV lõi, file/key/cột và cách hiểu NULL | Phúc | Dũng, Lộc, Trực | Bản đầu 19/10; sửa đổi phải ghi lại |
| Quy ước schema/bảng/cột SQL Server | Dũng + Phúc | Lộc, Trực | Draft 20/10; chốt 21/10 |
| Quy ước batch: source file + table + batch key + mode | Lộc + Dũng | Phúc, Trực | 21/10 |
| Grain/Fact/Dimension và KPI semantics | Trực + Phúc | Dũng, Lộc | Draft 20/10; chốt 22/10 |
| SQL query nghiệm thu và bằng chứng chạy | Trực + Dũng | Cả nhóm | 23-25/10 |

Phúc profile dữ liệu; Dũng viết DDL; Lộc xây Mage blocks với `file_name`/`target_table`; Trực vẽ star schema và định nghĩa KPI. Cả bốn có thể bắt đầu ngay từ `dataset/SCHEMA.md` và các file hiện có. Tích hợp thật vào SQL Server cần DDL + kết nối, nhưng không chặn việc profile, code loader/validation, thiết kế fact hay viết SQL kiểm tra chạy song song.

## 5. Cách chứng minh Full/Incremental và chạy lại

1. **Full Load:** nạp toàn bộ bảy file đã chốt; so số dòng và khóa Stage với baseline source. Chạy lại Full Load trên cùng snapshot; số dòng và tập khóa phải giữ nguyên.
2. **Incremental Load cho nguồn tĩnh:** chia mỗi file thành các batch xác định, lặp lại được theo natural key hoặc thứ tự khóa đã profile. Nạp batch 1 rồi batch 2; kiểm tra tập khóa. Chạy lại batch 2; không tăng số dòng và không tạo natural key trùng.
3. **Logging:** mỗi lần chạy có run ID, file/bảng, batch, mode, trạng thái, start/end, rows read/written/rejected và error message. Chỉ ghi batch thành công sau khi ghi SQL hoàn tất; lỗi không đánh dấu batch thành công.
4. **Quality evidence:** truy vấn chứng minh key không NULL/trùng, FK hợp lệ sau khi đủ bảng, số dòng source/stage khớp, batch state và run log đúng.

## 6. Mốc Phase 1

| Ngày | Mốc / kết quả |
|---|---|
| 18-19/10 | Kickoff; đọc requirements; Phúc đóng source contract bản 1; các thành viên bắt đầu phần việc độc lập |
| 20-21/10 | Chốt mapping/model/DDL interfaces; có DDL draft và Mage local blocks |
| 22-23/10 | Nối Mage với SQL Server; full load; kiểm tra schema, keys, FK, counts và logs |
| 24/10 | Incremental batch, rerun cùng batch, xử lý lỗi, hoàn thiện evidence/runbook |
| 25/10 trước 23:00 | Review chéo, freeze code/tài liệu, chuẩn bị demo Seminar 1 |

Nếu một mốc trễ, báo ngay người nhận interface bị ảnh hưởng và giao bản có thể review (DDL draft, source contract, loader local hoặc model draft), không chờ tới khi hoàn thiện toàn bộ mới bàn giao.

## 7. Traceability với đề và sản phẩm cuối

| Yêu cầu trong đề | Phase | Owner/đồng hành | Tiêu chí |
|---|---|---|---|
| Dataset Kaggle, bối cảnh, mục tiêu, người dùng, câu hỏi | 1 | Phúc + Trực | URL/mô tả/provenance; business questions và phạm vi rõ |
| 3.1 Mage ingestion vào Staging, checks, full/incremental, trạng thái/số dòng/lỗi, rerun | 1 | Lộc + Dũng; Phúc/Trực review | Demo SQL Server và bằng chứng theo mục 5 |
| 3.2 dbt làm sạch/chuẩn hóa/tích hợp, phép biến đổi, tests, dependencies, docs | 2 | Lộc | `dbt build`/tests/docs và graph thể hiện model dependencies |
| 3.3 Data Warehouse SQL Server, process/grain/fact/dims/measures, star/snowflake, dbt load | Thiết kế 1; triển khai 2 | Trực + Dũng; Lộc dbt | Một fact lõi ở grain rõ; dimensions/keys; schema chạy trên SQL Server |
| 3.4 Semantic Model, relationships, DAX, hierarchies, hai dashboard | 2 | Trực + Phúc | Overview và Detailed/Diagnostic đều có filter; trang 2 drill và evidence định lượng |
| 3.5 GenAI summary/explanation dựa trên measure và có thể kiểm chứng | 3/final | Lộc + Trực; Phúc xác nhận KPI; Dũng cấu hình kết nối an toàn | AI hiển thị nguồn measures/filter/period và không tạo kết luận thiếu căn cứ |
| Report PDF | 2/final | Phúc điều phối; mỗi owner viết phần mình; Trực biên tập | Dataset, bài toán, kiến trúc, DW, pipeline, kết quả |
| Source code, PBIX, dữ liệu/tài liệu deploy, video demo | Final | Mỗi owner bàn giao artifact; cả nhóm demo | Mã Mage/dbt/SQL/AI, PBIX, URL/run instructions, video đi từ nạp đến AI explanation |

## 8. Điều kiện nghiệm thu Phase 1

- [ ] README hướng dẫn cấu hình và chạy đúng với SQL Server; secret chỉ nằm trong `.env` không commit.
- [ ] Bảy bảng lõi được nạp vào `stg`; các bảng nguồn khác có quyết định phạm vi bằng văn bản.
- [ ] `\N` thành SQL NULL; kiểm tra keys/FKs/row counts có kết quả truy vấn lưu lại.
- [ ] Full Load, static-data incremental batches và rerun đều được demo không tạo duplicate.
- [ ] `ctl` có run/batch status, counts và error; có bằng chứng log cho success và failure.
- [ ] `docs/business_requirements.md`, `docs/dimensional_model.md`, source profile/mapping/quality rules và bốn plan cá nhân được rà soát.
- [ ] Trực điều phối review cuối; mỗi người review ít nhất một phần việc khác.
