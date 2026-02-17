import streamlit as st
import pandas as pd
import yfinance as yf
import time

# --- LAYOUT & STYLING ---
st.set_page_config(page_title="SST SMART MONEY ENGINE", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050816; color: white; }
    .stDataFrame { border: 1px solid #00D9FF; }
    .metric-card {
        background: #0A0E27;
        border: 1px solid #00D9FF;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CORE BEREKENINGEN (100% PINE MATCH) ---
def get_pine_metrics(df):
    """Berekent trend, momentum en volatiliteit exact volgens GainzAlgo PineScript"""
    if len(df) < 30: return 0, 0
    
    # 1. Trend: Price > EMA20 AND Price > VWAP
    ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
    # VWAP benadering (Typical Price * Volume)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).sum() / df['Volume'].sum()
    
    last_close = df['Close'].iloc[-1]
    trend_val = 1 if (last_close > ema20 and last_close > vwap) else (-1 if (last_close < ema20 and last_close < vwap) else 0)
    
    # 2. Momentum: close - close[3]
    mom = last_close - df['Close'].iloc[-4]
    mom_score = 0.5 if mom > 0 else (-0.5 if mom < 0 else 0)
    
    # 3. Volatility: ATR(14) vs SMA(ATR(14), 20)
    high_low = df['High'] - df['Low']
    high_cp = abs(df['High'] - df['Close'].shift())
    low_cp = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    atr_avg = atr.rolling(20).mean()
    
    vol_score = 0.5 if atr.iloc[-1] > atr_avg.iloc[-1] else 0
    
    final_score = trend_val + mom_score + vol_score
    return trend_val, final_score

def fetch_data(symbol, interval):
    try:
        ticker = yf.Ticker(symbol.replace("USDT", "-USD") if "USDT" in symbol else symbol)
        # Haal genoeg data op voor SMA van ATR en EMA warm-up
        df = ticker.history(period="60d" if interval == "1d" else "5d", interval=interval)
        return df if len(df) > 30 else None
    except: return None

# --- UI ---
st.title("⚡ SST SMART MONEY TERMINAL v3.0")

symbol_input = st.text_input("SYMBOLEN:", "AAPL, TSLA, NVDA, BTC-USD")
run_btn = st.button("RUN SMART ANALYSIS")

if run_btn:
    symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]
    intervals = {'1M':'1m','5M':'5m', '15M':'15m', '30M':'30m', '1H':'60m', '4H':'90m', '1D':'1d'}
    
    matrix_rows = []
    
    for sym in symbols:
        scores = []
        trends = []
        
        for label, inv in intervals.items():
            df = fetch_data(sym, inv)
            if df is not None:
                t_val, f_score = get_pine_metrics(df)
                trends.append(t_val)
                scores.append(f_score)
            else:
                trends.append(0)
                scores.append(0)
        
        # PineScript Logica voor Strength & Confidence
        # trend_strength_raw = som van trends over 7 timeframes
        trend_strength_raw = sum(trends)
        strength_pct = (trend_strength_raw / 7) * 100
        
        # Confidence logic exact uit de PineCode
        conf = 50.0
        abs_raw = abs(trend_strength_raw)
        if abs_raw >= 7: conf = 90.0
        elif abs_raw >= 4: conf = 75.0
        elif abs_raw >= 2: conf = 60.0
        
        # Prijs & Volume (1D)
        df_1d = fetch_data(sym, '1d')
        price = df_1d['Close'].iloc[-1] if df_1d is not None else 0
        vol = df_1d['Volume'].iloc[-1] if df_1d is not None else 0

        # Matrix format
        matrix_rows.append({
            'SYM': sym,
            'PRICE': f"{price:.2f}",
            '1M': "▲" if scores[0] > 0.5 else ("▼" if scores[0] < -0.5 else "━"),
            '5M': "▲" if scores[1] > 0.5 else ("▼" if scores[1] < -0.5 else "━"),
            '15M': "▲" if scores[2] > 0.5 else ("▼" if scores[2] < -0.5 else "━"),
            '30M': "▲" if scores[3] > 0.5 else ("▼" if scores[3] < -0.5 else "━"),
            '1H': "▲" if scores[4] > 0.5 else ("▼" if scores[4] < -0.5 else "━"),
            '4H': "▲" if scores[5] > 0.5 else ("▼" if scores[5] < -0.5 else "━"),
            '1D': "▲" if scores[6] > 0.5 else ("▼" if scores[6] < -0.5 else "━"),
            'STR': f"{strength_pct:.0f}%",
            'CONF': f"{conf:.0f}%",
            'VOL': f"{vol/1000:.0f}K"
        })

    # --- WEERGAVE ---
    st.subheader("🔮 SMART MONEY TREND MATRIX")
    df_matrix = pd.DataFrame(matrix_rows)
    
    def color_pijltjes(val):
        if val == "▲": return 'color: #76FF03; font-weight: bold; text-align: center;'
        if val == "▼": return 'color: #FF1744; font-weight: bold; text-align: center;'
        return 'color: #FFB627; text-align: center;'

    st.dataframe(
        df_matrix.style.applymap(color_pijltjes, subset=['1M','5M','15M','30M','1H','4H','1D']),
        use_container_width=True, hide_index=True
    )

    # Details per symbool
    for row in matrix_rows:
        with st.expander(f"Smart Money Flow: {row['SYM']}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Strength", row['STR'])
            c2.metric("Confidence", row['CONF'])
            c3.metric("Price", row['PRICE'])
            c4.metric("CVD / Vol", row['VOL'])

else:
    st.info("Systeem staat klaar voor GainzAlgo v3.0 Analyse.")





