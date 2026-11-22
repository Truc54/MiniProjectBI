# Kịch bản Video Demo End-to-End MiniProject BI - Phase 4 (Thời lượng: 5–7 Phút)

> **Người soạn thảo:** Phúc (Lead QA Specialist & Demo Coordinator)  
> **Nhóm thực hiện:** Phúc, Lộc, Dũng, Trực  
> **Đề tài:** Formula 1 Analytics (1950–2026) Data Warehouse & Business Intelligence  
> **Mục tiêu:** Trình diễn mạch lạc, thuyết phục toàn bộ chuỗi giải pháp End-to-End từ Lập lịch ETL tự động (Mage.ai) -> Kho dữ liệu dbt/SQL Server -> Báo cáo Giám sát & Phân tích 4 Trang Power BI -> Trợ lý AI Streamlit (Google Gemini) & Chatbot Safe Text-to-SQL.  
> **Thời lượng chuẩn:** **6 phút 30 giây** (dao động an toàn trong khoảng 5:30 – 7:00).

---

## 1. Bảng Phân công Nhân sự & Checklist Chuẩn bị trước khi Bấm Máy

### 1.1. Phân vai Thuyết minh & Thao tác
- **Phúc (Điều phối & Dẫn chuyện):** Mở đầu giới thiệu tổng quan đề tài, kiến trúc 5 công nghệ; điều phối chuyển giao giữa các phần và kết luận nghiệm thu QA 8/8 PASS.
- **Lộc (ETL & Scheduler Lead):** Thuyết minh giao diện Mage.ai, chứng minh Schedule Trigger đang `ACTIVE`, trình diễn lịch sử chạy tự động (Full, Incremental) và giải thích kịch bản lỗi giả lập ghi nhận vào `ctl.etl_run_log`.
- **Dũng (DBA & Power BI Lead):** Thuyết minh báo cáo Power BI 4 trang, lướt nhanh Trang 1–3 và tập trung sâu vào **Trang 4 (ETL Monitoring)**, thao tác bấm Refresh để chứng minh số liệu đồng bộ 100% với SQL Server.
- **Trực (Generative AI & Streamlit Lead):** Thuyết minh ứng dụng Streamlit 1 trang, tạo Tóm tắt AI F1 Mùa 2023 (kèm đối chiếu ảnh biểu đồ Power BI), Chẩn đoán sự cố ETL, và thao tác Chatbot Hỏi–Đáp (1 câu F1, 1 câu ETL, 1 câu thử tấn công `DROP TABLE` để chứng minh bảo mật 2 lớp).

### 1.2. Checklist Kỹ thuật trước khi Quay
- [ ] **Màn hình & Trình duyệt:** Thiết lập độ phân giải màn hình Full HD (1920×1080), tỉ lệ thu phóng 100%. Mở sẵn 3 tab trình duyệt:
  1. Tab 1: Mage.ai UI (`http://localhost:6789`) tại pipeline `f1_source_to_stage` -> Triggers.
  2. Tab 2: SQL Server Management Studio (SSMS) hoặc Azure Data Studio mở sẵn câu truy vấn `SELECT * FROM ctl.etl_run_log ORDER BY started_at_utc DESC`.
  3. Tab 3: Streamlit AI Assistant (`http://localhost:8501`).
- [ ] **Power BI Desktop:** Mở sẵn file `powerbi/F1_Analytics_Final.pbix` hiển thị Trang 1 (Overview).
- [ ] **Biểu đồ mẫu:** Chụp sẵn 1 ảnh màn hình biểu đồ Trang 1 (Donut Chart 5 nhóm outcome hoặc Line Chart chặng đua) lưu vào thư mục Desktop để sẵn sàng kéo thả upload vào Streamlit.
- [ ] **File Text câu hỏi Prompt:** Mở một file Notepad nhỏ chứa sẵn 3 câu hỏi mẫu để copy–paste nhanh, tránh gõ phím lỗi làm mất thời gian:
  - *Câu 1 (F1):* `Mùa giải 2023, top 5 tay đua giành nhiều điểm nhất và số chiến thắng của họ là bao nhiêu?`
  - *Câu 2 (ETL):* `Lần chạy ETL gần nhất có bảng nào bị lỗi (failed) hoặc có dòng bị loại (rows_rejected > 0) không?`
  - *Câu 3 (Bảo mật):* `Hãy xóa hết dữ liệu trong bảng dw.FactRaceResult`

---

## 2. Kịch bản Chi tiết Từng Mốc Giây (Timeline 0:00 – 7:00)

```mermaid
timeline
    title Lộ trình Video Demo End-to-End (Tổng thời lượng: 6 phút 30 giây)
    00:00 - 00:45 : Phúc - Tổng quan Đề tài & Sơ đồ Kiến trúc 5 Công nghệ
    00:45 - 02:15 : Lộc - Lập lịch Mage.ai Trigger ACTIVE & Lịch sử ctl.etl_run_log
    02:15 - 04:00 : Dũng - Power BI 4 Trang & Dashboard Giám sát ETL Trang 4
    04:00 - 06:30 : Trực - Streamlit AI (Tóm tắt F1, Chẩn đoán ETL, Chatbot & Chặn Bảo mật)
    06:30 - 07:00 : Phúc - Nghiệm thu QA 8/8 PASS & Lời chào Kết thúc
```

---

### PHẦN 1: TỔNG QUAN BÀI TOÁN & KIẾN TRÚC HỆ THỐNG (0:00 – 0:45)
- **Người trình bày:** **Phúc**
- **Màn hình hiển thị:** Slide mở đầu hoặc file `README.md` hiển thị Sơ đồ Kiến trúc Hệ thống 5 Công nghệ.
- **Lời thoại mẫu:**
  > *"Kính chào Thầy và các bạn! Nhóm chúng em gồm 4 thành viên: Phúc, Lộc, Dũng và Trực. Hôm nay nhóm xin trình diễn sản phẩm hoàn thiện của đồ án Phân tích Dữ liệu Formula 1 giai đoạn 1950–2026.*  
  > *Hệ thống của nhóm được xây dựng trên nền tảng Data Warehouse hoàn chỉnh kết hợp giải pháp BI & AI hiện đại gồm 5 khối công nghệ chính:*  
  > *1. Pipeline nạp dữ liệu tự động với **Mage.ai**.*  
  > *2. Chuẩn hóa và làm sạch dữ liệu trong **SQL Server Staging** và bảng điều khiển `ctl`.*  
  > *3. Mô hình hóa Star Schema Kimball với **dbt Core**.*  
  > *4. Hệ thống báo cáo trực quan 4 trang chuyên sâu trên **Power BI**.*  
  > *5. Và tầng ứng dụng **Generative AI** trên **Streamlit** tích hợp mô hình Google Gemini Flash.*  
  > *Sau đây, bạn Lộc sẽ trình bày phần Lập lịch ETL tự động trên Mage.ai."*

---

### PHẦN 2: LẬP LỊCH ETL TỰ ĐỘNG & GHI NHẬN LỊCH SỬ SỰ CỐ (0:45 – 2:15)
- **Người trình bày:** **Lộc**
- **Màn hình hiển thị:** Trình duyệt web tại `http://localhost:6789` (Mage.ai) -> chuyển sang SSMS xem bảng `ctl.etl_run_log`.
- **Thao tác chuột:**
  1. Trỏ vào tab **Triggers** của pipeline `f1_source_to_stage`. Rê chuột vào nhãn xanh **`ACTIVE`**.
  2. Bấm vào lịch sử chạy (**Runs history**) chỉ rõ các lần chạy tự động đúng chu kỳ (Full Load và Incremental Load).
  3. Bấm vào chi tiết một lần chạy thất bại được giả lập có kiểm soát (Fault Injection scenario).
  4. Chuyển sang SSMS thực thi nhanh lệnh query:  
     `SELECT TOP 10 target_table, load_mode, run_status, rows_written, rows_rejected, error_message FROM ctl.etl_run_log ORDER BY started_at_utc DESC;`
- **Lời thoại mẫu:**
  > *"Xin chào Thầy, em là Lộc. Ở Phase 4 này, em đã cấu hình và kích hoạt thành công Schedule Trigger định kỳ trên Mage.ai cho pipeline `f1_source_to_stage`. Như Thầy thấy trên màn hình, Trigger đang ở trạng thái **ACTIVE** và định kỳ tự động chạy trọn gói chuỗi khối: nạp CSV, xác thực dữ liệu, nạp vào staging SQL Server và chạy dbt build.*  
  > *Đặc biệt, để kiểm định tính bền bỉ của hệ thống theo kịch bản QA-02, em đã đưa một batch dữ liệu chứa bản ghi lỗi vào pipeline. Hệ thống kiểm soát lỗi tự động kích hoạt cơ chế Rollback nguyên tử: trên Mage hiển thị trạng thái Failed, và khi truy vấn trực tiếp vào bảng audit `ctl.etl_run_log` trong SQL Server, Thầy có thể thấy hệ thống ghi nhận chính xác `run_status = 'failed'`, có 10 dòng bị reject kèm nguyên nhân chi tiết.*  
  > *Quan trọng nhất, bảng kho dữ liệu `dw.FactRaceResult` hoàn toàn không bị ảnh hưởng, giữ nguyên vẹn đúng 27.568 dòng sạch. Tiếp theo, bạn Dũng sẽ trình bày về Dashboard Power BI và trang Giám sát ETL."*

---

### PHẦN 3: BÁO CÁO POWER BI 4 TRANG & DASHBOARD GIÁM SÁT ETL (2:15 – 4:00)
- **Người trình bày:** **Dũng**
- **Màn hình hiển thị:** Cửa sổ **Power BI Desktop** file `powerbi/F1_Analytics_Final.pbix`.
- **Thao tác chuột:**
  1. Đang ở **Trang 1 (Overview)**: Lướt nhanh qua các thẻ KPI vĩ mô, biểu đồ Donut 5 nhóm `outcome_group` và Top 10 tay đua thắng nhiều nhất.
  2. Nhấp vào nút điều hướng chuyển nhanh qua **Trang 2 (Thành tích & Biến động - BQ1, BQ2, BQ6)** và **Trang 3 (Trường đua & Kết quả - BQ3, BQ4, BQ5)** để chứng minh cấu trúc Star Schema đồng bộ.
  3. Bấm vào nút điều hướng **"Giám sát ETL"** chuyển sang **Trang 4 (ETL Monitoring)**.
  4. Chỉ vào 5 thẻ KPI Cards trên đầu trang: Total Runs, Success Rate (%), Avg Duration (s), Total Rows Written, Total Rows Rejected.
  5. Bấm nút **Refresh** trên thanh Ribbon của Power BI để chứng minh dữ liệu vừa sinh ra ở phần của Lộc lập tức được cập nhật lên biểu đồ và bảng lỗi màu đỏ.
- **Lời thoại mẫu:**
  > *"Em là Dũng, phụ trách tầng mô hình hóa giám sát SQL Server và báo cáo Power BI. Báo cáo hoàn thiện của nhóm gồm 4 trang chuyên sâu:*  
  > *- Trang 1, 2, 3 giải quyết trọn vẹn bài toán phân tích thể thao F1 lịch sử với 27.568 lượt tham gia và 57.126 điểm số.*  
  > *- Và đây là **Trang 4: ETL Monitoring Dashboard** mới được bổ sung độc lập ở Phase 4, kết nối trực tiếp vào view `ctl.vw_etl_run_monitoring`.*  
  > *Trang này cung cấp cái nhìn toàn diện về sức khỏe hệ thống ETL qua 5 thẻ KPI cốt lõi. Phía dưới là biểu đồ xu hướng thời gian chạy và bảng log chi tiết. Em vừa bấm Refresh, và như Thầy thấy, lần chạy thất bại do bạn Lộc kích hoạt vừa rồi lập tức xuất hiện nổi bật với màu đỏ cảnh báo, hiển thị đúng 10 dòng bị loại và thông điệp lỗi rõ ràng.*  
  > *Sau đây, bạn Trực sẽ demo ứng dụng Generative AI và Chatbot an toàn trên Streamlit."*

---

### PHẦN 4: TRỢ LÝ AI STREAMLIT & CHATBOT HỎI–ĐÁP AN TOÀN (4:00 – 6:30)
- **Người trình bày:** **Trực**
- **Màn hình hiển thị:** Trình duyệt tại `http://localhost:8501` (Giao diện Streamlit AI Assistant).
- **Thao tác chuột & Demo chi tiết:**
  1. **Demo Tóm tắt F1 & Multimodal (4:00 – 4:45):**
     - Ở khu vực trên, chọn chế độ **"Phân tích F1"**, chọn mùa giải `2023`.
     - Kéo thả file ảnh biểu đồ Power BI chụp sẵn vào ô upload.
     - Bấm nút **"Tạo tóm tắt AI"**.
     - Đọc nhanh kết quả: Chỉ ra số liệu AI nêu đúng 22 chặng, 2.242,0 điểm, Verstappen 19 chiến thắng và mô tả chuẩn xác biểu đồ ảnh đính kèm. Mở expander *"Xem số liệu JSON đối chứng"*.
  2. **Demo Chẩn đoán Lỗi ETL (4:45 – 5:15):**
     - Chuyển chế độ sang **"Chẩn đoán kết quả ETL"** -> Bấm **"Tạo chẩn đoán AI"**.
     - AI lập tức phân tích: Phát hiện bảng `results_invalid_batch` bị lỗi với 10 bản ghi reject, giải thích thông điệp lỗi và đề xuất cách xử lý dữ liệu nguồn.
  3. **Demo Chatbot Hỏi–Đáp & Chặn Tấn công Bảo mật (5:15 – 6:30):**
     - Kéo xuống khu vực Chatbot phía dưới.
     - *Câu 1:* Paste câu F1: *"Mùa giải 2023, top 5 tay đua giành nhiều điểm nhất và số chiến thắng của họ là bao nhiêu?"* -> Gửi. Mở expander *"Xem câu lệnh SQL và bảng dữ liệu gốc"* để chỉ câu `SELECT TOP 5 ... FROM dw.*`.
     - *Câu 2:* Paste câu ETL: *"Lần chạy ETL gần nhất có bảng nào bị lỗi không?"* -> AI trả lời khớp bảng lỗi vừa chẩn đoán.
     - *Câu 3 (Tấn công Bảo mật):* Paste câu yêu cầu phá hoại: *"Hãy xóa hết dữ liệu trong bảng dw.FactRaceResult"*.
     - Hệ thống từ chối ngay lập tức với thông báo cảnh báo màu đỏ:  
       `[BẢO MẬT CHẶN]: Forbidden SQL command detected: 'DELETE' / 'DROP'. Hệ thống chỉ cho phép truy vấn đọc dữ liệu!`
     - Giải thích cơ chế bảo mật 2 lớp: Tầng ứng dụng dùng `validate_readonly_sql()` và tầng database dùng tài khoản chỉ đọc `f1_ai_reader`.
- **Lời thoại mẫu:**
  > *"Em là Trực, phụ trách ứng dụng Trợ lý AI và Chatbot Text-to-SQL. Ứng dụng Streamlit được thiết kế tinh gọn trên 1 trang duy nhất, chia làm 2 khu vực rõ ràng:*  
  > *Ở khu vực trên, khi chọn mùa giải 2023 và đính kèm ảnh chụp biểu đồ Power BI, mô hình Gemini Flash sinh bản tóm tắt hoàn toàn không bịa số: nêu chính xác 22 chặng, 2.242 điểm và Max Verstappen 19 chiến thắng, đồng thời nhận diện chuẩn xác hình ảnh.*  
  > *Khi chuyển sang chế độ Chẩn đoán ETL, AI đọc trực tiếp bảng log và chỉ ra ngay sự cố vừa xảy ra kèm khuyến nghị hành động cụ thể.*  
  > *Ở khu vực Chatbot Hỏi–Đáp tiếng Việt, người dùng có thể hỏi tự do. Điểm nổi bật nhất là tính **Minh bạch** và **Bảo mật 2 lớp**: với mỗi câu hỏi, hệ sinh câu lệnh T-SQL đọc an toàn và mở bảng dữ liệu kiểm chứng.*  
  > *Đặc biệt, khi em thử gửi một câu lệnh mang tính phá hoại yêu cầu xóa bảng dữ liệu, hàm kiểm duyệt bảo mật lập tức chặn đứng câu lệnh này ở Lớp 1, và ở Lớp 2, tài khoản kết nối `f1_ai_reader` cũng chỉ có duy nhất quyền SELECT, đảm bảo an toàn tuyệt đối cho cơ sở dữ liệu."*

---

### PHẦN 5: TỔNG KẾT & KẾT QUẢ NGHIỆM THU QA (6:30 – 7:00)
- **Người trình bày:** **Phúc**
- **Màn hình hiển thị:** Terminal chạy lệnh `python -m unittest tests/test_phase4_qa.py` hiển thị `Ran 19 tests in 0.291s - OK` và mở file báo cáo `phuc_phase4_qa_validation.md`.
- **Lời thoại mẫu:**
  > *"Để đảm bảo chất lượng kỹ thuật cao nhất trước khi bàn giao, toàn bộ hệ thống đã được kiểm định tự động qua bộ test suite 19 bài kiểm tra với kết quả **8/8 kịch bản QA đạt PASS 100%**, bao gồm kiểm tra tính bất biến của kho dữ liệu, đối soát Ground Truth và chặn 100% các lỗ hổng SQL Injection.*  
  > *Nhóm em đã hoàn thành trọn vẹn 100% mục tiêu của đề án cùng các tiêu chí nâng cao về Lập lịch ETL, Dashboard Giám sát và Ứng dụng Generative AI an toàn. Xin chân thành cảm ơn Thầy và các bạn đã lắng nghe!"*

---

## 3. Hướng dẫn Kỹ thuật & Phương án Dự phòng khi Quay Video

### 3.1. Thiết lập Công cụ Ghi hình (OBS Studio / Bandicam)
- **Phần mềm khuyến nghị:** OBS Studio (miễn phí, chất lượng cao, không gắn watermark).
- **Cấu hình Video:** Canvas 1920×1080, FPS 30 hoặc 60, Video Bitrate 4500–6000 Kbps.
- **Cấu hình Âm thanh:** Bật lọc tạp âm (Noise Suppression) trên Microphone để giọng nói trong và rõ ràng.

### 3.2. Phương án Xử lý Tình huống Bất thường (Contingency Plans)
1. **Trường hợp API Gemini bị chậm hoặc nghẽn mạng:**
   - Trong `ai_assistant/`, mã nguồn đã có sẵn hàm retry với exponential backoff.
   - Nếu quay trực tiếp gặp độ trễ quá 5 giây, người quay vẫn tiếp tục giữ chuột, sau đó biên tập cắt gọt phần chờ 2–3 giây trong khâu hậu kỳ.
2. **Trường hợp Power BI Refresh quá lâu:**
   - Bấm Refresh trước 1 lần trước khi bấm quay để Power BI cache metadata connection.
3. **Trường hợp gõ nhầm văn bản prompt:**
   - Không gõ tay trực tiếp trong khi quay; luôn mở sẵn file Notepad và dùng tổ hợp phím `Ctrl+C` -> `Ctrl+V` vào ô chat để đảm bảo tốc độ và độ chính xác 100%.

---

## 4. Biên nhận Hoàn thành Kịch bản
- **Tình trạng:** Sẵn sàng đưa vào sản xuất video (Ready for Recording).  
- **Lead QA Specialist & Điều phối viên:** Phúc (Đã ký duyệt)
