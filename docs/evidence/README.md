# Evidence ETL của Lộc — 21/10/2026

| File | Kết quả | Môi trường |
|---|---|---|
| `loc_source_dry_run.json` | 7 file, 30.121 dòng, 6 quan hệ không orphan; counts/hash keys/nulls/blanks | Python đọc CSV, không ghi DB |
| `loc_unit_tests.txt` | 20 kiểm thử pass: source guards, contract Dũng, full/incremental/rerun, rollback, audit failure, retry | Python + SQLite transaction thật |
| `loc_sqlite_demo.json` | Full hai lần; reset Stage; 2 batch mỗi bảng + rerun batch 2; 35 run thành công và 1 duplicate-key failure có log | SQLite với DDL snapshot đã chuyển cú pháp |
| `loc_unit_tests_mage_runtime.txt` | 20 tests pass trong runtime production, SQLAlchemy 1.4.54 | Mage container + SQLite |
| `loc_live_sqlserver_mage.json` | Full x2, 2 batch/bảng + rerun, so từng giá trị có kiểu với nguồn, duplicate failure, write rollback, retry, application lock | SQL Server 2022 thật + Mage engine 0.9.79 + ODBC 18 |
| `loc_live_sqlserver_mage.log` | Exception expected khi block exporter chặn duplicate; run tổng thể vẫn pass | Mage engine |
| `loc_live_stage_checks.json` | 30.121 dòng ở Stage, 6 FK orphan_count=0, không NULL/trùng PK | SQL Server thật, CLI đối soát cuối |

Các file bằng chứng trên được tạo ngày 21/10/2026 với contract nhánh `Dung`, commit
`5b7113f`, khi chuỗi rỗng còn được giữ nguyên (14 dòng drivers có nationality/url = `''`).
Từ commit `84081c0` của Dũng, chuỗi rỗng được nạp thành NULL; cần chạy lại
`tests/live_integration.py` để cập nhật bằng chứng SQL Server.
CLI và Mage dùng cùng các hàm trong `mage/project/f1_etl/`.

**Kiểm thử thật hoàn tất ngày 21/10/2026:** SQL Server 2022 Developer
`16.0.4305.5`, database `F1_BI`, tài khoản `f1_loader`; Mage 0.9.79,
SQLAlchemy 1.4.54, pyodbc 5.1.0, ODBC Driver 18. Có **36 run success + 2 failed
chủ động** trong audit: 37 lần đi qua 3 block Mage, một lần inject lỗi sau SQL write
để kiểm tra rollback trực tiếp. Final Stage vẫn đầy đủ dữ liệu nguồn; 11.074
position NULL và 14 drivers có nationality/url trống được bảo toàn.

Mage pipeline chạy bằng `Pipeline.execute_sync`, với `update_status=False` để
không ghi trạng thái runtime vào YAML source. Danh sách block trong JSON là các
block thực sự đưa qua engine; log run/batch trong `ctl` được ghi thật. Đây không
phải run history của scheduler hay thao tác bấm Run trong UI.

SQL Server chạy x64 qua Docker emulation trên Apple Silicon; Mage chạy arm64.
Đây là database kiểm thử local dựng theo snapshot DDL của Dũng, chưa phải kiểm
thử kết nối đến SQL Server trên máy Dũng. [Microsoft không hỗ trợ chính thức SQL
Server qua emulation](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker?view=sql-server-ver16).

Đã kiểm tra cú pháp Python, YAML và Compose bằng
`docker compose --env-file .env.example config --no-env-resolution --quiet`;
và build/start container thật. Build đã phát hiện Mage yêu cầu SQLAlchemy <2;
đã sửa requirements và bật SQLAlchemy future mode cho ETL. Base Mage image được
pin digest để tái lập runtime.

Theo lựa chọn của người dùng, UI đang ở trang sign-in và kiểm thử tiếp tục bằng
Mage engine. Chưa có bằng chứng đăng nhập/chạy bằng UI; phần này làm sau khi người
dùng đăng nhập. Xem [runbook](../etl_runbook.md) để chạy lại suite thật và review nhóm.
