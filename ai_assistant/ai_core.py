"""Core database grounding, F1/ETL context builders, and Gemini API client.

Design principles:
- Zero dependency on new SQL views/tables: queries existing Phase 1-2 tables
  (`dw.*`, `ctl.etl_run_log`, `ctl.etl_batch_state`) directly.
- Automatic read-only credential preference: uses `MSSQL_AI_USERNAME` /
  `MSSQL_AI_PASSWORD` when configured, falling back to `MSSQL_USERNAME` /
  `MSSQL_PASSWORD`.
- Strict anti-hallucination grounding: Gemini only explains numbers provided in
  the computed SQL JSON payload (optionally cross-checked with a chart image).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import time
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, URL

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)

DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
FALLBACK_GEMINI_MODELS = (
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
)
SCORING_ERA_BOUNDARIES = (1961, 1991, 2003, 2010, 2019)


class AIConfigError(RuntimeError):
    """Raised when required database or Gemini API settings are missing."""


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def get_gemini_api_key(override_key: str | None = None) -> str:
    key = (override_key or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key or key.upper().startswith("YOUR_") or key == "CHANGE_ME":
        raise AIConfigError(
            "Chưa cấu hình GEMINI_API_KEY. Hãy lấy API key miễn phí tại "
            "Google AI Studio (https://aistudio.google.com/apikey) rồi thêm vào "
            "file .env hoặc nhập tạm ở thanh bên trái."
        )
    return key


def get_gemini_model(override_model: str | None = None) -> str:
    return (override_model or os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL).strip()


def _resolve_db_host(raw_host: str | None) -> str:
    host = (raw_host or "").strip()
    if host.lower() == "host.docker.internal" and not Path("/.dockerenv").exists():
        return "localhost"
    return host


def get_connection_info() -> dict[str, Any]:
    """Return sanitized connection metadata (never includes passwords)."""
    ai_user = (os.environ.get("MSSQL_AI_USERNAME") or "").strip()
    ai_pass = (os.environ.get("MSSQL_AI_PASSWORD") or "").strip()
    use_ai_reader = bool(ai_user and ai_pass and ai_pass != "CHANGE_ME_READONLY")

    username = ai_user if use_ai_reader else (os.environ.get("MSSQL_USERNAME") or "").strip()
    return {
        "host": _resolve_db_host(os.environ.get("MSSQL_HOST") or "localhost") or "localhost",
        "port": int(os.environ.get("MSSQL_PORT") or 1433),
        "database": (os.environ.get("MSSQL_DATABASE") or "F1_BI").strip(),
        "username": username or "(chưa cấu hình)",
        "is_readonly_user": use_ai_reader,
        "driver": (os.environ.get("MSSQL_ODBC_DRIVER") or "ODBC Driver 18 for SQL Server").strip(),
    }


def create_db_engine(timeout_sec: int = 10) -> Engine:
    """Create a SQLAlchemy engine to SQL Server `F1_BI` preferring `f1_ai_reader`."""
    ai_user = (os.environ.get("MSSQL_AI_USERNAME") or "").strip()
    ai_pass = (os.environ.get("MSSQL_AI_PASSWORD") or "").strip()
    use_ai_reader = bool(ai_user and ai_pass and ai_pass != "CHANGE_ME_READONLY")

    username = ai_user if use_ai_reader else (os.environ.get("MSSQL_USERNAME") or "").strip()
    password = ai_pass if use_ai_reader else (os.environ.get("MSSQL_PASSWORD") or "").strip()
    host = _resolve_db_host(os.environ.get("MSSQL_HOST"))
    port = (os.environ.get("MSSQL_PORT") or "1433").strip()
    database = (os.environ.get("MSSQL_DATABASE") or "F1_BI").strip()
    driver = (os.environ.get("MSSQL_ODBC_DRIVER") or "ODBC Driver 18 for SQL Server").strip()

    missing = [
        name
        for name, val in (
            ("MSSQL_HOST", host),
            ("MSSQL_DATABASE", database),
            ("MSSQL_USERNAME / MSSQL_AI_USERNAME", username),
            ("MSSQL_PASSWORD / MSSQL_AI_PASSWORD", password),
        )
        if not val
    ]
    if missing:
        raise AIConfigError(f"Thiếu biến môi trường kết nối SQL Server trong .env: {', '.join(missing)}")

    url = URL.create(
        "mssql+pyodbc",
        username=username,
        password=password,
        host=host,
        port=int(port),
        database=database,
        query={
            "driver": driver,
            "Encrypt": os.environ.get("MSSQL_ENCRYPT", "yes"),
            "TrustServerCertificate": os.environ.get("MSSQL_TRUST_CERTIFICATE", "no"),
        },
    )
    engine = create_engine(
        url,
        future=True,
        hide_parameters=True,
        pool_pre_ping=True,
        connect_args={"timeout": timeout_sec},
    )

    @event.listens_for(engine, "connect")
    def _configure_readonly_session(dbapi_connection: Any, _connection_record: Any) -> None:
        if hasattr(dbapi_connection, "timeout"):
            try:
                dbapi_connection.timeout = timeout_sec
            except Exception:
                pass
        cursor = dbapi_connection.cursor()
        try:
            # Never hang on writer locks during concurrent Mage/dbt ETL runs.
            cursor.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
            cursor.execute("SET LOCK_TIMEOUT 3000")
            try:
                dbapi_connection.commit()
            except Exception:
                pass
        finally:
            cursor.close()

    return engine


def check_db_health(engine: Engine | None = None) -> dict[str, Any]:
    """Verify live DB reachability and return quick DW/CTL row counts."""
    own_engine = engine is None
    try:
        engine = engine or create_db_engine(timeout_sec=5)
        with engine.connect() as conn:
            fact_rows = conn.execute(text("SELECT COUNT(*) FROM dw.FactRaceResult")).scalar_one()
            etl_runs = conn.execute(text("SELECT COUNT(*) FROM ctl.etl_run_log")).scalar_one()
        return {
            "connected": True,
            "fact_rows": int(fact_rows),
            "etl_runs": int(etl_runs),
            "error": None,
        }
    except Exception as exc:
        return {
            "connected": False,
            "fact_rows": 0,
            "etl_runs": 0,
            "error": str(exc),
        }
    finally:
        if own_engine and engine is not None:
            engine.dispose()


def get_filter_options(engine: Engine | None = None) -> dict[str, Any]:
    """Load dropdown filter values from `dw` dimensions (excluding SK = -1)."""
    own_engine = engine is None
    try:
        engine = engine or create_db_engine(timeout_sec=5)
        with engine.connect() as conn:
            season_row = conn.execute(
                text(
                    "SELECT MIN(season_year), MAX(season_year) "
                    "FROM dw.DimRace WHERE race_sk <> -1 AND season_year IS NOT NULL"
                )
            ).first()
            constructors = conn.execute(
                text(
                    "SELECT DISTINCT constructor_name FROM dw.DimConstructor "
                    "WHERE constructor_sk <> -1 ORDER BY constructor_name"
                )
            ).scalars().all()
            drivers = conn.execute(
                text(
                    "SELECT DISTINCT full_name FROM dw.DimDriver "
                    "WHERE driver_sk <> -1 ORDER BY full_name"
                )
            ).scalars().all()
            circuits = conn.execute(
                text(
                    "SELECT DISTINCT circuit_name FROM dw.DimCircuit "
                    "WHERE circuit_sk <> -1 ORDER BY circuit_name"
                )
            ).scalars().all()
            etl_tables = conn.execute(
                text(
                    "SELECT DISTINCT target_table FROM ctl.etl_run_log "
                    "WHERE target_table IS NOT NULL ORDER BY target_table"
                )
            ).scalars().all()

        min_season = int(season_row[0]) if season_row and season_row[0] is not None else 1950
        max_season = int(season_row[1]) if season_row and season_row[1] is not None else 2026
        return {
            "min_season": min_season,
            "max_season": max_season,
            "constructors": list(constructors),
            "drivers": list(drivers),
            "circuits": list(circuits),
            "etl_tables": list(etl_tables),
        }
    except Exception:
        return {
            "min_season": 1950,
            "max_season": 2026,
            "constructors": [],
            "drivers": [],
            "circuits": [],
            "etl_tables": [],
        }
    finally:
        if own_engine and engine is not None:
            engine.dispose()


def _detect_scoring_era_caveat(min_year: int | None, max_year: int | None) -> tuple[bool, list[int]]:
    if min_year is None or max_year is None or min_year == max_year:
        return False, []
    crossed = [y for y in SCORING_ERA_BOUNDARIES if min_year < y <= max_year]
    return bool(crossed), crossed


def _build_f1_where(
    season_start: int | None,
    season_end: int | None,
    constructor_name: str | None,
    driver_name: str | None,
    circuit_name: str | None,
) -> tuple[str, dict[str, Any]]:
    clauses = ["1 = 1"]
    params: dict[str, Any] = {}
    if season_start is not None:
        clauses.append("r.season_year >= :season_start")
        params["season_start"] = int(season_start)
    if season_end is not None:
        clauses.append("r.season_year <= :season_end")
        params["season_end"] = int(season_end)
    if constructor_name and constructor_name != "Tất cả":
        clauses.append("co.constructor_name = :constructor_name")
        params["constructor_name"] = constructor_name
    if driver_name and driver_name != "Tất cả":
        clauses.append("dr.full_name = :driver_name")
        params["driver_name"] = driver_name
    if circuit_name and circuit_name != "Tất cả":
        clauses.append("ci.circuit_name = :circuit_name")
        params["circuit_name"] = circuit_name
    return " AND ".join(clauses), params


def _top_clause(dialect_name: str, limit: int) -> tuple[str, str]:
    if dialect_name == "mssql":
        return f"TOP ({limit}) ", ""
    return "", f" LIMIT {limit}"


def get_f1_summary_data(
    season_start: int | None = None,
    season_end: int | None = None,
    constructor_name: str | None = None,
    driver_name: str | None = None,
    circuit_name: str | None = None,
    engine: Engine | None = None,
) -> dict[str, Any]:
    """Query computed KPIs and BQ1-BQ6 breakdowns directly from `dw.*`."""
    own_engine = engine is None
    where_sql, params = _build_f1_where(
        season_start, season_end, constructor_name, driver_name, circuit_name
    )
    base_from = """
        FROM dw.FactRaceResult f
        JOIN dw.DimRace r ON f.race_sk = r.race_sk
        JOIN dw.DimDriver dr ON f.driver_sk = dr.driver_sk
        JOIN dw.DimConstructor co ON f.constructor_sk = co.constructor_sk
        JOIN dw.DimCircuit ci ON f.circuit_sk = ci.circuit_sk
        JOIN dw.DimStatus st ON f.status_sk = st.status_sk
    """

    try:
        engine = engine or create_db_engine()
        with engine.connect() as conn:
            dialect = conn.dialect.name
            top10, lim10 = _top_clause(dialect, 10)
            top8, lim8 = _top_clause(dialect, 8)
            top15, lim15 = _top_clause(dialect, 15)

            kpi_row = conn.execute(
                text(f"""
                    SELECT
                        COUNT(*) AS total_entries,
                        COUNT(DISTINCT CASE WHEN f.race_sk <> -1 THEN f.race_sk END) AS total_races,
                        COUNT(DISTINCT CASE WHEN f.driver_sk <> -1 THEN f.driver_sk END) AS total_drivers,
                        COUNT(DISTINCT CASE WHEN f.constructor_sk <> -1 THEN f.constructor_sk END) AS total_constructors,
                        MIN(r.season_year) AS actual_min_season,
                        MAX(r.season_year) AS actual_max_season,
                        COALESCE(SUM(CASE WHEN f.position_order = 1 THEN 1 ELSE 0 END), 0) AS wins,
                        COALESCE(SUM(CASE WHEN f.finish_position IN (1, 2, 3) THEN 1 ELSE 0 END), 0) AS podiums,
                        COALESCE(SUM(CASE WHEN f.finish_position IS NOT NULL THEN 1 ELSE 0 END), 0) AS classified_entries,
                        COALESCE(SUM(CASE WHEN f.finish_position IS NULL THEN 1 ELSE 0 END), 0) AS non_classified_entries,
                        COALESCE(SUM(CAST(f.points AS FLOAT)), 0.0) AS total_points,
                        COALESCE(SUM(CASE WHEN f.grid_position > 0 AND f.finish_position IS NOT NULL THEN 1 ELSE 0 END), 0) AS eligible_grid_sample_n,
                        AVG(CASE WHEN f.finish_position IS NOT NULL THEN CAST(f.finish_position AS FLOAT) END) AS mean_classified_finish,
                        AVG(CASE WHEN f.grid_position > 0 AND f.finish_position IS NOT NULL THEN CAST(f.places_gained AS FLOAT) END) AS avg_places_gained
                    {base_from}
                    WHERE {where_sql}
                """),
                params,
            ).mappings().one()

            total_entries = int(kpi_row["total_entries"] or 0)
            classified = int(kpi_row["classified_entries"] or 0)
            non_classified = int(kpi_row["non_classified_entries"] or 0)
            eligible_grid_n = int(kpi_row["eligible_grid_sample_n"] or 0)
            actual_min = int(kpi_row["actual_min_season"]) if kpi_row["actual_min_season"] is not None else None
            actual_max = int(kpi_row["actual_max_season"]) if kpi_row["actual_max_season"] is not None else None
            era_caveat, crossed_eras = _detect_scoring_era_caveat(actual_min, actual_max)

            kpis = {
                "total_entries": total_entries,
                "total_races": int(kpi_row["total_races"] or 0),
                "total_drivers": int(kpi_row["total_drivers"] or 0),
                "total_constructors": int(kpi_row["total_constructors"] or 0),
                "actual_season_range": f"{actual_min}-{actual_max}" if actual_min and actual_max else "N/A",
                "wins": int(kpi_row["wins"] or 0),
                "podiums": int(kpi_row["podiums"] or 0),
                "classified_entries": classified,
                "non_classified_entries": non_classified,
                "classified_rate_pct": round(classified * 100.0 / total_entries, 2) if total_entries else 0.0,
                "non_classified_rate_pct": round(non_classified * 100.0 / total_entries, 2) if total_entries else 0.0,
                "total_points": round(float(kpi_row["total_points"] or 0.0), 2),
                "eligible_grid_sample_n": eligible_grid_n,
                "excluded_grid_rows": total_entries - eligible_grid_n,
                "mean_classified_finish": round(float(kpi_row["mean_classified_finish"]), 2)
                if kpi_row["mean_classified_finish"] is not None
                else None,
                "avg_places_gained": round(float(kpi_row["avg_places_gained"]), 2)
                if kpi_row["avg_places_gained"] is not None
                else None,
            }

            # BQ1 & BQ6: if single season selected, return per-round progression + delta; else recent seasons trend.
            single_season = actual_min is not None and actual_min == actual_max
            if single_season:
                raw_rounds = conn.execute(
                    text(f"""
                        SELECT
                            r.round_number,
                            r.race_name,
                            ci.circuit_name,
                            COUNT(*) AS entries,
                            SUM(CASE WHEN f.position_order = 1 THEN 1 ELSE 0 END) AS wins,
                            SUM(CASE WHEN f.finish_position IS NOT NULL THEN 1 ELSE 0 END) AS classified_entries,
                            ROUND(SUM(CAST(f.points AS FLOAT)), 2) AS total_points
                        {base_from}
                        WHERE {where_sql}
                        GROUP BY r.round_number, r.race_name, ci.circuit_name
                        ORDER BY r.round_number ASC
                    """),
                    params,
                ).mappings().all()
                trend_rows = []
                prev_pts = None
                for row in raw_rounds:
                    pts = round(float(row["total_points"] or 0.0), 2)
                    ent = int(row["entries"] or 0)
                    cls = int(row["classified_entries"] or 0)
                    trend_rows.append(
                        {
                            "round_number": int(row["round_number"]),
                            "race_name": row["race_name"],
                            "circuit_name": row["circuit_name"],
                            "entries": ent,
                            "wins": int(row["wins"] or 0),
                            "classified_rate_pct": round(cls * 100.0 / ent, 2) if ent else 0.0,
                            "total_points": pts,
                            "points_delta_vs_prior_round": round(pts - prev_pts, 2) if prev_pts is not None else None,
                        }
                    )
                    prev_pts = pts
                trend_granularity = "round"
            else:
                raw_seasons = conn.execute(
                    text(f"""
                        SELECT {top15}
                            r.season_year,
                            COUNT(DISTINCT r.race_sk) AS races,
                            COUNT(*) AS entries,
                            SUM(CASE WHEN f.position_order = 1 THEN 1 ELSE 0 END) AS wins,
                            SUM(CASE WHEN f.finish_position IS NOT NULL THEN 1 ELSE 0 END) AS classified_entries,
                            ROUND(SUM(CAST(f.points AS FLOAT)), 2) AS total_points
                        {base_from}
                        WHERE {where_sql} AND r.season_year IS NOT NULL
                        GROUP BY r.season_year
                        ORDER BY r.season_year DESC{lim15}
                    """),
                    params,
                ).mappings().all()
                trend_rows = [
                    {
                        "season_year": int(row["season_year"]),
                        "races": int(row["races"] or 0),
                        "entries": int(row["entries"] or 0),
                        "wins": int(row["wins"] or 0),
                        "classified_rate_pct": round(int(row["classified_entries"] or 0) * 100.0 / int(row["entries"]), 2)
                        if int(row["entries"] or 0)
                        else 0.0,
                        "total_points": round(float(row["total_points"] or 0.0), 2),
                    }
                    for row in reversed(raw_seasons)
                ]
                trend_granularity = "season"

            top_drivers = [
                {
                    "full_name": row["full_name"],
                    "nationality": row["driver_nationality"],
                    "entries": int(row["entries"]),
                    "wins": int(row["wins"]),
                    "podiums": int(row["podiums"]),
                    "points": round(float(row["points"] or 0.0), 2),
                    "classified_rate_pct": round(int(row["classified_entries"]) * 100.0 / int(row["entries"]), 2)
                    if int(row["entries"])
                    else 0.0,
                }
                for row in conn.execute(
                    text(f"""
                        SELECT {top10}
                            dr.full_name,
                            dr.driver_nationality,
                            COUNT(*) AS entries,
                            SUM(CASE WHEN f.position_order = 1 THEN 1 ELSE 0 END) AS wins,
                            SUM(CASE WHEN f.finish_position IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
                            SUM(CASE WHEN f.finish_position IS NOT NULL THEN 1 ELSE 0 END) AS classified_entries,
                            ROUND(SUM(CAST(f.points AS FLOAT)), 2) AS points
                        {base_from}
                        WHERE {where_sql} AND f.driver_sk <> -1
                        GROUP BY dr.full_name, dr.driver_nationality
                        ORDER BY points DESC, wins DESC, podiums DESC{lim10}
                    """),
                    params,
                ).mappings().all()
            ]

            top_constructors = [
                {
                    "constructor_name": row["constructor_name"],
                    "nationality": row["constructor_nationality"],
                    "entries": int(row["entries"]),
                    "wins": int(row["wins"]),
                    "podiums": int(row["podiums"]),
                    "points": round(float(row["points"] or 0.0), 2),
                    "classified_rate_pct": round(int(row["classified_entries"]) * 100.0 / int(row["entries"]), 2)
                    if int(row["entries"])
                    else 0.0,
                }
                for row in conn.execute(
                    text(f"""
                        SELECT {top10}
                            co.constructor_name,
                            co.constructor_nationality,
                            COUNT(*) AS entries,
                            SUM(CASE WHEN f.position_order = 1 THEN 1 ELSE 0 END) AS wins,
                            SUM(CASE WHEN f.finish_position IN (1, 2, 3) THEN 1 ELSE 0 END) AS podiums,
                            SUM(CASE WHEN f.finish_position IS NOT NULL THEN 1 ELSE 0 END) AS classified_entries,
                            ROUND(SUM(CAST(f.points AS FLOAT)), 2) AS points
                        {base_from}
                        WHERE {where_sql} AND f.constructor_sk <> -1
                        GROUP BY co.constructor_name, co.constructor_nationality
                        ORDER BY points DESC, wins DESC, podiums DESC{lim10}
                    """),
                    params,
                ).mappings().all()
            ]

            outcome_breakdown = [
                {
                    "outcome_group": row["outcome_group"],
                    "entries": int(row["entries"]),
                    "share_pct": round(int(row["entries"]) * 100.0 / total_entries, 2) if total_entries else 0.0,
                }
                for row in conn.execute(
                    text(f"""
                        SELECT
                            st.outcome_group,
                            COUNT(*) AS entries
                        {base_from}
                        WHERE {where_sql}
                        GROUP BY st.outcome_group
                        ORDER BY entries DESC
                    """),
                    params,
                ).mappings().all()
            ]

            top_non_classified_statuses = [
                {
                    "status_label": row["status_label"],
                    "outcome_group": row["outcome_group"],
                    "outcome_category": row["outcome_category"],
                    "entries": int(row["entries"]),
                }
                for row in conn.execute(
                    text(f"""
                        SELECT {top8}
                            st.status_label,
                            st.outcome_group,
                            st.outcome_category,
                            COUNT(*) AS entries
                        {base_from}
                        WHERE {where_sql} AND f.finish_position IS NULL
                        GROUP BY st.status_label, st.outcome_group, st.outcome_category
                        ORDER BY entries DESC{lim8}
                    """),
                    params,
                ).mappings().all()
            ]

            top_circuits = [
                {
                    "circuit_name": row["circuit_name"],
                    "country": row["country"],
                    "races": int(row["races"]),
                    "entries": int(row["entries"]),
                    "non_classified_rate_pct": round(
                        int(row["non_classified_entries"]) * 100.0 / int(row["entries"]), 2
                    )
                    if int(row["entries"])
                    else 0.0,
                    "avg_places_gained": round(float(row["avg_places_gained"]), 2)
                    if row["avg_places_gained"] is not None
                    else None,
                }
                for row in conn.execute(
                    text(f"""
                        SELECT {top8}
                            ci.circuit_name,
                            ci.country,
                            COUNT(DISTINCT r.race_sk) AS races,
                            COUNT(*) AS entries,
                            SUM(CASE WHEN f.finish_position IS NULL THEN 1 ELSE 0 END) AS non_classified_entries,
                            AVG(CASE WHEN f.grid_position > 0 AND f.finish_position IS NOT NULL
                                     THEN CAST(f.places_gained AS FLOAT) END) AS avg_places_gained
                        {base_from}
                        WHERE {where_sql} AND f.circuit_sk <> -1
                        GROUP BY ci.circuit_name, ci.country
                        ORDER BY races DESC, entries DESC{lim8}
                    """),
                    params,
                ).mappings().all()
            ]

        return _json_safe(
            {
                "filters_applied": {
                    "season_start": season_start,
                    "season_end": season_end,
                    "constructor_name": constructor_name or "Tất cả",
                    "driver_name": driver_name or "Tất cả",
                    "circuit_name": circuit_name or "Tất cả",
                },
                "kpis": kpis,
                "points_era_caveat": era_caveat,
                "crossed_scoring_era_years": crossed_eras,
                "trend_granularity": trend_granularity,
                "trend": trend_rows,
                "top_drivers": top_drivers,
                "top_constructors": top_constructors,
                "top_circuits": top_circuits,
                "outcome_breakdown": outcome_breakdown,
                "top_non_classified_statuses": top_non_classified_statuses,
            }
        )
    finally:
        if own_engine and engine is not None:
            engine.dispose()


def _compute_duration_sec(started: Any, completed: Any) -> float | None:
    if started is None or completed is None:
        return None
    if isinstance(started, str):
        started = datetime.fromisoformat(started.replace("Z", "+00:00"))
    if isinstance(completed, str):
        completed = datetime.fromisoformat(completed.replace("Z", "+00:00"))
    delta = (completed - started).total_seconds()
    return round(max(delta, 0.0), 3)


def get_etl_summary_data(
    last_n: int = 30,
    target_table: str | None = None,
    engine: Engine | None = None,
) -> dict[str, Any]:
    """Query ETL execution logs & watermark state directly from `ctl.etl_run_log`."""
    own_engine = engine is None
    last_n = max(1, min(int(last_n), 200))
    where_clauses = ["1 = 1"]
    params: dict[str, Any] = {}
    if target_table and target_table != "Tất cả":
        where_clauses.append("target_table = :target_table")
        params["target_table"] = target_table
    where_sql = " AND ".join(where_clauses)

    try:
        engine = engine or create_db_engine()
        with engine.connect() as conn:
            dialect = conn.dialect.name
            top_n, lim_n = _top_clause(dialect, last_n)
            top20, lim20 = _top_clause(dialect, 20)

            recent_raw = conn.execute(
                text(f"""
                    SELECT {top_n}
                        CAST(run_id AS VARCHAR(64)) AS run_id,
                        pipeline_name,
                        source_file,
                        target_schema,
                        target_table,
                        load_mode,
                        batch_key,
                        run_status,
                        started_at_utc,
                        completed_at_utc,
                        rows_read,
                        rows_written,
                        rows_rejected,
                        error_message
                    FROM ctl.etl_run_log
                    WHERE {where_sql}
                    ORDER BY started_at_utc DESC{lim_n}
                """),
                params,
            ).mappings().all()

            watermarks = [
                dict(row)
                for row in conn.execute(
                    text(f"""
                        SELECT {top20}
                            source_name,
                            source_table,
                            batch_key,
                            source_row_count,
                            CAST(last_run_id AS VARCHAR(64)) AS last_run_id,
                            loaded_at_utc,
                            batch_status
                        FROM ctl.etl_batch_state
                        ORDER BY loaded_at_utc DESC{lim20}
                    """)
                ).mappings().all()
            ]

        recent_runs: list[dict[str, Any]] = []
        durations: list[float] = []
        by_table: dict[str, dict[str, Any]] = {}
        by_mode: dict[str, dict[str, Any]] = {}
        failed_or_rejected: list[dict[str, Any]] = []

        success_count = 0
        failed_count = 0
        running_count = 0
        total_read = 0
        total_written = 0
        total_rejected = 0

        for row in recent_raw:
            dur = _compute_duration_sec(row["started_at_utc"], row["completed_at_utc"])
            if dur is not None:
                durations.append(dur)
            status = (row["run_status"] or "").lower()
            rows_read = int(row["rows_read"] or 0)
            rows_written = int(row["rows_written"] or 0)
            rows_rejected = int(row["rows_rejected"] or 0)
            err = (row["error_message"] or "").strip() or None

            total_read += rows_read
            total_written += rows_written
            total_rejected += rows_rejected
            if status == "success":
                success_count += 1
            elif status == "failed":
                failed_count += 1
            else:
                running_count += 1

            item = {
                "run_id": row["run_id"],
                "pipeline_name": row["pipeline_name"],
                "target_table": row["target_table"],
                "load_mode": row["load_mode"],
                "batch_key": row["batch_key"],
                "run_status": row["run_status"],
                "started_at_utc": row["started_at_utc"],
                "completed_at_utc": row["completed_at_utc"],
                "duration_sec": dur,
                "rows_read": rows_read,
                "rows_written": rows_written,
                "rows_rejected": rows_rejected,
                "error_message": err,
            }
            recent_runs.append(item)

            if status != "success" or rows_rejected > 0 or err is not None:
                failed_or_rejected.append(item)

            tbl = row["target_table"] or "unknown"
            tb = by_table.setdefault(
                tbl,
                {
                    "target_table": tbl,
                    "runs": 0,
                    "success_runs": 0,
                    "failed_runs": 0,
                    "rows_written": 0,
                    "rows_rejected": 0,
                    "_durations": [],
                },
            )
            tb["runs"] += 1
            tb["success_runs"] += 1 if status == "success" else 0
            tb["failed_runs"] += 1 if status == "failed" else 0
            tb["rows_written"] += rows_written
            tb["rows_rejected"] += rows_rejected
            if dur is not None:
                tb["_durations"].append(dur)

            mode = row["load_mode"] or "unknown"
            md = by_mode.setdefault(
                mode,
                {
                    "load_mode": mode,
                    "runs": 0,
                    "success_runs": 0,
                    "failed_runs": 0,
                    "rows_written": 0,
                    "rows_rejected": 0,
                    "_durations": [],
                },
            )
            md["runs"] += 1
            md["success_runs"] += 1 if status == "success" else 0
            md["failed_runs"] += 1 if status == "failed" else 0
            md["rows_written"] += rows_written
            md["rows_rejected"] += rows_rejected
            if dur is not None:
                md["_durations"].append(dur)

        total_runs = len(recent_runs)
        avg_dur = round(sum(durations) / len(durations), 3) if durations else None
        max_dur = round(max(durations), 3) if durations else None

        by_table_list = []
        for entry in sorted(by_table.values(), key=lambda x: (-x["failed_runs"], -x["runs"], x["target_table"])):
            durs = entry.pop("_durations")
            entry["avg_duration_sec"] = round(sum(durs) / len(durs), 3) if durs else None
            by_table_list.append(entry)

        by_mode_list = []
        for entry in sorted(by_mode.values(), key=lambda x: x["load_mode"]):
            durs = entry.pop("_durations")
            entry["avg_duration_sec"] = round(sum(durs) / len(durs), 3) if durs else None
            by_mode_list.append(entry)

        anomaly_flags: list[str] = []
        if failed_count > 0:
            bad_tables = sorted({r["target_table"] or "unknown" for r in failed_or_rejected if (r["run_status"] or "").lower() == "failed"})
            anomaly_flags.append(f"FAILED_RUN_DETECTED ({failed_count} lần lỗi ở bảng: {', '.join(bad_tables)})")
        if total_rejected > 0:
            anomaly_flags.append(f"REJECTED_ROWS_DETECTED ({total_rejected} dòng bị loại)")
        if avg_dur is not None and max_dur is not None and max_dur > max(5.0, avg_dur * 2.5):
            anomaly_flags.append(f"DURATION_SPIKE_DETECTED (max {max_dur}s vs avg {avg_dur}s)")
        if not anomaly_flags:
            anomaly_flags.append("HEALTHY_NO_ANOMALIES")

        return _json_safe(
            {
                "filters_applied": {
                    "last_n_runs": last_n,
                    "target_table": target_table or "Tất cả",
                },
                "window_summary": {
                    "total_runs": total_runs,
                    "success_runs": success_count,
                    "failed_runs": failed_count,
                    "running_runs": running_count,
                    "success_rate_pct": round(success_count * 100.0 / total_runs, 2) if total_runs else 0.0,
                    "avg_duration_sec": avg_dur,
                    "max_duration_sec": max_dur,
                    "total_rows_read": total_read,
                    "total_rows_written": total_written,
                    "total_rows_rejected": total_rejected,
                    "latest_run_utc": recent_runs[0]["started_at_utc"] if recent_runs else None,
                },
                "anomaly_flags": anomaly_flags,
                "failed_or_rejected_runs": failed_or_rejected,
                "by_table": by_table_list,
                "by_load_mode": by_mode_list,
                "recent_runs": recent_runs,
                "batch_watermarks": watermarks,
            }
        )
    finally:
        if own_engine and engine is not None:
            engine.dispose()


F1_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích Business Intelligence (BI) cho hệ thống Formula 1 Analytics (1950–2026).

QUY TẮC CHỐNG ẢO GIÁC BẮT BUỘC:
1. CHỈ được sử dụng các con số và thực thể xuất hiện trong dữ liệu JSON đầu vào (và đối chiếu với ảnh biểu đồ nếu người dùng đính kèm). TUYỆT ĐỐI KHÔNG tự bịa số liệu lịch sử F1 từ trí nhớ ngoài JSON.
2. Nếu `points_era_caveat` = true, BẮT BUỘC nêu rõ lưu ý rằng thang điểm F1 đã thay đổi nhiều lần qua các kỷ nguyên (`crossed_scoring_era_years`) nên không so sánh điểm thô đơn thuần giữa các thời kỳ.
3. Khi nhắc đến phân tích vị trí xuất phát vs về đích (BQ4), BẮT BUỘC ghi rõ cỡ mẫu hợp lệ `eligible_grid_sample_n` (lọc `grid_position > 0` và có vị trí phân loại `finish_position IS NOT NULL`) và số dòng loại trừ `excluded_grid_rows`.
4. Khi phân tích kết quả không phân loại (BQ5), BẮT BUỘC phân tách rõ 5 nhóm `outcome_group` (`CLASSIFIED`, `RETIREMENT_DNF`, `DNS`, `DSQ`, `OTHER`); TUYỆT ĐỐI KHÔNG gộp `DNS` hoặc `DSQ` vào `RETIREMENT_DNF`.
5. Ranh giới PHI NHÂN QUẢ (BQ6): Chỉ mô tả đóng góp định lượng theo số liệu (tăng/giảm bao nhiêu điểm, chiếm bao nhiêu %), KHÔNG suy diễn nguyên nhân ngoài dữ liệu (như thời tiết, lốp xe, chiến thuật pit) nếu không có trong JSON.
6. Nếu người dùng đính kèm ảnh biểu đồ Power BI: nhận xét xu hướng trực quan trên ảnh VÀ đối chiếu kiểm chứng với con số thật trong JSON; nếu bộ lọc của ảnh khác với JSON hiện tại thì ghi chú rõ.

ĐỊNH DẠNG ĐẦU RA (tiếng Việt, súc tích, chuyên nghiệp):
### 1. Tóm tắt điều hành (Executive Summary)
### 2. Xu hướng & Điểm nhấn nổi bật
### 3. Phân tích độ tin cậy, vị trí xuất phát & Ngữ cảnh dữ liệu
### 4. Số liệu kiểm chứng (trích ngắn gọn các chỉ số cốt lõi từ JSON)
"""

ETL_SYSTEM_PROMPT = """Bạn là kỹ sư DataOps / ETL Observability cho hệ thống Formula 1 BI (Mage.ai + dbt + SQL Server).

QUY TẮC CHẨN ĐOÁN BẮT BUỘC:
1. CHỈ dựa trên dữ liệu log thật từ bảng `ctl.etl_run_log` và `ctl.etl_batch_state` trong JSON đầu vào. Không bịa ra bảng lỗi hoặc nguyên nhân không có trong log.
2. Nếu có bất kỳ lần chạy nào `failed` hoặc `rows_rejected > 0` trong `failed_or_rejected_runs`, BẮT BUỘC chỉ rõ:
   - `target_table`, `load_mode`, `batch_key`, `rows_rejected`, và trích chính xác `error_message`.
   - Giải thích dễ hiểu nguyên nhân kỹ thuật từ `error_message` và đề xuất bước khắc phục cụ thể (VD: kiểm tra trùng khóa tự nhiên, dữ liệu đầu vào CSV, chạy lại batch).
3. Nếu tất cả các lần chạy đều thành công (`failed_runs = 0`, `total_rows_rejected = 0`), khẳng định hệ thống đang vận hành ổn định, đồng thời nhận xét hiệu năng (duration, so sánh Full Load vs Incremental Load).

ĐỊNH DẠNG ĐẦU RA (tiếng Việt, rõ ràng, thực chiến):
### 1. Tình trạng sức khỏe hệ thống ETL
### 2. Hiệu năng & Khối lượng nạp (Full vs Incremental)
### 3. Sự cố, Dòng bị loại & Chẩn đoán nguyên nhân
### 4. Khuyến nghị vận hành
"""


def call_gemini(
    system_prompt: str,
    user_prompt: str,
    *,
    api_key: str | None = None,
    model_name: str | None = None,
    temperature: float = 0.1,
    image_bytes: bytes | None = None,
    image_mime_type: str = "image/png",
    max_retries: int = 3,
) -> dict[str, Any]:
    """Call Google Gemini API with retry/backoff for 429/503 transient errors."""
    resolved_key = get_gemini_api_key(api_key)
    resolved_model = get_gemini_model(model_name)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=resolved_key, http_options=types.HttpOptions(timeout=35000))
    contents: list[Any] = [user_prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type))

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
    )

    candidates = [resolved_model] + [m for m in FALLBACK_GEMINI_MODELS if m != resolved_model]
    last_exc: Exception | None = None
    last_model = resolved_model
    t0 = time.perf_counter()

    for candidate in candidates:
        last_model = candidate
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=candidate,
                    contents=contents,
                    config=config,
                )
                text_out = (getattr(response, "text", None) or "").strip()
                if not text_out:
                    raise RuntimeError("Gemini trả về phản hồi rỗng.")
                return {
                    "text": text_out,
                    "model_name": candidate,
                    "latency_ms": int((time.perf_counter() - t0) * 1000),
                }
            except Exception as exc:
                last_exc = exc
                msg = str(exc).lower()
                is_rate_limit = any(code in msg for code in ("429", "resource_exhausted", "rate"))
                if is_rate_limit and attempt < max_retries - 1:
                    time.sleep(1.5 * (2**attempt))
                    continue
                is_model_unavailable = any(
                    code in msg
                    for code in ("404", "not_found", "503", "unavailable", "504", "deadline_exceeded", "timed out")
                )
                if is_model_unavailable:
                    break
                raise RuntimeError(f"Lỗi khi gọi Gemini API ({candidate}): {exc}") from exc

    raise RuntimeError(f"Lỗi khi gọi Gemini API ({last_model}): {last_exc}")


def generate_f1_summary(
    context_data: dict[str, Any],
    *,
    chart_image_bytes: bytes | None = None,
    image_mime_type: str = "image/png",
    focus_question: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    """Generate a grounded Vietnamese BI summary from computed `dw.*` metrics."""
    user_parts = [
        "Dưới đây là dữ liệu KPI và phân rã đã được tính toán trực tiếp từ SQL Server Data Warehouse (`dw.*`):",
        "```json",
        json.dumps(context_data, ensure_ascii=False, indent=2),
        "```",
    ]
    if chart_image_bytes:
        user_parts.append(
            "Người dùng CÓ đính kèm ảnh chụp biểu đồ Power BI. Hãy phân tích xu hướng trực quan trên ảnh "
            "và đối chiếu chặt chẽ với các con số thật trong JSON ở trên."
        )
    if focus_question and focus_question.strip():
        user_parts.append(f"Trọng tâm người dùng muốn làm rõ thêm: {focus_question.strip()}")

    res = call_gemini(
        F1_SYSTEM_PROMPT,
        "\n".join(user_parts),
        api_key=api_key,
        model_name=model_name,
        temperature=0.15,
        image_bytes=chart_image_bytes,
        image_mime_type=image_mime_type,
    )
    return {
        "summary_markdown": res["text"],
        "model_name": res["model_name"],
        "latency_ms": res["latency_ms"],
        "grounded_data": context_data,
    }


def generate_etl_summary(
    etl_data: dict[str, Any],
    *,
    focus_question: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    """Generate a grounded Vietnamese ETL health & incident diagnosis."""
    user_parts = [
        "Dưới đây là dữ liệu giám sát thực thi ETL được trích trực tiếp từ `ctl.etl_run_log` và `ctl.etl_batch_state`:",
        "```json",
        json.dumps(etl_data, ensure_ascii=False, indent=2),
        "```",
    ]
    if focus_question and focus_question.strip():
        user_parts.append(f"Trọng tâm người dùng muốn kiểm tra thêm: {focus_question.strip()}")

    res = call_gemini(
        ETL_SYSTEM_PROMPT,
        "\n".join(user_parts),
        api_key=api_key,
        model_name=model_name,
        temperature=0.1,
    )
    return {
        "summary_markdown": res["text"],
        "model_name": res["model_name"],
        "latency_ms": res["latency_ms"],
        "grounded_data": etl_data,
    }
