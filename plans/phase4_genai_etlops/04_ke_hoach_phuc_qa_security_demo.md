# Kế hoạch Cá nhân Phase 4 (Luồng 4 - Độc lập): Lead QA Kiểm định Tự động (AI Grounding, Bảo mật, ETL) & Kịch bản Video Demo

**Thành viên:** Phúc  
**Vai trò:** Lead QA Specialist (AI Grounding, Text-to-SQL Security & ETL Observability) & Video Demo Coordinator  
**Điểm tải công việc:** **25 điểm**  
**Bắt đầu:** **NGAY LẬP TỨC** (Không cần chờ code xong — viết ngay bộ test bảo mật SQL, bộ Ground Truth SQL đối soát trên `dw`/`ctl` và Kịch bản Video Demo từ chiều 21/11!)  
**Hạn hoàn thành:** Tối 21/11 xong khung `tests/test_phase4_qa.py`; Chiều 22/11 xong Kịch bản Demo; Trưa 23/11 (12:00) xong QA 8/8 PASS  
**Trạng thái:** **[ ] SẴN SÀNG LÀM NGAY**

---

> [!IMPORTANT]
> ### Trọng tâm Kỹ thuật của Phúc (Chuyên sâu QA & Demo — Đã loại bỏ phần viết Báo cáo PDF)
> Phúc tập trung 100% vào vai trò **Trưởng ban Kiểm định (Lead QA)** đúng sở trường từ Phase 2–3: xây dựng bộ test tự động bảo vệ hệ thống AI không bịa số và không bị SQL Injection, đối soát số liệu ETL Monitoring, lập biên bản nghiệm thu và điều phối quay **Video Demo End-to-End 5–7 phút**.

---

## 1. Nhiệm vụ Chi tiết & Phân bổ 25 Điểm

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí hoàn thành (DoD) |
|:---:|---|:---:|:---:|---|
| **1** | **Xây dựng Bộ Kiểm thử Tự động `tests/test_phase4_qa.py` (`pytest`)**<br/>Viết sẵn từ phút 0 các nhóm test tự động:<br/>• **Security Suite (10+ mẫu):** Kiểm tra hàm `validate_readonly_sql()` chặn 100% lệnh `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `EXEC`, `;` đa câu lệnh, comment `--`/`/*`, truy cập `stg.`/`sys.`.<br/>• **DB Least-Privilege Test:** Kiểm tra tài khoản `f1_ai_reader` đọc được `dw.*`/`ctl.*` nhưng bị SQL Server từ chối mọi lệnh ghi/xóa/đọc `stg.*`.<br/>• **Ground Truth Reconciliation:** Truy vấn đối soát chuẩn trên `dw.*` (Mùa 2023, BQ4 `n = 16.434`, BQ5 5 nhóm) & `ctl.etl_run_log` (5 KPI giám sát). | **9** | Khung test: 21/11 (23:00)<br/>Chạy đủ suite: 23/11 (10:00) | - `pytest tests/test_phase4_qa.py` chạy sạch và PASS 100%.<br/>- Bộ Ground Truth SQL đối soát chạy được ngay trên SQL Server hiện có. |
| **2** | **Thực thi Trọn bộ 8 Kịch bản Nghiệm thu (QA-01 đến QA-08) & Xuất Biên bản**<br/>Kiểm định trực tiếp trên sản phẩm của Lộc (Mage Trigger), Dũng (Power BI Trang 4 & `f1_ai_reader`) và Trực (Streamlit AI + Chatbot); ghi nhận mọi lỗi cần fix và chốt biên bản `docs/evidence/phuc_phase4_qa_validation.md` + `docs/evidence/phuc_phase4_qa_run.json`. | **9** | 23/11 (12:00) | - **8/8 kịch bản QA đạt PASS 100%**: tỷ lệ AI bịa số = 0%, 100% lệnh SQL độc hại bị chặn, 100% số liệu Trang 4 khớp `ctl.etl_run_log`.<br/>- Biên bản lưu chuẩn theo format Phase 2 & Phase 3 trong `docs/evidence/`. |
| **3** | **Soạn Kịch bản Video Demo End-to-End 5–7 Phút (`docs/04_operations_and_guides/phase4_demo_script.md`)**<br/>Viết kịch bản chi tiết từng mốc giây, phân vai rõ ràng, liệt kê sẵn đúng 3 câu hỏi Chatbot (1 F1, 1 ETL, 1 câu tấn công `DROP TABLE`) và các thao tác chuột trên Mage, Power BI 4 trang, Streamlit để quay mượt trong 1–2 lần. | **5** | 22/11 (16:00) | - Kịch bản đi trọn mạch End-to-End từ lập lịch ETL -> dbt -> Power BI 4 trang -> Streamlit AI (Tóm tắt F1/ETL, up ảnh chart, Chatbot Q&A + chặn bảo mật). |
| **4** | **Điều phối Quay Video Demo & Kiểm tra Vệ sinh Source Code trước khi Nộp**<br/>Cùng nhóm quay & kiểm duyệt Video Demo 5–7 phút; rà soát `git status`/gói nộp đảm bảo không lộ `.env` hay `GEMINI_API_KEY` thật và đủ link Kaggle + hướng dẫn chạy. | **2** | 23/11 (21:30) | - Video Demo đạt chuẩn hình ảnh/âm thanh.<br/>- Gói nộp sạch secret, sẵn sàng nộp trước 22:00 ngày 23/11/2026. |
| **TỔNG** | **Điểm tải công việc Phase 4 của Phúc** | **25** | | **Hoàn tất Lead QA 8/8 PASS, Security Suite & Video Demo End-to-End** |

---

## 2. Bộ 8 Kịch bản QA Cốt lõi (QA-01 đến QA-08)

| Mã QA | Đối tượng kiểm tra | Tiêu chí PASS |
|:---:|---|---|
| **QA-01** | **Mage.ai Schedule Trigger** *(Lộc)* | Trigger đang `ACTIVE`, có lịch sử chạy tự động trong `ctl.etl_run_log` (Full + Incremental). |
| **QA-02** | **Kịch bản lỗi giả lập ETL** *(Lộc)* | `ctl.etl_run_log` ghi `run_status='failed'`, `rows_rejected > 0`, có `error_message`; `dw.FactRaceResult` giữ nguyên đúng **27.568 dòng**. |
| **QA-03** | **Power BI Trang 4 vs SQL `ctl`** *(Dũng)* | 5 KPI Cards (Total Runs, Success Rate, Avg Duration, Rows Written, Rows Rejected) khớp 100% truy vấn trực tiếp `ctl.etl_run_log`. |
| **QA-04** | **AI Tóm tắt F1 (Chống ảo giác)** *(Trực)* | Lọc Mùa 2023: AI nêu đúng 22 chặng, 2.242,0 điểm, Verstappen 19 wins, không bịa số, giữ nguyên tắc phi nhân quả BQ6; toàn bộ 1950–2026 có nhắc caveat thang điểm. |
| **QA-05** | **AI Đối chiếu Ảnh biểu đồ Power BI** *(Trực)* | Upload ảnh biểu đồ Power BI kèm số liệu thật: AI mô tả khớp xu hướng trên ảnh và trích đúng số liệu từ `dw.*`. |
| **QA-06** | **AI Giải thích Kết quả ETL** *(Trực)* | AI đọc `ctl.etl_run_log` chỉ chính xác `target_table` và `error_message` của case lỗi QA-02 kèm gợi ý khắc phục. |
| **QA-07** | **Chatbot Hỏi–Đáp (F1 & ETL)** *(Trực)* | Trả lời đúng 1 câu tiếng Việt về F1 + 1 câu về ETL, hiển thị câu T-SQL `SELECT` và bảng dữ liệu khớp SQL Server. |
| **QA-08** | **Bảo mật Text-to-SQL (2 lớp)** *(Trực & Dũng)* | 10+ mẫu tấn công `DROP`/`DELETE`/`UPDATE`/`; EXEC` bị chặn 100% bởi `validate_readonly_sql()`; đồng thời user `f1_ai_reader` bị SQL Server từ chối mọi lệnh ghi/xóa/đọc `stg.*`. |

---

## 3. Khung Kịch bản Video Demo Tinh gọn (5–7 Phút)
1. **0:00 – 0:45 (Tổng quan):** Bài toán F1 (1950–2026), nguồn Kaggle và sơ đồ kiến trúc 5 công nghệ.
2. **0:45 – 2:15 (Lập lịch Mage.ai & dbt):** Show Mage Schedule Trigger đang `ACTIVE`, lịch sử chạy tự động (Full, Incremental, case lỗi) và log `ctl.etl_run_log` / `dw.*`.
3. **2:15 – 4:00 (Power BI 4 Trang):** Lướt nhanh Trang 1–3 (F1 Overview & BQ1–BQ6) → bấm nút sang **Trang 4 (ETL Monitoring)**, bấm Refresh thấy số liệu & bảng lỗi cập nhật.
4. **4:00 – 6:30 (Streamlit AI Assistant — 1 Trang):**
   - Bấm **Tạo tóm tắt AI F1 (Mùa 2023)** (kèm upload ảnh đồ thị Power BI).
   - Chuyển chế độ **Chẩn đoán ETL** → AI phát hiện và giải thích ngay bảng lỗi ở bước 2.
   - Hỏi trực tiếp trên **Chatbot tiếng Việt** (1 câu F1 + 1 câu ETL) kèm mở **Xem câu SQL & bảng dữ liệu gốc**, sau đó gõ câu yêu cầu **xóa bảng** để chứng minh cơ chế chặn bảo mật 2 lớp.
5. **6:30 – 7:00 (Tổng kết):** Chốt kết quả QA 8/8 PASS và kết thúc.
