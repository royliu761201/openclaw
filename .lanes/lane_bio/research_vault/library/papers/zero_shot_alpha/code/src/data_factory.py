
import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Constants
DATA_DIR = "data/zero_shot_alpha"
TARGET_FILE = os.path.join(DATA_DIR, "market_regimes.parquet")
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
LIMIT = 1000

def fetch_binance_data(symbol, interval, limit):
    """Fetch Klines from Binance Public API"""
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    print(f"🌍 Fetching {symbol} {interval} data from Binance...")
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Parse Response
        # [Open Time, Open, High, Low, Close, Volume, ...]
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", 
            "close_time", "quote_asset_volume", "trades", 
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        
        # Convert types
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
            
        print(f"✅ Fetched {len(df)} rows from Binance.")
        return df[["timestamp", "open", "high", "low", "close", "volume"]]
        
    except Exception as e:
        print(f"⚠️ Binance API Failed: {e}")
        return None

def generate_synthetic_data(n_rows=1000):
    """Generate Synthetic GBM Data if API fails"""
    print("🎲 Generating Synthetic GBM Data...")
    dates = pd.date_range(end=datetime.now(), periods=n_rows, freq="1h")
    
    # GBM Parameters
    dt = 1/24/365
    mu = 0.1
    sigma = 0.5
    s0 = 50000
    
    prices = [s0]
    for _ in range(n_rows-1):
        drift = (mu - 0.5 * sigma**2) * dt
        shock = sigma * np.sqrt(dt) * np.random.normal()
        price = prices[-1] * np.exp(drift + shock)
        prices.append(price)
        
    df = pd.DataFrame({
        "timestamp": dates,
        "close": prices,
        "open": prices, # Simplified
        "high": [p * 1.01 for p in prices],
        "low": [p * 0.99 for p in prices],
        "volume": np.random.random(n_rows) * 1000
    })
    return df

def limit_rsi(series, period=14):
    """Calculate RSI manually without ta-lib"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def label_regimes(df):
    """Add factors and regimes"""
    print("⚙️ Engineering Features & Labels...")
    
    # Factors
    df["log_ret"] = np.log(df["close"] / df["close"].shift(1)).fillna(0)
    df["volatility"] = df["log_ret"].rolling(24).std().fillna(0)
    df["rsi"] = limit_rsi(df["close"])
    
    # Hindsight Labeling (Next 24h Return)
    # If Next 24h > X% -> Bull, < -X% -> Bear, Else Chop
    
    df["fwd_ret_24h"] = df["close"].shift(-24) / df["close"] - 1
    
    # Thresholds
    THRESH = 0.02 # 2% move in 24h
    
    conditions = [
        (df["fwd_ret_24h"] > THRESH),
        (df["fwd_ret_24h"] < -THRESH)
    ]
    choices = ["BULL", "BEAR"]
    
    df["regime"] = np.select(conditions, choices, default="CHOP")
    
    # Clean NaN from shift
    df = df.dropna()
    
    return df

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    # 1. Fetch
    df = fetch_binance_data(SYMBOL, INTERVAL, LIMIT)
    
    # 2. Fallback
    if df is None or df.empty:
        df = generate_synthetic_data(LIMIT)
        
    # 3. Label
    df = label_regimes(df)
    
    # 4. Save
    print(f"💾 Saving to {TARGET_FILE}...")
    df.to_parquet(TARGET_FILE)
    
    # 5. Review
    print("\n--- Data Preview ---")
    print(df["regime"].value_counts())
    print(df.head())
    print("--------------------")

if __name__ == "__main__":
    main()
