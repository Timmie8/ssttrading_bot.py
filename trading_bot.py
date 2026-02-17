import streamlit as st
import pandas as pd
import yfinance as yf
import time

# --- CONFIGURATIE ---
st.set_page_config(page_title="SST SMART MONEY v3.0", layout="wide")

def get_pine_metrics(df):
    """
    Exacte Pine Script logica met fix voor de Pandas/Python 3.13 vergelijkingsfout.
    """
    if df is None or len(df) < 20: 
        return 0, 0
    
    try:
        # Zorg dat we met eendimensionale data werken (verwijder Multi-index)
        close_series = df['Close'].squeeze()
        high_series = df['High'].squeeze()
        low_series = df['Low'].squeeze()
        vol_series = df['Volume'].squeeze()

        # 1. EMA 20
        ema20_series = close_series.ewm(span=20, adjust=False).mean()
        last_ema20 = float(ema20_series.iloc[-1])
        
        # 2. VWAP (Typical Price * Volume)
        tp = (high_series + low_series + close_series) / 3
        tp_v = tp * vol_series
        
        cum_tp_v = float(tp_v.sum())
        cum_v = float(vol_series.sum())
        
        vwap = cum_tp_v / cum_v if cum_v != 0 else last_ema20
        last_close = float(close_series.iloc[-1])
        
        # Trend Score (Harde vergelijking)
        trend = 0
        if last_close > last_ema20 and last_close > vwap:
            trend = 1
        elif last_close < last_ema20 and last_close < vwap:
            trend = -1
            
        # 3. Momentum Score (close - close[3])
        mom = float(close_series.iloc[-1] - close_series.iloc[-4]) if len(close_series) >= 4 else 0
        mom_score = 0.5 if mom > 0 else (-0.5 if mom < 0 else 0)
        
        # 4. Volatility Score (ATR 14)
        hl = high_series - low_series
        hcp = abs(high_series - close_series.shift())
        lcp = abs(low_series - close_series.shift())
        tr = pd.concat([hl, hcp, lcp], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        atr_avg = atr.rolling(20).mean()
        
        vol_score = 0.5 if float(atr.iloc[-1]) > float(atr_avg.iloc[-1]) else 0
        
        final_score = trend + mom_score + vol_score
        return int(trend), float(final_score)
    except Exception as e:
        return 0, 0

def fetch_data(symbol, interval):
    ticker_sym = symbol.replace("USDT", "-USD") if "USDT" in symbol else symbol
    try:
        # auto_adjust=True en actions=False voor schone data
        data = yf.download(ticker_sym, 
                           period="5d" if "m" in interval else "60d", 
                           interval=interval, 
                           progress=False, 
                           auto_adjust=True)
        return data if not data.empty else None
    except:
        return None

# --- UI ---
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
        
        with st.status(f"Berekenen {sym}...", expanded=False):
            for label, inv in tfs.items():
                df = fetch_data(sym, inv)
                t_val, s_val = get_pine_metrics(df)
                trends.append(t_val)
                scores.append(s_val)
                time.sleep(0.05) # Voorkom rate limits
            
        # --- EXACT PINE BEREKENING ---
        trend_strength_raw = sum(trends)
        strength = (trend_strength_raw / 7) * 100
        
        abs_raw = abs(trend_strength_raw)
        if abs_raw == 7: conf = 90.0
        elif abs_raw >= 4: conf = 75.0
        elif abs_raw >= 2: conf = 60.0
        else: conf = 50.0

        matrix_rows.append({
            'SYM': sym,
            '1M': "▲" if scores[0] > 0.5 else ("▼" if scores[0] < -0.5 else "━"),
            '5M': "▲" if scores[1] > 0.5 else ("▼" if scores[1] < -0.5 else "━"),
            '15M': "▲" if scores[2] > 0.5 else ("▼" if scores[2] < -0.5 else "━"),
            '30M': "▲" if scores[3] > 0.5 else ("▼" if scores[3] < -0.5 else "━"),
            '1H': "▲" if scores[4] > 0.5 else ("▼" if scores[4] < -0.5 else "━"),
            '4H': "▲" if scores[5] > 0.5 else ("▼" if scores[5] < -0.5 else "━"),
            '1D': "▲" if scores[6] > 0.5 else ("▼" if scores[6] < -0.5 else "━"),
            'STR': f"{int(round(strength))}",
            'CONF': f"{int(round(conf))}%"
        })

    st.subheader("🔮 SMART MONEY TREND MATRIX")
    res_df = pd.DataFrame(matrix_rows)
    
    # 1. Styling voor de trend-pijltjes
    def style_pijltjes(val):
        if val == "▲": return 'color: #76FF03; font-weight: bold; text-align: center;'
        if val == "▼": return 'color: #FF1744; font-weight: bold; text-align: center;'
        return 'color: #FFB627; text-align: center;'

    # 2. Styling voor de Strength (Groene rand boven 70)
    def style_strength(row):
        # Haal het getal uit de string
        try:
            val = int(row['STR'])
            if val >= 70:
                return ['border: 2px solid #76FF03; border-radius: 5px; color: #76FF03; font-weight: bold; text-align: center;'] * len(row)
            elif val <= -70:
                return ['border: 2px solid #FF1744; border-radius: 5px; color: #FF1744; font-weight: bold; text-align: center;'] * len(row)
        except:
            pass
        return ['text-align: center;'] * len(row)

    # We passen de styling toe
    styled_df = res_df.style.applymap(style_pijltjes, subset=['1M','5M','15M','30M','1H','4H','1D']) \
                            .apply(lambda x: [
                                'border: 2px solid #76FF03; color: #76FF03; font-weight: bold; text-align: center;' 
                                if (col == 'STR' and int(x['STR']) >= 70) else 
                                ('border: 2px solid #FF1744; color: #FF1744; font-weight: bold; text-align: center;' 
                                 if (col == 'STR' and int(x['STR']) <= -70) else 'text-align: center;') 
                                for col in x.index
                            ], axis=1)

    st.dataframe(styled_df, use_container_width=True, hide_index=True)






