import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Finance Dashboard", layout="wide")

# AUTO REFRESH (30 mins)
st_autorefresh(interval=30 * 60 * 1000, key="refresh")

# API KEY (from Streamlit Secrets)
API_KEY = st.secrets["ALPHA_VANTAGE_API_KEY"]

# ---------------- HEADER ----------------
st.title("📊 Live Finance Dashboard")

# ---------------- SIDEBAR ----------------
symbol = st.sidebar.selectbox("Select Stock", ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"])
interval = st.sidebar.selectbox("Interval", ["5min", "15min", "30min", "60min"])

# ---------------- DATA ----------------
@st.cache_data(ttl=1800)
def load_data(symbol, interval):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={API_KEY}"
    r = requests.get(url)
    data = r.json()

    key = f"Time Series ({interval})"
    df = pd.DataFrame.from_dict(data.get(key, {}), orient='index')

    if df.empty:
        return df

    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    })

    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    return df

df = load_data(symbol, interval)

# ---------------- HANDLE EMPTY ----------------
if df.empty:
    st.error("⚠️ Data not loaded. Check API key or limit reached.")
    st.stop()

# ---------------- METRICS ----------------
latest = df.iloc[-1]
prev = df.iloc[-2]

price = latest["close"]
change = price - prev["close"]
pct = (change / prev["close"]) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Price", f"${price:.2f}", f"{pct:.2f}%")
c2.metric("📈 High", f"${df['high'].max():.2f}")
c3.metric("📉 Low", f"${df['low'].min():.2f}")
c4.metric("🔄 Volume", f"{int(latest['volume']):,}")

# ---------------- PRICE CHART ----------------
st.subheader("📈 Price Trend")
st.line_chart(df["close"])

# ---------------- MOVING AVERAGES ----------------
st.subheader("📉 Moving Averages")

df["MA20"] = df["close"].rolling(20).mean()
df["MA50"] = df["close"].rolling(50).mean()

ma_df = df[["close", "MA20", "MA50"]]
st.line_chart(ma_df)

# ---------------- VOLATILITY ----------------
st.subheader("⚡ Volatility")

df["returns"] = df["close"].pct_change()
volatility = df["returns"].std()

st.metric("Volatility", f"{volatility:.5f}")

# ---------------- ANOMALY ----------------
st.subheader("🚨 Anomaly Detection")

anomalies = df[df["returns"].abs() > 0.02]

if anomalies.empty:
    st.success("No anomalies detected ✅")
else:
    st.warning(f"{len(anomalies)} anomalies found")
    st.dataframe(anomalies.tail())

# ---------------- DIRECTION BAR ----------------
st.subheader("🔥 Market Direction")

df["direction"] = df["returns"].apply(lambda x: "Up" if x > 0 else "Down")
st.bar_chart(df["direction"].value_counts())

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Auto-refresh every 30 minutes")