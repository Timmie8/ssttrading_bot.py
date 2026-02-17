import streamlit as st
import pandas as pd
import yfinance as yf
import time

# --- CONFIGURATIE ---
st.set_page_config(page_title="SST SMART MONEY v3.0", layout="wide")

def get_pine_metrics(df):
    """
    Exacte Pine Script logica met fix voor de Pandas ValueError.
    """
    if df is None or len(df) < 20: 
        return 0, 0
    
    # Haal de Close kolom op als een Series
    close_series = df['Close']
    
    # 1. EMA 20 (Exacte Pine methode)
    ema20_series = close_series.ewm(span=20, adjust=False).mean()
    last_ema20 = ema20_series.iloc[-1]
    
    # 2. VWAP (Volume Weighted Average Price)
    # Gebruik Typical Price zoals in Pine Script: (H+L+C)/3
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    tp_v = typical_price * df['Volume']
    cum_tp_v = tp_v.sum()
    cum_v = df['Volume'].sum()
    
    # Voorkom delen door nul
    vwap = cum_tp_v / cum_v if cum_v != 0 else last_ema20
    
    last_close = float(close_series.iloc[-1])
    
    # Trend bepaling (Zet om naar float voor zuivere vergelijking)
    trend = 0
    if last_close > float(last_ema20) and last_close > float(vwap):
        trend = 1
    elif last_close < float(last_ema20) and last_close < float(vwap):
        trend = -1
        
    # 3. Momentum Score (close - close[3])
    mom = last_close - close_series.iloc[-4] if len(close_series) >= 4 else 0
    mom_score = 0.5 if mom > 0 else (-0.5 if mom < 0 else 0)
    
    # 4. Volatility Score (ATR 14)
    high_low = df['High'] - df['Low']
    tr = pd.concat([high_low, abs(df['High'] - close_series.shift()), abs(df['Low'] - close_series.shift())], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    atr_avg = atr.rolling(20).mean()
    vol_score = 0.5 if atr.iloc[-1] > atr_avg.iloc[-1] else 0
    
    final_score = trend + mom_score + vol_score
    return int(trend), float(final_score)

def fetch_data(symbol, interval):
    ticker_sym = symbol.replace("USDT", "-USD") if "USDT" in symbol else symbol
    try:
        # Belangrijk: Yahoo Finance geeft MultiIndex terug bij sommige symbols
        # We gebruiken group_by='ticker' om dit te voorkomen
        data = yf.download(ticker_sym, period="5d" if "m" in interval else "60d", interval=interval, progress=False)
        if data.empty:
            return None
        return data
    except:
        return None

# --- UI INTERFACE ---
st.title("⚡ SST AI QUANT - SMART MONEY ENGINE")

symbol_input = st.text_input("SYMBOLEN (gescheiden door komma):", "AVAV, AAPL, TSLA, BTC-USD")
run_btn = st.button("RUN ENGINE")

if run_btn:
    symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]
    tfs = {'1M':'1m', '5M':'5m', '15M':'15m', '30M':'30m', '1H':'60m', '4H':'90m', '1D':'1d'}
    
    matrix_rows = []
    
    for sym in symbols:
        trends = []
        scores = []
        
        # Voeg een kleine spinner toe voor feedback
        with st.status(f"Analyseert {sym}...", expanded=False):
            for label, inv in tfs.items():
                df = fetch_data(sym, inv)
                t_val, s_val = get_pine_metrics(df)
                trends.append(t_val)
                scores.append(s_val)
            
        # --- BEREKENING SCORES (Exact Pine) ---
        trend_strength_raw = sum(trends)
        strength = (trend_strength_raw / 7) * 100
        
        abs_raw = abs(trend_strength_raw)
        if abs_raw == 7: conf = 90.0
        elif abs_raw >= 4: conf = 75.0
        elif abs_raw >= 2: conf = 60.0
        else: conf = 50.0

        # Update Matrix
        matrix_rows.append({
            'SYM': sym,
            '1M': "▲" if scores[0] > 0.5 else ("▼" if scores[0] < -0.5 else "━"),
            '5M': "▲" if scores[1] > 0.5 else ("▼" if scores[1] < -0.5 else "━"),
            '15M': "▲" if scores[2] > 0.5 else ("▼" if scores[2] < -0.5 else "━"),
            '30M': "▲" if scores[3] > 0.5 else ("▼" if scores[3] < -0.5 else "━"),
            '1H': "▲" if scores[4] > 0.5 else ("▼" if scores[4] < -0.5 else "━"),
            '4H': "▲" if scores[5] > 0.5 else ("▼" if scores[5] < -0.5 else "━"),
            '1D': "▲" if scores[6] > 0.5 else ("▼" if scores[6] < -0.5 else "━"),
            'STRENGTH': f"{int(round(strength))}",
            'CONFIDENCE': f"{int(round(conf))}%"
        })

    # Toon resultaat
    st.subheader("🔮 SMART MONEY TREND MATRIX")
    res_df = pd.DataFrame(matrix_rows)
    
    # Styling voor de tabel
    def style_pijltjes(val):
        if val == "▲": return 'color: #76FF03; font-weight: bold; text-align: center;'
        if val == "▼": return 'color: #FF1744; font-weight: bold; text-align: center;'
        return 'color: gray; text-align: center;'

    st.dataframe(res_df.style.applymap(style_pijltjes, subset=['1M','5M','15M','30M','1H','4H','1D']), use_container_width=True)




