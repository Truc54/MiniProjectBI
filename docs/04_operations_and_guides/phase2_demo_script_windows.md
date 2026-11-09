# Kịch bản Demo Phase 2: dbt Transformation & Data Warehouse (Dành cho Windows)

**Đồ án:** Formula 1 Analytics (1950–2026) · **Nhóm:** Phúc, Dũng, Lộc, Trực  
**Thời lượng:** khoảng 15 phút demo + 5 phút hỏi đáp  
**Môi trường demo:** Windows 11, SQL Server 2025 (cổng 1433), Docker Desktop, SSMS 22, PowerShell  

> Mọi con số trong kịch bản này lấy từ lần chạy thật trên SQL Server cục bộ ngày 09/11/2026. Nếu lúc demo màn hình ra số khác, **nói đúng số trên màn hình**, đừng đọc thuộc lòng.

---

## 0. Tổng quan phân công & Chuẩn bị màn hình

| # | Phần | Người nói | Thời gian |
|---|---|---|:---:|
| 1 | Mở đầu & kiến trúc | Phúc | 1:30 |
| 2 | Quy tắc chuyển đổi & `OutcomeGroup` | Lộc | 2:00 |
| 3 | dbt project & build Star Schema | Trực | 2:30 |
| 4 | Kho dữ liệu vật lý trên SQL Server | Dũng | 2:00 |
| 5 | Lineage (dbt docs) | Trực | 1:00 |
| 6 | Kiểm thử: bắt lỗi, nạp tăng dần, chạy lại | Phúc | 2:30 |
| 7 | Thẩm định ngữ nghĩa 40+ điểm | Lộc | 1:30 |
| 8 | Điều phối bằng Mage | Trực | 1:00 |
| 9 | Kết luận | Phúc | 0:30 |

### Chuẩn bị các cửa sổ trước khi lên thuyết trình (Chuyển qua lại bằng `Alt + Tab`):

1. **Terminal A (PowerShell)**: Cỡ chữ to (18 trở lên), đặt tại `D:\MiniProjectBI`.
2. **SQL Server Management Studio (SSMS 22)**: Đã kết nối vào `localhost`, mở sẵn database `F1_BI`.
3. **VS Code**: Mở sẵn các file sau theo thứ tự trình bày:
   * `docs/02_data_dictionary_and_mapping/status_outcome_mapping.csv` (Phần 2)
   * `dbt/models/staging/stg_status.sql` (Phần 2)
   * `dbt/macros/generate_schema_name.sql` (Phần 3)
   * `dbt/models/marts/fact_race_result.sql` (Phần 3, 6)
   * `dbt/models/marts/schema.yml` (Phần 6)
   * `dbt/tests/assert_points_non_negative.sql` (Phần 6)
   * `mage/project/pipelines/f1_source_to_stage/metadata.yaml` (Phần 8)
   * `mage/project/custom/commit_watermark.py` (Phần 8)
4. **Trình duyệt (Chrome / Edge)**:
   * Tab 1: `http://localhost:8080` (dbt docs - Sơ đồ Lineage).
   * Tab 2: `http://localhost:6789` (Mage AI - Sơ đồ Pipeline ETL).

---

## A. Chuẩn bị trước giờ demo (30 phút trước, chuẩn bị âm thầm)

### A1. Khởi động Docker Desktop & SQL Server trên Windows
1. Đảm bảo ứng dụng **Docker Desktop** đang chạy (biểu tượng cá voi màu xanh góc taskbar báo `Engine running`).
2. Đảm bảo dịch vụ SQL Server đang chạy (mặc định đã chạy tự động trên cổng `1433`).

### A2. Khởi tạo 3 lệnh tắt trong PowerShell (Terminal A)
Mở cửa sổ PowerShell tại thư mục `D:\MiniProjectBI` và dán đoạn lệnh sau để có thể gõ các lệnh ngắn gọn khi tự thao tác từng bước:

```powershell
# Di chuyển vào repo
Set-Location D:\MiniProjectBI

# 1. Lệnh truy vấn SQL Server nhanh
function sql($query) { sqlcmd -S localhost -d F1_BI -U f1_loader -P "F1Loader@2026_SecurePwd!" -Q "SET NOCOUNT ON; $query" -C }

# 2. Lệnh chạy file script .sql
function sqlf($file) { Get-Content $file -Raw | sqlcmd -S localhost -d F1_BI -U f1_loader -P "F1Loader@2026_SecurePwd!" -C }

# 3. Lệnh chạy dbt qua Docker container (sử dụng image f1-dbt-demo)
function dbtx { docker run --rm -v "${PWD}/dbt:/dbt" -w /dbt --add-host host.docker.internal:host-gateway f1-dbt-demo:latest dbt $args --profiles-dir /dbt }

Clear-Host
```

### A3. Chạy tổng duyệt trước giờ thuyết trình
Chạy lần lượt 3 lệnh sau để kiểm tra trước toàn bộ hệ thống:

```powershell
# 1. Kiểm tra kết nối dbt
dbtx debug
# Kỳ vọng: All checks passed!

# 2. Build tổng duyệt toàn bộ 13 model và 48 tests
dbtx build --select +fact_race_result --full-refresh
# Kỳ vọng: Done. PASS=61 WARN=0 ERROR=0 SKIP=0 TOTAL=61

# 3. Sinh tài liệu dbt docs
dbtx docs generate
# Kỳ vọng: Catalog written to /dbt/target/catalog.json
```

### A4. Bật máy chủ dbt docs (Mở ở Terminal B riêng, giữ chạy suốt buổi)
Mở một cửa sổ PowerShell thứ hai (Terminal B) và chạy:

```powershell
docker run --rm -p 8080:8080 -v "D:\MiniProjectBI\dbt:/dbt" -w /dbt f1-dbt-demo:latest dbt docs serve --port 8080 --host 0.0.0.0 --no-browser
```

Mở trình duyệt kiểm tra trang `http://localhost:8080` đã hiển thị, sau đó quay lại Terminal A gõ `Clear-Host`.

---

## Phần 1. Mở đầu & Kiến trúc (Phúc, 1:30)

**Thao tác:** Chiếu sơ đồ kiến trúc trong slide hoặc file `plans/phase2_dbt_dw/00_ke_hoach_tong_quat_phase2.md`.

**Lời nói:**
> “Ở Phase 1, nhóm đã nạp 7 file CSV Formula 1 vào schema `stg` trên SQL Server, gồm 27.568 kết quả đua. Phase 2 biến dữ liệu thô đó thành kho dữ liệu dạng Star Schema theo phương pháp tiếp cận Kimball.
>
> Luồng gồm ba tầng:
> 1. Tầng `stg`: Lưu trữ dữ liệu thô từ ETL Phase 1.
> 2. Tầng `stg_clean`: dbt đọc từ `stg`, làm sạch kiểu dữ liệu và chuẩn hóa thông qua các view.
> 3. Tầng `dw`: Dựng 6 bảng chiều (Dimensions) và 1 bảng sự kiện (Fact) trong schema `dw`.
>
> Toàn bộ luồng được Mage AI điều phối và kiểm thử tự động ở mỗi lần chạy. Grain của bảng sự kiện là **một dòng cho mỗi kết quả của một tay đua trong một chặng đua**, tương ứng với một `resultId`.
>
> Nhóm phân công: Lộc làm quy tắc chuyển đổi & mapping, Trực viết dbt & tích hợp Mage, Dũng phụ trách vật lý SQL Server & tối ưu hóa chỉ mục, và tôi phụ trách kiến trúc & QA kiểm thử. Bây giờ mời Lộc trình bày quy tắc chuyển đổi.”

---

## Phần 2. Quy tắc chuyển đổi & `OutcomeGroup` (Lộc, 2:00)

**Thao tác 1 (VS Code):** Mở `docs/02_data_dictionary_and_mapping/status_outcome_mapping.csv`, cuộn qua vài dòng.

**Lời nói:**
> “Bảng `status` gốc có **141 mã trạng thái** rất vụn vặt: ‘Finished’, ‘+1 Lap’, ‘Engine’, ‘Gearbox’, ‘Accident’... Nếu phân tích trực tiếp trên 141 mã này sẽ rất rời rạc. Em gom chúng thành **5 nhóm nghiệp vụ chính**:
> - `CLASSIFIED`: Về đích hoặc được xếp hạng.
> - `RETIREMENT_DNF`: Bỏ cuộc giữa chừng do sự cố cơ học hoặc tai nạn.
> - `DNS`: Không thể xuất phát.
> - `DSQ`: Bị truất quyền thi đấu.
> - `OTHER`: Các trường hợp không phân hạng khác.
>
> Ví dụ trạng thái ‘+1 Lap’ nghĩa là về đích chậm một vòng nhưng vẫn hoàn thành chặng và được xếp hạng, do đó thuộc nhóm `CLASSIFIED`, chứ không phải bỏ cuộc.”

**Thao tác 2 (VS Code):** Mở `dbt/models/staging/stg_status.sql`, chỉ vào khối `CASE WHEN`.

**Lời nói:**
> “Trực đã đưa bảng phân loại này vào model `stg_status` của dbt. Sau Phase 2, em đã đối chiếu `dw.DimStatus` với file CSV: **141 trên 141 dòng khớp tuyệt đối**, không lệch dòng nào.
>
> Ngoài ra, em còn đặc tả các thước đo: cờ `is_win`, `is_podium`, số bậc tăng hạng `places_gained` (chỉ tính cho tay đua hoàn thành chặng và không xuất phát từ pit lane). Toàn bộ nằm trong từ điển dữ liệu `dw_data_dictionary.md`.”

**Thao tác 3 (Terminal A hoặc SSMS):** Chạy câu lệnh kiểm tra phân phối 5 nhóm trạng thái:

```powershell
sql "SELECT s.outcome_group, COUNT(*) AS so_dong FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk GROUP BY s.outcome_group ORDER BY so_dong DESC"
```

**Kết quả hiển thị trên màn hình:**

| outcome_group | so_dong |
|---|---:|
| CLASSIFIED | 15839 |
| RETIREMENT_DNF | 9771 |
| OTHER | 1538 |
| DNS | 258 |
| DSQ | 162 |

**Lời nói:**
> “Trên kho dữ liệu thật, 27.568 kết quả chia vào đúng 5 nhóm này. Tổng cộng lại đúng 27.568 dòng, bảo toàn 100% dữ liệu gốc. Mời Trực trình bày phần dbt.”

---

## Phần 3. dbt project & build Star Schema (Trực, 2:30)

**Thao tác 1 (VS Code):** Mở `dbt/macros/generate_schema_name.sql`.

**Lời nói:**
> “Project dbt tên `f1_bi`, gồm 7 model staging dạng view và 7 model mart. Mặc định dbt sẽ tự ghép prefix schema. Macro này ghi đè hành vi đó để các model được ghi chính xác vào schema `dw` và `stg_clean` trên SQL Server.”

**Thao tác 2 (Terminal A):** Kiểm tra cấu hình và kết nối dbt:
```powershell
dbtx debug
```
*(Chờ 3 giây, chỉ vào dòng cuối: `All checks passed!`)*

**Thao tác 3 (Terminal A):** Liệt kê đồ thị các model phụ thuộc của Fact:
```powershell
dbtx ls --resource-type model --select +fact_race_result
```

**Lời nói:**
> “Lệnh này liệt kê mọi model mà bảng sự kiện phụ thuộc: 6 view staging, 6 bảng chiều và chính bảng sự kiện, tổng cộng 13 model. Dấu cộng phía trước `+fact_race_result` nghĩa là biên dịch tuần tự từ các nhánh gốc lên.”

**Thao tác 4 (VS Code):** Mở `dbt/models/marts/fact_race_result.sql`, chỉ vào khối `config` và các hàm `coalesce(..., -1)`.

**Lời nói:**
> “Bảng sự kiện được thiết lập chế độ `incremental` với chiến lược `delete+insert` dựa trên khóa tự nhiên `source_result_id`. Khóa ngoại nào không tìm thấy ở bảng chiều sẽ tự động trỏ về `-1` (bản ghi Unknown Member). Nhờ vậy bảng Fact không bao giờ bị khóa mồ côi (orphan key).”

**Thao tác 5 (Terminal A):** Dựng lại toàn bộ Star Schema:
```powershell
dbtx build --select +fact_race_result --full-refresh
```

**Lời nói (trong lúc dbt đang chạy, khoảng 15 giây):**
> “Lệnh `dbt build` thực hiện đồng thời hai việc: vừa materialize dữ liệu vừa chạy bộ test kiểm tra tính toàn vẹn ngay sau mỗi model.”

**Kết quả hiển thị trên màn hình:**
```text
Done. PASS=61 WARN=0 ERROR=0 SKIP=0 TOTAL=61
```

**Lời nói:**
> “Toàn bộ 61 bước đều **PASS**: 13 model và 48 bài kiểm tra chất lượng dữ liệu. Sau đây mời Dũng trình bày về tầng vật lý trên SQL Server.”

---

## Phần 4. Kho dữ liệu vật lý trên SQL Server (Dũng, 2:00)

**Thao tác 1 (Terminal A hoặc mở SSMS bấm F5):** Kiểm tra số dòng thực tế trên SQL Server:

```powershell
sql "SELECT s.name + '.' + t.name AS bang, SUM(p.rows) AS so_dong FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1) WHERE s.name IN ('stg','dw') GROUP BY s.name, t.name ORDER BY 1"
```

**Kết quả hiển thị trên màn hình:**

| Bảng | Số dòng | Giải thích nghiệp vụ |
|---|---:|---|
| `dw.DimCircuit` | 79 | 78 trường đua + 1 bản ghi Unknown |
| `dw.DimConstructor` | 215 | 214 đội đua + 1 bản ghi Unknown |
| `dw.DimDate` | 28125 | Toàn bộ các ngày từ 1950 đến 2026 + 1 Unknown |
| `dw.DimDriver` | 880 | 879 tay đua + 1 bản ghi Unknown |
| `dw.DimRace` | 1165 | 1.164 chặng đua + 1 bản ghi Unknown |
| `dw.DimStatus` | 142 | 141 mã trạng thái + 1 bản ghi Unknown |
| `dw.FactRaceResult` | 27568 | Khớp tuyệt đối 100% với số dòng `stg.results` |

**Lời nói:**
> “Mỗi bảng chiều có đúng thêm 1 dòng so với dữ liệu nguồn, đó là bản ghi Unknown Member (`SK = -1`). Riêng `DimDate` là bảng ngày hoàn chỉnh từ năm 1950 đến hết 2026 (28.125 dòng) phục vụ phân tích Time Intelligence trên Power BI. Bảng Fact đạt chính xác 27.568 dòng.”

**Thao tác 2 (Terminal A hoặc SSMS):** Kiểm tra chỉ mục Columnstore:

```powershell
sql "SELECT OBJECT_SCHEMA_NAME(object_id) + '.' + OBJECT_NAME(object_id) AS bang, type_desc FROM sys.indexes WHERE type_desc LIKE '%COLUMNSTORE%'"
```

**Kết quả:** 7 dòng `CLUSTERED COLUMNSTORE` cho Fact và 6 Dimension.

**Lời nói:**
> “Toàn bộ các bảng trong schema `dw` được đánh chỉ mục **Clustered Columnstore Index (CCI)**. Dữ liệu được lưu trữ theo dạng cột và nén với tỷ lệ cao, giúp các truy vấn tổng hợp phân tích BI chạy nhanh hơn từ 5 đến 10 lần so với lưu trữ dòng truyền thống.”

**Thao tác 3 (Truy vấn nghiệp vụ Star Schema):**

```powershell
sql "SELECT TOP 5 d.full_name, SUM(CAST(f.is_win AS int)) AS thang, SUM(CAST(f.is_podium AS int)) AS podium, SUM(f.points) AS diem FROM dw.FactRaceResult f JOIN dw.DimDriver d ON d.driver_sk = f.driver_sk GROUP BY d.full_name ORDER BY thang DESC"
```

**Kết quả hiển thị trên màn hình:**

| full_name | thang | podium | diem |
|---|---:|---:|---:|
| Lewis Hamilton | 106 | 207 | 5134.50 |
| Michael Schumacher | 91 | 155 | 1566.00 |
| Max Verstappen | 71 | 134 | 3452.50 |
| Sebastian Vettel | 53 | 122 | 3098.00 |
| Alain Prost | 51 | 106 | 798.50 |

**Lời nói:**
> “Đây là một câu hỏi phân tích trả lời trực tiếp trên Star Schema: Top 5 tay đua vĩ đại nhất lịch sử. Phép join giữa `FactRaceResult` và `DimDriver` phản hồi tức thì.
>
> Một điểm thú vị ở cột điểm: Michael Schumacher thắng 91 chặng nhưng chỉ có 1.566 điểm, trong khi Lewis Hamilton có hơn 5.100 điểm. Đó là vì quy định tính điểm F1 đã thay đổi theo thời kỳ (trước 2010 nhất chặng chỉ được 10 điểm, sau 2010 là 25 điểm). Nhóm giữ nguyên điểm gốc lịch sử để đối soát chính xác với nguồn.”

---

## Phần 5. Lineage bằng dbt docs (Trực, 1:00)

**Thao tác (Trình duyệt):** Chuyển sang tab `http://localhost:8080`.
1. Nhấp chọn `fact_race_result` ở danh sách model bên trái.
2. Nhấp vào nút tròn có biểu tượng sơ đồ **Lineage** ở góc dưới cùng bên phải.

**Lời nói:**
> “Đây là tài liệu tự động do dbt sinh ra. Sơ đồ Lineage trực quan hóa toàn bộ hành trình của dòng dữ liệu: từ 7 bảng thô `stg`, đi qua các view làm sạch `stg_clean`, cho đến các bảng chiều và bảng sự kiện `dw`.
>
> Khi một nguồn cấp thay đổi, nhìn vào sơ đồ này nhóm có thể đánh giá được ngay phạm vi ảnh hưởng (Impact Analysis).”

---

## Phần 6. Kiểm thử: bắt lỗi, nạp tăng dần, chạy lại (Phúc, 2:30)

**Thao tác 1 (VS Code):** Mở `dbt/tests/assert_points_non_negative.sql`.

**Lời nói:**
> “Nhóm thiết lập 48 bài kiểm tra dbt, bao gồm: kiểm tra khóa chính duy nhất, khóa ngoại toàn vẹn tham chiếu, miền giá trị hợp lệ, và các kiểm thử nghiệp vụ đặc thù như điểm không được âm.
>
> Bây giờ tôi sẽ mô phỏng tình huống đưa dữ liệu bẩn vào Staging xem hệ thống có bắt được lỗi không.”

**Thao tác 2 (Tạo lỗi điểm âm trong Terminal A):**
```powershell
sql "UPDATE stg.results SET points = -5, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1"
dbtx build --select +fact_race_result
```

**Kết quả hiển thị trên màn hình:**
```text
FAIL 1 assert_points_non_negative ... [FAIL 1 ...]
Got 1 result, configured to fail if != 0
Done. PASS=60 WARN=0 ERROR=1 SKIP=0 TOTAL=61
```

**Lời nói:**
> “Bản ghi `resultId = 1` của Hamilton bị sửa thành âm 5 điểm. dbt lập tức chặn lại và báo **ERROR = 1**, không cho phép đánh dấu batch thành công.”

**Thao tác 3 (Sửa lại đúng & nạp tăng dần):**
```powershell
sql "UPDATE stg.results SET points = 10, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1"
dbtx build --select +fact_race_result
sql "SELECT COUNT(*) AS so_dong, COUNT(DISTINCT source_result_id) AS so_khoa, SUM(points) AS tong_diem FROM dw.FactRaceResult"
```

**Kết quả hiển thị trên màn hình:**
```text
Done. PASS=61 WARN=0 ERROR=0 SKIP=0 TOTAL=61
```
| so_dong | so_khoa | tong_diem |
|---:|---:|---:|
| 27568 | 27568 | 57126.05 |

**Lời nói:**
> “Sau khi sửa dữ liệu về 10 điểm và build lại: toàn bộ 61 bước lại PASS. Nhờ chiến lược `delete+insert`, dòng cũ được ghi đè chứ không nhân đôi, tổng số dòng vẫn chuẩn xác 27.568. Mời Lộc trình bày kiểm định ngữ nghĩa.”

---

## Phần 7. Thẩm định ngữ nghĩa 40+ điểm (Lộc, 1:30)

**Thao tác (Terminal A hoặc mở SSMS chạy F5):**
```powershell
sqlf sqlserver\dw\loc_semantic_validation.sql
```

**Kết quả hiển thị trên màn hình:**
```text
total_checks passed      failed     
------------ ----------- -----------
          40          40           0
```
*(Kèm dòng mẫu: `1 | Lewis Hamilton | McLaren | 2008 R01 Australian Grand Prix | ... | Finished | CLASSIFIED | 10.00`)*

**Lời nói:**
> “Script này của em kiểm tra **ý nghĩa nghiệp vụ chuyên sâu**: 40 điểm kiểm định đối chiếu chéo giữa `dw`, `stg` và baseline độc lập từ CSV:
> - Số lượt về nhất: 1.167 lượt (bao gồm 3 lượt chia sẻ xe trong thập niên 1950).
> - Số lượt lên bục podium: 3.513 lượt.
> - Điểm số tối đa của người thắng chặng ở từng mùa giải khớp đúng theo từng kỷ nguyên F1.
>
> Kết quả: **40 trên 40 bài test đều PASS** trên dữ liệu thật. Mời Trực trình bày phần điều phối.”

---

## Phần 8. Điều phối bằng Mage AI (Trực, 1:00)

**Thao tác (Trình duyệt):** Chuyển sang tab `http://localhost:6789`, mở Pipeline `f1_source_to_stage`.

**Lời nói:**
> “Pipeline Mage gồm chuỗi 5 block hoàn chỉnh:
> 1. `load_f1_csv`: Đọc dữ liệu từ file CSV.
> 2. `validate_f1_table`: Làm sạch và kiểm tra cấu trúc.
> 3. `load_sqlserver`: Nạp vào bảng thô `stg`.
> 4. `dbt_transformation`: Tự động gọi dbt transform sang Star Schema.
> 5. `commit_watermark`: Ghi nhận mốc batch thành công vào `ctl.etl_batch_state`.
>
> Thiết kế này đảm bảo an toàn giao dịch: chỉ khi dbt hoàn thành không có lỗi thì mốc watermark mới được ghi nhận. Nếu dbt gặp lỗi dữ liệu bẩn như phần 6 vừa demo, pipeline sẽ dừng lại và giữ nguyên trạng thái an toàn.”

---

## Phần 9. Kết luận (Phúc, 0:30)

**Lời nói:**
> “Tổng kết lại, trong Phase 2 nhóm đã hoàn thành toàn diện:
> 1. Xây dựng Star Schema chuẩn Kimball với 1 Fact và 6 Dimensions trên SQL Server.
> 2. Đạt 100% PASS trên cả 61 bước build test dbt và 40 điểm thẩm định ngữ nghĩa nghiệp vụ.
> 3. Tối ưu hóa hiệu năng bằng Clustered Columnstore Index và tự động hóa qua Mage AI.
> 4. Đây là nền tảng dữ liệu sạch, chuẩn hóa cao cho các dashboard Power BI ở Phase 3 tiếp theo.
>
> Nhóm xin chân thành cảm ơn Thầy Cô và các bạn đã lắng nghe!”

---

## Phụ lục: Câu hỏi đáp thường gặp (Q&A)

| Câu hỏi | Câu trả lời cốt lõi | Người trả lời |
|---|---|---|
| **Tại sao Surrogate Key (SK) lại bằng ID gốc?** | Nguồn Kaggle F1 có ID duy nhất và cố định. Giữ SK bằng Natural Key giúp việc rebuild bảng Dimension không làm gãy khóa ngoại đã nạp vào bảng Fact tăng dần. | Phúc |
| **Tại sao không dùng SCD Type 2?** | Thông tin tay đua, đội đua và trường đua F1 trong phạm vi đồ án không đòi hỏi theo dõi lịch sử thay đổi phiên bản theo thời gian, nên SCD Type 1 là tối ưu nhất. | Phúc |
| **Bảng `DimDate` tại sao có tới 28.125 dòng?** | Đây là bảng lịch chuẩn đủ mọi ngày từ 1950 đến 2026 (dù có đua hay không), giúp Power BI tính toán các hàm thời gian (Time Intelligence: YTD, MTD, YoY). | Dũng |
| **Khi dbt test lỗi thì dòng sai đã vào Fact chưa?** | Dòng sai đã được chèn vào Fact vì dbt build chạy test sau khi dựng dữ liệu. Tuy nhiên pipeline dừng lại, không ghi watermark, và khi sửa dữ liệu nạp lại thì dòng sai sẽ bị ghi đè hoàn toàn. | Trực |
| **Tại sao giữ điểm gốc thay vì quy đổi về thang điểm mới?** | Điểm gốc là sự thật lịch sử và dùng để đối soát 100% với nguồn. Việc quy đổi điểm có thể xử lý linh hoạt bằng các Measure trên Power BI ở Phase 3. | Lộc |

