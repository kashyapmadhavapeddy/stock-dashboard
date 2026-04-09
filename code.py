import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pandas_ta as ta
from streamlit_extras.metric_cards import style_metric_cards

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EquityPulse Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NEON GLASSMORPHISM UI ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(160deg, #0a0c10 0%, #1a1d24 100%);
    }
    
    /* Title Styling */
    .main-title {
        font-size: 45px;
        font-weight: 800;
        background: -webkit-linear-gradient(#00d1ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    /* Glass Cards */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 12, 16, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE (Auto-Refresh Logic) ---
@st.cache_data(ttl=1800) # Auto-refreshes every 30 minutes (1800 seconds)
def fetch_stock_data(ticker):
    try:
        # Fetch 1 month of hourly data for smooth trends
        df = yf.download(ticker, period="1mo", interval="1h")
        if df.empty:
            return None
        
        # Calculate Technical Metrics
        df.ta.rsi(append=True)
        df.ta.ema(length=20, append=True)
        # Volatility = Rolling Std Dev of returns
        df['Volatility'] = df['Close'].pct_change().rolling(window=10).std() * 100
        return df
    except Exception:
        return None

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2534/2534351.png", width=80)
    st.markdown("## Global Terminal")
    target_ticker = st.text_input("Enter Stock Ticker", value="AAPL").upper()
    
    st.markdown("---")
    st.write("**Refresh Interval:** 30 Minutes")
    st.write("**Data Source:** Yahoo Finance (Live)")
    
    if st.button("Manual Force Refresh"):
        st.cache_data.clear()
        st.rerun()

# --- HEADER ---
st.markdown(f'<h1 class="main-title">EquityPulse Terminal</h1>', unsafe_allow_html=True)
st.markdown(f"<p style='color:#8b949e;'>Real-time analysis for <b>{target_ticker}</b> | Last Sync: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

# --- DASHBOARD LOGIC ---
data = fetch_stock_data(target_ticker)

if data is not None:
    # Get Current Values
    curr = data.iloc[-1]
    prev = data.iloc[-2]
    price_change = curr['Close'] - prev['Close']
    pct_change = (price_change / prev['Close']) * 100

    # 1. TOP METRIC TILES
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Price", f"${curr['Close']:,.2f}", f"{pct_change:+.2f}%")
    col2.metric("Market RSI", f"{curr['RSI_14']:.1f}")
    col3.metric("EMA (20)", f"${curr['EMA_20']:,.2f}")
    col4.metric("Volatility", f"{curr['Volatility']:.2f}%")
    
    style_metric_cards(border_left_color="#00d1ff")

    # 2. MAIN CHART (Candlestick + EMA)
    st.markdown("### Market Momentum & Action")
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'],
        low=data['Low'], close=data['Close'], name="Price Action"
    ))
    
    # EMA Trendline
    fig.add_trace(go.Scatter(
        x=data.index, y=data['EMA_20'], 
        line=dict(color='#ff00ff', width=1.5), name="20-EMA Trend"
    ))

    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(t=30, b=0, l=0, r=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. SECONDARY ANALYTICS GRID
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 7-Day Volatility Trend")
        st.area_chart(data['Volatility'].tail(168), color="#00d1ff")

    with c2:
        st.markdown("#### Anomaly & Alert Center")
        if curr['RSI_14'] > 70:
            st.error(f"⚠️ **OVERBOUGHT ALERT:** {target_ticker} is showing extreme momentum. Potential pullback expected.")
        elif curr['RSI_14'] < 30:
            st.success(f"💎 **OVERSOLD ALERT:** {target_ticker} RSI is below 30. Possible buying opportunity.")
        else:
            st.info(f"✅ **STABLE:** Market movement for {target_ticker} is within healthy technical bounds.")
            
    # 4. DATA TABLE (Technical Summary)
    with st.expander("View Raw Technical Dataset"):
        st.dataframe(data.tail(20), use_container_width=True)

else:
    st.error(f"Could not retrieve data for '{target_ticker}'. Please ensure the ticker is valid (e.g., TSLA, NVDA, BTC-USD).")

# --- FOOTER ---
st.markdown("---")
st.caption("Developed by AI Team | Automated Real-Time Equity Pipeline | Streamlit Cloud Ready")