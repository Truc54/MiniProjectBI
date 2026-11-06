# Báo cáo Phase 2: Data Transformation & Modeling

> **Phần do Lộc biên soạn** cho báo cáo kỹ thuật Phase 2 của Nhóm 7 (đồ án Formula 1 Analytics 1950–2026).
> **Tài liệu chi tiết:** [`stage_to_dw_mapping.md`](../02_data_dictionary_and_mapping/stage_to_dw_mapping.md), [`dw_data_dictionary.md`](../02_data_dictionary_and_mapping/dw_data_dictionary.md).
> **Bằng chứng:** [`loc_phase2_validation_run.md`](../evidence/loc_phase2_validation_run.md).

---

## 1. Bối cảnh

Kết thúc Phase 1, bảy bảng nguồn lõi (`circuits`, `constructors`, `drivers`, `status`, `seasons`, `races`, `results`) đã được nạp vào schema `stg` trên SQL Server, tổng cộng 30.121 dòng. Pipeline Mage kiểm soát việc nạp, và audit được ghi vào schema `ctl`. Dữ liệu `stg` giữ nguyên ngữ nghĩa của nguồn Kaggle/Ergast: tên cột camelCase, chuỗi chưa chuẩn hóa, và 141 mã trạng thái chưa được phân nhóm.

Phase 2 chuyển dữ liệu từ `stg` sang kho dữ liệu `dw` theo mô hình hình sao Kimball. Mô hình gồm một bảng sự kiện `FactRaceResult` và sáu chiều `DimDate`, `DimRace`, `DimCircuit`, `DimDriver`, `DimConstructor`, `DimStatus`. Grain của bảng sự kiện là **một dòng cho mỗi `resultId`**, tức kết quả của một tay đua tại một Grand Prix (27.568 dòng). Phần biến đổi được viết bằng dbt Core, gồm tầng staging dạng view (`stg_clean`) và tầng marts dạng bảng (`dw`).

Nhiệm vụ của phần này là đặc tả *cái gì* được biến đổi và *vì sao*, để các model dbt, các script vật lý và bộ test cùng dựa trên một hợp đồng thống nhất.

## 2. Quy tắc chuyển đổi dữ liệu

### 2.1 Nguyên tắc chung

| Nguyên tắc | Nội dung | Lý do |
|---|---|---|
| Không lọc dòng | Không model nào loại bỏ dòng nguồn. Mọi phép nối dùng `LEFT JOIN`. | Giữ đúng grain: mỗi `resultId` có đúng một dòng trong fact. |
| Chuẩn hóa chuỗi | `NULLIF(LTRIM(RTRIM(col)), '')` | Nguồn có chuỗi thừa khoảng trắng, ví dụ quốc tịch `'Argentinian '` của tay đua 861. |
| Giữ NULL | Không dùng `COALESCE` trên measure. | 11.074 dòng không được xếp hạng, nên `position` là NULL. Nếu thay NULL bằng 0, các phép AVG và đếm số lần được xếp hạng sẽ sai. |
| Đặt tên | Tiếng Anh, `snake_case`, tránh từ khóa SQL (`year → season_year`, `rank → fastest_lap_rank`). | Thống nhất giữa model, test và từ điển dữ liệu. |
| Truy vết | Giữ `_batch_key`, `_ingested_at_utc` từ Stage đến Fact. | Truy được dòng DW về batch đã nạp; `_ingested_at_utc` còn dùng cho bộ lọc incremental. |

### 2.2 Khóa thay thế xác định (deterministic surrogate key)

Khóa thay thế của mỗi chiều lấy bằng chính khóa nguồn (`driver_sk = driverId`, …). Riêng `date_sk` có dạng `YYYYMMDD`, và `-1` là bản ghi Unknown. Lý do không dùng `IDENTITY` hay `ROW_NUMBER()`: các chiều được dbt dựng lại sau mỗi lần chạy, còn bảng sự kiện nạp tăng dần (incremental). Nếu khóa thay thế đổi giá trị giữa hai lần dựng, các dòng fact cũ sẽ trỏ sai chiều. Khóa nguồn của F1 là số nguyên dương, ổn định và không bị tái sử dụng, nên cách này an toàn và đơn giản.

### 2.3 Bảng sự kiện và các cột dẫn xuất

| Cột | Công thức | Ghi chú nghiệp vụ |
|---|---|---|
| `is_win` | `position_order = 1` | Có 1.167 dòng thắng trên 1.164 chặng. Ba chặng thập niên 1950 (race 780, 784, 828) có hai người cùng thắng do chung xe (shared drive). Khi đếm số chặng thắng phải dùng `COUNT(DISTINCT race_sk)`. |
| `is_podium` | `finish_position BETWEEN 1 AND 3` | 3.513 dòng |
| `is_classified` | `finish_position IS NOT NULL` | Đây là tiêu chí xếp hạng chính thức. |
| `places_gained` | `grid_position - finish_position`, chỉ khi `grid_position > 0` và `finish_position` khác NULL | `grid = 0` nghĩa là xuất phát từ pit lane. Có 16.434 dòng hợp lệ, trung bình +2,94 bậc. |
| `result_outcome_code` | Suy ra từ `positionText` (`R`, `D`, `E`, `W`, `F`, `N`, số) | Phân loại chính thức của từng dòng, xem mục 3. |

## 3. Phân nhóm trạng thái kết thúc (`OutcomeGroup`)

141 mã trạng thái nguồn được phân vào năm nhóm phân tích:

| Nhóm | Số mã | Số dòng kết quả | Ví dụ |
|---|---:|---:|---|
| `CLASSIFIED` | 35 | 15.839 | Finished, Lapped, +1 Lap, +2 Laps… |
| `RETIREMENT_DNF` | 96 | 9.771 | Engine, Gearbox, Accident, Collision… |
| `OTHER` | 5 | 1.538 | Did not qualify, 107% Rule, Not classified… |
| `DNS` | 2 | 258 | Did not start, Withdrew |
| `DSQ` | 3 | 162 | Disqualified, Excluded, Underweight |

Nhóm `RETIREMENT_DNF` được chi tiết thêm bằng cột `outcome_category` để phân tích độ tin cậy kỹ thuật. Cột này gồm bốn giá trị: `MECHANICAL` (75 mã, 6.584 dòng), `ACCIDENT_DAMAGE` (9 mã, 2.793 dòng), `DRIVER_MEDICAL` (6 mã, 65 dòng) và `OTHER_RETIREMENT` (6 mã, 329 dòng).

Ba nguyên tắc được áp dụng:
1. **Không gộp DNS và DSQ vào DNF**, vì ba nhóm có bản chất khác nhau: không xuất phát, bị loại do vi phạm, và bỏ cuộc sau khi đã xuất phát.
2. **`OutcomeGroup` chỉ giải thích lý do kết thúc, không quyết định việc xếp hạng.** Theo luật F1, tay đua bỏ cuộc sau khi hoàn thành trên 90% cự ly vẫn được xếp hạng. Dữ liệu có 679 dòng như vậy (nhóm `RETIREMENT_DNF` nhưng có `position`). Mọi KPI về tỉ lệ được xếp hạng đều dựa vào `finish_position`.
3. **Nhãn mới không bị phân loại im lặng.** Nhãn chưa được duyệt sẽ nhận `outcome_category = 'UNREVIEWED'` và kích hoạt một test cảnh báo của dbt.

Bảng phân nhóm (CSV) và câu lệnh SQL cho `stg_status` được sinh tự động từ cùng một danh sách nhãn, nên hai bản không thể lệch nhau. Khi chạy câu SQL này trên SQL Server, kết quả khớp CSV ở cả 141/141 mã.

## 4. Quy tắc điểm số theo kỷ nguyên

Thang điểm F1 thay đổi nhiều lần trong giai đoạn 1950–2026. Bảng dưới đối chiếu quy định với dữ liệu, thông qua điểm tối đa của người thắng mỗi mùa:

| Giai đoạn | Thang điểm | Điểm tối đa của người thắng |
|---|---|---:|
| 1950–1959 | 8-6-4-3-2, +1 điểm fastest lap | 9 |
| 1960 | 8-6-4-3-2-1 | 8 |
| 1961–1990 | 9-6-4-3-2-1 | 9 |
| 1991–2002 | 10-6-4-3-2-1 | 10 |
| 2003–2009 | 10-8-6-5-4-3-2-1 | 10 |
| 2010–2018, 2025–2026 | 25-18-15-12-10-8-6-4-2-1 | 25 (riêng 2014 là 50 do chặng cuối tính điểm gấp đôi) |
| 2019–2024 | Như trên, +1 điểm fastest lap | 26 |

Cả 77/77 mùa giải trong dữ liệu đều khớp bảng trên. Các trường hợp nửa điểm (1975 Tây Ban Nha và Áo, 1984 Monaco, 1991 Úc, 2009 Malaysia, 2021 Bỉ) đều có trong dữ liệu và được giữ nguyên.

Hệ quả đối với phân tích:
- Không cộng hay so sánh trực tiếp tổng điểm giữa các kỷ nguyên. Cần dùng tỉ lệ thắng, tỉ lệ podium, hoặc điểm chuẩn hóa theo mức tối đa của mùa.
- `results.points` chỉ là điểm Grand Prix, không gồm điểm sprint. Vì vậy từ 2021, tổng điểm trong DW **không bằng** điểm vô địch chính thức.

## 5. Đánh giá chất lượng và đối soát

Lộc viết script [`loc_semantic_validation.sql`](../../sqlserver/dw/loc_semantic_validation.sql) gồm 43 kiểm tra, bổ sung cho script đối soát của Dũng. Các kiểm tra được chia thành sáu nhóm:

| Nhóm kiểm tra | Nội dung |
|---|---|
| Số dòng và tổng | Số dòng, `SUM(points)` = 57.126,05, `SUM(laps)` = 1.282.619, số dòng mỗi chiều = nguồn + 1 |
| Theo khóa | Hai chiều: không thiếu và không thừa `resultId` giữa `stg.results` và fact |
| Theo từng giá trị | So 21 cột của từng dòng fact với dòng Stage tương ứng (so sánh an toàn với NULL) |
| Cột dẫn xuất | Tính lại `is_win`, `is_podium`, `places_gained`, `result_outcome_code`… trên từng dòng |
| Ngữ nghĩa | Số mã của mỗi `OutcomeGroup`, cặp group/category hợp lệ, không còn mã `UNREVIEWED`, thang điểm kỷ nguyên |
| Unknown member | Mỗi chiều có đúng một dòng `-1`, 0 dòng fact trỏ về `-1`, khóa thay thế bằng khóa nguồn |

**Kết quả:** đặc tả được dựng thử trên SQL Server 2022 bằng một bản DW tạm theo đúng mapping. Cả **43/43 kiểm tra đều PASS**. Để chứng minh script có khả năng phát hiện lỗi, nhóm cố ý đưa vào 8 loại lỗi: lệch điểm, sai nhóm status, sai khóa ngoại, mất dòng, sai `places_gained`, trùng bản ghi Unknown, chuỗi chưa TRIM và sai thang điểm. Script phát hiện đủ **8/8** lỗi.

**Các phát hiện chất lượng dữ liệu được ghi nhận và không sửa** (để giữ đúng nguồn):
- Race 452 có 13 dòng `position` khác `positionOrder`.
- 28 dòng thuộc nhóm `CLASSIFIED` nhưng không có `position` (26 dòng bị đánh `N`, 2 dòng là lỗi nguồn ở race 71).
- 108 dòng `positionText = 'W'` (không xuất phát) mang status cơ khí hoặc tai nạn. Các dòng này được phân loại đúng nhờ `result_outcome_code`.
- 3 đường đua có độ cao `0` là giá trị giữ chỗ (placeholder).
- 14 tay đua không có quốc tịch.

## 6. Hạn chế và việc còn lại

- Kết quả 43/43 ở trên đạt được trên bản DW dựng tạm theo đặc tả. Khi các model dbt của Trực hoàn thành, cần chạy lại cùng script trên `dw` thật và cập nhật mục này.
- Nhóm cần chốt quy ước tên cột: `snake_case` theo đặc tả, hay PascalCase theo script vật lý của Dũng. Bảng đối chiếu ở mục 10 của tài liệu mapping đã sẵn sàng cho cả hai hướng.
- Điểm sprint (từ 2021) nằm ngoài grain hiện tại. Nếu cần tái tạo bảng xếp hạng vô địch chính thức, phải bổ sung một bảng sự kiện cho sprint ở giai đoạn sau.
