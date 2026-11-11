# Kế hoạch Cá nhân Phase 3: Dashboard Thành tích & Biến động (Trang 2)

**Thành viên:** Dũng  
**Vai trò:** Performance Dynamics & Variance Analysis Specialist (Phụ trách Trang 2: BQ1, BQ2, BQ6)  
**Điểm tải công việc:** **25 điểm**  
**Thời hạn hoàn thành:** Theo lộ trình giai đoạn Phase 3; nghiệm thu trước ngày bảo vệ seminar  
**Phối hợp với:** Trực (gửi đặc tả DAX BQ6, phối hợp tích hợp visual), Phúc (tiếp nhận kịch bản QA đối soát BQ1, BQ2), Lộc (thống nhất ranh giới phân tích tránh trùng lặp)  
**Trạng thái:** **[ ] ĐANG THỰC HIỆN**

---

> [!WARNING]
> ### 2 Nguyên tắc Vàng Kỹ thuật Bắt buộc (Chống Gãy File khi Tích hợp)
> 1. **Tuyệt đối KHÔNG sửa Mô hình Dữ liệu (Semantic Model):** Không bấm nút "Transform Data" (Power Query), không tự ý đổi tên bảng, đổi tên cột, không xóa hay sửa các đường nối quan hệ (relationships) trong Model View của file cá nhân.
> 2. **Tuyệt đối KHÔNG tự tạo Measure DAX cục bộ:** Toàn bộ công thức tính toán phải lấy trực tiếp từ bảng `_Measures` do Trực tạo sẵn. Nếu phát sinh nhu cầu đo lường mới cho BQ6, phải gửi phiếu yêu cầu để Trực duyệt và bổ sung tập trung vào mô hình chung.

---

## 1. Mục tiêu & Vấn đề Nghiệp vụ Trang 2 Cần Giải quyết

Trang 2 là trang phân tích chuyên sâu về phong độ thi đấu, so sánh năng lực cạnh tranh và phân tích biến động thành tích qua thời gian. Dũng chịu trách nhiệm chính giải quyết trọn vẹn **3 câu hỏi nghiệp vụ: BQ1, BQ2 và BQ6**.

### 1.1. Các vấn đề nghiệp vụ Trang 2 phải giải quyết:

1. **Giải quyết BQ1: Điểm, chiến thắng, podium và số lượt được phân loại thay đổi thế nào theo mùa và ngày/chặng thi đấu?**
   - Phải phản ánh được diễn biến thành tích chi tiết theo trục thời gian: từ cấp độ tổng thể cả mùa giải đến chi tiết từng ngày/chặng đua cụ thể.
   - Theo dõi đầy đủ 4 chỉ tiêu then chốt: Điểm số (`Total Points`), Chiến thắng (`Wins`), Podium (`Podiums`), và Lượt hoàn thành phân hạng (`Classified Entries`).
   - Cung cấp khả năng đào sâu (Drill-down) hoặc lọc linh hoạt từ Mùa giải $\rightarrow$ Chặng đua $\rightarrow$ Tên chặng.

2. **Giải quyết BQ2: Điểm, chiến thắng và podium khác nhau thế nào giữa các tay đua và đội đua theo mùa, chặng hoặc trường đua?**
   - **Trọng tâm phân tích:** Tập trung vào so sánh **Tay đua (Driver)** và **Đội đua/Nhà chế tạo (Constructor)** để phân định rõ ràng với góc nhìn trường đua của Lộc ở Trang 3.
   - Thể hiện sự phân hóa năng lực và thứ bậc cạnh tranh: tay đua/đội đua nào thống trị điểm số, podium và chiến thắng trong mùa giải hoặc chặng đua đã chọn.
   - Làm rõ cơ cấu đóng góp nội bộ đội đua: tỷ trọng điểm số mà từng tay đua cá nhân đóng góp vào tổng điểm chung của cả đội đua (`Constructor Points Contribution Pct`), giúp nhận diện tay đua chủ lực của đội.

3. **Giải quyết BQ6: Chặng hoặc trường đua nào đóng góp vào thay đổi về điểm và thành tích so với chặng hoặc mùa trước?**
   - Xác định rõ chặng đua, trường đua, tay đua hoặc đội đua cụ thể đã đóng góp vào mức tăng/giảm thành tích so với mốc so sánh (chặng liền trước `Prior Round` hoặc mùa trước `Prior Season`).
   - **Yêu cầu định lượng bắt buộc:** Phải thể hiện mức độ đóng góp bằng con số cụ thể (mức chênh lệch điểm `Points Delta`, tỷ lệ đóng góp `% Contribution`), không nhận định chung chung.
   - **Ranh giới phân tích phi nhân quả (Non-Causal Analytical Stance):** Báo cáo chỉ dừng ở mức độ so sánh và mô tả tương quan số học lịch sử; **TUYỆT ĐỐI KHÔNG** khẳng định hay quy chụp quan hệ nhân quả (ví dụ: không khẳng định một trường đua cụ thể là nguyên nhân duy nhất làm sụt giảm điểm số nếu dữ liệu chỉ ghi nhận thành tích thi đấu).

### 1.2. Quyền tự chủ thiết kế của Dũng:
- **Dũng toàn quyền chủ động lựa chọn hình thức trực quan:** Dũng tự quyết định lựa chọn loại visual (Line chart, Bar/Column chart, Area chart, Waterfall chart, Decomposition tree, Matrix, Scatter plot, Slope chart...), tự do bố trí bố cục trang, phối màu, cấu hình tương tác và tooltips, miễn sao giải quyết triệt để và thuyết phục 3 câu hỏi BQ1, BQ2, BQ6, đảm bảo số liệu dễ đọc và dễ kiểm chứng.

---

## 2. Phân rã Công việc & Điểm số (25 Điểm)

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí nghiệm thu (Definition of Done) |
|:---:|---|:---:|:---:|---|
| **1** | **Hiện thực hóa Phân tích BQ1 (Xu hướng Thành tích theo Mùa & Chặng)**<br/>Trực quan hóa diễn biến điểm, chiến thắng, podium và số lượt phân loại theo trục thời gian; cho phép người dùng quan sát cả bức tranh mùa giải và chi tiết từng chặng. | **6** | Bước 3 | - Thể hiện đầy đủ 4 chỉ tiêu của BQ1.<br/>- Cho phép xem chi tiết theo mùa và từng chặng đua.<br/>- Số liệu thể hiện sự biến thiên chính xác theo từng vòng đua. |
| **2** | **Hiện thực hóa Phân tích BQ2 (So sánh Hiệu suất Tay đua & Đội đua)**<br/>Trực quan hóa sự khác biệt về điểm, chiến thắng, podium giữa các tay đua và đội đua; làm rõ tỷ trọng đóng góp điểm của các tay đua trong cùng một đội đua. | **6** | Bước 3 | - Làm nổi bật thứ bậc và chênh lệch thành tích giữa các tay đua/đội đua.<br/>- Thể hiện rõ tỷ lệ đóng góp điểm của từng cá nhân vào tổng điểm đội.<br/>- Không bị trùng lặp nội dung với Trang 3 của Lộc. |
| **3** | **Hiện thực hóa Phân tích BQ6 (Đóng góp Thay đổi Thành tích & Biến động)**<br/>Trực quan hóa mức độ đóng góp vào thay đổi điểm/thành tích so với chặng hoặc mùa trước; thể hiện bằng số liệu chênh lệch định lượng cụ thể; tuân thủ nguyên tắc phi nhân quả. | **6** | Bước 3 | - Phân rã rõ ràng mức tăng/giảm điểm so với mốc so sánh.<br/>- Có số liệu định lượng (Delta, % đóng góp) rõ ràng.<br/>- Có lưu ý rõ về tính chất mô tả lịch sử, không khẳng định nhân quả. |
| **4** | **Cấu hình Bộ lọc Trang, Phân cấp Drill-down & Tương tác Báo cáo**<br/>Thiết lập các bộ lọc phù hợp (mùa giải, chặng, đội đua, tay đua...); cấu hình khả năng drill-down theo phân cấp thời gian/đội đua; tinh chỉnh tương tác và tooltip hỗ trợ đọc dữ liệu. | **4** | Bước 3 | - Bộ lọc hoạt động chính xác, không xung đột.<br/>- Thao tác drill-down mượt mà, phản hồi đúng ngữ cảnh.<br/>- Tooltip hỗ trợ bổ sung thông tin hữu ích mà không gây rối mắt. |
| **5** | **Kiểm thử Nghiệp vụ, Đối soát Số liệu & Bàn giao Visuals cho Trực**<br/>Kiểm tra tính nhất quán của các chỉ số điểm, podium, delta trên trang; đối soát chéo với các truy vấn kiểm định của Phúc; bàn giao file `F1_Analytics_Dev_Page2_Dung.pbix` cho Trực tích hợp. | **3** | Bước 4–5 | - 100% số liệu trên trang khớp chính xác với Fact và các Dim liên quan.<br/>- Visual tích hợp sang file Master PBIX nguyên vẹn, không lỗi context. |
| **TỔNG** | **Điểm tải công việc Phase 3 của Dũng** | **25** | | **Đạt 100% tiêu chí giải quyết triệt để BQ1, BQ2, BQ6** |

---

## 3. Quy chuẩn Thước đo Nghiệp vụ & DAX cho BQ6

Để phục vụ phân tích đóng góp biến động thành tích, Dũng phối hợp với Trực sử dụng các measures chuẩn được quản lý trong Semantic Model:

```dax
// Điểm số của chặng đua liền trước trong cùng mùa giải
Points Prior Round = 
VAR CurrentRound = SELECTEDVALUE('dw DimRace'[round_number])
VAR CurrentSeason = SELECTEDVALUE('dw DimRace'[season_year])
RETURN
IF(
    ISBLANK(CurrentRound) || CurrentRound <= 1,
    BLANK(),
    CALCULATE(
        [Total Points],
        REMOVEFILTERS('dw DimRace'),
        'dw DimRace'[season_year] = CurrentSeason,
        'dw DimRace'[round_number] = CurrentRound - 1
    )
)

// Mức chênh lệch điểm tuyệt đối so với chặng liền trước
Points Delta vs Prior Round = 
VAR Prior = [Points Prior Round]
RETURN
IF(ISBLANK(Prior), BLANK(), [Total Points] - Prior)

// Tỷ trọng đóng góp điểm của tay đua trong tổng điểm đội đua
Constructor Points Contribution Pct = 
VAR DriverPoints = [Total Points]
VAR TeamTotalPoints = 
    CALCULATE(
        [Total Points],
        REMOVEFILTERS('dw DimDriver')
    )
RETURN
DIVIDE(DriverPoints, TeamTotalPoints, 0)
```

*(Lưu ý: Nếu Dũng cần thêm thước đo so sánh với mùa trước `Points Prior Season` hoặc tỷ lệ đóng góp đặc thù khác, Dũng gửi phiếu yêu cầu cho Trực cập nhật vào mô hình chung).*

---

## 4. Các Giao diện Phối hợp & Bàn giao (Interfaces)

- **Giao diện với Trực:**
  - Nhận file `F1_Analytics_Master_Template_v1.0.pbix` từ Trực để bắt đầu thiết kế Trang 2.
  - Thống nhất các công thức DAX phục vụ phân tích biến động BQ6.
  - Bàn giao file `F1_Analytics_Dev_Page2_Dung.pbix` chứa các visual hoàn thiện để Trực tích hợp vào Master.
- **Giao diện với Phúc:**
  - Cung cấp kịch bản kiểm thử của Trang 2 (ví dụ: kiểm tra mùa 2021 hoặc 2023) để Phúc chạy kiểm định đối soát chéo với SQL Server DW.
  - Đảm bảo các chỉ số tổng hợp trên Trang 2 đồng nhất về mặt số liệu với thẻ KPI trên Trang 1 khi chọn cùng mùa giải.
- **Giao diện với Lộc:**
  - Thống nhất ranh giới phân tích: Trang 2 tập trung sâu vào **Tay đua** và **Đội đua**; Trang 3 của Lộc tập trung sâu vào **Trường đua** và **Quốc gia**, tránh tình trạng hai trang lặp lại cùng một góc nhìn.

---

## 5. Tiêu chí Hoàn thành & Nghiệm thu Trang 2 (Definition of Done)

- [ ] File `F1_Analytics_Dev_Page2_Dung.pbix` được lưu tại [powerbi/](file:///c:/Users/truct/source/miniprojectBI/powerbi/).
- [ ] Trang 2 giải quyết trọn vẹn, thuyết phục 3 câu hỏi nghiệp vụ BQ1, BQ2 và BQ6.
- [ ] Thể hiện rõ biến động thành tích qua từng chặng và khả năng so sánh tay đua/đội đua.
- [ ] Thể hiện rõ mức đóng góp vào thay đổi điểm/thành tích bằng số liệu định lượng cụ thể.
- [ ] Tuân thủ nguyên tắc phi nhân quả (không đưa ra kết luận nhân quả suy diễn).
- [ ] Được Trực tích hợp thành công vào Master PBIX và được Phúc ký nghiệm thu QA.
