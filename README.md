# Formula 1 Analytics (1950–2026) · MiniProject BI

**Môn học:** Hệ thống thông tin phục vụ Trí tuệ Kinh doanh (BI)  
**Trường:** Đại học Khoa học Tự nhiên, ĐHQG-HCM  
**Nhóm thực hiện:** Nhóm 7  
**Giảng viên hướng dẫn:** Hồ Thị Hoàng Vy, Tiết Gia Hồng, Nguyễn Ngọc Minh Châu  

### Thành viên nhóm & Phân công:
- **Dương Viết Dũng** - 23120241: Quản trị SQL Server DW, Columnstore Indexing, Dashboard Trang 2 (BQ1, BQ2, BQ6).
- **Lê Văn Lộc** - 23120141: Mapping chuyển đổi Staging sang DW, Phân loại 141 Status, Dashboard Trang 3 (BQ3, BQ4, BQ5).
- **Trần Lê Trung Trực** - 23120180: Xây dựng dbt project, điều phối Mage AI pipeline, Semantic Model Power BI & Master Integrator.
- **Nguyễn Hồng Phúc** - 23120331: Thiết kế Kimball Star Schema, Bộ dbt tests tự động, Dashboard Trang 1 (Overview) & QA Lead.

## 🏗️ Kiến trúc Hệ thống (End-to-End BI Architecture)

```text
Kaggle CSV (dataset/)
        │
        ▼
Mage.ai Ingestion (Validation & Batch Control)
        │                                 │
        ▼                                 ▼
SQL Server: Schema [stg]          SQL Server: Schema [ctl]
        │
        ▼
dbt Core (Staging Views -> Kimball Star Schema Marts)
        │
        ▼
SQL Server: Schema [dw] (Fact Columnstore Index & 6 Dimensions)
        │
        ▼
Power BI Semantic Model & Dashboards (powerbi/)
```

---

## 📂 Cấu trúc Thư mục Dự án

- `powerbi/`: file Dashboard Power BI (`.pbix`) giải quyết trọn vẹn 6 câu hỏi nghiệp vụ (BQ1–BQ6).
- `dbt/`: Mã nguồn dbt Core chuyển đổi dữ liệu và bộ bài kiểm thử tự động (Staging views, Dim, Fact).
- `mage/`: Pipeline Mage AI tiếp nhận dữ liệu từ CSV vào SQL Server Staging (`stg`).
- `sqlserver/`: DDL tạo schema `stg`, `ctl`, `dw` và các script khởi tạo trên SQL Server.
- `dataset/`: 7 file CSV dữ liệu F1 gốc từ Kaggle (1950–2026).
- `docs/`: Toàn bộ hồ sơ kiến trúc, từ điển dữ liệu, hợp đồng QA và kịch bản demo.
- `plans/`: Lộ trình và kế hoạch phân công công việc cân bằng (25 điểm/thành viên).

---

## 🚀 Hướng dẫn Chạy & Khảo sát

### 1. Xem Báo cáo & Dashboard Power BI (Giai đoạn 2)
- Mở Power BI Desktop và mở file `dashboard.pbix` trong thư mục `powerbi/`:

### 2. Thiết lập Môi trường ETL & Data Warehouse
1. Sao chép `.env.example` thành `.env` và điền cấu hình kết nối SQL Server.
2. Khởi chạy SQL Server và thực thi script DDL: `python sqlserver/run_all_ddl.py`.
3. Khởi chạy Mage AI qua Docker Compose: `docker compose up -d mage`.
4. Chạy dbt build để xây dựng toàn bộ mô hình Star Schema trên kho `dw`:
   ```bash
   dbt build
   ```
- Xác thực nhanh dữ liệu nguồn CSV:
   ```bash
   python mage/run_etl.py --all --dry-run
   ```

---

## 📊 Các Giai đoạn Thực hiện Dự án (Project Phases)

- **Phase 1 (Completed):** Source profiling, source-to-stage mapping, Mage ingestion vào SQL Server staging (`stg`), logging (`ctl`), kiểm thử toàn vẹn dữ liệu.
- **Phase 2 (Completed):** dbt Core transformation (Staging views -> Kimball Star Schema Marts), nạp tăng dần Fact (`dw.FactRaceResult`), Clustered Columnstore Index, Unknown member (`SK = -1`), điều phối Mage DAG khép kín và 48 bài kiểm thử dữ liệu.
- **Phase 3 (Completed):** Power BI Semantic Model chuẩn Star Schema (6 1-to-Many relationships, 6 Hierarchies, bảng `_Measures` tập trung), 3 trang Dashboard chuyên sâu (Overview, Performance Dynamics, Circuit Outcomes) và Báo cáo phân tích tổng kết.
