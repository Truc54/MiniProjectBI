# Kiến trúc BI Formula 1

## Phạm vi hiện tại: Phase 1

Nguồn là bản Kaggle Formula 1 World Championship 1950-2026 trong `dataset/` (17 CSV). Mage đọc các file được chốt trong phạm vi, chuẩn hoá ký hiệu NULL, kiểm tra cơ bản và nạp vào SQL Server schema `stg`. Schema `ctl` lưu trạng thái chạy, batch và số lượng dòng. Ở Phase 1 nhóm đồng thời chốt quy trình nghiệp vụ, grain, fact/dimension mục tiêu và kiểm tra dữ liệu nguồn.

Phạm vi nạp khởi đầu là bảy bảng lõi: `results`, `races`, `drivers`, `constructors`, `circuits`, `status`, `seasons`. Các bảng còn lại được thống kê và chỉ thêm vào Stage nếu có câu hỏi phân tích được nhóm duyệt.

```text
Kaggle CSV (dataset/)
        |
        v
Mage.ai: đọc -> kiểm tra -> full/incremental -> ghi log
        |                         |
        v                         v
SQL Server stg.*             SQL Server ctl.*
        |
        v
dbt staging/cleaning -> dbt dimensional models -> SQL Server dw.*
                                                   |
                                                   v
                      Power BI semantic model, dashboards, AI-assisted explanation
```

Phase 1 tập trung Source -> Staging và thiết kế mục tiêu. Phase 2 thực hiện dbt, triển khai DW và Power BI. Phase 3 hoàn thiện phần Generative AI theo yêu cầu 3.5 của đề; truy vấn ngôn ngữ tự nhiên là phần khuyến khích.

## Grain và quy trình nghiệp vụ mục tiêu

Quy trình nghiệp vụ là kết quả phân loại của một tay đua trong một chặng đua. Grain của fact lõi là một dòng trong `results.csv`, định danh bởi `resultId`. Thiết kế mục tiêu có một fact `FactRaceResult` và các chiều Date, Race, Circuit, Driver, Constructor, Status. Không gộp bảng lap, pit stop hay standings vào fact lõi vì chúng có grain khác.

Các measure cộng được gồm points, laps, số dòng kết quả và cờ win/podium. Vị trí về đích, grid, tốc độ và thời gian là số đo không cộng; cần định nghĩa bộ lọc/aggregation riêng. `position` có thể NULL cho kết quả không phân loại, nên phân tích kết quả phải kết hợp `positionText`, `positionOrder` và `status`.

## Kết nối SQL Server

Compose chạy Mage; SQL Server là dịch vụ bên ngoài Compose. Thông tin kết nối lấy từ `.env`, không lưu mật khẩu trong source. Tạo schema và bảng kiểm soát bằng các script trong `sqlserver/ddl/`. dbt dùng profile mẫu SQL Server trong `dbt/profiles.yml.example`.
