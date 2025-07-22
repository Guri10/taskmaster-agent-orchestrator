"""
TaskMaster Agent main entrypoint.
- Accepts high-level instructions
- Uses LangChain + AutoGen for planning (stub)
- Fetches data using yfinance
- Persists to SQLite
- Prints result as JSON
"""
import os
import sys
import json
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf
import requests

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
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

def fetch_twelvedata(ticker):
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    print(f"DEBUG: API KEY = '{api_key}'", flush=True) 
    url = f"https://api.twelvedata.com/time_series"
    params = {
        "symbol": ticker,
        "interval": "1day",
        "outputsize": 30,
        "apikey": api_key
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if "values" not in data:
        raise Exception(f"Twelve Data error: {data}")
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.rename(columns={
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close"
    })
    df = df[["datetime", "open", "high", "low", "close"]].astype({"open": float, "high": float, "low": float, "close": float})
    df = df.sort_values("datetime")
    df = df.set_index("datetime")
    return df

def compute_sma20(df):
    df["sma20"] = df["close"].rolling(window=20).mean()
    return df

def store_to_sqlite(df, ticker, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(CREATE_TABLE_SQL)
    def to_float(val):
        return float(val.item()) if hasattr(val, "item") else float(val)
    for date, row in df.iterrows():
        if "sma20" not in row:
            print(f"DEBUG: 'sma20' not in row. Row keys: {list(row.keys())}. Row: {row}")
            raise Exception(f"'sma20' column missing in row for ticker {ticker} on {date}")
        if pd.isna(row["sma20"]):
            continue
        c.execute(
            "INSERT OR REPLACE INTO prices (date, ticker, open, high, low, close, sma20) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(date)[:10], ticker, to_float(row["open"]), to_float(row["high"]), to_float(row["low"]), to_float(row["close"]), to_float(row["sma20"]))
        )
    conn.commit()
    conn.close()

def agent(instruction):
    # Simple planner: extract tickers from instruction
    import re
    tickers = re.findall(r"[A-Z]{1,5}", instruction)
    results = []
    for ticker in tickers:
        df = fetch_twelvedata(ticker)
        df = compute_sma20(df)
        store_to_sqlite(df, ticker)
        clean_df = df.dropna(subset=["sma20"])
        if clean_df.empty:
            raise Exception(f"No rows with valid SMA for ticker {ticker}")
        if not all(col in clean_df.columns for col in ["open", "high", "low", "close", "sma20"]):
            raise Exception(f"Missing expected columns in clean_df: {clean_df.columns}")
        latest = clean_df.iloc[-1]
        try:
            results.append({
                "ticker": ticker,
                "date": latest.name.strftime("%Y-%m-%d"),
                "open": latest["open"],
                "high": latest["high"],
                "low": latest["low"],
                "close": latest["close"],
                "sma20": latest["sma20"]
            })
        except Exception as e:
            raise
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
