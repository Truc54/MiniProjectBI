# Hướng dẫn Thiết lập SQL Server & Kết nối Hệ thống (Phase 1)

**Tác giả:** Dũng (Phụ trách SQL Server & Staging)  
**Tài liệu tham chiếu:** [plans/02_ke_hoach_dung_sqlserver_staging.md](file:///d:/MiniProjectBI/plans/02_ke_hoach_dung_sqlserver_staging.md)  
**Áp dụng cho:** Mage ETL (Lộc), dbt (Phase 2), Power BI (Phase 2)

---

## 1. Yêu cầu môi trường & Cấu hình SQL Server

Dự án sử dụng cơ sở dữ liệu **Microsoft SQL Server** (hỗ trợ bản 2019, 2022 Developer / Standard hoặc Express).

### 1.1. Cấu hình mạng & Xác thực trên Windows Host
1. **SQL Server Management Studio (SSMS):**
   * Nhấp chuột phải vào Server Instance -> **Properties** -> **Security**.
   * Chọn **SQL Server and Windows Authentication mode** (Mixed Mode).
2. **SQL Server Configuration Manager:**
   * Vào **SQL Server Network Configuration** -> **Protocols for [INSTANCE]**.
   * Bật **TCP/IP** thành **Enabled**.
   * Nhấp đúp vào **TCP/IP** -> tab **IP Addresses** -> cuộn xuống mục **IPAll**:
     * Xóa giá trị ở **TCP Dynamic Ports** (nếu có).
     * Điền **TCP Port** là `1433`.
   * Khởi động lại dịch vụ SQL Server để thay đổi có hiệu lực.
3. **Mở Firewall Windows (cho Docker Desktop kết nối):**
   * Mở port `1433` (TCP) trong Windows Defender Firewall (Inbound Rules) để container Mage có thể truy cập qua `host.docker.internal`.

---

## 2. Cài đặt Microsoft ODBC Driver 18

### 2.1. Trên máy chủ Windows (Host)
Tải và cài đặt **ODBC Driver 18 for SQL Server**:
* Link chính thức từ Microsoft: [Download ODBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
* Driver name mặc định: `ODBC Driver 18 for SQL Server`.

### 2.2. Cho Mage Container (Linux/Debian)
File `mage/Dockerfile` đã được chuẩn bị sẵn `unixodbc` và `unixodbc-dev`. Khi container Mage cần kết nối SQL Server qua pyodbc, chuỗi kết nối sử dụng driver Microsoft tương thích với Linux (`ODBC Driver 18 for SQL Server`).

---

## 3. Cấu hình biến môi trường (`.env`)

Sao chép file mẫu `.env.example` thành `.env` tại thư mục gốc của dự án:
```bash
cp .env.example .env
```

Nội dung cấu hình chuẩn:
```env
# SQL Server connection
MSSQL_HOST=localhost
MSSQL_PORT=1433
MSSQL_DATABASE=F1_BI
MSSQL_USERNAME=f1_loader
MSSQL_PASSWORD=F1Loader@2026_SecurePwd!
MSSQL_ODBC_DRIVER=ODBC Driver 18 for SQL Server

# Luu y quan trong ve chung chi SSL/TLS:
# Voi moi truong local dev khong co SSL certificate hop le, bat Trust Certificate:
MSSQL_ENCRYPT=yes
MSSQL_TRUST_CERTIFICATE=yes

# Duong dan dataset trong Docker
F1_DATA_DIR=/home/src/dataset
```

> **Lưu ý đặc biệt cho Docker Desktop (Mage):**  
> Trong file [compose.yaml](file:///d:/MiniProjectBI/compose.yaml), biến `MSSQL_HOST` đã được ghi đè tự động thành `host.docker.internal` để container Mage có thể gọi ngược lại SQL Server đang chạy trên Windows Host.

---

## 4. Trình tự thực thi DDL khởi tạo

Chạy các file SQL trong thư mục `sqlserver/ddl/` bằng SSMS, Azure Data Studio hoặc tiện ích dòng lệnh `sqlcmd`:

### Bước 1: Khởi tạo Database và User dự án
Mở file [00_create_database_and_user.sql](file:///d:/MiniProjectBI/sqlserver/ddl/00_create_database_and_user.sql) chạy dưới tài khoản `sa` hoặc tài khoản Windows có quyền Admin:
* Tạo Database `F1_BI`.
* Tạo Login và User `f1_loader`.
* Cấp quyền thao tác đọc/ghi và DDL.

### Bước 2: Tạo các Schemas logic
Mở file [01_create_schemas.sql](file:///d:/MiniProjectBI/sqlserver/ddl/01_create_schemas.sql) chạy trên DB `F1_BI`:
* Tạo 3 schemas: `stg`, `ctl`, `dw`.

### Bước 3: Tạo các bảng kiểm soát ETL (Control Tables)
Mở file [02_create_control_tables.sql](file:///d:/MiniProjectBI/sqlserver/ddl/02_create_control_tables.sql) chạy trên DB `F1_BI`:
* Tạo bảng `ctl.etl_run_log`.
* Tạo bảng `ctl.etl_batch_state`.

### Bước 4: Tạo 7 bảng Staging lõi
Mở file [03_create_staging_tables.sql](file:///d:/MiniProjectBI/sqlserver/ddl/03_create_staging_tables.sql) chạy trên DB `F1_BI`:
* Tạo 7 bảng `stg.circuits`, `stg.constructors`, `stg.drivers`, `stg.status`, `stg.seasons`, `stg.races`, `stg.results`.
* Tạo sẵn các khóa chính (PK) và các index hỗ trợ tối ưu truy vấn.

---

## 5. Kiểm tra kết nối nhanh bằng Python script

Có thể kiểm tra kết nối từ môi trường Python máy host bằng đoạn mã ngắn sau:

```python
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

conn_str = (
    f"DRIVER={{{os.getenv('MSSQL_ODBC_DRIVER', 'ODBC Driver 18 for SQL Server')}}};"
    f"SERVER={os.getenv('MSSQL_HOST')},{os.getenv('MSSQL_PORT')};"
    f"DATABASE={os.getenv('MSSQL_DATABASE')};"
    f"UID={os.getenv('MSSQL_USERNAME')};"
    f"PWD={os.getenv('MSSQL_PASSWORD')};"
    f"Encrypt={os.getenv('MSSQL_ENCRYPT', 'yes')};"
    f"TrustServerCertificate={os.getenv('MSSQL_TRUST_CERTIFICATE', 'yes')};"
)

try:
    with pyodbc.connect(conn_str, timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION AS [Version], DB_NAME() AS [CurrentDB]")
        row = cursor.fetchone()
        print("Ket noi thanh cong den SQL Server!")
        print(f"Database: {row.CurrentDB}")
        print(f"Version: {row.Version}")
except Exception as e:
    print(f"Loi ket noi: {e}")
```
