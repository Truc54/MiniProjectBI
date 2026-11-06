# Kế hoạch cá nhân - Trực: Dimensional model, KPI và QA

**Tổng tải Phase 1: 25/100 điểm (25%).** Trực biến yêu cầu phân tích thành model/star schema và tiêu chí nghiệm thu. Thiết kế có thể làm độc lập với DDL và Mage dựa trên `dataset/SCHEMA.md`; xác nhận số liệu cuối sau khi tích hợp.

## Mục tiêu và sản phẩm bàn giao

- `docs/dimensional_model.md`: grain, fact, dimensions, keys, relationships, hierarchies và aggregation rules.
- `docs/business_requirements.md`: câu hỏi phân tích, KPI, logic filter/drill và evidence cần cho dashboard.
- Cập nhật `docs/architecture.md`, `docs/data_quality_rules.md`, `docs/phase1_checklist.md` để nối Phase 1 với yêu cầu dbt/DW/Power BI/AI của đề.
- Phase1 acceptance matrix/evidence checklist để cả nhóm biết khi nào Stage pipeline đạt.

## Công việc chi tiết

### T1. Quy trình nghiệp vụ, grain và star schema - 10 điểm

- [ ] Chốt business process: kết quả chính thức của một tay đua trong một race.
- [ ] Chốt một fact lõi `FactRaceResult`, đúng một row cho mỗi `results.resultId`; xác nhận uniqueness với source profile.
- [ ] Thiết kế dimensions Date, Race, Circuit, Driver, Constructor, Status; ghi natural key nguồn, generated surrogate key, attributes và relationship 1-to-many.
- [ ] Thiết kế hierarchies: Year -> Round -> Race; Country -> Circuit; Date Year -> Quarter -> Month -> Day; các cấp Driver/Constructor phù hợp.
- [ ] Định nghĩa measures additive (points, laps, result count, win/podium flags) và non-additive (grid, finish position, speed, time); nêu rõ phép tính/filter.
- [ ] Thiết kế outcome/status group dựa trên source status; giữ nguyên source label và phân biệt classified, retirement/DNF, DNS, DSQ, other theo mapping được review.
- [ ] Ghi xử lý `position = NULL`, `grid=0`, unknown dimension member, và lineage source ID; không gộp fact của lap/pit/standings vào grain này.
- [ ] Xác nhận star schema đáp ứng đề; thay đổi sang snowflake chỉ khi có lý do chuẩn hóa dimension được ghi lại.

**Hoàn tất khi:** thành viên khác có thể xác định grain của mỗi fact row và biết mọi FK/measure/aggregation.

### T2. Câu hỏi phân tích và KPI semantics - 5 điểm

- [ ] Chốt câu hỏi theo season, driver, constructor, circuit, status và grid-to-finish.
- [ ] Định nghĩa công thức KPI, denominator, lọc NULL và ý nghĩa tăng/giảm; tránh so sánh raw points xuyên thời kỳ mà không cảnh báo thay đổi hệ thống điểm.
- [ ] Lập bản đồ KPI/visual/filter/drill cho Dashboard Overview và Diagnostic để Phase 2 bắt đầu ngay.
- [ ] Xác định evidence định lượng cần cho Dashboard 2: số row, mẫu đối chiếu, contribution by status/constructor/circuit, grid-to-finish trên tập hợp hợp lệ.

**Hoàn tất khi:** mỗi KPI có công thức có thể tái tạo và mỗi câu hỏi gắn được với column/dimension có trong nguồn.

### T3. Quality acceptance và reconciliation - 6 điểm

- [ ] Cùng Phúc rà source null/keys và với Lộc chuyển thành acceptance rules có thể chạy.
- [ ] Xác định SQL queries kiểm tra source/stage counts, key null/duplicate, orphan FK, status group và batch rerun.
- [ ] Lập mẫu evidence cho Full Load, hai batch incremental, rerun cùng batch và failure log.
- [ ] Sau khi pipeline tích hợp, chọn một race/driver/constructor để reconcile từ `results.csv` tới `stg.results` và run log.
- [ ] Kiểm tra `\N` thành SQL NULL; chứng minh optional fields vẫn giữ dòng nguồn hợp lệ.
- [ ] Ghi discrepancy kèm nguyên nhân/chủ sở hữu thay vì bỏ qua.

**Hoàn tất khi:** mọi acceptance item Phase 1 có query/expected result/evidence path.

### T4. Tích hợp tài liệu và handoff - 4 điểm

- [ ] Đồng bộ overview với Phase1/Phase2/Phase3 và requirements 3.1-3.5 của đề.
- [ ] Cập nhật kiến trúc source -> Mage -> SQL Server Stage/control -> dbt/DW -> Power BI -> AI.
- [ ] Cập nhật NULL/F1-specific rules, checklist và liên kết với source profile/mapping.
- [ ] Rà đủ các output Phúc/Dũng/Lộc; review final plan với ba thành viên và bàn giao model contract cho dbt/Power BI.

**Hoàn tất khi:** tài liệu không hứa rằng Phase1 đã triển khai dbt/DW/dashboard/AI nếu các phần đó chưa hoàn thành; có bước tiếp nối rõ.

## Tiến độ và phụ thuộc

| Thời điểm | Kết quả |
|---|---|
| 18-20/10 | Business process, grain, star diagram, measures và KPI draft; làm song song profiling/DDL/Mage |
| 21-22/10 | Review mapping/NULL rules với Phúc; chốt acceptance và dashboard backlog |
| 23/10 | Reconciliation và thử evidence với SQL Server/Mage |
| 24-25/10 | Review runbook/requirements, đóng discrepancy, chuẩn bị demo và handoff Phase 2 |

**Đầu vào:** đề project, source schema, business questions từ Phúc. **Người nhận handoff:** Dũng (target DW grain/keys), Lộc (validation outcomes), Phúc (business/KPI narrative). Thiết kế có thể hoàn tất độc lập trước khi Stage được nạp; acceptance evidence sẽ chờ lần tích hợp cuối.

## Review chéo và nghiệm thu

- Phúc xác nhận KPI dùng đúng coverage và ngữ nghĩa nguồn.
- Dũng xác nhận star schema/keys triển khai được trên SQL Server.
- Lộc xác nhận phép kiểm tra khớp output Mage và không loại NULL hợp lệ.
- Trực tập hợp kiểm tra nghiệm thu và bảo đảm thiết kế một fact lõi không trộn grain.

## Trách nhiệm tiếp nối để hoàn thành project

Các việc sau thuộc Phase 2/3, không tính vào 25 điểm tải Phase 1:

- **Phase 2:** chuyển dimensional design thành Power BI Semantic Model; tạo relationships 1-to-many, DAX measures và hierarchies; cùng Phúc tạo Dashboard 1 Overview và Dashboard 2 Detailed/Diagnostic. Trang chi tiết phải có drill-down/drill-through/filter, phân tích contribution của biến động và số liệu/denominator để kiểm chứng. Tích hợp thiết kế, ảnh dashboard và KPI definitions vào report PDF.
- **Phase 3:** cùng Lộc thiết kế context/grounding và tiêu chí kiểm chứng cho AI summary/explanation; bảo đảm câu trả lời đọc đúng filter/period, cite KPI/breakdowns đang hiển thị và nói rõ khi không đủ dữ liệu; review các câu trả lời mẫu trước demo.
- **Final handoff:** điều phối Power BI file, report narrative và video demo; kiểm tra người xem có thể đi từ KPI overview -> diagnostic evidence -> AI explanation.
