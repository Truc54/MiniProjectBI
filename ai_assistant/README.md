# Formula 1 BI · Generative AI Assistant (`ai_assistant/`)

Ứng dụng Streamlit **1 trang duy nhất** kết nối trực tiếp SQL Server `F1_BI` (`dw.*` và `ctl.etl_run_log`, `ctl.etl_batch_state`) dùng **Google Gemini API (Flash Free Tier — 0 VNĐ)**.

## Chức năng chính
1. **AI Tóm tắt & Giải thích Nhanh (Có kiểm chứng số liệu):**
   - **Phân tích Nghiệp vụ F1 (`dw.*`):** Tóm tắt KPI thật theo bộ lọc mùa giải / đội đua / tay đua, tuân thủ cỡ mẫu BQ4 (`grid_position > 0` và classified), tách 5 nhóm `outcome_group` (BQ5), ranh giới phi nhân quả (BQ6) và lưu ý thay đổi thang điểm lịch sử. Hỗ trợ **Upload ảnh chụp biểu đồ Power BI** để AI đối chiếu đa phương thức (ảnh + số liệu thật).
   - **Chẩn đoán Kết quả ETL (`ctl.etl_run_log`):** Tự động phát hiện bất thường (`failed`, `rows_rejected > 0`, `duration spike`), chỉ đúng bảng lỗi, trích `error_message` và gợi ý hướng xử lý.
2. **Chatbot Hỏi–Đáp Ngôn ngữ Tự nhiên (Safe Text-to-SQL):**
   - Hỏi tiếng Việt tự do cho cả dữ liệu F1 (`dw.*`) lẫn log ETL (`ctl.*`).
   - **Bảo mật 2 lớp:** Bộ lọc `validate_readonly_sql()` chỉ cho phép 1 câu `SELECT`/`WITH` trên whitelist `dw.*` & `ctl.*` (chặn 100% `DROP`, `DELETE`, `UPDATE`, `INSERT`, `;`, `--`, `stg.`, `sys.`), đồng thời ưu tiên kết nối bằng tài khoản chỉ đọc `f1_ai_reader`.
   - Luôn hiển thị expander **Xem câu T-SQL đã chạy & Bảng dữ liệu kiểm chứng** + tự động vẽ biểu đồ nhanh.

---

## Cấu hình `.env`
1. Lấy **Gemini API Key miễn phí** tại Google AI Studio: https://aistudio.google.com/apikey
2. Mở file `.env` ở thư mục gốc dự án (tham khảo `.env.example`) và bổ sung:
   ```env
   GEMINI_API_KEY=your_free_gemini_api_key
   GEMINI_MODEL=gemini-3-flash-preview

   # Tùy chọn: điền sau khi Dũng tạo xong tài khoản read-only f1_ai_reader.
   # Nếu bỏ trống, app tự dùng tạm MSSQL_USERNAME/MSSQL_PASSWORD hiện có.
   MSSQL_AI_USERNAME=f1_ai_reader
   MSSQL_AI_PASSWORD=
   ```
   *(Lưu ý: Bạn cũng có thể dán tạm Gemini API Key ngay ở thanh bên trái của giao diện Streamlit mà không cần khởi động lại app).*

---

## Cách chạy (Python cục bộ — Windows/macOS/Linux)
```powershell
pip install -r ai_assistant/requirements.txt
streamlit run ai_assistant/app.py
```
Sau đó mở trình duyệt tại: **http://localhost:8501**

## Chạy bộ kiểm thử tự động
```powershell
pytest tests/test_ai_assistant_truc.py -v
```
