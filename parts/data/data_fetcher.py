
import yfinance as yf
import pandas as pd
import pytz


tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'USDC-USD', 'USDT-USD']
for ticker in tickers:
    df = yf.Ticker(ticker).history(start="2022-01-01", end="2022-12-31")

    df.reset_index(inplace=True)
    df["Date"] = [str(val)[:-15] for val in df['Date']]
    df.drop(columns=['Dividends', 'Stock Splits'], inplace=True)

    df.to_excel(f"{ticker.replace('-USD', '')}.xlsx", index=False)