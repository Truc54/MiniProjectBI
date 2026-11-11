# Kế hoạch Cá nhân Phase 3: Dashboard Trường đua & Kết quả (Trang 3)

**Thành viên:** Lộc  
**Vai trò:** Circuit Performance & Outcome Reliability Specialist (Phụ trách Trang 3: BQ3, BQ4, BQ5)  
**Điểm tải công việc:** **25 điểm**  
**Thời hạn hoàn thành:** Theo lộ trình giai đoạn Phase 3; nghiệm thu trước ngày bảo vệ seminar  
**Phối hợp với:** Trực (nhận Master Template, xác nhận điều kiện lọc DAX BQ4/BQ5), Phúc (tiếp nhận kịch bản QA đối soát BQ3, BQ4, BQ5), Dũng (thống nhất phân định ranh giới báo cáo)  
**Trạng thái:** **[ ] ĐANG THỰC HIỆN**

---

> [!WARNING]
> ### 2 Nguyên tắc Vàng Kỹ thuật Bắt buộc (Chống Gãy File khi Tích hợp)
> 1. **Tuyệt đối KHÔNG sửa Mô hình Dữ liệu (Semantic Model):** Không bấm nút "Transform Data" (Power Query), không tự ý đổi tên bảng, đổi tên cột, không xóa hay sửa các đường nối quan hệ (relationships) trong Model View của file cá nhân.
> 2. **Tuyệt đối KHÔNG tự tạo Measure DAX cục bộ:** Toàn bộ công thức tính toán phải lấy trực tiếp từ bảng `_Measures` do Trực tạo sẵn. Nếu phát sinh nhu cầu đo lường mới cho BQ4 hoặc BQ5, phải gửi phiếu yêu cầu để Trực duyệt và bổ sung tập trung vào mô hình chung.

---

## 1. Mục tiêu & Vấn đề Nghiệp vụ Trang 3 Cần Giải quyết

Trang 3 là trang phân tích chuyên sâu về địa lý trường đua, hiệu quả chuyển đổi từ vị trí xuất phát thành kết quả thi đấu thực tế, và phân tích các trường hợp rủi ro/bỏ cuộc. Lộc chịu trách nhiệm chính giải quyết trọn vẹn **3 câu hỏi nghiệp vụ: BQ3, BQ4 và BQ5**.

### 1.1. Các vấn đề nghiệp vụ Trang 3 phải giải quyết:

1. **Giải quyết BQ3: Kết quả thi đấu khác nhau thế nào giữa các trường đua và quốc gia?**
   - Đánh giá sự khác biệt về kết quả thi đấu, số chặng tổ chức, quy mô lượt đua, tỷ lệ hoàn thành cuộc đua giữa các trường đua (`circuit_name`) và các quốc gia (`country`).
   - Thể hiện được các yếu tố đặc thù của trường đua: phân bố địa lý toàn cầu, độ cao so với mực nước biển (`altitude_m`), và sự khác biệt về mức độ rủi ro giữa các đường đua.

2. **Giải quyết BQ4: Vị trí xuất phát liên hệ thế nào với vị trí về đích và điểm theo mùa, chặng và trường đua?**
   - Đánh giá mối quan hệ và khả năng chuyển đổi từ vị trí xuất phát vòng phân hạng (Grid) sang thứ hạng về đích chính thức (Finish) và điểm số ghi được.
   - Thể hiện được các xu hướng: tay đua tiến bậc (gained places), giữ nguyên thứ hạng (held position), hay bị tụt hạng (lost places).
   - **RÀNG BUỘC NGHIỆP VỤ BẮT BUỘC (Strict Business Filter):** 
     - **Chỉ tính toán và phân tích trên các lượt đua có `Grid > 0` và có vị trí phân loại hợp lệ (`finish_position IS NOT NULL`)**.
     - Bắt buộc phải loại trừ các trường hợp `Grid = 0` (xuất phát từ Pit Lane hoặc không có vị trí phân hạng hợp lệ) và các xe bỏ cuộc giữa chừng để không làm sai lệch tương quan.
     - **Yêu cầu hiển thị cỡ mẫu:** Phải công bố rõ ràng cỡ mẫu hợp lệ `n` (`Eligible Grid Sample Size`) và số bản ghi bị loại trừ để người xem nắm rõ độ tin cậy của phân tích.

3. **Giải quyết BQ5: Số lượng và tỷ lệ kết quả không được phân loại thay đổi thế nào theo mùa, chặng, trường đua, tay đua và đội đua? Những status nào thường gặp?**
   - Phân tích số lượng và tỷ lệ kết quả không được phân loại (`Non Classified Rate`) theo thời gian (mùa giải, chặng), trường đua, tay đua và đội đua.
   - Làm rõ những nguyên nhân bỏ cuộc phổ biến nhất thông qua mã trạng thái nguồn (`status_label`).
   - **RÀNG BUỘC TOÀN VẸN NGỮ NGHĨA (Domain Taxonomy Integrity):**
     - Bắt buộc phải phân tích theo 5 nhóm chiến lược chuẩn hóa `outcome_group`: `CLASSIFIED`, `RETIREMENT_DNF`, `DNS`, `DSQ`, `OTHER`.
     - **TUYỆT ĐỐI KHÔNG gộp chung `DNS` (Không xuất phát) và `DSQ` (Bị truất quyền thi đấu do phạm quy chế) vào chung với `RETIREMENT_DNF` (Bỏ cuộc do tai nạn hoặc hư hỏng cơ khí)** nhằm bảo đảm không bóp méo thống kê về độ tin cậy cơ học của xe thi đấu.

4. **Yêu cầu Drill-through (Đào sâu dữ liệu trường đua):**
   - Cung cấp tính năng Drill-through để khi người dùng tương tác với một trường đua cụ thể có thể xem chi tiết hồ sơ thành tích (lịch sử tổ chức, các kỷ lục, tay đua thắng nhiều nhất tại trường đua đó).

### 1.2. Quyền tự chủ thiết kế của Lộc:
- **Lộc toàn quyền chủ động lựa chọn hình thức trực quan:** Lộc tự quyết định lựa chọn loại visual (Map/Bản đồ địa lý, Scatter plot/Biểu đồ phân tán, Stacked Bar/Column chart, Matrix table, Heatmap, Card cỡ mẫu...), tự do bố trí bố cục trang, phối màu, cấu hình tương tác và tooltips, miễn sao giải quyết triệt để và thuyết phục 3 câu hỏi BQ3, BQ4, BQ5, bảo đảm tuân thủ nghiêm ngặt các ràng buộc lọc dữ liệu và ngữ nghĩa F1.

---

## 2. Phân rã Công việc & Điểm số (25 Điểm)

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí nghiệm thu (Definition of Done) |
|:---:|---|:---:|:---:|---|
| **1** | **Hiện thực hóa Phân tích BQ3 (Khác biệt theo Trường đua & Quốc gia)**<br/>Trực quan hóa sự phân bố địa lý của các trường đua trên thế giới; làm rõ sự khác biệt về số chặng tổ chức, độ cao và mức độ rủi ro giữa các trường đua/quốc gia. | **5** | Bước 3 | - Thể hiện trực quan vị trí địa lý của các trường đua.<br/>- Cho phép so sánh kết quả và đặc thù giữa các trường đua/quốc gia.<br/>- Thể hiện được thông số độ cao và tỷ lệ sự cố. |
| **2** | **Hiện thực hóa Phân tích BQ4 (Tương quan Xuất phát Grid vs Về đích Finish)**<br/>Trực quan hóa mối liên hệ giữa Grid và Finish Position & Điểm số; áp dụng đúng bộ lọc bắt buộc `Grid > 0` và có vị trí phân loại hợp lệ; hiển thị rõ cỡ mẫu hợp lệ `n`. | **6** | Bước 3 | - Thể hiện rõ mối tương quan giữa vị trí xuất phát và kết quả về đích.<br/>- Loại bỏ 100% các dòng `Grid = 0` hoặc vị trí rỗng.<br/>- Thể hiện rõ cỡ mẫu `n` hợp lệ và nhận diện các trường hợp tiến/lùi bậc. |
| **3** | **Hiện thực hóa Phân tích BQ5 (Cơ cấu & Tỷ lệ Không phân loại DNF/DNS/DSQ)**<br/>Trực quan hóa số lượng và tỷ lệ không phân loại theo 5 nhóm chiến lược `outcome_group`; đi sâu vào các nguyên nhân bỏ cuộc cụ thể (`status_label`); tách biệt rõ ràng DNS/DSQ khỏi DNF. | **6** | Bước 3 | - Thể hiện tỷ lệ không phân loại theo thời gian, trường đua, tay đua/đội đua.<br/>- Tách biệt rõ 5 nhóm outcome: không đánh đồng DNS/DSQ với lỗi cơ khí.<br/>- Thể hiện được các nguyên nhân kỹ thuật thường gặp nhất. |
| **4** | **Cấu hình Bộ lọc Trang, Ràng buộc Lọc & Tính năng Drill-through**<br/>Thiết lập các bộ lọc phù hợp (quốc gia, trường đua, mùa giải, nhóm trạng thái...); cấu hình trang đích Drill-through xem chi tiết hồ sơ trường đua. | **4** | Bước 3 | - Bộ lọc hoạt động chính xác, không xung đột.<br/>- Tính năng Drill-through trường đua hoạt động mượt mà khi click chuột phải. |
| **5** | **Kiểm thử Nghiệp vụ, Đối soát Cỡ mẫu & Bàn giao Visuals cho Trực**<br/>Kiểm tra đối chiếu số lượng bản ghi thỏa mãn điều kiện lọc của BQ4 và BQ5 với các truy vấn SQL của Phúc; bàn giao file `F1_Analytics_Dev_Page3_Loc.pbix` cho Trực tích hợp. | **4** | Bước 4–5 | - Cỡ mẫu BQ4 và tỷ lệ BQ5 khớp hoàn toàn với số liệu DW.<br/>- Visual tích hợp sang file Master PBIX nguyên vẹn, không lỗi context. |
| **TỔNG** | **Điểm tải công việc Phase 3 của Lộc** | **25** | | **Đạt 100% tiêu chí giải quyết triệt để BQ3, BQ4, BQ5** |

---

## 3. Ràng buộc Nghiệp vụ & Thước đo DAX cho BQ4 và BQ5

Để đảm bảo tính nghiêm ngặt về mặt dữ liệu, Lộc áp dụng đúng các thước đo chuẩn được quản lý trong Semantic Model:

```dax
// Cỡ mẫu hợp lệ cho phân tích BQ4 (Grid > 0 và có vị trí phân loại)
Eligible Grid Sample Size = 
CALCULATE(
    COUNTROWS('dw FactRaceResult'),
    'dw FactRaceResult'[grid_position] > 0,
    NOT(ISBLANK('dw FactRaceResult'[finish_position]))
)

// Trung bình số bậc tăng/giảm vị trí (chỉ tính trên mẫu hợp lệ)
Avg Places Gained = 
CALCULATE(
    AVERAGE('dw FactRaceResult'[places_gained]),
    'dw FactRaceResult'[grid_position] > 0,
    NOT(ISBLANK('dw FactRaceResult'[finish_position]))
)

// Tỷ lệ không phân loại (Non-classified rate)
Non Classified Rate = 
DIVIDE([Non Classified Entries], [Total Entries], 0)
```

*(Lưu ý: Nếu Lộc cần thêm thước đo chuyên biệt cho tỷ lệ hỏng hóc cơ khí hoặc tỷ lệ tai nạn theo trường đua, Lộc gửi phiếu yêu cầu cho Trực cập nhật vào mô hình chung).*

---

## 4. Các Giao diện Phối hợp & Bàn giao (Interfaces)

- **Giao diện với Trực:**
  - Nhận file `F1_Analytics_Master_Template_v1.0.pbix` từ Trực để bắt đầu thiết kế Trang 3.
  - Phối hợp với Trực kiểm tra xem Data Category của các trường địa lý (`country`, `latitude`, `longitude`) trên `DimCircuit` đã chuẩn xác hay chưa.
  - Bàn giao file `F1_Analytics_Dev_Page3_Loc.pbix` chứa các visual hoàn thiện để Trực tích hợp vào Master.
- **Giao diện với Phúc:**
  - Cung cấp số liệu thống kê về cỡ mẫu hợp lệ của BQ4 và tỷ lệ không phân loại của BQ5 để Phúc đưa vào kịch bản kiểm thử đối soát QA.
  - Phối hợp với Phúc kiểm tra tính nhất quán giữa tỷ lệ hoàn thành ở Trang 1 và tỷ lệ không phân loại ở Trang 3.
- **Giao diện với Dũng:**
  - Thống nhất phân định ranh giới phân tích: Trang 3 tập trung sâu vào **Trường đua**, **Quốc gia** và **Độ tin cậy kỹ thuật (Outcome)**; Trang 2 của Dũng tập trung sâu vào **Tay đua** và **Đội đua**.

---

## 5. Tiêu chí Hoàn thành & Nghiệm thu Trang 3 (Definition of Done)

- [ ] File `F1_Analytics_Dev_Page3_Loc.pbix` được lưu tại [powerbi/](file:///c:/Users/truct/source/miniprojectBI/powerbi/).
- [ ] Trang 3 giải quyết trọn vẹn, thuyết phục 3 câu hỏi nghiệp vụ BQ3, BQ4 và BQ5.
- [ ] Thể hiện rõ nét sự khác biệt kết quả giữa các trường đua và quốc gia (BQ3).
- [ ] Phân tích Grid vs Finish (BQ4) tuân thủ nghiêm ngặt bộ lọc `Grid > 0` và có vị trí phân loại; hiển thị rõ cỡ mẫu `n` hợp lệ.
- [ ] Phân tích kết quả không phân loại (BQ5) tách biệt rõ ràng 5 nhóm `OutcomeGroup`, không gộp nhầm DNS/DSQ vào DNF.
- [ ] Tính năng Drill-through trường đua hoạt động chính xác.
- [ ] Được Trực tích hợp thành công vào Master PBIX và được Phúc ký nghiệm thu QA.
