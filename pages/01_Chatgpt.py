# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(page_title="📈 글로벌 주식 비교", layout="wide")

st.title("📊 한국 vs 미국 주식 수익률 비교 앱")
st.write("yfinance를 이용해 주요 주식의 성과를 비교합니다.")

# 기본 종목 리스트
korea_stocks = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS"
}

us_stocks = {
    "애플": "AAPL",
    "마이크로소프트": "MSFT",
    "테슬라": "TSLA",
    "엔비디아": "NVDA"
}

# 사용자 선택
st.sidebar.header("🔍 종목 선택")
selected_korea = st.sidebar.multiselect("🇰🇷 한국 주식", list(korea_stocks.keys()), default=["삼성전자"])
selected_us = st.sidebar.multiselect("🇺🇸 미국 주식", list(us_stocks.keys()), default=["애플"])

# 기간 선택
st.sidebar.header("📅 기간 설정")
end_date = datetime.date.today()
start_date = st.sidebar.date_input("시작일", end_date - datetime.timedelta(days=180))

# 티커 변환
selected_tickers = [korea_stocks[s] for s in selected_korea] + [us_stocks[s] for s in selected_us]

if selected_tickers:
    data = yf.download(selected_tickers, start=start_date, end=end_date)['Adj Close']
    
    if isinstance(data, pd.Series):
        data = data.to_frame()

    # 수익률 계산
    returns = (data / data.iloc[0] - 1) * 100

    st.subheader("📈 누적 수익률 (%)")
    st.line_chart(returns)

    st.subheader("📊 현재 수익률 비교")
    latest_returns = returns.iloc[-1].sort_values(ascending=False)
    st.bar_chart(latest_returns)

    # 데이터 테이블
    st.subheader("📋 데이터 테이블")
    st.dataframe(returns.round(2))

    # 개별 종목 상세
    st.subheader("🔎 개별 종목 상세 보기")
    selected_detail = st.selectbox("종목 선택", selected_tickers)

    stock = yf.Ticker(selected_detail)
    info = stock.info

    col1, col2 = st.columns(2)

    with col1:
        st.metric("현재가", info.get("currentPrice", "N/A"))
        st.metric("시가총액", info.get("marketCap", "N/A"))

    with col2:
        st.metric("PER", info.get("trailingPE", "N/A"))
        st.metric("배당수익률", info.get("dividendYield", "N/A"))

    hist = stock.history(period="6mo")
    st.line_chart(hist['Close'])

else:
    st.warning("하나 이상의 종목을 선택해주세요.")

st.success("🎉 앱이 정상적으로 실행 중입니다!")


# requirements.txt
# 아래 내용을 별도 파일로 저장하세요
"""
streamlit
yfinance
pandas
"""
