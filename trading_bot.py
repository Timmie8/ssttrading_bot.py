import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="SST AI QUANT", layout="wide")

# --- API KEY ---
API_KEY = 'd5h3vm9r01qll3dlm2sgd5h3vm9r01qll3dlm2t0'

def check_api():
    """Test of de API-sleutel überhaupt werkt"""
    test_url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={API_KEY}"
    try:
        r = requests.get(test_url, timeout=5)
        if r.status_code == 429:
            return "ERROR: Te veel verzoeken (Rate Limit). Wacht 1 minuut."
        if r.status_code == 403:
            return "ERROR: Ongeldige API Key."
        return "OK"
    except:
        return "ERROR: Geen internetverbinding."

def fetch_candles(symbol, res):
    url = f"https://finnhub.io/api/v1/candle?symbol={symbol}&resolution={res}&count=30&token={API_KEY}"
    try:
        r = requests.get(url, timeout=7)
        data = r.json()
        if data.get('s') == 'ok':
            return pd.DataFrame({'close': data['c']})
        return None
    except:
        return None

# --- UI ---
st.title("⚡ SST AI QUANT TERMINAL")

# Status check
api_status = check_api()
if api_status == "OK":
    st.success("Verbinding met Finnhub: ✅ Actief")
else:
    st.error(f"Verbinding met Finnhub: ❌ {api_status}")

symbol_input = st.text_input("Symbolen:", "AAPL, TSLA, NVDA")

if st.button("START ANALYSE"):
    symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]
    resolutions = {'5M': '5', '15M': '15', '30M': '30', '1H': '60', '4H': '240', '1D': 'D'}
    
    for sym in symbols:
        st.write(f"### Analyseert: {sym}...")
        cols = st.columns(6)
        
        # Haal data op met vertraging om blokkade te voorkomen
        for i, (label, res_code) in enumerate(resolutions.items()):
            df = fetch_candles(sym, res_code)
            with cols[i]:
                if df is not None:
                    # Pine Script EMA 20 berekening
                    ema20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                    last_c = df['close'].iloc[-1]
                    
                    color = "#76FF03" if last_c > ema20 else "#FF1744"
                    icon = "▲" if last_c > ema20 else "▼"
                    st.markdown(f"**{label}**")
                    st.markdown(f"<h1 style='color:{color};'>{icon}</h1>", unsafe_allow_html=True)
                else:
                    st.warning("No Data")
            time.sleep(0.3) # Verlengde pauze tegen blokkade

