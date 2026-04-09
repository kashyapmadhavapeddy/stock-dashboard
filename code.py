"""
╔══════════════════════════════════════════════════════════╗
║         NEXUS — Real-Time Stock Intelligence Dashboard   ║
║         API: yfinance (Yahoo Finance) — No key needed    ║
║         Auto-refresh: every 30 minutes                   ║
╚══════════════════════════════════════════════════════════╝
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import pytz
import time

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS · Stock Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  AUTO-REFRESH EVERY 30 MINUTES (pure Streamlit)
# ─────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
    st.session_state.refresh_count = 0

elapsed = time.time() - st.session_state.last_refresh
if elapsed >= 1800:
    st.session_state.last_refresh = time.time()
    st.session_state.refresh_count += 1
    st.cache_data.clear()
    st.rerun()

refresh_count = st.session_state.refresh_count

# ─────────────────────────────────────────────
#  GLOBAL CSS — Dark luxury aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg:        #080c14;
    --surface:   #0d1320;
    --surface2:  #111827;
    --border:    #1e2d42;
    --accent:    #00d4ff;
    --accent2:   #7c3aed;
    --green:     #00e676;
    --red:       #ff3d57;
    --gold:      #fbbf24;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --font-head: 'Syne', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: var(--font-mono);
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.main { background: var(--bg) !important; }
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 1600px; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: var(--font-mono) !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    transition: border-color .25s;
}
[data-testid="stMetric"]:hover { border-color: var(--accent) !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: .7rem !important; letter-spacing: .12em; text-transform: uppercase; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-size: 1.6rem !important; font-family: var(--font-head) !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { font-size: .8rem !important; }

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-family: var(--font-mono) !important;
    font-size: .75rem !important;
    letter-spacing: .08em;
    color: var(--muted) !important;
    border-bottom: 2px solid transparent !important;
    padding: .5rem 1.2rem !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}

/* ── Selectbox & inputs ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--font-mono) !important;
}

/* ── Hero header ── */
.nexus-header {
    background: linear-gradient(135deg, #080c14 0%, #0d1320 40%, #0a1628 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.nexus-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,212,255,.12) 0%, transparent 70%);
    pointer-events: none;
}
.nexus-header::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 30%;
    width: 300px; height: 100px;
    background: radial-gradient(ellipse, rgba(124,58,237,.08) 0%, transparent 70%);
    pointer-events: none;
}
.nexus-title {
    font-family: var(--font-head);
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -.02em;
    color: #fff;
    margin: 0 0 .2rem;
}
.nexus-title span { color: var(--accent); }
.nexus-sub {
    font-family: var(--font-mono);
    font-size: .72rem;
    color: var(--muted);
    letter-spacing: .15em;
    text-transform: uppercase;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    background: rgba(0,230,118,.1);
    border: 1px solid rgba(0,230,118,.3);
    border-radius: 20px;
    padding: .25rem .75rem;
    font-size: .65rem;
    color: var(--green);
    letter-spacing: .1em;
    text-transform: uppercase;
    font-family: var(--font-mono);
}
.live-dot {
    width: 6px; height: 6px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse 1.6s infinite;
}
@keyframes pulse {
    0%,100% { opacity: 1; transform: scale(1); }
    50%      { opacity: .4; transform: scale(.7); }
}

/* ── Section labels ── */
.section-label {
    font-family: var(--font-mono);
    font-size: .65rem;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--muted);
    border-left: 2px solid var(--accent);
    padding-left: .6rem;
    margin-bottom: .75rem;
}

/* ── Anomaly alert box ── */
.alert-box {
    background: rgba(255,61,87,.07);
    border: 1px solid rgba(255,61,87,.3);
    border-radius: 10px;
    padding: .75rem 1rem;
    font-size: .75rem;
    color: #fca5a5;
    font-family: var(--font-mono);
    margin-bottom: .5rem;
}
.alert-box strong { color: var(--red); }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
WATCHLIST = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "META": "Meta",
    "JPM": "JPMorgan",
    "BRK-B": "Berkshire",
    "SPY": "S&P 500 ETF",
}

PERIOD_OPTIONS = {
    "1 Day": ("1d", "5m"),
    "5 Days": ("5d", "15m"),
    "1 Month": ("1mo", "1h"),
    "3 Months": ("3mo", "1d"),
    "6 Months": ("6mo", "1d"),
    "1 Year": ("1y", "1wk"),
}

COLOR_UP   = "#00e676"
COLOR_DOWN = "#ff3d57"
COLOR_NEUT = "#00d4ff"
PLOT_BG    = "#0d1320"
GRID_COLOR = "#1e2d42"


@st.cache_data(ttl=1800)   # cache for 30 minutes
def fetch_ticker(symbol: str, period: str = "1mo", interval: str = "1d"):
    tk = yf.Ticker(symbol)
    df = tk.history(period=period, interval=interval)
    info = tk.fast_info
    return df, info


def color_delta(val):
    if val > 0:  return f"<span style='color:#00e676'>▲ {val:+.2f}%</span>"
    if val < 0:  return f"<span style='color:#ff3d57'>▼ {val:.2f}%</span>"
    return f"<span style='color:#64748b'>– {val:.2f}%</span>"


def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def compute_volatility(df):
    """Annualised historical volatility (30-day window)."""
    log_ret = np.log(df["Close"] / df["Close"].shift(1))
    return log_ret.rolling(30).std() * np.sqrt(252) * 100


def detect_anomalies(df, z_thresh=2.5):
    ret = df["Close"].pct_change()
    mu, sigma = ret.mean(), ret.std()
    z = (ret - mu) / sigma
    return df[z.abs() > z_thresh]


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)
    
    symbol = st.selectbox(
        "Primary Symbol",
        list(WATCHLIST.keys()),
        format_func=lambda x: f"{x}  —  {WATCHLIST[x]}",
    )
    
    compare_syms = st.multiselect(
        "Compare With",
        [k for k in WATCHLIST if k != symbol],
        default=[],
        max_selections=3,
    )
    
    period_label = st.selectbox("Time Range", list(PERIOD_OPTIONS.keys()), index=2)
    period, interval = PERIOD_OPTIONS[period_label]
    
    st.markdown("---")
    st.markdown('<div class="section-label">Overlays</div>', unsafe_allow_html=True)
    show_ma      = st.checkbox("Moving Averages (20 / 50)", value=True)
    show_bollinger = st.checkbox("Bollinger Bands", value=False)
    show_volume  = st.checkbox("Volume Bars", value=True)
    show_rsi     = st.checkbox("RSI (14)", value=False)
    show_vol_idx = st.checkbox("Volatility Index", value=False)
    
    st.markdown("---")
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    st.markdown(f"""
    <div style="font-size:.65rem; color:#475569; line-height:1.8;">
        <div style="color:#94a3b8; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.4rem;">System</div>
        🕐 {now.strftime('%H:%M:%S IST')}<br>
        🔄 Refresh #<strong style="color:#00d4ff">{refresh_count}</strong><br>
        ⏱ Next in ~30 min<br>
        📡 Source: Yahoo Finance
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
company = WATCHLIST.get(symbol, symbol)
st.markdown(f"""
<div class="nexus-header">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
    <div>
      <div class="nexus-title">NEXUS <span>·</span> {symbol}</div>
      <div class="nexus-sub">{company} &nbsp;·&nbsp; Real-Time Stock Intelligence &nbsp;·&nbsp; {period_label}</div>
    </div>
    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:.5rem;">
      <div class="live-badge"><div class="live-dot"></div>Live Data</div>
      <div style="font-size:.65rem; color:#475569;">Auto-refresh every 30 min</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  FETCH DATA
# ─────────────────────────────────────────────
with st.spinner("Fetching market data…"):
    df, info = fetch_ticker(symbol, period, interval)

if df.empty:
    st.error("⚠️ No data returned. Check the symbol or try again.")
    st.stop()

latest   = df["Close"].iloc[-1]
prev     = df["Close"].iloc[-2] if len(df) > 1 else latest
day_chg  = (latest - prev) / prev * 100
high_52w = df["Close"].rolling(min(252, len(df))).max().iloc[-1]
low_52w  = df["Close"].rolling(min(252, len(df))).min().iloc[-1]
avg_vol  = df["Volume"].mean() if "Volume" in df else 0
cur_vol  = df["Volume"].iloc[-1] if "Volume" in df else 0


# ─────────────────────────────────────────────
#  KPI METRICS ROW
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Key Metrics</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Current Price",  f"${latest:,.2f}", f"{day_chg:+.2f}%")
k2.metric("Period High",    f"${df['High'].max():,.2f}")
k3.metric("Period Low",     f"${df['Low'].min():,.2f}")
k4.metric("52W High",       f"${high_52w:,.2f}")
k5.metric("52W Low",        f"${low_52w:,.2f}")
vol_delta = ((cur_vol - avg_vol) / avg_vol * 100) if avg_vol else 0
k6.metric("Volume vs Avg",  f"{vol_delta:+.1f}%", "↑ High" if vol_delta > 20 else ("↓ Low" if vol_delta < -20 else "Normal"))


st.markdown("---")


# ─────────────────────────────────────────────
#  ANOMALY ALERTS
# ─────────────────────────────────────────────
anomalies = detect_anomalies(df)
if not anomalies.empty:
    st.markdown('<div class="section-label">Anomaly Alerts</div>', unsafe_allow_html=True)
    for idx, row in anomalies.tail(3).iterrows():
        date_str = idx.strftime("%b %d, %Y") if hasattr(idx, "strftime") else str(idx)
        pct = (row["Close"] - df["Close"].shift(1).loc[idx]) / df["Close"].shift(1).loc[idx] * 100 if idx in df.index else 0
        st.markdown(f"""
        <div class="alert-box">
            ⚠ <strong>Anomaly Detected</strong> on {date_str} — 
            Close: <strong>${row['Close']:.2f}</strong> — 
            Unusual price movement detected (Z-score &gt; 2.5)
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN CHART TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊  Price Chart", "📈  Technical", "🌐  Comparison", "📉  Volatility"])

# ── Plotly theme base ──
layout_base = dict(
    paper_bgcolor=PLOT_BG,
    plot_bgcolor=PLOT_BG,
    font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
    xaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False,
               showspikes=True, spikecolor="#1e2d42", spikethickness=1),
    yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False,
               showspikes=True, spikecolor="#1e2d42", spikethickness=1),
    hovermode="x unified",
    legend=dict(bgcolor="rgba(13,19,32,.8)", bordercolor=GRID_COLOR, borderwidth=1),
    margin=dict(l=10, r=10, t=30, b=10),
)


# ─── TAB 1: Candlestick + Volume ───
with tab1:
    rows = 2 if show_volume else 1
    row_heights = [0.75, 0.25] if show_volume else [1]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"],  close=df["Close"],
        name=symbol,
        increasing=dict(fillcolor=COLOR_UP,   line=dict(color=COLOR_UP,   width=1)),
        decreasing=dict(fillcolor=COLOR_DOWN,  line=dict(color=COLOR_DOWN, width=1)),
    ), row=1, col=1)

    # Moving averages
    if show_ma:
        for window, color in [(20, "#00d4ff"), (50, "#fbbf24")]:
            ma = df["Close"].rolling(window).mean()
            fig.add_trace(go.Scatter(
                x=df.index, y=ma, name=f"MA{window}",
                line=dict(color=color, width=1.5, dash="dot"),
                opacity=0.85,
            ), row=1, col=1)

    # Bollinger Bands
    if show_bollinger:
        ma20   = df["Close"].rolling(20).mean()
        std20  = df["Close"].rolling(20).std()
        upper  = ma20 + 2 * std20
        lower  = ma20 - 2 * std20
        for y, nm, c in [(upper, "BB Upper", "#7c3aed"), (lower, "BB Lower", "#7c3aed")]:
            fig.add_trace(go.Scatter(
                x=df.index, y=y, name=nm,
                line=dict(color=c, width=1, dash="dash"),
                opacity=0.6,
            ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=list(df.index) + list(df.index[::-1]),
            y=list(upper) + list(lower[::-1]),
            fill="toself", fillcolor="rgba(124,58,237,.06)",
            line=dict(width=0), name="BB Band", showlegend=False,
        ), row=1, col=1)

    # Anomaly markers
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies.index, y=anomalies["Close"],
            mode="markers",
            marker=dict(symbol="x", size=12, color=COLOR_DOWN, line=dict(width=2)),
            name="Anomaly",
        ), row=1, col=1)

    # Volume bars
    if show_volume and "Volume" in df:
        colors = [COLOR_UP if c >= o else COLOR_DOWN
                  for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=colors, name="Volume",
            opacity=0.6,
        ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1,
                         title_font=dict(size=9))

    fig.update_layout(
        **layout_base,
        height=560,
        xaxis_rangeslider_visible=False,
        title=dict(text=f"{symbol} — {company}",
                   font=dict(family="Syne, sans-serif", size=14, color="#e2e8f0")),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── TAB 2: Technical Indicators ───
with tab2:
    sub_rows = 1 + int(show_rsi) + int(show_vol_idx)
    heights  = ([0.5] + [0.25] * (sub_rows - 1)) if sub_rows > 1 else [1]

    fig2 = make_subplots(rows=sub_rows, cols=1,
                         shared_xaxes=True,
                         vertical_spacing=0.04,
                         row_heights=heights)

    # Price line
    fig2.add_trace(go.Scatter(
        x=df.index, y=df["Close"], name="Close",
        line=dict(color=COLOR_NEUT, width=2),
        fill="tozeroy", fillcolor="rgba(0,212,255,.05)",
    ), row=1, col=1)

    cur_row = 2
    if show_rsi:
        rsi = compute_rsi(df["Close"])
        fig2.add_trace(go.Scatter(
            x=df.index, y=rsi, name="RSI(14)",
            line=dict(color="#fbbf24", width=1.5),
        ), row=cur_row, col=1)
        for level, col in [(70, "rgba(255,61,87,.3)"), (30, "rgba(0,230,118,.3)")]:
            fig2.add_hline(y=level, line_dash="dot", line_color=col,
                           row=cur_row, col=1)
        fig2.update_yaxes(title_text="RSI", row=cur_row, col=1,
                          range=[0, 100], title_font=dict(size=9))
        cur_row += 1

    if show_vol_idx:
        vol_idx = compute_volatility(df)
        fig2.add_trace(go.Scatter(
            x=df.index, y=vol_idx, name="Volatility %",
            line=dict(color="#7c3aed", width=1.5),
            fill="tozeroy", fillcolor="rgba(124,58,237,.07)",
        ), row=cur_row, col=1)
        fig2.update_yaxes(title_text="Annualised Vol %", row=cur_row, col=1,
                          title_font=dict(size=9))

    fig2.update_layout(**layout_base, height=500,
                       xaxis_rangeslider_visible=False)
    st.plotly_chart(fig2, use_container_width=True)


# ─── TAB 3: Comparison ───
with tab3:
    if not compare_syms:
        st.info("Select symbols in the sidebar to compare.")
    else:
        fig3 = go.Figure()
        # Normalise to 100
        base = df["Close"].iloc[0]
        fig3.add_trace(go.Scatter(
            x=df.index,
            y=(df["Close"] / base) * 100,
            name=symbol,
            line=dict(color=COLOR_NEUT, width=2),
        ))
        palette = ["#fbbf24", "#00e676", "#f472b6", "#a78bfa"]
        for i, sym in enumerate(compare_syms):
            cdf, _ = fetch_ticker(sym, period, interval)
            if not cdf.empty:
                cb = cdf["Close"].iloc[0]
                fig3.add_trace(go.Scatter(
                    x=cdf.index,
                    y=(cdf["Close"] / cb) * 100,
                    name=sym,
                    line=dict(color=palette[i % len(palette)], width=2),
                ))

        fig3.update_layout(
            **layout_base,
            height=460,
            title=dict(text="Normalised Performance (Base = 100)",
                       font=dict(family="Syne, sans-serif", size=13, color="#e2e8f0")),
            yaxis_title="Index Value",
        )
        st.plotly_chart(fig3, use_container_width=True)


# ─── TAB 4: Volatility Deep-Dive ───
with tab4:
    c1, c2 = st.columns(2)

    # Return distribution
    with c1:
        st.markdown('<div class="section-label">Daily Return Distribution</div>', unsafe_allow_html=True)
        returns = df["Close"].pct_change().dropna() * 100
        fig4a = go.Figure()
        fig4a.add_trace(go.Histogram(
            x=returns, nbinsx=40,
            marker_color=COLOR_NEUT,
            marker_line=dict(color=PLOT_BG, width=.5),
            opacity=0.85,
            name="Returns",
        ))
        fig4a.update_layout(**layout_base, height=340,
                            xaxis_title="Daily Return %",
                            bargap=0.05)
        st.plotly_chart(fig4a, use_container_width=True)

    # 7-day rolling trend
    with c2:
        st.markdown('<div class="section-label">7-Day Rolling Trend</div>', unsafe_allow_html=True)
        roll7  = df["Close"].rolling(7).mean()
        fig4b  = go.Figure()
        fig4b.add_trace(go.Scatter(
            x=df.index, y=df["Close"],
            name="Close", line=dict(color="#334155", width=1), opacity=0.5,
        ))
        fig4b.add_trace(go.Scatter(
            x=df.index, y=roll7,
            name="7-Day MA", line=dict(color=COLOR_UP, width=2.5),
            fill="tozeroy", fillcolor="rgba(0,230,118,.06)",
        ))
        fig4b.update_layout(**layout_base, height=340)
        st.plotly_chart(fig4b, use_container_width=True)

    # Volatility cone
    st.markdown('<div class="section-label">Rolling Volatility (Annualised)</div>', unsafe_allow_html=True)
    log_ret = np.log(df["Close"] / df["Close"].shift(1))
    vol_10  = log_ret.rolling(10).std()  * np.sqrt(252) * 100
    vol_20  = log_ret.rolling(20).std()  * np.sqrt(252) * 100
    vol_30  = log_ret.rolling(30).std()  * np.sqrt(252) * 100

    fig4c = go.Figure()
    for vol_s, nm, c in [(vol_30, "30-Day", "#7c3aed"),
                         (vol_20, "20-Day", "#00d4ff"),
                         (vol_10, "10-Day", "#fbbf24")]:
        fig4c.add_trace(go.Scatter(
            x=df.index, y=vol_s, name=nm,
            line=dict(color=c, width=1.8),
        ))
    fig4c.update_layout(**layout_base, height=320,
                        yaxis_title="Annualised Vol %")
    st.plotly_chart(fig4c, use_container_width=True)


# ─────────────────────────────────────────────
#  RAW DATA TABLE (collapsible)
# ─────────────────────────────────────────────
st.markdown("---")
with st.expander("📋  Raw OHLCV Data"):
    display_df = df[["Open", "High", "Low", "Close", "Volume"]].tail(30).copy()
    display_df.index = display_df.index.strftime("%Y-%m-%d %H:%M")
    st.dataframe(
        display_df.style.background_gradient(subset=["Close"], cmap="Blues"),
        use_container_width=True,
    )


# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding:1.5rem 0 .5rem; color:#334155; font-size:.65rem; letter-spacing:.1em;">
    NEXUS STOCK INTELLIGENCE &nbsp;·&nbsp; POWERED BY YAHOO FINANCE (yfinance) &nbsp;·&nbsp;
    AUTO-REFRESH: 30 MIN &nbsp;·&nbsp; LAST UPDATED: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %b %Y, %H:%M:%S IST')}
</div>
""", unsafe_allow_html=True)