import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="SST AI QUANT V4", layout="wide")

# --- CONFIGURATIE ---
# Yahoo gebruikt andere codes voor timeframes
YF_RES_MAP = {
    '5M': '5m',
    '15M': '15m',
    '30M': '30m',
    '1H': '60m',
    '4H': '90m', # Yahoo heeft geen 4u, we gebruiken 90m of 1h
    '1D': '1d'
}

def fetch_yfinance_data(symbol, interval):
    """Haalt data op via Yahoo Finance (Gratis & Geen Key)"""
    try:
        # Voor Yahoo moeten we soms de ticker aanpassen (bijv. BTC-USD ipv BTCUSDT)
        ticker_sym = symbol
        if "USDT" in symbol:
            ticker_sym = symbol.replace("USDT", "-USD")
            
        ticker = yf.Ticker(ticker_sym)
        # Haal genoeg data op voor de EMA 20
        period = "5d" if interval in ['5m', '15m', '30m', '60m'] else "1mo"
        df = ticker.history(period=period, interval=interval)
        
        if not df.empty:
            return pd.DataFrame({'close': df['Close']})
    except Exception as e:
        return None
    return None

# --- UI ---
st.title("⚡ SST AI QUANT - Yahoo Engine")
st.write("Status: **Yahoo Finance Fallback Actief**")

symbol_input = st.text_input("Symbolen (bijv. AAPL, TSLA, BTC-USD):", "AAPL, TSLA, NVDA")

if st.button("START ANALYSE"):
    symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]
    
    for sym in symbols:
        st.divider()
        st.subheader(f"Analyse: {sym}")
        cols = st.columns(6)
        
        results = []
        labels = list(YF_RES_MAP.keys())
        
        for i, label in enumerate(labels):
            interval = YF_RES_MAP[label]
            
            with st.spinner(f'Laden {label}...'):
                df = fetch_yfinance_data(sym, interval)
                
            with cols[i]:
                if df is not None and len(df) >= 20:
                    # Pine Script EMA 20 berekening
                    ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                    last_c = df['close'].iloc[-1]
                    
                    color = "#76FF03" if last_c > ema20 else "#FF1744"
                    icon = "▲" if last_c > ema20 else "▼"
                    st.markdown(f"**{label}**")
                    st.markdown(f"<h1 style='color:{color}; margin:0;'>{icon}</h1>", unsafe_allow_html=True)
                    st.caption(f"Price: {round(last_c, 2)}")
                else:
                    st.markdown(f"**{label}**")
                    st.warning("⚠️")
            
            time.sleep(0.1) # Yahoo is erg snel en blokkeert niet snel


