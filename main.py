from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ccxt
import pandas as pd
import ta

app = FastAPI()

class SymbolRequest(BaseModel):
    symbol: str

def get_klines(symbol, interval='15m', limit=100):
    exchange = ccxt.binanceus()
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except:
        return None

def calculate_macd(df):
    df['macd'] = ta.trend.macd(df['close'], window_slow=26, window_fast=12)
    df['signal'] = ta.trend.macd_signal(df['close'], window_slow=26, window_fast=12)
    return round(df['macd'].iloc[-1],5), round(df['signal'].iloc[-1],5)

def percentage_change(df, periods):
    if len(df) < periods:
        return None
    return round(((df["close"].iloc[-1] - df["close"].iloc[-periods]) / df["close"].iloc[-periods]) * 100, 2)

@app.post("/analyze")
def analyze_symbol(req: SymbolRequest):
    symbol = req.symbol.upper()
    df = get_klines(symbol)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="Symbol data not found")

    macd, signal = calculate_macd(df)
    change_6h = percentage_change(df, 24)  # 6 ساعات = 24 شريحة 15 دقيقة
    change_24h = percentage_change(df, 96) # 24 ساعة = 96 شريحة 15 دقيقة

    result = {
        "symbol": symbol,
        "macd": macd,
        "signal": signal,
        "change_6h_percent": change_6h,
        "change_24h_percent": change_24h,
    }
    return result
