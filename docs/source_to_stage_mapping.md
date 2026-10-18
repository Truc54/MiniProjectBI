# Source-to-Stage mapping

Tên cột nguồn được giữ nguyên trong Stage để dễ đối chiếu. `\N` được chuyển thành SQL NULL; không ép NULL thành 0 hoặc chuỗi rỗng. Cột kỹ thuật về file/batch/thời điểm nạp nếu được thêm phải được ghi riêng, không ghi đè cột nguồn.

## Phạm vi nạp lõi Phase 1

| Source file | Target | Grain | Natural key | Quan hệ chính |
|---|---|---|---|---|
| `circuits.csv` | `stg.circuits` | Một dòng mỗi circuit | `circuitId` | Tham chiếu từ races |
| `drivers.csv` | `stg.drivers` | Một dòng mỗi driver | `driverId` | Tham chiếu từ results |
| `constructors.csv` | `stg.constructors` | Một dòng mỗi constructor | `constructorId` | Tham chiếu từ results |
| `status.csv` | `stg.status` | Một dòng mỗi finishing status | `statusId` | Tham chiếu từ results |
| `seasons.csv` | `stg.seasons` | Một dòng mỗi season | `year` | So khớp `races.year` |
| `races.csv` | `stg.races` | Một dòng mỗi race event | `raceId` | `circuitId` -> circuits; `year` -> seasons |
| `results.csv` | `stg.results` | Một driver result trong một race | `resultId` | raceId, driverId, constructorId, statusId |

Thứ tự nạp thuận tiện cho kiểm tra tham chiếu: circuits/drivers/constructors/status/seasons, sau đó races, cuối cùng results. Có thể nạp theo thứ tự khác nếu kiểm tra tham chiếu được thực hiện sau khi đủ dữ liệu.

## Bảng phụ trong bộ dữ liệu

Các bảng dưới đây được profile trong Phase 1, nhưng chỉ thêm vào Stage khi có phân tích cụ thể và nhóm chốt phạm vi. Khóa bên dưới là khóa ứng viên cần xác nhận bằng profiling.

| Source file | Grain | Khóa ứng viên | Coverage/ghi chú |
|---|---|---|---|
| `qualifying.csv` | Một driver trong một qualifying session/race | `qualifyId` | Q2/Q3 thường NULL nếu không vào vòng sau |
| `sprint_results.csv` | Một driver trong một sprint/race | `resultId` trong file sprint | Chỉ weekend có sprint; khác bảng `results` |
| `driver_standings.csv` | Một driver sau một race | `driverStandingsId` | Điểm/vị trí là lũy kế tới race đó |
| `constructor_standings.csv` | Một constructor sau một race | `constructorStandingsId` | Điểm/vị trí là lũy kế tới race đó |
| `constructor_results.csv` | Một constructor trong một race | `constructorResultsId` | Points đã gộp cả các tay đua của constructor |
| `lap_times.csv` | Một lap của một driver trong một race | `(raceId, driverId, lap)` | Phân tích theo lap, grain lớn hơn fact lõi; không có 2025/2026 |
| `pit_stops.csv` | Một pit stop của một driver trong một race | `(raceId, driverId, stop)` | Duration là số đo ở grain pit stop |
| `practice_results.csv` | Một driver trong một practice session/race | `(raceId, driverId, session)` | Bộ dữ liệu chỉ có phần mở rộng 2025/2026 |
| `tire_stints.csv` | Một stint lốp của một driver trong một race | `(raceId, driverId, stint)` | Bộ dữ liệu chỉ có phần mở rộng 2025/2026 |
| `weather.csv` | Một bản tóm tắt thời tiết mỗi race | `raceId` | Bộ dữ liệu chỉ có phần mở rộng 2025/2026 |

## Ánh xạ kiểu dữ liệu và quy tắc nạp

- Thành viên phụ trách staging lập kiểu SQL Server từ `dataset/SCHEMA.md` và kết quả profile; khóa/measure dạng số chỉ cast khi giá trị nguồn hợp lệ.
- Các cột URL/ref/tên/quốc tịch giữ kiểu văn bản Unicode phù hợp.
- Các trường session time, lap time và duration có định dạng không đồng nhất; phải giữ giá trị nguồn và ghi rõ chuyển đổi nếu tạo cột chuẩn hóa.
- Các trường tùy chọn vẫn cho phép NULL: race session schedule, vị trí không phân loại, thời gian/fastest lap, Q2/Q3, sprint fields.
- Kiểm tra khóa tự nhiên trùng và khóa ngoại trước khi khóa schema Stage; không tự gộp dữ liệu chỉ vì nhiều cột trông giống nhau.
