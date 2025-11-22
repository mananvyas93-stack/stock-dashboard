import streamlit as st
import yfinance as yf

st.title("My Stock Dashboard 🚀")

# This box lets you type a stock symbol
ticker = st.text_input("Enter Stock Symbol", "AAPL")

# This gets the data from the internet
st.write(f"Showing data for: {ticker}")
data = yf.Ticker(ticker).history(period="6mo")

# This draws the line chart
st.line_chart(data['Close'])
