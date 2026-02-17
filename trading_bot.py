import streamlit as st
import pandas as pd
import yfinance as yf
import time

# --- STYLING & LAYOUT CONFIG ---
st.set_page_config(page_title="SST AI QUANT V4", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS voor de "Trading Terminal" look
st.markdown("""
    <style>
    .main { background-color: #050816; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .reportview-container { background: #050816; }
    
    /* Paneel styling */
    .stMetric {
        background-color: rgba(10, 14, 39, 0.9);
        border: 1px solid #00D9FF;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Trend cellen */
    .trend-box {
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #222;
        background: #0d1117;
        margin-bottom: 10px;
    }
    
    h1, h2, h3 { color: #00D9FF !important; font-family: 'Segoe UI', sans-serif; }
    .stMarkdown { color: white; }
    
    /* Verberg Streamlit rommel */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE ---
def get_ema(series, period=20):
    return series.ewm(span=period, adjust=False).mean()

def fetch_data(symbol, interval):
    try:
        ticker_sym = symbol.replace("USDT", "-USD") if "USDT" in symbol else symbol
        ticker = yf.Ticker(ticker_sym)
        # We halen 60 kaarsen op voor een zuivere EMA20 berekening
        df = ticker.history(period="1mo", interval=interval)
        return df if not df.empty else None
    except:
        return None

# --- UI ---
st.title("⚡ SST AI QUANT TERMINAL")

# Controls
c1, c2 = st.columns([3, 1])
with c1:
    symbol_input = st.text_input("SYMBOLEN (gescheiden door komma's):", "AAPL, TSLA, NVDA, BTC-USD")
with c2:
    st.write("##")
    run_btn = st.button("RUN ENGINE", use_container_width=True)

if run_btn:
    symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]
    intervals = {
        '5M': '5m', '15M': '15m', '30M': '30m', 
        '1H': '60m', '4H': '90m', '1D': '1d'
    }
    
    matrix_rows = []

    for sym in symbols:
        st.markdown(f"### 📈 {sym}")
        cols = st.columns(6)
        sym_trends = []

        for i, (label, inv) in enumerate(intervals.items()):
            df = fetch_data(sym, inv)
            
            with cols[i]:
                if df is not None and len(df) > 20:
                    last_price = df['Close'].iloc[-1]
                    ema20 = get_ema(df['Close'], 20).iloc[-1]
                    
                    # Exacte Pine Script vergelijking
                    is_bull = last_price > ema20
                    sym_trends.append(1 if is_bull else -1)
                    
                    color = "#76FF03" if is_bull else "#FF1744"
                    icon = "▲" if is_bull else "▼"
                    
                    st.markdown(f"""
                        <div class="trend-box" style="border-top: 3px solid {color};">
                            <div style="color:gray; font-size:12px; font-weight:bold;">{label}</div>
                            <div style="color:{color}; font-size:32px; margin:5px 0;">{icon}</div>
                            <div style="font-size:14px;">{last_price:.2f}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("N/A")
                    sym_trends.append(0)
            time.sleep(0.05)

        # Bereken Scores (Pine Script Match)
        bulls = sym_trends.count(1)
        bears = sym_trends.count(-1)
        strength = round(((bulls - bears) / 6) * 100)
        
        # Voeg toe aan matrix data
        matrix_rows.append([sym] + sym_trends + [f"{strength}%"])

    # --- MATRIX ONDERAAN (Exact zoals de bot) ---
    st.markdown("---")
    st.subheader("🔮 TREND PREDICTIONS MATRIX")
    
    matrix_df = pd.DataFrame(matrix_rows, columns=['SYM', '5M', '15M', '30M', '1H', '4H', '1D', 'STRENGTH'])
    
    def style_matrix(val):
        if val == 1: return 'background-color: rgba(118, 255, 3, 0.1); color: #76FF03; text-align: center;'
        if val == -1: return 'background-color: rgba(255, 23, 68, 0.1); color: #FF1744; text-align: center;'
        return 'text-align: center;'

    # Toon de matrix in volle breedte
    st.dataframe(
        matrix_df.style.applymap(style_matrix, subset=['5M', '15M', '30M', '1H', '4H', '1D']),
        use_container_width=True,
        hide_index=True
    )


