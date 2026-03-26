import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="📈 글로벌 주식 비교 대시보드", layout="wide")

st.title("📊 한국 vs 미국 주식 수익률 비교")

# -----------------------------
# 기본 종목 리스트
# -----------------------------
default_tickers = {
    "한국": ["005930.KS", "000660.KS", "035420.KS"],  # 삼성전자, SK하이닉스, NAVER
    "미국": ["AAPL", "MSFT", "GOOGL"]
}

# -----------------------------
# 사용자 입력
# -----------------------------
st.sidebar.header("⚙️ 설정")

market = st.sidebar.multiselect(
    "시장 선택",
    ["한국", "미국"],
    default=["한국", "미국"]
)

tickers = []
for m in market:
    tickers += default_tickers[m]

custom_input = st.sidebar.text_input(
    "추가 티커 입력 (쉼표로 구분)",
    ""
)

if custom_input:
    tickers += [t.strip().upper() for t in custom_input.split(",")]

start_date = st.sidebar.date_input("시작 날짜", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("종료 날짜", pd.to_datetime("today"))

# -----------------------------
# 데이터 다운로드
# -----------------------------
@st.cache_data
def load_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end)["Adj Close"]
    return data

if len(tickers) == 0:
    st.warning("티커를 선택하세요!")
    st.stop()

data = load_data(tickers, start_date, end_date)

# -----------------------------
# 수익률 계산
# -----------------------------
returns = (data / data.iloc[0] - 1) * 100

# -----------------------------
# 차트 출력
# -----------------------------
st.subheader("📈 누적 수익률 비교 (%)")

fig, ax = plt.subplots(figsize=(12, 6))

for col in returns.columns:
    ax.plot(returns.index, returns[col], label=col)

ax.set_ylabel("수익률 (%)")
ax.legend()
ax.grid(True)

st.pyplot(fig)

# -----------------------------
# 데이터 테이블
# -----------------------------
st.subheader("📋 수익률 데이터")

st.dataframe(returns.tail())

# -----------------------------
# 개별 종목 상세 보기
# -----------------------------
st.subheader("🔍 개별 종목 상세")

selected_stock = st.selectbox("종목 선택", returns.columns)

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.plot(data.index, data[selected_stock])
ax2.set_title(f"{selected_stock} 가격 추이")
ax2.grid(True)

st.pyplot(fig2)

# -----------------------------
# 요약 통계
# -----------------------------
st.subheader("📊 요약 통계")

summary = pd.DataFrame({
    "총 수익률 (%)": returns.iloc[-1],
    "최고 수익률 (%)": returns.max(),
    "최저 수익률 (%)": returns.min()
})

st.dataframe(summary)
