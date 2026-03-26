import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(page_title="차트 분석 | 글로벌 주식 분석기", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: #0d1117; color: #e6edf3; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1117 0%, #161b22 100%); }
[data-testid="stSidebar"] * { color: #e6edf3 !important; }
.stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 0.9rem; text-align: center; }
[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 0.8rem; }
[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }
.stDataFrame, .stTable { overflow-x: auto !important; display: block !important; }
@media (max-width: 768px) {
    .block-container { padding: 0.8rem 0.6rem !important; }
    h1 { font-size: 1.3rem !important; }
}
</style>
""", unsafe_allow_html=True)

ALL_STOCKS = {
    # 한국
    "삼성전자 (005930.KS)": "005930.KS",
    "SK하이닉스 (000660.KS)": "000660.KS",
    "LG에너지솔루션 (373220.KS)": "373220.KS",
    "현대차 (005380.KS)": "005380.KS",
    "POSCO홀딩스 (005490.KS)": "005490.KS",
    "카카오 (035720.KS)": "035720.KS",
    "네이버 (035420.KS)": "035420.KS",
    "셀트리온 (068270.KS)": "068270.KS",
    # 미국
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "NVIDIA (NVDA)": "NVDA",
    "Amazon (AMZN)": "AMZN",
    "Alphabet (GOOGL)": "GOOGL",
    "Meta (META)": "META",
    "Tesla (TSLA)": "TSLA",
    "JPMorgan (JPM)": "JPM",
    "Eli Lilly (LLY)": "LLY",
}

PERIOD_MAP = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "3년": "3y",
    "5년": "5y",
}

# ── 헤더 ──────────────────────────────────────────────────────────────────────
st.markdown("# 📈 차트 분석")
st.markdown("캔들스틱·이동평균선·거래량으로 종목을 심층 분석합니다.")
st.divider()

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    mode = st.radio("종목 입력 방식", ["목록에서 선택", "직접 입력"])
    if mode == "목록에서 선택":
        sel_name = st.selectbox("종목 선택", list(ALL_STOCKS.keys()))
        ticker_input = ALL_STOCKS[sel_name]
    else:
        ticker_input = st.text_input("티커 입력 (예: 005930.KS, AAPL)", "AAPL").strip().upper()

    period_label = st.selectbox("📅 기간", list(PERIOD_MAP.keys()), index=2)
    period = PERIOD_MAP[period_label]

    st.divider()
    st.markdown("**이동평균선**")
    show_ma5   = st.checkbox("MA5 (단기)", value=True)
    show_ma20  = st.checkbox("MA20 (중기)", value=True)
    show_ma60  = st.checkbox("MA60 (장기)", value=True)
    show_ma120 = st.checkbox("MA120", value=False)
    show_bb    = st.checkbox("볼린저 밴드", value=True)

    st.divider()
    chart_type = st.radio("차트 유형", ["캔들스틱", "라인 차트"])

# ── 데이터 로딩 ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=180)
def load_stock(ticker, period):
    t = yf.Ticker(ticker)
    hist = t.history(period=period)
    info = {}
    try:
        info = t.info
    except Exception:
        pass
    return hist, info

with st.spinner("데이터 로딩 중..."):
    try:
        hist, info = load_stock(ticker_input, period)
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        st.stop()

if hist.empty:
    st.error("데이터를 찾을 수 없습니다. 티커를 확인해 주세요.")
    st.stop()

# ── 이동평균 계산 ──────────────────────────────────────────────────────────────
hist["MA5"]   = hist["Close"].rolling(5).mean()
hist["MA20"]  = hist["Close"].rolling(20).mean()
hist["MA60"]  = hist["Close"].rolling(60).mean()
hist["MA120"] = hist["Close"].rolling(120).mean()
hist["BB_mid"] = hist["Close"].rolling(20).mean()
hist["BB_std"] = hist["Close"].rolling(20).std()
hist["BB_upper"] = hist["BB_mid"] + 2 * hist["BB_std"]
hist["BB_lower"] = hist["BB_mid"] - 2 * hist["BB_std"]

# ── 종목 정보 요약 ────────────────────────────────────────────────────────────
name = info.get("longName") or info.get("shortName") or ticker_input
curr_price = hist["Close"].iloc[-1]
prev_price = hist["Close"].iloc[-2] if len(hist) > 1 else curr_price
chg = (curr_price - prev_price) / prev_price * 100
ret_period = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
vol_avg = hist["Volume"].mean()

st.markdown(f"### {name} ({ticker_input})")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("현재가", f"{curr_price:,.2f}", f"{chg:+.2f}%")
c2.metric(f"{period_label} 수익률", f"{ret_period:+.2f}%")
c3.metric("52주 고가", f"{hist['High'].max():,.2f}")
c4.metric("52주 저가", f"{hist['Low'].min():,.2f}")
c5.metric("평균 거래량", f"{vol_avg:,.0f}")

st.divider()

# ── 메인 차트 ──────────────────────────────────────────────────────────────────
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.75, 0.25],
    subplot_titles=["가격 차트", "거래량"],
)

# 캔들스틱 / 라인
if chart_type == "캔들스틱":
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"],
        name="OHLC",
        increasing_line_color="#3fb950",
        decreasing_line_color="#f85149",
    ), row=1, col=1)
else:
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"],
        name="종가", mode="lines",
        line=dict(color="#58a6ff", width=2),
    ), row=1, col=1)

# 이동평균선
MA_CFG = [
    ("MA5",   "#d29922", show_ma5),
    ("MA20",  "#3fb950", show_ma20),
    ("MA60",  "#f85149", show_ma60),
    ("MA120", "#bc8cff", show_ma120),
]
for col_name, color, visible in MA_CFG:
    if visible and col_name in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist[col_name],
            name=col_name, mode="lines",
            line=dict(color=color, width=1.2, dash="solid"),
            visible=True,
        ), row=1, col=1)

# 볼린저 밴드
if show_bb:
    fig.add_trace(go.Scatter(
        x=pd.concat([hist.index.to_series(), hist.index.to_series()[::-1]]),
        y=pd.concat([hist["BB_upper"], hist["BB_lower"][::-1]]),
        fill="toself", fillcolor="rgba(88,166,255,0.07)",
        line=dict(color="rgba(0,0,0,0)"),
        name="볼린저 밴드",
        showlegend=True,
    ), row=1, col=1)
    for band, dash in [("BB_upper", "dot"), ("BB_lower", "dot")]:
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist[band],
            mode="lines",
            line=dict(color="#58a6ff", width=0.8, dash=dash),
            showlegend=False,
        ), row=1, col=1)

# 거래량
vol_colors = ["#3fb950" if c >= o else "#f85149"
              for c, o in zip(hist["Close"], hist["Open"])]
fig.add_trace(go.Bar(
    x=hist.index, y=hist["Volume"],
    name="거래량",
    marker_color=vol_colors,
    opacity=0.8,
), row=2, col=1)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0d1117",
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
    xaxis_rangeslider_visible=False,
    margin=dict(l=50, r=20, t=50, b=40),
    hovermode="x unified",
)
fig.update_yaxes(gridcolor="#21262d", row=1, col=1)
fig.update_yaxes(gridcolor="#21262d", row=2, col=1)
fig.update_xaxes(gridcolor="#21262d")

st.plotly_chart(fig, use_container_width=True)

# ── 추가 정보 ──────────────────────────────────────────────────────────────────
with st.expander("📋 기업 기본 정보", expanded=False):
    fields = {
        "섹터": info.get("sector"),
        "산업": info.get("industry"),
        "시가총액": f"{info.get('marketCap', 0):,}" if info.get("marketCap") else "-",
        "PER (TTM)": info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "배당 수익률": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get("dividendYield") else "-",
        "52주 고가": info.get("fiftyTwoWeekHigh"),
        "52주 저가": info.get("fiftyTwoWeekLow"),
        "홈페이지": info.get("website"),
    }
    df_info = pd.DataFrame(list(fields.items()), columns=["항목", "값"])
    st.dataframe(df_info, use_container_width=True, hide_index=True)
