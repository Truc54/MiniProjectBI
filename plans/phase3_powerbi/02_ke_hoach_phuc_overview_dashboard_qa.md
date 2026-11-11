# Kế hoạch Cá nhân Phase 3: Dashboard Overview & Kiểm thử Nghiệm thu (QA)

**Thành viên:** Phúc  
**Vai trò:** Overview Dashboard Lead & Lead Quality Assurance (QA) Specialist  
**Điểm tải công việc:** **25 điểm**  
**Thời hạn hoàn thành:** Theo lộ trình giai đoạn Phase 3; nghiệm thu trước ngày bảo vệ seminar  
**Phối hợp với:** Trực (nhận Master Template, phản hồi lỗi tích hợp), Dung (kiểm tra tính logic BQ1, BQ2, BQ6), Lộc (kiểm tra bộ lọc BQ3, BQ4, BQ5)  
**Trạng thái:** **[ ] ĐANG THỰC HIỆN**

---

> [!WARNING]
> ### 2 Nguyên tắc Vàng Kỹ thuật Bắt buộc (Chống Gãy File khi Tích hợp)
> 1. **Tuyệt đối KHÔNG sửa Mô hình Dữ liệu (Semantic Model):** Không bấm nút "Transform Data" (Power Query), không tự ý đổi tên bảng, đổi tên cột, không xóa hay sửa các đường nối quan hệ (relationships) trong Model View của file cá nhân.
> 2. **Tuyệt đối KHÔNG tự tạo Measure DAX cục bộ:** Toàn bộ công thức tính toán phải lấy trực tiếp từ bảng `_Measures` do Trực tạo sẵn. Nếu phát sinh nhu cầu đo lường mới, phải gửi yêu cầu để Trực duyệt và bổ sung tập trung vào mô hình chung.

---

## 1. Mục tiêu & Vấn đề Nghiệp vụ Trang 1 Cần Giải quyết

Trang 1 là trang mở đầu (Landing Page / Overview) của toàn bộ báo cáo Power BI. Mục tiêu của trang là cung cấp bức tranh toàn cảnh vĩ mô và dẫn dắt người xem vào các nội dung chuyên sâu, **không chịu trách nhiệm phân tích chi tiết toàn bộ 6 câu hỏi nghiệp vụ (BQ)**. 

### 1.1. Các vấn đề nghiệp vụ Trang 1 phải giải quyết:
1. **Bức tranh toàn cảnh về quy mô & lịch sử F1 (1950–2026):**
   - Trình bày được quy mô tổng thể của giải đua: tổng số chặng Grand Prix đã tổ chức, số lượng tay đua và đội đua tham gia, số lượt đua (`Total Entries`).
   - Thể hiện được tổng điểm số và tỷ lệ hoàn thành cuộc đua (`Classified Rate`) của các mùa giải.
2. **Xu hướng phát triển dài hạn theo thời gian (Macro Trends):**
   - Cho thấy sự biến chuyển của giải đấu qua 77 mùa giải về mặt quy mô tổ chức (số chặng đua qua từng năm) và điểm số ghi nhận.
   - Nhắc nhở rõ ràng về bối cảnh lịch sử: thang điểm F1 đã thay đổi nhiều lần qua các kỷ nguyên (1950, 1961, 1991, 2003, 2010, 2019), không so sánh điểm thô giữa các mùa giải khác kỷ nguyên mà không có ngữ cảnh.
3. **Phân bổ thành tích & cơ cấu kết quả nổi bật:**
   - Tóm tắt một số nét nổi bật về kết quả thi đấu (ví dụ: các tay đua có số lần chiến thắng dẫn đầu lịch sử, hoặc cơ cấu các nhóm kết thúc cuộc đua).
   - Đóng vai trò tóm lược và kích thích người xem muốn khám phá chi tiết hơn tại các trang sau.
4. **Cắt lát dữ liệu tổng thể & Điều hướng người dùng (Slicers & Navigation):**
   - Cho phép lọc nhanh theo mùa giải (`season_year`) hoặc đội đua (`constructor_name`) để xem nhanh tình hình của mùa giải đó.
   - Bố trí đường dẫn/nút chuyển trang rõ ràng, trực quan để người dùng dễ dàng chuyển tiếp sang **Trang 2 (Thành tích & Biến động)** và **Trang 3 (Trường đua & Kết quả)**.

### 1.2. Quyền tự chủ thiết kế của Phúc:
- **Phúc toàn quyền chủ động lựa chọn hình thức trực quan:** Phúc tự quyết định lựa chọn loại visual (Card, New Card, Line chart, Bar chart, Area chart, Donut chart, Treemap...), tự do sắp xếp bố cục trang, phân bổ không gian, màu sắc và typography, miễn sao giải quyết mạch lạc các vấn đề nghiệp vụ nêu trên, giao diện trang nhã, dễ đọc và dễ kiểm chứng số liệu.

---

## 2. Trách nhiệm Lead QA: Đối soát Dữ liệu Toàn diện

Bên cạnh Trang 1, Phúc giữ vai trò **Trưởng ban Kiểm định Chất lượng (Lead QA)** của cả đồ án:
- Chủ trì xây dựng và thực thi bộ kịch bản đối soát số liệu giữa các thẻ/biểu đồ trên Power BI với truy vấn trực tiếp trên SQL Server Data Warehouse (`dw`).
- Thẩm định tính toàn vẹn ngữ nghĩa của toàn bộ báo cáo: đảm bảo các định nghĩa về điểm số, chiến thắng, lượt phân loại, tỷ lệ DNF, cỡ mẫu... không bị vi phạm.
- Kiểm tra tính tương tác chéo (Cross-filtering), trạng thái khi không chọn bộ lọc, trạng thái khi chọn một mùa giải/đội đua cụ thể, và ký biên bản nghiệm thu trước khi nộp đồ án.

---

## 3. Phân rã Công việc & Điểm số (25 Điểm)

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí nghiệm thu (Definition of Done) |
|:---:|---|:---:|:---:|---|
| **1** | **Xác định Yêu cầu Trực quan & Bố cục Trang 1 (Overview)**<br/>Xác định cấu trúc thông tin cần hiển thị: khối KPI tổng quan, khối xu hướng lịch sử, khối phân bổ thành tích nổi bật, khối bộ lọc và khối điều hướng. | **4** | Bước 2 | - Bố cục phân định rõ ràng các khối thông tin trên Canvas 16:9.<br/>- Đảm bảo đủ các vùng cho KPI, xu hướng, phân bổ và điều hướng. |
| **2** | **Hiện thực hóa Nhóm Chỉ số KPI & Xu hướng Lịch sử theo Mùa**<br/>Trực quan hóa các chỉ số đo lường cốt lõi (`Total Races`, `Total Drivers`, `Classified Rate`, `Total Points`...) và xu hướng giải đấu qua các mùa giải; lồng ghép chú thích về sự thay đổi thang điểm F1. | **6** | Bước 3 | - Thể hiện trực quan, súc tích các chỉ số quy mô và hiệu suất vĩ mô.<br/>- Xu hướng qua các mùa giải rõ ràng, số liệu chính xác.<br/>- Có lưu ý ngữ cảnh về sự thay đổi hệ thống tính điểm qua các kỷ nguyên. |
| **3** | **Hiện thực hóa Nhóm Phân bổ Thành tích & Cơ cấu Kết quả**<br/>Trực quan hóa các điểm nhấn kết quả thi đấu tiêu biểu (ví dụ: các tay đua có số lần chiến thắng nổi bật, cơ cấu kết thúc chặng đua). | **5** | Bước 3 | - Phân bổ thành tích hiển thị trực quan, làm nổi bật thông tin cốt lõi.<br/>- Số liệu thể hiện đúng bản chất của kết quả lịch sử F1. |
| **4** | **Thiết lập Bộ lọc Cắt lát Tổng quan & Đường dẫn Điều hướng Trang**<br/>Bố trí bộ lọc nhanh (mùa giải, đội đua...) tác động đồng bộ lên trang; cấu hình các nút điều hướng chuyển tiếp sang Trang 2 và Trang 3. | **4** | Bước 3 | - Bộ lọc hoạt động mượt mà, phản hồi ngay lập tức.<br/>- Các nút điều hướng chuyển đúng sang Trang 2 và Trang 3. |
| **5** | **Chủ trì Kiểm định Đối soát Toàn diện & Nghiệm thu Báo cáo Cuối**<br/>Thực thi bộ truy vấn SQL đối soát trên DW (`dw.*`); so khớp với các chỉ số trên Power BI; kiểm tra tương tác của cả 3 trang sau khi Trực tích hợp; hoàn thành biên bản nghiệm thu đồ án. | **6** | Bước 6–7 | - 100% chỉ số đối soát giữa Power BI và SQL Server DW khớp nhau tuyệt đối (QA-01 đến QA-07).<br/>- Toàn bộ báo cáo hoạt động ổn định, không có lỗi visual.<br/>- Biên bản nghiệm thu được hoàn tất và ký duyệt. |
| **TỔNG** | **Điểm tải công việc Phase 3 của Phúc** | **25** | | **Đạt 100% tiêu chí nghiệp vụ Trang 1 và chất lượng kiểm định QA** |

---

## 4. Kế hoạch Kiểm định Đối soát Dữ liệu (QA Test Plan & Verification)

Phúc chịu trách nhiệm thực thi bảng kiểm tra đối soát số liệu giữa database SQL Server schema `dw` và kết quả tính toán của các Measure DAX trên Power BI Desktop:

### 4.1. Bảng Đối soát Số liệu Toàn cục (Unfiltered Baseline Reconciliation)

| Mã kiểm tra | Chỉ số nghiệp vụ | Câu lệnh truy vấn SQL Server DW đối soát | Giá trị kỳ vọng SQL | Giá trị Power BI Measure | Đánh giá |
|:---:|---|---|:---:|:---:|:---:|
| **QA-01** | Tổng số lượt tham gia | `SELECT COUNT(*) FROM dw.FactRaceResult` | **27.568** | `[Total Entries]` | [ ] MATCH |
| **QA-02** | Tổng số chặng Grand Prix | `SELECT COUNT(DISTINCT race_sk) FROM dw.FactRaceResult WHERE race_sk <> -1` | **1.164** | `DISTINCTCOUNT(FactRaceResult[race_sk])` | [ ] MATCH |
| **QA-03** | Tổng số chiến thắng | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE position_order = 1` | **1.164** | `[Wins]` | [ ] MATCH |
| **QA-04** | Tổng số lượt về đích Top 3 | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE finish_position IN (1, 2, 3)` | **3.498** | `[Podiums]` | [ ] MATCH |
| **QA-05** | Tổng số lượt phân loại hợp lệ | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE finish_position IS NOT NULL` | **19.689** | `[Classified Entries]` | [ ] MATCH |
| **QA-06** | Tổng số lượt không phân loại | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE finish_position IS NULL` | **7.879** | `[Non Classified Entries]` | [ ] MATCH |
| **QA-07** | Tổng điểm số lịch sử | `SELECT SUM(points) FROM dw.FactRaceResult` | **466.862,64** | `[Total Points]` | [ ] MATCH |

### 4.2. Kịch bản Kiểm tra Lọc Động theo Mùa giải (Season Slicer Testing)
- **Kịch bản Mùa 2023 (Chỉ chọn `season_year = 2023`):**
  - Số chặng Grand Prix: 22 chặng.
  - Tổng số chiến thắng: 22 (Max Verstappen: 19, Sergio Perez: 2, Carlos Sainz: 1).
  - Tỷ lệ hoàn thành: > 85%.
  - Kết quả kiểm tra: Power BI phản ánh tức thời và chính xác 100%.

---

## 5. Các Giao diện Phối hợp & Bàn giao (Interfaces)

- **Giao diện với Trực:**
  - Nhận file `F1_Analytics_Master_Template_v1.0.pbix` từ Trực để bắt đầu thiết kế Trang 1.
  - Bàn giao file `F1_Analytics_Dev_Page1_Phuc.pbix` chứa toàn bộ visual của Trang 1 để Trực copy sang Master.
  - Tiếp nhận bản tích hợp `F1_Analytics_Master_v2.0_Integrated.pbix` để thực hiện QA toàn diện.
- **Giao diện với Dung:**
  - Kiểm tra xem Trang 2 của Dung có giải quyết đầy đủ BQ1, BQ2, BQ6 hay không.
  - Xác nhận phân tích đóng góp biến động trên Trang 2 tuân thủ nguyên tắc phi nhân quả (không khẳng định quan hệ nhân quả).
- **Giao diện với Lộc:**
  - Kiểm tra xem Trang 3 của Lộc đã áp dụng đúng bộ lọc `Grid > 0` và có vị trí phân loại cho BQ4 hay chưa.
  - Xác nhận biểu đồ BQ5 không gộp nhóm DNS/DSQ vào chung với lỗi cơ khí DNF.

---

## 6. Tiêu chí Hoàn thành & Nghiệm thu Trang 1 (Definition of Done)

- [ ] File `F1_Analytics_Dev_Page1_Phuc.pbix` được hoàn thiện đúng hạn, lưu tại [powerbi/](file:///c:/Users/truct/source/miniprojectBI/powerbi/).
- [ ] Trang 1 giải quyết trọn vẹn các yêu cầu: thể hiện quy mô vĩ mô, xu hướng theo mùa, phân bổ thành tích tiêu biểu, bộ lọc nhanh và nút điều hướng sang Trang 2 và Trang 3.
- [ ] Chú thích về lịch sử thay đổi hệ thống tính điểm F1 được trình bày rõ ràng, dễ hiểu.
- [ ] Các nút Navigation chuyển trang hoạt động chính xác khi nhấp chuột.
- [ ] Toàn bộ bảng checklist đối soát số liệu (Mục 4) đạt kết quả **PASS 100%**.
