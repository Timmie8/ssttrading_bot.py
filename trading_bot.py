import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="SST SMART MONEY v3.0", layout="wide")

# --- EXACTE PINE SCRIPT LOGICA ---
def get_pine_metrics(df):
    if df is None or len(df) < 20: return 0, 0
    
    # Trend: Price > EMA20 AND Price > VWAP
    ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).sum() / df['Volume'].sum()
    last_close = df['Close'].iloc[-1]
    
    # trend1M, trend5M, etc logic
    trend = 0
    if last_close > ema20 and last_close > vwap:
        trend = 1
    elif last_close < ema20 and last_close < vwap:
        trend = -1
        
    # Momentum & Volatility scores voor de pijltjes (Predict)
    mom = last_close - df['Close'].shift(3).iloc[-1]
    mom_score = 0.5 if mom > 0 else (-0.5 if mom < 0 else 0)
    
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    atr_avg = atr.rolling(20).mean()
    vol_score = 0.5 if atr.iloc[-1] > atr_avg.iloc[-1] else 0
    
    final_score = trend + mom_score + vol_score
    return trend, final_score

def fetch_data(symbol, interval):
    ticker_sym = symbol.replace("USDT", "-USD") if "USDT" in symbol else symbol
    try:
        # Voor 1m en 5m hebben we minder dagen nodig om snelheid te houden
        p = "2d" if "m" in interval else "60d"
        df = yf.download(ticker_sym, period=p, interval=interval, progress=False)
        return df if not df.empty else None
    except: return None

st.title("⚡ SST AI QUANT - EXACT PINE MATCH")

symbol_input = st.text_input("SYMBOLEN:", "AVAV, AAPL, TSLA, BTC-USD")
run_btn = st.button("RUN ENGINE")

if run_btn:
    symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]
    # De 7 timeframes uit de PineCode
    tfs = {'1M':'1m', '5M':'5m', '15M':'15m', '30M':'30m', '1H':'60m', '4H':'90m', '1D':'1d'}
    
    matrix_rows = []
    for sym in symbols:
        trends = []
        scores = []
        
        for label, inv in tfs.items():
            df = fetch_data(sym, inv)
            t_val, s_val = get_pine_metrics(df)
            trends.append(t_val)
            scores.append(s_val)
            
        # --- DE BEREKENING (EXACT PINE) ---
        trend_strength_raw = sum(trends) # trend1M + trend5M + ... + trendD
        strength = (trend_strength_raw / 7) * 100
        
        # System Confidence Logic
        abs_raw = abs(trend_strength_raw)
        if abs_raw == 7: conf = 90.0
        elif abs_raw >= 4: conf = 75.0
        elif abs_raw >= 2: conf = 60.0
        else: conf = 50.0

        # Laatste prijs ophalen
        last_p = fetch_data(sym, '1m')['Close'].iloc[-1]

        matrix_rows.append({
            'SYM': sym,
            'PRICE': f"{last_p:.2f}",
            '1M': "▲" if scores[0] > 0.5 else ("▼" if scores[0] < -0.5 else "━"),
            '5M': "▲" if scores[1] > 0.5 else ("▼" if scores[1] < -0.5 else "━"),
            '15M': "▲" if scores[2] > 0.5 else ("▼" if scores[2] < -0.5 else "━"),
            '30M': "▲" if scores[3] > 0.5 else ("▼" if scores[3] < -0.5 else "━"),
            '1H': "▲" if scores[4] > 0.5 else ("▼" if scores[4] < -0.5 else "━"),
            '4H': "▲" if scores[5] > 0.5 else ("▼" if scores[5] < -0.5 else "━"),
            '1D': "▲" if scores[6] > 0.5 else ("▼" if scores[6] < -0.5 else "━"),
            'STRENGTH': f"{round(strength)}",
            'CONFIDENCE': f"{round(conf)}%"
        })

    st.table(pd.DataFrame(matrix_rows))





