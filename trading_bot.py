import streamlit as st
import pandas as pd
import yfinance as yf
import time

# --- CONFIGURATIE ---
st.set_page_config(page_title="SST AI QUANT TERMINAL", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS voor de Quant Look
st.markdown("""
    <style>
    .main { background-color: #050816; color: white; }
    .stDataFrame { background-color: #0a0e27; border: 1px solid #00D9FF; border-radius: 5px; }
    .trend-box {
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        background: #0d1117;
        border: 1px solid #222;
        margin-bottom: 10px;
    }
    h1, h2, h3 { color: #00D9FF !important; }
    </style>
    """, unsafe_allow_html=True)

def get_ema(series, period=20):
    return series.ewm(span=period, adjust=False).mean()

def fetch_data(symbol, interval, period="1mo"):
    try:
        ticker_sym = symbol.replace("USDT", "-USD") if "USDT" in symbol else symbol
        ticker = yf.Ticker(ticker_sym)
        df = ticker.history(period=period, interval=interval)
        return df if not df.empty else None
    except:
        return None

# --- UI HEADER ---
st.title("⚡ SST AI QUANT ENGINE")

# Controls
c1, c2 = st.columns([3, 1])
with c1:
    symbol_input = st.text_input("SYMBOLEN (bijv. AAPL, TSLA, BTC-USD):", "AAPL, TSLA, NVDA, BTC-USD")
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
    detail_data = {}

    # --- DATA VERZAMELEN ---
    progress_bar = st.progress(0)
    for idx, sym in enumerate(symbols):
        sym_trends = []
        last_vol = 0
        last_price = 0
        
        for label, inv in intervals.items():
            df = fetch_data(sym, inv)
            if df is not None and len(df) > 20:
                price = df['Close'].iloc[-1]
                ema20 = get_ema(df['Close'], 20).iloc[-1]
                trend = 1 if price > ema20 else -1
                sym_trends.append(trend)
                if label == '1D': # Pak volume en prijs van de daggrafiek
                    last_vol = df['Volume'].iloc[-1]
                    last_price = price
            else:
                sym_trends.append(0)
        
        # Berekeningen (Pine Script Style)
        bulls = sym_trends.count(1)
        bears = sym_trends.count(-1)
        strength = round(((bulls - bears) / 6) * 100)
        confidence = round((max(bulls, bears) / 6) * 100)
        
        # Matrix Rij
        matrix_rows.append([
            sym, 
            "▲" if sym_trends[0]==1 else "▼", 
            "▲" if sym_trends[1]==1 else "▼",
            "▲" if sym_trends[2]==1 else "▼",
            "▲" if sym_trends[3]==1 else "▼",
            "▲" if sym_trends[4]==1 else "▼",
            "▲" if sym_trends[5]==1 else "▼",
            f"{strength}%",
            f"{confidence}%",
            f"{last_vol:,.0f}"
        ])
        
        detail_data[sym] = {
            'trends': sym_trends,
            'strength': strength,
            'confidence': confidence,
            'price': last_price,
            'volume': last_vol
        }
        progress_bar.progress((idx + 1) / len(symbols))

    # --- 1. MATRIX BOVENAAN ---
    st.subheader("🔮 TREND PREDICTIONS MATRIX")
    matrix_df = pd.DataFrame(matrix_rows, columns=['SYM', '5M', '15M', '30M', '1H', '4H', '1D', 'STRENGTH', 'CONFIDENCE', 'VOLUME'])
    
    def style_trend(val):
        if val == "▲": return 'color: #76FF03; font-weight: bold; text-align: center;'
        if val == "▼": return 'color: #FF1744; font-weight: bold; text-align: center;'
        return 'text-align: center;'

    st.dataframe(
        matrix_df.style.applymap(style_trend, subset=['5M', '15M', '30M', '1H', '4H', '1D']),
        use_container_width=True,
        hide_index=True
    )

    # --- 2. DETAILS ONDERAAN ---
    st.divider()
    st.subheader("📊 SYMBOL DETAILS")
    
    for sym, data in detail_data.items():
        with st.expander(f"Details voor {sym} (Prijs: {data['price']:.2f})", expanded=True):
            m1, m2, m3 = st.columns(3)
            m1.metric("STRENGTH", f"{data['strength']}%", delta=data['strength'])
            m2.metric("CONFIDENCE", f"{data['confidence']}%")
            m3.metric("VOLUME (24h)", f"{data['volume']:,.0f}")
            
            # De kleine trendboxen
            cols = st.columns(6)
            labels = list(intervals.keys())
            for i, label in enumerate(labels):
                trend = data['trends'][i]
                color = "#76FF03" if trend == 1 else "#FF1744"
                icon = "▲" if trend == 1 else "▼"
                with cols[i]:
                    st.markdown(f"""
                        <div class="trend-box" style="border-top: 3px solid {color};">
                            <div style="color:gray; font-size:10px;">{label}</div>
                            <div style="color:{color}; font-size:24px;">{icon}</div>
                        </div>
                    """, unsafe_allow_html=True)

else:
    st.info("Voer symbolen in en klik op 'RUN ENGINE' om te starten.")



