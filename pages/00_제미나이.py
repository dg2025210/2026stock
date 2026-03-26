import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 페이지 기본 설정
st.set_page_config(page_title="한미 주식 수익률 비교 분석기", page_icon="📈", layout="wide")

st.title("📈 한미 주요 주식 수익률 비교 분석기")
st.markdown("한국과 미국의 주요 주식들의 기간별 누적 수익률을 한눈에 비교해 보세요.")

# 주요 주식 종목 (이름: 티커)
KOR_STOCKS = {
    "삼성전자": "005930.KS", 
    "SK하이닉스": "000660.KS", 
    "NAVER": "035420.KS", 
    "카카오": "035720.KS", 
    "현대차": "005380.KS",
    "에코프로비엠": "247540.KQ" # 코스닥은 .KQ
}

US_STOCKS = {
    "애플 (AAPL)": "AAPL", 
    "마이크로소프트 (MSFT)": "MSFT", 
    "엔비디아 (NVDA)": "NVDA", 
    "테슬라 (TSLA)": "TSLA", 
    "알파벳 (GOOGL)": "GOOGL",
    "S&P 500 ETF (SPY)": "SPY"
}

# --- 사이드바 설정 ---
st.sidebar.header("설정 (Settings)")

# 날짜 선택
today = datetime.today()
one_year_ago = today - timedelta(days=365)
start_date = st.sidebar.date_input("시작일", one_year_ago)
end_date = st.sidebar.date_input("종료일", today)

# 종목 다중 선택
selected_kor = st.sidebar.multiselect("한국 주식 선택", list(KOR_STOCKS.keys()), default=["삼성전자", "SK하이닉스"])
selected_us = st.sidebar.multiselect("미국 주식 선택", list(US_STOCKS.keys()), default=["애플 (AAPL)", "엔비디아 (NVDA)"])

# 선택된 티커 리스트 생성
tickers_to_download = [KOR_STOCKS[s] for s in selected_kor] + [US_STOCKS[s] for s in selected_us]
ticker_names = selected_kor + selected_us # 차트 범례용 이름

# --- 데이터 로딩 및 처리 ---
if not tickers_to_download:
    st.warning("👈 사이드바에서 최소 한 개 이상의 종목을 선택해 주세요.")
else:
    with st.spinner("주식 데이터를 불러오는 중입니다..."):
        # yfinance로 데이터 다운로드 (수정종가 기준)
        data = yf.download(tickers_to_download, start=start_date, end=end_date)['Close']
        
        # 종목이 하나일 경우 Series로 반환되므로 DataFrame으로 변환
        if isinstance(data, pd.Series):
            data = data.to_frame()
            
        # 열 이름을 보기 편한 회사 이름으로 변경
        # yfinance는 여러 종목 다운로드 시 컬럼이 정렬될 수 있으므로 매핑을 통해 안전하게 변경
        ticker_to_name = {v: k for k, v in KOR_STOCKS.items()}
        ticker_to_name.update({v: k for k, v in US_STOCKS.items()})
        data.rename(columns=ticker_to_name, inplace=True)
        
        # 결측치 처리 (앞의 데이터로 채우기)
        data = data.ffill().dropna()

        if data.empty:
            st.error("해당 기간의 데이터가 존재하지 않습니다. 날짜를 변경해 보세요.")
        else:
            # 기준일(첫 날) 대비 누적 수익률(%) 계산
            # (현재가 / 첫날가격 - 1) * 100
            returns = (data / data.iloc[0] - 1) * 100

            # --- 시각화 (Plotly) ---
            st.subheader("기간 내 누적 수익률 차트 (%)")
            
            # Plotly 포맷에 맞게 데이터 재구조화(Melt)
            returns_melted = returns.reset_index().melt(id_vars='Date', var_name='종목', value_name='수익률(%)')
            
            fig = px.line(returns_melted, x='Date', y='수익률(%)', color='종목', 
                          title=f"기준일: {returns.index[0].strftime('%Y-%m-%d')} (0%)")
            
            fig.update_layout(
                xaxis_title="날짜",
                yaxis_title="누적 수익률 (%)",
                hovermode="x unified",
                legend_title="선택한 종목"
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- 요약 데이터 표시 ---
            st.subheader("📊 종목별 요약 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**기간 내 최종 누적 수익률**")
                final_returns = returns.iloc[-1].sort_values(ascending=False).round(2)
                st.dataframe(final_returns.to_frame(name="수익률(%)"), use_container_width=True)
                
            with col2:
                st.markdown("**실제 주가 데이터 (종가 기준)**")
                st.dataframe(data.round(2).sort_index(ascending=False), use_container_width=True)
