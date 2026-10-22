# Kế hoạch cá nhân - Phúc: Data source và profiling

**Tổng tải Phase 1: 25/100 điểm (25%).** Vai trò của Phúc là xác nhận chính xác nguồn dữ liệu và tạo contract dùng chung; Dũng, Lộc và Trực có thể bắt đầu từ schema Kaggle hiện có trong lúc profile hoàn thiện.

## Mục tiêu và sản phẩm bàn giao

- `docs/source_profile.md`: provenance, snapshot, số dòng/cột, phạm vi thời gian, missing-value patterns và quyết định bảng lõi/phụ.
- `docs/source_to_stage_mapping.md`: file -> bảng Stage, grain, natural/candidate keys, quan hệ và lưu ý kiểu dữ liệu.
- `docs/business_requirements.md`: xác nhận đối tượng người dùng, bối cảnh, câu hỏi nghiệp vụ và cách diễn giải phù hợp dữ liệu.
- Một bản source contract ngắn gửi nhóm trước 19/10: bảy file lõi, tên cột, key, quy tắc `\N`, row-count baseline.

## Công việc chi tiết

### P1. Provenance và phạm vi nguồn - 4 điểm

- [x] Ghi URL Kaggle, tên/maintainer, mô tả, license theo `dataset/README.md`, ngày profile local và phạm vi dữ liệu.
- [x] Ghi dataset có 17 CSV và ghi nhận README nguồn mô tả phần bổ sung 2025/2026 qua Hungarian Grand Prix ngày 26/07/2026.
- [x] Chốt bảy file lõi `results`, `races`, `drivers`, `constructors`, `circuits`, `status`, `seasons` cho Phase 1; ghi rõ mười bảng phụ và lý do chưa thêm vào core.
- [ ] Trao đổi với nhóm về câu hỏi F1 cần trả lời để phạm vi Stage không phình to.

**Hoàn tất khi:** URL/license/snapshot/selected sources có trong profile; người khác biết vì sao chọn core subset.

### P2. Profiling toàn bộ 17 CSV - 9 điểm

- [x] Đọc `dataset/SCHEMA.md`; ghi cho từng file header, column count, row count, kiểu dữ liệu dự kiến, khóa nguồn/khóa ghép ứng viên, khoảng năm và quan hệ.
- [x] Đếm literal `\N` theo cột và empty string riêng; xác định cột NULL là expected/optional.
- [x] Kiểm tra sơ bộ uniqueness/non-null của key; kiểm tra quan hệ core `results -> races/drivers/constructors/status`, `races -> circuits/seasons`.
- [x] Ghi rõ `results.position` thiếu ở nhiều kết quả không phân loại; `fastestLapSpeed` thiếu trong phần mở rộng 2025/2026; Q2/Q3 và lịch session có NULL theo quy tắc nguồn.
- [ ] Đánh dấu các giới hạn coverage của `practice_results`, `weather`, `tire_stints` (2025/2026-only), và quy mô `lap_times`.
- [x] Lưu lệnh/script profiling nếu nhóm tạo; báo cáo số dòng theo snapshot, không sửa CSV gốc.

**Hoàn tất khi:** profile đủ 17 file; null-marker và key caveats được diễn giải; row count có thể tái tạo.

### P3. Mapping và source contract - 7 điểm

- [x] Cập nhật mapping bảy bảng lõi, target names trong `stg`, grain, natural key và FK.
- [ ] Đưa các bảng phụ vào bảng tham khảo với candidate key cần xác nhận; đánh dấu grain riêng để không join làm nhân bản fact.
- [ ] Đánh dấu trường nguồn được giữ nguyên; ghi rule `\N` -> SQL NULL, không đổi NULL/blank/0.
- [x] Gửi bảng header/key cho Dũng làm DDL và Lộc làm Mage validation; sửa khác biệt dựa trên file thực tế.
- [x] Khóa version source contract ngày 21/10; thay đổi sau mốc này phải báo cả nhóm và ghi change note.

**Hoàn tất khi:** các thành viên map được file vào target, key, NULL handling và quan hệ mà không phải đoán.

### P4. Business context và data-use caveats - 5 điểm

- [ ] Viết bối cảnh phân tích F1 theo mùa giải, tay đua, constructor, circuit và kết quả.
- [ ] Đề xuất người dùng: performance/media analyst hoặc người theo dõi F1; ghi quyết định mà dashboard hỗ trợ.
- [ ] Đề xuất/duyệt câu hỏi nghiệp vụ trong `docs/business_requirements.md`: performance trend, comparison, grid-to-finish, status/outcome, bất thường theo race/circuit.
- [ ] Rà KPI với Trực: points so sánh theo mùa/era; finish position chỉ trên classified result; status group không gộp DNS/DSQ thành DNF.
- [ ] Xác nhận giới hạn: dữ liệu lịch sử, rule points thay đổi theo thời kỳ, không suy luận quan hệ nhân quả từ grid/circuit.

**Hoàn tất khi:** câu hỏi/KPI dùng được với cột có thật và nêu rõ giới hạn dữ liệu.

## Tiến độ và phụ thuộc

| Thời điểm | Kết quả |
|---|---|
| 18-19/10 | Provenance + source contract bản 1; nhóm có thể bắt đầu profiling/DDL/loader/model song song |
| 20-21/10 | Hoàn thiện profile 17 file, keys, mapping; chốt header/NULL contract |
| 22-23/10 | Rà đối soát source vs Stage cùng Dũng/Lộc; bổ sung chênh lệch |
| 24-25/10 | Chốt business context, cập nhật tài liệu và thuyết minh giới hạn trong demo |

**Đầu vào:** CSVs, `dataset/README.md`, `dataset/SCHEMA.md`, đề project. **Người nhận handoff:** Dũng (DDL), Lộc (loader/validation), Trực (grain/KPI). Không chặn các phần khác: mọi người có thể dùng schema/source hiện tại để bắt đầu trước khi profile cuối cùng xong.

## Review chéo và nghiệm thu

- Dũng xác nhận tên bảng/cột/key khớp khả năng staging.
- Lộc xác nhận format, encoding và null token xử lý được trong Mage.
- Trực xác nhận các câu hỏi phân tích có thể ánh xạ vào fact/dimensions.
- Phúc đối chiếu tổng dòng của các bảng core trong SQL Server với source baseline và ghi lý do nếu khác.

## Trách nhiệm tiếp nối để hoàn thành project

Các việc sau thuộc Phase 2/3, không tính vào 25 điểm tải Phase 1:

- **Phase 2:** cung cấp phần dataset/provenance, business context, câu hỏi và KPI narrative cho report PDF; cùng Trực chọn KPI và filter cho trang Overview; xác minh các câu kết luận trong report đúng với số đo trên dashboard.
- **Phase 3:** chuẩn bị các ví dụ tóm tắt KPI có baseline/thời kỳ và evidence; review câu trả lời AI với tư cách analyst, đánh dấu câu không được dữ liệu hỗ trợ.
- **Final handoff:** xác nhận Kaggle URL, license, snapshot/version, limitations và source tables nằm trong deployment guide/video; cập nhật profile nếu nhóm đổi snapshot.

