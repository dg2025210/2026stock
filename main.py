import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="글로벌 주식 비교 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Pretendard:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Pretendard', sans-serif;
    background-color: #0a0d14;
    color: #e2e8f0;
  }

  .main { background-color: #0a0d14; }
  .block-container { padding: 1.5rem 2rem 3rem; }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background-color: #0f1520;
    border-right: 1px solid #1e2a3a;
  }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stMultiSelect label,
  section[data-testid="stSidebar"] .stDateInput label,
  section[data-testid="stSidebar"] p {
    color: #94a3b8 !important;
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  /* Header */
  .dash-header {
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-bottom: 0.5rem;
  }
  .dash-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.7rem;
    font-weight: 600;
    color: #f0f6ff;
    letter-spacing: -0.02em;
  }
  .dash-sub {
    font-size: 0.85rem;
    color: #4a90d9;
    font-family: 'IBM Plex Mono', monospace;
  }
  .divider { border: none; border-top: 1px solid #1e2a3a; margin: 0.8rem 0 1.4rem; }

  /* Metric Cards */
  .metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
    margin-bottom: 1.4rem;
  }
  .metric-card {
    background: #111927;
    border: 1px solid #1e2a3a;
    border-radius: 10px;
    padding: 14px 16px;
    position: relative;
    overflow: hidden;
  }
  .metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }
  .metric-card.pos::before { background: linear-gradient(90deg, #22c55e, #4ade80); }
  .metric-card.neg::before { background: linear-gradient(90deg, #ef4444, #f87171); }
  .metric-card.neu::before { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
  .metric-ticker {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #64748b;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
  }
  .metric-name {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-bottom: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .metric-price {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.15rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 4px;
  }
  .metric-ret.pos { color: #22c55e; font-size: 0.88rem; font-weight: 600; }
  .metric-ret.neg { color: #ef4444; font-size: 0.88rem; font-weight: 600; }

  /* Section Label */
  .section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a90d9;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e2a3a;
  }

  /* Flag badge */
  .flag-badge {
    display: inline-block;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 4px;
    font-family: 'IBM Plex Mono', monospace;
  }
  .flag-kr { background: #1a2a4a; color: #60a5fa; border: 1px solid #1e3a6e; }
  .flag-us { background: #1a2a2a; color: #34d399; border: 1px solid #1e4a3a; }

  /* Streamlit overrides */
  .stMultiSelect [data-baseweb="tag"] {
    background-color: #1e3a6e !important;
  }
  div[data-testid="stDateInput"] input {
    background-color: #111927;
    border-color: #1e2a3a;
    color: #e2e8f0;
  }
</style>
""", unsafe_allow_html=True)

# ─── Stock Universe ──────────────────────────────────────────────────────────
KR_STOCKS = {
    "삼성전자 (005930)":   "005930.KS",
    "SK하이닉스 (000660)": "000660.KS",
    "LG에너지솔루션 (373220)": "373220.KS",
    "삼성바이오로직스 (207940)": "207940.KS",
    "현대차 (005380)":     "005380.KS",
    "기아 (000270)":       "000270.KS",
    "POSCO홀딩스 (005490)": "005490.KS",
    "NAVER (035420)":      "035420.KS",
    "카카오 (035720)":     "035720.KS",
    "셀트리온 (068270)":   "068270.KS",
    "LG화학 (051910)":     "051910.KS",
    "KB금융 (105560)":     "105560.KS",
}
US_STOCKS = {
    "Apple (AAPL)":        "AAPL",
    "Microsoft (MSFT)":    "MSFT",
    "NVIDIA (NVDA)":       "NVDA",
    "Amazon (AMZN)":       "AMZN",
    "Alphabet (GOOGL)":    "GOOGL",
    "Meta (META)":         "META",
    "Tesla (TSLA)":        "TSLA",
    "Broadcom (AVGO)":     "AVGO",
    "Berkshire (BRK-B)":   "BRK-B",
    "JPMorgan (JPM)":      "JPM",
    "Netflix (NFLX)":      "NFLX",
    "AMD (AMD)":           "AMD",
}
ALL_STOCKS = {**KR_STOCKS, **US_STOCKS}
NAME_BY_TICKER = {v: k for k, v in ALL_STOCKS.items()}

PERIODS = {
    "1개월":   30, "3개월":  90, "6개월": 180,
    "1년":    365, "2년":   730, "3년": 1095,
}

COLORS = [
    "#4a90d9", "#22c55e", "#f59e0b", "#ec4899",
    "#a78bfa", "#34d399", "#fb923c", "#60a5fa",
    "#f472b6", "#4ade80", "#fbbf24", "#38bdf8",
]

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 설정")
    st.markdown("---")

    period_label = st.selectbox("📅 기간", list(PERIODS.keys()), index=3)
    days = PERIODS[period_label]
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=days)

    st.markdown("**🇰🇷 한국 주식**")
    sel_kr = st.multiselect(
        "한국 종목 선택",
        list(KR_STOCKS.keys()),
        default=["삼성전자 (005930)", "SK하이닉스 (000660)", "현대차 (005380)"],
        label_visibility="collapsed",
    )

    st.markdown("**🇺🇸 미국 주식**")
    sel_us = st.multiselect(
        "미국 종목 선택",
        list(US_STOCKS.keys()),
        default=["Apple (AAPL)", "NVIDIA (NVDA)", "Tesla (TSLA)"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    chart_type = st.radio("차트 타입", ["라인", "캔들스틱"], horizontal=True)
    show_volume = st.toggle("거래량 표시", value=True)
    normalize = st.toggle("수익률 기준 정규화 (100)", value=True)

selected_names   = sel_kr + sel_us
selected_tickers = [ALL_STOCKS[n] for n in selected_names]
color_map        = {t: COLORS[i % len(COLORS)] for i, t in enumerate(selected_tickers)}

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
  <span class="dash-title">📈 글로벌 주식 대시보드</span>
  <span class="dash-sub">// KR & US Market Tracker</span>
</div>
<hr class="divider">
""", unsafe_allow_html=True)

if not selected_tickers:
    st.info("👈 사이드바에서 종목을 선택해주세요.")
    st.stop()

# ─── Data Fetch ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(tickers, start, end):
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if len(tickers) == 1:
        raw.columns = pd.MultiIndex.from_product([raw.columns, tickers])
    return raw

with st.spinner("데이터 불러오는 중..."):
    raw = fetch_data(selected_tickers, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

close  = raw["Close"].dropna(how="all")
volume = raw["Volume"].dropna(how="all") if "Volume" in raw else pd.DataFrame()

if close.empty:
    st.error("데이터를 불러올 수 없습니다. 종목을 다시 선택해주세요.")
    st.stop()

# ─── Metric Cards ─────────────────────────────────────────────────────────────
def fmt_price(ticker, price):
    if ticker.endswith(".KS"):
        return f"₩{price:,.0f}"
    return f"${price:,.2f}"

cards_html = '<div class="metric-grid">'
for ticker in selected_tickers:
    if ticker not in close.columns:
        continue
    series = close[ticker].dropna()
    if len(series) < 2:
        continue
    ret   = (series.iloc[-1] / series.iloc[0] - 1) * 100
    name  = NAME_BY_TICKER.get(ticker, ticker)
    price = series.iloc[-1]
    cls   = "pos" if ret >= 0 else "neg"
    arrow = "▲" if ret >= 0 else "▼"
    flag  = "KR" if ticker.endswith(".KS") else "US"
    flag_cls = "flag-kr" if flag == "KR" else "flag-us"
    short_name = name.split("(")[0].strip()
    cards_html += f"""
    <div class="metric-card {cls}">
      <div class="metric-ticker">
        <span class="flag-badge {flag_cls}">{flag}</span>{ticker.replace('.KS','')}
      </div>
      <div class="metric-name">{short_name}</div>
      <div class="metric-price">{fmt_price(ticker, price)}</div>
      <div class="metric-ret {cls}">{arrow} {abs(ret):.1f}% ({period_label})</div>
    </div>"""
cards_html += "</div>"
st.markdown(cards_html, unsafe_allow_html=True)

# ─── Normalized Return Chart ──────────────────────────────────────────────────
st.markdown('<div class="section-label">수익률 비교</div>', unsafe_allow_html=True)

fig_ret = go.Figure()
for ticker in selected_tickers:
    if ticker not in close.columns:
        continue
    series = close[ticker].dropna()
    if series.empty:
        continue
    label = NAME_BY_TICKER.get(ticker, ticker).split("(")[0].strip()
    if normalize:
        y_vals = series / series.iloc[0] * 100
        y_label = "정규화 수익률 (기준 100)"
    else:
        y_vals = (series / series.iloc[0] - 1) * 100
        y_label = "수익률 (%)"

    fig_ret.add_trace(go.Scatter(
        x=series.index, y=y_vals,
        name=label,
        line=dict(color=color_map[ticker], width=2),
        hovertemplate=f"<b>{label}</b><br>날짜: %{{x|%Y-%m-%d}}<br>값: %{{y:.1f}}<extra></extra>",
    ))

fig_ret.update_layout(
    height=400,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d1520",
    font=dict(family="IBM Plex Mono, monospace", color="#94a3b8", size=11),
    legend=dict(
        bgcolor="rgba(15,21,32,0.9)", bordercolor="#1e2a3a", borderwidth=1,
        font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
    ),
    xaxis=dict(gridcolor="#1e2a3a", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1e2a3a", showgrid=True, zeroline=False, title=y_label),
    hovermode="x unified",
    margin=dict(t=40, b=40, l=50, r=20),
)
st.plotly_chart(fig_ret, use_container_width=True)

# ─── Individual Charts ────────────────────────────────────────────────────────
st.markdown('<div class="section-label">개별 종목 차트</div>', unsafe_allow_html=True)

valid_tickers = [t for t in selected_tickers if t in close.columns and not close[t].dropna().empty]
n = len(valid_tickers)
cols_per_row = 2
rows_needed  = (n + cols_per_row - 1) // cols_per_row

for row_idx in range(rows_needed):
    cols = st.columns(cols_per_row)
    for col_idx in range(cols_per_row):
        i = row_idx * cols_per_row + col_idx
        if i >= n:
            break
        ticker = valid_tickers[i]
        label  = NAME_BY_TICKER.get(ticker, ticker).split("(")[0].strip()
        color  = color_map[ticker]
        series = close[ticker].dropna()

        with cols[col_idx]:
            if chart_type == "캔들스틱":
                ohlc = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
                if show_volume:
                    fig_c = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                          row_heights=[0.75, 0.25], vertical_spacing=0.03)
                else:
                    fig_c = make_subplots(rows=1, cols=1)

                fig_c.add_trace(go.Candlestick(
                    x=ohlc.index,
                    open=ohlc["Open"].squeeze(),
                    high=ohlc["High"].squeeze(),
                    low=ohlc["Low"].squeeze(),
                    close=ohlc["Close"].squeeze(),
                    name=label,
                    increasing_line_color="#22c55e",
                    decreasing_line_color="#ef4444",
                    increasing_fillcolor="#22c55e",
                    decreasing_fillcolor="#ef4444",
                ), row=1, col=1)

                if show_volume and not volume.empty and ticker in volume.columns:
                    vol_series = volume[ticker].dropna()
                    fig_c.add_trace(go.Bar(
                        x=vol_series.index, y=vol_series,
                        name="거래량", marker_color="#1e3a6e", opacity=0.7,
                    ), row=2, col=1)
                fig_c.update_layout(
                    title=dict(text=label, font=dict(size=12, color=color)),
                    height=320 if show_volume else 260,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1520",
                    font=dict(family="IBM Plex Mono, monospace", color="#94a3b8", size=10),
                    xaxis_rangeslider_visible=False,
                    showlegend=False,
                    margin=dict(t=36, b=30, l=50, r=20),
                )
                fig_c.update_xaxes(gridcolor="#1e2a3a")
                fig_c.update_yaxes(gridcolor="#1e2a3a")
                st.plotly_chart(fig_c, use_container_width=True)
            else:
                # Line chart with fill
                ret_pct = (series.iloc[-1] / series.iloc[0] - 1) * 100
                fig_l = go.Figure()
                fig_l.add_trace(go.Scatter(
                    x=series.index, y=series,
                    name=label,
                    line=dict(color=color, width=2),
                    fill="tozeroy",
                    fillcolor=color.replace(")", ",0.08)").replace("rgb", "rgba").replace("#", "rgba(")
                         if "#" in color else color,
                ))
                # Reformat fill for hex colors
                fig_l.data[0].fillcolor = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)"
                ret_str = f"▲ +{ret_pct:.1f}%" if ret_pct >= 0 else f"▼ {ret_pct:.1f}%"
                fig_l.update_layout(
                    title=dict(text=f"{label}  <span style='color:{'#22c55e' if ret_pct>=0 else '#ef4444'};font-size:11px'>{ret_str}</span>",
                               font=dict(size=12, color=color)),
                    height=200,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1520",
                    font=dict(family="IBM Plex Mono, monospace", color="#94a3b8", size=10),
                    showlegend=False,
                    xaxis=dict(gridcolor="#1e2a3a", showgrid=True),
                    yaxis=dict(gridcolor="#1e2a3a", showgrid=True),
                    margin=dict(t=36, b=30, l=55, r=15),
                )
                st.plotly_chart(fig_l, use_container_width=True)

# ─── Performance Table ────────────────────────────────────────────────────────
st.markdown('<div class="section-label">수익률 통계 테이블</div>', unsafe_allow_html=True)

rows = []
for ticker in selected_tickers:
    if ticker not in close.columns:
        continue
    s = close[ticker].dropna()
    if len(s) < 5:
        continue
    daily_ret = s.pct_change().dropna()
    total_ret = (s.iloc[-1] / s.iloc[0] - 1) * 100
    vol_ann   = daily_ret.std() * np.sqrt(252) * 100
    sharpe    = (daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0
    max_dd_val = ((s / s.cummax()) - 1).min() * 100
    flag      = "🇰🇷" if ticker.endswith(".KS") else "🇺🇸"
    rows.append({
        "": flag,
        "종목":        NAME_BY_TICKER.get(ticker, ticker).split("(")[0].strip(),
        "티커":        ticker.replace(".KS", ""),
        f"수익률 ({period_label})": f"{'▲ +' if total_ret>=0 else '▼ '}{abs(total_ret):.1f}%",
        "연환산 변동성": f"{vol_ann:.1f}%",
        "샤프지수":    f"{sharpe:.2f}",
        "최대 낙폭 (MDD)": f"{max_dd_val:.1f}%",
        "현재가":      fmt_price(ticker, s.iloc[-1]),
    })

if rows:
    df_table = pd.DataFrame(rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

# ─── Correlation Heatmap ──────────────────────────────────────────────────────
if len(valid_tickers) >= 2:
    st.markdown('<div class="section-label">수익률 상관관계</div>', unsafe_allow_html=True)

    daily_rets = close[valid_tickers].pct_change().dropna()
    corr = daily_rets.corr()
    labels = [NAME_BY_TICKER.get(t, t).split("(")[0].strip() for t in corr.columns]

    fig_heat = go.Figure(go.Heatmap(
        z=corr.values,
        x=labels, y=labels,
        colorscale=[[0, "#1a3a6e"], [0.5, "#0d1520"], [1, "#1a4a2e"]],
        zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in corr.values],
        texttemplate="%{text}",
        textfont=dict(size=10, family="IBM Plex Mono"),
        hoverongaps=False,
    ))
    fig_heat.update_layout(
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d1520",
        font=dict(family="IBM Plex Mono, monospace", color="#94a3b8", size=10),
        margin=dict(t=20, b=60, l=120, r=20),
        xaxis=dict(tickangle=-30),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#334155; font-size:0.72rem;
     font-family: IBM Plex Mono, monospace; margin-top:2rem; padding-top:1rem;
     border-top: 1px solid #1e2a3a;'>
  데이터 출처: Yahoo Finance (yfinance) &nbsp;|&nbsp; 5분 캐시 &nbsp;|&nbsp;
  투자 참고용이며 투자 권유가 아닙니다.
</div>
""", unsafe_allow_html=True)
