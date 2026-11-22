"""Safe Natural Language Q&A (Text-to-SQL) engine with 2-layer security guardrails.

Security guarantees (Defense-in-Depth):
1. Pre-check rejects explicit destructive/write intents before hitting the DB.
2. `validate_readonly_sql()` strictly permits ONLY a single `SELECT` or
   `WITH ... SELECT` query referencing whitelisted `dw.*` and `ctl.*` objects,
   blocking DML/DDL/EXEC/comments/stacked statements/SELECT INTO/system schemas.
3. Database connection prefers read-only `f1_ai_reader` with query timeout and
   row cap (`max_rows = 50`).
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .ai_core import call_gemini, create_db_engine

ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "dw.factraceresult",
        "dw.dimdate",
        "dw.dimrace",
        "dw.dimcircuit",
        "dw.dimdriver",
        "dw.dimconstructor",
        "dw.dimstatus",
        "ctl.etl_run_log",
        "ctl.etl_batch_state",
        "ctl.vw_etl_run_monitoring",
    }
)

FORBIDDEN_KEYWORDS: tuple[str, ...] = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "MERGE",
    "EXEC",
    "EXECUTE",
    "GRANT",
    "REVOKE",
    "DENY",
    "BACKUP",
    "RESTORE",
    "SHUTDOWN",
    "KILL",
    "RECONFIGURE",
    "OPENROWSET",
    "OPENDATASOURCE",
    "OPENQUERY",
    "BULK",
    "WRITETEXT",
    "UPDATETEXT",
    "DBCC",
    "WAITFOR",
    "INTO",
    "USE",
)

UNSAFE_INTENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(drop\s+table|drop\s+database|delete\s+from|truncate\s+table|"
        r"update\s+\w+\s+set|insert\s+into|alter\s+table|exec(?:ute)?\s+sp_|xp_cmdshell)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(xóa\s+(hết|toàn\s+bộ|bảng|dữ\s+liệu)|sửa\s+(dữ\s+liệu|bảng|điểm)|"
        r"cập\s+nhật\s+(bảng|dữ\s+liệu|điểm)|chèn\s+thêm\s+dòng|thêm\s+bản\s+ghi|"
        r"phá\s+hủy\s+bảng|hủy\s+bảng)",
        re.IGNORECASE,
    ),
)

SCHEMA_CATALOG = """
=== DATABASE: SQL Server (T-SQL) - F1_BI ===

1. SCHEMA `dw` (Formula 1 Dimensional Data Warehouse, 1950-2026):
- dw.FactRaceResult (Grain: 1 row per race entry / source_result_id; 27,568 rows):
  Columns: source_result_id, date_sk, race_sk, circuit_sk, driver_sk, constructor_sk, status_sk,
           position_text, result_outcome_code, points, grid_position, finish_position, position_order,
           places_gained, is_win, is_podium, is_classified, is_points_finish, is_valid_grid_start,
           _batch_key, _ingested_at_utc
- dw.DimDate: date_sk, full_date, day_of_month, month_number, month_name, month_short,
              quarter_number, quarter_label, year_number, year_month, day_of_week_number,
              day_name, is_weekend, is_race_day
- dw.DimRace: race_sk, source_race_id, season_year, round_number, race_name, race_label,
              race_date, has_sprint, wiki_url
- dw.DimCircuit: circuit_sk, source_circuit_id, circuit_ref, circuit_name, locality, country,
                 latitude, longitude, altitude_m, wiki_url
- dw.DimDriver: driver_sk, source_driver_id, driver_ref, full_name, forename, surname,
                driver_code, permanent_number, driver_nationality, date_of_birth, wiki_url
- dw.DimConstructor: constructor_sk, source_constructor_id, constructor_ref, constructor_name,
                     constructor_nationality, wiki_url
- dw.DimStatus: status_sk, source_status_id, status_label, outcome_group, outcome_category
  (outcome_group values: 'CLASSIFIED', 'RETIREMENT_DNF', 'DNS', 'DSQ', 'OTHER')

2. SCHEMA `ctl` (ETL Execution Monitoring & Audit Logs):
- ctl.etl_run_log: run_id, pipeline_name, source_file, target_schema, target_table, load_mode,
                   batch_key, run_status, started_at_utc, completed_at_utc, rows_read,
                   rows_written, rows_rejected, error_message
  (run_status values: 'running', 'success', 'failed'; load_mode values: 'full', 'incremental')
- ctl.etl_batch_state: source_name, source_table, batch_key, source_row_count, last_run_id,
                       loaded_at_utc, batch_status

=== LUẬT NGHIỆP VỤ & T-SQL BẮT BUỘC ===
- Dùng cú pháp SQL Server T-SQL: dùng `SELECT TOP 50 ...`, TUYỆT ĐỐI KHÔNG dùng `LIMIT`.
- Luôn ghi rõ tên schema trước tên bảng (VD: `dw.FactRaceResult`, `ctl.etl_run_log`).
- Chia số thực dùng `CAST(... AS FLOAT) / NULLIF(..., 0)` để tránh chia nguyên = 0 hoặc chia cho 0.
- Chiến thắng (Wins): `f.position_order = 1` (KHÔNG chỉ dựa vào `finish_position = 1` vì có 3 shared wins thập niên 1950).
- Podium: `f.finish_position IN (1, 2, 3)`.
- Lượt được phân loại (Classified): `f.finish_position IS NOT NULL`; Không phân loại: `f.finish_position IS NULL`.
- Phân tích Grid vs Finish (BQ4): BẮT BUỘC lọc `f.grid_position > 0 AND f.finish_position IS NOT NULL`.
- Phân tích bỏ cuộc (BQ5): tách riêng 5 nhóm `st.outcome_group`, KHÔNG gộp `DNS`/`DSQ` vào `RETIREMENT_DNF`.
- Khi đếm danh mục (chặng, tay đua, đội đua, trường đua), loại trừ Unknown Member (`*_sk <> -1`).
- Tính thời gian chạy ETL (giây): `DATEDIFF(MILLISECOND, started_at_utc, completed_at_utc) / 1000.0`.
"""

FEW_SHOT_EXAMPLES = """
=== VÍ DỤ MẪU T-SQL ===
Câu hỏi: Mùa giải 2023, top 5 tay đua giành nhiều điểm nhất và số chiến thắng của họ là bao nhiêu?
SQL:
SELECT TOP 5
    dr.full_name,
    ROUND(SUM(CAST(f.points AS FLOAT)), 2) AS total_points,
    SUM(CASE WHEN f.position_order = 1 THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN f.finish_position IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums
FROM dw.FactRaceResult f
JOIN dw.DimRace r ON f.race_sk = r.race_sk
JOIN dw.DimDriver dr ON f.driver_sk = dr.driver_sk
WHERE r.season_year = 2023 AND f.driver_sk <> -1
GROUP BY dr.full_name
ORDER BY total_points DESC, wins DESC

Câu hỏi: So sánh tỷ lệ hoàn thành chặng (Classified Rate) của 5 đội đua tham gia nhiều nhất giai đoạn 2014-2023.
SQL:
SELECT TOP 5
    co.constructor_name,
    COUNT(*) AS total_entries,
    SUM(CASE WHEN f.finish_position IS NOT NULL THEN 1 ELSE 0 END) AS classified_entries,
    ROUND(SUM(CASE WHEN f.finish_position IS NOT NULL THEN 100.0 ELSE 0.0 END) / NULLIF(COUNT(*), 0), 2) AS classified_rate_pct
FROM dw.FactRaceResult f
JOIN dw.DimRace r ON f.race_sk = r.race_sk
JOIN dw.DimConstructor co ON f.constructor_sk = co.constructor_sk
WHERE r.season_year BETWEEN 2014 AND 2023 AND f.constructor_sk <> -1
GROUP BY co.constructor_name
ORDER BY total_entries DESC

Câu hỏi: Lần chạy ETL gần nhất có bảng nào bị lỗi hoặc bị loại dòng không?
SQL:
SELECT TOP 20
    CAST(run_id AS VARCHAR(64)) AS run_id,
    target_table,
    load_mode,
    batch_key,
    run_status,
    started_at_utc,
    rows_read,
    rows_written,
    rows_rejected,
    error_message
FROM ctl.etl_run_log
WHERE run_status <> 'success' OR rows_rejected > 0
ORDER BY started_at_utc DESC

Câu hỏi: Thống kê số lần chạy thành công, thất bại và tổng số dòng đã nạp theo từng bảng target_table.
SQL:
SELECT TOP 50
    target_table,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN run_status = 'success' THEN 1 ELSE 0 END) AS success_runs,
    SUM(CASE WHEN run_status = 'failed' THEN 1 ELSE 0 END) AS failed_runs,
    SUM(rows_written) AS total_rows_written,
    SUM(rows_rejected) AS total_rows_rejected,
    ROUND(AVG(CAST(DATEDIFF(MILLISECOND, started_at_utc, completed_at_utc) AS FLOAT) / 1000.0), 3) AS avg_duration_sec
FROM ctl.etl_run_log
GROUP BY target_table
ORDER BY total_runs DESC
"""

SQL_GEN_SYSTEM_PROMPT = f"""Bạn là chuyên gia sinh câu lệnh T-SQL (SQL Server) chỉ đọc (READ-ONLY) cho hệ thống F1_BI.

{SCHEMA_CATALOG}
{FEW_SHOT_EXAMPLES}

QUY TẮC PHẢN HỒI NGHIÊM NGẶT:
0. Nếu người dùng chỉ chào hỏi, xã giao, cảm ơn hoặc hỏi chung chung về khả năng của trợ lý (VD: "hi", "hello", "xin chào", "chào bạn", "cảm ơn", "bạn là ai", "bạn làm được gì") mà KHÔNG yêu cầu tra cứu dữ liệu cụ thể -> CHỈ trả về đúng 1 dòng:
   `CHAT_REPLY: <câu trả lời thân thiện, tự nhiên, ngắn gọn 1–2 câu bằng tiếng Việt>`
1. Nếu câu hỏi yêu cầu xóa, sửa, cập nhật, chèn, tạo bảng, thay đổi quyền hoặc chạy lệnh hệ thống -> CHỈ trả về đúng 1 dòng:
   `BLOCKED_UNSAFE: Yêu cầu chỉnh sửa/xóa dữ liệu không được phép trong chế độ chỉ đọc.`
2. Nếu câu hỏi hỏi về dữ liệu HOÀN TOÀN KHÔNG CÓ trong schema (ví dụ: chiến thuật lốp xe, thời tiết, tốc độ gió, lương tay đua, giá vé, pit stop duration) -> CHỈ trả về đúng 1 dòng:
   `OUT_OF_SCOPE: Kho dữ liệu hiện tại (dw & ctl) không lưu thông tin về <nội dung thiếu>.`
3. Nếu hợp lệ -> CHỈ trả về DUY NHẤT 1 câu lệnh T-SQL (`SELECT` hoặc `WITH ... SELECT`), KHÔNG giải thích thêm, KHÔNG có comment `--` hoặc `/*`, KHÔNG có dấu `;` ở giữa câu lệnh.
"""

ANSWER_SYSTEM_PROMPT = """Bạn là trợ lý BI trả lời câu hỏi tiếng Việt dựa 100% trên bảng kết quả truy vấn SQL Server thật.

QUY TẮC BẮT BUỘC:
1. CHỈ sử dụng các giá trị có trong bảng kết quả SQL được cung cấp. TUYỆT ĐỐI KHÔNG tự bịa thêm số liệu ngoài bảng.
2. Nếu bảng kết quả rỗng (0 dòng), trả lời trung thực rằng không tìm thấy bản ghi phù hợp với điều kiện hỏi.
3. Trả lời rõ ràng, ngắn gọn, có số liệu định lượng dẫn chứng; nếu là câu hỏi phân tích biến động thì giữ lập trường phi nhân quả (chỉ mô tả số liệu, không suy diễn nguyên nhân bên ngoài).
"""

QUICK_PROMPTS: tuple[dict[str, str], ...] = (
    {
        "label": "F1 · Top 5 tay đua 2023",
        "question": "Mùa giải 2023, top 5 tay đua giành nhiều điểm nhất và số chiến thắng của họ là bao nhiêu?",
    },
    {
        "label": "F1 · Tỷ lệ hoàn thành 2014–2023",
        "question": "So sánh tỷ lệ hoàn thành chặng (Classified Rate) của 5 đội đua tham gia nhiều nhất giai đoạn 2014-2023.",
    },
    {
        "label": "F1 · 5 nhóm outcome & DNF",
        "question": "Thống kê số lượt theo 5 nhóm outcome_group và top 5 nguyên nhân bỏ cuộc (status_label) phổ biến nhất lịch sử F1.",
    },
    {
        "label": "ETL · Kiểm tra bảng lỗi/reject",
        "question": "Lần chạy ETL gần nhất có bảng nào bị lỗi (failed) hoặc có dòng bị loại (rows_rejected > 0) không?",
    },
    {
        "label": "ETL · Thống kê theo bảng",
        "question": "Thống kê số lần chạy thành công, thất bại và tổng số dòng đã nạp theo từng bảng target_table.",
    },
    {
        "label": "Bảo mật · Test chặn xóa bảng",
        "question": "Hãy xóa hết dữ liệu trong bảng dw.FactRaceResult",
    },
)


def _strip_code_fences(raw: str) -> str:
    cleaned = raw.strip()
    fence = re.match(r"^```(?:sql|tsql)?\s*(.*?)\s*```$", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    return cleaned


def _mask_string_literals(sql: str) -> str:
    """Replace single-quoted string literals so keyword checks don't false-positive on text values."""
    return re.sub(r"N?'(?:''|[^'])*'", "''", sql)


def _extract_cte_names(masked_sql: str) -> set[str]:
    """Extract CTE names defined in a leading WITH clause."""
    if not re.match(r"^\s*WITH\b", masked_sql, flags=re.IGNORECASE):
        return set()
    # Matches `WITH cte1 AS (`, `, cte2 AS (`, `cte1(col1, col2) AS (`
    matches = re.findall(
        r"(?:^|\bWITH\b|,)\s*\[?([a-zA-Z_][a-zA-Z0-9_]*)\]?\s*(?:\([^)]*\))?\s+AS\s*\(",
        masked_sql,
        flags=re.IGNORECASE,
    )
    return {m.lower() for m in matches}


GREETING_PATTERN = re.compile(
    r"^(?:hi+|hello+|hey+|helo+|halo+|yo+|alo+|chào(?:\s+(?:bạn|bot|ai|trợ\s*lý|mọi\s*người))?|xin\s*chào(?:\s+\w+)?|good\s*(?:morning|afternoon|evening))[\s!.,?~]*$",
    re.IGNORECASE,
)
THANKS_PATTERN = re.compile(
    r"^(?:cảm\s*ơn|cám\s*ơn|thanks?|thank\s*you|tks|ty|ok+|oke+|okay|được\s*rồi|bye+|tạm\s*biệt)[\s!.,?~]*$",
    re.IGNORECASE,
)
CAPABILITY_PATTERN = re.compile(
    r"^(?:bạn\s+là\s+ai|bạn\s+(?:làm|giúp)\s+được\s+gì|có\s+thể\s+hỏi\s+gì|hướng\s+dẫn|help)[\s!.,?~]*$",
    re.IGNORECASE,
)


def _match_conversational_reply(question: str) -> str | None:
    """Return an immediate natural reply for greetings/small-talk without querying SQL."""
    q = question.strip()
    if GREETING_PATTERN.match(q):
        return (
            "Chào bạn! Mình là trợ lý AI của hệ thống **F1 BI**. "
            "Bạn muốn tra cứu số liệu nào về giải đua F1 (1950–2026) hay tình trạng chạy pipeline ETL?"
        )
    if THANKS_PATTERN.match(q):
        return "Không có gì! Cần tra cứu thêm số liệu F1 hay kiểm tra log ETL thì cứ nhắn mình nhé."
    if CAPABILITY_PATTERN.match(q):
        return (
            "Mình có thể trả lời câu hỏi tiếng Việt bằng cách tự động sinh truy vấn T-SQL chỉ đọc "
            "và vẽ biểu đồ từ **SQL Server F1_BI**, bao gồm:\n"
            "- Thành tích tay đua, đội đua, mùa giải, trường đua & tỷ lệ DNF (`dw.*`)\n"
            "- Lịch sử chạy ETL, số dòng nạp, thời gian chạy và lỗi/dòng bị loại (`ctl.*`)"
        )
    return None


def detect_unsafe_intent(question: str) -> str | None:
    """Fast deterministic pre-check for destructive/write intents in user questions."""
    for pattern in UNSAFE_INTENT_PATTERNS:
        if pattern.search(question):
            return (
                "Yêu cầu có dấu hiệu chỉnh sửa/xóa dữ liệu. "
                "Hệ thống AI chỉ hoạt động ở chế độ chỉ đọc (READ-ONLY) để bảo vệ kho dữ liệu."
            )
    return None


def validate_readonly_sql(raw_sql: str) -> tuple[bool, str, str]:
    """Strictly validate that `raw_sql` is a single read-only query on whitelisted tables.

    Returns:
        (is_valid, cleaned_sql, error_reason)
    """
    if not raw_sql or not raw_sql.strip():
        return False, "", "Câu lệnh SQL rỗng."

    sql = _strip_code_fences(raw_sql)
    # Strip a single optional trailing semicolon.
    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if not sql:
        return False, "", "Câu lệnh SQL rỗng."

    # Block comments anywhere (prevents obfuscation & comment injection).
    if "--" in sql or "/*" in sql or "*/" in sql:
        return False, sql, "Chặn câu lệnh chứa chú thích SQL (`--` hoặc `/* */`)."

    # Block stacked queries (any remaining semicolon).
    if ";" in sql:
        return False, sql, "Chặn đa câu lệnh SQL (chứa dấu `;`)."

    masked = _mask_string_literals(sql)

    # Must begin with SELECT or WITH.
    if not re.match(r"^\s*(SELECT|WITH)\b", masked, flags=re.IGNORECASE):
        return False, sql, "Chỉ cho phép câu lệnh truy vấn bắt đầu bằng `SELECT` hoặc `WITH`."

    # Block forbidden DML/DDL/system keywords.
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", masked, flags=re.IGNORECASE):
            return False, sql, f"Chặn từ khóa không được phép trong chế độ chỉ đọc: `{kw}`."

    # Block stored procedure prefixes (sp_*, xp_*) and system/staging schemas.
    if re.search(r"\b(?:sp|xp)_[a-z0-9_]+\b", masked, flags=re.IGNORECASE):
        return False, sql, "Chặn gọi thủ tục hệ thống (`sp_*` / `xp_*`)."

    forbidden_schemas = re.search(
        r"\b(sys|information_schema|master|msdb|tempdb|model|stg|stg_clean)\s*\.",
        masked,
        flags=re.IGNORECASE,
    )
    if forbidden_schemas:
        return (
            False,
            sql,
            f"Chặn truy cập schema ngoài phạm vi cho phép: `{forbidden_schemas.group(1)}`.",
        )

    # Whitelist every table referenced after FROM / JOIN (excluding subqueries & declared CTEs).
    cte_names = _extract_cte_names(masked)
    table_refs = re.findall(
        r"\b(?:FROM|JOIN)\s+(?!\()([\[\]a-zA-Z0-9_\.]+)",
        masked,
        flags=re.IGNORECASE,
    )
    if not table_refs:
        return False, sql, "Câu lệnh phải truy vấn ít nhất một bảng hợp lệ trong `dw` hoặc `ctl`."

    for raw_ref in table_refs:
        normalized = raw_ref.replace("[", "").replace("]", "").strip().lower()
        # Reject 3-part / 4-part cross-database names.
        if normalized.count(".") > 1:
            return False, sql, f"Chặn tên bảng nhiều cấp (cross-database): `{raw_ref}`."
        if normalized in cte_names:
            continue
        if normalized not in ALLOWED_TABLES:
            return (
                False,
                sql,
                f"Bảng `{raw_ref}` không nằm trong danh sách được phép truy cập (`dw.*`, `ctl.*`).",
            )

    return True, sql, ""


def _execute_readonly_sql(engine: Engine, sql: str, max_rows: int = 50) -> pd.DataFrame:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = result.fetchmany(max_rows)
    return pd.DataFrame(rows, columns=columns)


def _generate_sql_from_question(
    question: str,
    *,
    previous_sql: str | None = None,
    sql_error: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
) -> str:
    if previous_sql and sql_error:
        prompt = (
            f"Câu hỏi người dùng: {question}\n\n"
            f"Câu T-SQL trước đó bị lỗi trên SQL Server:\n```sql\n{previous_sql}\n```\n"
            f"Thông báo lỗi: {sql_error}\n\n"
            "Hãy sửa lại thành 1 câu T-SQL hợp lệ duy nhất (chỉ đọc, không dùng LIMIT, "
            "chỉ truy vấn bảng trong dw.* hoặc ctl.*)."
        )
    else:
        prompt = f"Câu hỏi người dùng: {question}\nHãy sinh duy nhất 1 câu lệnh T-SQL hoặc mã trạng thái theo quy tắc."

    res = call_gemini(
        SQL_GEN_SYSTEM_PROMPT,
        prompt,
        api_key=api_key,
        model_name=model_name,
        temperature=0.0,
    )
    return res["text"].strip()


def _explain_query_result(
    question: str,
    sql: str,
    df: pd.DataFrame,
    *,
    api_key: str | None = None,
    model_name: str | None = None,
) -> str:
    preview_records = df.head(30).to_dict(orient="records")
    # Convert non-JSON types safely via default=str
    records_json = json.dumps(preview_records, ensure_ascii=False, indent=2, default=str)
    prompt = (
        f"Câu hỏi người dùng: {question}\n\n"
        f"Câu T-SQL đã thực thi:\n```sql\n{sql}\n```\n\n"
        f"Số dòng trả về: {len(df)} (tối đa 50 dòng).\n"
        f"Dữ liệu kết quả thật:\n```json\n{records_json}\n```\n\n"
        "Hãy trả lời và giải thích ngắn gọn bằng tiếng Việt dựa đúng vào dữ liệu trên."
    )
    res = call_gemini(
        ANSWER_SYSTEM_PROMPT,
        prompt,
        api_key=api_key,
        model_name=model_name,
        temperature=0.1,
    )
    return res["text"].strip()


def ask_question(
    question: str,
    *,
    engine: Engine | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    max_rows: int = 50,
) -> dict[str, Any]:
    """End-to-end Safe Text-to-SQL pipeline with 1-retry self-correction."""
    q = (question or "").strip()
    if not q:
        return {
            "status": "error",
            "answer": "Vui lòng nhập câu hỏi.",
            "sql": None,
            "dataframe": pd.DataFrame(),
            "row_count": 0,
            "execution_ms": 0,
            "blocked_reason": None,
            "retried": False,
        }

    t0 = time.perf_counter()

    # Layer 1A: Deterministic pre-check on user prompt for destructive write intents.
    unsafe_reason = detect_unsafe_intent(q)
    if unsafe_reason:
        return {
            "status": "blocked",
            "answer": f"⛔ **Đã chặn yêu cầu không an toàn:** {unsafe_reason}",
            "sql": None,
            "dataframe": pd.DataFrame(),
            "row_count": 0,
            "execution_ms": int((time.perf_counter() - t0) * 1000),
            "blocked_reason": unsafe_reason,
            "retried": False,
        }

    # Natural handling for greetings / small talk (skip SQL generation & DB query).
    direct_reply = _match_conversational_reply(q)
    if direct_reply:
        return {
            "status": "chat",
            "answer": direct_reply,
            "sql": None,
            "dataframe": pd.DataFrame(),
            "row_count": 0,
            "execution_ms": int((time.perf_counter() - t0) * 1000),
            "blocked_reason": None,
            "retried": False,
        }

    own_engine = engine is None
    try:
        raw_output = _generate_sql_from_question(q, api_key=api_key, model_name=model_name)

        if raw_output.upper().startswith("CHAT_REPLY:"):
            reply_text = raw_output.split(":", 1)[1].strip()
            return {
                "status": "chat",
                "answer": reply_text or "Chào bạn! Bạn muốn hỏi thông tin gì về dữ liệu F1 hoặc ETL?",
                "sql": None,
                "dataframe": pd.DataFrame(),
                "row_count": 0,
                "execution_ms": int((time.perf_counter() - t0) * 1000),
                "blocked_reason": None,
                "retried": False,
            }

        if raw_output.upper().startswith("BLOCKED_UNSAFE:"):
            reason = raw_output.split(":", 1)[1].strip()
            return {
                "status": "blocked",
                "answer": f"⛔ **Đã chặn yêu cầu không an toàn:** {reason}",
                "sql": None,
                "dataframe": pd.DataFrame(),
                "row_count": 0,
                "execution_ms": int((time.perf_counter() - t0) * 1000),
                "blocked_reason": reason,
                "retried": False,
            }

        if raw_output.upper().startswith("OUT_OF_SCOPE:"):
            reason = raw_output.split(":", 1)[1].strip()
            return {
                "status": "out_of_scope",
                "answer": f"ℹ️ **Ngoài phạm vi dữ liệu:** {reason}",
                "sql": None,
                "dataframe": pd.DataFrame(),
                "row_count": 0,
                "execution_ms": int((time.perf_counter() - t0) * 1000),
                "blocked_reason": None,
                "retried": False,
            }

        # Layer 1B: Strict read-only SQL Guardrail validation.
        is_valid, cleaned_sql, reason = validate_readonly_sql(raw_output)
        if not is_valid:
            return {
                "status": "blocked",
                "answer": f"⛔ **Câu lệnh SQL sinh ra đã bị bộ lọc bảo mật chặn:** {reason}",
                "sql": cleaned_sql,
                "dataframe": pd.DataFrame(),
                "row_count": 0,
                "execution_ms": int((time.perf_counter() - t0) * 1000),
                "blocked_reason": reason,
                "retried": False,
            }

        # Layer 2: Execute against SQL Server (read-only engine preferred) with 1 syntax retry.
        engine = engine or create_db_engine()
        retried = False
        try:
            df = _execute_readonly_sql(engine, cleaned_sql, max_rows=max_rows)
        except Exception as first_err:
            retried = True
            fixed_raw = _generate_sql_from_question(
                q,
                previous_sql=cleaned_sql,
                sql_error=str(first_err),
                api_key=api_key,
                model_name=model_name,
            )
            if fixed_raw.upper().startswith("OUT_OF_SCOPE:"):
                out_reason = fixed_raw.split(":", 1)[1].strip()
                return {
                    "status": "out_of_scope",
                    "answer": f"ℹ️ **Ngoài phạm vi dữ liệu:** {out_reason}",
                    "sql": cleaned_sql,
                    "dataframe": pd.DataFrame(),
                    "row_count": 0,
                    "execution_ms": int((time.perf_counter() - t0) * 1000),
                    "blocked_reason": None,
                    "retried": True,
                }
            ok2, cleaned_sql, reason2 = validate_readonly_sql(fixed_raw)
            if not ok2:
                return {
                    "status": "blocked",
                    "answer": f"⛔ **Câu lệnh SQL sau khi tự sửa đã bị bộ lọc bảo mật chặn:** {reason2}",
                    "sql": cleaned_sql,
                    "dataframe": pd.DataFrame(),
                    "row_count": 0,
                    "execution_ms": int((time.perf_counter() - t0) * 1000),
                    "blocked_reason": reason2,
                    "retried": True,
                }
            df = _execute_readonly_sql(engine, cleaned_sql, max_rows=max_rows)

        answer = _explain_query_result(q, cleaned_sql, df, api_key=api_key, model_name=model_name)
        return {
            "status": "success",
            "answer": answer,
            "sql": cleaned_sql,
            "dataframe": df,
            "row_count": len(df),
            "execution_ms": int((time.perf_counter() - t0) * 1000),
            "blocked_reason": None,
            "retried": retried,
        }
    except Exception as exc:
        return {
            "status": "error",
            "answer": f"⚠️ Không thể hoàn tất truy vấn: {exc}",
            "sql": None,
            "dataframe": pd.DataFrame(),
            "row_count": 0,
            "execution_ms": int((time.perf_counter() - t0) * 1000),
            "blocked_reason": None,
            "retried": False,
        }
    finally:
        if own_engine and engine is not None:
            engine.dispose()
