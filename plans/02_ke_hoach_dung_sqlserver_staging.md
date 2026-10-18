# Kế hoạch cá nhân - Dũng: SQL Server và Staging

**Tổng tải Phase 1: 25/100 điểm (25%).** Dũng phụ trách hạ tầng dữ liệu SQL Server, DDL Stage và control tables. DDL được phát triển độc lập với Mage; tích hợp nạp chỉ bắt đầu khi hai bên chốt table contract.

## Mục tiêu và sản phẩm bàn giao

- DDL idempotent trong `sqlserver/ddl/` để tạo schema và bảng cần cho Phase 1.
- Bảy bảng Stage khớp `docs/source_to_stage_mapping.md`, giữ natural keys và hỗ trợ NULL đúng nguồn.
- Control tables cho run/batch log theo thiết kế được Lộc dùng.
- `docs/stage_schema.md` mô tả kiểu dữ liệu, khóa, nullable, quyền/kết nối và cách triển khai.
- SQL queries đối soát row counts, duplicate/null keys và FKs để Trực đưa vào evidence.

## Công việc chi tiết

### D1. SQL Server connection/setup contract - 5 điểm

- [ ] Chọn database project và cấu hình SQL Server instance local/remote; thống nhất host/port/database với Compose/dbt profile.
- [ ] Xác nhận ODBC Driver 18 sẵn có cho Mage runtime và quyền cho tài khoản project: tạo/nạp vào `stg`, ghi `ctl`; secrets chỉ nằm trong `.env`.
- [ ] Viết hướng dẫn setup không gắn mật khẩu/certificate thật vào repo; ghi rõ `host.docker.internal` khi Mage chạy trong Docker Desktop.
- [ ] Chốt cùng Lộc tên schema, tên bảng, column casing, metadata columns, `load_mode`, `batch_key`, trạng thái log.

**Hoàn tất khi:** người khác biết cấu hình SQL Server và quyền cần thiết mà không cần credential ghi sẵn.

### D2. Staging schemas và bảy bảng lõi - 11 điểm

- [ ] Viết DDL idempotent cho `stg`, `ctl`, `dw`; chỉ cần tạo cấu trúc `dw` ở Phase 1, triển khai dimensional tables là Phase 2.
- [ ] Viết DDL cho `stg.circuits`, `stg.constructors`, `stg.drivers`, `stg.status`, `stg.seasons`, `stg.races`, `stg.results` theo source mapping đã chốt.
- [ ] Dùng SQL Server Unicode text types cho tên/ref/url; chọn numeric/date/time types chỉ sau khi Phúc profile format và Lộc xác nhận converter.
- [ ] Cho phép NULL ở trường optional; giữ source key; không đặt `NOT NULL`/default 0 trên cột nguồn mà source cho NULL.
- [ ] Thiết kế source lineage/batch metadata tách khỏi cột nguồn, thống nhất cách nạp với Lộc.
- [ ] Thêm primary/unique constraints và index có ích ở natural keys sau khi profile xác nhận; không áp FK nạp trước khi dimension/lookup đã sẵn sàng.

**Hoàn tất khi:** script chạy lặp không lỗi, schema khớp source contract, và Mage có thể nạp tất cả 7 target.

### D3. ETL control tables - 5 điểm

- [ ] Tạo `ctl.etl_run_log`: run ID, pipeline, source, target, mode/batch, start/end, status, rows read/written/rejected, error.
- [ ] Tạo `ctl.etl_batch_state`: source/table/batch key, trạng thái, counts, run ID và load timestamp; khóa chính ngăn batch state trùng.
- [ ] Chốt với Lộc quy tắc chỉ commit trạng thái `success` sau khi data transaction thành công; error phải lưu trạng thái và lỗi.
- [ ] Dùng UTC timestamps và kiểu SQL Server phù hợp; ghi thời gian bằng server hoặc UTC thống nhất.

**Hoàn tất khi:** Lộc có schema interface để implement log mà không phải sửa tên/kiểu sau khi tích hợp.

### D4. Reconciliation queries, deploy notes - 4 điểm

- [ ] Viết truy vấn đếm dòng theo từng bảng và kiểm tra key NULL/trùng.
- [ ] Viết orphan checks cho các FK core, chạy sau khi nạp đủ bảng.
- [ ] Viết truy vấn đọc run log/batch state, kiểm tra rerun.
- [ ] Ghi hướng dẫn chạy DDL theo thứ tự và cách thu bằng chứng cho Seminar 1.

**Hoàn tất khi:** mọi tiêu chí Phase 1 có query SQL Server có thể chụp kết quả làm evidence.

## Tiến độ và phụ thuộc

| Thời điểm | Kết quả |
|---|---|
| 18-19/10 | Chốt DB/network/env contract; đọc schema hiện có và lập DDL draft song song profile |
| 20-21/10 | Tạo schema + bảng Stage/control; review interface với Lộc |
| 22/10 | Chạy DDL trên project DB và bàn giao connection/table contract cho Mage |
| 23-24/10 | Hỗ trợ full/incremental integration, đối soát rows/FKs/logs |
| 25/10 | Freeze DDL, cập nhật stage schema/runbook, hỗ trợ demo |

**Đầu vào:** SQL Server project database, dataset schema/source contract (bản hiện tại đủ để bắt đầu). **Người nhận handoff:** Lộc cần table/log contract; Trực cần reconciliation SQL; Phúc review field types. DDL có thể viết trước khi Mage hoàn thiện; chỉ integration load cần pipeline và database cùng sẵn sàng.

## Review chéo và nghiệm thu

- Phúc xác nhận cột/key/nullable tương ứng CSV.
- Lộc xác nhận importer có thể truyền batch, lineage và load mode vào schema.
- Trực xác nhận source constraints không loại mất NULL hợp lệ và có query phục vụ acceptance.
- Dũng bàn giao DDL, SQL queries, hướng dẫn kết nối và bằng chứng tạo schema thành công.

## Trách nhiệm tiếp nối để hoàn thành project

Các việc sau thuộc Phase 2/3, không tính vào 25 điểm tải Phase 1:

- **Phase 2:** phối hợp Lộc triển khai schema `dw` và quyền dbt; kiểm tra các bảng dimensional/fact được dbt tạo trong SQL Server, kiểu dữ liệu, unique/FK relationships và row counts; cấu hình Power BI kết nối đúng DW; cung cấp SQL reconciliation cho report.
- **Phase 3:** rà cấu hình bảo mật/secret cho dịch vụ GenAI và môi trường deploy; bổ sung hướng dẫn cấu hình/chạy hệ thống và lỗi kết nối vào deployment docs.
- **Final handoff:** chịu trách nhiệm hướng dẫn khởi tạo SQL Server, schema, ODBC/network và các bước nối Mage/dbt/Power BI; không đưa `.env`/credential vào source, PDF hay video.
