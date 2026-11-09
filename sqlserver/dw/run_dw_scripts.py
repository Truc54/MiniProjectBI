"""
Script: run_dw_scripts.py
Description: Cong cu tu dong hoa trien khai ha tang Schema dw tren SQL Server,
             seed ban ghi Unknown Member, ap dung Columnstore Index va doi soat du lieu.

Cach dung:
    python sqlserver/dw/run_dw_scripts.py            # Chay 01, 02, 03 (Setup, Seed, Indexes)
    python sqlserver/dw/run_dw_scripts.py --reconcile # Chay bo truy van doi soat stg vs dw
    python sqlserver/dw/run_dw_scripts.py --all       # Chay toan bo va doi soat
"""

import argparse
import os
import re
import sys
from pathlib import Path

# Load .env tu thu muc goc cua repo
repo_root = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(repo_root / '.env')
except ImportError:
    pass

try:
    import pyodbc
except ImportError:
    pyodbc = None


def get_connection_string():
    # Khi chay tu host, neu MSSQL_HOST la host.docker.internal thi fallback ve localhost
    host = os.environ.get('MSSQL_HOST', 'localhost')
    if host == 'host.docker.internal':
        host = 'localhost'
    port = os.environ.get('MSSQL_PORT', '1433')
    db = os.environ.get('MSSQL_DATABASE', 'F1_BI')
    user = os.environ.get('MSSQL_USERNAME', 'f1_loader')
    pwd = os.environ.get('MSSQL_PASSWORD', 'F1Loader@2026_SecurePwd!')
    driver = os.environ.get('MSSQL_ODBC_DRIVER', 'ODBC Driver 18 for SQL Server')
    encrypt = os.environ.get('MSSQL_ENCRYPT', 'yes')
    trust_cert = os.environ.get('MSSQL_TRUST_CERTIFICATE', 'yes')

    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"DATABASE={db};"
        f"UID={user};"
        f"PWD={pwd};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_cert};"
    )


def split_go_batches(sql_text: str):
    """Tach cac block lenh SQL theo tu khoa GO cua SQL Server."""
    lines = sql_text.splitlines()
    batches = []
    current_batch = []
    for line in lines:
        if re.match(r'^\s*GO\s*(?:--.*)?$', line, re.IGNORECASE):
            batch_str = '\n'.join(current_batch).strip()
            if batch_str:
                batches.append(batch_str)
            current_batch = []
        else:
            current_batch.append(line)
    batch_str = '\n'.join(current_batch).strip()
    if batch_str:
        batches.append(batch_str)
    return batches


def execute_sql_file(cursor, file_path: Path):
    print(f"\n--> Dang thuc thi: {file_path.name}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    batches = split_go_batches(content)
    for i, batch in enumerate(batches, 1):
        clean_batch = batch.strip()
        if not clean_batch or (clean_batch.startswith('--') and '\n' not in clean_batch):
            continue
        try:
            cursor.execute(clean_batch)
            while cursor.nextset():
                pass
        except Exception as e:
            # Bo qua loi canh bao khong nghiem trong
            err_msg = str(e)
            if 'Warning!' in err_msg or 'Warning' in err_msg:
                print(f"    [CANH BAO] Batch {i}: {err_msg}")
            else:
                print(f"    [THONG BAO/LOI] Batch {i} trong {file_path.name}: {err_msg}")
    print(f"    [XONG] {file_path.name} da hoan tat.")


def run_dw_setup():
    if pyodbc is None:
        print("[LOI] pyodbc chua duoc cai dat. Vui long chay: pip install pyodbc python-dotenv")
        return False

    dw_dir = Path(__file__).resolve().parent
    scripts = [
        dw_dir / '01_setup_dw_schema_and_permissions.sql',
        dw_dir / '02_seed_unknown_members.sql',
        dw_dir / '03_apply_columnstore_indexes.sql',
    ]

    conn_str = get_connection_string()
    print("================================================================")
    print("TRIEN KHAI HA TANG DATA WAREHOUSE (PHASE 2 - DUNG)")
    print(f"Database: {os.environ.get('MSSQL_DATABASE', 'F1_BI')}")
    print(f"Target: dw & stg_clean schemas | Clustered Columnstore Index")
    print("================================================================")

    try:
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
        cursor = conn.cursor()
    except Exception as e:
        print(f"[LOI KET NOI] Khong the ket noi den SQL Server: {e}")
        print("Goi y: Kiem tra SQL Server service dang chay va file .env da duoc cau hinh dung.")
        return False

    for script in scripts:
        if script.exists():
            execute_sql_file(cursor, script)
        else:
            print(f"[LOI] Khong tim thay file: {script}")

    print("\n================================================================")
    print("DANH SACH BANG TRONG SCHEMA [dw] & CHÍ MỤC COLUMNSTORE:")
    cursor.execute("""
        SELECT 
            t.name AS TableName,
            (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) AS ColumnsCount,
            ISNULL(i.type_desc, 'HEAP/NONE') AS IndexType,
            p.rows AS TotalRows
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        LEFT JOIN sys.indexes i ON t.object_id = i.object_id AND (i.type = 5 OR i.is_primary_key = 1)
        LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
        WHERE s.name = 'dw'
        ORDER BY t.name;
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"  * dw.{r.TableName:<20} | Cot: {r.ColumnsCount:<2} | Chi muc: {r.IndexType:<22} | Dong: {r.TotalRows}")
    else:
        print("  (Chua co bang nao trong schema dw)")

    conn.close()
    return True


def run_reconciliation():
    if pyodbc is None:
        print("[LOI] pyodbc chua duoc cai dat.")
        return False

    dw_dir = Path(__file__).resolve().parent
    reconcile_file = dw_dir / 'dw_reconciliation_queries.sql'

    if not reconcile_file.exists():
        print(f"[LOI] Khong tim thay file: {reconcile_file}")
        return False

    conn_str = get_connection_string()
    print("\n================================================================")
    print("CHAY BO DOI SOAT CHAT LUONG DATA WAREHOUSE (STG VS DW)")
    print("================================================================")

    try:
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=15)
        cursor = conn.cursor()
    except Exception as e:
        print(f"[LOI KET NOI] {e}")
        return False

    with open(reconcile_file, 'r', encoding='utf-8') as f:
        content = f.read()

    batches = split_go_batches(content)
    for batch in batches:
        clean_batch = batch.strip()
        if not clean_batch or clean_batch.startswith('--'):
            continue
        try:
            cursor.execute(clean_batch)
            while True:
                if cursor.description:
                    cols = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    header = " | ".join(f"{c:<24}" for c in cols)
                    print("-" * len(header))
                    print(header)
                    print("-" * len(header))
                    for r in rows:
                        print(" | ".join(f"{str(val):<24}" for val in r))
                    print()
                if not cursor.nextset():
                    break
        except Exception as e:
            print(f"[CANH BAO/THONG BAO] {e}")

    conn.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Trien khai & Doi soat Data Warehouse SQL Server (Dung - Phase 2)")
    parser.add_argument('--reconcile', action='store_true', help="Chay bo truy van doi soat stg vs dw")
    parser.add_argument('--all', action='store_true', help="Chay toan bo DDL va doi soat")
    args = parser.parse_args()

    if args.reconcile:
        run_reconciliation()
    elif args.all:
        if run_dw_setup():
            run_reconciliation()
    else:
        run_dw_setup()


if __name__ == '__main__':
    main()

