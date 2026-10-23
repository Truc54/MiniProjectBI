# Runbook ETL Phase 1 — Lộc

## Phạm vi và contract của Dũng

Luồng: `dataset/*.csv → Mage loader → validation → SQL Server stg + ctl`.
Thực hiện trên nhánh `Loc`, tham chiếu nhánh [Dung](https://github.com/Truc54/MiniProjectBI/tree/Dung)
tại commit [`84081c0`](https://github.com/Truc54/MiniProjectBI/commit/84081c0) (đã merge vào `Loc`).
DDL dùng chung là `sqlserver/ddl/` của Dũng; unit test đọc trực tiếp các file này
để so contract. Cấu trúc bảng giống hệt snapshot `5b7113f` trước đó.

Các file đã đọc ở nhánh Dũng:

- `sqlserver/ddl/03_create_staging_tables.sql` và `02_create_control_tables.sql`.
- `docs/stage_schema.md`, `docs/mage_sqlserver_integration_contract.md`.
- `mage/project/data_exporters/load_sqlserver.py` và hướng dẫn setup/deploy SQL Server.

ETL dùng đúng natural PK, tên cột camelCase, nullability, độ dài Unicode,
`DECIMAL`, `DATE`, `TIME(0)` và 4 cột lineage của Dũng. Mọi bảng phải có sẵn;
exporter không tự tạo hay thay thế cấu trúc bảng. Các check contract nằm trong
`mage/project/f1_etl/contract.py` và được đối chiếu với snapshot DDL trong tests.

## Kiểm tra nguồn ngay trên máy, chưa cần database

Chạy từ thư mục gốc repo, Python 3.9 trở lên:

```bash
python3 mage/run_etl.py --all --dry-run --evidence docs/evidence/loc_source_dry_run.json
```

Lệnh này chỉ đọc dữ liệu, kiểm tra cả 7 file và 6 quan hệ FK trong nguồn;
không cần Mage, pandas, ODBC hay SQL Server. Exit code khác 0 nghĩa là lỗi.

| Bảng | Số dòng snapshot hiện tại | Natural key |
|---|---:|---|
| circuits | 78 | circuitId |
| constructors | 214 | constructorId |
| drivers | 879 | driverId |
| status | 141 | statusId |
| seasons | 77 | year |
| races | 1.164 | raceId |
| results | 27.568 | resultId |
| **Tổng** | **30.121** | |

`\N` và chuỗi rỗng `''` đều thành Python `None` rồi SQL NULL (mapping P3-v1.0 của
Phúc, stage schema của Dũng). `'0'`, `'0.0'`, `'R'` được giữ nguyên. Bản CSV có
28 ô trống ở nationality/url của 14 drivers, đều thành NULL; cột NOT NULL gặp
ô trống sẽ bị reject. Optional position/lap/time được phép NULL; không suy ra
DNF từ position NULL hoặc DNS từ grid=0.

Giờ UTC của races có cả `HH:MM:SS` và `HH:MM:SSZ`. Chỉ khi chuyển sang kiểu SQL,
hậu tố `Z` được bỏ để ghi vào `TIME(0)`; không dịch múi giờ, không sửa CSV.
Race time/gap và fastestLapTime của results vẫn là chuỗi theo contract Dũng.

## Chuẩn bị database từ nhánh Dũng

Dũng cần tạo database, tài khoản và chạy đủ DDL `01`, `02`, `03` trên database
project. Nếu đã có database của Dũng thì dùng kết nối đó. Nếu cần đọc DDL ở máy
này mà không thay đổi nhánh `Loc`, lấy snapshot ra thư mục tạm:

```bash
git fetch origin Dung
mkdir -p /tmp/miniprojectbi-dung-contract
git archive origin/Dung sqlserver/ddl | tar -x -C /tmp/miniprojectbi-dung-contract
```

Đưa các file đó vào SQL client, thực thi theo thứ tự với database project được
chọn đúng. Script của Dũng có `USE F1_BI`; nếu đổi database, Dũng cần điều chỉnh
đồng bộ trước khi triển khai. Cấp tài khoản ETL quyền đọc/ghi `stg`, `ctl`, đọc
metadata để reflect bảng và gọi `sp_getapplock`/`sp_releaseapplock` trong database.
Database/tài khoản do Dũng chuẩn bị; dùng mật khẩu riêng trong `.env`.

## Cấu hình và khởi động Mage

```bash
cp .env.example .env
```

Điền host, port, database, username, password, tên ODBC driver và TLS.
Không commit `.env`; không đưa connection string vào runtime variables.

- SQL Server trên chính máy chạy Docker: `MSSQL_HOST=host.docker.internal`.
- SQL Server trên máy Dũng: `MSSQL_HOST=<DNS/IP truy cập được của máy Dũng>`.
  `host.docker.internal` luôn trỏ về máy chạy Docker, không tự trỏ tới máy Dũng.
- SQL Server trên mạng khác cần tuyến mạng/VPN và firewall phù hợp do Dũng cấu hình.
- Khi chạy CLI trực tiếp trên host, có thể cần `MSSQL_HOST=localhost` nếu DB ở máy đó.
- `MSSQL_TRUST_CERTIFICATE=no` là mặc định; cấu hình theo chứng chỉ của instance.

Dockerfile kiểm tra/cài Microsoft ODBC Driver 18 ngay trong container;
không phụ thuộc ODBC trên host. Cách cài dựa trên [hướng dẫn Microsoft](https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server).

```bash
docker compose up --build -d mage
docker compose exec mage python -c "import pyodbc; print(pyodbc.drivers())"
```

Mở `http://localhost:6789`, chọn pipeline `f1_source_to_stage`. Pipeline gồm
`load_f1_csv → validate_f1_table → load_sqlserver`; tên file exporter và UUID đã khớp.
Các biến môi trường và runtime variables là hai loại riêng trong
[Mage](https://docs.mage.ai/development/variables/environment-variables).

Trong phần chạy pipeline/trigger, nhập runtime variables cho lần chạy. Ví dụ:

```json
{
  "file_name": "results.csv",
  "table_name": "results",
  "target_table": "results",
  "schema_name": "stg",
  "load_mode": "full",
  "batch_key": "full_snapshot_20261021"
}
```

| Biến | Quy tắc |
|---|---|
| file_name | Một trong 7 CSV lõi; không có thư mục, không symlink ra ngoài dataset |
| table_name / target_table | Phải cùng khớp tên file; có thể suy ra khi chỉ truyền file_name |
| schema_name | Chỉ `stg` |
| load_mode | `full` hoặc `incremental`; mặc định `full` |
| batch_key | Tối đa 100 đơn vị UTF-16; mặc định `full` hoặc tên suy ra từ key bounds |
| key_min / key_max | Cận **bao gồm** của natural PK; incremental cần ít nhất một cận |

Full load từ chối key bounds; incremental không lọc theo thứ tự dòng hay số thứ tự ngẫu nhiên.
Ví dụ `results` dùng resultId, không dùng raceId; `races` dùng raceId, không dùng year.

## Chạy full và incremental

Thứ tự: circuits → constructors → drivers → status → seasons → races → results.
Chạy từng bảng trên Mage UI hoặc dùng cùng implementation qua CLI trong container:

```bash
docker compose exec mage python /home/src/run_etl.py --help
```

Compose mount CLI tại `/home/src/run_etl.py`. Có thể nạp và lưu evidence bằng:

```bash
docker compose exec mage python /home/src/run_etl.py --all
```

Hoặc chạy trên host với môi trường Python và ODBC đã cài:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r mage/requirements.txt
.venv/bin/python mage/run_etl.py --all --evidence docs/evidence/sql_full_1.json
.venv/bin/python mage/run_etl.py --all --evidence docs/evidence/sql_full_2.json
```

Full xóa/nạp lại trong một transaction, giữ PK/index/DDL. Kiểm tra lần 2 có cùng
count và key set. Incremental thay thế các natural keys có trong batch rồi insert;
keys ngoài batch được giữ. Không skip chỉ vì batch_key từng thành công: rerun phải
ghi được các giá trị cập nhật. `rows_written` là số dòng insert của lần nạp, gồm cả
keys được thay thế, không phải số dòng tăng thêm.

**Khác biệt có chủ ý so với contract của Dũng (cần Dũng xác nhận):**

- Rerun batch đã `success` vẫn nạp lại (idempotent) thay vì bỏ qua, để ghi nhận giá trị cập nhật; log ghi đủ 2 lần success.
- Batch chia theo khoảng natural key (`key_min`/`key_max`, biến thêm ngoài contract), không theo `year`/`raceId` của `results`. Demo `races` của Dũng tương đương `key_max=1120` (1.101 dòng, năm ≤ 2023) và `key_min=1121` (63 dòng); `results` chia theo `resultId`, không theo `raceId`.
- Full load xóa `ctl.etl_batch_state` của bảng đó (giữ nguyên `etl_run_log`).

Ví dụ hai batch results, sau khi có các parent tables:

```bash
.venv/bin/python mage/run_etl.py --table results --mode incremental --key-max 14000 --batch-key results_part1
.venv/bin/python mage/run_etl.py --table results --mode incremental --key-min 14001 --batch-key results_part2
.venv/bin/python mage/run_etl.py --table results --mode incremental --key-min 14001 --batch-key results_part2
.venv/bin/python mage/run_etl.py --check-stage --evidence docs/evidence/sql_stage_checks.json
```

Nếu Stage đang chứa full snapshot thì hai lệnh đầu sẽ thay thế keys hiện có.
Để chứng minh batch 1 + batch 2 **từ bảng rỗng**, dùng demo tự động trên DB project
riêng cho thử nghiệm:

```bash
.venv/bin/python mage/run_etl.py --demo --evidence docs/evidence/sql_demo.json
```

`--demo` thực hiện full 7 bảng hai lần, đối soát count/FK; xóa nội dung 7 bảng Stage
và checkpoint; chia mỗi bảng thành hai khoảng PK, nạp batch 1, batch 2 và rerun
batch 2; đối chiếu toàn bộ key sets/counts/FK; chủ động gửi duplicate key để ghi
failed log. Cuối demo dữ liệu hợp lệ vẫn đủ 30.121 dòng. Lịch sử run được giữ lại.
Không chạy song song demo và các phiên nạp khác.

## Log, lỗi và retry

Mỗi lần exporter chạy có UUID mới, ghi `ctl.etl_run_log=running` và
`ctl.etl_batch_state=in_progress`. SQL Server application lock tuần tự hóa các
run trên cùng bảng. Nạp dữ liệu + success run log + success batch state được
commit cùng transaction; không có success hiển thị trước khi data commit.
Sau rollback, transaction riêng ghi failed; exception trả lại Mage khiến run thất bại.

Loader/validator trả payload lỗi JSON cho exporter thay vì dừng ngay upstream.
Vì vậy cần chạy **cả pipeline**, kể cả khi loader có lỗi, để có failed log trong
`ctl`. Không chạy exporter với output cũ sau khi thay runtime variables; chạy lại
từ loader. Payload chứa rows/context và 4 metadata lineage được gắn lúc insert.

`rows_read` là số dòng batch sau lọc nếu hợp lệ, hoặc số dòng đọc hoàn chỉnh trước
validation nếu bị reject; `source_rows` trong JSON là số dòng toàn file.
Lỗi giải mã/header/shape xảy ra trước khi có payload hoàn chỉnh ghi rows_read=0.
`rows_rejected` đếm dòng vi phạm được validator xác định; lỗi DB ghi rejected=0,
written=0 vì cả transaction rollback. Không tự loại dòng lỗi để nạp phần còn lại.

```sql
SELECT TOP (30) run_id, source_file, target_table, load_mode, batch_key,
       run_status, rows_read, rows_written, rows_rejected,
       started_at_utc, completed_at_utc, error_message
FROM ctl.etl_run_log ORDER BY started_at_utc DESC;

SELECT * FROM ctl.etl_batch_state ORDER BY source_table, batch_key;

SELECT COUNT(*) AS rows, COUNT(DISTINCT resultId) AS unique_keys FROM stg.results;
SELECT COUNT(*) AS expected_null_positions FROM stg.results WHERE position IS NULL;
-- Snapshot: 27568 rows/keys; 11074 NULL positions.
```

Retry cùng runtime variables sau khi sửa nguyên nhân. Batch failed/in_progress
không cản retry. Khi full thay snapshot, các checkpoint cũ của source/table bị
xóa và thay bởi checkpoint full, còn run history được giữ nguyên.

Nếu SQL Server không kết nối được/thiếu ctl/quyền, không thể ghi log vào DB đó;
CLI/Mage trả thông báo đã lọc secret và run_id. Nếu process bị kill hoặc mất kết
nối ở lúc commit, đối soát dữ liệu + run_id trước khi kết luận; state có thể còn
running/in_progress. Thực thi lại an toàn theo PK sau khi database hoạt động.
Thông báo driver chỉ giữ loại lỗi, không in connection string/password/SQL params.

## Kiểm thử và bằng chứng hiện có

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Tests đọc DDL `sqlserver/ddl/` của Dũng để so cột/kiểu/nullable/PK, kiểm tra BOM/NULL/blank,
header/shape/path/symlink, ngày/giờ/precision, duplicate key, batch coverage;
dùng SQLite với schema `stg`/`ctl` tách biệt để chạy transaction thật cho
full/rerun/update/rollback/failure logs và lỗi ghi success audit.
SQLite không chứng minh ODBC, T-SQL application lock hay triển khai SQL Server thật.

Bằng chứng trong `docs/evidence/` ghi rõ backend: source dry-run, unit tests,
demo SQLite và **kiểm thử SQL Server/Mage thật** (xem phần tiếp theo).

## Kết quả SQL Server/Mage thật ngày 21/10/2026

Môi trường đã dựng và kiểm thử:

- SQL Server 2022 Developer `16.0.4305.5`, container `miniprojectbi-sqlserver-test`.
- Database `F1_BI` theo đúng DDL nhánh Dũng, commit `5b7113f` (cấu trúc không đổi ở `84081c0`); user `f1_loader`
  chỉ có quyền đọc/ghi Stage/control và đọc schema metadata.
- Mage 0.9.79, Python 3.10.19, SQLAlchemy 1.4.54, pyodbc 5.1.0, ODBC Driver 18.
- Docker host Apple Silicon; Mage arm64, SQL Server x64 qua emulation. Đây là
  kiểm thử local; [Microsoft không hỗ trợ chính thức SQL Server qua emulation](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker?view=sql-server-ver16).
- `.env` đã tạo với mật khẩu random riêng cho database kiểm thử, chmod 600,
  được gitignore. Host CLI dùng `127.0.0.1:14339`; Mage dùng
  `host.docker.internal:14339`. `TrustServerCertificate=yes` cho instance test
  local này. Không dùng cấu hình này để kết luận đã nối được máy Dũng.
- Mage UI chỉ bind `127.0.0.1:6789`; volume `mage_data` giữ dữ liệu runtime.

Suite `tests/live_integration.py` đã thực thi **pipeline Mage thật** bằng
`Pipeline.execute_sync`. Tất cả lần nạp bình thường đi qua loader → transformer
→ exporter, sử dụng output persisted của Mage, rồi ghi SQL qua ODBC.
`update_status=False` giữ YAML source không chứa trạng thái run; suite này không
tạo scheduler run history hay giả lập thao tác UI.

Kết quả:

1. Full load cả 7 bảng hai lần, so từng giá trị đã chuyển kiểu với nguồn, không
   chỉ so số dòng/khóa.
2. Xóa Stage trong DB test; mỗi bảng chia 2 khoảng natural PK, nạp batch 1,
   batch 2, rerun batch 2. Mỗi bước có count/hash khóa, cuối cùng khớp nguồn.
3. Gửi CSV duplicate qua chính 3 block Mage: pipeline fail, ctl ghi failed,
   rejected=1, written=0, Stage không thay đổi.
4. Inject lỗi sau DELETE/INSERT trên SQL Server thật: rollback toàn bộ,
   ghi failed ở transaction riêng, thông báo không lộ secret marker.
5. Hai phiên SQL Server cạnh tranh application lock: phiên sau bị chặn,
   rồi lấy được lock khi phiên trước nhả.
6. Retry thành công, cuối suite có **36 success + 2 failed chủ động** trong ctl,
   **30.121 dòng**, không duplicate/NULL PK, **6 FK không orphan**,
   **11.074 position NULL**, giữ **14 drivers có nationality/url trống**.
7. 20 unit/transaction tests cũng pass bên trong chính Mage runtime 1.4.54.

Bằng chứng chính: `docs/evidence/loc_live_sqlserver_mage.json`, log cùng tên,
`loc_live_stage_checks.json`, `loc_unit_tests_mage_runtime.txt`.
Người dùng chọn tiếp tục bằng Mage engine và đăng nhập UI sau;
chưa có bằng chứng bấm Run/đăng nhập từ UI.

Chạy lại trên môi trường local đã dựng (suite thay nội dung Stage, giữ run history):

```bash
docker start miniprojectbi-sqlserver-test
docker compose up -d mage
docker compose cp tests/live_integration.py mage:/tmp/live_integration.py
docker compose exec -T mage python /tmp/live_integration.py --reset-stage --evidence /home/src/evidence/loc_live_sqlserver_mage.json
docker compose exec -T mage python /home/src/run_etl.py --check-stage --evidence /home/src/evidence/loc_live_stage_checks.json
```

SQL Server data nằm trong volume `miniprojectbi-sqlserver-test-data`; Mage runtime
nằm trong volume `miniprojectbi_mage_data`. Để tạm dừng mà giữ dữ liệu:

```bash
docker compose stop mage
docker stop miniprojectbi-sqlserver-test
```

Build thật phát hiện Mage 0.9.79 yêu cầu SQLAlchemy <2, nên requirements được
chốt 1.4 và engine ETL dùng `future=True`. Base image được pin digest trong
Dockerfile; thay dependency/runtime phải chạy lại suite này.
