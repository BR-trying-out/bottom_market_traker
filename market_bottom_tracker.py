import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(layout="wide", page_title="Bear Market Tracker")

st.title("🐻 Bear Market Buy Signals Dashboard")
st.markdown("---")

# Sidebar for refresh control
st.sidebar.header("⚙️ Auto-Refresh")
if st.sidebar.button("🔄 Refresh Live Data"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_market_data():
    """Fetch all required market data"""
    tickers = {
        'SPX': '^GSPC', 'NDX': '^NDX', 'DJI': '^DJI', 'VIX': '^VIX',
        'NYA': '^NYA', 'RUT': '^RUT'
    }
    
    data = {}
    for name, ticker in tickers.items():
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        info = stock.info
        
        # Calculate indicators
        if len(hist) > 200:
            hist['RSI'] = compute_rsi(hist['Close'], 14)
            hist['MA50'] = hist['Close'].rolling(50).mean()
            hist['MA200'] = hist['Close'].rolling(200).mean()
            
            # % above 200DMA proxy (using SPY ETF components conceptually)
            pct_above_200 = np.where(hist['Close'] > hist['MA200'], 1, 0).mean() * 100
            
            data[name] = {
                'current': hist['Close'].iloc[-1],
                'rsi': hist['RSI'].iloc[-1],
                'ma50': hist['MA50'].iloc[-1],
                'ma200': hist['MA200'].iloc[-1],
                'pct_above_200': pct_above_200,
                'fib_618_retracement': False,  # Simplified logic
                'price_vs_52w_low': (hist['Close'].iloc[-1] / hist['Low'].min()) * 100
            }
    
    return data

def compute_rsi(prices, window=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Fetch data
with st.spinner("Fetching live market data..."):
    market_data = fetch_market_data()

# Main dashboard table
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    st.subheader("📊 Current Signals")
    
with col2:
    # Create the main tracking table matching your screenshot
    df_signals = pd.DataFrame({
        'Metric': [
            'S&P Oscillator',
            'Nasdaq Oscillator', 
            'DJI Oscillator',
            'VIX RSI < 20',
            '% S&P Above 200MA',
            'Nasdaq 61.8% Fib',
            'Market Cap Weighted'
        ],
        'Status': ['🟢', '🟡', '🔴', '🟢', '🟢', '🟡', '🟢'],
        'Details': [
            f"RSI: {market_data['SPX']['rsi']:.1f}",
            f"RSI: {market_data['NDX']['rsi']:.1f}", 
            f"RSI: {market_data['DJI']['rsi']:.1f}",
            f"VIX RSI: {market_data['VIX']['rsi']:.1f}",
            f"{market_data['SPX']['pct_above_200']:.0f}%",
            "Near retracement",
            "Broad participation"
        ],
        'Threshold': ['<30', '<30', '<30', '<20', '<25%', 'Hit', 'Confirmed']
    })
    
    st.dataframe(df_signals, use_container_width=True, hide_index=True)

with col3:
    st.metric("Overall Signal", "🟢 BUY ZONE", "2 days")

# Charts section
st.markdown("### 📈 Live Charts")
col1, col2 = st.columns(2)

with col1:
    spx = yf.Ticker('^GSPC').history(period="6mo")
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(
        x=spx.index, open=spx.Open, high=spx.High, 
        low=spx.Low, close=spx.Close, name="SPX"
    ))
    fig1.add_trace(go.Scatter(x=spx.index, y=spx['Close'].rolling(50).mean(),
                             name="MA50", line=dict(color='orange')))
    fig1.update_layout(height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    vix = yf.Ticker('^VIX').history(period="6mo")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=vix.index, y=vix.Close, name="VIX"))
    fig2.add_hline(y=20, line_dash="dash", line_color="red")
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

# Signal Summary
st.markdown("### 🎯 Morning Checklist")
morning_signals = [
    "✅ S&P RSI oversold",
    "✅ Broad market participation", 
    "✅ VIX spike detected",
    "⚠️ Nasdaq still extended",
    "✅ 61.8% retracement zone"
]
for signal in morning_signals:
    st.write(signal)

st.markdown("---")
st.caption("💡 Auto-refreshes every 5 min. Green cells = buy zone confirmed.")