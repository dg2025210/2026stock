import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="글로벌 주식 비교 분석",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

    .main { background: #0d1117; }
    .stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #1c2333 100%);
        border-right: 1px solid #30363d;
    }

    /* 카드 */
    .metric-card {
        background: linear-gradient(135deg, #1c2333 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin: 6px 0;
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); border-color: #58a6ff; }

    .metric-label { color: #8b949e; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px; }
    .metric-value { font-size: 26px; font-weight: 700; color: #f0f6fc; }
    .metric-delta-pos { color: #3fb950; font-size: 14px; font-weight: 600; }
    .metric-delta-neg { color: #f85149; font-size: 14px; font-weight: 600; }

    /* 섹션 헤더 */
    .section-header {
        font-size: 20px; font-weight: 700; color: #f0f6fc;
        border-left: 4px solid #58a6ff;
        padding-left: 12px; margin: 24px 0 16px;
    }

    /* 배지 */
    .badge-kr { background: #1f6feb33; color: #58a6ff; border: 1px solid #1f6feb; border-radius: 20px; padding: 2px 10px; font-size: 11px; font-weight: 600; }
    .badge-us { background: #3fb95033; color: #3fb950; border: 1px solid #3fb950; border-radius: 20px; padding: 2px 10px; font-size: 11px; font-weight: 600; }

    /* Streamlit 기본 요소 오버라이드 */
    .stSelectbox > div > div { background: #21262d; border: 1px solid #30363d; color: #f0f6fc; }
    .stMultiSelect > div > div { background: #21262d; border: 1px solid #30363d; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { background: #161b22; border-radius: 8px; border: 1px solid #30363d; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; }
    .stTabs [aria-selected="true"] { color: #58a6ff !important; background: #1c2333; border-radius: 6px; }

    hr { border-color: #30363d; }

    /* 테이블 */
    .dataframe { background: #161b22 !important; color: #f0f6fc !important; }
</style>
""", unsafe_allow_html=True)

# ── 주식 데이터 정의 ─────────────────────────────────────────
KR_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "셀트리온": "068270.KS",
    "POSCO홀딩스": "005490.KS",
    "KB금융": "105560.KS",
}

US_STOCKS = {
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Meta": "META",
    "Alphabet (Google)": "GOOGL",
    "Berkshire Hathaway": "BRK-B",
    "Broadcom": "AVGO",
    "JPMorgan Chase": "JPM",
}

INDICES = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI",
}

PERIODS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}

# ── 데이터 로드 함수 ─────────────────────────────────────────
@st.cache_data(ttl=300)
def get_stock_data(ticker: str, period: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_stock_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).fast_info
        return {
            "market_cap": getattr(info, "market_cap", None),
            "last_price": getattr(info, "last_price", None),
            "previous_close": getattr(info, "previous_close", None),
            "52w_high": getattr(info, "year_high", None),
            "52w_low": getattr(info, "year_low", None),
        }
    except Exception:
        return {}

def calc_returns(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 2:
        return {}
    close = df["Close"].squeeze()
    total_ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
    daily_rets = close.pct_change().dropna()
    volatility = daily_rets.std() * np.sqrt(252) * 100
    max_dd = ((close / close.cummax()) - 1).min() * 100
    sharpe = (daily_rets.mean() / daily_rets.std() * np.sqrt(252)) if daily_rets.std() > 0 else 0
    return {
        "total_return": round(total_ret, 2),
        "volatility": round(volatility, 2),
        "max_drawdown": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "current_price": round(float(close.iloc[-1]), 2),
        "start_price": round(float(close.iloc[0]), 2),
    }

def normalize_series(df: pd.DataFrame) -> pd.Series:
    close = df["Close"].squeeze()
    return (close / close.iloc[0]) * 100

# ── 차트 함수 ────────────────────────────────────────────────
CHART_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(13,17,23,0.6)",
    "font_color": "#8b949e",
    "gridcolor": "#21262d",
}

def make_candlestick(df: pd.DataFrame, name: str) -> go.Figure:
    fig = go.Figure(go.Candlestick(
        x=df.index,
        open=df["Open"].squeeze(),
        high=df["High"].squeeze(),
        low=df["Low"].squeeze(),
        close=df["Close"].squeeze(),
        name=name,
        increasing_line_color="#3fb950",
        decreasing_line_color="#f85149",
    ))
    vol_colors = ["#3fb95088" if df["Close"].squeeze().iloc[i] >= df["Open"].squeeze().iloc[i]
                  else "#f8514988" for i in range(len(df))]
    fig.add_bar(
        x=df.index, y=df["Volume"].squeeze(),
        marker_color=vol_colors, name="거래량", yaxis="y2", opacity=0.5
    )
    fig.update_layout(
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"]),
        xaxis=dict(gridcolor=CHART_THEME["gridcolor"], rangeslider_visible=False, showspikes=True),
        yaxis=dict(gridcolor=CHART_THEME["gridcolor"], side="right", domain=[0.25, 1], title=f"{name} 가격"),
        yaxis2=dict(domain=[0, 0.2], gridcolor=CHART_THEME["gridcolor"], title="거래량"),
        legend=dict(bgcolor="#1c2333", bordercolor="#30363d"),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=20, b=10),
        height=480,
    )
    return fig

def make_normalized_chart(data_dict: dict, colors_dict: dict) -> go.Figure:
    fig = go.Figure()
    for name, series in data_dict.items():
        fig.add_scatter(
            x=series.index, y=series.values,
            name=name, line=dict(width=2, color=colors_dict.get(name)),
            hovertemplate=f"<b>{name}</b><br>%{{y:.1f}}<extra></extra>",
        )
    fig.add_hline(y=100, line_dash="dot", line_color="#8b949e", opacity=0.5)
    fig.update_layout(
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"]),
        xaxis=dict(gridcolor=CHART_THEME["gridcolor"], showspikes=True),
        yaxis=dict(gridcolor=CHART_THEME["gridcolor"], title="정규화 수익률 (기준=100)", ticksuffix=""),
        legend=dict(bgcolor="#1c2333", bordercolor="#30363d", orientation="h", y=-0.15),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=20, b=10),
        height=420,
    )
    return fig

def make_bar_comparison(names, returns, colors) -> go.Figure:
    bar_colors = ["#3fb950" if r >= 0 else "#f85149" for r in returns]
    fig = go.Figure(go.Bar(
        x=names, y=returns,
        marker_color=bar_colors,
        text=[f"{r:+.1f}%" for r in returns],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>수익률: %{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"]),
        xaxis=dict(gridcolor=CHART_THEME["gridcolor"], tickangle=-30),
        yaxis=dict(gridcolor=CHART_THEME["gridcolor"], title="수익률 (%)", ticksuffix="%"),
        margin=dict(l=10, r=10, t=30, b=80),
        height=380,
    )
    return fig

def make_scatter(stats_list) -> go.Figure:
    fig = go.Figure()
    for s in stats_list:
        fig.add_scatter(
            x=[s["volatility"]], y=[s["total_return"]],
            mode="markers+text",
            name=s["name"],
            text=[s["name"]],
            textposition="top center",
            marker=dict(size=14, symbol="circle",
                        color="#58a6ff" if s["market"] == "KR" else "#3fb950",
                        line=dict(width=1, color="#0d1117")),
            hovertemplate=(
                f"<b>{s['name']}</b><br>"
                "변동성: %{x:.1f}%<br>수익률: %{y:.1f}%<extra></extra>"
            ),
        )
    fig.add_hline(y=0, line_dash="dot", line_color="#8b949e", opacity=0.5)
    fig.update_layout(
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"]),
        xaxis=dict(gridcolor=CHART_THEME["gridcolor"], title="연간 변동성 (%)"),
        yaxis=dict(gridcolor=CHART_THEME["gridcolor"], title="수익률 (%)"),
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=10),
        height=380,
    )
    return fig

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px;'>
        <div style='font-size:40px;'>📈</div>
        <div style='font-size:20px; font-weight:700; color:#f0f6fc;'>글로벌 주식 분석</div>
        <div style='font-size:12px; color:#8b949e; margin-top:4px;'>Korea & US Market</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    period_label = st.selectbox("📅 분석 기간", list(PERIODS.keys()), index=3)
    period = PERIODS[period_label]

    st.markdown("#### 🇰🇷 한국 주식")
    kr_selected = st.multiselect(
        "종목 선택", list(KR_STOCKS.keys()),
        default=["삼성전자", "SK하이닉스", "NAVER"],
        label_visibility="collapsed"
    )

    st.markdown("#### 🇺🇸 미국 주식")
    us_selected = st.multiselect(
        "종목 선택", list(US_STOCKS.keys()),
        default=["Apple", "NVIDIA", "Tesla"],
        label_visibility="collapsed"
    )

    show_index = st.checkbox("지수 포함 (KOSPI / S&P 500)", value=True)
    st.divider()
    st.markdown("<div style='color:#8b949e; font-size:11px;'>📡 데이터: Yahoo Finance<br>🔄 캐시: 5분 갱신</div>", unsafe_allow_html=True)

# ── 데이터 수집 ──────────────────────────────────────────────
all_names = kr_selected + us_selected
all_tickers = {n: KR_STOCKS[n] for n in kr_selected}
all_tickers.update({n: US_STOCKS[n] for n in us_selected})

if not all_names:
    st.warning("사이드바에서 분석할 종목을 선택해주세요.")
    st.stop()

with st.spinner("📡 시장 데이터 불러오는 중..."):
    raw_data = {name: get_stock_data(ticker, period) for name, ticker in all_tickers.items()}
    stats_map = {name: calc_returns(df) for name, df in raw_data.items()}

# 색상 팔레트
KR_COLORS = ["#58a6ff", "#1f6feb", "#388bfd", "#79c0ff", "#a5d6ff", "#cae8ff"]
US_COLORS = ["#3fb950", "#2ea043", "#56d364", "#7ee787", "#aff5b4", "#d1f5d3"]
color_map = {}
for i, n in enumerate(kr_selected):
    color_map[n] = KR_COLORS[i % len(KR_COLORS)]
for i, n in enumerate(us_selected):
    color_map[n] = US_COLORS[i % len(US_COLORS)]

# ── 메인 콘텐츠 ──────────────────────────────────────────────
st.markdown(f"""
<div style='padding: 8px 0 24px;'>
    <h1 style='color:#f0f6fc; font-size:28px; font-weight:700; margin:0;'>📊 글로벌 주식 비교 분석</h1>
    <div style='color:#8b949e; font-size:14px; margin-top:6px;'>분석 기간: <b style='color:#58a6ff;'>{period_label}</b> | 선택 종목: <b style='color:#f0f6fc;'>{len(all_names)}개</b></div>
</div>
""", unsafe_allow_html=True)

# ── 탭 ───────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 수익률 비교", "🕯️ 개별 차트", "📊 리스크 분석", "📋 데이터 테이블"])

# ─── TAB 1: 수익률 비교 ──────────────────────────────────────
with tab1:
    # 정규화 차트
    st.markdown('<div class="section-header">정규화 수익률 추이</div>', unsafe_allow_html=True)
    norm_data = {}
    if show_index:
        for idx_name, idx_ticker in [("KOSPI", "^KS11"), ("S&P500", "^GSPC")]:
            df_idx = get_stock_data(idx_ticker, period)
            if not df_idx.empty:
                norm_data[idx_name] = normalize_series(df_idx)
                color_map[idx_name] = "#f0883e" if idx_name == "KOSPI" else "#bc8cff"

    for name, df in raw_data.items():
        if not df.empty:
            norm_data[name] = normalize_series(df)

    if norm_data:
        st.plotly_chart(make_normalized_chart(norm_data, color_map), use_container_width=True)

    # 수익률 바 차트
    st.markdown('<div class="section-header">기간 수익률 순위</div>', unsafe_allow_html=True)
    valid_stats = [(n, stats_map[n]) for n in all_names if stats_map.get(n)]
    valid_stats.sort(key=lambda x: x[1]["total_return"], reverse=True)

    if valid_stats:
        names_sorted = [x[0] for x in valid_stats]
        returns_sorted = [x[1]["total_return"] for x in valid_stats]
        colors_sorted = [color_map.get(n, "#58a6ff") for n in names_sorted]
        st.plotly_chart(make_bar_comparison(names_sorted, returns_sorted, colors_sorted), use_container_width=True)

    # 지표 카드
    st.markdown('<div class="section-header">핵심 지표 요약</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(valid_stats), 4))
    for i, (name, s) in enumerate(valid_stats[:8]):
        ret = s["total_return"]
        market = "KR" if name in kr_selected else "US"
        badge = f'<span class="badge-kr">🇰🇷 KR</span>' if market == "KR" else f'<span class="badge-us">🇺🇸 US</span>'
        delta_cls = "metric-delta-pos" if ret >= 0 else "metric-delta-neg"
        delta_sym = "▲" if ret >= 0 else "▼"
        with cols[i % 4]:
            st.markdown(f"""
            <div class="metric-card">
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <span style='color:#f0f6fc; font-weight:700; font-size:14px;'>{name}</span>
                    {badge}
                </div>
                <div class="metric-label">수익률 ({period_label})</div>
                <div class="{delta_cls}" style='font-size:22px; font-weight:700;'>{delta_sym} {abs(ret):.2f}%</div>
                <div style='margin-top:10px; display:flex; gap:16px;'>
                    <div><div class="metric-label">변동성</div><div style='color:#f0f6fc; font-size:13px;'>{s["volatility"]:.1f}%</div></div>
                    <div><div class="metric-label">샤프비율</div><div style='color:#f0f6fc; font-size:13px;'>{s["sharpe"]:.2f}</div></div>
                    <div><div class="metric-label">MDD</div><div style='color:#f85149; font-size:13px;'>{s["max_drawdown"]:.1f}%</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─── TAB 2: 개별 차트 ────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">캔들스틱 차트</div>', unsafe_allow_html=True)
    chart_choice = st.selectbox("종목 선택", all_names, key="chart_select")
    if chart_choice and not raw_data[chart_choice].empty:
        df_c = raw_data[chart_choice]
        s = stats_map.get(chart_choice, {})
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("현재가", f"{s.get('current_price', '-'):,.2f}")
        with c2:
            ret = s.get("total_return", 0)
            st.metric("기간 수익률", f"{ret:+.2f}%", delta=f"{ret:+.2f}%")
        with c3: st.metric("연간 변동성", f"{s.get('volatility', '-'):.1f}%")
        with c4: st.metric("최대 낙폭", f"{s.get('max_drawdown', '-'):.1f}%")
        st.plotly_chart(make_candlestick(df_c, chart_choice), use_container_width=True)

        # 이동평균선
        close = df_c["Close"].squeeze()
        fig_ma = go.Figure()
        fig_ma.add_scatter(x=close.index, y=close, name="종가", line=dict(color=color_map.get(chart_choice, "#58a6ff"), width=1.5))
        for ma, col in [(20, "#f0883e"), (60, "#bc8cff"), (120, "#3fb950")]:
            if len(close) >= ma:
                fig_ma.add_scatter(x=close.index, y=close.rolling(ma).mean(), name=f"MA{ma}", line=dict(width=1.5, dash="dot", color=col))
        fig_ma.update_layout(
            paper_bgcolor=CHART_THEME["paper_bgcolor"], plot_bgcolor=CHART_THEME["plot_bgcolor"],
            font=dict(color=CHART_THEME["font_color"]),
            xaxis=dict(gridcolor=CHART_THEME["gridcolor"]),
            yaxis=dict(gridcolor=CHART_THEME["gridcolor"], side="right"),
            legend=dict(bgcolor="#1c2333", bordercolor="#30363d", orientation="h", y=-0.15),
            hovermode="x unified", margin=dict(l=10, r=10, t=20, b=10), height=340,
            title=dict(text="이동평균선", font=dict(color="#f0f6fc", size=14))
        )
        st.plotly_chart(fig_ma, use_container_width=True)

# ─── TAB 3: 리스크 분석 ──────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">리스크-수익률 산점도</div>', unsafe_allow_html=True)
    scatter_list = []
    for name, s in stats_map.items():
        if s:
            scatter_list.append({**s, "name": name, "market": "KR" if name in kr_selected else "US"})
    if scatter_list:
        st.plotly_chart(make_scatter(scatter_list), use_container_width=True)
        st.markdown("<div style='color:#8b949e; font-size:12px; text-align:center;'>🔵 한국 주식 &nbsp;|&nbsp; 🟢 미국 주식</div>", unsafe_allow_html=True)

    # 한/미 평균 비교
    st.markdown('<div class="section-header">한국 vs 미국 평균 비교</div>', unsafe_allow_html=True)
    kr_stats = [stats_map[n] for n in kr_selected if stats_map.get(n)]
    us_stats = [stats_map[n] for n in us_selected if stats_map.get(n)]

    def avg(lst, key): return np.mean([s[key] for s in lst]) if lst else 0

    metrics = ["수익률", "변동성", "샤프비율"]
    kr_vals = [avg(kr_stats, "total_return"), avg(kr_stats, "volatility"), avg(kr_stats, "sharpe")]
    us_vals = [avg(us_stats, "total_return"), avg(us_stats, "volatility"), avg(us_stats, "sharpe")]

    fig_comp = go.Figure()
    fig_comp.add_bar(name="🇰🇷 한국", x=metrics, y=kr_vals, marker_color="#58a6ff",
                     text=[f"{v:.2f}" for v in kr_vals], textposition="outside")
    fig_comp.add_bar(name="🇺🇸 미국", x=metrics, y=us_vals, marker_color="#3fb950",
                     text=[f"{v:.2f}" for v in us_vals], textposition="outside")
    fig_comp.update_layout(
        paper_bgcolor=CHART_THEME["paper_bgcolor"], plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"]),
        xaxis=dict(gridcolor=CHART_THEME["gridcolor"]),
        yaxis=dict(gridcolor=CHART_THEME["gridcolor"]),
        legend=dict(bgcolor="#1c2333", bordercolor="#30363d"),
        barmode="group", margin=dict(l=10, r=10, t=20, b=10), height=340,
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# ─── TAB 4: 데이터 테이블 ─────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">종목별 상세 지표</div>', unsafe_allow_html=True)
    rows = []
    for name in all_names:
        s = stats_map.get(name)
        if s:
            rows.append({
                "종목": name,
                "시장": "🇰🇷 KR" if name in kr_selected else "🇺🇸 US",
                "티커": all_tickers[name],
                f"수익률({period_label})": f"{s['total_return']:+.2f}%",
                "현재가": f"{s['current_price']:,.2f}",
                "시작가": f"{s['start_price']:,.2f}",
                "연간변동성": f"{s['volatility']:.1f}%",
                "샤프비율": f"{s['sharpe']:.2f}",
                "MDD": f"{s['max_drawdown']:.1f}%",
            })
    if rows:
        df_table = pd.DataFrame(rows)
        st.dataframe(df_table, use_container_width=True, hide_index=True,
                     column_config={"종목": st.column_config.TextColumn(width="medium")})

    # 최근 가격 데이터
    st.markdown('<div class="section-header">최근 가격 데이터</div>', unsafe_allow_html=True)
    raw_choice = st.selectbox("종목 선택", all_names, key="raw_select")
    if raw_choice and not raw_data[raw_choice].empty:
        df_show = raw_data[raw_choice][["Open", "High", "Low", "Close", "Volume"]].tail(20).copy()
        df_show.index = df_show.index.strftime("%Y-%m-%d")
        df_show.columns = ["시가", "고가", "저가", "종가", "거래량"]
        df_show = df_show.round(2)
        st.dataframe(df_show[::-1], use_container_width=True)

# ── 푸터 ─────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#484f58; font-size:12px; margin-top:40px; padding:20px; border-top:1px solid #21262d;'>
    📊 데이터 출처: Yahoo Finance (yfinance) &nbsp;|&nbsp; 본 정보는 투자 참고용이며 투자 권유가 아닙니다
</div>
""", unsafe_allow_html=True)
