import streamlit as st
import pandas as pd
import requests
import time

# --- PAGINA CONFIGURATIE ---
st.set_page_config(page_title="SST AI QUANT TERMINAL", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050816; color: white; }
    .stMetric { background-color: #0d1117; padding: 15px; border-radius: 10px; border: 1px solid #00D9FF; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATIE ---
API_KEY = 'd5h3vm9r01qll3dlm2sgd5h3vm9r01qll3dlm2t0'

def get_ema(series, period=20):
    """Berekent de EMA zoals Pine Script (TradingView)"""
    return series.ewm(span=period, adjust=False).mean()

def fetch_data(symbol, res):
    """Haalt kaarsdata op van Finnhub"""
    url = f"https://finnhub.io/api/v1/candle?symbol={symbol}&resolution={res}&count=50&token={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        if data.get('s') == 'ok':
            return pd.DataFrame({'close': data['c']})
    except:
        return None
    return None

# --- UI HEADER ---
st.title("⚡ SST AI QUANT ENGINE")
st.subheader("Multi-Timeframe Trend Analysis (EMA 20)")

# Input voor de gebruiker
symbol_input = st.text_input("Voer symbolen in (gescheiden door komma's):", "AAPL, TSLA, NVDA, BTCUSDT")
run_button = st.button("RUN ANALYSE")

if run_button:
    symbols = [s.strip().upper() for s in symbol_input.split(',')]
    resolutions = {'5M': '5', '15M': '15', '30M': '30', '1H': '60', '4H': '240', '1D': 'D'}
    
    # Grid voor dashboards
    cols = st.columns(len(symbols))
    matrix_data = []

    for idx, sym in enumerate(symbols):
        with cols[idx % len(cols)]:
            st.write(f"### {sym}")
            results = []
            
            for label, res in resolutions.items():
                df = fetch_data(sym, res)
                
                if df is not None:
                    df['ema20'] = get_ema(df['close'], 20)
                    last_c = df['close'].iloc[-1]
                    last_e = df['ema20'].iloc[-1]
                    trend = 1 if last_c > last_e else -1
                else:
                    trend = 0 # Fout bij ophalen
                
                results.append(trend)
                time.sleep(0.1) # Voorkom API blokkade

            # Berekening Scores
            bulls = results.count(1)
            bears = results.count(-1)
            strength = round(((bulls - bears) / 6) * 100)
            conf = round((max(bulls, bears) / 6) * 100)

            # Toon metrics
            st.metric("Strength", f"{strength}%")
            st.metric("Confidence", f"{conf}%")

            # Detail tabel per symbool
            res_df = pd.DataFrame({
                'Timeframe': list(resolutions.keys()),
                'Trend': ['▲ Bullish' if r==1 else '▼ Bearish' if r==-1 else '━ Geen Data' for r in results]
            })
            st.table(res_df)
            
            # Data voor de Matrix onderaan
            matrix_data.append([sym] + results)

    # --- MATRIX OVERZICHT ---
    st.divider()
    st.write("### 🔮 TREND PREDICTIONS MATRIX")
    matrix_columns = ['SYMBOOL', '5M', '15M', '30M', '1H', '4H', '1D']
    final_matrix = pd.DataFrame(matrix_data, columns=matrix_columns)
    
    # Styling voor de matrix
    def color_trend(val):
        if val == 1: return 'color: #76FF03'
        if val == -1: return 'color: #FF1744'
        return 'color: gray'

    st.dataframe(final_matrix.style.applymap(color_trend, subset=matrix_columns[1:]))

else:
    st.info("Vul de symbolen in en klik op 'RUN ANALYSE' om de live data te laden.")
