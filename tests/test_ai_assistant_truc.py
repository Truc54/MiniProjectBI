"""Unit and security verification suite for Trực's Phase 4 AI Assistant.

Tests cover:
1. SQL Guardrail (`validate_readonly_sql`): 15+ injection/write/bypass payloads blocked,
   valid T-SQL queries (including CTEs, dw.*, ctl.*) allowed.
2. Pre-LLM destructive user intent detection (`detect_unsafe_intent`).
3. Grounded F1 & ETL context builders (`get_f1_summary_data`, `get_etl_summary_data`)
   verified against a deterministic SQLite replica with `dw` and `ctl` attached schemas.
4. End-to-end mocked Gemini flows (`generate_f1_summary`, `generate_etl_summary`,
   `ask_question` including 1-retry syntax self-correction, blocked & out-of-scope handling).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text

from ai_assistant.ai_core import (
    generate_etl_summary,
    generate_f1_summary,
    get_etl_summary_data,
    get_f1_summary_data,
)
from ai_assistant.text_to_sql import (
    ask_question,
    detect_unsafe_intent,
    validate_readonly_sql,
)


def _create_mock_f1_engine():
    """Create an in-memory SQLite DB with attached `dw` and `ctl` schemas."""
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("ATTACH DATABASE ':memory:' AS dw"))
        conn.execute(text("ATTACH DATABASE ':memory:' AS ctl"))

        conn.execute(
            text("""
                CREATE TABLE dw.DimRace (
                    race_sk INTEGER PRIMARY KEY,
                    season_year INTEGER,
                    round_number INTEGER,
                    race_name TEXT
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE dw.DimDriver (
                    driver_sk INTEGER PRIMARY KEY,
                    full_name TEXT,
                    driver_nationality TEXT
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE dw.DimConstructor (
                    constructor_sk INTEGER PRIMARY KEY,
                    constructor_name TEXT,
                    constructor_nationality TEXT
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE dw.DimCircuit (
                    circuit_sk INTEGER PRIMARY KEY,
                    circuit_name TEXT,
                    country TEXT
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE dw.DimStatus (
                    status_sk INTEGER PRIMARY KEY,
                    status_label TEXT,
                    outcome_group TEXT,
                    outcome_category TEXT
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE dw.FactRaceResult (
                    source_result_id INTEGER PRIMARY KEY,
                    race_sk INTEGER,
                    driver_sk INTEGER,
                    constructor_sk INTEGER,
                    circuit_sk INTEGER,
                    status_sk INTEGER,
                    points REAL,
                    grid_position INTEGER,
                    finish_position INTEGER,
                    position_order INTEGER,
                    places_gained INTEGER
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE ctl.etl_run_log (
                    run_id TEXT PRIMARY KEY,
                    pipeline_name TEXT,
                    source_file TEXT,
                    target_schema TEXT,
                    target_table TEXT,
                    load_mode TEXT,
                    batch_key TEXT,
                    run_status TEXT,
                    started_at_utc TEXT,
                    completed_at_utc TEXT,
                    rows_read INTEGER,
                    rows_written INTEGER,
                    rows_rejected INTEGER,
                    error_message TEXT
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE ctl.etl_batch_state (
                    source_name TEXT,
                    source_table TEXT,
                    batch_key TEXT,
                    source_row_count INTEGER,
                    last_run_id TEXT,
                    loaded_at_utc TEXT,
                    batch_status TEXT
                )
            """)
        )

        # Seed F1 test rows covering 2000 & 2023 (crosses scoring era boundaries),
        # grid=0 exclusion (BQ4), and separate outcome_group values (BQ5).
        conn.execute(
            text("""
                INSERT INTO dw.DimRace VALUES
                    (1, 2023, 1, 'Bahrain Grand Prix'),
                    (2, 2023, 2, 'Saudi Arabian Grand Prix'),
                    (3, 2000, 1, 'Australian Grand Prix')
            """)
        )
        conn.execute(
            text("""
                INSERT INTO dw.DimDriver VALUES
                    (1, 'Max Verstappen', 'Dutch'),
                    (2, 'Lewis Hamilton', 'British')
            """)
        )
        conn.execute(
            text("""
                INSERT INTO dw.DimConstructor VALUES
                    (1, 'Red Bull', 'Austrian'),
                    (2, 'Mercedes', 'German')
            """)
        )
        conn.execute(
            text("""
                INSERT INTO dw.DimCircuit VALUES
                    (1, 'Bahrain International Circuit', 'Bahrain'),
                    (2, 'Jeddah Corniche Circuit', 'Saudi Arabia')
            """)
        )
        conn.execute(
            text("""
                INSERT INTO dw.DimStatus VALUES
                    (1, 'Finished', 'CLASSIFIED', 'FINISHED_OR_LAPPED'),
                    (2, 'Engine', 'RETIREMENT_DNF', 'MECHANICAL'),
                    (3, 'Did not start', 'DNS', 'DID_NOT_START'),
                    (4, 'Disqualified', 'DSQ', 'DISQUALIFIED')
            """)
        )
        conn.execute(
            text("""
                INSERT INTO dw.FactRaceResult VALUES
                    (101, 1, 1, 1, 1, 1, 25.0, 1, 1, 1, 0),
                    (102, 1, 2, 2, 1, 2, 0.0,  5, NULL, 18, NULL),
                    (103, 2, 1, 1, 2, 1, 18.0, 15, 2, 2, 13),
                    (104, 2, 2, 2, 2, 1, 10.0, 0, 5, 5, NULL),
                    (105, 3, 2, 2, 1, 3, 0.0,  0, NULL, 20, NULL),
                    (106, 3, 1, 1, 1, 4, 0.0,  3, NULL, 19, NULL)
            """)
        )

        # Seed ETL logs: 2 successful runs + 1 controlled failed run with rejected rows.
        conn.execute(
            text("""
                INSERT INTO ctl.etl_run_log VALUES
                    ('run-1', 'f1_source_to_stage', 'results.csv', 'stg', 'results', 'full',
                     'full', 'success', '2026-11-21T10:00:00', '2026-11-21T10:00:04',
                     27568, 27568, 0, NULL),
                    ('run-2', 'f1_source_to_stage', 'races.csv', 'stg', 'races', 'incremental',
                     'part2', 'success', '2026-11-21T10:15:00', '2026-11-21T10:15:01',
                     500, 500, 0, NULL),
                    ('run-3', 'f1_source_to_stage', 'status.csv', 'stg', 'status', 'full',
                     'intentional_duplicate_failure', 'failed', '2026-11-21T10:30:00',
                     '2026-11-21T10:30:01', 142, 0, 1, 'Duplicate natural key statusId=1')
            """)
        )
        conn.execute(
            text("""
                INSERT INTO ctl.etl_batch_state VALUES
                    ('results.csv', 'results', 'full', 27568, 'run-1', '2026-11-21T10:00:04', 'success'),
                    ('status.csv', 'status', 'intentional_duplicate_failure', 0, 'run-3', NULL, 'failed')
            """)
        )
    return engine


@pytest.mark.parametrize(
    "malicious_sql",
    [
        "DROP TABLE dw.FactRaceResult",
        "DELETE FROM dw.FactRaceResult WHERE source_result_id = 1",
        "UPDATE dw.FactRaceResult SET points = 0",
        "INSERT INTO ctl.etl_run_log (run_id) VALUES ('hack')",
        "TRUNCATE TABLE ctl.etl_run_log",
        "ALTER TABLE dw.DimDriver ADD hack INT",
        "SELECT * FROM dw.FactRaceResult; DROP TABLE dw.DimRace",
        "SELECT * FROM dw.FactRaceResult -- comment bypass",
        "SELECT /* comment */ * FROM dw.FactRaceResult",
        "SELECT * INTO dw.HackedTable FROM dw.FactRaceResult",
        "EXEC sp_who2",
        "SELECT * FROM stg.results",
        "SELECT * FROM sys.tables",
        "SELECT * FROM master.sys.databases",
        "SELECT * FROM INFORMATION_SCHEMA.TABLES",
        "WITH x AS (SELECT * FROM dw.FactRaceResult) DELETE FROM x",
        "SELECT * FROM unknown_schema.secret_table",
    ],
)
def test_validate_readonly_sql_blocks_all_unsafe_queries(malicious_sql):
    ok, _, reason = validate_readonly_sql(malicious_sql)
    assert not ok, f"Expected SQL to be blocked: {malicious_sql}"
    assert reason


@pytest.mark.parametrize(
    "valid_sql",
    [
        "SELECT TOP 5 full_name FROM dw.DimDriver WHERE driver_sk <> -1;",
        "```sql\nSELECT TOP 10 target_table, COUNT(*) AS runs FROM ctl.etl_run_log GROUP BY target_table\n```",
        """
        WITH ranked AS (
            SELECT dr.full_name, SUM(CAST(f.points AS FLOAT)) AS pts
            FROM dw.FactRaceResult f
            JOIN dw.DimDriver dr ON f.driver_sk = dr.driver_sk
            GROUP BY dr.full_name
        )
        SELECT TOP 5 full_name, pts FROM ranked ORDER BY pts DESC
        """,
        "SELECT TOP 20 * FROM ctl.vw_etl_run_monitoring ORDER BY started_at_utc DESC",
        "SELECT TOP 5 status_label FROM dw.DimStatus WHERE status_label = 'Drop out'",
    ],
)
def test_validate_readonly_sql_allows_clean_queries(valid_sql):
    ok, cleaned, reason = validate_readonly_sql(valid_sql)
    assert ok, f"Expected valid SQL to pass, got reason: {reason}"
    assert cleaned


@pytest.mark.parametrize(
    "prompt",
    [
        "Hãy xóa hết dữ liệu trong bảng dw.FactRaceResult",
        "DROP TABLE ctl.etl_run_log ngay lập tức",
        "Cập nhật điểm của Verstappen thành 0",
        "DELETE FROM dw.DimDriver",
    ],
)
def test_detect_unsafe_intent_blocks_destructive_prompts(prompt):
    assert detect_unsafe_intent(prompt) is not None


def test_get_f1_summary_data_enforces_bq4_bq5_and_era_caveat():
    engine = _create_mock_f1_engine()
    try:
        # Full range crosses scoring era boundaries (2000 -> 2023)
        full_data = get_f1_summary_data(engine=engine)
        kpis = full_data["kpis"]
        assert kpis["total_entries"] == 6
        assert kpis["classified_entries"] == 3
        assert kpis["non_classified_entries"] == 3
        # Row 104 has grid=0 (excluded from BQ4), only rows 101 and 103 have grid>0 & finish_position IS NOT NULL
        assert kpis["eligible_grid_sample_n"] == 2
        assert kpis["excluded_grid_rows"] == 4
        assert full_data["points_era_caveat"] is True
        groups = {row["outcome_group"]: row["entries"] for row in full_data["outcome_breakdown"]}
        assert groups["DNS"] == 1
        assert groups["DSQ"] == 1
        assert groups["RETIREMENT_DNF"] == 1

        # Single season (2023) triggers per-round trend with round-over-round delta
        s2023 = get_f1_summary_data(season_start=2023, season_end=2023, engine=engine)
        assert s2023["points_era_caveat"] is False
        assert s2023["trend_granularity"] == "round"
        assert len(s2023["trend"]) == 2
        assert s2023["trend"][1]["points_delta_vs_prior_round"] == 3.0  # 28.0 - 25.0
    finally:
        engine.dispose()


def test_get_etl_summary_data_detects_failures_and_rejects():
    engine = _create_mock_f1_engine()
    try:
        etl = get_etl_summary_data(last_n=10, engine=engine)
        ws = etl["window_summary"]
        assert ws["total_runs"] == 3
        assert ws["success_runs"] == 2
        assert ws["failed_runs"] == 1
        assert ws["total_rows_written"] == 28068
        assert ws["total_rows_rejected"] == 1
        assert len(etl["failed_or_rejected_runs"]) == 1
        assert etl["failed_or_rejected_runs"][0]["target_table"] == "status"
        assert any("FAILED_RUN_DETECTED" in flag for flag in etl["anomaly_flags"])
        assert any("REJECTED_ROWS_DETECTED" in flag for flag in etl["anomaly_flags"])
    finally:
        engine.dispose()


def test_ask_question_blocks_destructive_request_without_calling_db():
    res = ask_question("Hãy xóa hết dữ liệu trong bảng dw.FactRaceResult")
    assert res["status"] == "blocked"
    assert res["blocked_reason"] is not None


def test_ask_question_executes_and_self_corrects_on_syntax_error():
    engine = _create_mock_f1_engine()
    mock_responses = iter(
        [
            # Attempt 1: intentionally invalid column name to trigger 1-retry self-correction
            {"text": "SELECT non_existent_col FROM dw.DimDriver", "model_name": "gemini-2.5-flash", "latency_ms": 12},
            # Attempt 2: corrected valid SQL
            {"text": "SELECT full_name FROM dw.DimDriver ORDER BY full_name", "model_name": "gemini-2.5-flash", "latency_ms": 15},
            # Step 3: Vietnamese grounded answer
            {"text": "Có 2 tay đua: Lewis Hamilton và Max Verstappen.", "model_name": "gemini-2.5-flash", "latency_ms": 20},
        ]
    )
    try:
        with patch("ai_assistant.text_to_sql.call_gemini", side_effect=lambda *a, **kw: next(mock_responses)):
            res = ask_question("Liệt kê các tay đua trong hệ thống", engine=engine)
        assert res["status"] == "success"
        assert res["retried"] is True
        assert res["row_count"] == 2
        assert "Max Verstappen" in res["answer"]
    finally:
        engine.dispose()


def test_ask_question_handles_out_of_scope_honestly():
    with patch(
        "ai_assistant.text_to_sql.call_gemini",
        return_value={
            "text": "OUT_OF_SCOPE: Kho dữ liệu hiện tại không có thông tin về lốp xe.",
            "model_name": "gemini-2.5-flash",
            "latency_ms": 10,
        },
    ):
        res = ask_question("Chiến thuật lốp mềm ở chặng Monaco 2023 như thế nào?")
    assert res["status"] == "out_of_scope"
    assert "lốp xe" in res["answer"]


def test_generate_summaries_pass_grounding_payload_to_gemini():
    engine = _create_mock_f1_engine()
    try:
        f1_data = get_f1_summary_data(season_start=2023, season_end=2023, engine=engine)
        etl_data = get_etl_summary_data(last_n=10, engine=engine)
        with patch(
            "ai_assistant.ai_core.call_gemini",
            return_value={"text": "### 1. Tóm tắt\nOK", "model_name": "gemini-2.5-flash", "latency_ms": 25},
        ) as mocked:
            f1_res = generate_f1_summary(f1_data, chart_image_bytes=b"\x89PNG\r\n")
            etl_res = generate_etl_summary(etl_data)
        assert f1_res["summary_markdown"].startswith("### 1.")
        assert etl_res["summary_markdown"].startswith("### 1.")
        assert mocked.call_count == 2
        # Verify multimodal image bytes were forwarded on the F1 call
        assert mocked.call_args_list[0].kwargs["image_bytes"] == b"\x89PNG\r\n"
    finally:
        engine.dispose()
