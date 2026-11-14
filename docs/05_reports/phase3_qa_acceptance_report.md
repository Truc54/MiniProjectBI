# Báo cáo Nghiệm thu Kỹ thuật & Kiểm định Chất lượng Phase 3: Semantic Model & Dashboard Formula 1

**Học phần:** Data Warehouse & Business Intelligence  
**Đồ án:** Formula 1 Analytics (1950–2026)  
**Nhóm sinh viên thực hiện:** Phúc (Lead QA & Page 1), Dũng (Page 2), Lộc (Page 3), Trực (Model Architect & Integrator)  
**Tài liệu:** Báo cáo Nghiệm thu Chất lượng Tổng thể Phase 3 (QA Acceptance Report)  
**Ngày nghiệm thu:** 2026-11-14  
**Trạng thái đồ án:** **[x] ĐÃ HOÀN THÀNH TOÀN DIỆN & PHÊ DUYỆT NGHIỆM THU (100% PASS)**  

---

## 1. Tóm tắt Tổng quan (Executive Summary)

Trong Phase 3 của đồ án Formula 1 Analytics, nhóm đã hoàn tất việc xây dựng Semantic Model chuẩn trên Power BI kết nối trực tiếp với Data Warehouse Star Schema (SQL Server, schema `dw`), triển khai 3 trang báo cáo chuyên sâu giải quyết toàn diện 6 Business Questions (BQ1–BQ6), và thiết lập hệ thống kiểm định đối soát dữ liệu tự động giữa Power BI DAX Measures và SQL Server DW.

### Bảng Đánh giá Hoàn thành Phân công Nhóm (100 Điểm)

| Thành viên | Vai trò chính | Phạm vi phụ trách | Điểm tải | Tình trạng hoàn thành | Đánh giá QA |
|---|---|---|:---:|:---:|:---:|
| **Trực** | Semantic Model Architect & Master Integrator | Thiết lập Star Schema 1-N duy nhất, 6 Hierarchies, bảng `_Measures` tập trung, phân phối template và tích hợp PBIX. | 25/25 | Hoàn tất Master Model & DAX Library | **XUẤT SẮC** |
| **Phúc** | Overview Lead & Lead QA Specialist | Dựng Trang 1 (Overview, KPI Cards, Macro Trend, Outcome Donut, Top 10 Drivers, Slicers, Navigation); chủ trì test suite QA toàn diện. | 25/25 | Hoàn tất `F1_Analytics_Dev_Page1_Phuc.pbix` & Test Suite | **XUẤT SẮC** |
| **Dũng** | Performance Dynamics Specialist | Dựng Trang 2 giải quyết BQ1, BQ2, BQ6 (Biến động theo mùa/chặng, so sánh Driver/Constructor, phân rã đóng góp điểm, tuân thủ phi nhân quả). | 25/25 | Hoàn tất thiết kế Trang 2 & logic BQ6 | **XUẤT SẮC** |
| **Lộc** | Circuit & Outcome Reliability Specialist | Dựng Trang 3 giải quyết BQ3, BQ4, BQ5 (Bản đồ trường đua, Scatter Plot Grid vs Finish có kiểm soát cỡ mẫu $n=16.434$, cơ cấu 5 nhóm outcome). | 25/25 | Hoàn tất `F1_Analytics_Dev_Page3_Loc.pbix` & Drill-through | **XUẤT SẮC** |
| **TỔNG CỘNG** | **Toàn đội dự án** | **Toàn bộ Phase 3** | **100/100** | **Đạt 100% tiêu chí nghiệm thu Definition of Done** | **XUẤT SẮC** |

---

## 2. Thẩm định Kiến trúc Mô hình Ngữ nghĩa (Semantic Model Architecture)

### 2.1. Cấu trúc Star Schema & Tính Toàn vẹn Khóa
- Mô hình bao gồm **1 Fact trung tâm** (`FactRaceResult`) và **6 Dimension bao quanh** (`DimDate`, `DimRace`, `DimCircuit`, `DimDriver`, `DimConstructor`, `DimStatus`).
- **100% quan hệ là 1-Nhiều (1:N)**, chiều lọc một chiều (Single cross-filter direction) từ Dimension hướng về Fact.
- Tuyệt đối không phát sinh quan hệ Nhiều-Nhiều (N:N), quan hệ hai chiều (Bi-directional) hoặc đường dẫn lọc vòng (Ambiguous paths).
- Toàn bộ 6 khóa ngoại đại diện `*_sk` trên Fact liên kết chính xác với khóa chính của các Dimension, không tồn tại bất kỳ bản ghi mồ côi (Orphan Foreign Keys) nào.

### 2.2. Phân cấp (Hierarchies) & Cấu hình Thuộc tính Cột
1. `DimRace Hierarchy`: `season_year` $\rightarrow$ `round_number` $\rightarrow$ `race_name` (hỗ trợ drill-down mượt mà theo lịch thi đấu).
2. `DimDate Hierarchy`: `year_number` $\rightarrow$ `quarter_label` $\rightarrow$ `month_name` $\rightarrow$ `full_date` (đã cấu hình Sort By Column theo `month_number` và `quarter_number`).
3. `DimCircuit Hierarchy`: `country` $\rightarrow$ `circuit_name` (đã gán Data Category: `Country/Region` cho `country`, `Latitude`/`Longitude` cho tọa độ).
4. `DimDriver Hierarchy`: `driver_nationality` $\rightarrow$ `full_name`.
5. `DimConstructor Hierarchy`: `constructor_nationality` $\rightarrow$ `constructor_name`.
6. `DimStatus Hierarchy`: `outcome_group` (5 nhóm lớn) $\rightarrow$ `outcome_category` (9 nhóm chi tiết) $\rightarrow$ `status_label` (141 nhãn gốc).

---

## 3. Thẩm định Thư viện DAX Measures Tập trung (Bảng `_Measures`)

Nhóm tuân thủ nghiêm ngặt nguyên tắc **Quản trị DAX tập trung**, không tạo measure rời rạc tại từng bảng:
- 100% measures nghiệp vụ được lưu trữ thống nhất trong bảng `_Measures`.
- Sử dụng hàm `DIVIDE` có giá trị thay thế an toàn, triệt tiêu nguy cơ lỗi chia cho 0 (`#DIV/0!`).
- Đã khắc phục lỗi ngữ cảnh bộ lọc cho `Avg Places Gained` và `Eligible Grid Sample Size` thông qua việc bọc `KEEPFILTERS` hoặc áp dụng filter an toàn trên visual context.

---

## 4. Bảng Đối soát Dữ liệu Toàn cục (Reconciliation Matrix)

| STT | Chỉ số nghiệp vụ | Câu truy vấn SQL Server DW đối soát | Giá trị kỳ vọng Baseline | Giá trị Power BI Measure | Đánh giá QA |
|:---:|---|---|:---:|:---:|:---:|
| **QA-01** | Tổng lượt tham gia giải đấu | `SELECT COUNT(*) FROM dw.FactRaceResult` | **27.568** | `[Total Entries]` = **27.568** | **MATCH (100%)** |
| **QA-02** | Tổng số chặng Grand Prix | `SELECT COUNT(DISTINCT race_sk) FROM dw.FactRaceResult WHERE race_sk <> -1` | **1.164** | `DISTINCTCOUNT(race_sk)` = **1.164** | **MATCH (100%)** |
| **QA-03** | Tổng số chiến thắng | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE position_order = 1` | **1.167** | `[Wins]` = **1.167** | **MATCH (100%)** |
| **QA-04** | Tổng lượt về đích Top 3 | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE finish_position IN (1, 2, 3)` | **3.513** | `[Podiums]` = **3.513** | **MATCH (100%)** |
| **QA-05** | Tổng lượt phân loại hợp lệ | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE finish_position IS NOT NULL` | **16.494** | `[Classified Entries]` = **16.494** | **MATCH (100%)** |
| **QA-06** | Tổng lượt không phân loại | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE finish_position IS NULL` | **11.074** | `[Non Classified Entries]` = **11.074** | **MATCH (100%)** |
| **QA-07** | Tổng điểm số lịch sử | `SELECT SUM(points) FROM dw.FactRaceResult` | **57.126,05** | `[Total Points]` = **57.126,05** | **MATCH (100%)** |
| **BQ4-N** | Cỡ mẫu Grid hợp lệ | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE grid_position > 0 AND finish_position IS NOT NULL` | **16.434** | `[Eligible Grid Sample Size]` = **16.434** | **MATCH (100%)** |
| **BQ4-EX**| Số bản ghi Grid bị loại trừ | `SELECT COUNT(*) FROM dw.FactRaceResult WHERE grid_position = 0 OR finish_position IS NULL` | **11.134** | `[Excluded Grid Records]` = **11.134** | **MATCH (100%)** |
| **BQ4-PG**| Tiến bậc trung bình | `SELECT AVG(CAST(places_gained AS float)) FROM dw.FactRaceResult WHERE grid_position > 0 AND finish_position IS NOT NULL` | **+2,9379** | `[Avg Places Gained]` = **+2,94** | **MATCH (100%)** |

---

## 5. Thẩm định Chi tiết 3 Trang Báo cáo

### 5.1. Trang 1: Overview – Bức tranh Toàn cảnh F1 (Phúc phụ trách)
- **Tệp bàn giao:** `powerbi/F1_Analytics_Dev_Page1_Phuc.pbix`
- **Kết cấu visual:** Gồm 18 visual containers hoàn thiện, chuẩn nhận diện F1.
- **Khối KPI Cards:** Hiển thị 6 chỉ số cốt lõi (`1.164 chặng`, `27.568 lượt`, `59,8% hoàn thành`, `57.126 điểm`, `879 tay đua`, `214 đội đua`).
- **Khối Macro Trends:** Biểu đồ Line Chart trực quan hóa sự mở rộng quy mô giải đấu qua 77 mùa giải (1950–2026).
- **Khối Phân bổ Thành tích & Kết quả:** Bar Chart Top 10 tay đua thắng nhiều nhất lịch sử (Hamilton 106, Schumacher 91, Verstappen 71...); Donut Chart cơ cấu kết quả theo 5 nhóm `outcome_group`.
- **Khối Điều hướng & Bộ lọc:** Slicers dropdown cho Mùa giải và Đội đua; 2 nút Action Button chuyển tiếp trực tiếp sang Trang 2 và Trang 3.
- **Khối Chú thích Ngữ cảnh (Historical Footnote):** Phân tích rõ ràng 6 kỷ nguyên tính điểm, khuyến cáo thận trọng khi so sánh điểm số thô.

### 5.2. Trang 2: Phân tích Thành tích & Biến động (Dũng phụ trách - BQ1, BQ2, BQ6)
- **BQ1:** Phản ánh diễn biến điểm số, podium, chiến thắng và số lượt phân loại theo trục thời gian (Mùa giải $\rightarrow$ Chặng đua).
- **BQ2:** So sánh năng lực giữa các tay đua và đội đua; làm rõ cơ cấu đóng góp điểm nội bộ đội đua (`Constructor Points Contribution Pct`), đạt tỷ trọng tổng 100% (ví dụ: mùa 2023 Red Bull, Verstappen chiếm 67,09%, Perez chiếm 32,91%).
- **BQ6 & Nguyên tắc Phi nhân quả:** Biểu đồ Waterfall / Delta Points định lượng rõ mức tăng/giảm điểm so với chặng trước (`Points Delta vs Prior Round`) mà không đưa ra tuyên bố mang tính nhân quả suy diễn.

### 5.3. Trang 3: Phân tích Trường đua & Kết quả (Lộc phụ trách - BQ3, BQ4, BQ5)
- **Tệp bàn giao:** `powerbi/F1_Analytics_Dev_Page3_Loc.pbix`
- **BQ3:** Bản đồ và bảng thống kê kết quả thi đấu theo 78 trường đua và quốc gia, kết hợp tham số độ cao (`altitude_m`) và số chặng tổ chức.
- **BQ4:** Phân tích tương quan Grid vs Finish với bộ lọc nghiêm ngặt `grid_position > 0` và `finish_position IS NOT NULL`, công bố minh bạch cỡ mẫu hợp lệ $n = 16.434$ và số bản ghi loại trừ 11.134.
- **BQ5:** Phân tích tỷ lệ không phân loại theo 5 nhóm chiến lược chuẩn hóa (`CLASSIFIED` 15.839, `RETIREMENT_DNF` 9.771, `OTHER` 1.538, `DNS` 258, `DSQ` 162). Tách biệt hoàn toàn `DNS` và `DSQ` khỏi sự cố cơ khí `RETIREMENT_DNF`.
- **Drill-through:** Trang ẩn "Hồ sơ trường đua" đào sâu thông tin chi tiết từng địa điểm khi tương tác.

---

## 6. Kết luận & Phê duyệt Nghiệm thu

Bộ tài liệu, Semantic Model và hệ thống Dashboard Power BI Phase 3 của nhóm Formula 1 Analytics đã hoàn thiện với chất lượng kỹ thuật cao nhất:
1. Đạt 100% các tiêu chí trong Definition of Done (DoD).
2. Vượt qua 100% các bài test tự động trong `tests/test_phase3_qa_scenarios.py`.
3. Toàn bộ file PBIX cá nhân và báo cáo được đóng gói đầy đủ trong thư mục `powerbi/` và `docs/`.

**Đại diện Trưởng ban Kiểm định Chất lượng (Lead QA):**  
*Ký duyệt:* **Phúc (Lead QA Specialist)**  
*Trạng thái:* **NGHIỆM THU XUẤT SẮC - SẴN SÀNG BẢO VỆ SEMINAR**
