"""
TaskMaster Agent main entrypoint.
- Accepts high-level instructions
- Uses LangChain + AutoGen for planning (stub)
- Calls Alpha Vantage API
- Persists to SQLite
- Prints result as JSON
"""
import os
import sys
import json
import sqlite3
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
DB_PATH = os.getenv("DB_PATH", "taskmaster.db")

# SQLite schema
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS prices (
    date TEXT,
    ticker TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    sma20 REAL,
    PRIMARY KEY (date, ticker)
);
"""

def fetch_alpha_vantage(ticker):
    url = f"https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": ticker,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "outputsize": "compact"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    if "Time Series (Daily)" not in data:
        raise Exception(f"Alpha Vantage error: {data}")
    df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
    df = df.rename(columns={
        '1. open': 'open',
        '2. high': 'high',
        '3. low': 'low',
        '4. close': 'close',
    })
    df = df[["open", "high", "low", "close"]].astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df

def compute_sma20(df):
    df["sma20"] = df["close"].rolling(window=20).mean()
    return df

def store_to_sqlite(df, ticker, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(CREATE_TABLE_SQL)
    for date, row in df.iterrows():
        if pd.isna(row["sma20"]):
            continue
        c.execute(
            "INSERT OR REPLACE INTO prices (date, ticker, open, high, low, close, sma20) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date.strftime("%Y-%m-%d"), ticker, row["open"], row["high"], row["low"], row["close"], row["sma20"])
        )
    conn.commit()
    conn.close()

def agent(instruction):
    # Simple planner: extract tickers from instruction
    # e.g., "fetch AAPL, MSFT, GOOGL prices; compute 20-day SMA; store in DB"
    import re
    tickers = re.findall(r"[A-Z]{1,5}", instruction)
    results = []
    for ticker in tickers:
        df = fetch_alpha_vantage(ticker)
        df = compute_sma20(df)
        store_to_sqlite(df, ticker)
        latest = df.dropna().iloc[-1]
        results.append({
            "ticker": ticker,
            "date": latest.name.strftime("%Y-%m-%d"),
            "open": latest["open"],
            "high": latest["high"],
            "low": latest["low"],
            "close": latest["close"],
            "sma20": latest["sma20"]
        })
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py 'fetch AAPL'", file=sys.stderr)
        sys.exit(1)
    instruction = sys.argv[1]
    try:
        results = agent(instruction)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
