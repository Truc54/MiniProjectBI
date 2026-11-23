# Formula 1 BI · Generative AI Assistant (`ai_assistant/`)

Ứng dụng web **Streamlit 2 tab** kết nối trực tiếp SQL Server `F1_BI` (`dw.*`, `ctl.etl_run_log`, `ctl.etl_batch_state`) bằng tài khoản chỉ đọc và sử dụng **Google Gemini API (Free Tier)** để tóm tắt số liệu, đối chiếu ảnh biểu đồ Power BI và hỏi đáp tiếng Việt qua Text-to-SQL.

## Chức năng chính

1. **Tab 1 – Tóm tắt AI & Biểu đồ (Bám sát số liệu thực tế):**
   - **Phân tích F1 (`dw.*`):** Lọc khoảng năm hợp lệ (`Từ năm` ≤ `Đến năm` trong `1950–2026`) và đội đua; tính sẵn toàn bộ KPI trước khi gửi cho Gemini diễn giải. Tuân thủ cỡ mẫu BQ4 (`grid_position > 0` và có vị trí về đích, `n = 16.434`), tách 5 nhóm `outcome_group` (BQ5), giữ lập trường phi nhân quả (BQ6) và tự cảnh báo khi đi qua các mốc đổi luật tính điểm (1961, 1991, 2003, 2010, 2019). Hỗ trợ **Upload ảnh PBI** để AI đối chiếu đa phương thức giữa ảnh chụp Power BI và số liệu SQL.
   - **Chẩn đoán ETL (`ctl.etl_run_log`, `ctl.etl_batch_state`):** Tự động phát hiện bất thường (lần chạy thất bại, dòng bị loại, thời lượng tăng đột biến), chỉ chính xác bảng đích lỗi, trích thông báo lỗi thực tế và đề xuất hướng xử lý.
   - Kèm 2 biểu đồ Altair tương tác và mục **Xem số liệu gốc đã gửi AI** để đối chứng.

2. **Tab 2 – Chatbot Hỏi–Đáp (Safe Text-to-SQL):**
   - Hỏi tiếng Việt tự do cho cả dữ liệu F1 (`dw.*`) lẫn nhật ký ETL (`ctl.*`), nhận diện hội thoại giao tiếp thông thường và từ chối câu hỏi ngoài phạm vi kho dữ liệu.
   - **Phòng thủ chiều sâu hai lớp:**
     - *Lớp 1 (Ứng dụng):* Tiền kiểm ý định phá hoại (`detect_unsafe_intent`) và kiểm duyệt cú pháp tĩnh (`validate_readonly_sql`) — chỉ cho phép 1 câu `SELECT` hoặc `WITH ... SELECT` trên 10 bảng/view whitelist thuộc `dw.*` và `ctl.*` (chặn `DROP`, `DELETE`, `UPDATE`, `INSERT`, `;`, `--`, `/* */`, `stg.*`, `sys.*`).
     - *Lớp 2 (SQL Server):* Ưu tiên kết nối bằng tài khoản chỉ đọc `f1_ai_reader` (`db_ai_reader`), bật `READ UNCOMMITTED` và `LOCK_TIMEOUT` để không bị treo khi ETL chạy song song.
   - Tự vẽ biểu đồ Altair cho bảng kết quả 2–20 dòng và luôn hiển thị mục **Xem SQL & Bảng dữ liệu** để kiểm chứng.

---

## Cấu hình `.env`

1. Lấy **Gemini API Key miễn phí** tại Google AI Studio: https://aistudio.google.com/apikey
2. Mở file `.env` ở thư mục gốc dự án (tham khảo `.env.example`, **không commit `.env` lên Git**) và bổ sung:
   ```env
   GEMINI_API_KEY=your_free_gemini_api_key
   GEMINI_MODEL=gemini-3-flash-preview

   # Tùy chọn: tài khoản chỉ đọc do sqlserver/ctl/01_etl_monitoring_view_and_reader.sql tạo.
   # Nếu bỏ trống, ứng dụng tự fallback sang MSSQL_USERNAME / MSSQL_PASSWORD.
   MSSQL_AI_USERNAME=f1_ai_reader
   MSSQL_AI_PASSWORD=
   ```
   *(Bạn cũng có thể chọn model hoặc dán tạm Gemini API Key trực tiếp trong nút **Cài đặt** ở góc trên bên phải giao diện mà không cần sửa `.env`.)*

---

## Cách chạy (Python cục bộ — Windows/macOS/Linux)

Chạy từ thư mục gốc dự án:
```powershell
pip install -r ai_assistant/requirements.txt
streamlit run ai_assistant/app.py
```
Sau đó mở trình duyệt tại: **http://localhost:8501**

## Chạy bộ kiểm thử tự động

```powershell
python -m pytest tests/test_ai_assistant_truc.py -v
```
*(32/32 kịch bản kiểm thử đơn vị tự động — chạy ngoại tuyến, không cần API key hay SQL Server.)*
