"""
╔══════════════════════════════════════════════════════════╗
║         NEXUS — Real-Time Stock Intelligence Dashboard   ║
║         API: yfinance + requests-cache (no key needed)   ║
║         Auto-refresh: every 30 minutes                   ║
╚══════════════════════════════════════════════════════════╝
"""

import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import pytz
import time

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS · Stock Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto",
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
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg:       #080c14;
    --surface:  #0d1320;
    --surface2: #111827;
    --border:   #1e2d42;
    --accent:   #00d4ff;
    --accent2:  #7c3aed;
    --green:    #00e676;
    --red:      #ff3d57;
    --gold:     #fbbf24;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --font-head:'Syne', sans-serif;
    --font-mono:'JetBrains Mono', monospace;
}
html, body, [class*="css"] {
    font-family: var(--font-mono);
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.main { background: var(--bg) !important; }
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 1600px; }
#MainMenu, footer { visibility: hidden; }
/* Keep the sidebar toggle arrow always visible */
[data-testid="collapsedControl"] { visibility: visible !important; display: flex !important; }

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: var(--font-mono) !important; }

[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    transition: border-color .25s;
}
[data-testid="stMetric"]:hover { border-color: var(--accent) !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size:.7rem !important; letter-spacing:.12em; text-transform:uppercase; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-size:1.6rem !important; font-family:var(--font-head) !important; font-weight:700 !important; }

[data-testid="stTabs"] button {
    font-family: var(--font-mono) !important;
    font-size: .75rem !important;
    letter-spacing: .08em;
    color: var(--muted) !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}

[data-testid="stSelectbox"] > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--font-mono) !important;
}

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
    content:'';
    position:absolute; top:-60px; right:-60px;
    width:200px; height:200px;
    background:radial-gradient(circle, rgba(0,212,255,.12) 0%, transparent 70%);
    pointer-events:none;
}
.nexus-title {
    font-family: var(--font-head);
    font-size: 2.2rem; font-weight: 800;
    letter-spacing: -.02em; color: #fff; margin: 0 0 .2rem;
}
.nexus-title span { color: var(--accent); }
.nexus-sub { font-family:var(--font-mono); font-size:.72rem; color:var(--muted); letter-spacing:.15em; text-transform:uppercase; }
.live-badge {
    display:inline-flex; align-items:center; gap:.4rem;
    background:rgba(0,230,118,.1); border:1px solid rgba(0,230,118,.3);
    border-radius:20px; padding:.25rem .75rem;
    font-size:.65rem; color:var(--green); letter-spacing:.1em; text-transform:uppercase;
}
.live-dot { width:6px; height:6px; background:var(--green); border-radius:50%; animation:pulse 1.6s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.7)} }

.section-label {
    font-family:var(--font-mono); font-size:.65rem; letter-spacing:.18em;
    text-transform:uppercase; color:var(--muted);
    border-left:2px solid var(--accent); padding-left:.6rem; margin-bottom:.75rem;
}
.alert-box {
    background:rgba(255,61,87,.07); border:1px solid rgba(255,61,87,.3);
    border-radius:10px; padding:.75rem 1rem;
    font-size:.75rem; color:#fca5a5; font-family:var(--font-mono); margin-bottom:.5rem;
}
.alert-box strong { color:var(--red); }
.api-warn {
    background:rgba(251,191,36,.07); border:1px solid rgba(251,191,36,.3);
    border-radius:10px; padding:1rem 1.2rem;
    font-size:.8rem; color:#fde68a; font-family:var(--font-mono);
}
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }

div[data-testid="stButton"] > button {
    background: rgba(0,212,255,.08) !important;
    border: 1px solid rgba(0,212,255,.25) !important;
    color: #00d4ff !important;
    font-family: JetBrains Mono, monospace !important;
    font-size: .72rem !important;
    letter-spacing: .1em !important;
    padding: .3rem 1rem !important;
    border-radius: 8px !important;
    transition: all .2s;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,212,255,.18) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
WATCHLIST = {
    "AAPL":  "Apple",
    "MSFT":  "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN":  "Amazon",
    "NVDA":  "NVIDIA",
    "TSLA":  "Tesla",
    "META":  "Meta",
    "JPM":   "JPMorgan",
    "SPY":   "S&P 500 ETF",
    "QQQ":   "Nasdaq ETF",
}

PERIOD_OPTIONS = {
    "Daily (3 months)":   "daily",
    "Weekly (1 year)":    "weekly",
    "Monthly (5 years)":  "monthly",
}

COLOR_UP   = "#00e676"
COLOR_DOWN = "#ff3d57"
COLOR_NEUT = "#00d4ff"
PLOT_BG    = "#0d1320"
GRID_COLOR = "#1e2d42"

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


# ─────────────────────────────────────────────
#  YFINANCE DATA FETCH  (no API key needed)
# ─────────────────────────────────────────────
PERIOD_MAP = {
    "daily":   ("3mo",  "1d"),
    "weekly":  ("1y",   "1wk"),
    "monthly": ("5y",   "1mo"),
}

@st.cache_data(ttl=1800)
def fetch_ticker(symbol: str, interval: str) -> pd.DataFrame:
    period, freq = PERIOD_MAP.get(interval, ("3mo", "1d"))
    tk = yf.Ticker(symbol)
    df = tk.history(period=period, interval=freq, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")
    df.index = df.index.tz_localize(None)
    return df[["Open", "High", "Low", "Close", "Volume"]]


@st.cache_data(ttl=1800)
def fetch_quote(symbol: str) -> dict:
    tk  = yf.Ticker(symbol)
    fi  = tk.fast_info
    def _f(attr):
        try: return float(getattr(fi, attr) or 0)
        except: return 0.0
    prev  = _f("previous_close")
    price = _f("last_price") or _f("regular_market_price")
    chg   = price - prev
    chg_p = (chg / prev * 100) if prev else 0.0
    return {
        "price":      price,
        "change":     chg,
        "change_pct": chg_p,
        "open":       _f("open"),
        "high":       _f("day_high"),
        "low":        _f("day_low"),
        "volume":     _f("three_month_average_volume"),
        "prev_close": prev,
        "latest_day": datetime.now().strftime("%Y-%m-%d"),
    }


def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def detect_anomalies(df, z_thresh=2.5):
    ret = df["Close"].pct_change()
    mu, sigma = ret.mean(), ret.std()
    z = (ret - mu) / sigma
    return df[z.abs() > z_thresh]


# ─────────────────────────────────────────────
#  SIDEBAR — all controls live here
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)

    symbol = st.selectbox(
        "Symbol",
        list(WATCHLIST.keys()),
        format_func=lambda x: f"{x}  —  {WATCHLIST[x]}",
    )

    compare_syms = st.multiselect(
        "Compare With",
        [k for k in WATCHLIST if k != symbol],
        default=[],
        max_selections=3,
        format_func=lambda x: f"{x}  —  {WATCHLIST[x]}",
    )

    period_label = st.selectbox("Time Range", list(PERIOD_OPTIONS.keys()), index=0)
    interval = PERIOD_OPTIONS[period_label]

    st.markdown("---")
    st.markdown('<div class="section-label">Chart Overlays</div>', unsafe_allow_html=True)
    show_ma        = st.checkbox("Moving Averages (20 / 50)", value=True)
    show_bollinger = st.checkbox("Bollinger Bands",           value=False)
    show_volume    = st.checkbox("Volume Bars",               value=True)
    show_rsi       = st.checkbox("RSI (14)",                  value=False)

    st.markdown("---")
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    st.markdown(f"""
    <div style="font-size:.65rem; color:#475569; line-height:2;">
        <div style="color:#94a3b8; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.4rem;">System</div>
        🕐 {now.strftime('%H:%M:%S IST')}<br>
        🔄 Refresh #<strong style="color:#00d4ff">{refresh_count}</strong><br>
        ⏱ Next refresh in ~30 min<br>
        📡 Yahoo Finance (yfinance)<br><br>
        <span style="color:#334155;">Press <kbd style="background:#1e2d42;color:#94a3b8;padding:.1rem .4rem;border-radius:4px;font-size:.7rem;">【</kbd> to hide/show this panel</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# ─────────────────────────────────────────────
#  FETCH DATA
# ─────────────────────────────────────────────
company = WATCHLIST.get(symbol, symbol)

with st.spinner(f"Fetching {symbol}…"):
    try:
        df    = fetch_ticker(symbol, interval)
        quote = fetch_quote(symbol)
    except Exception as e:
        st.error(f"⚠️ Data fetch failed: {e}")
        st.stop()

if df.empty:
    st.error("No data returned for this symbol.")
    st.stop()


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
price     = quote["price"] or df["Close"].iloc[-1]
chg_pct   = float(quote["change_pct"] or 0)
chg_arrow = "▲" if chg_pct >= 0 else "▼"
chg_color = "#00e676" if chg_pct >= 0 else "#ff3d57"

st.markdown(f"""
<div class="nexus-header">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
    <div>
      <div class="nexus-title">NEXUS <span>·</span> {symbol}</div>
      <div class="nexus-sub">{company} &nbsp;·&nbsp; {period_label} &nbsp;·&nbsp; {quote.get('latest_day','')}</div>
    </div>
    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:.5rem;">
      <div style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; color:#fff;">
          ${price:,.2f}
          <span style="font-size:1rem; color:{chg_color};">{chg_arrow} {abs(chg_pct):.2f}%</span>
      </div>
      <div class="live-badge"><div class="live-dot"></div>Yahoo Finance · Live</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  KPI METRICS
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Key Metrics</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Current Price",  f"${price:,.2f}",               f"{chg_pct:+.2f}%")
k2.metric("Today Open",     f"${quote['open']:,.2f}")
k3.metric("Today High",     f"${quote['high']:,.2f}")
k4.metric("Today Low",      f"${quote['low']:,.2f}")
k5.metric("Prev Close",     f"${quote['prev_close']:,.2f}")
avg_vol = df["Volume"].mean()
cur_vol = quote["volume"] or df["Volume"].iloc[-1]
vol_delta = ((cur_vol - avg_vol) / avg_vol * 100) if avg_vol else 0
k6.metric("Volume vs Avg",  f"{vol_delta:+.1f}%",
          "↑ High" if vol_delta > 20 else ("↓ Low" if vol_delta < -20 else "Normal"))

st.markdown("---")


# ─────────────────────────────────────────────
#  ANOMALY ALERTS
# ─────────────────────────────────────────────
anomalies = detect_anomalies(df)
if not anomalies.empty:
    st.markdown('<div class="section-label">Anomaly Alerts</div>', unsafe_allow_html=True)
    for idx, row in anomalies.tail(3).iterrows():
        date_str = idx.strftime("%b %d, %Y") if hasattr(idx, "strftime") else str(idx)
        st.markdown(f"""
        <div class="alert-box">
            ⚠ <strong>Anomaly Detected</strong> on {date_str} —
            Close: <strong>${row['Close']:.2f}</strong> —
            Unusual price movement (Z-score &gt; 2.5)
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN CHART TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊  Price Chart", "📈  Technical", "🌐  Comparison", "📉  Volatility"])


# ── TAB 1: Candlestick ──────────────────────
with tab1:
    rows        = 2 if show_volume else 1
    row_heights = [0.75, 0.25] if show_volume else [1]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=row_heights)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name=symbol,
        increasing=dict(fillcolor=COLOR_UP,  line=dict(color=COLOR_UP,  width=1)),
        decreasing=dict(fillcolor=COLOR_DOWN, line=dict(color=COLOR_DOWN, width=1)),
    ), row=1, col=1)

    if show_ma:
        for w, c in [(20, "#00d4ff"), (50, "#fbbf24")]:
            fig.add_trace(go.Scatter(
                x=df.index, y=df["Close"].rolling(w).mean(),
                name=f"MA{w}", line=dict(color=c, width=1.5, dash="dot"), opacity=.85,
            ), row=1, col=1)

    if show_bollinger:
        ma20  = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()
        for y, nm, c in [(ma20+2*std20, "BB Upper", "#7c3aed"),
                         (ma20-2*std20, "BB Lower", "#7c3aed")]:
            fig.add_trace(go.Scatter(
                x=df.index, y=y, name=nm,
                line=dict(color=c, width=1, dash="dash"), opacity=.6,
            ), row=1, col=1)

    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies.index, y=anomalies["Close"], mode="markers",
            marker=dict(symbol="x", size=12, color=COLOR_DOWN, line=dict(width=2)),
            name="Anomaly",
        ), row=1, col=1)

    if show_volume:
        colors = [COLOR_UP if c >= o else COLOR_DOWN
                  for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=colors, name="Volume", opacity=.6,
        ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1, title_font=dict(size=9))

    fig.update_layout(**layout_base, height=560,
                      xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)


# ── TAB 2: Technical ────────────────────────
with tab2:
    sub_rows = 1 + int(show_rsi)
    heights  = ([0.6, 0.4] if show_rsi else [1])

    fig2 = make_subplots(rows=sub_rows, cols=1, shared_xaxes=True,
                         vertical_spacing=0.04, row_heights=heights)

    fig2.add_trace(go.Scatter(
        x=df.index, y=df["Close"], name="Close",
        line=dict(color=COLOR_NEUT, width=2),
        fill="tozeroy", fillcolor="rgba(0,212,255,.05)",
    ), row=1, col=1)

    if show_rsi:
        rsi = compute_rsi(df["Close"])
        fig2.add_trace(go.Scatter(
            x=df.index, y=rsi, name="RSI(14)",
            line=dict(color="#fbbf24", width=1.5),
        ), row=2, col=1)
        for level, col in [(70, "rgba(255,61,87,.3)"), (30, "rgba(0,230,118,.3)")]:
            fig2.add_hline(y=level, line_dash="dot", line_color=col, row=2, col=1)
        fig2.update_yaxes(title_text="RSI", row=2, col=1,
                          range=[0, 100], title_font=dict(size=9))

    fig2.update_layout(**layout_base, height=480,
                       xaxis_rangeslider_visible=False)
    st.plotly_chart(fig2, use_container_width=True)


# ── TAB 3: Volatility ───────────────────────
with tab3:
    if not compare_syms:
        st.info("Select symbols in the sidebar under **Compare With** to overlay them here.")
    else:
        fig_cmp = go.Figure()
        # Normalise primary to 100
        base = df["Close"].iloc[0]
        fig_cmp.add_trace(go.Scatter(
            x=df.index,
            y=(df["Close"] / base) * 100,
            name=symbol,
            line=dict(color="#00d4ff", width=2.5),
        ))
        palette = ["#fbbf24", "#00e676", "#f472b6"]
        for i, sym in enumerate(compare_syms):
            try:
                cdf = fetch_ticker(sym, interval)
                if not cdf.empty:
                    cb = cdf["Close"].iloc[0]
                    fig_cmp.add_trace(go.Scatter(
                        x=cdf.index,
                        y=(cdf["Close"] / cb) * 100,
                        name=sym,
                        line=dict(color=palette[i % len(palette)], width=2),
                    ))
            except Exception:
                st.warning(f"Could not fetch data for {sym}")

        fig_cmp.update_layout(
            **layout_base,
            height=480,
            title=dict(
                text="Normalised Performance (Base = 100)",
                font=dict(family="Syne, sans-serif", size=13, color="#e2e8f0"),
            ),
            yaxis_title="Index Value",
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

with tab4:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-label">Daily Return Distribution</div>',
                    unsafe_allow_html=True)
        returns = df["Close"].pct_change().dropna() * 100
        fig3a = go.Figure(go.Histogram(
            x=returns, nbinsx=40,
            marker_color=COLOR_NEUT,
            marker_line=dict(color=PLOT_BG, width=.5),
            opacity=0.85, name="Returns",
        ))
        fig3a.update_layout(**layout_base, height=320,
                            xaxis_title="Daily Return %", bargap=0.05)
        st.plotly_chart(fig3a, use_container_width=True)

    with c2:
        st.markdown('<div class="section-label">7-Day Rolling Trend</div>',
                    unsafe_allow_html=True)
        roll7 = df["Close"].rolling(7).mean()
        fig3b = go.Figure()
        fig3b.add_trace(go.Scatter(
            x=df.index, y=df["Close"], name="Close",
            line=dict(color="#334155", width=1), opacity=.5,
        ))
        fig3b.add_trace(go.Scatter(
            x=df.index, y=roll7, name="7-Day MA",
            line=dict(color=COLOR_UP, width=2.5),
            fill="tozeroy", fillcolor="rgba(0,230,118,.06)",
        ))
        fig3b.update_layout(**layout_base, height=320)
        st.plotly_chart(fig3b, use_container_width=True)

    st.markdown('<div class="section-label">Rolling Volatility (Annualised)</div>',
                unsafe_allow_html=True)
    log_ret = np.log(df["Close"] / df["Close"].shift(1))
    fig3c = go.Figure()
    for w, nm, c in [(10, "10-Day", "#fbbf24"),
                     (20, "20-Day", "#00d4ff"),
                     (30, "30-Day", "#7c3aed")]:
        fig3c.add_trace(go.Scatter(
            x=df.index,
            y=log_ret.rolling(w).std() * np.sqrt(252) * 100,
            name=nm, line=dict(color=c, width=1.8),
        ))
    fig3c.update_layout(**layout_base, height=300, yaxis_title="Annualised Vol %")
    st.plotly_chart(fig3c, use_container_width=True)


# ─────────────────────────────────────────────
#  RAW DATA TABLE
# ─────────────────────────────────────────────
st.markdown("---")
with st.expander("📋  Raw OHLCV Data (last 30 rows)"):
    display_df = df[["Open", "High", "Low", "Close", "Volume"]].tail(30).copy()
    display_df.index = display_df.index.strftime("%Y-%m-%d")
    st.dataframe(display_df, use_container_width=True)


# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
ist = pytz.timezone("Asia/Kolkata")
st.markdown(f"""
<div style="text-align:center; padding:1.5rem 0 .5rem; color:#334155; font-size:.65rem; letter-spacing:.1em;">
    NEXUS STOCK INTELLIGENCE &nbsp;·&nbsp; ALPHA VANTAGE API &nbsp;·&nbsp;
    AUTO-REFRESH: 30 MIN &nbsp;·&nbsp;
    LAST UPDATED: {datetime.now(ist).strftime('%d %b %Y, %H:%M:%S IST')}
</div>
""", unsafe_allow_html=True)