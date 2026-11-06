# Kế hoạch Cá nhân Phase 2: Quản trị SQL Server & Tối ưu Vật lý Data Warehouse

**Thành viên:** Dũng  
**Vai trò:** Database Administrator & Physical DW Optimization Specialist  
**Điểm tải công việc:** **25 điểm**  
**Thời hạn hoàn thành:** Mốc từng phần từ 28/10 đến 04/11/2026; nghiệm thu trước 23:00 ngày 05/11/2026  
**Phối hợp với:** Trực (hỗ trợ môi trường dbt kết nối SQL Server), Phúc (chạy script đối soát nghiệm thu), Lộc (nhận danh mục seed Unknown)

---

## 1. Mục tiêu & Trách nhiệm của Dũng trong Phase 2

Trong Phase 1, Dũng đã hoàn thành xuất sắc việc khởi tạo database `F1_BI`, các bảng `stg` và bảng `ctl`.
Trong Phase 2, trách nhiệm của Dũng là đảm bảo hạ tầng SQL Server sẵn sàng tiếp nhận, lưu trữ và phục vụ phân tích hiệu năng cao từ dbt:
1. **Quản trị Schema `dw` & Phân quyền Truy cập:** Khởi tạo schema `dw`, phân định quyền đọc/ghi cho user ETL (`f1_etl_user`) và quyền chỉ đọc (read-only) cho người dùng phân tích.
2. **Khởi tạo Bản ghi Mặc định Unknown Member (`SK = -1`):** Viết script idempotent nạp dòng dữ liệu dự phòng `-1` cho toàn bộ 6 bảng Dimension nhằm triệt tiêu hoàn toàn nguy cơ vi phạm ràng buộc toàn vẹn khóa ngoại.
3. **Chiến lược Tối ưu hóa Lưu trữ & Chỉ mục (Indexing):** Áp dụng công nghệ **Clustered Columnstore Index (CCI)** trên bảng Fact `dw.FactRaceResult` và các chỉ mục B-Tree tối ưu cho Dimensions.
4. **Xây dựng Bộ Truy vấn Đối soát Dữ liệu (Reconciliation Queries):** Viết script SQL tự động đối soát số lượng dòng, checksum độ đo tổng và tính hợp lệ của khóa ngoại giữa `stg` và `dw`.
5. **Đóng góp Phần Quản trị Hạ tầng vào Báo cáo Phase 2:** Phân tích dung lượng, mức độ nén và thời gian thực thi truy vấn của kho dữ liệu.

---

## 2. Phân rã Công việc & Điểm số (25 Điểm)

| STT | Nhiệm vụ chi tiết | Điểm | Hạn chót | Tiêu chí nghiệm thu |
|:---:|---|:---:|:---:|---|
| **1** | **Khởi tạo & Cấu hình Schema `dw` trên SQL Server**<br/>Kiểm tra/tạo schema `dw`; cấp quyền `CREATE TABLE`, `CREATE VIEW`, `ALTER`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` cho tài khoản dbt trong `.env`. | **4** | 28/10 | dbt có thể kết nối và tự do tạo/ghi đè các bảng trong schema `dw` mà không gặp lỗi permission. |
| **2** | **Viết Script Seeding Bản ghi Unknown (`SK = -1`)**<br/>Soạn thảo script DDL/DML idempotent nạp bản ghi mặc định cho 6 Dimension (`DimDate`, `DimRace`, `DimCircuit`, `DimDriver`, `DimConstructor`, `DimStatus`). | **6** | 30/10 | Script chạy lặp lại không lỗi, mỗi bảng chiều có đúng 1 bản ghi `-1` với tên mô tả rõ ràng ('Unknown Driver', 'Unknown Constructor'...). |
| **3** | **Áp dụng Clustered Columnstore Index (CCI) cho Fact**<br/>Nghiên cứu và tạo script đánh Clustered Columnstore Index cho `dw.FactRaceResult` sau khi dbt hoàn thành nạp bảng; tạo B-Tree Index cho các khóa chính/khóa tự nhiên của Dimension. | **5** | 01/11 | Fact được đánh chỉ mục Columnstore thành công, giảm ít nhất 50% dung lượng đĩa và tăng tốc độ quét dữ liệu theo cột. |
| **4** | **Xây dựng Bộ Script Đối soát Dữ liệu Toàn diện**<br/>Tạo file `sqlserver/dw/dw_reconciliation_queries.sql` gồm các truy vấn đối soát: Row counts match, Measure checksum (`SUM(points)`), Orphan foreign keys check, và Unknown record distribution. | **6** | 03/11 | Script kiểm tra tự động chạy mượt mà, trả về kết quả định lượng rõ ràng phục vụ bằng chứng nghiệm thu Phase 2. |
| **5** | **Thử nghiệm Tải & Đóng góp Báo cáo Kỹ thuật**<br/>Đo đạc thời gian thực thi truy vấn phân tích trước/sau khi đánh Columnstore Index; viết phần báo cáo về thiết kế vật lý và bảo mật database. | **4** | 05/11 | Hoàn thiện phần báo cáo DBA; có số liệu đo đạc thực tế về hiệu năng lưu trữ và truy vấn. |

---

## 3. Chi tiết Kỹ thuật: Clustered Columnstore Index & Seeding Unknown

### 3.1. Script Khởi tạo Bản ghi Mặc định Unknown Member (`SK = -1`)
```sql
-- Idempotent Seed script cho dw.DimDriver
IF NOT EXISTS (SELECT 1 FROM dw.DimDriver WHERE DriverSK = -1)
BEGIN
    SET IDENTITY_INSERT dw.DimDriver ON;
    INSERT INTO dw.DimDriver (
        DriverSK, SourceDriverId, DriverRef, FullName, 
        DriverNumber, DriverCode, Nationality, DateOfBirth
    )
    VALUES (
        -1, -1, 'unknown', 'Unknown Driver', 
        NULL, 'UNK', 'Unknown', '1900-01-01'
    );
    SET IDENTITY_INSERT dw.DimDriver OFF;
END;
```

### 3.2. Cấu hình Clustered Columnstore Index (CCI) trên `dw.FactRaceResult`
Bảng Fact với hơn 27.000 dòng được lưu trữ dưới định dạng Columnar:
```sql
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE name = 'CCI_FactRaceResult' AND object_id = OBJECT_ID('dw.FactRaceResult')
)
BEGIN
    CREATE CLUSTERED COLUMNSTORE INDEX CCI_FactRaceResult 
    ON dw.FactRaceResult;
    PRINT N'Da khoi tao Clustered Columnstore Index cho dw.FactRaceResult.';
END;
```

---

## 4. Bộ Truy vấn Đối soát Nghiệm thu (`sqlserver/dw/dw_reconciliation_queries.sql`)

Dũng chịu trách nhiệm cung cấp 4 câu truy vấn chuẩn mực:
1. **Row Count Reconciliation:** Đối chiếu số dòng giữa `stg.results` và `dw.FactRaceResult` (đảm bảo độ khớp 100%).
2. **Points Checksum:** Tổng điểm đua F1 giữa Staging và Fact phải có độ lệch đúng bằng 0 (`Stage_Total_Points - DW_Total_Points = 0`).
3. **Orphan Foreign Key Check:** Truy vấn kiểm tra Fact có khóa ngoại nào trỏ ra ngoài Dimension hay không (kết quả bắt buộc bằng 0).
4. **Unknown Member Distribution:** Đo lường tỷ lệ các bản ghi Fact phải gắn với chiều Unknown (`SK = -1`), đảm bảo ngưỡng an toàn < 0.1%.

---

## 5. Các Giao diện Phối hợp & Bàn giao

- **Bàn giao cho Trực:** Cấp quyền đầy đủ trên schema `dw`, cung cấp tài liệu về thứ tự thực thi (dbt run xong -> Dũng áp dụng CCI nếu dbt không tự tạo index).
- **Bàn giao cho Phúc:** Bộ script đối soát dữ liệu hoàn chỉnh để Phúc sử dụng khi nghiệm thu chất lượng end-to-end.
- **Bàn giao cho Lộc:** Cung cấp thông số vật lý (tổng dung lượng, kích thước nén của Columnstore) để Lộc đưa vào tài liệu từ điển dữ liệu.

