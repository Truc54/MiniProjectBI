# Kịch bản Demo Phase 2: dbt Transformation & Data Warehouse

**Đồ án:** Formula 1 Analytics (1950–2026) · **Nhóm:** Phúc, Dũng, Lộc, Trực
**Thời lượng:** khoảng 15 phút demo + 5 phút hỏi đáp
**Máy demo:** một máy duy nhất có SQL Server trong Docker (đã chạy thử toàn bộ kịch bản ngày 08/11/2026)

> Mọi con số trong kịch bản này lấy từ lần chạy thật trên SQL Server ngày 08/11/2026. Nếu lúc demo màn hình ra số khác, **nói đúng số trên màn hình**, đừng đọc thuộc lòng.

---

## 0. Tổng quan

| # | Phần | Người nói | Thời gian |
|---|---|---|:---:|
| 1 | Mở đầu & kiến trúc | Phúc | 1:30 |
| 2 | Quy tắc chuyển đổi & `OutcomeGroup` | Lộc | 2:00 |
| 3 | dbt project & build Star Schema | Trực | 2:30 |
| 4 | Kho dữ liệu vật lý trên SQL Server | Dũng | 2:00 |
| 5 | Lineage (dbt docs) | Trực | 1:00 |
| 6 | Kiểm thử: bắt lỗi, nạp tăng dần, chạy lại | Phúc | 2:30 |
| 7 | Thẩm định ngữ nghĩa 43 điểm | Lộc | 1:30 |
| 8 | Điều phối bằng Mage | Trực | 1:00 |
| 9 | Kết luận | Phúc | 0:30 |

**Chuẩn bị màn hình** (mở sẵn trước khi lên, chuyển qua lại bằng Cmd+Tab):

- **Terminal A** (chữ to, cỡ 18 trở lên): chạy `dbtx` và `sql`.
- **VS Code**: mở sẵn các file trong bảng dưới.
- **Trình duyệt**: tab `http://localhost:8080` (dbt docs), tab `http://localhost:6789` (Mage, chỉ khi dùng phương án A ở phần 8).

| File mở sẵn trong VS Code | Dùng ở phần |
|---|---|
| `docs/02_data_dictionary_and_mapping/status_outcome_mapping.csv` | 2 |
| `dbt/models/staging/stg_status.sql` | 2 |
| `dbt/macros/generate_schema_name.sql` | 3 |
| `dbt/models/marts/fact_race_result.sql` | 3, 6 |
| `dbt/models/marts/schema.yml` | 6 |
| `dbt/tests/assert_points_non_negative.sql` | 6 |
| `mage/project/pipelines/f1_source_to_stage/metadata.yaml` | 8 |
| `mage/project/custom/commit_watermark.py` | 8 |

---

## A. Chuẩn bị trước giờ demo (30 phút trước, không chiếu màn hình)

### A1. Khởi động Docker và SQL Server

```zsh
open -a Docker                      # đợi biểu tượng Docker báo "running"
docker start miniprojectbi-sqlserver-test
docker port miniprojectbi-sqlserver-test   # kỳ vọng: 1433/tcp -> 127.0.0.1:14339
```

### A2. Image chạy dbt

Image Mage hiện tại có sẵn `dbt-sqlserver 1.8.4`, bản này lỗi khi import (`get_pyodbc_attrs_before`). Cho đến khi Trực sửa `mage/requirements.txt` thành `dbt-sqlserver>=1.8.7,<1.9.0`, dùng image tạm:

```zsh
mkdir -p ~/f1_demo/img ~/f1_demo/prof ~/f1_demo/out
printf 'FROM miniprojectbi-mage:latest\nRUN pip3 install --no-cache-dir --upgrade "dbt-sqlserver>=1.8.7,<1.9.0"\n' > ~/f1_demo/img/Dockerfile
docker build -t f1-dbt-demo ~/f1_demo/img
cp dbt/profiles.yml.example ~/f1_demo/prof/profiles.yml
```

### A3. Lệnh tắt cho Terminal A

Chạy trong thư mục gốc repo. Mật khẩu `sa` đặt **trước khi chiếu màn hình** để không lộ trên máy chiếu:

```zsh
cd ~/Desktop/MiniProjectBI
export MSSQL_SA_PASSWORD="$(docker inspect miniprojectbi-sqlserver-test --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^MSSQL_SA_PASSWORD=//p')"

sql()  { docker exec miniprojectbi-sqlserver-test /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -d F1_BI -s'|' -W -Q "SET NOCOUNT ON; $1"; }
sqlf() { docker cp "$1" miniprojectbi-sqlserver-test:/tmp/run.sql >/dev/null && docker exec miniprojectbi-sqlserver-test /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -d F1_BI -s'|' -W -i /tmp/run.sql; }
dbtx() { docker run --rm -v "$PWD/dbt:/dbt" -v "$HOME/f1_demo/prof:/prof" -v "$HOME/f1_demo/out:/out" \
  -e DBT_PROFILES_DIR=/prof -e MSSQL_HOST=host.docker.internal -e MSSQL_PORT=14339 -e MSSQL_USERNAME=sa \
  -e MSSQL_PASSWORD="$MSSQL_SA_PASSWORD" -e DBT_TARGET_PATH=/out/target -e DBT_LOG_PATH=/out/logs \
  --add-host host.docker.internal:host-gateway --entrypoint sh f1-dbt-demo -c "cd /dbt && $*"; }
clear
```

### A4. Sao lưu và chạy tổng duyệt

```zsh
sql "BACKUP DATABASE F1_BI TO DISK='/var/opt/mssql/data/F1_BI_before_demo.bak' WITH INIT, COPY_ONLY"
dbtx dbt debug                                              # kỳ vọng: All checks passed!
dbtx dbt build --select +fact_race_result --full-refresh    # kỳ vọng: PASS=61 ERROR=0
dbtx dbt docs generate
```

### A5. Bật dbt docs ở cửa sổ terminal riêng (Terminal B, để chạy suốt buổi)

```zsh
docker run --rm -p 127.0.0.1:8080:8080 -v "$PWD/dbt:/dbt" -v "$HOME/f1_demo/prof:/prof" -v "$HOME/f1_demo/out:/out" \
  -e DBT_PROFILES_DIR=/prof -e MSSQL_PASSWORD=x -e DBT_TARGET_PATH=/out/target --entrypoint sh f1-dbt-demo \
  -c "cd /dbt && dbt docs serve --port 8080 --host 0.0.0.0 --no-browser"
```

Mở `http://localhost:8080` để chắc trang đã lên, rồi `clear` Terminal A.

---

## Phần 1. Mở đầu & kiến trúc (Phúc, 1:30)

**Thao tác:** chiếu sơ đồ kiến trúc trong `plans/phase2_dbt_dw/00_ke_hoach_tong_quat_phase2.md` (khối “KIẾN TRÚC LUỒNG DỮ LIỆU PHASE 2”) hoặc slide tương ứng.

**Lời nói:**
> “Ở Phase 1, nhóm đã nạp 7 file CSV Formula 1 vào schema `stg` trên SQL Server, gồm 27.568 kết quả đua. Phase 2 biến dữ liệu thô đó thành kho dữ liệu dạng Star Schema theo Kimball.
>
> Luồng gồm ba tầng. Tầng `stg` là dữ liệu thô từ Phase 1. dbt đọc `stg`, tạo các view làm sạch trong schema `stg_clean`, rồi dựng 6 bảng chiều và 1 bảng sự kiện trong schema `dw`. Toàn bộ được Mage điều phối và có kiểm thử tự động ở mỗi lần chạy.
>
> Grain của bảng sự kiện là **một dòng cho mỗi kết quả của một tay đua trong một chặng đua**, tức là một `resultId`.
>
> Nhóm chia việc như sau: Lộc làm đặc tả chuyển đổi, Trực viết dbt và tích hợp Mage, Dũng phụ trách SQL Server, và tôi phụ trách kiến trúc và kiểm thử. Bây giờ mời Lộc trình bày quy tắc chuyển đổi.”

---

## Phần 2. Quy tắc chuyển đổi & `OutcomeGroup` (Lộc, 2:00)

**Thao tác 1:** mở `status_outcome_mapping.csv` trong VS Code, cuộn qua vài dòng.

**Lời nói:**
> “Bảng `status` gốc có **141 mã trạng thái** rất vụn: ‘Finished’, ‘+1 Lap’, ‘Engine’, ‘Gearbox’, ‘Accident’… Phân tích trực tiếp trên 141 mã thì không ra ý nghĩa gì. Em gom chúng thành **5 nhóm nghiệp vụ**: `CLASSIFIED` là về đích hoặc được xếp hạng, `RETIREMENT_DNF` là bỏ cuộc giữa chừng, `DNS` là không xuất phát, `DSQ` là bị loại, và `OTHER` cho các trường hợp còn lại.
>
> Ví dụ ‘+1 Lap’ nghĩa là về đích chậm một vòng, vẫn được xếp hạng nên thuộc `CLASSIFIED`, chứ không phải bỏ cuộc.”

**Thao tác 2:** mở `dbt/models/staging/stg_status.sql`, chỉ vào khối `CASE WHEN`.

**Lời nói:**
> “Trực đưa bảng phân loại này vào model `stg_status` của dbt. Sau Phase 2, em đã đối chiếu `dw.DimStatus` với file CSV: **141 trên 141 dòng khớp**, không lệch dòng nào.
>
> Ngoài trạng thái, em còn đặc tả các quy tắc khác: điểm số của từng thời kỳ F1, cờ `is_win` và `is_podium`, cột `places_gained` (số bậc tăng so với vị trí xuất phát, chỉ tính khi được xếp hạng và không xuất phát từ pit lane). Tất cả nằm trong tài liệu mapping và từ điển dữ liệu `dw_data_dictionary.md`.”

**Thao tác 3 (Terminal A):**

```zsh
sql "SELECT s.outcome_group, COUNT(*) AS so_dong FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk GROUP BY s.outcome_group ORDER BY so_dong DESC"
```

**Kết quả mong đợi:**

| outcome_group | so_dong |
|---|---:|
| CLASSIFIED | 15839 |
| RETIREMENT_DNF | 9771 |
| OTHER | 1538 |
| DNS | 258 |
| DSQ | 162 |

**Lời nói:**
> “Trên kho thật, 27.568 kết quả chia vào 5 nhóm như trên. Cộng lại đúng 27.568, không mất dòng nào. Mời Trực trình bày phần dbt.”

---

## Phần 3. dbt project & build Star Schema (Trực, 2:30)

**Thao tác 1:** mở `dbt/macros/generate_schema_name.sql`.

**Lời nói:**
> “Project dbt tên `f1_bi`, gồm 7 model staging dạng view và 7 model mart. Mặc định dbt sẽ ghép tên schema thành `dw_dw` hoặc `dw_stg_clean`. Macro này ghi đè hành vi đó để model ghi đúng vào schema `dw` và `stg_clean`.”

**Thao tác 2:**

```zsh
dbtx dbt debug
```

**Kết quả mong đợi:** dòng cuối `All checks passed!`

**Thao tác 3:**

```zsh
dbtx dbt ls --resource-type model --select +fact_race_result
```

**Lời nói:**
> “Lệnh này liệt kê mọi model mà bảng sự kiện phụ thuộc: 6 view staging, 6 bảng chiều và chính bảng sự kiện, tổng cộng 13 model. Dấu cộng trước `fact_race_result` nghĩa là chạy cả những model đứng trước nó.”

**Thao tác 4:** mở `dbt/models/marts/fact_race_result.sql`, chỉ vào khối `config` và các dòng `coalesce(..., -1)`.

**Lời nói:**
> “Bảng sự kiện dùng chế độ `incremental` với chiến lược `delete+insert` và khóa `source_result_id`. Mỗi lần chạy chỉ xử lý những dòng `stg` mới hơn mốc `_ingested_at_utc` lớn nhất đã có trong bảng. Dòng trùng khóa sẽ bị xóa rồi chèn lại, nên chạy lại không bao giờ nhân đôi dữ liệu.
>
> Khóa ngoại nào không tìm thấy trong bảng chiều sẽ trỏ về `-1`, tức là bản ghi Unknown. Nhờ vậy bảng sự kiện không bao giờ có khóa mồ côi.”

**Thao tác 5:**

```zsh
dbtx dbt build --select +fact_race_result --full-refresh
```

**Lời nói (trong lúc chạy, khoảng 10 giây):**
> “`dbt build` vừa tạo model vừa chạy test theo đúng thứ tự phụ thuộc. Cờ `--full-refresh` dựng lại toàn bộ từ đầu.”

**Kết quả mong đợi:** dòng cuối `Done. PASS=61 WARN=0 ERROR=0 SKIP=0 TOTAL=61`

**Lời nói:**
> “61 bước đều PASS: 13 model và 48 test. Mời Dũng kiểm tra kết quả trên SQL Server.”

---

## Phần 4. Kho dữ liệu vật lý trên SQL Server (Dũng, 2:00)

**Thao tác 1:**

```zsh
sql "SELECT s.name + '.' + t.name AS bang, SUM(p.rows) AS so_dong FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1) WHERE s.name IN ('stg','dw') GROUP BY s.name, t.name ORDER BY 1"
```

**Kết quả mong đợi (phần `dw`):**

| Bảng | Số dòng | Giải thích |
|---|---:|---|
| `dw.DimCircuit` | 79 | 78 trường đua + 1 Unknown |
| `dw.DimConstructor` | 215 | 214 đội + 1 Unknown |
| `dw.DimDate` | 28125 | mọi ngày từ 01/01/1950 đến 31/12/2026 (28.124 ngày) + 1 Unknown |
| `dw.DimDriver` | 880 | 879 tay đua + 1 Unknown |
| `dw.DimRace` | 1165 | 1.164 chặng + 1 Unknown |
| `dw.DimStatus` | 142 | 141 trạng thái + 1 Unknown |
| `dw.FactRaceResult` | 27568 | bằng đúng `stg.results` |

**Lời nói:**
> “Mỗi bảng chiều có đúng thêm một dòng so với nguồn, đó là bản ghi Unknown `SK = -1`. Riêng `DimDate` là lịch đầy đủ từng ngày từ 1950 đến 2026, không chỉ những ngày có đua. Bảng sự kiện có 27.568 dòng, khớp tuyệt đối với `stg.results`.”

**Thao tác 2:**

```zsh
sql "SELECT OBJECT_SCHEMA_NAME(object_id) + '.' + OBJECT_NAME(object_id) AS bang, type_desc FROM sys.indexes WHERE type_desc LIKE '%COLUMNSTORE%'"
```

**Kết quả mong đợi:** 7 dòng `CLUSTERED COLUMNSTORE`, gồm `dw.FactRaceResult` và 6 bảng chiều.

**Lời nói:**
> “Bảng sự kiện được lưu bằng Clustered Columnstore Index: dữ liệu lưu theo cột và được nén, nên các truy vấn tổng hợp kiểu `SUM` hay `COUNT` trên hàng chục nghìn dòng chạy rất nhanh. Adapter `dbt-sqlserver` tự tạo index này mỗi khi dựng bảng, nên chạy `--full-refresh` cũng không làm mất index.”

**Thao tác 3 (truy vấn phân tích trên Star Schema):**

```zsh
sql "SELECT TOP 5 d.full_name, SUM(CAST(f.is_win AS int)) AS thang, SUM(CAST(f.is_podium AS int)) AS podium, SUM(f.points) AS diem FROM dw.FactRaceResult f JOIN dw.DimDriver d ON d.driver_sk = f.driver_sk GROUP BY d.full_name ORDER BY thang DESC"
```

**Kết quả mong đợi:**

| full_name | thang | podium | diem |
|---|---:|---:|---:|
| Lewis Hamilton | 106 | 207 | 5134.50 |
| Michael Schumacher | 91 | 155 | 1566.00 |
| Max Verstappen | 71 | 134 | 3452.50 |
| Sebastian Vettel | 53 | 122 | 3098.00 |
| Alain Prost | 51 | 106 | 798.50 |

**Lời nói:**
> “Đây là một câu hỏi nghiệp vụ trả lời ngay trên Star Schema: top 5 tay đua thắng nhiều nhất, chỉ cần một phép join giữa bảng sự kiện và bảng chiều tay đua.
>
> Lưu ý cột điểm: Schumacher thắng 91 chặng nhưng chỉ có 1.566 điểm, còn Hamilton có hơn 5.000 điểm. Lý do là thang điểm F1 đã đổi qua các thời kỳ: giai đoạn 1991–2009 người thắng chặng được 10 điểm, từ 2010 là 25 điểm. Nhóm **giữ nguyên điểm gốc** của từng thời kỳ, nên khi so sánh tay đua giữa các thời kỳ phải dùng số trận thắng hoặc podium, không dùng tổng điểm.”

---

## Phần 5. Lineage bằng dbt docs (Trực, 1:00)

**Thao tác:** chuyển sang tab `http://localhost:8080`. Bấm vào `fact_race_result` ở cây bên trái, sau đó bấm nút lineage graph (biểu tượng sơ đồ ở góc dưới bên phải).

**Lời nói:**
> “Đây là tài liệu dbt tự sinh ra từ code. Sơ đồ lineage cho thấy đường đi của dữ liệu: từ 7 bảng nguồn `stg`, qua các view `stg_clean`, tới 6 bảng chiều và bảng sự kiện. Khi một bảng nguồn thay đổi, nhìn sơ đồ là biết ngay những bảng nào bị ảnh hưởng.
>
> Mỗi model đều có mô tả cột và danh sách test đi kèm, lấy từ file `schema.yml`.”

---

## Phần 6. Kiểm thử: bắt lỗi, nạp tăng dần, chạy lại (Phúc, 2:30)

**Thao tác 1:** mở `dbt/models/marts/schema.yml` và `dbt/tests/assert_points_non_negative.sql`.

**Lời nói:**
> “Nhóm có 48 test dbt. Các generic test gồm `not_null` và `unique` cho khóa, `relationships` cho 6 khóa ngoại của bảng sự kiện, và `accepted_values` cho các cột phân loại. Ngoài ra có 4 singular test viết bằng SQL cho logic nghiệp vụ F1, ví dụ test này kiểm tra không có điểm số âm.
>
> Bây giờ tôi sẽ cố ý đưa một dòng sai vào dữ liệu nguồn để xem kiểm thử có bắt được không.”

**Thao tác 2 (tạo lỗi):**

```zsh
sql "UPDATE stg.results SET points = -5, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1"
dbtx dbt build --select +fact_race_result
```

**Kết quả mong đợi:**

```text
FAIL 1 assert_points_non_negative ... [FAIL 1 ...]
Got 1 result, configured to fail if != 0
Done. PASS=60 WARN=0 ERROR=1 SKIP=0 TOTAL=61
```

**Lời nói:**
> “Dòng `resultId = 1`, Hamilton thắng chặng Úc 2008, bị sửa thành âm 5 điểm. Bảng sự kiện chỉ nạp tăng dần đúng 1 dòng này, và test `assert_points_non_negative` báo **FAIL**, kết thúc với 1 lỗi.
>
> Trong pipeline Mage, khi dbt lỗi thì bước ghi watermark phía sau không được chạy. Batch này vì vậy không bị đánh dấu là thành công, và lần chạy sau sẽ xử lý lại.”

**Thao tác 3 (sửa nguồn, nạp tăng dần lại):**

```zsh
sql "UPDATE stg.results SET points = 10, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1"
dbtx dbt build --select +fact_race_result
sql "SELECT COUNT(*) AS so_dong, COUNT(DISTINCT source_result_id) AS so_khoa, SUM(points) AS tong_diem FROM dw.FactRaceResult"
```

**Kết quả mong đợi:** `Done. PASS=61 ... ERROR=0`, sau đó:

| so_dong | so_khoa | tong_diem |
|---:|---:|---:|
| 27568 | 27568 | 57126.05 |

**Lời nói:**
> “Sửa nguồn về 10 điểm rồi chạy lại: tất cả PASS. Bảng sự kiện **vẫn 27.568 dòng**, số khóa phân biệt cũng 27.568, tổng điểm về đúng 57.126,05. Nhờ chiến lược `delete+insert` theo `source_result_id`, dòng cũ bị thay thế chứ không bị chèn thêm, nên chạy lại bao nhiêu lần cũng không nhân đôi. Mời Lộc trình bày phần thẩm định.”

---

## Phần 7. Thẩm định ngữ nghĩa 43 điểm (Lộc, 1:30)

**Thao tác:**

```zsh
sqlf sqlserver/dw/loc_semantic_validation.sql
```

**Kết quả mong đợi:** bảng 43 dòng đều `PASS`, sau đó dòng tổng kết:

```text
total_checks|passed|failed
43|43|0
```

và dòng mẫu cuối: `1|Lewis Hamilton|McLaren|2008 R01 Australian Grand Prix|...|Finished|CLASSIFIED|...|10.00`

**Lời nói:**
> “Test dbt kiểm tra cấu trúc. Script này của em kiểm tra **ý nghĩa nghiệp vụ**: 43 điểm, mỗi điểm so giá trị trong `dw` với giá trị tính trực tiếp từ `stg` và với baseline em tính độc lập từ file CSV.
>
> Ví dụ: tổng điểm, tổng số vòng, 1.167 lượt thắng (trong đó có 3 lượt hai tay đua chung xe thời đầu), 3.513 podium, số dòng của từng `OutcomeGroup`, tổng `places_gained`, và việc mỗi mùa giải dùng đúng thang điểm của thời kỳ đó.
>
> Kết quả 43 trên 43 PASS trên kho thật do dbt tạo ra. Trước đó em cũng đã kiểm thử ngược: cố ý làm hỏng 8 chỗ, script bắt được đủ 8 lỗi. Mời Trực trình bày phần điều phối.”

---

## Phần 8. Điều phối bằng Mage (Trực, 1:00)

> **Chọn phương án trước buổi demo.** Phương án A chỉ dùng khi đã sửa `mage/requirements.txt`, build lại image Mage và chạy thử pipeline thành công ít nhất một lần. Nếu chưa chạy thử, **dùng phương án B**: đừng thử lần đầu trước giảng viên.

### Phương án A: chạy thật trên Mage UI

**Thao tác:** `docker compose up -d`, mở `http://localhost:6789`, vào **Pipelines → `f1_source_to_stage`**, chỉ vào DAG, rồi bấm **Run pipeline now** và mở log của block `dbt_transformation`.

### Phương án B: trình bày cấu hình

**Thao tác:** mở `mage/project/pipelines/f1_source_to_stage/metadata.yaml`, sau đó mở `mage/project/custom/commit_watermark.py`.

**Lời nói (dùng cho cả hai phương án):**
> “Pipeline Mage gồm 5 block nối tiếp: `load_f1_csv` đọc CSV, `validate_f1_table` kiểm tra dữ liệu, `load_sqlserver` nạp vào `stg`, `dbt_transformation` chạy `dbt run --select +fact_race_result`, và cuối cùng `commit_watermark` ghi trạng thái batch vào `ctl.etl_batch_state`.
>
> Thứ tự này là có chủ đích. Watermark chỉ được ghi **sau khi** dbt thành công. Nếu dbt lỗi như phần vừa demo, block cuối bị hủy, batch không được đánh dấu thành công, và lần chạy sau sẽ xử lý lại an toàn.”

---

## Phần 9. Kết luận (Phúc, 0:30)

**Lời nói:**
> “Tóm lại, Phase 2 đã dựng xong Star Schema 1 bảng sự kiện, 6 bảng chiều trên SQL Server bằng dbt, với các kết quả: 61 trên 61 bước build và test PASS, 43 trên 43 điểm thẩm định nghiệp vụ PASS, số dòng và tổng điểm khớp 100% với nguồn, và chạy lại không nhân đôi dữ liệu. Kho này là nền cho dashboard Power BI ở giai đoạn tiếp theo. Nhóm xin cảm ơn và sẵn sàng nhận câu hỏi.”

---

## Chuẩn bị hỏi đáp

| Câu hỏi có thể gặp | Trả lời gợi ý | Ai trả lời |
|---|---|---|
| Tại sao surrogate key lại bằng luôn ID gốc? | Nguồn Kaggle không đổi ID, và SK cố định giúp rebuild bảng chiều (`materialized='table'`) mà không làm hỏng khóa đã lưu trong bảng sự kiện tăng dần. Đây là lựa chọn có cân nhắc, đánh đổi bằng việc không theo dõi lịch sử thay đổi (SCD type 2). | Phúc |
| Sao không dùng SCD type 2? | Dữ liệu tay đua, đội, trường đua trong bộ này hầu như không đổi theo thời gian và phạm vi đồ án không yêu cầu theo dõi lịch sử, nên dùng type 1 (ghi đè). | Phúc |
| Khi test lỗi thì dữ liệu sai đã vào bảng sự kiện chưa? | **Đã vào**, vì `dbt build` chạy test sau khi dựng model. Điều nhóm đảm bảo là pipeline dừng lại, watermark không được ghi, và sửa nguồn rồi chạy lại sẽ ghi đè dòng sai (như phần 6). Muốn chặn hẳn thì có thể đặt test lên tầng staging, trước khi nạp vào bảng sự kiện. | Trực |
| `DimDate` sao có tới 28.125 dòng? | Đây là lịch đầy đủ mọi ngày từ 1950 đến 2026 cộng 1 dòng Unknown, để Power BI dùng làm bảng ngày chuẩn (time intelligence). Số ngày có đua là 1.164. | Dũng |
| Tại sao giữ nguyên điểm gốc mà không quy đổi về thang điểm hiện tại? | Điểm gốc là sự thật lịch sử và khớp được với nguồn để đối soát. Quy đổi là một phép phân tích, có thể làm thành measure riêng ở Power BI. | Lộc |
| Nạp tăng dần dựa vào cột nào? | Cột `_ingested_at_utc` mà ETL Phase 1 ghi vào `stg`. Mỗi lần chạy, bảng sự kiện chỉ xử lý những dòng mới hơn giá trị lớn nhất mà nó đang có. | Trực |
| `OTHER` gồm những gì? | Các trạng thái không thuộc 4 nhóm rõ ràng, ví dụ không vượt qua vòng phân hạng (‘Did not qualify’, ‘Did not prequalify’). Danh sách đầy đủ có trong `status_outcome_mapping.csv`. | Lộc |

**Không nên nói khi demo:**
- Đừng nói “`DimDate` có 1.165 dòng” (con số trong báo cáo QA của Phúc). Số thật trên kho là **28.125**.
- Đừng nói 4 kịch bản QA đã chạy trên SQL Server. Kịch bản trong `phuc_phase2_qa_validation.md` chạy trên SQLite. Trên SQL Server thật, nhóm đã chạy nạp toàn bộ, nạp tăng dần có lỗi rồi sửa, và chạy lại (phần 3 và 6 của kịch bản này).

---

## Xử lý sự cố khi đang demo

| Sự cố | Cách xử lý nhanh |
|---|---|
| `dbtx` báo `ImportError: get_pyodbc_attrs_before` | Đang dùng nhầm image Mage gốc. Kiểm tra lệnh `dbtx` có dùng image `f1-dbt-demo` (bước A2). |
| `dbt debug` báo không kết nối được | `docker start miniprojectbi-sqlserver-test`, đợi khoảng 15 giây rồi chạy lại. Kiểm tra cổng `14339`. |
| `sql` báo `Login failed` | Chưa chạy dòng `export MSSQL_SA_PASSWORD=...` ở bước A3 trong terminal này. |
| Trang `localhost:8080` không lên | Terminal B đã tắt. Chạy lại lệnh ở bước A5. |
| Phần 6 quên sửa lại điểm về 10 | Chạy lại thao tác 3 của phần 6 trước khi sang phần 7, nếu không script thẩm định sẽ báo FAIL. |

## Sau buổi demo

Dữ liệu sau demo vẫn đúng (điểm đã được sửa về 10). Nếu muốn trả database về đúng trạng thái trước demo:

```zsh
sql "USE master; ALTER DATABASE F1_BI SET SINGLE_USER WITH ROLLBACK IMMEDIATE; RESTORE DATABASE F1_BI FROM DISK='/var/opt/mssql/data/F1_BI_before_demo.bak' WITH REPLACE; ALTER DATABASE F1_BI SET MULTI_USER"
```
