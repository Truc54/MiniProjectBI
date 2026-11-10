# Kịch Bản Thuyết Trình Kèm Video Demo (Presentation & Voiceover Script)

**Dự án:** Formula 1 Analytics (1950–2026) · MiniProject BI  
**Mục đích:** Dành cho người thuyết trình nói trực tiếp trong buổi báo cáo seminar hoặc lồng tiếng video.  
**Cơ chế sử dụng:** Bạn có thể cho video chạy bình thường, và **bấm TẠM DỪNG (PAUSE)** tại các điểm đánh dấu `[PAUSE POINT]` để giải thích sâu cho Thầy Cô và Hội đồng mà không bị trôi video.  
**Thời lượng dự kiến:** 10 – 15 phút.

---

## PHẦN 1: MỞ ĐẦU, BÀI TOÁN & Ý NGHĨA DATASET (~2 phút)

*(Bật video: Màn hình VS Code lướt qua cấu trúc thư mục và file dataset thô)*

### Lời thoại:
> "Kính chào Thầy Cô và các bạn. Hôm nay em xin đại diện nhóm trình bày về đồ án Xây dựng Kho Dữ Liệu và Phân tích giải đua xe Công thức 1 (Formula 1 Analytics) giai đoạn lịch sử từ năm 1950 đến 2026.
>
> **1. Về bộ dữ liệu lựa chọn:**
> Bộ dữ liệu F1 từ Kaggle gồm 17 file CSV với hơn 750.000 dòng. Tuy nhiên, nhóm đã khảo sát và chọn lọc ra **7 file lõi** (tổng cộng 30.121 dòng) đại diện cho đúng một quy trình nghiệp vụ trọng tâm: **Kết quả thi đấu chính thức của một tay đua trong một chặng Grand Prix**:
> * `results.csv` (27.568 dòng): Bảng sự kiện trung tâm ghi nhận kết quả từng tay đua (điểm số, vị trí xuất phát `grid`, thứ tự về đích `position`).
> * `races.csv` (1.164 dòng): Danh mục các chặng đua qua 77 mùa giải (năm đua, vòng đua, ngày giờ đua).
> * `drivers.csv` (879 dòng): Danh mục hồ sơ tay đua (họ tên, mã code, số xe, quốc tịch, ngày sinh).
> * `constructors.csv` (214 dòng): Danh mục các đội đua / nhà sản xuất xe (Ferrari, McLaren, Mercedes...).
> * `circuits.csv` (78 dòng): Danh mục trường đua và tọa độ địa lý (tên trường đua, thành phố, quốc gia, độ cao).
> * `status.csv` (141 dòng): Danh mục trạng thái kết thúc cuộc đua (`Finished`, hỏng động cơ, va chạm, bị loại...).
> * `seasons.csv` (77 dòng): Danh mục các mùa giải từ 1950 đến 2026 để kiểm tra độ bao phủ thời gian.
>
> *(10 file còn lại như `lap_times`, `pit_stops`, `qualifying` có hạt dữ liệu khác—từng vòng, từng giây—hoặc chỉ có dữ liệu cho 2 mùa gần đây nên được tách ra để tránh làm loãng mô hình).*
>
> Bộ dữ liệu này có tính thử thách kỹ thuật và giá trị phân tích cao vì 3 đặc điểm:
> * **Thứ nhất, tính chất lịch sử trải dài hơn 70 năm:** F1 liên tục thay đổi quy định qua các thời kỳ, đặc biệt là thang điểm thi đấu (ví dụ: trước 2010 nhất chặng chỉ được 10 điểm, sau 2010 là 25 điểm). Dữ liệu này đòi hỏi hệ thống BI phải bảo toàn đúng sự thật lịch sử.
> * **Thứ hai, quan hệ thực thể phong phú:** Một chặng đua (`race`) diễn ra tại một đường đua (`circuit`), với sự tranh tài của các tay đua (`driver`) thuộc các đội đua/nhà sản xuất (`constructor`).
> * **Thứ ba, sự đa dạng của trạng thái kết thúc:** Có tới 141 mã trạng thái về đích khác nhau, chứa cả lỗi động cơ, tai nạn, truất quyền thi đấu, đặt ra bài toán chuẩn hóa dữ liệu rất thực tế.
>
> **2. Kiến trúc giải pháp tổng thể:**
> Quy trình ELT của nhóm gồm 3 tầng rõ ràng:
> * **Tầng Staging (`stg`):** Dùng **Mage AI** để ingest dữ liệu từ CSV vào SQL Server, kiểm tra schema và loại bỏ giá trị rác.
> * **Tầng Transformation & Modeling:** Dùng **dbt Core** để đọc từ Staging, làm sạch qua view và dựng mô hình hình sao (Kimball Star Schema) tại schema `dw`.
> * **Tầng Storage:** Đặt trên **SQL Server**, được tối ưu hóa toàn diện bằng chỉ mục **Clustered Columnstore Index**."

---

## PHẦN 2: ĐIỀU PHỐI & NẠP DỮ LIỆU BẰNG MAGE AI (~2 phút)

*(Video chuyển sang màn hình Mage AI: Tab DAG Pipeline `f1_source_to_stage`)*

### Lời thoại:
> "Mời Thầy Cô quan sát trên màn hình, đây là giao diện điều phối của công cụ **Mage AI**. 
> Toàn bộ pipeline `f1_source_to_stage` được thiết kế theo chuẩn đồ thị có hướng (DAG) gồm 5 block khép kín:
> 1. `load_f1_csv`: Đọc dữ liệu từ 7 file CSV nguồn từ Kaggle.
> 2. `validate_f1_table`: Kiểm tra cấu trúc bảng, ép kiểu dữ liệu chuẩn, và xử lý các ký tự rỗng hoặc `\N` thành `NULL`.
> 3. `load_sqlserver`: Nạp dữ liệu vào các bảng trong schema `stg`. Mage hỗ trợ cả nạp toàn phần (Full load) và nạp tăng dần (Incremental load) dựa trên khóa lô (`batch_key`).
> 4. `dbt_transformation`: Tự động gọi container dbt để kích hoạt luồng biến đổi dữ liệu sang kho `dw`.
> 5. `commit_watermark`: Bước chốt chặn an toàn giao dịch."

---

> ⏸️ **[PAUSE POINT 1: TẠM DỪNG VIDEO TẠI MAGE AI ĐỂ NÓI SÂU]**  
> *(Dừng video ở block `commit_watermark` và giải thích thêm nếu muốn ghi điểm chuyên môn)*
> 
> *"Thưa Thầy Cô, điểm đặc biệt trong thiết kế của nhóm là **tính an toàn giao dịch (Atomic Transaction)**: Block `commit_watermark` nằm ở cuối cùng. Nếu tầng dbt gặp lỗi dữ liệu bẩn thì pipeline dừng ngay lập tức và mốc thời gian không được ghi nhận. Nhờ đó, ở lần chạy sau hệ thống sẽ tự động quét lại dữ liệu bị lỗi mà không bị sót bản ghi."*

*(Bấm tiếp tục phát video)*

---

## PHẦN 3: ĐỐI SOÁT TRỰC QUAN 2 TẦNG BIẾN ĐỔI DBT (STAGING $\rightarrow$ VIEW SẠCH $\rightarrow$ DW) (~3 phút)

*(Video chuyển sang màn hình SSMS hoặc Slide so sánh Trước - Sau)*

### Lời thoại:
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

> ⏸️ **[PAUSE POINT 2: GIẢI THÍCH INCREMENTAL CỦA FACT NẾU CÔ HỎI]**  
> *(Dừng video ở bảng so sánh Fact)*  
> *"Thưa Cô, bảng Fact được nạp theo cơ chế tăng dần `incremental` với chiến lược `delete+insert`. Điều kiện so sánh `_ingested_at_utc > max(_ingested_at_utc)` giúp hệ thống chỉ bốc đúng các bản ghi chặng đua mới nạp hôm nay để đưa vào Fact, bỏ qua 70 năm lịch sử cũ, tối ưu thời gian chạy từ vài phút xuống còn vài giây."*

---

## PHẦN 4: LINEAGE GRAPH & THỰC THI DBT BUILD (~2 phút)

*(Video chuyển sang dbt docs trên trình duyệt rồi sang Terminal)*

### Lời thoại:
> "Trên màn hình là **Sơ đồ Lineage (Cây phả hệ dữ liệu)** do dbt docs tự động sinh ra. 
> Chỉ cần gõ lệnh:
> `dbt build --select +fact_race_result`
> Nhờ các hàm `{{ ref() }}`, dbt tự động phân tích đồ thị DAG, nhận biết các quan hệ phụ thuộc để chạy đúng thứ tự: các view Staging trước $\rightarrow$ 6 bảng Dimension $\rightarrow$ cuối cùng là bảng Fact. Dấu `+` phía trước tên model nghĩa là hãy build model đó cùng toàn bộ các model tổ tiên của nó.
>
> *(Video quay màn hình Terminal chạy lệnh)*
> Lệnh `dbt build` thực hiện đồng thời việc tạo bảng và chạy 48 bài kiểm tra chất lượng dữ liệu.
> Kết quả: **PASS 61/61 bước** (13 models và 48 data tests), hoàn toàn không có cảnh báo hay lỗi."

---

## PHẦN 5: KIỂM TRA ĐỐI SOÁT TRỰC QUAN TRÊN SSMS (~3 phút)

*(Video chuyển sang màn hình SQL Server Management Studio - SSMS)*

### Lời thoại:
> "Bây giờ, chúng em vào thẳng SQL Server để đối soát thực tế:
>
> **1. Đối soát số dòng:**
> * Bảng nguồn `stg.results` có **27.568 dòng**.
> * Bảng đích `dw.FactRaceResult` đạt chính xác **27.568 dòng**. Dữ liệu được bảo toàn trọn vẹn 100%.
> * Các bảng Dim đều có thêm đúng 1 dòng ngoại lệ `-1`. Riêng `DimDate` có 28.125 dòng (từ năm 1950 đến 2026) phục vụ Time Intelligence.
>
> **2. Kiểm tra chỉ mục Columnstore:**
> Toàn bộ 7 bảng trong schema `dw` đều được đánh chỉ mục **Clustered Columnstore Index (CCI)**. Đây là công nghệ lưu trữ theo cột của SQL Server, giúp nén dung lượng và tăng tốc các câu lệnh tổng hợp `SUM`, `COUNT` lên gấp 5 đến 10 lần.
>
> **3. Đối soát 1 dòng chi tiết của Lewis Hamilton (Chặng Úc 2008):**
> Kết quả cho thấy: Mã trạng thái `Finished` đã chuyển thành `CLASSIFIED`, các khóa ngoại `driver_sk`, `race_sk` đều trỏ chính xác, và các cờ `is_win = 1`, `is_podium = 1` được tính đúng tuyệt đối.
>
> **4. Truy vấn nghiệp vụ Star Schema:**
> Nhóm chạy thử câu query tìm **Top 5 tay đua nhiều chiến thắng nhất lịch sử**:
> Câu lệnh JOIN giữa Fact và Dim phản hồi tức thì: Đứng đầu là Lewis Hamilton (106 chiến thắng), Michael Schumacher (91) và Max Verstappen (71)."

---

> ⏸️ **[PAUSE POINT 3: TẠM DỪNG VIDEO TẠI KẾT QUẢ TOP 5 TAY ĐUA ĐỂ CHIA SẺ INSIGHT]**  
> *(Dừng video ở bảng kết quả Top 5 tay đua)*
> 
> *"Thưa Thầy Cô, ở đây có một điểm thú vị về nghiệp vụ: Michael Schumacher có 91 chiến thắng nhưng chỉ đạt 1.566 điểm, trong khi Hamilton có hơn 5.100 điểm. Lý do là vì quy định tính điểm F1 đã thay đổi sau năm 2010. Nhóm quyết định giữ nguyên điểm gốc lịch sử ở tầng DW để phục vụ đối soát, và sự chênh lệch này sẽ được chuẩn hóa linh hoạt bằng các thước đo DAX trên Power BI ở Phase 3."*

*(Bấm tiếp tục phát video)*

---

## PHẦN 6: KIỂM THỬ BẮT LỖI & NẠP TĂNG DẦN (DATA QUALITY) (~2 phút)

*(Video quay cảnh cố tình sửa điểm âm và build lại dbt)*

### Lời thoại:
> "Một hệ thống BI chuẩn doanh nghiệp phải chứng minh được khả năng **chặn đứng dữ liệu bẩn**.
>
> Để kiểm thử:
> 1. Nhóm giả lập tình huống dữ liệu nguồn bị lỗi: sửa điểm số của một tay đua thành số âm (`points = -5`) trong bảng Staging.
> 2. Khi chạy `dbt build`, bài test nghiệp vụ `assert_points_non_negative` **lập tức báo lỗi FAIL (Error = 1)** và chặn đứng quy trình, không cho phép dữ liệu bẩn lọt vào kho báo cáo.
> 3. Sau khi sửa lại điểm số hợp lệ và build lại: toàn bộ 61 bước lại chuyển sang màu xanh **PASS**.
>
> Nhờ chiến lược `delete+insert`, bản ghi cũ bị sửa đổi được ghi đè chính xác mà không làm nhân đôi dòng, tổng số dòng của bảng Fact vẫn giữ nguyên chuẩn xác là **27.568 dòng**."

---

## PHẦN 7: TỔNG KẾT & ĐỊNH HƯỚNG PHASE 3 (~1 phút)

*(Video chuyển về slide kết luận)*

### Lời thoại:
> "Tổng kết lại, nhóm đã hoàn thành toàn diện các mục tiêu kỹ thuật:
> 1. Xây dựng quy trình ELT tự động, đồng bộ từ CSV qua Mage AI đến SQL Server.
> 2. Thiết kế mô hình Star Schema chuẩn Kimball với 1 Fact và 6 Dimensions.
> 3. Đạt tỷ lệ **100% PASS** trên cả 61 bước build test dbt và 40 điểm thẩm định ngữ nghĩa nghiệp vụ.
> 4. Tối ưu hóa hiệu năng lưu trữ và truy vấn bằng Clustered Columnstore Index.
>
> Đây là nền tảng dữ liệu sạch và chuẩn mực nhất để nhóm tự tin bước vào Phase 3: Xây dựng Semantic Model, các thước đo DAX nâng cao và thiết kế Dashboard trực quan trên Power BI.
>
> Nhóm em xin chân thành cảm ơn Thầy Cô và các bạn đã chú ý lắng nghe!"

---

---

# PHỤ LỤC: BỘ CÂU HỎI & CÂU TRẢ LỜI BẢO VỆ TRƯỚC HỘI ĐỒNG (Q&A)

Dưới đây là các câu hỏi Thầy Cô rất hay hỏi và câu trả lời chuẩn xác nhất để bạn tự tin phản hồi:

### Q1: Tại sao nhóm không dùng SCD Type 2 cho các bảng Dimension?
* **Trả lời:**  
  * Thứ nhất, thuộc tính của các thực thể F1 mang tính chất cố định (ngày sinh, quốc tịch của tay đua, tọa độ đường đua là bất biến).
  * Thứ hai, **lịch sử thi đấu đã được lưu trọn vẹn ở bảng Fact**: Bảng `FactRaceResult` đã chứa riêng cả `driver_sk` LẪN `constructor_sk`. Ví dụ: Năm 2008 Hamilton đua cho McLaren thì dòng Fact năm 2008 trỏ vào McLaren; năm 2014 đua cho Mercedes thì dòng Fact trỏ vào Mercedes. Lịch sử không hề bị mất mát dù bảng `DimDriver` chỉ dùng Type 1.

### Q2: Tại sao Surrogate Key (SK) lại bằng luôn Source ID (`race_sk = race_id`)?
* **Trả lời:**  
  * Đây là kỹ thuật **Deterministic Surrogate Key**. Dữ liệu F1 nguồn đã có sẵn ID là số nguyên duy nhất. 
  * Trong dbt, nếu dùng số tự tăng ngẫu nhiên (`IDENTITY` hay `ROW_NUMBER`), mỗi lần build lại bảng có thể sinh ra ID khác nhau làm gãy quan hệ dữ liệu. Dùng Deterministic SK vừa giữ tính tất định, vừa tối ưu hiệu năng JOIN kiểu số nguyên, lại rất dễ đối soát ngược về nguồn.

### Q3: Tại sao không dùng `incremental` cho các bảng Dimension?
* **Trả lời:**  
  * Toàn bộ lịch sử F1 chỉ có khoảng 1.100 chặng đua, 880 tay đua, 80 đường đua. Kích thước dữ liệu quá nhỏ (dưới vài nghìn dòng), nên việc chạy full-refresh (`materialized='table'`) chỉ mất 0.1 giây. 
  * Dùng `table` giúp code đơn giản, dữ liệu luôn đồng bộ sạch sẽ mà không phải duy trì các logic so sánh cập nhật phức tạp như ở bảng Fact.

### Q4: Bảng `DimDate` tại sao có tới 28.125 dòng trong khi các chặng đua chỉ diễn ra vào cuối tuần?
* **Trả lời:**  
  * Đây là chuẩn thiết kế DimDate của Kimball. Bảng ngày cần chứa **đầy đủ mọi ngày liên tục từ 1950 đến 2026** (kể cả ngày không có đua). Điều này bắt buộc phải có để các hàm tính toán theo thời gian (Time Intelligence: MTD, YTD, YoY) trên Power BI hoạt động chính xác.

