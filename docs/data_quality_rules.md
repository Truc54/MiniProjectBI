# Data quality rules

## Structural checks

- Source file thuộc danh sách được duyệt, mở được, có header đúng thứ tự/tên cột theo `dataset/SCHEMA.md`, và giải mã được bằng UTF-8/UTF-8 BOM.
- Số cột mỗi dòng khớp header. Ghi lại số dòng nguồn theo snapshot để đối chiếu với số dòng Stage.
- Bắt buộc có natural key theo `docs/source_to_stage_mapping.md`; kiểm tra khóa không NULL và duy nhất ở đúng grain.
- Kiểm tra referential integrity sau khi nạp đủ bảng: results.raceId -> races.raceId; results.driverId -> drivers.driverId; results.constructorId -> constructors.constructorId; results.statusId -> status.statusId; races.circuitId -> circuits.circuitId; races.year -> seasons.year.

## NULL and source-specific rules

- Chuỗi chính xác `\N` là null marker của nguồn và phải trở thành SQL NULL. Giá trị `0`, `0.0`, `R`, chuỗi rỗng và NULL là các trường hợp khác nhau; không tự đổi chúng cho nhau.
- `results.position` có thể NULL khi kết quả không được phân loại. Dùng thêm positionText/status để phân tích kết quả; không biến NULL thành vị trí cuối hoặc DNF.
- `results.time`, `milliseconds`, fastestLap, rank, fastestLapTime, fastestLapSpeed có thể NULL; không loại toàn bộ kết quả vì thiếu các chỉ số này.
- `races` session date/time có thể NULL; sprint_date/time NULL có thể nghĩa là race weekend không có sprint.
- `qualifying.q2`/`q3` NULL có thể nghĩa là tay đua không vào vòng đó; `drivers.number`/`code` có thể chưa tồn tại ở các giai đoạn lịch sử.
- `grid = 0` không đủ bằng chứng kết luận DNS. Xác định outcome từ dữ liệu position/status theo quy tắc phân tích được nhóm duyệt.
- Weather, tire stints, practice results chỉ có phần dữ liệu 2025/2026 theo mô tả nguồn; không diễn giải thiếu dữ liệu lịch sử là giá trị thời tiết/session bằng 0.
- `circuits.alt = 0` có thể là placeholder cho circuit mới chưa có altitude nguồn; phải ghi chú khi dùng bản đồ/địa lý.

## Load and rerun checks

- Ghi run ID, source file, target, load mode, batch key, thời gian bắt đầu/kết thúc, trạng thái, rows read/written/rejected và thông báo lỗi.
- Lưu trạng thái batch chỉ sau khi giao dịch nạp hoàn tất thành công.
- Full load được chạy hai lần cho cùng snapshot và cho cùng số dòng/khóa, không nhân đôi.
- Incremental load mô phỏng bằng batch xác định từ khóa nguồn; chạy lại cùng batch giữ nguyên số dòng và khóa duy nhất.
- Đối chiếu tổng số dòng theo bảng với baseline `docs/source_profile.md`; mọi chênh lệch có giải thích, không bỏ qua im lặng.
- Kiểm tra thử lỗi ở môi trường phát triển, bảo đảm log ghi trạng thái thất bại và lỗi, không đánh dấu batch hoàn tất.
