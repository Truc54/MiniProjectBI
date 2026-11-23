# Formula 1 Analytics (1950–2026) · MiniProject BI

**Môn học:** Hệ thống thông tin phục vụ trí tuệ kinh doanh 
**Trường:** Đại học Khoa học Tự nhiên, ĐHQG-HCM  
**Nhóm thực hiện:** Nhóm 7  
**Giảng viên hướng dẫn:** Hồ Thị Hoàng Vy, Tiết Gia Hồng, Nguyễn Ngọc Minh Châu  

### Thành viên nhóm & Phân công
- **Dương Viết Dũng (23120241):** Quản trị hạ tầng SQL Server (`stg`, `ctl`, `dw`), thiết kế DDL & Clustered Columnstore Index; Dashboard Trang 2 (Thành tích & Biến động đội đua — BQ1, BQ2, BQ6); view giám sát `ctl.vw_etl_run_monitoring`, tài khoản chỉ đọc `f1_ai_reader`, Trang 4 Power BI (Giám sát vận hành ETL) và đóng gói `powerbi/F1_Analytics_Final.pbix`.
- **Lê Văn Lộc (23120141):** Pipeline Mage.ai Ingestion (Full/Incremental Load); luồng biến đổi dbt Core (7 view `stg_clean`, 6 Dimension, `FactRaceResult`, 43 kiểm thử ngữ nghĩa); Dashboard Trang 3 (Trường đua & Kết quả thi đấu — BQ3–BQ5) cùng trang Drill-through Circuit Profile; cấu hình Mage Schedule Trigger (`triggers.yaml`) và kiểm chứng lịch sử thực thi kèm kịch bản lỗi giả lập.
- **Trần Lê Trung Trực (23120180):** Thiết kế kiến trúc kho dữ liệu Star Schema; chuẩn hóa thư viện measure DAX tập trung (`_Measures`) & tích hợp Master PBIX; thiết kế và phát triển toàn diện ứng dụng Trợ lý Generative AI trên Streamlit (`ai_assistant/`) tích hợp Google Gemini API (tóm tắt F1/ETL bám sát số liệu, đối chiếu ảnh biểu đồ Power BI, Chatbot Text-to-SQL phòng thủ hai lớp, biểu đồ Altair tương tác) cùng bộ 32 kiểm thử đơn vị (`tests/test_ai_assistant_truc.py`); tổng hợp và biên tập báo cáo.
- **Nguyễn Hồng Phúc (23120331):** Khảo sát và đặc tả dữ liệu nguồn; xây dựng Semantic Model & Dashboard Trang 1 (Overview); chủ trì kiểm định bảo mật Text-to-SQL, đối soát độ chính xác AI và nghiệm thu vận hành toàn diện (`tests/test_phase4_qa.py`, 8/8 kịch bản QA-01 đến QA-08) cùng kịch bản Video Demo.

---

## 🏗️ Kiến trúc Hệ thống (End-to-End BI, ETLOps & Generative AI)

```text
Kaggle CSV (dataset/ · 1950–2026)
        │
        ▼
Mage.ai Orchestration & Schedule Triggers (mage/)
  [load_f1_csv -> validate_f1_table -> load_sqlserver -> dbt_transformation -> commit_watermark]
        │                                             │
        ▼                                             ▼
SQL Server: Schema [stg]                      SQL Server: Schema [ctl]
        │                                     (etl_run_log, etl_batch_state,
        ▼                                      vw_etl_run_monitoring)
dbt Core (stg_clean Views -> Kimball Star Schema)     │
        │                                             │
        ▼                                             │
SQL Server: Schema [dw] (FactRaceResult CCI + 6 Dims) │
        │                                             │
        ├─────────────────────┬───────────────────────┤
        ▼                     ▼                       ▼
Power BI (powerbi/F1_Analytics_Final.pbix)    F1 BI Assistant (ai_assistant/)
- Trang 1–3 + Drill-through Circuit Profile   - Streamlit 2 tab + Altair Charts
- Trang 4: Giám sát vận hành ETL              - Google Gemini API (Free Tier)
                                              - Phòng thủ Text-to-SQL 2 lớp
                                                (App Guardrail + f1_ai_reader RO)
```

---

## 📂 Cấu trúc Thư mục Dự án

- `ai_assistant/`: Ứng dụng Trợ lý Generative AI trên Streamlit (`app.py`, `ai_core.py`, `text_to_sql.py`) tích hợp Google Gemini API.
- `powerbi/`: Báo cáo Power BI hợp nhất `F1_Analytics_Final.pbix` (4 trang: Overview, Performance Dynamics, Circuit Outcomes, ETL Monitoring + Drill-through Circuit Profile).
- `dbt/`: Mã nguồn dbt Core chuyển đổi dữ liệu thành Kimball Star Schema (13 models, 48 data tests).
- `mage/`: Pipeline Mage.ai 5 block, cấu hình Schedule Trigger dạng mã nguồn (`triggers.yaml`), CLI `run_etl.py` và script thu thập bằng chứng vận hành.
- `sqlserver/`: DDL tạo schema `stg`, `ctl`, `dw`, tối ưu Columnstore Index và script tạo view giám sát cùng tài khoản chỉ đọc `f1_ai_reader` (`sqlserver/ctl/01_etl_monitoring_view_and_reader.sql`).
- `tests/`: Bộ kiểm thử tự động cho ETL, mapping, lập lịch Mage, phân hệ AI (`test_ai_assistant_truc.py`) và kiểm định QA/bảo mật Phase 4 (`test_phase4_qa.py`).
- `dataset/`: 7 file CSV dữ liệu F1 cốt lõi từ Kaggle (1950–2026, 27.568 bản ghi kết quả).
- `docs/`: Hồ sơ kiến trúc, từ điển dữ liệu, runbook vận hành, kịch bản demo và bằng chứng kiểm thử (`docs/evidence/`).
- `plans/`: Kế hoạch thực hiện chi tiết theo từng giai đoạn (Phase 1–4).
- `report.pdf`: Báo cáo đồ án tổng hợp đầy đủ của Nhóm 7.

---

## 🚀 Hướng dẫn Cài đặt & Chạy Hệ thống

### 1. Xem Báo cáo & Dashboard Power BI
- Mở Power BI Desktop và mở tệp hợp nhất:
  ```text
  powerbi/F1_Analytics_Final.pbix
  ```
- Bao gồm 3 trang phân tích nghiệp vụ F1 (BQ1–BQ6), trang Drill-through **Circuit Profile** và **Trang 4 – Giám sát vận hành ETL** đọc từ `ctl.vw_etl_run_monitoring`.

### 2. Thiết lập SQL Server, View Giám sát & Tài khoản Chỉ đọc
1. Sao chép `.env.example` thành `.env` và điền thông tin kết nối SQL Server (`MSSQL_HOST`, `MSSQL_PORT`, `MSSQL_DATABASE`, `MSSQL_USERNAME`, `MSSQL_PASSWORD`).
   > **Lưu ý bảo mật:** File `.env` đã được đưa vào `.gitignore`. Tuyệt đối không commit mật khẩu hay API key thật lên Git.
2. Chạy script khởi tạo schema `stg`, `ctl`, `dw`:
   ```powershell
   python sqlserver/run_all_ddl.py
   ```
3. Thực thi script tạo view giám sát `ctl.vw_etl_run_monitoring`, role `db_ai_reader` và tài khoản chỉ đọc `f1_ai_reader` (chỉ có quyền `SELECT` trên `dw` và `ctl`, chặn mọi quyền ghi/xóa và chặn đọc `stg`):
   ```text
   sqlserver/ctl/01_etl_monitoring_view_and_reader.sql
   ```

### 3. Vận hành & Lập lịch ETL Tự động trên Mage.ai
1. Khởi chạy Mage.ai bằng Docker Compose:
   ```powershell
   docker compose up -d mage
   ```
   Truy cập giao diện Mage tại **http://localhost:6789**.
2. Ba Schedule Trigger được quản lý dạng mã nguồn trong `mage/project/pipelines/f1_source_to_stage/triggers.yaml` (giờ UTC), kèm cơ chế tuần tự hóa (`skip_if_previous_running: true`, `pipeline_run_limit_all_triggers: 1`):
   - `f1_full_reload_every_30min` (`0,30 * * * *`): nạp full `results.csv` + `dbt build` (phục vụ demo).
   - `f1_incremental_every_30min` (`15,45 * * * *`): nạp incremental lũy đẳng `batch_2026_R15_AZE` + `dbt build` (phục vụ demo).
   - `f1_daily_production` (`@daily`): lịch vận hành chuẩn hằng ngày lúc 00:00 UTC (07:00 giờ Việt Nam).
3. Chạy thủ công toàn bộ 7 bảng kèm `dbt build` hoặc kiểm tra khô (dry-run):
   ```powershell
   docker exec -w /home/src miniprojectbi-mage-1 python run_etl.py --all --dbt-build
   python mage/run_etl.py --all --dry-run
   ```
   *(Xem hướng dẫn chi tiết bật/tắt trigger, chạy kịch bản lỗi giả lập và thu bằng chứng tại `docs/04_operations_and_guides/etl_runbook.md`.)*

### 4. Chạy Ứng dụng Trợ lý Generative AI (`ai_assistant/`)
1. Lấy **Gemini API Key miễn phí** tại [Google AI Studio](https://aistudio.google.com/apikey) và điền vào `.env` (hoặc dán trực tiếp vào ô **Gemini API Key** trong nút **Cài đặt** ngay trên giao diện web):
   ```env
   GEMINI_API_KEY=your_free_gemini_api_key
   GEMINI_MODEL=gemini-3-flash-preview
   MSSQL_AI_USERNAME=f1_ai_reader
   MSSQL_AI_PASSWORD=your_readonly_password
   ```
2. Cài thư viện và khởi động Streamlit (Python 3.11+):
   ```powershell
   pip install -r ai_assistant/requirements.txt
   streamlit run ai_assistant/app.py
   ```
3. Mở trình duyệt tại **http://localhost:8501**:
   - **Tab 1 – Tóm tắt AI & Biểu đồ:** chọn chế độ *Phân tích F1* (lọc khoảng năm `1950–2026`, đội đua, tùy chọn *Upload ảnh PBI* đối chiếu đa phương thức) hoặc *Chẩn đoán ETL* (đọc `ctl.etl_run_log`, tự gắn cờ lỗi/reject/tăng độ trễ).
   - **Tab 2 – Chatbot Hỏi–Đáp:** hỏi tiếng Việt về F1 hoặc ETL; AI tự sinh T-SQL chỉ đọc, vẽ biểu đồ tự động và đính kèm mục *Xem SQL & Bảng dữ liệu* để kiểm chứng; bảo vệ hai lớp (kiểm duyệt ứng dụng + tài khoản chỉ đọc SQL Server).

   *(Xem thêm hướng dẫn riêng tại [`ai_assistant/README.md`](ai_assistant/README.md).)*

### 5. Chạy Bộ Kiểm thử Tự động (Phase 4)
```powershell
# 1. Bộ kiểm thử đơn vị phân hệ Generative AI & Safe Text-to-SQL (32/32 PASS)
python -m pytest tests/test_ai_assistant_truc.py -v

# 2. Bộ kiểm thử ETL & cấu hình lập lịch Mage (47/47 PASS)
python -m pytest tests/test_phase4_loc_schedule.py tests/test_etl.py tests/test_phase2_mapping.py -v

# 3. Bộ kiểm định QA, bảo mật 12 mẫu tấn công & đối soát Ground Truth Phase 4 (19/19 PASS)
python -m pytest tests/test_phase4_qa.py -v
```

---

## 📊 Các Giai đoạn Thực hiện Dự án (Project Phases)

- **Phase 1 (Completed):** Khảo sát dữ liệu nguồn (17 file CSV), ánh xạ Source-to-Stage, xây dựng pipeline Mage.ai nạp vào SQL Server Staging (`stg`) kèm bảng kiểm soát (`ctl.etl_run_log`, `ctl.etl_batch_state`) và kiểm thử chất lượng dữ liệu.
- **Phase 2 (Completed):** Chuyển đổi dữ liệu bằng dbt Core (7 view `stg_clean`, 6 Dimension có Unknown Member `SK = -1`, `dw.FactRaceResult` nạp tăng dần bảo toàn 27.568 dòng và tối ưu Clustered Columnstore Index); đạt **61/61 bước dbt** (13 models, 48 tests) và **43/43 kiểm tra ngữ nghĩa**.
- **Phase 3 (Completed):** Xây dựng Power BI Semantic Model chuẩn Star Schema (6 quan hệ 1–nhiều, bộ measure DAX tập trung `_Measures`), 3 trang Dashboard chuyên sâu (Overview, Performance Dynamics, Circuit Outcomes) cùng trang Drill-through Circuit Profile; đạt **6/6 kịch bản QA Power BI**.
- **Phase 4 (Completed):** Tự động hóa vận hành ETL, tích hợp Generative AI và kiểm định toàn diện:
  - **Giám sát ETL & Phân quyền tối thiểu:** view `ctl.vw_etl_run_monitoring`, tài khoản chỉ đọc `f1_ai_reader` (`db_ai_reader`) và **Trang 4 – Giám sát ETL** trong `powerbi/F1_Analytics_Final.pbix`.
  - **Lập lịch tự động Mage.ai:** chuỗi 5 block khép kín (`Staging -> dbt build -> commit_watermark`), 3 Schedule Trigger dạng mã nguồn (`triggers.yaml`), **6/6 lần chạy tự động liên tiếp thành công** và kiểm chứng rollback bảo toàn 27.568 dòng khi gặp lỗi khóa trùng.
  - **Trợ lý Generative AI (`ai_assistant/`):** ứng dụng Streamlit 2 tab tích hợp Google Gemini API (tóm tắt F1/ETL bám sát số liệu, đối chiếu ảnh biểu đồ Power BI, Chatbot Text-to-SQL phòng thủ hai lớp, biểu đồ Altair); đạt **32/32 kiểm thử đơn vị**.
  - **Kiểm định QA & Bảo mật (`tests/test_phase4_qa.py`):** đạt **19/19 kiểm thử tự động**, chặn **12/12 mẫu tấn công SQL**, đối soát khớp 100% số liệu Ground Truth và đạt **8/8 kịch bản nghiệm thu (QA-01 đến QA-08)**.

---

