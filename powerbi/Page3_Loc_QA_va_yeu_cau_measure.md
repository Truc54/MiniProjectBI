# Trang 3 (Lộc) – Bảng kiểm thử BQ4/BQ5 & phiếu yêu cầu gửi Trực

## 1. Truy vấn đối soát (gửi Phúc) – chạy trên SQL Server schema `dw`

```sql
-- BQ4: cỡ mẫu hợp lệ n  ↔  card "Cỡ mẫu Grid hợp lệ (n)"
SELECT COUNT(*) AS eligible_n
FROM dw.FactRaceResult
WHERE grid_position > 0 AND finish_position IS NOT NULL;

-- BQ4: số bản ghi bị loại trừ  ↔  bảng "Cơ cấu mẫu BQ4" (tổng các dòng khác True/True)
SELECT
    CASE WHEN grid_position > 0 THEN 'True' ELSE 'False' END       AS grid_gt_0,
    CASE WHEN finish_position IS NOT NULL THEN 'True' ELSE 'False' END AS co_vi_tri_ve_dich,
    COUNT(*) AS so_luot
FROM dw.FactRaceResult
GROUP BY CASE WHEN grid_position > 0 THEN 'True' ELSE 'False' END,
         CASE WHEN finish_position IS NOT NULL THEN 'True' ELSE 'False' END;

-- BQ4: vị trí về đích TB & số bậc tăng/giảm TB theo Grid  ↔  2 biểu đồ BQ4
SELECT grid_position,
       AVG(CAST(finish_position AS float)) AS mean_finish,
       AVG(CAST(places_gained  AS float)) AS avg_places_gained,
       COUNT(*) AS n
FROM dw.FactRaceResult
WHERE grid_position > 0 AND finish_position IS NOT NULL
GROUP BY grid_position ORDER BY grid_position;

-- BQ5: tỷ lệ không phân loại toàn bộ  ↔  card "Tỷ lệ không phân loại"
SELECT CAST(SUM(CASE WHEN finish_position IS NULL THEN 1 ELSE 0 END) AS float) / COUNT(*) AS non_classified_rate
FROM dw.FactRaceResult;

-- BQ5: cơ cấu 5 nhóm outcome  ↔  biểu đồ cột 100% / donut
SELECT s.outcome_group, COUNT(*) AS so_luot
FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk
GROUP BY s.outcome_group ORDER BY so_luot DESC;

-- BQ5: top nguyên nhân không phân loại  ↔  biểu đồ "Nguyên nhân KPL phổ biến"
SELECT TOP 10 s.status_label, COUNT(*) AS so_luot
FROM dw.FactRaceResult f JOIN dw.DimStatus s ON s.status_sk = f.status_sk
WHERE s.outcome_group <> 'CLASSIFIED'
GROUP BY s.status_label ORDER BY so_luot DESC;

-- Kiểm tra nhất quán với Trang 1: Classified Rate + Non Classified Rate = 100%
SELECT CAST(SUM(CASE WHEN finish_position IS NOT NULL THEN 1 ELSE 0 END) AS float) / COUNT(*) AS classified_rate
FROM dw.FactRaceResult;
```

| Chỉ số | SQL | Power BI (Trang 3) | Khớp |
|---|---|---|---|
| n hợp lệ BQ4 | | | [ ] |
| Bản ghi bị loại trừ BQ4 | | | [ ] |
| Non Classified Rate | | | [ ] |
| Số lượt RETIREMENT_DNF / DNS / DSQ / OTHER | | | [ ] |

## 2. Phiếu yêu cầu gửi Trực (theo mục 5.4)

Trang 3 **không** tạo measure cục bộ. Các chỉ số phụ đang dùng *tổng hợp ngầm theo cột* ngay trên visual (Distinct count `race_sk`/`circuit_sk`, Min/Max `season_year`, Average lat/long). Định dạng % được đặt ở mức visual. Đề nghị Trực bổ sung vào `_Measures` để chuẩn hóa:

0. **LỖI measure (ưu tiên cao):** `Avg Places Gained` và `Eligible Grid Sample Size` dùng bộ lọc `'dw FactRaceResult'[grid_position] > 0` trực tiếp trong CALCULATE. Bộ lọc này **ghi đè** ngữ cảnh khi đặt `grid_position` lên trục, nên mọi vị trí Grid đều cho cùng một giá trị (giá trị trung bình toàn bộ, khoảng +3). Đề nghị bọc điều kiện bằng `KEEPFILTERS(...)`:
   ```dax
   Avg Places Gained =
   CALCULATE(
       AVERAGE('dw FactRaceResult'[places_gained]),
       KEEPFILTERS('dw FactRaceResult'[grid_position] > 0),
       KEEPFILTERS(NOT ISBLANK('dw FactRaceResult'[finish_position]))
   )
   ```
   (Sửa tương tự cho `Eligible Grid Sample Size`.) Trong lúc chờ, Trang 3 dùng Average của cột `places_gained` cộng bộ lọc visual (Grid > 0, `is_classified` = True), cho kết quả tương đương.
1. **`Races Hosted`** = `DISTINCTCOUNT('dw FactRaceResult'[race_sk])`. Dùng cho BQ3 (số chặng theo trường đua). Mẫu số không có, nên không cần xử lý biên.
2. **`Excluded Grid Records`** = `[Total Entries] - [Eligible Grid Sample Size]`. Dùng cho BQ4 (công bố số bản ghi bị loại trừ). Trả về 0 nếu không có dòng nào.
3. **Format string**: `Non Classified Rate` → `0.0%`; `Mean Classified Finish` → `0.0`; `Avg Places Gained` → `+0.00;-0.00;0.00` (hiện đang là General number).
6. **Thẻ hiện "(Blank)" thay vì 0:** khi lọc một nhóm không có lượt nào được phân loại (ví dụ DSQ), `Classified Rate` và `Eligible Grid Sample Size` trả về BLANK. Đề nghị thêm `+ 0` vào `Classified Entries` / `Eligible Grid Sample Size` (hoặc `COALESCE(..., 0)`).
4. **Data Category**: `dw DimCircuit[country]` đang là **County**, cần sửa thành **Country/Region** (mục 7.1 checklist).
5. Quan hệ hiện có tên `AutoDetected_*`. Cần xác nhận cả 6 quan hệ đều là 1:N, lọc một chiều (Single).

## 3. Ghi chú tích hợp cho Trực
- Trang 3 có thêm **trang ẩn "Hồ sơ trường đua"** (drill-through theo `circuit_name`). Khi tích hợp, cần **sao chép nguyên trang** này (Duplicate/copy cả trang), không chỉ copy visual, để giữ cấu hình drill-through.
- Định dạng nền, viền, tiêu đề được đặt trực tiếp trên từng visual, nên vẫn giữ nguyên khi copy sang Master.

## 4. Kết quả kiểm thử 14/11 (đối chiếu dataset/*.csv ↔ Power BI trong máy ảo)

| Kịch bản | Số chuẩn (tính từ CSV) | Power BI | Khớp |
|---|---|---|---|
| Không lọc | 78 trường đua · 1.164 chặng · 27.568 lượt · 59,8% / 40,2% · n = 16.434 · tiến bậc TB +2,94 · mẫu 1.578 / 60 / 9.496 / 16.434 | như bên | ✅ |
| Quốc gia = Monaco | 1 · 72 · 1.706 · 49,2% / 50,8% · n = 839 · +3,27 · mẫu 226 / 1 / 640 / 839 | như bên | ✅ |
| Trường đua = Bahrain | 1 · 22 · 460 · 84,1% / 15,9% · n = 386 · +1,06 · Engine 15, Collision 10 | như bên | ✅ |
| Đội đua = Ferrari | 77 · 1.139 · 2.517 · 72,7% / 27,3% · n = 1.830 · +1,31 · Engine 166, Accident 96 | như bên | ✅ |
| Mùa giải = 2014–2026 | 33 · 267 · 5.435 · 84,5% / 15,5% · n = 4.533 · +1,14 · mẫu 19 / 60 / 823 / 4.533 · Italy 19, USA 16, Austria 15 · Retired 165, Collision 150, Accident 85, Engine 81 · không còn nhóm OTHER | như bên | ✅ |
| Drill-through Bahrain | Sakhir · 7 m · 22 chặng · Hamilton 5, Vettel 4, Alonso 3 · Ferrari 7, Mercedes 6 · CLASSIFIED 374 (81,3%) · Sainz/Button 41,7% | như bên | ✅ |
| Drill-through Monaco (bản đã sửa, 14/11 16:00) | 1950-05-21 / 2026-06-07 · Senna 6, Hill 5, Schumacher 5 · McLaren 16, Ferrari 10, Red Bull 7 · 1.706 lượt · 50,8% · CLASSIFIED 788 (46,19%), DNF 684 (40,09%), OTHER 204 (11,96%), DNS 24 (1,41%) | như bên | ✅ |
| Nhóm kết quả = DNS | 45 · 127 · 258 · 1,2% / 98,8% · n = 3 · −3,00 · mẫu 164 / 91 / 3 · Withdrew 248, Did not start 10 · Lotus-Climax 26, BRM 17, Ferrari 14 | như bên | ✅ |
| Nhóm kết quả = DSQ | 162 lượt | 162 lượt; thẻ tỷ lệ phân loại và thẻ n hiện "(Blank)" | ⚠️ xem yêu cầu 6 bên dưới |
| Biểu đồ BQ4 mới (không lọc) | Điểm TB: Grid 1 = 11,62 · Grid 10 = 2,31 · Phân bố tiến/lùi đỉnh tại 0 (1.987), từ −27 đến +30 | như bên | ✅ |
| Drill-through Bahrain: mùa đầu / gần nhất | 2004 / 2025 | 1950 / 2026 | ❌ đã sửa (lấy ngày chặng đầu/cuối từ bảng Fact) |

Số chuẩn cho các visual mới (chưa xem trên Power BI): điểm TB theo Grid (không lọc) — Grid 1: 11,62 · Grid 2: 9,72 · Grid 5: 5,83 · Grid 10: 2,31; phân bố tiến/lùi — tiến 11.036 · giữ nguyên 1.987 · lùi 3.411 (tổng 16.434).

**Lưu ý định nghĩa (báo Phúc/Trực):** "Tỷ lệ được phân loại" 59,8% tính theo `finish_position` có giá trị (16.494 lượt), còn nhóm `CLASSIFIED` của `outcome_group` là 15.839 lượt (57,5%). Chênh lệch này đã ghi trong baseline Phase 2 (`known_discrepancies`: 679 lượt nhóm RETIREMENT nhưng vẫn có vị trí, 28 lượt nhóm CLASSIFIED nhưng không có vị trí), không phải lỗi dashboard. Mục 7.2 của kế hoạch tổng Phase 3 ghi số kỳ vọng 19.689 / 7.879 / 466.862,64, lệch với baseline 16.494 / 11.074 / 57.126,05.
