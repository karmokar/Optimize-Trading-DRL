from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import yfinance as yf
import pandas as pd

router = APIRouter()

NIFTY100_TICKER = "^CNX100"

class BenchmarkPoint(BaseModel):
    month: str
    benchmark: float

@router.get("/api/nifty100-performance", response_model=list[BenchmarkPoint])
def get_nifty100_performance(
    months: int = Query(12, ge=1, le=60, description="How many months of history to return")
):
    try:
        data = yf.download(
            NIFTY100_TICKER,
            period=f"{months+1}mo",
            interval="1d",
            progress=False
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Nifty 100 data: {e}")

    if data.empty:
        raise HTTPException(status_code=502, detail="Yahoo Finance returned no Nifty 100 data")

    monthly = data['Close'].squeeze().resample("ME").last().dropna()
    monthly = monthly.tail(months)

    if monthly.empty:
        raise HTTPException(status_code=502, detail="Not enough Nifty 100 history to build the series")

    base_value = float(monthly.iloc[0])
    if base_value == 0:
        raise HTTPException(status_code=502, detail="Invalid base value in Nifty 100 series")

    result: list[BenchmarkPoint] = []
    for ts, close in monthly.items():
        result.append(
            BenchmarkPoint(
                month=pd.Timestamp(ts).strftime("%b %y"),
                benchmark=round(float(close) / base_value, 4)
            )
        )

    return result