# ==============================================================================
# Script: run_demo_windows.ps1
# Muc dich: Cong cu tu dong hoa toan dien kich ban Demo Phase 2 tren Windows.
#           Nhan vien chi can bam so tuong ung de chay va xem loi thoai thuyet trinh.
# Tac gia: Nhom Do an Formula 1 BI (Phuc, Dung, Loc, Truc)
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

# Cau hinh ket noi SQL Server local
$DB_SERVER = "localhost"
$DB_NAME = "F1_BI"
$DB_USER = "f1_loader"
$DB_PWD = "F1Loader@2026_SecurePwd!"

function Run-Sql([string]$query) {
    sqlcmd -S $DB_SERVER -d $DB_NAME -U $DB_USER -P $DB_PWD -Q "SET NOCOUNT ON; $query" -C
}

function Run-SqlFile([string]$filePath) {
    if (-not (Test-Path $filePath)) {
        Write-Host "[LOI] Khong tim thay tep: $filePath" -ForegroundColor Red
        return
    }
    Get-Content $filePath -Raw -Encoding UTF8 | sqlcmd -S $DB_SERVER -d $DB_NAME -U $DB_USER -P $DB_PWD -C
}

function Run-Dbt([string]$dbtArgs) {
    $cmd = "docker run --rm -v `"${RepoRoot}/dbt:/dbt`" -w /dbt --add-host host.docker.internal:host-gateway f1-dbt-demo:latest dbt $dbtArgs --profiles-dir /dbt"
    Invoke-Expression $cmd
}

function Show-Header {
    Clear-Host
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host "       CHUONG TRINH CHAY DEMO PHASE 2: dbt & DATA WAREHOUSE (WINDOWS)        " -ForegroundColor Yellow -NoNewline
    Write-Host ""
    Write-Host "                 Formula 1 BI Analytics Project (Phuc, Dung, Loc, Truc)        " -ForegroundColor Gray
    Write-Host "==============================================================================" -ForegroundColor Cyan
}

function Show-Menu {
    Show-Header
    Write-Host "[1] " -ForegroundColor Green -NoNewline; Write-Host "Kiem tra ket noi dbt den SQL Server (dbt debug)"
    Write-Host "[2] " -ForegroundColor Green -NoNewline; Write-Host "Liet ke danh sach model phu thuoc cua Fact (dbt ls)"
    Write-Host "[3] " -ForegroundColor Green -NoNewline; Write-Host "Build toan bo Star Schema + 48 Tests (dbt build --full-refresh)"
    Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "[4] " -ForegroundColor Yellow -NoNewline; Write-Host "Kiem tra so dong thuc te tren SQL Server (6 Dims + 1 Fact)" -ForegroundColor Yellow
    Write-Host "[5] " -ForegroundColor Yellow -NoNewline; Write-Host "Kiem tra 7 Clustered Columnstore Indexes toi uu hoa (Dung)" -ForegroundColor Yellow
    Write-Host "[6] " -ForegroundColor Yellow -NoNewline; Write-Host "Truy van phan tich Top 5 tay dua vo dich nhieu nhat lich su" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "[7] " -ForegroundColor Magenta -NoNewline; Write-Host "Mo phong loi: Chen diem am (-5) & xem dbt chan bat loi FAIL"
    Write-Host "[8] " -ForegroundColor Magenta -NoNewline; Write-Host "Sua lai diem dung (10) & Nap tang dan (Incremental PASS 61)"
    Write-Host "[9] " -ForegroundColor Cyan -NoNewline; Write-Host "Chay tham dinh ngu nghia 40/40 diem (loc_semantic_validation.sql)"
    Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "[D] " -ForegroundColor White -NoNewline; Write-Host "Bat may chu xem so do Lineage web tren http://localhost:8080"
    Write-Host "[A] " -ForegroundColor White -NoNewline; Write-Host "Chay TOAN BO luong demo tu buoc 1 den buoc 9 tu dong"
    Write-Host "[Q] " -ForegroundColor Red -NoNewline; Write-Host "Thoat"
    Write-Host "==============================================================================" -ForegroundColor Cyan
}

function Prompt-Speaker([string]$speaker, [string]$scriptText) {
    Write-Host ""
    Write-Host "[Goi y loi thoai ($speaker)]:" -ForegroundColor Yellow
    Write-Host "`"$scriptText`"" -ForegroundColor Cyan
    Write-Host ""
}

# Vong lap menu chinh
do {
    Show-Menu
    $choice = Read-Host "Moi ban chon mot buoc (1-9, D, A, Q)"

    switch ($choice.ToUpper()) {
        "1" {
            Write-Host "`n>>> [BUOC 1] KIEM TRA KET NOI dbt..." -ForegroundColor Green
            Run-Dbt "debug"
            Prompt-Speaker "Truc" "Tat ca cac ket noi tu dbt den SQL Server deu thanh cong, he thong san sang de bien dich Star Schema."
            Pause
        }
        "2" {
            Write-Host "`n>>> [BUOC 2] LIET KE MODEL PHU THUOC CUA FACT..." -ForegroundColor Green
            Run-Dbt "ls --resource-type model --select +fact_race_result"
            Prompt-Speaker "Truc" "Bang su kien phu thuoc vao 6 view staging va 6 bang chieu. dbt se bien dich tuan tu tu duoi len tren."
            Pause
        }
        "3" {
            Write-Host "`n>>> [BUOC 3] BUILD STAR SCHEMA & CHAY 48 TESTS (--full-refresh)..." -ForegroundColor Green
            Run-Dbt "build --select +fact_race_result --full-refresh"
            Prompt-Speaker "Truc" "Toan bo 61 buoc gom 13 model va 48 data tests deu PASS hoan toan."
            Pause
        }
        "4" {
            Write-Host "`n>>> [BUOC 4] KIEM TRA SO DONG TREN SQL SERVER (DUNG)..." -ForegroundColor Yellow
            $q = @"
SELECT s.name + '.' + t.name AS Bang, SUM(p.rows) AS So_Dong
FROM sys.tables t 
JOIN sys.schemas s ON s.schema_id = t.schema_id 
JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1) 
WHERE s.name IN ('stg','dw') 
GROUP BY s.name, t.name ORDER BY 1;
"@
            Run-Sql $q
            Prompt-Speaker "Dung" "FactRaceResult co dung 27.568 dong khop 100% voi du lieu goc. Cac bang chieu deu co them 1 dong Unknown SK=-1 de tranh orphan keys."
            Pause
        }
        "5" {
            Write-Host "`n>>> [BUOC 5] KIEM TRA CLUSTERED COLUMNSTORE INDEXES (DUNG)..." -ForegroundColor Yellow
            $q = "SELECT OBJECT_SCHEMA_NAME(object_id) + '.' + OBJECT_NAME(object_id) AS Bang, type_desc FROM sys.indexes WHERE type_desc LIKE '%COLUMNSTORE%';"
            Run-Sql $q
            Prompt-Speaker "Dung" "Fact va 6 Dimension deu duoc ap dung Clustered Columnstore Index, giup nen du lieu va tang toc truy van BI gap nhieu lan."
            Pause
        }
        "6" {
            Write-Host "`n>>> [BUOC 6] TRUY VAN PHAN TICH TOP 5 TAY DUA (DUNG)..." -ForegroundColor Yellow
            $q = @"
SELECT TOP 5 d.full_name, SUM(CAST(f.is_win AS int)) AS So_Tran_Thang, SUM(CAST(f.is_podium AS int)) AS Podium, SUM(f.points) AS Tong_Diem 
FROM dw.FactRaceResult f 
JOIN dw.DimDriver d ON d.driver_sk = f.driver_sk 
GROUP BY d.full_name ORDER BY So_Tran_Thang DESC;
"@
            Run-Sql $q
            Prompt-Speaker "Dung" "Day la cau hoi nghiep vu tra loi ngay tren Star Schema: Lewis Hamilton dan dau voi 106 chien thang, Schumacher 91 va Verstappen 71."
            Pause
        }
        "7" {
            Write-Host "`n>>> [BUOC 7] MO PHONG DUA DU LIEU BAN (DIEM = -5) VAO STAGING..." -ForegroundColor Magenta
            Run-Sql "UPDATE stg.results SET points = -5, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1;"
            Write-Host "[INFO] Da sua resultId = 1 thanh -5 diem. Dang chay dbt build..." -ForegroundColor Yellow
            Run-Dbt "build --select +fact_race_result"
            Prompt-Speaker "Phuc" "Test assert_points_non_negative da bat duoc loi ngay lap tuc va bao FAIL 1 ERROR=1. Pipeline dung lai an toan."
            Pause
        }
        "8" {
            Write-Host "`n>>> [BUOC 8] SUA LAI DIEM DUNG (10) VA NAP TANG DAN (INCREMENTAL)..." -ForegroundColor Magenta
            Run-Sql "UPDATE stg.results SET points = 10, _ingested_at_utc = SYSUTCDATETIME() WHERE resultId = 1;"
            Write-Host "[INFO] Da sua resultId = 1 ve 10 diem. Dang chay dbt incremental build..." -ForegroundColor Yellow
            Run-Dbt "build --select +fact_race_result"
            Run-Sql "SELECT COUNT(*) AS Tong_So_Dong, COUNT(DISTINCT source_result_id) AS So_Khoa_Duy_Nhat, SUM(points) AS Tong_Diem FROM dw.FactRaceResult;"
            Prompt-Speaker "Phuc" "Sau khi sua dung, he thong ghi de dong cu (delete+insert), khong nhan doi du lieu, tong so dong van chuan xac 27.568."
            Pause
        }
        "9" {
            Write-Host "`n>>> [BUOC 9] CHAY THAM DINH NGU NGHIA 40/40 CHECKS (LOC)..." -ForegroundColor Cyan
            Run-SqlFile "sqlserver\dw\loc_semantic_validation.sql"
            Prompt-Speaker "Loc" "Toan bo 40 diem kiem dinh nghiep vu ve so chien thang, podium, thang diem ky nguyen deu dat PASS 100% tren kho that."
            Pause
        }
        "D" {
            Write-Host "`n>>> [BUOC D] DANG KHOI CHAY dbt docs serve tren cong 8080..." -ForegroundColor Green
            Write-Host "[HUONG DAN] Mo trinh duyet truy cap: http://localhost:8080" -ForegroundColor Yellow
            Write-Host "[HUONG DAN] Bam Ctrl + C de dung may chu khi muon quay lai menu chinh." -ForegroundColor Gray
            docker run --rm -p 8080:8080 -v "${RepoRoot}/dbt:/dbt" -w /dbt f1-dbt-demo:latest dbt docs serve --port 8080 --host 0.0.0.0 --no-browser
        }
        "A" {
            Write-Host "`n>>> CHAY TOAN BO LUONG DEMO TU DONG..." -ForegroundColor White
            Run-Dbt "debug"
            Run-Dbt "build --select +fact_race_result --full-refresh"
            Run-Sql "SELECT s.name + '.' + t.name AS Bang, SUM(p.rows) AS So_Dong FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1) WHERE s.name IN ('stg','dw') GROUP BY s.name, t.name ORDER BY 1;"
            Run-Sql "SELECT OBJECT_SCHEMA_NAME(object_id) + '.' + OBJECT_NAME(object_id) AS Bang, type_desc FROM sys.indexes WHERE type_desc LIKE '%COLUMNSTORE%';"
            Run-Sql "SELECT TOP 5 d.full_name, SUM(CAST(f.is_win AS int)) AS So_Tran_Thang, SUM(f.points) AS Tong_Diem FROM dw.FactRaceResult f JOIN dw.DimDriver d ON d.driver_sk = f.driver_sk GROUP BY d.full_name ORDER BY So_Tran_Thang DESC;"
            Run-SqlFile "sqlserver\dw\loc_semantic_validation.sql"
            Write-Host "`n[HOAN TAT] Da chay xong toan bo luong demo!" -ForegroundColor Green
            Pause
        }
        "Q" {
            Write-Host "`nTam biet va chuc buoi demo thanh cong ruc ro!" -ForegroundColor Yellow
            break
        }
        Default {
            Write-Host "`nLua chon khong hop le. Vui long chon lai." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
} while ($choice.ToUpper() -ne "Q")
