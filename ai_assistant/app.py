"""Two-tab Streamlit Generative AI Assistant for Formula 1 BI & ETL Observability.

Theme palette (Light Editorial / Soft Glass style):
- Primary Accent: #FD550A (Racing Orange)
- Secondary Accent: #015D47 (Deep Racing Emerald)
- Highlight Accent: #E0F354 (Acid Lime)

Layout:
- Clean header bar: App title, live SQL Server status badge, compact Settings popover.
- Tab 1 (Tóm tắt AI & Biểu đồ): F1 (dw.*) with exact year range (Từ năm – Đến năm)
  or ETL (ctl.etl_run_log) AI summary + light-themed Altair charts + optional Power BI
  chart image upload + raw grounding data.
- Tab 2 (Chatbot Hỏi–Đáp): Soft luminous fixed-frame chat workspace with two-sided
  messenger bubbles (user right in #FD550A, AI left in crisp white card with orb avatar
  & timestamps), native autoscroll upward, floating gradient-border bottom input,
  auto-generated Altair charts, and SQL + DataFrame transparency.

Run locally:
    streamlit run ai_assistant/app.py
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import html
from pathlib import Path
import re
import sys
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai_assistant.ai_core import (
    DEFAULT_GEMINI_MODEL,
    FALLBACK_GEMINI_MODELS,
    check_db_health,
    generate_etl_summary,
    generate_f1_summary,
    get_connection_info,
    get_etl_summary_data,
    get_f1_summary_data,
    get_filter_options,
)
from ai_assistant.text_to_sql import ask_question

COLOR_ORANGE = "#FD550A"
COLOR_GREEN = "#015D47"
COLOR_LIME = "#E0F354"
COLOR_TEXT = "#121E1A"
COLOR_MUTED = "#6B7C76"
COLOR_GRID = "rgba(1, 93, 71, 0.09)"

st.set_page_config(
    page_title="F1 BI Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
      header[data-testid="stHeader"],
      #MainMenu,
      footer,
      [data-testid="stDeployButton"],
      [data-testid="stAppDeployButton"],
      [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
      }}

      /* Luminous editorial light canvas with ultra-soft brand ambient mesh */
      [data-testid="stAppViewContainer"] {{
        background:
          radial-gradient(circle at 12% 10%, rgba(253, 85, 10, 0.08) 0%, transparent 42%),
          radial-gradient(circle at 48% 85%, rgba(224, 243, 84, 0.14) 0%, transparent 46%),
          radial-gradient(circle at 88% 18%, rgba(1, 93, 71, 0.08) 0%, transparent 42%),
          #F8FAF9 !important;
        color: {COLOR_TEXT} !important;
      }}

      .block-container {{
        max-width: 1080px;
        padding-top: 0.9rem !important;
        padding-bottom: 0.75rem !important;
      }}

      /* Header */
      .app-title {{
        display: flex;
        align-items: center;
        gap: 0.7rem;
        flex-wrap: wrap;
      }}
      .app-title h2 {{
        margin: 0;
        font-size: 1.38rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: {COLOR_TEXT};
      }}
      .app-title .accent-dot {{
        color: {COLOR_ORANGE};
      }}
      .db-badge {{
        font-size: 0.74rem;
        padding: 0.18rem 0.55rem;
        border-radius: 5px;
        font-weight: 600;
      }}
      .db-ok {{
        background: rgba(1, 93, 71, 0.09);
        color: {COLOR_GREEN};
        border: 1px solid rgba(1, 93, 71, 0.22);
      }}
      .db-err {{
        background: rgba(253, 85, 10, 0.1);
        color: {COLOR_ORANGE};
        border: 1px solid rgba(253, 85, 10, 0.28);
      }}

      /* Tabs: crisp underline + bright orange text when active, zero box/outline */
      .stTabs [data-baseweb="tab-list"] {{
        gap: 1.5rem;
        border-bottom: 1px solid rgba(1, 93, 71, 0.12);
        margin-bottom: 0.8rem;
        background: transparent !important;
      }}
      .stTabs button[data-baseweb="tab"],
      .stTabs button[role="tab"] {{
        padding: 0.45rem 0.1rem !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        color: {COLOR_MUTED} !important;
        background: transparent !important;
        border: 0 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        outline: 0 !important;
      }}
      .stTabs button[data-baseweb="tab"]::before,
      .stTabs button[data-baseweb="tab"]::after {{
        display: none !important;
        border: 0 !important;
        box-shadow: none !important;
      }}
      .stTabs button[data-baseweb="tab"] p {{
        color: {COLOR_MUTED} !important;
        font-weight: 600 !important;
      }}
      .stTabs button[data-baseweb="tab"]:hover p {{
        color: {COLOR_TEXT} !important;
      }}
      .stTabs button[data-baseweb="tab"]:focus,
      .stTabs button[data-baseweb="tab"]:focus-visible,
      .stTabs button[data-baseweb="tab"]:active,
      .stTabs button[role="tab"]:focus,
      .stTabs button[role="tab"]:focus-visible {{
        box-shadow: none !important;
        outline: 0 !important;
        border: 0 !important;
        background: transparent !important;
      }}
      .stTabs button[aria-selected="true"],
      .stTabs button[aria-selected="true"] p,
      .stTabs button[aria-selected="true"] span,
      .stTabs [data-baseweb="tab"] * {{
        box-shadow: none !important;
        outline: none !important;
      }}
      .stTabs button[aria-selected="true"],
      .stTabs button[aria-selected="true"] p,
      .stTabs button[aria-selected="true"] span {{
        color: {COLOR_ORANGE} !important;
        background: transparent !important;
        border: 0 !important;
      }}
      /* Kill BaseWeb focus border pseudo-element on active tabs */
      .stTabs [data-baseweb="tab-list"] button:focus {{
        outline: none !important;
        box-shadow: none !important;
      }}
      .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {COLOR_ORANGE} !important;
        height: 2.5px !important;
      }}

      /* Clean modern controls (subtle 6px radius — crisp, never overly bubbly) */
      .stButton > button,
      [data-testid="stPopover"] > button,
      [data-baseweb="select"] > div,
      [data-baseweb="input"] > div,
      [data-testid="stSegmentedControl"] button,
      [data-testid="stExpander"] {{
        border-radius: 6px !important;
      }}

      .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {COLOR_ORANGE} 0%, #FF6F2C 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(253, 85, 10, 0.24) !important;
      }}
      .stButton > button[kind="primary"]:hover {{
        filter: brightness(0.95);
        box-shadow: 0 6px 16px rgba(253, 85, 10, 0.32) !important;
      }}

      .stButton > button[kind="secondary"],
      [data-testid="stPopover"] > button {{
        background: #FFFFFF !important;
        border: 1px solid rgba(1, 93, 71, 0.16) !important;
        color: {COLOR_TEXT} !important;
        box-shadow: 0 1px 4px rgba(15, 28, 24, 0.04) !important;
      }}
      .stButton > button[kind="secondary"]:hover,
      [data-testid="stPopover"] > button:hover {{
        border-color: {COLOR_ORANGE} !important;
        color: {COLOR_ORANGE} !important;
      }}

      /* White cards for Tab 1 charts & summaries */
      [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(255, 255, 255, 0.92) !important;
        border: 1px solid rgba(1, 93, 71, 0.11) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 20px rgba(1, 93, 71, 0.05) !important;
      }}

      /* ===== CHAT WORKSPACE (Soft luminous glass panel inspired by reference) ===== */
      .st-key-chat_frame {{
        background:
          radial-gradient(circle at 18% 22%, rgba(253, 85, 10, 0.09) 0%, transparent 45%),
          radial-gradient(circle at 82% 20%, rgba(1, 93, 71, 0.09) 0%, transparent 46%),
          radial-gradient(circle at 52% 78%, rgba(224, 243, 84, 0.16) 0%, transparent 50%),
          radial-gradient(rgba(1, 93, 71, 0.06) 1px, transparent 1px),
          #FFFFFF !important;
        background-size: 100% 100%, 100% 100%, 100% 100%, 22px 22px, 100% 100% !important;
        border: 1px solid rgba(1, 93, 71, 0.13) !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 34px rgba(1, 93, 71, 0.07) !important;
        padding: 1.15rem 1.35rem !important;
      }}

      /* Empty state with 3D glass orb centerpiece */
      .chat-hero {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        min-height: 335px;
        padding: 0.75rem;
      }}
      .chat-hero-title {{
        font-size: 1.48rem;
        line-height: 1.35;
        font-weight: 700;
        letter-spacing: -0.025em;
        margin-bottom: 1.35rem;
        color: {COLOR_TEXT};
      }}
      .chat-hero-title .soft {{
        color: #93A39D;
        font-weight: 600;
      }}
      .hero-orb-wrap {{
        position: relative;
        width: 112px;
        height: 138px;
        display: flex;
        flex-direction: column;
        align-items: center;
      }}
      .hero-orb {{
        width: 108px;
        height: 108px;
        border-radius: 50%;
        background:
          radial-gradient(circle at 30% 24%, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0.18) 22%, transparent 44%),
          radial-gradient(circle at 72% 76%, rgba(1, 93, 71, 0.92) 0%, rgba(1, 93, 71, 0.35) 38%, transparent 65%),
          radial-gradient(circle at 26% 72%, rgba(224, 243, 84, 0.95) 0%, rgba(224, 243, 84, 0.25) 42%, transparent 68%),
          radial-gradient(circle at 68% 28%, rgba(253, 85, 10, 0.92) 0%, rgba(253, 85, 10, 0.3) 48%, rgba(255, 244, 238, 0.85) 100%);
        box-shadow:
          inset -8px -10px 20px rgba(1, 93, 71, 0.28),
          inset 6px 6px 16px rgba(255, 255, 255, 0.85),
          0 14px 32px rgba(253, 85, 10, 0.18),
          0 4px 12px rgba(1, 93, 71, 0.14);
        border: 1px solid rgba(255, 255, 255, 0.7);
      }}
      .hero-orb-reflect {{
        width: 84px;
        height: 18px;
        margin-top: 8px;
        border-radius: 50%;
        background: radial-gradient(ellipse at center, rgba(253, 85, 10, 0.22) 0%, rgba(1, 93, 71, 0.12) 48%, transparent 75%);
        filter: blur(4px);
      }}
      .chat-hero-sub {{
        margin-top: 0.4rem;
        font-size: 0.84rem;
        color: {COLOR_MUTED};
      }}

      /* Two-sided Messenger bubbles */
      .msg-row {{
        display: flex;
        width: 100%;
        margin-bottom: 0.85rem;
      }}
      .msg-row.user {{
        justify-content: flex-end;
      }}
      .msg-row.assistant {{
        justify-content: flex-start;
        align-items: flex-start;
        gap: 0.65rem;
      }}
      .msg-col {{
        display: flex;
        flex-direction: column;
        max-width: 78%;
      }}
      .msg-row.user .msg-col {{
        align-items: flex-end;
        max-width: 68%;
      }}
      .msg-row.assistant .msg-col {{
        align-items: flex-start;
        max-width: 82%;
      }}
      .bot-orb-avatar {{
        width: 28px;
        height: 28px;
        min-width: 28px;
        border-radius: 50%;
        margin-top: 2px;
        background:
          radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.9) 0%, transparent 45%),
          radial-gradient(circle at 75% 75%, {COLOR_GREEN} 0%, transparent 62%),
          radial-gradient(circle at 25% 78%, {COLOR_LIME} 0%, transparent 60%),
          {COLOR_ORANGE};
        box-shadow: 0 2px 8px rgba(253, 85, 10, 0.28);
        border: 1px solid rgba(255, 255, 255, 0.85);
      }}
      .bubble-user {{
        background: linear-gradient(135deg, {COLOR_ORANGE} 0%, #FF6B26 100%);
        color: #FFFFFF;
        padding: 0.58rem 0.95rem;
        border-radius: 12px 12px 3px 12px;
        font-size: 0.91rem;
        line-height: 1.48;
        box-shadow: 0 4px 14px rgba(253, 85, 10, 0.24);
        word-break: break-word;
      }}
      .bubble-ai {{
        background: #FFFFFF;
        color: {COLOR_TEXT};
        padding: 0.72rem 1rem;
        border-radius: 3px 12px 12px 12px;
        border: 1px solid rgba(1, 93, 71, 0.12);
        box-shadow: 0 3px 14px rgba(15, 28, 24, 0.055);
        font-size: 0.91rem;
        line-height: 1.55;
        word-break: break-word;
      }}
      .bubble-ai.blocked {{
        background: #FFF6F3;
        border-color: rgba(253, 85, 10, 0.35);
        color: #9A2B04;
      }}
      .bubble-ai.out_of_scope {{
        background: #F3FAF7;
        border-color: rgba(1, 93, 71, 0.25);
        color: {COLOR_GREEN};
      }}
      .bubble-ai code {{
        background: rgba(1, 93, 71, 0.08);
        color: {COLOR_GREEN};
        padding: 0.08rem 0.35rem;
        border-radius: 4px;
        font-size: 0.84em;
      }}
      .bubble-ai ul, .bubble-ai ol {{
        margin: 0.35rem 0 0.15rem 1.15rem;
        padding: 0;
      }}
      .bubble-ai li {{
        margin-bottom: 0.22rem;
      }}
      .msg-time {{
        font-size: 0.71rem;
        color: #8D9C96;
        margin-top: 0.24rem;
        padding: 0 0.15rem;
      }}

      /* Floating gradient-border input bar flush with the chat window */
      [data-testid="stChatInput"] {{
        max-width: 100%;
        margin: 0.7rem 0 0 0 !important;
      }}
      [data-testid="stChatInput"] > div {{
        background:
          linear-gradient(#FFFFFF, #FFFFFF) padding-box,
          linear-gradient(125deg, rgba(253, 85, 10, 0.55), rgba(224, 243, 84, 0.75), rgba(1, 93, 71, 0.55)) border-box !important;
        border: 1.5px solid transparent !important;
        border-radius: 10px !important;
        box-shadow: 0 6px 24px rgba(1, 93, 71, 0.08) !important;
      }}
      [data-testid="stChatInput"] textarea {{
        color: {COLOR_TEXT} !important;
      }}
      [data-testid="stChatInputSubmitButton"] {{
        background: {COLOR_ORANGE} !important;
        color: #FFFFFF !important;
        border-radius: 7px !important;
      }}

      /* Subtle light scrollbar */
      ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
      }}
      ::-webkit-scrollbar-track {{
        background: transparent;
      }}
      ::-webkit-scrollbar-thumb {{
        background: rgba(1, 93, 71, 0.22);
        border-radius: 3px;
      }}
      ::-webkit-scrollbar-thumb:hover {{
        background: {COLOR_ORANGE};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=120, show_spinner=False)
def _cached_health() -> dict[str, Any]:
    return check_db_health()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_filter_options() -> dict[str, Any]:
    return get_filter_options()


def _format_inline_md(line: str) -> str:
    safe = html.escape(line)
    safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", safe)
    return safe


def _md_to_html(md_text: str) -> str:
    """Safely render concise Markdown (bold, inline code, lists, line breaks) inside HTML bubbles."""
    lines = (md_text or "").strip().splitlines()
    out: list[str] = []
    in_ul = False
    in_ol = False

    def _close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    for raw in lines:
        s = raw.strip()
        if not s:
            _close_lists()
            continue
        ul_m = re.match(r"^[-*•]\s+(.*)$", s)
        ol_m = re.match(r"^\d+\.\s+(.*)$", s)
        if ul_m:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_format_inline_md(ul_m.group(1))}</li>")
        elif ol_m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_format_inline_md(ol_m.group(1))}</li>")
        else:
            _close_lists()
            out.append(f'<div style="margin-bottom:0.25rem;">{_format_inline_md(s)}</div>')

    _close_lists()
    return "".join(out)


def _style_chart(chart: alt.Chart | alt.LayerChart, title: str, height: int = 245) -> alt.Chart | alt.LayerChart:
    return (
        chart.properties(
            title=alt.TitleParams(title, color=COLOR_TEXT, fontSize=13, fontWeight=600, anchor="start", offset=10),
            height=height,
        )
        .configure(background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor=COLOR_MUTED,
            titleColor=COLOR_MUTED,
            gridColor=COLOR_GRID,
            domainColor="rgba(1, 93, 71, 0.18)",
            tickColor="rgba(1, 93, 71, 0.18)",
            labelFontSize=11,
            titleFontSize=11,
        )
        .configure_legend(
            labelColor=COLOR_TEXT,
            titleColor=COLOR_MUTED,
            labelFontSize=11,
            orient="right",
        )
    )


def _render_f1_charts(f1_data: dict[str, Any]) -> None:
    drivers = f1_data.get("top_drivers") or []
    outcomes = f1_data.get("outcome_breakdown") or []
    if not drivers and not outcomes:
        return

    c_left, c_right = st.columns([1.35, 1.0], gap="medium")

    with c_left:
        if drivers:
            df_d = pd.DataFrame(drivers[:8]).copy()
            max_pts = float(df_d["points"].max()) if not df_d.empty else 1.0
            df_d["is_top"] = df_d["points"] == max_pts
            base = alt.Chart(df_d).encode(
                y=alt.Y("full_name:N", sort="-x", title=None, axis=alt.Axis(labelLimit=160)),
                x=alt.X(
                    "points:Q",
                    title="Điểm số",
                    scale=alt.Scale(domain=[0, max(1.0, max_pts * 1.18)]),
                ),
                tooltip=[
                    alt.Tooltip("full_name:N", title="Tay đua"),
                    alt.Tooltip("points:Q", title="Điểm", format=",.1f"),
                    alt.Tooltip("wins:Q", title="Chiến thắng"),
                    alt.Tooltip("podiums:Q", title="Podium"),
                    alt.Tooltip("classified_rate_pct:Q", title="Hoàn thành (%)", format=".1f"),
                ],
            )
            bars = base.mark_bar(cornerRadiusEnd=3, size=18).encode(
                color=alt.condition(
                    alt.datum.is_top,
                    alt.value(COLOR_ORANGE),
                    alt.value(COLOR_GREEN),
                )
            )
            labels = base.mark_text(align="left", dx=6, fontSize=11, fontWeight=600, color=COLOR_TEXT).encode(
                text=alt.Text("points:Q", format=",.0f")
            )
            st.altair_chart(
                _style_chart(bars + labels, "Top tay đua theo điểm", height=245),
                use_container_width=True,
                theme=None,
            )

    with c_right:
        if outcomes:
            df_o = pd.DataFrame(outcomes).copy()
            domain = ["CLASSIFIED", "RETIREMENT_DNF", "DNS", "DSQ", "OTHER"]
            palette = [COLOR_GREEN, COLOR_ORANGE, COLOR_LIME, "#FF9A62", "#94A7A0"]
            donut = (
                alt.Chart(df_o)
                .mark_arc(innerRadius=50, outerRadius=88, cornerRadius=3, padAngle=0.02, stroke="#FFFFFF", strokeWidth=1.5)
                .encode(
                    theta=alt.Theta("entries:Q", stack=True),
                    color=alt.Color(
                        "outcome_group:N",
                        title="Nhóm kết quả",
                        scale=alt.Scale(domain=domain, range=palette),
                    ),
                    tooltip=[
                        alt.Tooltip("outcome_group:N", title="Nhóm"),
                        alt.Tooltip("entries:Q", title="Số lượt", format=","),
                        alt.Tooltip("share_pct:Q", title="Tỷ lệ (%)", format=".2f"),
                    ],
                )
            )
            st.altair_chart(
                _style_chart(donut, "Phân bổ kết quả (outcome_group)", height=245),
                use_container_width=True,
                theme=None,
            )


def _render_etl_charts(etl_data: dict[str, Any]) -> None:
    by_table = etl_data.get("by_table") or []
    if not by_table:
        return

    df_t = pd.DataFrame(by_table).copy()
    df_t["avg_duration_sec"] = pd.to_numeric(df_t["avg_duration_sec"], errors="coerce").fillna(0.0)
    df_t["status_label"] = df_t["failed_runs"].apply(lambda x: "Có lỗi" if int(x or 0) > 0 else "Ổn định")
    max_rows = float(df_t["rows_written"].max()) if not df_t.empty else 1.0
    max_dur = float(df_t["avg_duration_sec"].max()) if not df_t.empty else 1.0

    c_left, c_right = st.columns(2, gap="medium")

    with c_left:
        base_rows = alt.Chart(df_t).encode(
            y=alt.Y("target_table:N", sort="-x", title=None, axis=alt.Axis(labelLimit=160)),
            x=alt.X(
                "rows_written:Q",
                title="Số dòng đã nạp",
                scale=alt.Scale(domain=[0, max(1.0, max_rows * 1.24)]),
            ),
            tooltip=[
                alt.Tooltip("target_table:N", title="Bảng đích"),
                alt.Tooltip("rows_written:Q", title="Dòng đã nạp", format=","),
                alt.Tooltip("runs:Q", title="Số lần chạy"),
                alt.Tooltip("rows_rejected:Q", title="Dòng bị loại", format=","),
            ],
        )
        bars = base_rows.mark_bar(cornerRadiusEnd=3, size=18, color=COLOR_GREEN)
        labels = base_rows.mark_text(align="left", dx=6, fontSize=11, fontWeight=600, color=COLOR_TEXT).encode(
            text=alt.Text("rows_written:Q", format=",")
        )
        st.altair_chart(
            _style_chart(bars + labels, "Tổng dòng đã nạp theo bảng", height=240),
            use_container_width=True,
            theme=None,
        )

    with c_right:
        base_dur = alt.Chart(df_t).encode(
            y=alt.Y("target_table:N", sort="-x", title=None, axis=alt.Axis(labelLimit=160)),
            x=alt.X(
                "avg_duration_sec:Q",
                title="Thời gian TB (giây)",
                scale=alt.Scale(domain=[0, max(1.0, max_dur * 1.24)]),
            ),
            color=alt.Color(
                "status_label:N",
                title="Trạng thái",
                scale=alt.Scale(domain=["Ổn định", "Có lỗi"], range=[COLOR_GREEN, COLOR_ORANGE]),
            ),
            tooltip=[
                alt.Tooltip("target_table:N", title="Bảng đích"),
                alt.Tooltip("avg_duration_sec:Q", title="TB (giây)", format=".2f"),
                alt.Tooltip("success_runs:Q", title="Thành công"),
                alt.Tooltip("failed_runs:Q", title="Thất bại"),
            ],
        )
        bars = base_dur.mark_bar(cornerRadiusEnd=3, size=18)
        labels = base_dur.mark_text(align="left", dx=6, fontSize=11, fontWeight=600, color=COLOR_TEXT).encode(
            text=alt.Text("avg_duration_sec:Q", format=".2f")
        )
        st.altair_chart(
            _style_chart(bars + labels, "Thời gian chạy trung bình theo bảng", height=240),
            use_container_width=True,
            theme=None,
        )


def _render_chat_chart(df: pd.DataFrame) -> None:
    """Render a clean light-themed Altair chart directly below a chat answer."""
    if df is None or df.empty or not (2 <= len(df) <= 20) or df.shape[1] < 2:
        return

    try:
        plot_df = df.copy()
        for col in plot_df.columns:
            if plot_df[col].apply(lambda v: isinstance(v, Decimal)).any():
                plot_df[col] = plot_df[col].apply(lambda v: float(v) if isinstance(v, Decimal) else v)

        num_cols = [c for c in plot_df.columns if pd.api.types.is_numeric_dtype(plot_df[c])]
        cat_cols = [c for c in plot_df.columns if c not in num_cols]

        time_candidates = [c for c in plot_df.columns if any(k in c.lower() for k in ("season", "year", "round"))]
        if time_candidates and num_cols:
            time_col = time_candidates[0]
            metric_candidates = [c for c in num_cols if c != time_col]
            if metric_candidates and plot_df[time_col].nunique(dropna=True) == len(plot_df):
                metric_col = metric_candidates[0]
                tooltips = [alt.Tooltip(c) for c in plot_df.columns[:5]]
                area = (
                    alt.Chart(plot_df)
                    .mark_area(
                        line={"color": COLOR_ORANGE, "strokeWidth": 2.2},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[
                                alt.GradientStop(color="rgba(1, 93, 71, 0.22)", offset=0),
                                alt.GradientStop(color="rgba(224, 243, 84, 0.04)", offset=1),
                            ],
                            x1=1,
                            x2=1,
                            y1=1,
                            y2=0,
                        ),
                    )
                    .encode(
                        x=alt.X(f"{time_col}:O", title=time_col),
                        y=alt.Y(f"{metric_col}:Q", title=metric_col),
                        tooltip=tooltips,
                    )
                )
                pts = (
                    alt.Chart(plot_df)
                    .mark_circle(size=55, color=COLOR_LIME, stroke=COLOR_GREEN, strokeWidth=1.5)
                    .encode(
                        x=alt.X(f"{time_col}:O"),
                        y=alt.Y(f"{metric_col}:Q"),
                        tooltip=tooltips,
                    )
                )
                st.altair_chart(
                    _style_chart(area + pts, f"Xu hướng {metric_col}", height=195),
                    use_container_width=True,
                    theme=None,
                )
                return

        if not num_cols or not cat_cols:
            return

        label_col = cat_cols[0]
        if plot_df[label_col].nunique(dropna=True) != len(plot_df):
            return

        metric_col = num_cols[0]
        max_val = float(plot_df[metric_col].max()) if not plot_df.empty else 1.0
        plot_df["_is_top"] = plot_df[metric_col] == max_val
        tooltips = [alt.Tooltip(c) for c in plot_df.columns if c != "_is_top"][:6]

        if "outcome_group" in label_col.lower() and len(plot_df) <= 6:
            domain = ["CLASSIFIED", "RETIREMENT_DNF", "DNS", "DSQ", "OTHER"]
            palette = [COLOR_GREEN, COLOR_ORANGE, COLOR_LIME, "#FF9A62", "#94A7A0"]
            donut = (
                alt.Chart(plot_df)
                .mark_arc(innerRadius=42, outerRadius=76, cornerRadius=3, padAngle=0.02, stroke="#FFFFFF", strokeWidth=1.5)
                .encode(
                    theta=alt.Theta(f"{metric_col}:Q", stack=True),
                    color=alt.Color(
                        f"{label_col}:N",
                        title=label_col,
                        scale=alt.Scale(domain=domain, range=palette),
                    ),
                    tooltip=tooltips,
                )
            )
            st.altair_chart(
                _style_chart(donut, f"Phân bổ theo {label_col}", height=200),
                use_container_width=True,
                theme=None,
            )
            return

        fmt = ".1f" if pd.api.types.is_float_dtype(plot_df[metric_col]) else ","
        base = alt.Chart(plot_df).encode(
            y=alt.Y(f"{label_col}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=180)),
            x=alt.X(
                f"{metric_col}:Q",
                title=metric_col,
                scale=alt.Scale(domain=[0, max(1.0, max_val * 1.18)]),
            ),
            tooltip=tooltips,
        )
        bars = base.mark_bar(cornerRadiusEnd=3, size=16).encode(
            color=alt.condition(
                alt.datum._is_top,
                alt.value(COLOR_ORANGE),
                alt.value(COLOR_GREEN),
            )
        )
        labels = base.mark_text(align="left", dx=6, fontSize=11, fontWeight=600, color=COLOR_TEXT).encode(
            text=alt.Text(f"{metric_col}:Q", format=fmt)
        )
        chart_height = max(170, min(245, len(plot_df) * 28 + 46))
        st.altair_chart(
            _style_chart(bars + labels, f"Biểu đồ {metric_col} theo {label_col}", height=chart_height),
            use_container_width=True,
            theme=None,
        )
    except Exception:
        return


def _render_header() -> tuple[str | None, str, bool]:
    conn_info = get_connection_info()
    health = _cached_health()
    connected = bool(health["connected"])

    left, right = st.columns([5.4, 1.0], vertical_alignment="center")
    with left:
        err_badge = '<span class="db-badge db-err">● Mất kết nối SQL Server</span>' if not connected else ""
        st.markdown(
            f'<div class="app-title"><h2>F1<span class="accent-dot">.</span> BI Assistant</h2>{err_badge}</div>',
            unsafe_allow_html=True,
        )

    with right:
        with st.popover("Cài đặt", use_container_width=True):
            st.caption(
                f"DB: `{conn_info['host']}:{conn_info['port']}/{conn_info['database']}` · "
                f"User: `{conn_info['username']}` "
                f"({'Read-Only' if conn_info['is_readonly_user'] else 'Fallback'})"
            )
            model_options = list(FALLBACK_GEMINI_MODELS)
            default_idx = model_options.index(DEFAULT_GEMINI_MODEL) if DEFAULT_GEMINI_MODEL in model_options else 0
            model_choice = st.selectbox("Model Gemini", options=model_options, index=default_idx)
            override_key = st.text_input(
                "Gemini API Key (ghi đè .env)",
                type="password",
                placeholder="Mặc định dùng .env",
            )
            c1, c2 = st.columns(2)
            if c1.button("Làm mới DB", use_container_width=True):
                _cached_health.clear()
                _cached_filter_options.clear()
                st.rerun()
            if c2.button("Xóa chat", use_container_width=True):
                st.session_state["chat_history"] = []
                st.rerun()

    if not connected:
        st.error(f"Không kết nối được SQL Server ({conn_info['host']}:{conn_info['port']}): {health['error']}")

    return (override_key.strip() or None), model_choice, connected


def _render_tab_summary(api_key: str | None, model_name: str, db_connected: bool) -> None:
    if not db_connected:
        return

    mode = (
        st.segmented_control(
            "Chế độ",
            options=["Phân tích F1", "Chẩn đoán ETL"],
            default="Phân tích F1",
            label_visibility="collapsed",
        )
        or "Phân tích F1"
    )

    filter_opts = _cached_filter_options()

    if mode == "Phân tích F1":
        min_s, max_s = int(filter_opts["min_season"]), int(filter_opts["max_season"])
        years_desc = list(range(max_s, min_s - 1, -1))
        default_year = min(2023, max_s)
        default_year_idx = years_desc.index(default_year) if default_year in years_desc else 0

        c1, c2, c3, c4, c5 = st.columns([0.85, 0.85, 1.35, 1.05, 1.05], vertical_alignment="bottom")
        year_from = c1.selectbox("Từ năm", years_desc, index=default_year_idx)
        year_to = c2.selectbox("Đến năm", years_desc, index=default_year_idx)
        season_start, season_end = min(year_from, year_to), max(year_from, year_to)
        selected_constructor = c3.selectbox("Đội đua", ["Tất cả"] + filter_opts["constructors"])

        uploaded_chart = None
        with c4:
            with st.popover("Upload ảnh PBI", use_container_width=True):
                st.caption("Tùy chọn: tải ảnh chụp biểu đồ Power BI để AI đối chiếu trực quan với số liệu SQL.")
                uploaded_chart = st.file_uploader(
                    "Chọn ảnh PNG/JPG",
                    type=["png", "jpg", "jpeg"],
                    key="f1_chart_upload",
                    label_visibility="collapsed",
                )
                if uploaded_chart is not None:
                    st.image(uploaded_chart, width=280)

        run_f1 = c5.button("Tạo tóm tắt AI", type="primary", use_container_width=True)
        if uploaded_chart is not None:
            st.caption(f"Đang đính kèm ảnh Power BI: `{uploaded_chart.name}`")

        if run_f1:
            with st.spinner(f"Đang phân tích giai đoạn {season_start}–{season_end}..."):
                try:
                    f1_data = get_f1_summary_data(
                        season_start=season_start,
                        season_end=season_end,
                        constructor_name=selected_constructor,
                    )
                    img_bytes = uploaded_chart.getvalue() if uploaded_chart is not None else None
                    img_mime = (uploaded_chart.type or "image/png") if uploaded_chart is not None else "image/png"
                    st.session_state["last_f1_summary"] = generate_f1_summary(
                        f1_data,
                        chart_image_bytes=img_bytes,
                        image_mime_type=img_mime,
                        api_key=api_key,
                        model_name=model_name,
                    )
                except Exception as exc:
                    st.error(str(exc))

        if "last_f1_summary" in st.session_state:
            res = st.session_state["last_f1_summary"]
            with st.container(border=True):
                _render_f1_charts(res["grounded_data"])
            with st.container(border=True):
                st.markdown(res["summary_markdown"])
            with st.expander("Xem số liệu gốc đã gửi AI"):
                st.json(res["grounded_data"])

    else:
        c1, c2, c3 = st.columns([1.0, 1.5, 1.0], vertical_alignment="bottom")
        last_n = c1.selectbox("Lần chạy gần nhất", [15, 30, 50, 100], index=1)
        selected_table = c2.selectbox("Bảng đích", ["Tất cả"] + filter_opts["etl_tables"])
        run_etl = c3.button("Chẩn đoán ETL", type="primary", use_container_width=True)

        if run_etl:
            with st.spinner("Đang đọc log ETL và chẩn đoán..."):
                try:
                    etl_data = get_etl_summary_data(last_n=int(last_n), target_table=selected_table)
                    st.session_state["last_etl_summary"] = generate_etl_summary(
                        etl_data,
                        api_key=api_key,
                        model_name=model_name,
                    )
                except Exception as exc:
                    st.error(str(exc))

        if "last_etl_summary" in st.session_state:
            res = st.session_state["last_etl_summary"]
            flags = res["grounded_data"].get("anomaly_flags", [])
            if any(not f.startswith("HEALTHY") for f in flags):
                st.error("Phát hiện bất thường: " + " | ".join(flags))
            with st.container(border=True):
                _render_etl_charts(res["grounded_data"])
            with st.container(border=True):
                st.markdown(res["summary_markdown"])
            with st.expander("Xem bảng log gốc (`ctl.etl_run_log`)"):
                st.dataframe(pd.DataFrame(res["grounded_data"]["recent_runs"]), use_container_width=True)


def _render_chat_bubble(msg: dict[str, Any]) -> None:
    ts = html.escape(msg.get("timestamp") or "")
    if msg["role"] == "user":
        safe_q = html.escape(msg["content"]).replace("\n", "<br/>")
        st.markdown(
            f"""
            <div class="msg-row user">
              <div class="msg-col">
                <div class="bubble-user">{safe_q}</div>
                <div class="msg-time">{ts}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    status = msg.get("status") or "success"
    extra_cls = " blocked" if status == "blocked" else (" out_of_scope" if status == "out_of_scope" else "")
    body_html = _md_to_html(msg["content"])
    st.markdown(
        f"""
        <div class="msg-row assistant">
          <div class="bot-orb-avatar"></div>
          <div class="msg-col">
            <div class="bubble-ai{extra_cls}">{body_html}</div>
            <div class="msg-time">{ts}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = msg.get("dataframe")
    has_df = isinstance(df, pd.DataFrame) and not df.empty
    has_sql = bool(msg.get("sql"))
    if has_df or has_sql:
        _, detail_col = st.columns([0.055, 0.945])
        with detail_col:
            if has_df:
                _render_chat_chart(df)
            if has_sql:
                with st.expander(f"Xem SQL & Bảng dữ liệu ({msg.get('row_count', 0)} dòng)"):
                    st.code(msg["sql"], language="sql")
                    if has_df:
                        st.dataframe(df, use_container_width=True)


def _render_tab_chatbot(api_key: str | None, model_name: str, db_connected: bool) -> None:
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    has_messages = bool(st.session_state["chat_history"])

    # Soft luminous framed chat window with native autoscroll upward
    chat_frame = st.container(height=410, border=True, key="chat_frame", autoscroll=True)

    with chat_frame:
        if not has_messages:
            st.markdown(
                """
                <div class="chat-hero">
                  <div class="chat-hero-title">
                    Trợ lý F1 BI<br/>
                    Tra cứu dữ liệu tức thì
                  </div>
                  <div class="hero-orb-wrap">
                    <div class="hero-orb"></div>
                    <div class="hero-orb-reflect"></div>
                  </div>
                  <div class="chat-hero-sub">Tra cứu số liệu giải đua F1 (1950–2026) và tình trạng chạy ETL</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state["chat_history"]:
                _render_chat_bubble(msg)

    active_question = st.chat_input(
        "Nhập câu hỏi bất kỳ về F1 hoặc ETL...",
        disabled=not db_connected,
    )

    if active_question:
        now_str = datetime.now().strftime("%H:%M")
        user_msg = {"role": "user", "content": active_question, "timestamp": now_str}
        st.session_state["chat_history"].append(user_msg)

        with chat_frame:
            _render_chat_bubble(user_msg)
            with st.spinner("Đang phân tích câu hỏi..."):
                res = ask_question(
                    active_question,
                    api_key=api_key,
                    model_name=model_name,
                )

        assistant_msg = {
            "role": "assistant",
            "content": res["answer"],
            "status": res["status"],
            "sql": res.get("sql"),
            "dataframe": res.get("dataframe"),
            "row_count": res.get("row_count", 0),
            "execution_ms": res.get("execution_ms", 0),
            "timestamp": datetime.now().strftime("%H:%M"),
        }
        st.session_state["chat_history"].append(assistant_msg)
        st.rerun()


def main() -> None:
    api_key, model_name, db_connected = _render_header()
    tab_summary, tab_chat = st.tabs(["Tóm tắt AI & Biểu đồ", "Chatbot Hỏi–Đáp"])
    with tab_summary:
        _render_tab_summary(api_key, model_name, db_connected)
    with tab_chat:
        _render_tab_chatbot(api_key, model_name, db_connected)


if __name__ == "__main__":
    main()
