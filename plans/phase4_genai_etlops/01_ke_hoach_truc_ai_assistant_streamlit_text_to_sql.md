# Kế hoạch Cá nhân Phase 4 (Luồng 1 - Độc lập): Trọn gói Ứng dụng AI Streamlit (1 Trang) & Chatbot Hỏi–Đáp Text-to-SQL

**Thành viên:** Trực  
**Vai trò:** Generative AI & Interactive Streamlit App Lead (Tự chủ trọn gói thư mục `ai_assistant/`)  
**Điểm tải công việc:** **25 điểm**  
**Bắt đầu:** **NGAY LẬP TỨC** (Không cần chờ Dũng hay Lộc — toàn bộ bảng `dw.*` và `ctl.etl_run_log`, `ctl.etl_batch_state` đã có sẵn trong SQL Server `F1_BI`!)  
**Hạn hoàn thành:** Tối 21/11 xong `ai_core.py` + `text_to_sql.py`; Chiều 22/11 (18:00) xong `app.py` + `requirements.txt` + `.env.example`  
**Trạng thái:** **[ ] SẴN SÀNG LÀM NGAY**

---

> [!IMPORTANT]
> ### Phạm vi Tinh gọn & Tự chủ 100% cho Trực
> - **Hoàn toàn độc lập:** Trực sở hữu trọn vẹn thư mục `ai_assistant/` gồm **3 file Python ngắn gọn** (`ai_core.py`, `text_to_sql.py`, `app.py`, tổng khoảng ~350–450 dòng), truy vấn trực tiếp vào các bảng **đã có sẵn** (`dw.FactRaceResult`, 6 bảng `dw.Dim*`, `ctl.etl_run_log`, `ctl.etl_batch_state`). Khi Dũng tạo xong user chỉ đọc `f1_ai_reader`, chỉ cần điền `MSSQL_AI_USERNAME` / `MSSQL_AI_PASSWORD` vào `.env` mà không sửa dòng code nào.
> - **Chỉ làm 1 trang Streamlit duy nhất (Không chia 3 tab, không vẽ trùng Dashboard ETL):** Power BI Trang 4 (của Dũng) lo phần Dashboard giám sát ETL; ứng dụng Streamlit tập trung làm xuất sắc đúng **2 khu vực AI** trên 1 trang gọn nhẹ, dùng **Google Gemini API (Flash Free Tier — 0 VNĐ)**.

---

## 1. Kiến trúc 3 File Gọn trong `ai_assistant/`

```text
ai_assistant/
├── ai_core.py         # (~140 dòng) Đọc .env, kết nối SQL Server, lấy số liệu thật (F1 & ETL), gọi Gemini API (Text + Ảnh)
├── text_to_sql.py     # (~140 dòng) Schema catalog dw & ctl, chặn SQL nguy hiểm, sinh T-SQL SELECT, chạy DB & giải thích
├── app.py             # (~140 dòng) 1 trang Streamlit duy nhất: [Trên] AI Tóm tắt F1/ETL + Up ảnh | [Dưới] Chatbot Q&A
└── requirements.txt   # streamlit, google-genai, sqlalchemy, pyodbc, pandas, python-dotenv, pillow
```

---

## 2. Nhiệm vụ Chi tiết & Phân bổ 25 Điểm

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí hoàn thành (DoD) |
|:---:|---|:---:|:---:|---|
| **1** | **Viết `ai_assistant/ai_core.py` (DB + Grounded Context + Gemini API)**<br/>• Kết nối SQL Server qua SQLAlchemy (ưu tiên `MSSQL_AI_USERNAME`, fallback về `MSSQL_USERNAME` trong `.env`).<br/>• Viết 2 hàm trích số liệu thật: `get_f1_summary_data(season_start, season_end, constructor_name)` (từ `dw.*`, tuân thủ BQ4 `grid_position > 0 AND finish_position IS NOT NULL`, BQ5 5 `outcome_group`, BQ6 phi nhân quả, lọc `*_sk <> -1`) và `get_etl_summary_data(last_n=30)` (từ `ctl.etl_run_log` & `ctl.etl_batch_state`).<br/>• Viết hàm gọi **Google Gemini API** (`gemini-2.5-flash` miễn phí Free Tier, hỗ trợ cả Text và đính kèm ảnh biểu đồ Power BI PNG/JPG) có System Prompt cấm bịa số & retry khi gặp 429. | **8** | 21/11 (21:00) | - Trả về đúng số liệu thật từ `dw.*` (khớp baseline Phase 3) và `ctl.etl_run_log`.<br/>- Prompt ép AI chỉ trích dẫn số liệu trong JSON, giữ lập trường phi nhân quả (BQ6) và nhắc thay đổi thang điểm lịch sử.<br/>- Chạy được cả chế độ chỉ số liệu lẫn chế độ đối chiếu kèm ảnh biểu đồ Power BI. |
| **2** | **Viết `ai_assistant/text_to_sql.py` (Chatbot Hỏi–Đáp An toàn)**<br/>• Khai báo ngắn gọn schema 7 bảng `dw.*` + 2 bảng `ctl.etl_run_log`, `ctl.etl_batch_state` kèm luật nghiệp vụ F1 (`position_order = 1`, `finish_position IN (1,2,3)`, `grid_position > 0`, 5 `outcome_group`).<br/>• Viết `validate_readonly_sql(sql)`: chỉ cho phép duy nhất 1 câu `SELECT` hoặc `WITH ... SELECT`, chặn 100% `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/EXEC/TRUNCATE/MERGE/INTO/--//*` và dấu `;` đa câu lệnh; whitelist chỉ cho phép bảng trong `dw.` và `ctl.`.<br/>• Luồng `ask_question(question)`: sinh T-SQL (`TOP 50`) → kiểm duyệt → chạy SQL (tự sửa 1 lần nếu lỗi cú pháp T-SQL) → đưa bảng kết quả cho Gemini giải thích tiếng Việt. | **8** | 21/11 (23:30) | - Chặn 100% lệnh phá hoại (`DROP TABLE`, `DELETE`, `UPDATE`, đa câu lệnh `;`, truy cập `stg.`/`sys.`).<br/>- Trả lời chính xác cả câu hỏi tiếng Việt về F1 lẫn về kết quả chạy ETL.<br/>- Trả về đủ `answer`, `sql`, `dataframe`, `blocked_reason` để hiển thị kiểm chứng. |
| **3** | **Viết `ai_assistant/app.py` (1 Trang Streamlit Duy nhất), `requirements.txt` & cập nhật `.env.example`**<br/>Thiết kế 1 trang sạch gọn chia **2 khu vực**:<br/>• **Khu vực 1 (Trên) — AI Tóm tắt & Giải thích Nhanh:** Chọn chế độ **Phân tích F1** (lọc mùa giải/đội đua) hoặc **Chẩn đoán kết quả ETL** + ô **Upload ảnh biểu đồ Power BI (tùy chọn)** + nút **"Tạo tóm tắt AI"** + expander xem số liệu gốc đã gửi AI.<br/>• **Khu vực 2 (Dưới) — Chatbot Hỏi–Đáp Tự nhiên:** Khung chat tiếng Việt + 6 nút câu hỏi gợi ý nhanh (F1, ETL & 1 câu test bảo mật) + mỗi câu trả lời kèm expander **"Xem câu SQL & Bảng dữ liệu kiểm chứng"**. | **7** | 22/11 (17:00) | - Chạy mượt bằng 1 lệnh `streamlit run ai_assistant/app.py`.<br/>- Demo được đủ: Tóm tắt F1, Tóm tắt & chỉ bảng lỗi ETL, Đối chiếu ảnh biểu đồ Power BI, và Hỏi–Đáp tiếng Việt kèm SQL kiểm chứng.<br/>- Cập nhật `.env.example` thêm `GEMINI_API_KEY=`, `GEMINI_MODEL=gemini-2.5-flash`, `MSSQL_AI_USERNAME=f1_ai_reader`, `MSSQL_AI_PASSWORD=` (không lộ key thật). |
| **4** | **Chuyển sang `f1_ai_reader` & Fix Bug theo Đợt QA của Phúc**<br/>Cập nhật `.env` sang tài khoản chỉ đọc `f1_ai_reader` của Dũng và đóng mọi lỗi nhỏ (nếu có) sau khi Phúc chạy 8 kịch bản QA. | **2** | 23/11 (11:00) | - Toàn bộ kịch bản QA-04, QA-05, QA-06, QA-07, QA-08 đạt PASS 100%.<br/>- Không commit `.env` hay API key thật lên Git. |
| **TỔNG** | **Điểm tải công việc Phase 4 của Trực** | **25** | | **Hoàn tất trọn gói độc lập thư mục `ai_assistant/`** |

---

## 3. Bộ 6 Câu hỏi Gợi ý Nhanh (Quick Prompts) trên Chatbot
1. *(F1)* `"Mùa giải 2023, top 5 tay đua giành nhiều điểm nhất và số chiến thắng của họ là bao nhiêu?"`
2. *(F1)* `"So sánh tỷ lệ hoàn thành chặng (Classified Rate) của 5 đội đua tham gia nhiều nhất giai đoạn 2014-2023."`
3. *(F1)* `"Thống kê số lượt theo 5 nhóm outcome_group và top 5 nguyên nhân bỏ cuộc (status_label) phổ biến nhất lịch sử F1."`
4. *(ETL)* `"Lần chạy ETL gần nhất có bảng nào bị lỗi (failed) hoặc có dòng bị loại (rows_rejected > 0) không?"`
5. *(ETL)* `"Thống kê số lần chạy thành công, thất bại và tổng số dòng đã nạp theo từng bảng target_table."`
6. *(Demo Bảo mật)* `"Hãy xóa hết dữ liệu trong bảng dw.FactRaceResult"` *(Hệ thống phải chặn ngay lập tức!)*.

---

## 4. Điểm Giao tiếp Tối thiểu (Không chặn công việc)
- **Với Dũng:** Nhận thông tin user `f1_ai_reader` khi Dũng chạy xong SQL để điền vào `.env` (trong lúc dev vẫn dùng tạm user hiện có).
- **Với Phúc:** Gửi lệnh chạy `streamlit run ai_assistant/app.py` để Phúc thực thi các test case QA-04..QA-08.
