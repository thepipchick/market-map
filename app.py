# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Live Market Map")

# Ticker groups (confirmed)
INDICES = ["IWM","RSP","QQQ","SPY","DIA"]
SECTORS = ["XLK","SMH","IYR","XLI","XLY","ARKK","XLV","XLF","XLB","XLU","XLE","IBB","XLP","SLV","XLC","GLD","GBTC"]
BIG10 = ["MU","AAPL","TSM","TSLA","AVGO","GOOG","AMZN","NVDA","MSFT","META"]

ALL = INDICES + SECTORS + BIG10

# Helper: fetch last 5 trading days (to compute "yesterday" change robustly)
@st.cache_data(ttl=600)
def fetch_close(ticker):
    try:
        df = yf.Ticker(ticker).history(period="7d", auto_adjust=False)
        closes = df["Close"].dropna()
        if len(closes) < 2:
            return None
        # take last two valid closes
        last = closes.iloc[-1]
        prev = closes.iloc[-2]
        return {"ticker": ticker, "prev_close": float(prev), "close": float(last), "pct": (last/prev - 1) * 100}
    except Exception:
        return None

def build_df(tickers):
    rows = []
    for t in tickers:
        out = fetch_close(t)
        if out:
            rows.append(out)
    df = pd.DataFrame(rows).set_index("ticker")
    # simple normalized strength: scale pct into 0-100 via robust min-max
    if not df.empty:
        pmin, pmax = np.percentile(df["pct"], [5,95])  # robust bounds
        df["strength"] = (df["pct"] - pmin) / (pmax - pmin)
        df["strength"] = df["strength"].clip(0,1) * 100
        # Score: map strength 0-100 into 0-120 scale like screenshot
        df["score"] = (df["strength"] * 1.2).round().astype(int)
        df["strength_pct"] = df["strength"].round().astype(int).astype(str) + "%"
    else:
        df["strength_pct"] = []
        df["score"] = []
    return df

def color_for_strength(val):
    # val is numeric 0-100
    if val >= 80:
        return "background-color: #0f9d58"  # bright green
    if val >= 60:
        return "background-color: #2ebf6e"
    if val >= 40:
        return "background-color: #ffd54f"  # yellowish
    if val >= 20:
        return "background-color: #64b5f6"  # light blue
    return "background-color: #7e57c2"      # purple for weak

def styled_table(df):
    # Build a style that colors rows by strength
    sty = df.style.format({"pct":"{:+.2f}%"}).hide_index()
    def row_style(row):
        return [color_for_strength(row["strength"]) for _ in row]
    try:
        return sty.apply(lambda r: [color_for_strength(r["strength"])]*len(r), axis=1).set_table_styles(
            [{"selector":"th","props":[("background-color","#0b3b60"),("color","white")]}]
        )
    except Exception:
        return sty

st.title("Market Map — Daily (based on previous close)")
st.caption("Data: Yahoo Finance via yfinance. Refresh the page after market close for updated previous-close results.")

col1, col2, col3 = st.columns([1,1,1])

with col1:
    st.subheader("INDICES")
    df_i = build_df(INDICES)
    if not df_i.empty:
        df_i_display = df_i[["strength_pct","score","pct"]].sort_values("score", ascending=False)
        st.dataframe(df_i_display.style.apply(lambda r: [color_for_strength(r["strength"])]*len(r), axis=1), use_container_width=True)
    else:
        st.write("No data yet.")

with col2:
    st.subheader("SECTORS")
    df_s = build_df(SECTORS)
    if not df_s.empty:
        df_s_display = df_s[["strength_pct","score","pct"]].sort_values("score", ascending=False)
        st.dataframe(df_s_display.style.apply(lambda r: [color_for_strength(r["strength"])]*len(r), axis=1), use_container_width=True)
    else:
        st.write("No data yet.")

with col3:
    st.subheader("BIG 10")
    df_b = build_df(BIG10)
    if not df_b.empty:
        df_b_display = df_b[["strength_pct","score","pct"]].sort_values("score", ascending=False)
        st.dataframe(df_b_display.style.apply(lambda r: [color_for_strength(r["strength"])]*len(r), axis=1), use_container_width=True)
    else:
        st.write("No data yet.")

st.markdown("---")
st.caption("Colors: green = strong, purple = weak. Strength and score are a normalized view of yesterday's percent move.")
