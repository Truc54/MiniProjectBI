# Kịch Bản Master: Quay Video Demo & Lời Thoại Thuyết Trình (All-In-One)

**Đồ án:** Formula 1 Analytics (1950–2026) · MiniProject BI (Nhóm 7)  
**Sinh viên thực hiện:** Trần Lê Trung Trực, Nguyễn Hồng Phúc, Dương Viết Dũng, Lê Văn Lộc  
**Giảng viên hướng dẫn:** ThS. Hồ Thị Hoàng Vy, ThS. Tiết Gia Hồng  
**Thời lượng:** Video quay gọn từ 6 – 8 phút; khi thuyết trình có thể dừng ngắt video tại các điểm `[PAUSE]` để mở rộng thành 10 – 15 phút.

---

## 0. CHUẨN BỊ MÔI TRƯỜNG & CỬA SỔ (Trước khi bấm quay)

1. **VS Code:** Mở sẵn thư mục `miniprojectBI`, mở sẵn các tab theo thứ tự:
   * `dataset/results.csv` (File dữ liệu thô)
   * `dbt/models/staging/formula1/stg_status.sql`
   * `dbt/models/marts/dim_race.sql`
   * `dbt/models/marts/fact_race_result.sql`
2. **Trình duyệt (Chrome / Edge):**
   * Tab 1: `http://localhost:6789` (Mage AI - Pipeline `f1_source_to_stage`)
   * Tab 2: `http://localhost:8080` (dbt docs - Sơ đồ Lineage Graph)
3. **SSMS (SQL Server Management Studio):** Kết nối vào `localhost`, mở sẵn database `F1_BI` với các câu lệnh SQL ở mục Phụ lục.
4. **Terminal (PowerShell):** Cỡ chữ to 18pt, nền tối rõ nét.

---

## PHẦN 1: BÀI TOÁN, DATASET & THIẾT KẾ SCHEMA (2 – 3 phút)

### 🎬 Thao tác trên màn hình:
* Mở **Slide kiến trúc** hoặc mở file sơ đồ dữ liệu trong VS Code.
* Mở thư mục `dataset/`, mở nhanh file `dataset/results.csv` lướt nhẹ qua các dòng dữ liệu thô và ký tự `\N`.

### 🎙️ Lời thoại thuyết trình:
> "Kính chào Thầy Cô và các bạn. Hôm nay em xin đại diện Nhóm 7 trình bày video demo giải pháp xây dựng Kho Dữ Liệu và Phân tích giải đua xe Formula 1 giai đoạn lịch sử từ 1950 đến 2026.
>
> **1. Về nguồn dữ liệu:**
> Bộ dữ liệu F1 từ Kaggle gồm 17 file CSV với hơn 750.000 dòng. Tuy nhiên, nhóm không nạp tràn lan mà khảo sát và chọn ra **7 file lõi** (tổng cộng 30.121 dòng) đại diện cho đúng một quy trình nghiệp vụ trọng tâm: **Kết quả thi đấu chính thức của một tay đua trong một chặng Grand Prix**:
> * `results.csv` (27.568 dòng): Bảng sự kiện trung tâm ghi nhận kết quả từng tay đua (điểm số, vị trí xuất phát `grid`, thứ tự về đích `position`).
> * `races.csv` (1.164 dòng): Danh mục các chặng đua qua 77 mùa giải (năm đua, vòng đua, ngày diễn ra).
> * `drivers.csv` (879 dòng): Danh mục hồ sơ tay đua (họ tên, mã code, số xe, quốc tịch, ngày sinh).
> * `constructors.csv` (214 dòng): Danh mục các đội đua / nhà sản xuất xe (Ferrari, McLaren, Mercedes...).
> * `circuits.csv` (78 dòng): Danh mục trường đua và tọa độ địa lý (tên trường đua, thành phố, quốc gia, độ cao).
> * `status.csv` (141 dòng): Danh mục trạng thái kết thúc cuộc đua (`Finished`, hỏng động cơ, va chạm, bị loại...).
> * `seasons.csv` (77 dòng): Danh mục các mùa giải từ 1950 đến 2026, dùng để kiểm tra độ bao phủ thời gian.
>
> *(Mười file còn lại như `lap_times`, `pit_stops`, `qualifying` có hạt dữ liệu khác—từng vòng, từng giây—hoặc chỉ có dữ liệu cho 2 mùa 2025/2026 nên được tách ra để tránh làm loãng mô hình).*
>
> **2. Thiết kế Lược đồ hình sao (Star Schema) & Lý do lựa chọn:**
> Dựa trên phương pháp luận Kimball, nhóm thiết kế mô hình gồm **1 bảng Fact trung tâm** và **6 bảng Dimension**:
> * **Bảng Fact (`FactRaceResult`):** Có hạt dữ liệu (Grain) là **một dòng cho mỗi `resultId`** (kết quả của 1 tay đua trong 1 chặng). Fact lưu các số đo cộng được như `points`, vị trí xuất phát `grid`, vị trí về đích `position`, cùng các cờ nhị phân `is_win`, `is_podium`.
> * **Sáu bảng Dimension:** `DimDate` (thời gian), `DimRace` (chặng đua), `DimCircuit` (đường đua/địa điểm), `DimDriver` (tay đua), `DimConstructor` (đội đua) và `DimStatus` (trạng thái kết thúc).
>
> **Tại sao nhóm lại thiết kế Star Schema phẳng mà không dùng Snowflake Schema?**
> * **Thứ nhất, tối ưu hiệu năng truy vấn BI:** Nhóm gom thông tin mùa giải (`seasons`) trực tiếp vào `DimRace`, gom quốc gia/thành phố vào `DimCircuit`. Các bảng Dim nối trực tiếp 1-nhiều với Fact, không nối bắc cầu. Điều này giúp các dashboard Power BI chỉ cần 1 bước JOIN là lấy được dữ liệu, tốc độ phản hồi cực nhanh.
> * **Thứ hai, trả lời trọn vẹn 6 câu hỏi nghiệp vụ (BQ1 - BQ6):** Mô hình này đáp ứng đầy đủ mọi góc nhìn: phân tích điểm số theo mùa giải, so sánh thành tích giữa các tay đua và đội đua, tương quan giữa vị trí xuất phát lưới (`grid`) với vị trí về đích (`position`), và tỷ lệ bỏ cuộc (`DNF`) do lỗi cơ học hay tai nạn."

---

> ⏸️ **[ĐIỂM DỪNG 1: TẠM DỪNG NẾU CẦN GIẢI THÍCH SÂU CHO CÔ]**  
> *"Thưa Cô, việc chọn đúng hạt dữ liệu (Grain) là `results.resultId` giúp bảo toàn trọn vẹn 27.568 kết quả thi đấu lịch sử của F1 mà không bị tổng hợp non (pre-mature aggregation), đảm bảo dữ liệu ở mức chi tiết nhất phục vụ mọi phép cắt lát sau này."*

---

## PHẦN 2: QUY TRÌNH NẠP STAGING BẰNG MAGE AI (1 – 2 phút)

### 🎬 Thao tác trên màn hình:
* Chuyển sang trình duyệt: Tab **Mage AI** (`http://localhost:6789`).
* Mở Pipeline `f1_source_to_stage`, zoom vào sơ đồ đồ thị DAG 5 block.
* Nhấp vào tab **Runs / Logs** chỉ vào lần chạy thành công gần nhất.

### 🎙️ Lời thoại thuyết trình:
> "Tiếp theo là quy trình nạp dữ liệu (Ingestion) bằng **Mage AI**.
> Pipeline `f1_source_to_stage` được thiết kế theo chuẩn đồ thị có hướng (DAG) khép kín gồm 5 block:
> 1. `load_f1_csv`: Đọc an toàn 7 file CSV nguồn từ Kaggle.
> 2. `validate_f1_table`: Kiểm tra cấu trúc file, ép kiểu dữ liệu chuẩn, chuyển toàn bộ ký tự `\N` và chuỗi rỗng thành `SQL NULL`, giữ nguyên giá trị `0` hợp lệ.
> 3. `load_sqlserver`: Nạp dữ liệu vào schema `stg` trên SQL Server. Hỗ trợ cả 2 chế độ: **Full Load** và **Incremental Load** theo từng khoảng khóa tự nhiên (Natural Key).
> 4. `dbt_transformation`: Tự động gọi container dbt để kích hoạt luồng biến đổi dữ liệu sang kho `dw`.
> 5. `commit_watermark`: Bước chốt chặn an toàn giao dịch.
>
> **Điểm nổi bật về tính an toàn:** Nếu dbt gặp dữ liệu bẩn thì toàn bộ pipeline dừng lại ngay lập tức và mốc watermark không được ghi nhận. Nhờ đó, hệ thống không bao giờ có trạng thái 'thành công giả' và cho phép chạy lại (idempotent) mà không sợ sinh bản ghi trùng."

---

## PHẦN 3: ĐỐI SOÁT TRỰC QUAN 2 TẦNG BIẾN ĐỔI DBT (STAGING $\rightarrow$ VIEW SẠCH $\rightarrow$ DW) (2 – 3 phút)

### 🎬 Thao tác trên màn hình:
* Chuyển sang **SSMS**, bôi đen và chạy lần lượt 3 block query trực quan:
  1. **Block 1 (Tầng Staging $\rightarrow$ View `stg_clean`):** So sánh `stg.drivers` và `stg_clean.stg_drivers` (thấy rõ việc đổi tên cột snake_case, cắt khoảng trắng và sinh cột `full_name`).
  2. **Block 2 (Tầng View $\rightarrow$ Dimension DW):** So sánh `stg.status` và `dw.DimStatus` (thấy rõ việc gom 141 mã status thành 5 nhóm `outcome_group`).
  3. **Block 3 (Tầng View $\rightarrow$ Fact DW):** So sánh `stg.results` và `dw.FactRaceResult` (thấy rõ việc sinh cờ `is_win`, tính `places_gained` và ánh xạ SK).

### 🎙️ Lời thoại thuyết trình:
> "Trong dbt, nhóm chia quá trình biến đổi dữ liệu thành **2 tầng rõ ràng**: từ bảng thô sang View làm sạch, rồi từ View làm sạch dựng mô hình Kho DW:
>
> **1. Tầng 1: Từ Bảng thô `stg` $\rightarrow$ View làm sạch `stg_clean` (Làm sạch & Chuẩn hóa tên cột):**
> *(Chạy và chỉ vào kết quả so sánh bảng `drivers`)*
> * **Ở nguồn thô (`stg.drivers`):** Tên cột dùng chuẩn `camelCase` của file gốc (`driverId`, `driverRef`, `dob`), dữ liệu chuỗi có thể dính khoảng trắng ở 2 đầu, và họ tên bị tách thành 2 cột `forename`, `surname`.
> * **Sau khi qua view dbt (`stg_clean.stg_drivers`):**
>   * dbt **đổi tên toàn bộ cột sang chuẩn `snake_case` đồng nhất**: `driverId` $\rightarrow$ `driver_id`, `dob` $\rightarrow$ `date_of_birth`.
>   * Dùng hàm `LTRIM(RTRIM(...))` để **cắt sạch khoảng trắng dư thừa ở 2 đầu** văn bản, đồng thời dùng `NULLIF(..., N'')` để đưa chuỗi rỗng về đúng chuẩn `SQL NULL`.
>   * Ghép tự động `forename + surname` thành một cột hiển thị hoàn chỉnh là **`full_name`**.
>
> **2. Tầng 2: Từ View làm sạch $\rightarrow$ Kho dữ liệu Star Schema `dw` (Mô hình hóa & Làm giàu):**
> *(Chạy tiếp so sánh bảng `status` và bảng `Fact`)*
> * **Chuẩn hóa trạng thái (`dw.DimStatus`):** 141 mã status rời rạc ở nguồn được dbt phân loại thành **5 nhóm chiến lược (`outcome_group`)**: `Finished` thành `CLASSIFIED`, `Accident` hay `Engine` gom về `RETIREMENT_DNF`, `Disqualified` thành `DSQ`.
> * **Làm giàu dữ liệu bảng Fact (`dw.FactRaceResult`):**
>   * Khóa tự nhiên được thay bằng khóa đại diện (`driver_sk`, `race_sk`), nếu thiếu thông tin sẽ tự động fallback về bản ghi ngoại lệ **`-1 (Unknown Member)`**.
>   * dbt tự động tính số bậc vượt hạng: `places_gained = grid - finish`.
>   * dbt sinh sẵn các cờ nhị phân kiểu `BIT`: `is_win = 1`, `is_podium = 1`, `is_classified = 1` giúp Power BI chỉ cần kéo thả là đếm được ngay mà không cần viết DAX phức tạp."

---

> ⏸️ **[ĐIỂM DỪNG 2: GIẢI THÍCH INCREMENTAL CỦA FACT NẾU CÔ HỎI]**  
> *(Dừng video ở bảng so sánh Fact)*  
> *"Thưa Cô, bảng Fact được nạp theo cơ chế tăng dần `incremental` với chiến lược `delete+insert`. Điều kiện so sánh `_ingested_at_utc > max(_ingested_at_utc)` giúp hệ thống chỉ bốc đúng các bản ghi chặng đua mới nạp hôm nay để đưa vào Fact, bỏ qua 70 năm lịch sử cũ, tối ưu thời gian chạy từ vài phút xuống còn vài giây."*

---

> ⏸️ **[ĐIỂM DỪNG 2: GIẢI THÍCH INCREMENTAL CỦA FACT NẾU CÔ HỎI]**  
> *(Dừng video ở bảng so sánh Fact)*  
> *"Thưa Cô, bảng Fact được nạp theo cơ chế tăng dần `incremental` với chiến lược `delete+insert`. Điều kiện so sánh `_ingested_at_utc > max(_ingested_at_utc)` giúp hệ thống chỉ bốc đúng các bản ghi chặng đua mới nạp hôm nay để đưa vào Fact, bỏ qua 70 năm lịch sử cũ, tối ưu thời gian chạy từ vài phút xuống còn vài giây."*

---

## PHẦN 4: SƠ ĐỒ LINEAGE & THỰC THI DBT BUILD (1 – 2 phút)

### 🎬 Thao tác trên màn hình:
* Chuyển sang trình duyệt: Tab **dbt docs** (`http://localhost:8080`), bấm nút **Lineage Graph** góc dưới phải, rê chuột qua các nhánh phụ thuộc.
* Chuyển sang **Terminal PowerShell**, chạy lệnh:
  ```powershell
  docker run --rm --env-file .env -v "${PWD}/dbt:/dbt" -w /dbt --add-host host.docker.internal:host-gateway f1-dbt-demo:latest dbt build --select +fact_race_result --profiles-dir /dbt
  ```
* Chờ màn hình chạy xong, bôi đen dòng kết quả: **`Done. PASS=61 WARN=0 ERROR=0`**.

### 🎙️ Lời thoại thuyết trình:
> "Trên màn hình là **Sơ đồ Lineage (Cây phả hệ dữ liệu)** do dbt sinh ra. Khi gõ lệnh `dbt build --select +fact_race_result`, toán tử dấu `+` chỉ định dbt lần ngược lại cây phả hệ để nạp các view Staging trước $\rightarrow$ dựng 6 Dimension $\rightarrow$ cuối cùng mới nạp Fact.
>
> *(Chỉ vào Terminal)*
> Lệnh `dbt build` chạy đồng thời việc tạo bảng vật lý và thực thi 48 bài data tests. 
> Kết quả trên màn hình: **Toàn bộ 61 bước đều PASS** (13 models và 48 tests), đảm bảo 100% tính toàn vẹn khóa chính, khóa ngoại và miền giá trị."

---

## PHẦN 5: KIỂM TRA ĐỐI SOÁT TRỰC QUAN TRÊN SSMS (2 – 3 phút)

### 🎬 Thao tác trên màn hình:
* Chuyển sang **SSMS**, bôi đen và chạy lần lượt 4 câu lệnh truy vấn đã chuẩn bị sẵn:
  1. *Query 1:* Đếm số dòng so sánh giữa `stg` và `dw`.
  2. *Query 2:* Kiểm tra chỉ mục Columnstore Index.
  3. *Query 3:* Xem chi tiết 1 dòng của Lewis Hamilton (`source_result_id = 1`).
  4. *Query 4:* Truy vấn Top 5 tay đua nhiều trận thắng nhất lịch sử.

### 🎙️ Lời thoại thuyết trình:
> "Bây giờ chúng ta vào thẳng SQL Server để đối soát kết quả thực tế:
>
> **1. Đối soát số dòng:**
> * Bảng nguồn `stg.results` có **27.568 dòng**.
> * Bảng đích `dw.FactRaceResult` đạt chính xác **27.568 dòng**, bảo toàn 100% dữ liệu gốc.
> * Các bảng Dim đều có thêm đúng 1 dòng ngoại lệ `-1`. Riêng `DimDate` có đủ 28.125 ngày từ 1950 đến 2026 để phục vụ phân tích Time Intelligence.
>
> **2. Kiểm tra chỉ mục Columnstore:**
> Toàn bộ 7 bảng trong schema `dw` đều được đánh chỉ mục **Clustered Columnstore Index (CCI)**. Đây là công nghệ lưu trữ theo cột hiện đại của SQL Server, giúp nén dữ liệu và tăng tốc độ truy vấn tổng hợp BI lên từ 5 đến 10 lần.
>
> **3. Đối soát 1 dòng chi tiết của Lewis Hamilton:**
> Dòng kết quả chặng Úc năm 2008 của Hamilton cho thấy trạng thái `Finished` đã được chuẩn hóa thành `CLASSIFIED`, các khóa ngoại `driver_sk`, `race_sk` đều trỏ chính xác, và các cờ `is_win = 1`, `is_podium = 1` được tính đúng tuyệt đối.
>
> **4. Truy vấn phân tích nghiệp vụ Star Schema:**
> Chạy thử câu query tìm **Top 5 tay đua nhiều chiến thắng nhất lịch sử**:
> Câu lệnh phản hồi tức thì: Đứng đầu là Lewis Hamilton với 106 chiến thắng, tiếp theo là Michael Schumacher (91) và Max Verstappen (71)."

---

> ⏸️ **[ĐIỂM DỪNG 3: CHIA SẺ INSIGHT ĐIỂM SỐ NẾU CẦN]**  
> *"Thưa Thầy Cô, một điểm thú vị là Michael Schumacher có 91 chiến thắng nhưng chỉ được 1.566 điểm, trong khi Hamilton có hơn 5.100 điểm. Đó là vì thang điểm F1 đã thay đổi từ sau năm 2010. Nhóm quyết định giữ nguyên điểm gốc lịch sử ở tầng DW để đối soát chuẩn 1-1 với nguồn, và sự chênh lệch này sẽ được chuẩn hóa linh hoạt bằng DAX trên Power BI ở Phase 3."*

---

## PHẦN 6: DEMO CHẶN LỖI DỮ LIỆU & NẠP TĂNG DẦN (1 – 2 phút)

### 🎬 Thao tác trên màn hình:
1. Chạy lệnh cố tình sửa điểm thành số âm trong SSMS:
   ```sql
   UPDATE stg.results SET points = -5, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1;
   ```
2. Trong Terminal PowerShell, chạy lại lệnh build:
   ```powershell
   docker run --rm --env-file .env -v "${PWD}/dbt:/dbt" -w /dbt --add-host host.docker.internal:host-gateway f1-dbt-demo:latest dbt build --select +fact_race_result --profiles-dir /dbt
   ```
   $\rightarrow$ Màn hình hiện chữ đỏ **`FAIL 1 assert_points_non_negative`**, dừng quy trình.
3. Trong SSMS, sửa lại điểm hợp lệ (`points = 10`):
   ```sql
   UPDATE stg.results SET points = 10, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1;
   ```
4. Trong Terminal PowerShell, chạy lại lệnh build:
   ```powershell
   docker run --rm --env-file .env -v "${PWD}/dbt:/dbt" -w /dbt --add-host host.docker.internal:host-gateway f1-dbt-demo:latest dbt build --select +fact_race_result --profiles-dir /dbt
   ```
   $\rightarrow$ Màn hình xanh báo **`Done. PASS=61 WARN=0 ERROR=0`**.
5. Chạy câu lệnh đếm dòng trong SSMS: Tổng số dòng vẫn chuẩn xác là **27.568 dòng**.

### 🎙️ Lời thoại thuyết trình:
> "Một hệ thống BI chuyên nghiệp phải có khả năng **chặn đứng dữ liệu rác**.
>
> Để kiểm thử:
> 1. Nhóm cố tình sửa điểm của một tay đua thành số âm (`points = -5`) trong Staging.
> 2. Khi chạy `dbt build`, bài test `assert_points_non_negative` lập tức phát hiện và **báo FAIL**, chặn không cho dữ liệu lỗi được hợp thức hóa.
> 3. Sau khi sửa lại điểm số hợp lệ và build lại: toàn bộ 61 bước lại chuyển sang màu xanh **PASS**.
>
> Nhờ chiến lược `delete+insert`, dòng dữ liệu được cập nhật ghi đè chính xác mà không làm tăng số dòng, tổng số dòng của Fact vẫn giữ nguyên chuẩn xác là **27.568 dòng**."

---

## PHẦN 7: TỔNG KẾT & KẾ HOẠCH PHASE 3 (1 phút)

### 🎬 Thao tác trên màn hình:
* Quay lại Slide hoặc mở file `README.md` của dự án.

### 🎙️ Lời thoại thuyết trình:
> "Tổng kết lại, nhóm đã hoàn thành toàn diện các mục tiêu kỹ thuật:
> 1. Xây dựng pipeline ELT tự động, đồng bộ từ CSV qua Mage AI đến SQL Server.
> 2. Thiết kế mô hình Star Schema chuẩn Kimball với 1 Fact và 6 Dimensions.
> 3. Đạt tỷ lệ **100% PASS** trên cả 61 bài test dbt và 40 điểm thẩm định ngữ nghĩa nghiệp vụ.
> 4. Tối ưu hóa hiệu năng bằng Clustered Columnstore Index.
>
> Đây là nền tảng dữ liệu sạch và chuẩn hóa vững chắc để nhóm bước vào Phase 3: Xây dựng Semantic Model, các thước đo DAX và thiết kế Dashboard tương tác trên Power BI.
>
> Em xin chân thành cảm ơn Thầy Cô và các bạn đã chú ý lắng nghe!"

---

---

## PHỤ LỤC: CÁC ĐOẠN LỆNH SQL DÙNG ĐỂ CHẠY TRONG LÚC DEMO SSMS

```sql
USE F1_BI;
GO

-- ==============================================================================
-- NHÓM A: DÙNG CHO PHẦN 3 (ĐỐI SOÁT TRỰC QUAN 2 TẦNG BIẾN ĐỔI DBT)
-- ==============================================================================

-- 1. Tầng 1 (Bảng thô stg -> View sạch stg_clean):
-- Biến đổi: Đổi tên cột snake_case, LTRIM/RTRIM cắt khoảng trắng 2 đầu, NULLIF chuỗi rỗng, ghép full_name
-- [TRƯỚC - BẢNG THÔ]:
SELECT TOP 3 driverId, driverRef, forename, surname, dob FROM stg.drivers;
-- [SAU - VIEW LÀM SẠCH]:
SELECT TOP 3 driver_id, driver_ref, full_name, date_of_birth FROM stg_clean.stg_drivers;

-- 2. Tầng 2 (View sạch -> Dimension DW):
-- Biến đổi: Gom 141 mã status vụn vặt sang 5 nhóm OutcomeGroup chuẩn mực
-- [TRƯỚC - NGUỒN]:
SELECT TOP 4 statusId, status FROM stg.status WHERE statusId IN (1, 3, 4, 130);
-- [SAU - KHO DW]:
SELECT status_sk, status_label, outcome_group, outcome_category 
FROM dw.DimStatus WHERE status_sk IN (1, 3, 4, 130);

-- 3. Tầng 2 (View sạch -> Fact DW):
-- Biến đổi: Sinh mã chuẩn hóa, tính số bậc tăng hạng places_gained, sinh cờ nhị phân is_win, is_podium
-- [TRƯỚC - NGUỒN]:
SELECT resultId, raceId, driverId, grid, position, positionText, points 
FROM stg.results WHERE resultId = 1;
-- [SAU - KHO DW]:
SELECT source_result_id, race_sk, driver_sk, result_outcome_code, 
       grid_position, finish_position, places_gained, is_win, is_podium, points 
FROM dw.FactRaceResult WHERE source_result_id = 1;

-- ==============================================================================
-- NHÓM B: DÙNG CHO PHẦN 5 (KIỂM TRA ĐỐI SOÁT TỔNG THỂ & PHÂN TÍCH STAR SCHEMA)
-- ==============================================================================

-- 4. ĐỐI SOÁT SỐ DÒNG BẢO TOÀN GIỮA STG VÀ DW
SELECT 
    s.name + '.' + t.name AS [Bang], 
    SUM(p.rows) AS [So_Dong] 
FROM sys.tables t 
JOIN sys.schemas s ON s.schema_id = t.schema_id 
JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1) 
WHERE s.name IN ('stg','dw') 
GROUP BY s.name, t.name 
ORDER BY 1;

-- 5. KIỂM TRA CHỈ MỤC COLUMNSTORE TRÊN TẦNG DW
SELECT 
    OBJECT_SCHEMA_NAME(object_id) + '.' + OBJECT_NAME(object_id) AS [Bang], 
    name AS [Ten_Index],
    type_desc AS [Kieu_Index]
FROM sys.indexes 
WHERE type_desc LIKE '%COLUMNSTORE%';

-- 6. ĐỐI SOÁT CHI TIẾT 1 DÒNG CỦA LEWIS HAMILTON (Australian GP 2008)
SELECT 
    f.source_result_id,
    d.full_name AS [Tay_Dua],
    c.constructor_name AS [Doi_Dua],
    r.race_name AS [Chang_Dua],
    f.result_outcome_code AS [Trang_Thai_Chuan_Hoa],
    f.points AS [Diem],
    f.is_win AS [Thang],
    f.is_podium AS [Podium]
FROM dw.FactRaceResult f
JOIN dw.DimDriver d ON f.driver_sk = d.driver_sk
JOIN dw.DimConstructor c ON f.constructor_sk = c.constructor_sk
JOIN dw.DimRace r ON f.race_sk = r.race_sk
WHERE f.source_result_id = 1;

-- 7. TRUY VẤN NGHIỆP VỤ STAR SCHEMA: TOP 5 TAY ĐUA NHIỀU CHIẾN THẮNG NHẤT
SELECT TOP 5 
    d.full_name AS [Tay_Dua], 
    SUM(CAST(f.is_win AS int)) AS [So_Lan_Thang], 
    SUM(CAST(f.is_podium AS int)) AS [So_Lan_Podium], 
    SUM(f.points) AS [Tong_Diem] 
FROM dw.FactRaceResult f 
JOIN dw.DimDriver d ON d.driver_sk = f.driver_sk 
GROUP BY d.full_name 
ORDER BY [So_Lan_Thang] DESC;
```
