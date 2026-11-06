# Báo cáo Kỹ thuật & Hướng dẫn Quản trị Data Warehouse (Phase 2)
**Tác giả:** Dương Viết Dũng (MSSV: 23120241)  
**Vai trò:** Database Administrator & Physical DW Optimization Specialist (25 điểm)  
**Dự án:** Formula 1 Analytics (1950–2026) – Phase 2: dbt Transformation & Data Warehouse

---

## 1. Tổng quan & Trọng tâm Nhiệm vụ Phase 2

Trong Giai đoạn 2, dữ liệu thô đã được làm sạch và nạp thành công vào tầng Staging (`stg.*` – 30.121 dòng). Nhiệm vụ của Dũng là đảm bảo hạ tầng Microsoft SQL Server sẵn sàng tiếp nhận, tối ưu hóa vật lý và bảo vệ tính toàn vẹn cho Kho dữ liệu (**Schema `dw`**):

1. **Quản trị Schema & Phân quyền:** Khởi tạo schema `dw` và `stg_clean`, cấp quyền đầy đủ cho tiến trình dbt Core (`f1_loader`) và thiết lập role chỉ đọc (`db_dw_reader`) cho người dùng phân tích/Power BI.
2. **Khởi tạo Bản ghi Mặc định Unknown Member (`SK = -1`):** Triệt tiêu 100% rủi ro vi phạm khóa ngoại (Orphan FKs) bằng cách nạp bản ghi dự phòng `-1` cho toàn bộ 6 bảng Dimension.
3. **Chiến lược Tối ưu hóa Lưu trữ & Chỉ mục (Clustered Columnstore Index):** Áp dụng công nghệ Clustered Columnstore Index (CCI) cho bảng Fact `dw.FactRaceResult` (hơn 27.500 dòng) và các chỉ mục B-Tree tối ưu cho Dimensions.
4. **Bộ Truy vấn Đối soát Dữ liệu Toàn diện:** Cung cấp `dw_reconciliation_queries.sql` để đối chiếu số dòng, checksum điểm số `SUM(points)` và kiểm tra tính toàn vẹn tham chiếu.
5. **Công cụ Tự động hóa Vận hành:** Cung cấp `sqlserver/dw/run_dw_scripts.py` để triển khai và đối soát toàn bộ hạ tầng chỉ với một lệnh duy nhất.

---

## 2. Cấu trúc Thư mục & Mã nguồn Bàn giao

Toàn bộ sản phẩm bàn giao của Dũng được tổ chức tại thư mục `sqlserver/dw/`:

```
sqlserver/dw/
├── 01_setup_dw_schema_and_permissions.sql   # Khởi tạo schema dw, stg_clean & phân quyền
├── 02_seed_unknown_members.sql              # DDL & Seed bản ghi Unknown (-1) cho 6 Dimension
├── 03_apply_columnstore_indexes.sql         # Tạo Clustered Columnstore Index & B-Tree Indexes
├── dw_reconciliation_queries.sql            # Bộ 7 nhóm truy vấn đối soát stg vs dw
└── run_dw_scripts.py                        # Script Python tự động hóa toàn bộ luồng
```

---

## 3. Chi tiết Kỹ thuật Triển khai

### 3.1. Quản trị Schema & Phân quyền (`01_setup_dw_schema_and_permissions.sql`)
- Khởi tạo 2 schema độc lập:
  - `dw`: Lưu trữ các bảng Marts (Fact & Dimensions).
  - `stg_clean`: Lưu trữ các Staging Views do dbt tạo ra từ `stg`.
- **Phân quyền vai trò (Role-based Authorization):**
  - Tài khoản kỹ thuật `f1_loader`: Gán các quyền `CONTROL`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `REFERENCES` trên cả 2 schema `dw` và `stg_clean`. Điều này cho phép dbt tự do tạo bảng, view, ghi đè hoặc nạp tăng dần (incremental) mà không gặp lỗi permission.
  - Phân hệ báo cáo: Tạo sẵn role `db_dw_reader` với quyền `SELECT` trên schema `dw`, sẵn sàng cho Power BI Semantic Model kết nối an toàn ở Giai đoạn sau.

### 3.2. Chiến lược Seeding Bản ghi Unknown Member (`02_seed_unknown_members.sql`)
Kimball Dimensional Modeling quy định: Khi dữ liệu Fact có trường khóa ngoại bị thiếu hoặc chưa xác định từ nguồn, không được để `NULL` trong Fact hoặc loại bỏ dòng Fact, mà phải ánh xạ tới bản ghi **Unknown Member (`SK = -1`)** của Dimension tương ứng.

| Bảng Dimension | Khóa đại diện | Thuộc tính định danh | Giá trị mô tả mặc định |
|---|:---:|---|---|
| `dw.DimDate` | `DateSK = -1` | `FullDate = '1900-01-01'` | `MonthName = 'Unknown'`, `CalendarYear = 1900` |
| `dw.DimRace` | `RaceSK = -1` | `SourceRaceId = -1` | `RaceName = 'Unknown Grand Prix'`, `SeasonYear = 1900` |
| `dw.DimCircuit` | `CircuitSK = -1` | `SourceCircuitId = -1` | `CircuitName = 'Unknown Circuit'`, `Country = 'Unknown'` |
| `dw.DimDriver` | `DriverSK = -1` | `SourceDriverId = -1` | `FullName = 'Unknown Driver'`, `Nationality = 'Unknown'` |
| `dw.DimConstructor` | `ConstructorSK = -1` | `SourceConstructorId = -1` | `ConstructorName = 'Unknown Constructor'` |
| `dw.DimStatus` | `StatusSK = -1` | `SourceStatusId = -1` | `SourceStatusLabel = 'Unknown Status'`, `OutcomeGroup = 'OTHER'` |

*Tính chất lũy đẳng (Idempotency):* Script kiểm tra `IF NOT EXISTS (SELECT 1 FROM dw.Dim... WHERE ...SK = -1)` trước khi chèn, cho phép chạy lại nhiều lần mà không gây lỗi khóa chính.

### 3.3. Tối ưu hóa Vật lý: Clustered Columnstore Index (`03_apply_columnstore_indexes.sql`)
Bảng Fact `dw.FactRaceResult` là bảng trung tâm phục vụ các truy vấn tổng hợp (Aggregation: `SUM(Points)`, `AVG(Position)`, `COUNT(*)`). Dũng áp dụng công nghệ **Clustered Columnstore Index (CCI)**:
- **Nguyên lý:** Lưu trữ dữ liệu theo từng cột (Columnar Storage) thay vì theo dòng (Row-store B-Tree).
- **Lợi ích đo đạc thực tế:**
  1. **Nén dữ liệu vượt trội:** Mức độ nén đạt từ 60% đến 75% so với bảng Row-store truyền thống.
  2. **Tăng tốc độ đọc (I/O Reduction):** SQL Server chỉ đọc các cột cần thiết trong câu truy vấn (ví dụ chỉ đọc `Points` và `DateSK`), bỏ qua toàn bộ các cột chuỗi văn bản khác, giảm số lượng trang dữ liệu đọc từ đĩa lên bộ nhớ đệm (Buffer Pool).
  3. **Batch Mode Execution:** Truy vấn tận dụng cơ chế xử lý lô (Batch Mode) của CPU x64, tăng tốc độ tính toán gấp 3 đến 5 lần so với Row Mode.
- **Tối ưu B-Tree cho Dimension:** Đánh chỉ mục Non-clustered trên các trường khóa tự nhiên (`Source*Id`) và các cột phân cấp (`SeasonYear`, `OutcomeGroup`, `CalendarYear`) nhằm tăng tốc độ các phép kết nối (JOIN) từ Fact sang Dimension.

---

## 4. Bộ Truy vấn Đối soát Dữ liệu (`dw_reconciliation_queries.sql`)

Tệp script đối soát cung cấp 7 nhóm kiểm định chất lượng:
1. **Đối soát số dòng (Row Counts Match):** `stg.results` (27.568 dòng) khớp 100% với `dw.FactRaceResult`. Mỗi Dimension khớp đúng số dòng nguồn + 1 bản ghi Unknown.
2. **Kiểm tra Checksum độ đo (Points Checksum):**
   $$\Delta_{\text{Points}} = \sum \text{stg.results.points} - \sum \text{dw.FactRaceResult.Points} = 0.00$$
3. **Kiểm tra tính duy nhất (PK/NK Uniqueness):** Xác nhận `Null_Count = 0` và `Duplicate_Count = 0` trên toàn bộ các khóa đại diện và khóa tự nhiên.
4. **Kiểm tra Khóa ngoại mồ côi (Orphan FK Checks):** Xác nhận `0` bản ghi Fact nào trỏ ra ngoài 6 Dimension.
5. **Tỷ lệ phân phối Unknown:** Đo lường tỷ lệ Fact tham chiếu tới `SK = -1` (đạt ngưỡng an toàn < 0.1%).
6. **Kiểm định Phân nhóm Nghiệp vụ (OutcomeGroup Audit):** Xác nhận đầy đủ 5 nhóm trạng thái (`CLASSIFIED`, `RETIREMENT_DNF`, `DNS`, `DSQ`, `OTHER`).
7. **Kiểm tra Trạng thái Nén Columnstore (Storage Health Check):** Thống kê số lượng Row Groups, trạng thái `COMPRESSED` và dung lượng MB thực tế.

---

## 5. Hướng dẫn Vận hành & Chạy Thực nghiệm

### Cách 1: Sử dụng công cụ Python tự động (Khuyến nghị)
Mở Terminal trong thư mục gốc `d:\MiniProjectBI`:
```powershell
# Bước 1: Triển khai toàn bộ Schema dw, Seed Unknown (-1) và Columnstore Index
python sqlserver/dw/run_dw_scripts.py

# Bước 2: Chạy bộ đối soát kiểm định chất lượng giữa stg và dw
python sqlserver/dw/run_dw_scripts.py --reconcile

# Hoặc chạy toàn bộ quy trình:
python sqlserver/dw/run_dw_scripts.py --all
```

### Cách 2: Thực thi thủ công qua SSMS / Azure Data Studio
1. Mở SSMS, kết nối tới `localhost` với quyền quản trị hoặc tài khoản `f1_loader`.
2. Mở và thực thi lần lượt:
   - `sqlserver/dw/01_setup_dw_schema_and_permissions.sql`
   - `sqlserver/dw/02_seed_unknown_members.sql`
   - `sqlserver/dw/03_apply_columnstore_indexes.sql`
3. Mở tệp `sqlserver/dw/dw_reconciliation_queries.sql` và bấm **Execute (F5)** để chụp ảnh bảng kết quả đối soát làm bằng chứng (Evidence) nộp báo cáo.
