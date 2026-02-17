import streamlit as st
import pandas as pd
import yfinance as yf
import time

# --- CONFIGURATIE ---
st.set_page_config(page_title="SST AI QUANT TERMINAL", layout="wide")

# Custom CSS voor de Quant Look
st.markdown("""
    <style>
    .main { background-color: #050816; color: white; }
    .stDataFrame { background-color: #0a0e27; border: 1px solid #00D9FF; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00D9FF; }
    .trend-box {
        text-align: center;
        padding: 8px;
        border-radius: 5px;
        background: #0d1117;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

def calculate_pine_ema(series, period=20):
    """
    Exacte match met Pine Script ta.ema():
    Maakt gebruik van de recursieve formule: EMA = alpha * close + (1 - alpha) * prev_ema
    """
    return series.ewm(span=period, adjust=False).mean()

def fetch_data(symbol, interval):
    try:
        ticker_sym = symbol.replace("USDT", "-USD") if "USDT" in symbol else symbol
        ticker = yf.Ticker(ticker_sym)
        # We halen 100 kaarsen op om de EMA 'warm' te laten draaien voor accuratesse
        df = ticker.history(period="1mo", interval=interval)
        return df if not df.empty else None
    except:
        return None

# --- UI HEADER ---
st.title("⚡ SST AI QUANT ENGINE")

c1, c2 = st.columns([3, 1])
with c1:
    symbol_input = st.text_input("SYMBOLEN:", "AAPL, TSLA, NVDA, BTC-USD")
with c2:
    st.write("##")
    run_btn = st.button("RUN ENGINE", use_container_width=True)

if run_btn:
    symbols = [s.strip().upper() for s in symbol_input.split(',') if s.strip()]
    intervals = {'5M':'5m', '15M':'15m', '30M':'30m', '1H':'60m', '4H':'90m', '1D':'1d'}
    
    matrix_rows = []
    
    progress_bar = st.progress(0)
    for idx, sym in enumerate(symbols):
        trends = []
        current_price = 0
        volume = 0
        
        for label, inv in intervals.items():
            df = fetch_data(sym, inv)
            if df is not None and len(df) > 20:
                # Pine Script berekening: Close > EMA20
                ema_series = calculate_pine_ema(df['Close'], 20)
                last_close = df['Close'].iloc[-1]
                last_ema = ema_series.iloc[-1]
                
                trends.append(1 if last_close > last_ema else -1)
                
                if label == '1D':
                    current_price = last_close
                    volume = df['Volume'].iloc[-1]
            else:
                trends.append(0)
        
        # Berekening Strength & Confidence
        bulls = trends.count(1)
        bears = trends.count(-1)
        strength = round(((bulls - bears) / 6) * 100)
        confidence = round((max(bulls, bears) / 6) * 100)
        
        # Kleurcode symbolen voor Matrix
        t_icons = ["▲" if t == 1 else "▼" if t == -1 else "━" for t in trends]
        
        matrix_rows.append({
            'SYM': sym,
            'PRICE': f"{current_price:.2f}",
            '5M': t_icons[0], '15M': t_icons[1], '30M': t_icons[2],
            '1H': t_icons[3], '4H': t_icons[4], '1D': t_icons[5],
            'STR': f"{strength}%",
            'CONF': f"{confidence}%",
            'VOL': f"{volume/1_000_000:.1f}M"
        })
        progress_bar.progress((idx + 1) / len(symbols))

    # --- MATRIX WEERGAVE ---
    st.subheader("🔮 LIVE TREND PREDICTIONS MATRIX")
    df_matrix = pd.DataFrame(matrix_rows)

    def style_trend(val):
        if val == "▲": return 'color: #76FF03; text-align: center; font-weight: bold;'
        if val == "▼": return 'color: #FF1744; text-align: center; font-weight: bold;'
        return 'text-align: center; color: gray;'

    st.dataframe(
        df_matrix.style.applymap(style_trend, subset=['5M','15M','30M','1H','4H','1D']),
        use_container_width=True,
        hide_index=True
    )

    # --- VISUELE DETAILS ---
    st.divider()
    for row in matrix_rows:
        with st.expander(f"Detail Analyse: {row['SYM']} | Prijs: {row['PRICE']}"):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", row['PRICE'])
            col2.metric("Trend Strength", row['STR'])
            col3.metric("Confidence", row['CONF'])
            col4.metric("Vol (24h)", row['VOL'])

else:
    st.info("Systeem gereed. Voer symbolen in om de Pine Script engine te starten.")




