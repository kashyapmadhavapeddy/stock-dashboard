import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Finance Dashboard", layout="wide")

# AUTO REFRESH EVERY 30 MIN
st_autorefresh(interval=30 * 60 * 1000, key="refresh")

# GET API KEY FROM SECRETS
API_KEY = st.secrets["ALPHA_VANTAGE_API_KEY"]

# ---------------- STYLE ----------------
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1e293b, #020617);
    padding: 20px;
    border-radius: 15px;
    color: white;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
}
.title {
    font-size: 38px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown('<div class="title">📊 Live Finance Dashboard</div>', unsafe_allow_html=True)

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
    df = pd.DataFrame.from_dict(data[key], orient='index')

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

# ---------------- CANDLESTICK ----------------
st.subheader("📊 Market View")

fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close']
)])

fig.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig, use_container_width=True)

# ---------------- MOVING AVERAGES ----------------
st.subheader("📉 Trend Indicators")

df["MA20"] = df["close"].rolling(20).mean()
df["MA50"] = df["close"].rolling(50).mean()

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df.index, y=df["close"], name="Price"))
fig2.add_trace(go.Scatter(x=df.index, y=df["MA20"], name="MA20"))
fig2.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA50"))

fig2.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig2, use_container_width=True)

# ---------------- VOLATILITY ----------------
st.subheader("⚡ Volatility")

df["returns"] = df["close"].pct_change()
volatility = df["returns"].std()

st.metric("Volatility", f"{volatility:.5f}")

# ---------------- ANOMALY ----------------
st.subheader("🚨 Alerts")

anomalies = df[df["returns"].abs() > 0.02]

if anomalies.empty:
    st.success("No anomalies detected")
else:
    st.error(f"{len(anomalies)} anomalies detected")
    st.dataframe(anomalies.tail())

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Auto-refresh every 30 minutes enabled")