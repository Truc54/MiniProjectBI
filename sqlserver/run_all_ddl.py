"""
Script: run_all_ddl.py
Description: Cong cu tu dong hoa chay DDL SQL Server va doi soat du lieu cho F1 BI.
Tac gia: Dung (SQL Server & Staging)
Cach dung:
    python sqlserver/run_all_ddl.py            # Chay toan bo DDL tao schema & bang
    python sqlserver/run_all_ddl.py --reconcile # Chay bo truy van doi soat chat luong
"""

import argparse
import os
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pyodbc
except ImportError:
    pyodbc = None


def get_connection_string(master_db=False):
    host = os.environ.get('MSSQL_HOST', 'localhost')
    port = os.environ.get('MSSQL_PORT', '1433')
    db = 'master' if master_db else os.environ.get('MSSQL_DATABASE', 'F1_BI')
    user = os.environ.get('MSSQL_USERNAME', 'sa')
    pwd = os.environ.get('MSSQL_PASSWORD', '')
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
    print(f"--> Dang thuc thi: {file_path.name}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    batches = split_go_batches(content)
    for i, batch in enumerate(batches, 1):
        if not batch or batch.startswith('--') and '\n' not in batch:
            continue
        try:
            cursor.execute(batch)
            while cursor.nextset():
                pass
        except Exception as e:
            print(f"    [CANH BAO/LOI] Batch {i} trong {file_path.name}: {e}")
    print(f"    [XONG] {file_path.name} da chay thanh cong.")


def run_ddl():
    if pyodbc is None:
        print("[LOI] pyodbc chua duoc cai dat. Vui long cai dat: pip install pyodbc python-dotenv")
        return

    base_dir = Path(__file__).resolve().parent
    ddl_dir = base_dir / 'ddl'

    ddl_files = [
        ddl_dir / '01_create_schemas.sql',
        ddl_dir / '02_create_control_tables.sql',
        ddl_dir / '03_create_staging_tables.sql',
    ]

    conn_str = get_connection_string()
    print("================================================================")
    print("KHOI CHAY DDL SQL SERVER CHO F1_BI (DUNG - SQL SERVER & STAGING)")
    print(f"Target Database: {os.environ.get('MSSQL_DATABASE', 'F1_BI')}")
    print(f"Host: {os.environ.get('MSSQL_HOST', 'localhost')}:{os.environ.get('MSSQL_PORT', '1433')}")
    print("================================================================")

    try:
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
        cursor = conn.cursor()
    except Exception as e:
        print(f"[LOI KET NOI] Khong the ket noi den SQL Server: {e}")
        print("Huong dan: Kiem tra dich vu SQL Server, port 1433 va file .env (xem docs/sql_server_setup.md)")
        return

    for f in ddl_files:
        if f.exists():
            execute_sql_file(cursor, f)
        else:
            print(f"[LOI] Khong tim thay file DDL: {f}")

    print("\n================================================================")
    print("KIEM TRA CAC BANG DA TAO THANH CONG:")
    cursor.execute("""
        SELECT s.name AS schema_name, t.name AS table_name,
               (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) AS col_count
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name IN ('stg', 'ctl')
        ORDER BY s.name, t.name;
    """)
    rows = cursor.fetchall()
    for r in rows:
        print(f"  * {r.schema_name}.{r.table_name:<16} - {r.col_count} cot")

    conn.close()
    print("\n>>> TOAN BO DDL DA HOAN TAT VA SAN SANG CHO MAGE (LOC) NAP DU LIEU! <<<")


def run_reconciliation():
    if pyodbc is None:
        print("[LOI] pyodbc chua duoc cai dat.")
        return

    base_dir = Path(__file__).resolve().parent
    reconcile_file = base_dir / 'reconciliation_queries.sql'
    if not reconcile_file.exists():
        print(f"[LOI] Khong tim thay {reconcile_file}")
        return

    conn_str = get_connection_string()
    print("================================================================")
    print("DANG CHAY TRUY VAN DOI SOAT DU LIEU (RECONCILIATION QUERIES)...")
    print("================================================================")

    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
    except Exception as e:
        print(f"[LOI KET NOI] {e}")
        return

    with open(reconcile_file, 'r', encoding='utf-8') as f:
        batches = split_go_batches(f.read())

    for b in batches:
        if not b:
            continue
        try:
            cursor.execute(b)
            while True:
                if cursor.description:
                    headers = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()
                    col_widths = [max(len(h), 12) for h in headers]
                    hdr_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
                    print("-" * len(hdr_line))
                    print(hdr_line)
                    print("-" * len(hdr_line))
                    for r in rows:
                        print(" | ".join(str(val).ljust(w) for val, w in zip(r, col_widths)))
                    print("-" * len(hdr_line))
                if not cursor.nextset():
                    break
        except Exception as e:
            print(f"[LOI DOI SOAT] {e}")

    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chay DDL va kiem tra SQL Server cho F1 BI")
    parser.add_argument('--reconcile', action='store_true', help="Chay truy van doi soat chat luong")
    args = parser.parse_args()

    if args.reconcile:
        run_reconciliation()
    else:
        run_ddl()
